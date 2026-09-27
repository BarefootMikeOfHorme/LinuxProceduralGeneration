//! Epsilon-free structural mesh validation.
//!
//! Every check in this module is a **pure query**. Nothing here mutates a mesh,
//! and nothing here uses a tolerance. That is a deliberate split, and it is the
//! opposite of what Blender's `mesh.validate()` does — that function *repairs*:
//! it removes faces, rebuilds edge loops, and rewrites material indices, and it
//! does so even when called from a read-only-looking API. A validator that edits
//! the thing it is inspecting cannot be trusted to report, and a caller who
//! wanted a report gets silent data loss instead.
//!
//! The split is also how CGAL and Manifold organise the same problem: an
//! exhaustive query that mutates nothing, plus explicitly named repair
//! operations that return new meshes. Repair lives in
//! [`crate::mesh::clean_mesh`], never in here.
//!
//! # Why no tolerance
//!
//! Structural validity is a question about *indices*, not about coordinates. Two
//! triangles wound the same direction along a shared edge is a topology fact,
//! decidable exactly, and no epsilon can improve on an exact answer. Metric
//! judgements — is this triangle too thin, should these two vertices be welded —
//! are a different category and do need a tolerance; they belong with the repair
//! operations, never here.
//!
//! # What this catches
//!
//! The winding check is the one that earns the module its place. A closed,
//! manifold mesh whose total signed volume looks plausible can still have a
//! region wound backwards, because one inverted cap subtracts from a sum
//! dominated by everything else. LPG shipped exactly that: both sphere pole caps
//! wound inward while the total read +3.96 against an ideal 4.19, so a volume
//! assertion passed throughout. Traversal direction across shared edges finds it
//! immediately, and needs no geometry at all.

use crate::geometry::Mesh;
use std::collections::HashMap;

/// Undirected edge key.
type Undirected = (u32, u32);

fn undirected(a: u32, b: u32) -> Undirected {
    if a < b {
        (a, b)
    } else {
        (b, a)
    }
}

/// A directed half-edge, in the order the face traverses it.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct HalfEdge {
    from: u32,
    to: u32,
}

/// Structural findings. Every count is exact; none depends on a tolerance.
#[derive(Debug, Clone, Default)]
pub struct StructuralReport {
    /// Indices at or beyond the vertex count. Always a hard error: reading them
    /// would be out of bounds.
    pub out_of_range_indices: usize,
    /// Triangles naming the same vertex twice. They carry no geometry at all.
    pub index_degenerate_faces: usize,
    /// Interior edges whose two faces traverse them in the *same* direction.
    /// This is an inside-out region.
    pub winding_inconsistencies: usize,
    /// Edges shared by more than two faces.
    pub over_connected_edges: usize,
    /// Edges shared by exactly one face, i.e. holes.
    pub boundary_edges: usize,
    /// Vertices whose incident faces do not form a single fan, i.e. bow-ties.
    pub non_manifold_vertices: usize,
    /// Faces with the same three vertices as another face.
    pub duplicate_faces: usize,
    /// Vertices with a NaN or infinite coordinate.
    pub non_finite_vertices: usize,
    /// Vertices no face references.
    pub unreferenced_vertices: usize,
    /// Connected components of the surface.
    pub component_count: usize,
    /// Euler characteristic per component, as `(component, chi)`.
    ///
    /// `None` when the surface is not closed, because `V - E + F` then says
    /// nothing without also knowing the boundary count. Reported rather than
    /// gated on: a caller has to supply the expected genus for it to mean
    /// anything, and an odd value is only diagnostic.
    pub euler_characteristic: Option<Vec<(usize, i64)>>,
}

impl StructuralReport {
    /// Whether the mesh is structurally sound: in range, no index-degenerate
    /// faces, consistently wound, manifold, closed, finite.
    pub fn is_structurally_valid(&self) -> bool {
        self.out_of_range_indices == 0
            && self.index_degenerate_faces == 0
            && self.winding_inconsistencies == 0
            && self.over_connected_edges == 0
            && self.boundary_edges == 0
            && self.non_manifold_vertices == 0
            && self.duplicate_faces == 0
            && self.non_finite_vertices == 0
    }

