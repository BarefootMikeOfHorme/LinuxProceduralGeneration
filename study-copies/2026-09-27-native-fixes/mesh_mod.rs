//! Mesh processing and optimization
//!
//! Inspired by Ice Engine's Meshmerizer: mesh cleaning, LOD generation,
//! compression, subdivision surfaces, convex hulls, etc.

use crate::geometry::Mesh;
use crate::{Result, GeometryError};
use rayon::prelude::*;
use std::collections::HashMap;

pub mod validation;
pub mod optimizer;
pub mod lod;
pub mod subdivision;
pub mod obj;
pub mod simplify;
pub mod structure;

pub use optimizer::MeshOptimizer;
pub use validation::{MeshValidator, ValidationReport};
pub use lod::LodGenerator;
pub use obj::load_obj;
pub use simplify::simplify;
pub use structure::{check_structure, StructuralReport};

/// Clean a mesh: drop degenerate triangles, weld coincident vertices, recompute
/// normals.
///
/// This **mutates** and is the repair counterpart to
/// [`crate::mesh::structure::check_structure`], which is a pure query. The split
/// is deliberate and is how CGAL and Manifold organise the same problem: report
/// exhaustively without touching anything, then repair under an explicitly named
/// operation that returns new geometry.
///
/// Note the *order*. Degenerate triangles go first, because welding can turn a
/// valid triangle into an index-degenerate one and there is no point removing
/// index degeneracies that welding is about to create. Welding is not
/// undoable in general: merging two vertices is a geometric operation, and the
/// floating-point error in doing it need not come back to a manifold result.
///
/// `tolerance` is explicit and has no hidden default. Welding generated
/// geometry with a non-exact tolerance hides construction bugs rather than fixing
/// them; see [`WeldTolerance`].
pub fn clean_mesh(mesh: &mut Mesh, tolerance: WeldTolerance) -> Result<()> {
    remove_degenerate_triangles(mesh)?;
    let (welded, merged) = weld_vertices(mesh, tolerance);
    if merged > 0 {
        *mesh = welded;
        mesh.compute_normals();
    }
    Ok(())
}

/// Remove index-degenerate triangles: those naming a vertex twice, or with an
/// index out of range.
///
/// This is a *structural* test, decided on indices alone, so it needs no
/// tolerance. Whether a triangle with three distinct vertices is geometrically
/// too thin to keep is a different question with a different answer, and it is
/// deliberately not answered here: see [`WeldTolerance`] for why an absolute
/// threshold is the wrong tool and what the scale-relative form looks like.
///
/// Removing a sliver is not the same as removing an index degenerate, and
/// conflating them is a real bug. Dropping a zero-area face loses the attributes
/// attached to it. The correct treatment is to collapse its shortest edge and
/// interpolate, which is what Manifold's `RemoveDegenerates` does, because a
/// "remove zero-area faces" filter that just deletes the triangle throws the UVs
/// and the material away with it.
fn remove_degenerate_triangles(mesh: &mut Mesh) -> Result<()> {
    let mut valid_indices: Vec<u32> = Vec::with_capacity(mesh.indices.len());
    let vertex_count = mesh.vertices.len();

    for chunk in mesh.indices.chunks(3) {
        if chunk.len() != 3 {
            continue;
        }
        let (i0, i1, i2) = (chunk[0] as usize, chunk[1] as usize, chunk[2] as usize);
        if i0 >= vertex_count || i1 >= vertex_count || i2 >= vertex_count {
            continue;
        }
        if i0 == i1 || i1 == i2 || i0 == i2 {
            continue;
        }
        valid_indices.extend_from_slice(chunk);
    }

    mesh.indices = valid_indices;
    Ok(())
}

