//! Render-mesh derivation: one welded topology, two usable representations.
//!
//! A [`Mesh`] is welded so a closed solid stays manifold, which is what CAD
//! booleans, collision, and simulation need. A renderer needs the opposite: one
//! normal and one UV per output vertex, so a hard edge or a UV seam has to
//! produce a duplicated position.
//!
//! Those are not competing requirements, they are two views of one mesh, and
//! this module derives the render view from the topology view. The split is
//! driven by two independent signals:
//!
//! - **Marked sharp edges** (`Mesh::sharp_edges`). Blender's "Mark Sharp".
//!   A cube marks all twelve; a sphere marks none.
//! - **Dihedral angle.** Any edge steeper than the threshold is treated as
//!   sharp automatically, so a tessellated curve stays smooth without every edge
//!   being marked by hand.
//!
//! Positions are shared wherever a corner can share them, so a smooth surface
//! produces no duplication at all and a cube produces exactly what it needs.

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
}

/// Unit normal of a triangle, or zero if it is degenerate.
///
/// `pub(crate)` so the split tests can assert on winding directly rather than
/// duplicating the definition.
pub(crate) fn face_normal(a: Point3<f32>, b: Point3<f32>, c: Point3<f32>) -> Vector3<f32> {
    let cross = (b - a).cross(&(c - a));
    let length = cross.norm();
    if length > 1e-12 {
        cross / length
    } else {
        Vector3::zeros()
    }
}

/// Two faces are smoothing-compatible when they share an edge that is neither
/// marked sharp nor steeper than the threshold.
fn can_smooth(
    mesh: &Mesh,
    face_a: usize,
    face_b: usize,
    normals: &[Vector3<f32>],
    cos_threshold: f32,
) -> bool {
    if face_a == face_b {
        return true;
    }
    // Faces that share no edge must not be merged into one fan, whatever the
    // angle between them happens to be. Two unrelated surfaces meeting at a
    // shallow angle are still unrelated.
    let Some((ea, eb)) = shared_edge(mesh, face_a, face_b) else {
        return false;
    };
    if mesh.is_edge_sharp(ea, eb) {
        return false;
    }
    normals[face_a].dot(&normals[face_b]) >= cos_threshold
}

/// The edge two faces share, as a sorted vertex pair.
///
/// Returns `None` when the faces do not share an edge, which for a triangle
/// soup means they must not be merged into one smoothing fan.
fn shared_edge(mesh: &Mesh, face_a: usize, face_b: usize) -> Option<(u32, u32)> {
    let a = [
        mesh.indices[face_a * 3],
        mesh.indices[face_a * 3 + 1],
        mesh.indices[face_a * 3 + 2],
    ];
    let b = [
        mesh.indices[face_b * 3],
        mesh.indices[face_b * 3 + 1],
        mesh.indices[face_b * 3 + 2],
    ];

    for &va in &a {
        for &vb in &b {
            if va != vb {
                continue;
            }
            // The shared edge is (va, partner) where the partner is the vertex
            // adjacent to va in both faces.
            let a_next = a[(a.iter().position(|&x| x == va).unwrap() + 1) % 3];
            let a_prev = a[(a.iter().position(|&x| x == va).unwrap() + 2) % 3];
            let b_next = b[(b.iter().position(|&x| x == vb).unwrap() + 1) % 3];
            let b_prev = b[(b.iter().position(|&x| x == vb).unwrap() + 2) % 3];
            for candidate in [a_next, a_prev] {
                if candidate == b_next || candidate == b_prev {
                    return Some(if va < candidate {
                        (va, candidate)
                    } else {
                        (candidate, va)
                    });
                }
            }
        }
    }
    None
}

