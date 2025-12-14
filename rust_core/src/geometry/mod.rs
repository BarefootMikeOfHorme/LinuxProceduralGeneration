//! Geometry primitives and operations
//!
//! This module provides basic geometric primitives (box, sphere, cylinder, etc.)
//! and procedural operations (extrude, revolve, loft).

use nalgebra::{Point3, Vector3};
use serde::{Deserialize, Serialize};
use crate::{Result, GeometryError};

pub mod primitives;
pub mod operations;

pub use primitives::{Box, Sphere, Cylinder, Cone, Torus};
pub use operations::{extrude, revolve, loft, sweep};

/// Core mesh representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Mesh {
    /// Vertex positions
    pub vertices: Vec<Point3<f32>>,

    /// Vertex normals
    pub normals: Vec<Vector3<f32>>,

    /// UV coordinates
    pub uvs: Vec<(f32, f32)>,

    /// Triangle indices (triplets)
    pub indices: Vec<u32>,

    /// Material assignments per face
    pub materials: Vec<u32>,
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
        }
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

        self.vertices.extend_from_slice(&other.vertices);
        self.normals.extend_from_slice(&other.normals);
        self.uvs.extend_from_slice(&other.uvs);

        // Offset indices
        for &idx in &other.indices {
            self.indices.push(idx + vertex_offset);
        }

        self.materials.extend_from_slice(&other.materials);
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