/// How close two vertices must be to be treated as the same point.
///
/// Split by path, which is the whole answer and is what every system that
/// ships a hard guarantee does: CGAL, Manifold, MikkTSpace, VTK and xatlas all
/// default to **bit-exact**, and every one of them that offers a tolerance
/// exposes it as a user-facing knob whose docs warn that it alters topology.
///
/// The default is exact for a reason that is specific to LPG. The primitives
/// used to close their cylinder, cone and torus seams with a spare column of
/// vertices, and the gap that produced was about 2.4e-7 of a unit. The obvious
/// reading was "that needs a weld tolerance of about 2.4e-7", and that reading
/// is wrong: 2*pi sits in the f32 binade [4, 8) where the half-ulp is 2.38e-7,
/// so that number *was* the f32 rounding at 2*pi, and in f64 `sin(2*pi)` is
/// -2.4e-16. The seam was a type bug in the generator. A tolerance would have
/// hidden a construction defect and left the geometry 1e-7 wrong everywhere,
/// not just at the seam.
///
/// A one-ULP tolerance is still the right default for *imported* meshes, where
/// there is no generator to fix. See [`WeldTolerance::OneUlp`].
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum WeldTolerance {
    /// Bit-exact. The only correct default for generated geometry.
    Exact,
    /// `2^-23 * max|coordinate|`, the tightest tolerance that can never merge two
    /// f32 values further apart than about one ULP. This is Manifold's
    /// `MeshGL::Merge` floor, and the right choice for an import path.
    OneUlp,
    /// An absolute distance in model units. Named, never defaulted to, because
    /// an absolute number means nothing across a pipeline that handles both
    /// millimetres and metres.
    Absolute(f32),
}

impl WeldTolerance {
    /// The absolute epsilon to use for a mesh of this size, or `None` for exact.
    pub fn resolve(self, mesh: &Mesh) -> Option<f32> {
        match self {
            Self::Exact => None,
            Self::Absolute(value) => Some(value),
            Self::OneUlp => {
                // Manifold uses the largest absolute coordinate rather than the
                // bounding-box extent, because that is what bounds how finely
                // f32 can represent the points where they actually are.
                let scale = mesh
                    .vertices
                    .iter()
                    .fold(0.0f32, |acc, v| acc.max(v.x.abs()).max(v.y.abs()).max(v.z.abs()));
                Some(f32::EPSILON * scale.max(1.0))
            }
        }
    }
}

