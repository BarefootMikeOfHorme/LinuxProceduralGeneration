//! Render-mesh derivation: one welded topology, two usable representations.
//!
//! A [`Mesh`] is welded so a closed solid stays manifold, which is what CAD
//! booleans, collision, and simulation need. A renderer needs the opposite: one
//! normal and one UV per output vertex, so a hard edge or a UV seam has to
//! produce a duplicated position.
//!
//! Those are not competing requirements, they are two views of one mesh, and
//! this module derives the render view from the topology view.
//!
//! # How a corner gets its normal
//!
//! Each face corner ends up in exactly one output vertex, and two corners share
//! an output vertex exactly when they agree on both normal and UV. Three rules
//! decide the normal:
//!
//! - **Marked sharp edge** (`Mesh::sharp_edges`, Blender's "Mark Sharp"). A
//!   corner touching a marked edge is pinned to its own face's normal. This is
//!   deliberately *local*: it does not consult the rest of the ring.
//! - **Dihedral angle.** Neighbouring faces steeper than the threshold are not
//!   averaged together, so a tessellated curve stays smooth without every edge
//!   being marked by hand.
//! - **Otherwise**, a corner averages the faces it is smooth with.
//!
//! # Why the sharp rule is local, and not a flood fill
//!
//! The obvious alternative is to flood-fill smoothing groups outward from each
//! corner across non-sharp edges, which is how "connected components" reads on
//! paper. It is wrong, and wrong in a way that is invisible in a vertex count.
//!
//! The faces around a vertex form a **cycle**, so removing one link from it
//! leaves it connected. Flood fill therefore walks straight around a marked edge
//! and reunites the two faces it was supposed to separate. On a sphere, marking
//! a single edge sharp then changes nothing at all: no crease, no split, not one
//! extra vertex. An artist marks an edge, sees no result, and concludes the
//! feature is broken.
//!
//! Pinning the marked edge's own corners sidesteps the cycle entirely. The
//! crease appears along the whole edge, endpoints included, which is what
//! marking an edge is supposed to mean, and the answer no longer depends on how
//! the surrounding ring happens to wrap.
//!
//! Grouping by final attribute value is also what Assimp does, for the same
//! reason: it splits on a differing `(position, uv, normal)` triple and has no
//! smoothing-group traversal to get wrong.

use crate::geometry::Mesh;
use nalgebra::{Point3, Vector3};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// A render-ready mesh: one normal and one UV per vertex.
///
/// Deliberately a distinct type rather than another `Mesh`. A render mesh is not
/// manifold, and making that a type error stops it being fed back into CSG,
/// collision, or CAD boolean work by accident.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct RenderMesh {
    /// Vertex positions, split at seams and sharp edges.
    pub vertices: Vec<Point3<f32>>,

    /// One normal per vertex: the fan average when smoothed, the face normal
    /// when flat.
    pub normals: Vec<Vector3<f32>>,

    /// One UV per vertex, taken from `Mesh::face_uvs` when that is present.
    pub uvs: Vec<(f32, f32)>,

    /// Triangle indices over the split vertices.
    pub indices: Vec<u32>,

    /// Material assignment per face, carried through unchanged.
    pub materials: Vec<u32>,
}

impl RenderMesh {
    /// Number of output vertices. Larger than the source mesh wherever a seam
    /// or crease forced a split.
    pub fn vertex_count(&self) -> usize {
        self.vertices.len()
    }

    /// Total triangles. Equal to the source mesh: the split duplicates
    /// vertices, it never changes topology.
    pub fn triangle_count(&self) -> usize {
        self.indices.len() / 3
    }

    /// How many distinct positions the split produced.
    ///
    /// Equal to `vertex_count()` for a mesh that needed no split, and larger
    /// once creases and seams start duplicating. Exposed because "did the split
    /// actually do anything" is the first question a caller has, and answering
    /// it should not mean writing a loop.
    pub fn unique_position_count(&self) -> usize {
        let mut seen: HashMap<(u32, u32, u32), ()> = HashMap::new();
        for v in &self.vertices {
            seen.insert((v.x.to_bits(), v.y.to_bits(), v.z.to_bits()), ());
        }
        seen.len()
    }
}

