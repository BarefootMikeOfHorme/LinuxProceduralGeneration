//! Geometric primitives (box, sphere, cylinder, cone, torus)

use nalgebra::{Point3, Vector3};
use std::f32::consts::PI;
use crate::geometry::{Mesh, Primitive};
use crate::Result;

/// Box primitive
#[derive(Debug, Clone)]
pub struct Box {
    pub size: Vector3<f32>,
    pub center: Point3<f32>,
}

impl Box {
    pub fn new(size: Vector3<f32>) -> Self {
        Self {
            size,
            center: Point3::origin(),
        }
    }

    pub fn with_center(mut self, center: Point3<f32>) -> Self {
        self.center = center;
        self
    }
}

impl Primitive for Box {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();

        let hx = self.size.x / 2.0;
        let hy = self.size.y / 2.0;
        let hz = self.size.z / 2.0;
        let c = self.center;

        // 8 vertices of a box
        let vertices = vec![
            Point3::new(c.x - hx, c.y - hy, c.z - hz),
            Point3::new(c.x + hx, c.y - hy, c.z - hz),
            Point3::new(c.x + hx, c.y + hy, c.z - hz),
            Point3::new(c.x - hx, c.y + hy, c.z - hz),
            Point3::new(c.x - hx, c.y - hy, c.z + hz),
            Point3::new(c.x + hx, c.y - hy, c.z + hz),
            Point3::new(c.x + hx, c.y + hy, c.z + hz),
            Point3::new(c.x - hx, c.y + hy, c.z + hz),
        ];

        // 6 faces, 2 triangles each
        let indices = vec![
            // Front
            0, 1, 2, 0, 2, 3,
            // Back
            5, 4, 7, 5, 7, 6,
            // Left
            4, 0, 3, 4, 3, 7,
            // Right
            1, 5, 6, 1, 6, 2,
            // Bottom
            4, 5, 1, 4, 1, 0,
            // Top
            3, 2, 6, 3, 6, 7,
        ];

        mesh.vertices = vertices;
        mesh.indices = indices;
        mesh.compute_normals();

        // Generate UVs (simple box mapping)
        mesh.uvs = vec![(0.0, 0.0); mesh.vertices.len()];

        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        let hx = self.size.x / 2.0;
        let hy = self.size.y / 2.0;
        let hz = self.size.z / 2.0;
        let c = self.center;

        (
            Point3::new(c.x - hx, c.y - hy, c.z - hz),
            Point3::new(c.x + hx, c.y + hy, c.z + hz),
        )
    }
}

/// Sphere primitive
#[derive(Debug, Clone)]
pub struct Sphere {
    pub radius: f32,
    pub center: Point3<f32>,
    pub segments: u32,
    pub rings: u32,
}

impl Sphere {
    pub fn new(radius: f32) -> Self {
        Self {
            radius,
            center: Point3::origin(),
            segments: 32,
            rings: 16,
        }
    }

    pub fn with_center(mut self, center: Point3<f32>) -> Self {
        self.center = center;
        self
    }

    pub fn with_detail(mut self, segments: u32, rings: u32) -> Self {
        self.segments = segments;
        self.rings = rings;
        self
    }
}

impl Primitive for Sphere {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();

        // UV sphere generation
        for ring in 0..=self.rings {
            let phi = PI * ring as f32 / self.rings as f32;
            let sin_phi = phi.sin();
            let cos_phi = phi.cos();

            for seg in 0..=self.segments {
                let theta = 2.0 * PI * seg as f32 / self.segments as f32;
                let sin_theta = theta.sin();
                let cos_theta = theta.cos();

                let x = sin_phi * cos_theta;
                let y = cos_phi;
                let z = sin_phi * sin_theta;

                mesh.vertices.push(Point3::new(
                    self.center.x + self.radius * x,
                    self.center.y + self.radius * y,
                    self.center.z + self.radius * z,
                ));

                mesh.normals.push(Vector3::new(x, y, z));

                let u = seg as f32 / self.segments as f32;
                let v = ring as f32 / self.rings as f32;
                mesh.uvs.push((u, v));
            }
        }

        // Generate indices
        for ring in 0..self.rings {
            for seg in 0..self.segments {
                let curr = ring * (self.segments + 1) + seg;
                let next = curr + self.segments + 1;

                mesh.indices.push(curr);
                mesh.indices.push(next);
                mesh.indices.push(curr + 1);

                mesh.indices.push(curr + 1);
                mesh.indices.push(next);
                mesh.indices.push(next + 1);
            }
        }

        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        let r = self.radius;
        let c = self.center;

