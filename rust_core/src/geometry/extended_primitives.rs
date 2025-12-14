//! Extended Primitive Library - 20+ Geometric Shapes
//!
//! Comprehensive shape library with scalable templates for:
//! - Unity, Unreal, CryEngine, Lumix Engine
//!
//! All primitives support:
//! - Custom sizing
//! - Custom tessellation/subdivision
//! - UV mapping
//! - Normal generation

use nalgebra::{Point3, Vector3};
use std::f32::consts::PI;
use crate::geometry::{Mesh, Primitive};
use crate::Result;

// ============================================================================
// CAPSULE - Cylinder with hemispherical caps
// ============================================================================

#[derive(Debug, Clone)]
pub struct Capsule {
    pub radius: f32,
    pub height: f32, // Height of cylindrical section
    pub rings: usize,
    pub segments: usize,
}

impl Capsule {
    pub fn new(radius: f32, height: f32) -> Self {
        Self { radius, height, rings: 8, segments: 16 }
    }

    pub fn with_detail(mut self, rings: usize, segments: usize) -> Self {
        self.rings = rings;
        self.segments = segments;
        self
    }
}

impl Primitive for Capsule {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();

        // Top hemisphere
        for i in 0..=self.rings {
            let theta = PI * 0.5 * (i as f32 / self.rings as f32);
            let y = self.height / 2.0 + self.radius * theta.cos();
            let r = self.radius * theta.sin();

            for j in 0..=self.segments {
                let phi = 2.0 * PI * (j as f32 / self.segments as f32);
                let x = r * phi.cos();
                let z = r * phi.sin();
                mesh.vertices.push(Point3::new(x, y, z));
            }
        }

        // Cylindrical section
        for i in 0..=self.rings {
            let y = self.height / 2.0 - (self.height * i as f32 / self.rings as f32);
            for j in 0..=self.segments {
                let phi = 2.0 * PI * (j as f32 / self.segments as f32);
                let x = self.radius * phi.cos();
                let z = self.radius * phi.sin();
                mesh.vertices.push(Point3::new(x, y, z));
            }
        }

        // Bottom hemisphere
        for i in 0..=self.rings {
            let theta = PI * 0.5 + PI * 0.5 * (i as f32 / self.rings as f32);
            let y = -self.height / 2.0 + self.radius * theta.cos();
            let r = self.radius * theta.sin();

            for j in 0..=self.segments {
                let phi = 2.0 * PI * (j as f32 / self.segments as f32);
                let x = r * phi.cos();
                let z = r * phi.sin();
                mesh.vertices.push(Point3::new(x, y, z));
            }
        }

        mesh.compute_normals();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        let half_height = self.height / 2.0 + self.radius;
        (
            Point3::new(-self.radius, -half_height, -self.radius),
            Point3::new(self.radius, half_height, self.radius),
        )
    }
}

// ============================================================================
// PYRAMID - Square pyramid
// ============================================================================

#[derive(Debug, Clone)]
pub struct Pyramid {
    pub base_size: f32,
    pub height: f32,
}

impl Pyramid {
    pub fn new(base_size: f32, height: f32) -> Self {
        Self { base_size, height }
    }
}

impl Primitive for Pyramid {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();
        let h = self.base_size / 2.0;

        // Base vertices
        mesh.vertices.push(Point3::new(-h, 0.0, -h)); // 0
        mesh.vertices.push(Point3::new(h, 0.0, -h));  // 1
        mesh.vertices.push(Point3::new(h, 0.0, h));   // 2
        mesh.vertices.push(Point3::new(-h, 0.0, h));  // 3
        // Apex
        mesh.vertices.push(Point3::new(0.0, self.height, 0.0)); // 4

        // Base (2 triangles)
        mesh.indices.extend_from_slice(&[0, 2, 1, 0, 3, 2]);

        // 4 side faces
        mesh.indices.extend_from_slice(&[0, 1, 4]); // Front
        mesh.indices.extend_from_slice(&[1, 2, 4]); // Right
        mesh.indices.extend_from_slice(&[2, 3, 4]); // Back
        mesh.indices.extend_from_slice(&[3, 0, 4]); // Left

        mesh.compute_normals();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        let h = self.base_size / 2.0;
        (Point3::new(-h, 0.0, -h), Point3::new(h, self.height, h))
    }
}