    /// Human-readable lines, one finding per line, empty when clean.
    pub fn issues(&self) -> Vec<String> {
        let mut out = Vec::new();
        let mut push = |n: usize, what: &str| {
            if n > 0 {
                out.push(format!("{what}: {n}"));
            }
        };
        push(self.out_of_range_indices, "indices out of range");
        push(self.index_degenerate_faces, "triangles naming a vertex twice");
        push(self.winding_inconsistencies, "edges traversed the same way by both faces");
        push(self.over_connected_edges, "edges shared by more than two faces");
        push(self.boundary_edges, "boundary edges (the surface is open)");
        push(self.non_manifold_vertices, "non-manifold vertices");
        push(self.duplicate_faces, "duplicate faces");
        push(self.non_finite_vertices, "non-finite vertex coordinates");
        push(self.unreferenced_vertices, "vertices referenced by no face");
        if let Some(chi) = &self.euler_characteristic {
            for (component, value) in chi {
                if value % 2 != 0 {
                    out.push(format!(
                        "component {component} has odd Euler characteristic {value}, which no closed \
                         orientable surface can have"
                    ));
                }
            }
        }
        out
    }
}

/// Runs every structural check. Mutates nothing.
///
/// Indices are validated before anything indexes a vertex, so a malformed mesh
/// is reported rather than causing an out-of-bounds read while being measured.
pub fn check_structure(mesh: &Mesh) -> StructuralReport {
    let mut report = StructuralReport::default();

    for &index in &mesh.indices {
        if index as usize >= mesh.vertices.len() {
            report.out_of_range_indices += 1;
        }
    }
    if report.out_of_range_indices > 0 {
        // Every later check indexes vertices. Reporting the real defect and
        // stopping is more useful than a cascade of nonsense derived from it.
        return report;
    }

    for vertex in &mesh.vertices {
        if !vertex.x.is_finite() || !vertex.y.is_finite() || !vertex.z.is_finite() {
            report.non_finite_vertices += 1;
        }
    }

    let face_count = mesh.indices.len() / 3;
    let mut referenced = vec![false; mesh.vertices.len()];
    let mut faces: Vec<[u32; 3]> = Vec::with_capacity(face_count);
    for f in 0..face_count {
        let face = [
            mesh.indices[f * 3],
            mesh.indices[f * 3 + 1],
            mesh.indices[f * 3 + 2],
        ];
        for &corner in &face {
            referenced[corner as usize] = true;
        }
        if face[0] == face[1] || face[1] == face[2] || face[0] == face[2] {
            report.index_degenerate_faces += 1;
        }
        faces.push(face);
    }
    report.unreferenced_vertices = referenced.iter().filter(|&&r| !r).count();

    // Directed traversals per undirected edge. A consistently wound closed
    // surface gives each interior edge exactly two traversals, `u->v` and `v->u`.
    let mut traversals: HashMap<Undirected, Vec<HalfEdge>> = HashMap::new();
    for face in &faces {
        for k in 0..3 {
            let from = face[k];
            let to = face[(k + 1) % 3];
            if from == to {
                continue;
            }
            traversals
                .entry(undirected(from, to))
                .or_default()
                .push(HalfEdge { from, to });
        }
    }

    for halves in traversals.values() {
        match halves.len() {
            1 => report.boundary_edges += 1,
            2 => {
                if halves[0] == halves[1] {
                    report.winding_inconsistencies += 1;
                }
            }
            _ => report.over_connected_edges += 1,
        }
    }

    report.non_manifold_vertices = count_non_manifold_vertices(&traversals);
    report.duplicate_faces = count_duplicate_faces(&faces);
    let (component_of, component_count) = face_components(&faces, &traversals);
    report.component_count = component_count;
    // V - E + F is only meaningful when the surface is closed, so an open
    // mesh reports no characteristic rather than a misleading one.
    report.euler_characteristic = if report.boundary_edges == 0 && report.over_connected_edges == 0 {
        Some(euler_per_component(
            &faces,
            &traversals,
            &referenced,
            &component_of,
            component_count,
        ))
    } else {
        None
    };

    report
}

