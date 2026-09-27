//! Geometry primitives and operations
//!
//! This module provides basic geometric primitives (box, sphere, cylinder, etc.)
//! and procedural operations (extrude, revolve, loft).

use nalgebra::{Point3, Vector3};
use serde::{Deserialize, Serialize};
use crate::{Result, GeometryError};

/// Angle for step `index` of `count` around a full turn, in radians.
///
/// Computed in f64 and only narrowed by the caller, deliberately. A wrapped
/// primitive evaluates this at `index == count`, where the angle is `2*pi` and
/// `sin` is about -2.4e-16 rather than 0. Doing the same arithmetic in f32 puts
/// the error at the f32 half-ulp near 2*pi, which is about 2.4e-7: nine orders of
/// magnitude worse, and enough to leave a wrap column a hair away from column 0
/// instead of on it.
///
/// That is a type bug, not a tolerance problem, and it is worth naming because
/// the symptom looks exactly like one. An earlier revision of the cylinder, cone
/// and torus closed their seams with a spare column of vertices, on the theory
/// that the duplicate needed a weld tolerance to absorb. It did not need a
/// tolerance at all: it needed the index-level wrap *and* f64 angles, and the
/// spare column was a construction bug that no tolerance fixes.
pub(crate) fn wrap_angle(index: u32, count: u32) -> f64 {
    debug_assert!(count > 0, "a wrap angle needs a positive segment count");
    std::f64::consts::TAU * f64::from(index) / f64::from(count)
}

/// Angle for step `index` of `count` across a half turn, in radians, in f64.
///
/// See [`wrap_angle`] for why the precision matters.
pub(crate) fn half_turn_angle(index: u32, count: u32) -> f64 {
    debug_assert!(count > 0, "a half-turn angle needs a positive segment count");
    std::f64::consts::PI * f64::from(index) / f64::from(count)
}

pub mod primitives;
pub mod operations;
pub mod render;

#[cfg(test)]
mod primitives_seam_tests;
#[cfg(test)]
mod render_keyed_tests;
#[cfg(test)]
mod render_tests;

#[cfg(test)]
mod render_winding_tests;

pub use render::RenderMesh;

pub use primitives::{Box, Sphere, Cylinder, Cone, Torus};
pub use operations::{extrude, revolve, loft, sweep};

/// Core mesh representation.
///
/// This is the **topology** mesh: positions are welded, so a closed solid stays
/// manifold and remains usable for collision, simulation, and CAD boolean work.
/// Rendering needs something different, because one position cannot carry two
/// normals or two UVs at once. Rather than compromise one for the other, this
/// type records *where a corner disagrees with its vertex* in `sharp_edges` and
/// `face_uvs`, and `render::split_for_render` derives the render form.
///
/// That division is the same one Blender draws: it keeps custom split normals
/// per face corner and marks edges sharp, rather than duplicating positions in
/// the topology buffer. Assimp takes the opposite approach, duplicating
/// vertices outright and documenting `aiProcess_JoinIdenticalVertices` as
/// incompatible with smooth normals. Both are workable; keeping the welded form
/// is the one that also serves CAD, which is a requirement here.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Mesh {
    /// Vertex positions. Welded: shared by every face touching this point.
    pub vertices: Vec<Point3<f32>>,

    /// Vertex normals, averaged across adjacent faces. A hard edge needs
    /// `sharp_edges` or a per-corner value to survive.
    pub normals: Vec<Vector3<f32>>,

    /// UV coordinates, one per vertex.
    ///
    /// A single UV per vertex cannot describe a surface needing different
    /// coordinates either side of an edge, which is every UV seam. Primitives
    /// that need that store it in `face_uvs`; this remains the smooth,
    /// continuous parameterisation.
    pub uvs: Vec<(f32, f32)>,

    /// Triangle indices (triplets)
    pub indices: Vec<u32>,

    /// Material assignments per face
    pub materials: Vec<u32>,

    /// Edges that smoothing must not cross, as sorted vertex pairs.
    ///
    /// This is Blender's "Mark Sharp". A listed edge gets its own face normal on
    /// each side, so a cube keeps crisp corners while a sphere, with no marked
    /// edges, stays smooth. `split_for_render` also treats an edge as sharp when
    /// its dihedral angle exceeds the threshold, so marking is additive rather
    /// than the only mechanism.
    pub sharp_edges: Vec<(u32, u32)>,

    /// UVs per face corner: three per triangle, parallel to `indices`.
    ///
    /// Empty means "fall back to `uvs`", which preserves the previous behaviour
    /// for any mesh that has not opted in. When present it takes precedence,
    /// because it is the only representation that can express a seam.
    pub face_uvs: Vec<[(f32, f32); 3]>,
}

impl Mesh {
    /// Create a new empty mesh
    pub fn new() -> Self {
        Self {
            vertices: Vec::new(),
            normals: Vec::new(),
            uvs: Vec::new(),
            indices: Vec::new(),
            materials: Vec::new(),
            sharp_edges: Vec::new(),
            face_uvs: Vec::new(),
        }
    }