/// Weld coincident vertices, returning a new mesh and how many were merged.
///
/// Order-independent by construction: clusters are formed by union-find over a
/// spatial hash, and the representative is the lowest original index in each
/// cluster. Both choices matter and the previous implementation got both wrong.
///
/// The old code scanned a growing vector and took the *first* vertex within
/// tolerance, which is order-dependent by construction, and "within tolerance"
/// is not a transitive relation, so `a~b` and `b~c` did not imply `a~c`. That is
/// formally undefined behaviour as a hash-map equality predicate, which is
/// exactly the bug Assimp ships in `JoinVerticesProcess`, and in practice it
/// makes the result depend on iteration order and therefore on how a parallel
/// pipeline happens to be scheduled. It was also O(n^2).
pub fn weld_vertices(mesh: &Mesh, tolerance: WeldTolerance) -> (Mesh, usize) {
    let Some(epsilon) = tolerance.resolve(mesh) else {
        // Exact path: identical bit patterns, which is a hash of the raw bits
        // and needs no spatial search at all.
        let mut index: HashMap<[u32; 3], u32> = HashMap::with_capacity(mesh.vertices.len());
        for (i, v) in mesh.vertices.iter().enumerate() {
            index.entry([v.x.to_bits(), v.y.to_bits(), v.z.to_bits()]).or_insert(i as u32);
        }
        let mut remap = vec![0u32; mesh.vertices.len()];
        let mut merged = 0usize;
        for (i, v) in mesh.vertices.iter().enumerate() {
            let target = index[&[v.x.to_bits(), v.y.to_bits(), v.z.to_bits()]];
            remap[i] = target;
            if target as usize != i {
                merged += 1;
            }
        }
        return (remap_mesh(mesh, &remap, mesh.vertices.len()), merged);
    };

    if epsilon <= 0.0 {
        return (mesh.clone(), 0);
    }

    // Spatial hash on a grid of cell size epsilon, probing the 27 surrounding
    // cells so a pair either side of a cell boundary still merges. Snapping
    // coordinates to a grid would be one hash pass instead of 27 probes, but two
    // points within tolerance can straddle a cell boundary and then never meet,
    // so the snapping form has to be offered as a documented separate mode or not
    // at all.
    let cell = epsilon;
    let cell_of = |v: &nalgebra::Point3<f32>| -> [i64; 3] {
        [
            (v.x as f64 / cell as f64).floor() as i64,
            (v.y as f64 / cell as f64).floor() as i64,
            (v.z as f64 / cell as f64).floor() as i64,
        ]
    };

    let mut grid: HashMap<[i64; 3], Vec<u32>> = HashMap::new();
    for (i, v) in mesh.vertices.iter().enumerate() {
        grid.entry(cell_of(v)).or_default().push(i as u32);
    }

    let mut parent: Vec<u32> = (0..mesh.vertices.len() as u32).collect();
    fn find(parent: &mut [u32], mut v: u32) -> u32 {
        while parent[v as usize] != v {
            parent[v as usize] = parent[parent[v as usize] as usize];
            v = parent[v as usize];
        }
        v
    }
    let mut union = |parent: &mut Vec<u32>, a: u32, b: u32| {
        let (ra, rb) = (find(parent, a), find(parent, b));
        if ra != rb {
            // Always attach the higher root to the lower, so the representative
            // is the lowest index in the cluster regardless of merge order.
            if ra < rb {
                parent[rb as usize] = ra;
            } else {
                parent[ra as usize] = rb;
            }
        }
    };

    for (i, v) in mesh.vertices.iter().enumerate() {
        let base = cell_of(v);
        for dx in -1..=1i64 {
            for dy in -1..=1i64 {
                for dz in -1..=1i64 {
                    let key = [base[0] + dx, base[1] + dy, base[2] + dz];
                    let Some(neighbours) = grid.get(&key) else {
                        continue;
                    };
                    for &other in neighbours {
                        if other as usize == i {
                            continue;
                        }
                        let o = mesh.vertices[other as usize];
                        // Chebyshev, matching Manifold's box-overlap merge and
                        // avoiding a square root in the inner loop.
                        let within = (o.x - v.x).abs() <= cell
                            && (o.y - v.y).abs() <= cell
                            && (o.z - v.z).abs() <= cell;
                        if within {
                            union(&mut parent, i as u32, other);
                        }
                    }
                }
            }
        }
    }

    let mut remap = vec![0u32; mesh.vertices.len()];
    for i in 0..mesh.vertices.len() {
        remap[i] = find(&mut parent, i as u32);
    }
    let survivors = {
        let mut seen: HashMap<u32, ()> = HashMap::new();
        for &r in &remap {
            seen.insert(r, ());
        }
        seen.len()
    };
    let merged = mesh.vertices.len() - survivors;
    (remap_mesh(mesh, &remap, survivors), merged)
}