/// Unit normal of a triangle, or zero if it is degenerate.
///
/// Test-only: the split tests assert on winding directly rather than
/// duplicating this definition. Production code uses `wide_face_normals`, which
/// needs f64.
#[cfg(test)]
pub(crate) fn face_normal(a: Point3<f32>, b: Point3<f32>, c: Point3<f32>) -> Vector3<f32> {
    let cross = (b - a).cross(&(c - a));
    let length = cross.norm();
    if length > 1e-12 {
        cross / length
    } else {
        Vector3::zeros()
    }
}

/// Signed volume of a mesh: positive means outward winding.
///
/// Test-only: lets the primitives tests prove a shape is not inside-out. That
/// defect is invisible in a vertex count but inverts lighting and every
/// inside/outside answer derived from the mesh, so it needs a direct assertion.
#[cfg(test)]
pub(crate) fn signed_volume(mesh: &Mesh) -> f64 {
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
    total
}

/// Edge key for an unordered vertex pair.
fn edge_key(a: u32, b: u32) -> (u32, u32) {
    if a < b {
        (a, b)
    } else {
        (b, a)
    }
}

/// Which faces touch each edge, keyed by unordered vertex pair.
fn edge_face_table(mesh: &Mesh, face_count: usize) -> HashMap<(u32, u32), Vec<usize>> {
    let mut table: HashMap<(u32, u32), Vec<usize>> = HashMap::new();
    for f in 0..face_count {
        for k in 0..3 {
            let a = mesh.indices[f * 3 + k];
            let b = mesh.indices[f * 3 + (k + 1) % 3];
            if a == b {
                continue;
            }
            table.entry(edge_key(a, b)).or_default().push(f);
        }
    }
    table
}

/// Position of `vertex` inside `face`, as a corner index 0..3.
fn corner_of(mesh: &Mesh, face: usize, vertex: u32) -> Option<usize> {
    (0..3).find(|&k| mesh.indices[face * 3 + k] == vertex)
}

/// Which smoothing group a corner belongs to.
///
/// A pinned corner is alone on its face; an averaged corner shares its fan.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum Group {
    /// Touches a marked sharp edge, so it keeps its own face normal.
    Pinned(usize),
    /// Free to average, and does so across `usize` faces.
    Fan(usize),
}

/// Replace `-0.0` with `0.0` in a normal.
///
/// A cross product produces signed zeros readily. LPG's own +Z box quad is the
/// worked example: its two triangles are coplanar, so they ought to yield the
/// same normal, and they do — as `(0, 0, 1)` and `(0, -0, 1)`. The directions are
/// identical and `0.0 == -0.0` is true, but the bit patterns differ, so a
/// bitwise corner key splits two corners that are in fact the same. That defeats
/// the entire keyed strategy on a case that should have been free.
///
/// The fix is to canonicalise rather than to loosen the comparison. Loosening
/// would mean a tolerance on the normal, which is precisely the thing that
/// swallows a 0.33-degree crease. Canonicalising keeps the contract exact —
/// "the same bits" still means the same bits — while making those bits mean the
/// same thing for two normals that agree, which they already did.
///
/// Nothing is lost. `-0.0` carries no directional information: the IEEE-754
/// comparison `-0.0 == 0.0` is true by definition, and only the sign bit differs.
fn canonical_normal(mut n: Vector3<f32>) -> Vector3<f32> {
    // The comparison covers both 0.0 and -0.0, and is false for NaN, which must
    // not be silently turned into a direction. Written as three statements
    // because an array of simultaneous mutable borrows of three fields is not a
    // thing the borrow checker will allow, and this is not worth a helper type.
    if n.x == 0.0 {
        n.x = 0.0;
    }
    if n.y == 0.0 {
        n.y = 0.0;
    }
    if n.z == 0.0 {
        n.z = 0.0;
    }
    n
}