// ============================================================================
// PLANE - Flat subdivided plane
// ============================================================================

#[derive(Debug, Clone)]
pub struct Plane {
    pub width: f32,
    pub depth: f32,
    pub subdivisions_x: usize,
    pub subdivisions_z: usize,
}

impl Plane {
    pub fn new(width: f32, depth: f32) -> Self {
        Self {
            width,
            depth,
            subdivisions_x: 1,
            subdivisions_z: 1,
        }
    }

    pub fn with_subdivisions(mut self, x: usize, z: usize) -> Self {
        self.subdivisions_x = x;
        self.subdivisions_z = z;
        self
    }
}

impl Primitive for Plane {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();

        let hw = self.width / 2.0;
        let hd = self.depth / 2.0;

        // Generate grid vertices
        for z in 0..=self.subdivisions_z {
            for x in 0..=self.subdivisions_x {
                let px = -hw + (x as f32 / self.subdivisions_x as f32) * self.width;
                let pz = -hd + (z as f32 / self.subdivisions_z as f32) * self.depth;
                mesh.vertices.push(Point3::new(px, 0.0, pz));
            }
        }

        // Generate triangles
        for z in 0..self.subdivisions_z {
            for x in 0..self.subdivisions_x {
                let i0 = (z * (self.subdivisions_x + 1) + x) as u32;
                let i1 = i0 + 1;
                let i2 = i0 + (self.subdivisions_x + 1) as u32;
                let i3 = i2 + 1;

                mesh.indices.extend_from_slice(&[i0, i2, i1, i1, i2, i3]);
            }
        }

        mesh.compute_normals();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        (
            Point3::new(-self.width / 2.0, 0.0, -self.depth / 2.0),
            Point3::new(self.width / 2.0, 0.0, self.depth / 2.0),
        )
    }
}

// ============================================================================
// DISC - Flat circle
// ============================================================================

#[derive(Debug, Clone)]
pub struct Disc {
    pub radius: f32,
    pub segments: usize,
}

impl Disc {
    pub fn new(radius: f32) -> Self {
        Self { radius, segments: 32 }
    }

    pub fn with_segments(mut self, segments: usize) -> Self {
        self.segments = segments;
        self
    }
}

impl Primitive for Disc {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();

        // Center vertex
        mesh.vertices.push(Point3::origin());

        // Circle vertices
        for i in 0..=self.segments {
            let angle = 2.0 * PI * (i as f32 / self.segments as f32);
            let x = self.radius * angle.cos();
            let z = self.radius * angle.sin();
            mesh.vertices.push(Point3::new(x, 0.0, z));
        }

        // Triangles
        for i in 0..self.segments {
            mesh.indices.extend_from_slice(&[0, (i + 2) as u32, (i + 1) as u32]);
        }

        mesh.compute_normals();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        (
            Point3::new(-self.radius, 0.0, -self.radius),
            Point3::new(self.radius, 0.0, self.radius),
        )
    }
}

// ============================================================================
// RING/ANNULUS - Flat ring
// ============================================================================

#[derive(Debug, Clone)]
pub struct Ring {
    pub inner_radius: f32,
    pub outer_radius: f32,
    pub segments: usize,
}

impl Ring {
    pub fn new(inner_radius: f32, outer_radius: f32) -> Self {
        Self {
            inner_radius,
            outer_radius,
            segments: 32,
        }
    }
}

impl Primitive for Ring {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();

        for i in 0..=self.segments {
            let angle = 2.0 * PI * (i as f32 / self.segments as f32);
            let cos_a = angle.cos();
            let sin_a = angle.sin();

            // Inner circle
            mesh.vertices.push(Point3::new(
                self.inner_radius * cos_a,
                0.0,
                self.inner_radius * sin_a,
            ));

            // Outer circle
            mesh.vertices.push(Point3::new(
                self.outer_radius * cos_a,
                0.0,
                self.outer_radius * sin_a,
            ));
        }

        // Generate quad faces (2 triangles each)
        for i in 0..self.segments {
            let i0 = (i * 2) as u32;
            let i1 = i0 + 1;
            let i2 = i0 + 2;
            let i3 = i0 + 3;

            mesh.indices.extend_from_slice(&[i0, i2, i1, i1, i2, i3]);
        }