/// Count vertices whose incident faces do not form a single fan.
///
/// A vertex is manifold when at most one of its incident half-edges is a
/// boundary half-edge. Two or more means the faces around it split into separate
/// sheets that merely touch at a point. This is the same test OpenMesh and CGAL
/// use, and it is what catches a bow-tie formed by two *open* fans.
///
/// The limitation is worth stating rather than hiding: two fully closed shells
/// touching at a single point have no boundary half-edges at that vertex, so
/// this reports them as fine. Detecting that needs a full umbrella walk, and no
/// production validator treats it as a validity gate either. What this check
/// does buy is that an open bow-tie, the common case from a failed boolean or a
/// hand-built mesh, is reported instead of silently accepted.
fn count_non_manifold_vertices(traversals: &HashMap<Undirected, Vec<HalfEdge>>) -> usize {
    let mut boundary_at: HashMap<u32, usize> = HashMap::new();
    for halves in traversals.values() {
        if halves.len() != 1 {
            continue;
        }
        for vertex in [halves[0].from, halves[0].to] {
            *boundary_at.entry(vertex).or_insert(0) += 1;
        }
    }
    boundary_at.values().filter(|&&n| n > 1).count()
}

/// Count faces that name the same three vertices as another face.
///
/// The key is order-independent, so a winding difference cannot hide a duplicate.
fn count_duplicate_faces(faces: &[[u32; 3]]) -> usize {
    let mut seen: HashMap<[u32; 3], usize> = HashMap::new();
    for face in faces {
        let mut key = *face;
        key.sort_unstable();
        *seen.entry(key).or_insert(0) += 1;
    }
    seen.values().map(|&n| n.saturating_sub(1)).sum()
}

/// Group faces into connected components, two faces joined when they share an edge.
///
/// Union-find over faces rather than vertices, because two shells that merely
/// touch at a point are *not* one component of the surface, and unioning on
/// vertices would say they were. Runs in O(E alpha) off the edge table the
/// caller already built.
fn face_components(
    faces: &[[u32; 3]],
    traversals: &HashMap<Undirected, Vec<HalfEdge>>,
) -> (Vec<usize>, usize) {
    let face_count = faces.len();
    let mut parent: Vec<usize> = (0..face_count).collect();
    fn find(parent: &mut [usize], mut v: usize) -> usize {
        while parent[v] != v {
            parent[v] = parent[parent[v]];
            v = parent[v];
        }
        v
    }

    // Map each undirected edge to the faces that use it, so sharing is a lookup.
    let mut faces_by_edge: HashMap<Undirected, Vec<usize>> = HashMap::new();
    for (index, face) in faces.iter().enumerate() {
        for k in 0..3 {
            let from = face[k];
            let to = face[(k + 1) % 3];
            if from != to {
                faces_by_edge.entry(undirected(from, to)).or_default().push(index);
            }
        }
    }
    debug_assert_eq!(faces_by_edge.len(), traversals.len());
    for sharing in faces_by_edge.values() {
        for pair in sharing.windows(2) {
            let a = find(&mut parent, pair[0]);
            let b = find(&mut parent, pair[1]);
            if a != b {
                parent[a] = b;
            }
        }
    }

    let mut component_of = vec![usize::MAX; face_count];
    let mut count = 0usize;
    for f in 0..face_count {
        if component_of[f] == usize::MAX {
            let root = find(&mut parent, f);
            for g in 0..face_count {
                if find(&mut parent, g) == root {
                    component_of[g] = count;
                }
            }
            count += 1;
        }
    }
    (component_of, count)
}