/// How two corners are decided to be the same vertex.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum CornerKeying {
    /// On the source vertex, the smoothing group, and the UV.
    ///
    /// Conservative, and correct by construction: a pinned corner is alone on its
    /// face by identity, so it can never merge with the corner across the marked
    /// edge. It is also lossy in the other direction — the two triangles of a
    /// coplanar face are different faces, so different groups, so they never
    /// merge even when they are the same quad and should.
    SmoothingGroup,
    /// On the source vertex, the resolved normal, and the UV, compared exactly.
    ///
    /// Carries the same crease information as `SmoothingGroup` because the normal
    /// is derived from the group, but it no longer distinguishes two faces that
    /// resolved to the same normal. That is the whole difference, and it is worth
    /// 36 corners down to 24 on a cube.
    Attributes,
}

/// Identity of one output vertex.
///
/// `uv` and, under [`CornerKeying::Attributes`], `normal` are stored as bit
/// patterns rather than floats so the comparison is bitwise. A float key would
/// need `PartialEq` on `f32`, which has three legal NaN representations that are
/// not `==` to themselves, and which would silently split a corner in two.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct CornerKey {
    vertex: u32,
    group: Group,
    uv: (u32, u32),
    normal: (u32, u32, u32),
}

/// Build the key for one corner under the given strategy.
fn corner_key(corner: &Corner, keying: CornerKeying) -> CornerKey {
    let uv = (corner.uv.0.to_bits(), corner.uv.1.to_bits());
    match keying {
        CornerKeying::SmoothingGroup => CornerKey {
            vertex: corner.vertex,
            group: corner.group,
            uv,
            normal: (0, 0, 0),
        },
        CornerKeying::Attributes => CornerKey {
            vertex: corner.vertex,
            group: Group::Pinned(0),
            uv,
            normal: (
                corner.normal.x.to_bits(),
                corner.normal.y.to_bits(),
                corner.normal.z.to_bits(),
            ),
        },
    }
}

/// One corner of the output mesh, fully resolved: where it points, which way it
/// faces, and where it lands in UV space.
#[derive(Debug, Clone, Copy)]
struct Corner {
    vertex: u32,
    normal: Vector3<f32>,
    uv: (f32, f32),
    group: Group,
}

/// Everything the two split strategies share.
///
/// The expensive part of splitting — face normals, smoothing fans, fan normals —
/// does not depend on how corners are keyed, so it is computed once here and
/// both strategies read from it. Two copies of this logic would be two chances
/// for the strategies to disagree about a mesh, which is precisely the kind of
/// drift that makes an "equivalent" second code path a lie.
struct CornerAttributes {
    corners: Vec<Corner>,
    face_count: usize,
}

impl Mesh {
    /// Derive the render form of this mesh.
    ///
    /// Corners are emitted in face order and merged when they share a source
    /// vertex, a smoothing group, and a UV. So a sphere, which has no sharp
    /// edges, continuous UVs, and only shallow angles, comes out with exactly
    /// one output vertex per input vertex; a cube, with all twelve edges marked
    /// and six disjoint UV islands, comes out fully split and flat.
    ///
    /// `smooth_angle_degrees` is Blender's auto-smooth angle. 180.0 smooths
    /// everything not explicitly marked; 0.0 flattens everything; a negative
    /// value is treated as 180.0.
    pub fn split_for_render(&self, smooth_angle_degrees: f32) -> RenderMesh {
        self.finish_render(self.corner_attributes(smooth_angle_degrees), CornerKeying::SmoothingGroup)
    }

