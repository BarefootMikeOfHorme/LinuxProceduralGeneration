//! Geometric primitives (box, sphere, cylinder, cone, torus)

use nalgebra::{Point3, Vector3};
use std::f32::consts::PI;
use crate::geometry::{Mesh, Primitive};
use crate::Result;

fn validate_finite_positive(label: &str, value: f32) -> Result<()> {
    if !value.is_finite() || value <= 0.0 {
        return Err(crate::GeometryError::InvalidParameters(format!(
            "{label} must be finite and greater than zero"
        )));
    }
    Ok(())
}

fn validate_finite_vector(label: &str, vector: Vector3<f32>) -> Result<()> {
    if !vector.x.is_finite() || !vector.y.is_finite() || !vector.z.is_finite() {
        return Err(crate::GeometryError::InvalidParameters(format!(
            "{label} must contain only finite values"
        )));
    }
    Ok(())
}

fn validate_finite_point(label: &str, point: Point3<f32>) -> Result<()> {
    validate_finite_vector(label, point.coords)
}

fn validate_count(label: &str, value: u32, minimum: u32) -> Result<()> {
    if value < minimum {
        return Err(crate::GeometryError::InvalidParameters(format!(
            "{label} must be at least {minimum}"
        )));
    }
    Ok(())
}

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
        validate_finite_vector("box size", self.size)?;
        validate_finite_positive("box size.x", self.size.x)?;
        validate_finite_positive("box size.y", self.size.y)?;
        validate_finite_positive("box size.z", self.size.z)?;
        validate_finite_point("box center", self.center)?;

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
        validate_finite_positive("sphere radius", self.radius)?;
        validate_finite_point("sphere center", self.center)?;
        validate_count("sphere segments", self.segments, 3)?;
        validate_count("sphere rings", self.rings, 2)?;

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
        validate_finite_positive("cylinder radius", self.radius)?;
        validate_finite_positive("cylinder height", self.height)?;
        validate_finite_point("cylinder center", self.center)?;
        validate_count("cylinder segments", self.segments, 3)?;

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

            // Two triangles per quad, wound outward.
            mesh.indices.push(curr_bottom);
            mesh.indices.push(curr_top);
            mesh.indices.push(next_bottom);

            mesh.indices.push(curr_top);
            mesh.indices.push(next_top);
            mesh.indices.push(next_bottom);
        }

        // Bottom and top cap centers.
        let bottom_center_idx = mesh.vertices.len() as u32;
        mesh.vertices.push(Point3::new(
            self.center.x,
            self.center.y - half_height,
            self.center.z,
        ));
        let top_center_idx = mesh.vertices.len() as u32;
        mesh.vertices.push(Point3::new(
            self.center.x,
            self.center.y + half_height,
            self.center.z,
        ));

        for i in 0..self.segments {
            let curr_bottom = i * 2;
            let curr_top = curr_bottom + 1;
            let next = ((i + 1) % (self.segments + 1)) * 2;
            let next_top = next + 1;

            // Bottom cap points outward along -Y.
            mesh.indices.push(bottom_center_idx);
            mesh.indices.push(curr_bottom);
            mesh.indices.push(next);

            // Top cap points outward along +Y.
            mesh.indices.push(top_center_idx);
            mesh.indices.push(next_top);
            mesh.indices.push(curr_top);
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

    pub fn with_center(mut self, center: Point3<f32>) -> Self {
        self.center = center;
        self
    }

    pub fn with_segments(mut self, segments: u32) -> Self {
        self.segments = segments;
        self
    }

    /// Create cone with low detail (8 segments)
    pub fn low_detail(radius: f32, height: f32) -> Self {
        Self::new(radius, height).with_segments(8)
    }

    /// Create cone with medium-low detail (16 segments)
    pub fn medium_low_detail(radius: f32, height: f32) -> Self {
        Self::new(radius, height).with_segments(16)
    }

    /// Create cone with medium detail (32 segments) - default
    pub fn medium_detail(radius: f32, height: f32) -> Self {
        Self::new(radius, height).with_segments(32)
    }

    /// Create cone with medium-high detail (48 segments)
    pub fn medium_high_detail(radius: f32, height: f32) -> Self {
        Self::new(radius, height).with_segments(48)
    }

    /// Create cone with high detail (64 segments)
    pub fn high_detail(radius: f32, height: f32) -> Self {
        Self::new(radius, height).with_segments(64)
    }

    /// Create cone with very high detail (128 segments)
    pub fn very_high_detail(radius: f32, height: f32) -> Self {
        Self::new(radius, height).with_segments(128)
    }
}