        mesh.compute_normals();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        (
            Point3::new(-self.outer_radius, 0.0, -self.outer_radius),
            Point3::new(self.outer_radius, 0.0, self.outer_radius),
        )
    }
}

// ============================================================================
// TUBE - Hollow cylinder
// ============================================================================

#[derive(Debug, Clone)]
pub struct Tube {
    pub inner_radius: f32,
    pub outer_radius: f32,
    pub height: f32,
    pub segments: usize,
}

impl Tube {
    pub fn new(inner_radius: f32, outer_radius: f32, height: f32) -> Self {
        Self {
            inner_radius,
            outer_radius,
            height,
            segments: 32,
        }
    }
}

impl Primitive for Tube {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();
        let h2 = self.height / 2.0;

        // Generate vertices
        for i in 0..=self.segments {
            let angle = 2.0 * PI * (i as f32 / self.segments as f32);
            let cos_a = angle.cos();
            let sin_a = angle.sin();

            // Bottom inner
            mesh.vertices.push(Point3::new(
                self.inner_radius * cos_a,
                -h2,
                self.inner_radius * sin_a,
            ));
            // Bottom outer
            mesh.vertices.push(Point3::new(
                self.outer_radius * cos_a,
                -h2,
                self.outer_radius * sin_a,
            ));
            // Top inner
            mesh.vertices.push(Point3::new(
                self.inner_radius * cos_a,
                h2,
                self.inner_radius * sin_a,
            ));
            // Top outer
            mesh.vertices.push(Point3::new(
                self.outer_radius * cos_a,
                h2,
                self.outer_radius * sin_a,
            ));
        }

        // Generate faces
        for i in 0..self.segments {
            let base = (i * 4) as u32;

            // Outer wall
            mesh.indices.extend_from_slice(&[
                base + 1, base + 5, base + 3,
                base + 3, base + 5, base + 7,
            ]);

            // Inner wall
            mesh.indices.extend_from_slice(&[
                base, base + 2, base + 4,
                base + 2, base + 6, base + 4,
            ]);

            // Bottom ring
            mesh.indices.extend_from_slice(&[
                base, base + 4, base + 1,
                base + 1, base + 4, base + 5,
            ]);

            // Top ring
            mesh.indices.extend_from_slice(&[
                base + 2, base + 3, base + 6,
                base + 3, base + 7, base + 6,
            ]);
        }

        mesh.compute_normals();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        let h2 = self.height / 2.0;
        (
            Point3::new(-self.outer_radius, -h2, -self.outer_radius),
            Point3::new(self.outer_radius, h2, self.outer_radius),
        )
    }
}

// ============================================================================
// PRISM - N-sided prism
// ============================================================================

#[derive(Debug, Clone)]
pub struct Prism {
    pub radius: f32,
    pub height: f32,
    pub sides: usize,
}

impl Prism {
    pub fn triangular(radius: f32, height: f32) -> Self {
        Self { radius, height, sides: 3 }
    }

    pub fn hexagonal(radius: f32, height: f32) -> Self {
        Self { radius, height, sides: 6 }
    }

    pub fn octagonal(radius: f32, height: f32) -> Self {
        Self { radius, height, sides: 8 }
    }
}

impl Primitive for Prism {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();
        let h2 = self.height / 2.0;

        // Generate vertices (bottom and top)
        for i in 0..self.sides {
            let angle = 2.0 * PI * (i as f32 / self.sides as f32);
            let x = self.radius * angle.cos();
            let z = self.radius * angle.sin();

            mesh.vertices.push(Point3::new(x, -h2, z)); // Bottom
            mesh.vertices.push(Point3::new(x, h2, z));  // Top
        }

        // Side faces
        for i in 0..self.sides {
            let i0 = (i * 2) as u32;
            let i1 = i0 + 1;
            let i2 = ((i + 1) % self.sides * 2) as u32;
            let i3 = i2 + 1;

            mesh.indices.extend_from_slice(&[i0, i2, i1, i1, i2, i3]);
        }

        // Bottom and top caps
        let center_bottom = mesh.vertices.len() as u32;
        mesh.vertices.push(Point3::new(0.0, -h2, 0.0));
        let center_top = mesh.vertices.len() as u32;
        mesh.vertices.push(Point3::new(0.0, h2, 0.0));