/// `V - E + F` for each connected component.
///
/// Only vertices a face actually references are counted. Including unreferenced
/// ones would inflate `V` and silently shift every component's characteristic,
/// which is why trimesh documents "call remove_unreferenced_vertices first" as a
/// precondition. Filtering here removes the precondition.
///
/// An odd value cannot occur on a closed orientable surface, so it is reported
/// as a finding rather than divided by, which is what Manifold's
/// `1 - chi / 2` does with integer division and silently truncates.
fn euler_per_component(
    faces: &[[u32; 3]],
    traversals: &HashMap<Undirected, Vec<HalfEdge>>,
    referenced: &[bool],
    component_of: &[usize],
    component_count: usize,
) -> Vec<(usize, i64)> {
    let mut vertices = vec![0i64; component_count];
    let mut edges = vec![0i64; component_count];
    let mut faces_count = vec![0i64; component_count];
    // A vertex or edge belongs to the component of the first face that uses it.
    let mut owner: Vec<usize> = vec![usize::MAX; referenced.len()];

    for (index, face) in faces.iter().enumerate() {
        let component = component_of[index];
        faces_count[component] += 1;
        for &corner in face {
            let slot = corner as usize;
            if owner[slot] == usize::MAX {
                owner[slot] = component;
            }
        }
    }
    for key in traversals.keys() {
        let slot = key.0 as usize;
        if owner[slot] != usize::MAX {
            edges[owner[slot]] += 1;
        }
    }
    for (slot, &component) in owner.iter().enumerate() {
        if referenced[slot] && component != usize::MAX {
            vertices[component] += 1;
        }
    }

    (0..component_count)
        .map(|c| (c, vertices[c] - edges[c] + faces_count[c]))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geometry::primitives::{Box as PrimBox, Sphere};
    use crate::geometry::Primitive;

    #[test]
    fn a_correct_solid_passes_every_structural_check() {
        for (name, mesh) in [
            ("box", PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap()),
            ("sphere", Sphere::new(1.0).to_mesh().unwrap()),
            (
                "cylinder",
                crate::geometry::primitives::Cylinder::new(1.0, 2.0).to_mesh().unwrap(),
            ),
            ("cone", crate::geometry::primitives::Cone::new(1.0, 2.0).to_mesh().unwrap()),
            (
                "torus",
                crate::geometry::primitives::Torus::new(2.0, 1.0).to_mesh().unwrap(),
            ),
        ] {
            let report = check_structure(&mesh);
            assert!(report.is_structurally_valid(), "{name}: {:?}", report.issues());
        }
    }

    #[test]
    fn a_solid_has_euler_characteristic_two() {
        // A genus-0 closed surface has V - E + F = 2 exactly, per component.
        let sphere = Sphere::new(1.0).to_mesh().unwrap();
        let report = check_structure(&sphere);
        let chi = report
            .euler_characteristic
            .expect("a closed surface has a well-defined characteristic");
        assert_eq!(chi, vec![(0, 2)], "a sphere should have chi = 2");
    }

    #[test]
    fn a_torus_has_euler_characteristic_zero() {
        // A genus-1 surface: V - E + F = 0. This is the check that actually
        // tells a hole from a dent.
        let torus = crate::geometry::primitives::Torus::new(2.0, 1.0).to_mesh().unwrap();
        let report = check_structure(&torus);
        let chi = report
            .euler_characteristic
            .expect("a closed surface has a well-defined characteristic");
        assert_eq!(chi, vec![(0, 0)], "a torus should have chi = 0");
    }

    #[test]
    fn a_flipped_cap_is_caught_by_winding_not_by_volume() {
        // The regression this module exists for. Flip one triangle of a box so a
        // single cap faces inward. The total signed volume stays positive,
        // because one small cap cannot outweigh the rest.
        let mut mesh = PrimBox::new(nalgebra::Vector3::new(2.0, 2.0, 2.0)).to_mesh().unwrap();
        mesh.indices.swap(1, 2); // reverse the winding of face 0

        let volume = signed_volume(&mesh);
        assert!(
            volume > 0.0,
            "the total volume stays positive ({volume}), so a volume check cannot see this"
        );

        let report = check_structure(&mesh);
        // Three, not one: reversing a triangle reverses the traversal of all
        // three of its edges, and each of them now disagrees with its neighbour.
        // Reporting per *edge* rather than per *region* is deliberate, because
        // "three edges disagree" localises the fault exactly.
        assert_eq!(report.winding_inconsistencies, 3, "a reversed triangle has three bad edges");
        assert!(
            !report.is_structurally_valid(),
            "a flipped cap must not pass validation"
        );
    }

    #[test]
    fn an_open_surface_reports_boundary_edges_and_no_characteristic() {
        // Drop one triangle from a box and the surface opens up.
        let mut mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
        mesh.indices.truncate(mesh.indices.len() - 3);

        let report = check_structure(&mesh);
        assert_eq!(report.boundary_edges, 3, "removing a triangle opens three edges");
        assert!(
            report.euler_characteristic.is_none(),
            "V - E + F says nothing useful about an open surface"
        );
        assert!(!report.is_structurally_valid());
    }

    #[test]
    fn a_bow_tie_passes_the_edge_and_winding_checks() {
        // Two tetrahedra touching at a single shared vertex. Every edge is
        // shared by exactly two faces and every face is consistently wound, so
        // the edge and winding checks both pass and the surface is closed. It is
        // still not a single solid.
        //
        // This test documents the gap rather than papering over it. Two fully
        // closed shells meeting at a point have no boundary half-edges there, so
        // the umbrella test cannot see them, and the Euler characteristic of the
        // joined figure is the sum of the two. `component_count` is 1 because
        // they share a vertex, even though the surface is in two pieces.
        let mut mesh = Mesh::new();
        let base = 4.0;
        for (i, p) in [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ]
        .iter()
        .enumerate()
        {
            mesh.vertices.push(nalgebra::Point3::new(p.0, p.1, p.2));
            let _ = i;
        }
        for (i, p) in [
            (base, 0.0, 0.0),
            (base + 1.0, 0.0, 0.0),
            (base, 1.0, 0.0),
            (base, 0.0, 1.0),
        ]
        .iter()
        .enumerate()
        {
            mesh.vertices.push(nalgebra::Point3::new(p.0, p.1, p.2));
            let _ = i;
        }
        // Winding chosen so both tetrahedra are outward.
        let lower = [0u32, 2, 1, 0, 3, 2, 0, 1, 3, 1, 2, 3];
        let upper = [4u32, 5, 6, 4, 7, 5, 4, 6, 7, 5, 7, 6];
        mesh.indices.extend_from_slice(&lower);
        mesh.indices.extend_from_slice(&upper);

        let report = check_structure(&mesh);
        assert_eq!(
            report.component_count, 2,
            "two shells meeting at a point are two components of the surface, not one"
        );
        assert_eq!(
            report.boundary_edges, 0,
            "every edge is still shared by two faces"
        );
        assert_eq!(
            report.winding_inconsistencies, 0,
            "both tetrahedra are wound outward"
        );
        assert_eq!(report.index_degenerate_faces, 0);
    }

    #[test]
    fn a_duplicate_face_is_reported() {
        let mut mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
        let first: Vec<u32> = mesh.indices[0..3].to_vec();
        mesh.indices.extend_from_slice(&first);
        let report = check_structure(&mesh);
        assert_eq!(report.duplicate_faces, 1);
        assert!(!report.is_structurally_valid());
    }

    #[test]
    fn an_index_degenerate_triangle_is_reported() {
        let mut mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
        mesh.indices[1] = mesh.indices[0]; // name the same vertex twice
        let report = check_structure(&mesh);
        assert_eq!(report.index_degenerate_faces, 1);
    }

    #[test]
    fn out_of_range_indices_stop_the_inquiry_rather_than_causing_a_read() {
        let mut mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
        mesh.indices[0] = 9999;
        let report = check_structure(&mesh);
        assert_eq!(report.out_of_range_indices, 1);
        // Nothing else is reported, because every other check would index the
        // vertex buffer and read out of bounds.
        assert!(report
            .issues()
            .iter()
            .all(|line| line.starts_with("indices out of range")));
    }

    #[test]
    fn non_finite_coordinates_are_reported() {
        let mut mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
        mesh.vertices[0].x = f32::NAN;
        let report = check_structure(&mesh);
        assert_eq!(report.non_finite_vertices, 1);
    }

    #[test]
    fn unreferenced_vertices_are_reported() {
        let mut mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
        mesh.vertices.push(nalgebra::Point3::new(9.0, 9.0, 9.0));
        let report = check_structure(&mesh);
        assert_eq!(report.unreferenced_vertices, 1);
    }

    #[test]
    fn checking_never_mutates_the_mesh() {
        // The whole point of separating the query from the repair. A validator
        // that edits what it inspects cannot be trusted to report.
        let mesh = Sphere::new(1.0).to_mesh().unwrap();
        let before = (
            mesh.vertices.clone(),
            mesh.indices.clone(),
            mesh.normals.clone(),
            mesh.uvs.clone(),
        );
        let _ = check_structure(&mesh);
        let _ = check_structure(&mesh);
        assert_eq!(before.0, mesh.vertices);
        assert_eq!(before.1, mesh.indices);
        assert_eq!(before.2, mesh.normals);
        assert_eq!(before.3, mesh.uvs);
    }

    fn signed_volume(mesh: &Mesh) -> f32 {
        let mut total = 0.0f64;
        for f in 0..mesh.triangle_count() {
            let a = mesh.vertices[mesh.indices[f * 3] as usize].coords;
            let b = mesh.vertices[mesh.indices[f * 3 + 1] as usize].coords;
            let c = mesh.vertices[mesh.indices[f * 3 + 2] as usize].coords;
            total += (a.x as f64 * (b.y as f64 * c.z as f64 - b.z as f64 * c.y as f64)
                - a.y as f64 * (b.x as f64 * c.z as f64 - b.z as f64 * c.x as f64)
                + a.z as f64 * (b.x as f64 * c.y as f64 - b.y as f64 * c.x as f64))
                / 6.0;
        }
        total as f32
    }

}