    /// Derive the render form, merging corners on `(position, normal, uv)`
    /// compared **bit for bit**.
    ///
    /// This is MikkTSpace's rule, and it is the rule glTF's reference cube obeys:
    /// `Box.gltf` ships 24 positions for 36 indices, meaning the two triangles of
    /// each face share their corner attributes. [`Self::split_for_render`] cannot
    /// get there on a cube, because it keys on the smoothing group and the two
    /// triangles of a face are different groups. It emits 36.
    ///
    /// # Why the comparison is exact and not a tolerance
    ///
    /// A crease is exactly the case where the normal differs between two corners
    /// sharing a position, so the normal is the one field that must never be
    /// quantised. Put it on a grid of step `h` and two normals separated by
    /// `h / sqrt(3)` collapse onto the same key; at `h = 1e-2` that is 0.33
    /// degrees, and a 0.33-degree crease across a 2000-unit model is invisible.
    /// Every other field — position, UV — is either genuinely shared or genuinely
    /// not, and welding those is what the key is for. So there is no tolerance to
    /// tune and no way to mis-tune it; a crease survives because its normals are
    /// not the same bits, and two corners merge exactly when nothing about them
    /// needs to be distinguished.
    ///
    /// The cost of exactness is that a *nearly* coplanar pair does not merge: the
    /// face normals of a non-axis-aligned quad are computed from different vertex
    /// triples, and in f32 those can differ in the last bit. That is not a defect
    /// to be papered over with an epsilon — it is the behaviour of the reference
    /// implementation, and matching it is the point. Meshes whose faces are
    /// exactly coplanar, which includes every axis-aligned solid this crate
    /// generates, merge fully.
    ///
    /// # What it costs
    ///
    /// Nothing, as far as this mesh is concerned: the attribute tuple is
    /// complete, so every corner that merges shares the position, the normal and
    /// the UV, and the render form is the same mesh drawn with fewer vertices.
    /// The count can only go down, never up, which
    /// [`Self::split_for_render_keyed_never_grows`] asserts for every primitive.
    pub fn split_for_render_keyed(&self, smooth_angle_degrees: f32) -> RenderMesh {
        self.finish_render(self.corner_attributes(smooth_angle_degrees), CornerKeying::Attributes)
    }

    /// Resolve every corner of every face: position, normal, UV, smoothing group.
    fn corner_attributes(&self, smooth_angle_degrees: f32) -> CornerAttributes {
        let mut corners = Vec::new();
        let face_count = self.indices.len() / 3;
        if self.indices.is_empty() || self.indices.len() % 3 != 0 {
            return CornerAttributes { corners, face_count: 0 };
        }

        // See `wide_face_normals` for why this is f64 arithmetic on f32
        // positions, and why widening an f32 result is not good enough.
        let normals = self.wide_face_normals();
        let normals32: Vec<Vector3<f32>> = normals
            .iter()
            .map(|n| Vector3::new(n.x as f32, n.y as f32, n.z as f32))
            .collect();

        let threshold = if smooth_angle_degrees < 0.0 {
            std::f64::consts::PI
        } else {
            (smooth_angle_degrees as f64).to_radians()
        };
        let cos_threshold = threshold.cos();

        let table = edge_face_table(self, face_count);
        let fans = self.build_fans(&normals, cos_threshold, &table, face_count);

        // Averaged normal per fan, computed once so every corner in it agrees.
        let mut fan_normal: Vec<Vec<Vector3<f32>>> = vec![Vec::new(); self.vertices.len()];
        for (v, vertex_fans) in fans.iter().enumerate() {
            for fan in vertex_fans {
                let mut acc = Vector3::zeros();
                for &face in fan {
                    acc += normals32[face];
                }
                let length = acc.norm();
                // Coincident faces average to a zero vector, which downstream
                // shading turns black. Fall back to the first face normal.
                fan_normal[v].push(if length > 1e-12 {
                    acc / length
                } else {
                    normals32[fan[0]]
                });
            }
        }

        // Fan index for each (vertex, face) pair.
        let mut fan_of: Vec<HashMap<usize, usize>> = vec![HashMap::new(); self.vertices.len()];
        for (v, vertex_fans) in fans.iter().enumerate() {
            for (fi, fan) in vertex_fans.iter().enumerate() {
                for &face in fan {
                    fan_of[v].insert(face, fi);
                }
            }
        }

        let has_face_uvs = self.face_uvs.len() == face_count;
        let has_vertex_uvs = self.uvs.len() == self.vertices.len();
        corners.reserve(self.indices.len());

        for face in 0..face_count {
            for k in 0..3 {
                let v = self.indices[face * 3 + k];
                let vi = v as usize;

                // A corner touching a marked edge keeps its own face normal. Both
                // edges at this corner are checked, so an edge marked from either
                // direction still pins the corner.
                let ahead = self.indices[face * 3 + (k + 1) % 3];
                let behind = self.indices[face * 3 + (k + 2) % 3];
                let pinned = self.is_edge_sharp(edge_key(v, ahead).0, edge_key(v, ahead).1)
                    || self.is_edge_sharp(edge_key(v, behind).0, edge_key(v, behind).1);

                let group = if pinned {
                    Group::Pinned(face)
                } else {
                    Group::Fan(fan_of[vi].get(&face).copied().unwrap_or(0))
                };
                let normal = canonical_normal(match group {
                    Group::Pinned(_) => normals32[face],
                    Group::Fan(fi) => fan_normal[vi][fi],
                });

                let uv = if has_face_uvs {
                    self.face_uvs[face][k]
                } else if has_vertex_uvs {
                    self.uvs[vi]
                } else {
                    (0.0, 0.0)
                };

                corners.push(Corner { vertex: v, normal, uv, group });
            }
        }

        CornerAttributes { corners, face_count }
    }