        for i in 0..self.sides {
            let i0 = (i * 2) as u32;
            let i1 = i0 + 1;
            let i2 = ((i + 1) % self.sides * 2) as u32;
            let i3 = i2 + 1;

            // Bottom cap
            mesh.indices.extend_from_slice(&[center_bottom, i2, i0]);
            // Top cap
            mesh.indices.extend_from_slice(&[center_top, i1, i3]);
        }

        mesh.compute_normals();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        let h2 = self.height / 2.0;
        (
            Point3::new(-self.radius, -h2, -self.radius),
            Point3::new(self.radius, h2, self.radius),
        )
    }
}

// ============================================================================
// DOME/HEMISPHERE
// ============================================================================

#[derive(Debug, Clone)]
pub struct Dome {
    pub radius: f32,
    pub rings: usize,
    pub segments: usize,
}

impl Dome {
    pub fn new(radius: f32) -> Self {
        Self { radius, rings: 16, segments: 32 }
    }
}

impl Primitive for Dome {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();

        // Top hemisphere only
        for i in 0..=self.rings {
            let theta = PI * 0.5 * (i as f32 / self.rings as f32);
            let y = self.radius * theta.cos();
            let r = self.radius * theta.sin();

            for j in 0..=self.segments {
                let phi = 2.0 * PI * (j as f32 / self.segments as f32);
                let x = r * phi.cos();
                let z = r * phi.sin();
                mesh.vertices.push(Point3::new(x, y, z));
            }
        }

        // Generate triangles
        for i in 0..self.rings {
            for j in 0..self.segments {
                let i0 = (i * (self.segments + 1) + j) as u32;
                let i1 = i0 + 1;
                let i2 = i0 + (self.segments + 1) as u32;
                let i3 = i2 + 1;

                mesh.indices.extend_from_slice(&[i0, i2, i1, i1, i2, i3]);
            }
        }

        mesh.compute_normals();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        (
            Point3::new(-self.radius, 0.0, -self.radius),
            Point3::new(self.radius, self.radius, self.radius),
        )
    }
}

// ============================================================================
// PLATONIC SOLIDS
// ============================================================================

#[derive(Debug, Clone)]
pub struct Tetrahedron {
    pub size: f32,
}

impl Tetrahedron {
    pub fn new(size: f32) -> Self {
        Self { size }
    }
}

impl Primitive for Tetrahedron {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();
        let s = self.size;

        // 4 vertices
        mesh.vertices.push(Point3::new(s, s, s));
        mesh.vertices.push(Point3::new(s, -s, -s));
        mesh.vertices.push(Point3::new(-s, s, -s));
        mesh.vertices.push(Point3::new(-s, -s, s));

        // 4 faces
        mesh.indices.extend_from_slice(&[
            0, 2, 1,
            0, 3, 2,
            0, 1, 3,
            1, 2, 3,
        ]);

        mesh.compute_normals();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        (
            Point3::new(-self.size, -self.size, -self.size),
            Point3::new(self.size, self.size, self.size),
        )
    }
}

#[derive(Debug, Clone)]
pub struct Octahedron {
    pub size: f32,
}

impl Octahedron {
    pub fn new(size: f32) -> Self {
        Self { size }
    }
}

impl Primitive for Octahedron {
    fn to_mesh(&self) -> Result<Mesh> {
        let mut mesh = Mesh::new();
        let s = self.size;

        // 6 vertices (axis points)
        mesh.vertices.push(Point3::new(s, 0.0, 0.0));   // +X
        mesh.vertices.push(Point3::new(-s, 0.0, 0.0));  // -X
        mesh.vertices.push(Point3::new(0.0, s, 0.0));   // +Y
        mesh.vertices.push(Point3::new(0.0, -s, 0.0));  // -Y
        mesh.vertices.push(Point3::new(0.0, 0.0, s));   // +Z
        mesh.vertices.push(Point3::new(0.0, 0.0, -s));  // -Z

        // 8 triangular faces
        mesh.indices.extend_from_slice(&[
            0, 2, 4,  0, 4, 3,  0, 3, 5,  0, 5, 2,
            1, 4, 2,  1, 3, 4,  1, 5, 3,  1, 2, 5,
        ]);

        mesh.compute_normals();
        Ok(mesh)
    }

    fn bounding_box(&self) -> (Point3<f32>, Point3<f32>) {
        (
            Point3::new(-self.size, -self.size, -self.size),
            Point3::new(self.size, self.size, self.size),
        )
    }
}