/// Build a new mesh with vertices collapsed onto their cluster representatives.
fn remap_mesh(mesh: &Mesh, remap: &[u32], vertex_count: usize) -> Mesh {
    let mut out = Mesh::new();
    let mut dense = vec![u32::MAX; remap.len()];
    let mut next = 0u32;
    for v in 0..remap.len() {
        let root = remap[v];
        if dense[root as usize] == u32::MAX {
            dense[root as usize] = next;
            out.vertices.push(mesh.vertices[root as usize]);
            if mesh.normals.len() == mesh.vertices.len() {
                out.normals.push(mesh.normals[root as usize]);
            }
            if mesh.uvs.len() == mesh.vertices.len() {
                out.uvs.push(mesh.uvs[root as usize]);
            }
            next += 1;
        }
        dense[v] = dense[root as usize];
    }
    debug_assert_eq!(out.vertices.len(), vertex_count);

    for f in 0..mesh.triangle_count() {
        for k in 0..3 {
            let corner = mesh.indices[f * 3 + k];
            out.indices.push(dense[corner as usize]);
        }
    }
    out.sharp_edges = mesh
        .sharp_edges
        .iter()
        .filter_map(|&(a, b)| {
            let (x, y) = (dense[a as usize], dense[b as usize]);
            if x != y {
                Some((x, y))
            } else {
                None
            }
        })
        .collect();
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A triangle with a duplicated vertex at two slightly different positions.
    fn near_duplicate_triangle() -> Mesh {
        let mut mesh = Mesh::new();
        mesh.vertices.push(nalgebra::Point3::new(0.0, 0.0, 0.0));
        mesh.vertices.push(nalgebra::Point3::new(1.0, 0.0, 0.0));
        // 2e-7 away from vertex 0: about the f32 half-ulp at 2*pi, which is
        // exactly the gap LPG's seam bug used to produce.
        mesh.vertices.push(nalgebra::Point3::new(0.0, 1.0, 0.0));
        mesh.vertices.push(nalgebra::Point3::new(0.0, 1.0 + 2.0e-7, 0.0));
        mesh.indices.extend_from_slice(&[0, 1, 2, 1, 3, 2]);
        mesh
    }

    #[test]
    fn exact_welding_ignores_near_duplicates() {
        // The default must not merge these, because they are not the same point.
        // A tolerance that did would be hiding a construction bug.
        let mesh = near_duplicate_triangle();
        let (welded, merged) = weld_vertices(&mesh, WeldTolerance::Exact);
        assert_eq!(merged, 0, "bit-exact welding must not merge a 2e-7 gap");
        assert_eq!(welded.vertices.len(), 4);
    }

    #[test]
    fn a_one_ulp_tolerance_is_still_too_tight_to_bridge_that_gap() {
        // Which is the point: a one-ULP tolerance is for *import* paths. It would
        // not, and must not, paper over a generator that rounds at 2*pi.
        let mesh = near_duplicate_triangle();
        let (welded, merged) = weld_vertices(&mesh, WeldTolerance::OneUlp);
        assert_eq!(merged, 0, "one ULP must not bridge a 2e-7 gap");
        assert_eq!(welded.vertices.len(), 4);
    }

    #[test]
    fn an_explicit_absolute_tolerance_does_merge_and_renumbers_correctly() {
        let mesh = near_duplicate_triangle();
        let (welded, merged) = weld_vertices(&mesh, WeldTolerance::Absolute(1.0e-6));
        assert_eq!(merged, 1, "1e-6 is comfortably wider than 2e-7");
        assert_eq!(welded.vertices.len(), 3);
        // Every index must still be in range, or the mesh is now corrupt.
        assert!(welded.indices.iter().all(|&i| (i as usize) < welded.vertices.len()));
        assert_eq!(welded.indices.len(), mesh.indices.len(), "topology preserved");
    }

    #[test]
    fn welding_is_order_independent() {
        // The old implementation took the first vertex within tolerance, and
        // "within tolerance" is not transitive, so the result depended on
        // iteration order. Two runs that differ only in input ordering must agree
        // on the vertex count, and the merged count must be stable.
        let mut mesh = near_duplicate_triangle();
        let (_, first) = weld_vertices(&mesh, WeldTolerance::Absolute(1.0e-6));
        // Reverse the vertex order and reindex.
        let n = mesh.vertices.len();
        mesh.vertices.reverse();
        let new_indices: Vec<u32> = mesh
            .indices
            .iter()
            .map(|&i| (n as u32 - 1) - i)
            .collect();
        mesh.indices = new_indices;
        let (welded, second) = weld_vertices(&mesh, WeldTolerance::Absolute(1.0e-6));
        assert_eq!(first, second, "the merged count must not depend on order");
        assert_eq!(welded.vertices.len(), 3);
    }

    #[test]
    fn welding_keeps_the_result_structurally_sound() {
        let mesh = near_duplicate_triangle();
        let (welded, _) = weld_vertices(&mesh, WeldTolerance::Absolute(1.0e-6));
        let report = crate::mesh::structure::check_structure(&welded);
        assert!(
            report.out_of_range_indices == 0,
            "welding left a dangling index: {:?}",
            report.issues()
        );
    }

    #[test]
    fn clean_mesh_requires_an_explicit_tolerance() {
        let mut mesh = near_duplicate_triangle();
        clean_mesh(&mut mesh, WeldTolerance::Exact).unwrap();
        assert_eq!(mesh.vertex_count(), 4, "exact cleaning changes nothing here");
    }
}
pub mod advanced_optimizer;
pub use advanced_optimizer::AdvancedOptimizer;