    /// Walk resolved corners in face order, merging according to `keying`.
    fn finish_render(&self, attributes: CornerAttributes, keying: CornerKeying) -> RenderMesh {
        let mut out = RenderMesh::default();
        let CornerAttributes { corners, face_count } = attributes;
        if face_count == 0 {
            return out;
        }

        let mut emitted: HashMap<CornerKey, u32> = HashMap::new();
        for corner in &corners {
            let key = corner_key(corner, keying);
            let index = match emitted.get(&key) {
                Some(&index) => index,
                None => {
                    let index = out.vertices.len() as u32;
                    out.vertices.push(self.vertices[corner.vertex as usize]);
                    out.normals.push(corner.normal);
                    out.uvs.push(corner.uv);
                    emitted.insert(key, index);
                    index
                }
            };
            out.indices.push(index);
        }

        if self.materials.len() >= face_count {
            out.materials
                .extend_from_slice(&self.materials[..face_count]);
        } else {
            out.materials = vec![0; face_count];
        }

        out
    }

    /// Face normals widened to f64, computed from the f32 positions.
    ///
    /// Doing this in f32 fails three times over, and every failure is silent.
    ///
    /// An f32 dot product saturates at 1.0, so the many near-coplanar triangles
    /// packed around a pole compare exactly equal, and a zero-degree threshold
    /// then refuses to flatten the mesh it was asked to flatten.
    ///
    /// An f32 cross product rounds genuinely distinct normals onto each other for
    /// faces that share a latitude, so those merge as well.
    ///
    /// And widening an f32 result fixes none of it: the rounding error is
    /// preserved, leaving a norm of about 1.0000000858, and the dot product of
    /// two such "unit" vectors comes out slightly *above* 1.0. The positions must
    /// be widened before any arithmetic touches them too, because `(b.x - a.x) as
    /// f64` subtracts in f32 and throws away about half the digits.
    fn wide_face_normals(&self) -> Vec<Vector3<f64>> {
        let face_count = self.indices.len() / 3;
        let mut normals = Vec::with_capacity(face_count);
        for f in 0..face_count {
            let a = self.vertices[self.indices[f * 3] as usize].coords;
            let b = self.vertices[self.indices[f * 3 + 1] as usize].coords;
            let c = self.vertices[self.indices[f * 3 + 2] as usize].coords;
            let a = Vector3::new(a.x as f64, a.y as f64, a.z as f64);
            let b = Vector3::new(b.x as f64, b.y as f64, b.z as f64);
            let c = Vector3::new(c.x as f64, c.y as f64, c.z as f64);
            let cross = (b - a).cross(&(c - a));
            let length = cross.norm();
            normals.push(if length > 1e-12 {
                cross / length
            } else {
                // A degenerate face has no meaningful normal. Leaving it zero
                // makes every angle test against it fail, so it splits from its
                // neighbours rather than silently averaging with them.
                Vector3::zeros()
            });
        }
        normals
    }