impl Mesh {
    /// Derive the render form of this mesh.
    ///
    /// Corners are grouped into smoothing fans per vertex: two faces sharing an
    /// unmarked edge at or below `smooth_angle_degrees` join the same fan, and
    /// every corner in a fan shares one output vertex whose normal is the fan
    /// average. A fan of one is a flat face, which is exactly what a cube needs,
    /// and a sphere has one fan per vertex, which is exactly what it needs too.
    ///
    /// `smooth_angle_degrees` is Blender's auto-smooth angle. 180.0 smooths
    /// everything not explicitly marked; 0.0 flattens everything; a negative
    /// value is treated as 180.0.
    pub fn split_for_render(&self, smooth_angle_degrees: f32) -> crate::geometry::render::RenderMesh {
        use crate::geometry::render::RenderMesh;

        let mut out = RenderMesh::default();
        if self.indices.is_empty() || self.indices.len() % 3 != 0 {
            return out;
        }

        let face_count = self.indices.len() / 3;
        let normals: Vec<Vector3<f32>> = (0..face_count)
            .map(|f| {
                face_normal(
                    self.vertices[self.indices[f * 3] as usize],
                    self.vertices[self.indices[f * 3 + 1] as usize],
                    self.vertices[self.indices[f * 3 + 2] as usize],
                )
            })
            .collect();

        let threshold = if smooth_angle_degrees < 0.0 {
            std::f32::consts::PI
        } else {
            smooth_angle_degrees.to_radians()
        };
        let cos_threshold = threshold.cos();

        // Incident faces per vertex.
        let mut incident: Vec<Vec<usize>> = vec![Vec::new(); self.vertices.len()];
        for face in 0..face_count {
            for k in 0..3 {
                incident[self.indices[face * 3 + k] as usize].push(face);
            }
        }

        // Partition each vertex's incident faces into smoothing fans.
        //
        // A face joins a fan when it is smooth with *any* face already in it,
        // not just the one that seeded the fan. That distinction is not
        // cosmetic: the faces around a vertex form a cycle, so on a valence-6
        // vertex the third face is adjacent to the second but not the first.
        // Comparing only against the seed splits one smooth ring into three
        // fans and turns a sphere faceted.
        let mut fans: Vec<Vec<Vec<usize>>> = vec![Vec::new(); self.vertices.len()];
        for (v, faces) in incident.iter().enumerate() {
            for &face in faces {
                let mut placed = false;
                for fan in fans[v].iter_mut() {
                    if fan
                        .iter()
                        .any(|&other| can_smooth(self, face, other, &normals, cos_threshold))
                    {
                        fan.push(face);
                        placed = true;
                        break;
                    }
                }
                if !placed {
                    fans[v].push(vec![face]);
                }
            }
        }

        // fan_of[v][face] -> index of the fan within fans[v].
        let mut fan_of: Vec<HashMap<usize, usize>> = vec![HashMap::new(); self.vertices.len()];
        for (v, vertex_fans) in fans.iter().enumerate() {
            for (fi, fan) in vertex_fans.iter().enumerate() {
                for &face in fan {
                    fan_of[v].insert(face, fi);
                }
            }
        }

        // Averaged normal per fan, computed once so all its corners agree.
        let mut fan_normal: Vec<Vec<Vector3<f32>>> = vec![Vec::new(); self.vertices.len()];
        for (v, vertex_fans) in fans.iter().enumerate() {
            for fan in vertex_fans {
                let mut acc = Vector3::zeros();
                for &face in fan {
                    acc += normals[face];
                }
                let length = acc.norm();
                // A fan of coincident faces averages to zero; fall back to the
                // first face normal so the output is never a zero vector, which
                // downstream shading turns into black.
                let averaged = if length > 1e-12 {
                    acc / length
                } else {
                    normals[fan[0]]
                };
                fan_normal[v].push(averaged);
            }
        }

        // Emit one output vertex per (source vertex, fan).
        let has_face_uvs = self.face_uvs.len() == face_count;
        let has_vertex_uvs = self.uvs.len() == self.vertices.len();
        let mut slot: Vec<Vec<u32>> = vec![Vec::new(); self.vertices.len()];
        let mut emitted: HashMap<(u32, usize), u32> = HashMap::new();

        for face in 0..face_count {
            for k in 0..3 {
                let v = self.indices[face * 3 + k] as usize;
                let fan = fan_of[v].get(&face).copied().unwrap_or(0);

                let index = match emitted.get(&(v as u32, fan)) {
                    Some(&index) => index,
                    None => {
                        let index = out.vertices.len() as u32;
                        out.vertices.push(self.vertices[v]);
                        out.normals.push(fan_normal[v][fan]);
                        let uv = if has_face_uvs {
                            self.face_uvs[face][k]
                        } else if has_vertex_uvs {
                            self.uvs[v]
                        } else {
                            (0.0, 0.0)
                        };
                        out.uvs.push(uv);
                        if slot[v].len() <= fan {
                            slot[v].resize(fan + 1, index);
                        }
                        slot[v][fan] = index;
                        emitted.insert((v as u32, fan), index);
                        index
                    }
                };
                out.indices.push(index);
            }
        }

        if self.materials.len() >= face_count {
            out.materials.extend_from_slice(&self.materials[..face_count]);
        } else {
            out.materials = vec![0; face_count];
        }

        out
    }
}