        (
            Point3::new(c.x - r, c.y - r, c.z - r),
            Point3::new(c.x + r, c.y + r, c.z + r),
        )
    }
}

/// Cylinder primitive
#[derive(Debug, Clone)]
pub struct Cylinder {
    pub radius: f32,
    pub height: f32,
    pub center: Point3<f32>,
    pub segments: u32,
}

impl Cylinder {
    pub fn new(radius: f32, height: f32) -> Self {
        Self {
            radius,
            height,
            center: Point3::origin(),
            segments: 32,
        }
    }

    pub fn with_center(mut self, center: Point3<f32>) -> Self {
        self.center = center;
        self
    }

    pub fn with_segments(mut self, segments: u32) -> Self {
        self.segments = segments;
        self
    }
}

impl Primitive for Cylinder {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();

        let half_height = self.height / 2.0;

        // Top and bottom circles
        for i in 0..=self.segments {
            let theta = 2.0 * PI * i as f32 / self.segments as f32;
            let x = self.radius * theta.cos();
            let z = self.radius * theta.sin();

            // Bottom vertex
            mesh.vertices.push(Point3::new(
                self.center.x + x,
                self.center.y - half_height,
                self.center.z + z,
            ));

            // Top vertex
            mesh.vertices.push(Point3::new(
                self.center.x + x,
                self.center.y + half_height,
                self.center.z + z,
            ));
        }

        // Side faces
        for i in 0..self.segments {
            let curr_bottom = i * 2;
            let curr_top = curr_bottom + 1;
            let next_bottom = ((i + 1) % (self.segments + 1)) * 2;
            let next_top = next_bottom + 1;

            // Two triangles per quad
            mesh.indices.push(curr_bottom);
            mesh.indices.push(next_bottom);
            mesh.indices.push(curr_top);

            mesh.indices.push(curr_top);
            mesh.indices.push(next_bottom);
            mesh.indices.push(next_top);
        }

        mesh.compute_normals();
        mesh.uvs = vec![(0.0, 0.0); mesh.vertices.len()];

        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        let r = self.radius;
        let h = self.height / 2.0;
        let c = self.center;

        (
            Point3::new(c.x - r, c.y - h, c.z - r),
            Point3::new(c.x + r, c.y + h, c.z + r),
        )
    }
}

/// Cone primitive
#[derive(Debug, Clone)]
pub struct Cone {
    pub radius: f32,
    pub height: f32,
    pub center: Point3<f32>,
    pub segments: u32,
}

impl Cone {
    pub fn new(radius: f32, height: f32) -> Self {
        Self {
            radius,
            height,
            center: Point3::origin(),
            segments: 32,
        }
    }
}

impl Primitive for Cone {
    fn to_mesh(&self) -> Result<Mesh> {
        // Similar to cylinder but with top radius = 0
        // Implementation simplified for now
        let mut mesh = Mesh::new();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        let r = self.radius;
        let h = self.height;
        let c = self.center;

        (
            Point3::new(c.x - r, c.y, c.z - r),
            Point3::new(c.x + r, c.y + h, c.z + r),
        )
    }
}

/// Torus primitive
#[derive(Debug, Clone)]
pub struct Torus {
    pub major_radius: f32,
    pub minor_radius: f32,
    pub center: Point3<f32>,
    pub major_segments: u32,
    pub minor_segments: u32,
}

impl Torus {
    pub fn new(major_radius: f32, minor_radius: f32) -> Self {
        Self {
            major_radius,
            minor_radius,
            center: Point3::origin(),
            major_segments: 48,
            minor_segments: 24,
        }
    }
}

impl Primitive for Torus {
    fn to_mesh(&self) -> Result<Mesh> {
        // Torus generation - implementation simplified for now
        let mut mesh = Mesh::new();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        let r = self.major_radius + self.minor_radius;
        let c = self.center;

        (
            Point3::new(c.x - r, c.y - self.minor_radius, c.z - r),
            Point3::new(c.x + r, c.y + self.minor_radius, c.z + r),
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_box_creation() {
        let b = Box::new(Vector3::new(2.0, 2.0, 2.0));
        let mesh = b.to_mesh().unwrap();
        assert_eq!(mesh.vertex_count(), 8);
        assert_eq!(mesh.triangle_count(), 12); // 6 faces * 2 triangles
    }

    #[test]
    fn test_sphere_creation() {
        let s = Sphere::new(1.0).with_detail(16, 8);
        let mesh = s.to_mesh().unwrap();
        assert!(mesh.vertex_count() > 0);
    }
}