    /// Mark an edge sharp so smoothing will not cross it.
    ///
    /// The pair is stored sorted, so the same edge is a single entry whichever
    /// order it is added from.
    pub fn mark_edge_sharp(&mut self, a: u32, b: u32) {
        if a == b {
            return;
        }
        let key = if a < b { (a, b) } else { (b, a) };
        if !self.sharp_edges.contains(&key) {
            self.sharp_edges.push(key);
        }
    }

    /// Whether an edge is marked sharp.
    pub fn is_edge_sharp(&self, a: u32, b: u32) -> bool {
        if a == b {
            return false;
        }
        let key = if a < b { (a, b) } else { (b, a) };
        self.sharp_edges.contains(&key)
    }

    /// Get the number of vertices
    pub fn vertex_count(&self) -> usize {
        self.vertices.len()
    }

    /// Get the number of triangles
    pub fn triangle_count(&self) -> usize {
        self.indices.len() / 3
    }

    /// Calculate bounding box
    pub fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        if self.vertices.is_empty() {
            return (Point3::origin(), Point3::origin());
        }

        let mut min = self.vertices[0];
        let mut max = self.vertices[0];

        for v in &self.vertices {
            min.x = min.x.min(v.x);
            min.y = min.y.min(v.y);
            min.z = min.z.min(v.z);
            max.x = max.x.max(v.x);
            max.y = max.y.max(v.y);
            max.z = max.z.max(v.z);
        }

        (min, max)
    }

    /// Compute smooth normals
    pub fn compute_normals(&mut self) {
        self.normals.clear();
        self.normals.resize(self.vertices.len(), Vector3::zeros());

        // Accumulate face normals
        for chunk in self.indices.chunks(3) {
            let i0 = chunk[0] as usize;
            let i1 = chunk[1] as usize;
            let i2 = chunk[2] as usize;

            let v0 = self.vertices[i0];
            let v1 = self.vertices[i1];
            let v2 = self.vertices[i2];

            let edge1 = v1 - v0;
            let edge2 = v2 - v0;
            let normal = edge1.cross(&edge2);

            self.normals[i0] += normal;
            self.normals[i1] += normal;
            self.normals[i2] += normal;
        }

        // Normalize
        for normal in &mut self.normals {
            *normal = normal.normalize();
        }
    }

    /// Merge another mesh into this one
    pub fn merge(&mut self, other: &Mesh) {
        let vertex_offset = self.vertices.len() as u32;
        let face_offset = self.indices.len();

        self.vertices.extend_from_slice(&other.vertices);
        self.normals.extend_from_slice(&other.normals);
        self.uvs.extend_from_slice(&other.uvs);

        // Offset indices
        for &idx in &other.indices {
            self.indices.push(idx + vertex_offset);
        }

        self.materials.extend_from_slice(&other.materials);

        // Per-corner UVs stay per corner, and sharp edges move with their
        // vertices. Dropping either would silently attach UVs to the wrong face
        // or lose a crease at the seam between the two meshes.
        if self.face_uvs.is_empty() {
            self.face_uvs = other.face_uvs.clone();
        } else if !other.face_uvs.is_empty() {
            self.face_uvs.extend_from_slice(&other.face_uvs);
        }

        for &(a, b) in &other.sharp_edges {
            self.sharp_edges.push((a + vertex_offset, b + vertex_offset));
        }

        let _ = face_offset;
    }

    /// Transform mesh by matrix
    pub fn transform(&mut self, matrix: &nalgebra::Matrix4<f32>) {
        for vertex in &mut self.vertices {
            let v4 = matrix * vertex.to_homogeneous();
            *vertex = Point3::from_homogeneous(v4).unwrap();
        }

        // Transform normals (using inverse transpose for correct normal transformation)
        let normal_matrix = matrix.try_inverse()
            .map(|inv| inv.transpose())
            .unwrap_or_else(|| *matrix);

        for normal in &mut self.normals {
            let n4 = normal_matrix * normal.to_homogeneous();
            *normal = Vector3::new(n4.x, n4.y, n4.z).normalize();
        }
    }
}

impl Default for Mesh {
    fn default() -> Self {
        Self::new()
    }
}

/// Trait for geometric primitives
pub trait Primitive {
    /// Generate mesh representation
    fn to_mesh(&self) -> Result<Mesh>;

    /// Get bounding box
    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_mesh() {
        let mesh = Mesh::new();
        assert_eq!(mesh.vertex_count(), 0);
        assert_eq!(mesh.triangle_count(), 0);
    }

    #[test]
    fn test_mesh_merge() {
        let mut mesh1 = Mesh::new();
        mesh1.vertices.push(Point3::new(0.0, 0.0, 0.0));
        mesh1.indices.push(0);

        let mut mesh2 = Mesh::new();
        mesh2.vertices.push(Point3::new(1.0, 1.0, 1.0));
        mesh2.indices.push(0);

        mesh1.merge(&mesh2);

        assert_eq!(mesh1.vertex_count(), 2);
        assert_eq!(mesh1.indices[1], 1);
    }
}
pub mod extended_primitives;
pub mod templates;

pub use extended_primitives::*;
pub use templates::*;