impl Primitive for Cone {
    fn to_mesh(&self) -> Result<Mesh> {
        validate_finite_positive("cone radius", self.radius)?;
        validate_finite_positive("cone height", self.height)?;
        validate_finite_point("cone center", self.center)?;
        validate_count("cone segments", self.segments, 3)?;

        let mut mesh = Mesh::new();

        // Center of base circle
        let base_center_idx = 0;
        mesh.vertices.push(Point3::new(
            self.center.x,
            self.center.y,
            self.center.z,
        ));

        // Base circle vertices
        for i in 0..=self.segments {
            let theta = 2.0 * PI * i as f32 / self.segments as f32;
            let x = self.radius * theta.cos();
            let z = self.radius * theta.sin();

            mesh.vertices.push(Point3::new(
                self.center.x + x,
                self.center.y,
                self.center.z + z,
            ));
        }

        // Apex at top
        let apex_idx = mesh.vertices.len() as u32;
        mesh.vertices.push(Point3::new(
            self.center.x,
            self.center.y + self.height,
            self.center.z,
        ));

        // Base triangles (fan from center)
        for i in 0..self.segments {
            let curr = 1 + i;
            let next = 1 + ((i + 1) % (self.segments + 1));

            mesh.indices.push(base_center_idx);
            mesh.indices.push(curr);
            mesh.indices.push(next);
        }

        // Side triangles (from base to apex)
        for i in 0..self.segments {
            let curr = 1 + i;
            let next = 1 + ((i + 1) % (self.segments + 1));

            mesh.indices.push(curr);
            mesh.indices.push(apex_idx);
            mesh.indices.push(next);
        }

        mesh.compute_normals();
        mesh.uvs = vec![(0.0, 0.0); mesh.vertices.len()];

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

    pub fn with_center(mut self, center: Point3<f32>) -> Self {
        self.center = center;
        self
    }

    pub fn with_segments(mut self, major_segments: u32, minor_segments: u32) -> Self {
        self.major_segments = major_segments;
        self.minor_segments = minor_segments;
        self
    }

    /// Create torus with low detail (16, 8)
    pub fn low_detail(major_radius: f32, minor_radius: f32) -> Self {
        Self::new(major_radius, minor_radius).with_segments(16, 8)
    }

    /// Create torus with medium-low detail (24, 12)
    pub fn medium_low_detail(major_radius: f32, minor_radius: f32) -> Self {
        Self::new(major_radius, minor_radius).with_segments(24, 12)
    }

    /// Create torus with medium detail (48, 24) - default
    pub fn medium_detail(major_radius: f32, minor_radius: f32) -> Self {
        Self::new(major_radius, minor_radius).with_segments(48, 24)
    }

    /// Create torus with medium-high detail (64, 32)
    pub fn medium_high_detail(major_radius: f32, minor_radius: f32) -> Self {
        Self::new(major_radius, minor_radius).with_segments(64, 32)
    }

    /// Create torus with high detail (96, 48)
    pub fn high_detail(major_radius: f32, minor_radius: f32) -> Self {
        Self::new(major_radius, minor_radius).with_segments(96, 48)
    }

    /// Create torus with very high detail (128, 64)
    pub fn very_high_detail(major_radius: f32, minor_radius: f32) -> Self {
        Self::new(major_radius, minor_radius).with_segments(128, 64)
    }
}

impl Primitive for Torus {
    fn to_mesh(&self) -> Result<Mesh> {
        validate_finite_positive("torus major radius", self.major_radius)?;
        validate_finite_positive("torus minor radius", self.minor_radius)?;
        if self.major_radius <= self.minor_radius {
            return Err(crate::GeometryError::InvalidParameters(
                "torus major radius must be greater than minor radius".to_string(),
            ));
        }
        validate_finite_point("torus center", self.center)?;
        validate_count("torus major segments", self.major_segments, 3)?;
        validate_count("torus minor segments", self.minor_segments, 3)?;

        let mut mesh = Mesh::new();

        // Generate torus vertices
        for i in 0..=self.major_segments {
            let theta = 2.0 * PI * i as f32 / self.major_segments as f32;
            let cos_theta = theta.cos();
            let sin_theta = theta.sin();

            for j in 0..=self.minor_segments {
                let phi = 2.0 * PI * j as f32 / self.minor_segments as f32;
                let cos_phi = phi.cos();
                let sin_phi = phi.sin();

                // Torus parametric equations
                let x = (self.major_radius + self.minor_radius * cos_phi) * cos_theta;
                let y = self.minor_radius * sin_phi;
                let z = (self.major_radius + self.minor_radius * cos_phi) * sin_theta;

                mesh.vertices.push(Point3::new(
                    self.center.x + x,
                    self.center.y + y,
                    self.center.z + z,
                ));

                // Normal vector for torus
                let nx = cos_phi * cos_theta;
                let ny = sin_phi;
                let nz = cos_phi * sin_theta;
                mesh.normals.push(Vector3::new(nx, ny, nz));

                // UV coordinates
                let u = i as f32 / self.major_segments as f32;
                let v = j as f32 / self.minor_segments as f32;
                mesh.uvs.push((u, v));
            }
        }

        // Generate indices
        for i in 0..self.major_segments {
            for j in 0..self.minor_segments {
                let curr = i * (self.minor_segments + 1) + j;
                let next_i = ((i + 1) % (self.major_segments + 1)) * (self.minor_segments + 1) + j;
                let next_j = curr + 1;
                let next_both = next_i + 1;

                // First triangle, wound outward.
                mesh.indices.push(curr);
                mesh.indices.push(next_j);
                mesh.indices.push(next_i);

                // Second triangle, wound outward.
                mesh.indices.push(next_j);
                mesh.indices.push(next_both);
                mesh.indices.push(next_i);
            }
        }

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

    fn signed_volume(mesh: &Mesh) -> f32 {
        mesh.indices
            .chunks(3)
            .map(|chunk| {
                let a = mesh.vertices[chunk[0] as usize];
                let b = mesh.vertices[chunk[1] as usize];
                let c = mesh.vertices[chunk[2] as usize];
                a.coords.dot(&b.coords.cross(&c.coords)) / 6.0
            })
            .sum()
    }

    #[test]
    fn test_cylinder_is_capped_and_outward() {
        let mesh = Cylinder::new(1.0, 2.0).with_segments(8).to_mesh().unwrap();
        assert_eq!(mesh.vertex_count(), 20);
        assert_eq!(mesh.triangle_count(), 32);
        assert!(signed_volume(&mesh) > 0.0);
    }

    #[test]
    fn test_cone_and_torus_winding() {
        let cone = Cone::new(1.0, 2.0).with_segments(8).to_mesh().unwrap();
        assert!(signed_volume(&cone) > 0.0);

        let torus = Torus::new(2.0, 0.5)
            .with_segments(12, 8)
            .to_mesh()
            .unwrap();
        assert!(signed_volume(&torus) > 0.0);
    }

    #[test]
    fn test_invalid_primitive_parameters_are_rejected() {
        assert!(Cylinder::new(1.0, 1.0).with_segments(0).to_mesh().is_err());
        assert!(Sphere::new(1.0).with_detail(0, 8).to_mesh().is_err());
        assert!(Torus::new(1.0, 1.0).to_mesh().is_err());
    }
}