    /// Averaging fans per vertex: the groups a non-pinned corner averages over.
    ///
    /// The faces around a vertex form a ring. Each link in that ring is smooth
    /// when the two faces it joins are no steeper than the threshold, and the
    /// fans are the maximal runs of smooth links. One cut in a ring therefore
    /// leaves a single fan spanning every face, and it takes two cuts to actually
    /// divide one; that is correct, and it is also why the sharp-edge rule is
    /// applied by pinning corners in `split_for_render` rather than by cutting
    /// here.
    fn build_fans(
        &self,
        normals: &[Vector3<f64>],
        cos_threshold: f64,
        table: &HashMap<(u32, u32), Vec<usize>>,
        face_count: usize,
    ) -> Vec<Vec<Vec<usize>>> {
        let mut fans: Vec<Vec<Vec<usize>>> = vec![Vec::new(); self.vertices.len()];
        for v in 0..self.vertices.len() {
            let cycle = self.corner_cycle(v, table, face_count);
            if cycle.is_empty() {
                continue;
            }

            let count = cycle.len();
            // smooth_link[i] describes the ring edge between cycle[i] and the
            // next entry, wrapping at the end.
            let mut smooth_link = vec![true; count];
            if count > 1 {
                for i in 0..count {
                    let here = cycle[i].0;
                    let next = cycle[(i + 1) % count].0;
                    if normals[here].dot(&normals[next]) < cos_threshold {
                        smooth_link[i] = false;
                    }
                }
            }

            if smooth_link.iter().all(|&s| s) {
                // Unbroken ring: the whole fan averages together.
                fans[v].push(cycle.iter().map(|entry| entry.0).collect());
                continue;
            }

            // Cut the ring into arcs, one per cut, each walked forward from it.
            for i in 0..count {
                if smooth_link[i] {
                    continue;
                }
                let mut arc = Vec::new();
                let mut k = (i + 1) % count;
                loop {
                    arc.push(cycle[k].0);
                    if smooth_link[k] {
                        k = (k + 1) % count;
                    } else {
                        break;
                    }
                }
                fans[v].push(arc);
            }
        }
        fans
    }

    /// Walk the faces around `vertex` in order, returning
    /// `(face, corner, exit_edge_vertex)` triples.
    ///
    /// Consecutive entries share an edge containing `vertex`, and
    /// `exit_edge_vertex` names the edge leading onward, so the caller can judge
    /// each link in the ring without re-deriving it.
    ///
    /// Tracking the edge that was *entered* is what keeps the walk going
    /// forward. A face has two edges at `vertex`; taking the `(corner + 1)` one
    /// unconditionally re-selects the edge just crossed, and the walk ping-pongs
    /// between two faces forever, yielding a ring of length 2 that silently
    /// smooths corners it should split.
    fn corner_cycle(
        &self,
        vertex: usize,
        table: &HashMap<(u32, u32), Vec<usize>>,
        face_count: usize,
    ) -> Vec<(usize, usize, u32)> {
        let target = vertex as u32;
        let Some(start_face) =
            (0..face_count).find(|&f| (0..3).any(|k| self.indices[f * 3 + k] == target))
        else {
            return Vec::new();
        };
        let Some(start_corner) = corner_of(self, start_face, target) else {
            return Vec::new();
        };

        // Either direction is a valid ring, so pick one and stay with it.
        let mut exit_vertex = self.indices[start_face * 3 + (start_corner + 1) % 3];
        let mut cycle = vec![(start_face, start_corner, exit_vertex)];
        let mut current = (start_face, start_corner);

        // Bounded by the face count: a well-formed mesh closes its ring first,
        // and this keeps a malformed one from looping forever.
        for _ in 0..face_count {
            let face = current.0;
            let neighbours = table
                .get(&edge_key(target, exit_vertex))
                .map(|faces| faces.as_slice())
                .unwrap_or(&[]);

            let next = neighbours
                .iter()
                .copied()
                .filter(|&f| f != face)
                .find_map(|f| corner_of(self, f, target).map(|k| (f, k)));

            let Some((next_face, next_corner)) = next else {
                break;
            };
            if next_face == start_face {
                break;
            }

            // Leave by the edge at `vertex` that is not the one just crossed.
            let ahead = self.indices[next_face * 3 + (next_corner + 1) % 3];
            let behind = self.indices[next_face * 3 + (next_corner + 2) % 3];
            let next_exit = if ahead == exit_vertex { behind } else { ahead };

            cycle.push((next_face, next_corner, next_exit));
            exit_vertex = next_exit;
            current = (next_face, next_corner);
        }

        cycle
    }
}
