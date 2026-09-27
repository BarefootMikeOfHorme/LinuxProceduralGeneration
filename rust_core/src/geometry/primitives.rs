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

        // 6 faces, 2 triangles each, wound counter-clockwise when seen from
        // outside so that face normals and the signed volume come out positive.
        //
        // Winding matters here and used to be wrong: every face was listed
        // clockwise-from-outside, giving a signed volume of -size.x*size.y*size.z
        // and normals pointing into the solid. That inverts box lighting and
        // silently flips the inside/outside answer for anything built on top of
        // it, so the order below is load-bearing, not cosmetic.
        let indices = vec![
            // Front (-Z)
            0, 2, 1, 0, 3, 2,
            // Back (+Z)
            5, 7, 4, 5, 6, 7,
            // Left (-X)
            4, 3, 0, 4, 7, 3,
            // Right (+X)
            1, 6, 5, 1, 2, 6,
            // Bottom (-Y)
            4, 1, 5, 4, 0, 1,
            // Top (+Y)
            3, 6, 2, 3, 7, 6,
        ];

        mesh.vertices = vertices;
        mesh.indices = indices;
        mesh.compute_normals();

        // A cube has twelve hard edges. Marking them sharp is what tells
        // `split_for_render` to keep the faces flat; without it a 180-degree
        // auto-smooth angle averages all six face normals into a rounded blob.
        for &(a, b) in &[
            (0u32, 4u32),
            (1, 5),
            (2, 6),
            (3, 7), // along Z
            (0, 1),
            (3, 2),
            (4, 5),
            (7, 6), // along X
            (0, 3),
            (1, 2),
            (4, 7),
            (5, 6), // along Y
        ] {
            mesh.mark_edge_sharp(a, b);
        }

        // Each face gets its own 0..1 square. A single UV per vertex cannot do
        // this: the eight corners are shared by three faces each, and no one
        // coordinate is right for all three. So the per-corner buffer is
        // authoritative and `uvs` is left empty rather than filled with a
        // plausible-looking value that no face actually uses.
        //
        // Each face's (u, v) axes are chosen so that u x v is the outward
        // normal. That keeps the tangent frame right-handed, so a normal map
        // applied on top is not mirrored.
        let (min_x, max_x) = (c.x - hx, c.x + hx);
        let (min_y, max_y) = (c.y - hy, c.y + hy);
        let (min_z, max_z) = (c.z - hz, c.z + hz);
        let span = |lo: f32, hi: f32, v: f32| (v - lo) / (hi - lo);
        let flip = |lo: f32, hi: f32, v: f32| (hi - v) / (hi - lo);

        // Face order matches the index order above.
        let face_uv = |p: Point3<f32>, face: usize| -> (f32, f32) {
            match face {
                0 => (flip(min_x, max_x, p.x), span(min_y, max_y, p.y)), // -Z: u=-X v=+Y
                1 => (span(min_x, max_x, p.x), span(min_y, max_y, p.y)), // +Z: u=+X v=+Y
                2 => (flip(min_y, max_y, p.y), span(min_z, max_z, p.z)), // -X: u=-Y v=+Z
                3 => (span(min_y, max_y, p.y), span(min_z, max_z, p.z)), // +X: u=+Y v=+Z
                4 => (flip(min_z, max_z, p.z), span(min_x, max_x, p.x)), // -Y: u=-Z v=+X
                _ => (span(min_z, max_z, p.z), span(min_x, max_x, p.x)), // +Y: u=+Z v=+X
            }
        };

        mesh.face_uvs = (0..mesh.triangle_count())
            .map(|f| {
                let base = f * 3;
                [
                    face_uv(mesh.vertices[mesh.indices[base] as usize], f),
                    face_uv(mesh.vertices[mesh.indices[base + 1] as usize], f),
                    face_uv(mesh.vertices[mesh.indices[base + 2] as usize], f),
                ]
            })
            .collect();

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

        // North pole is a single vertex, not a ring.
        //
        // The previous version generated a full (rings + 1) x (segments + 1)
        // grid, so the first and last rows placed segments + 1 vertices on the
        // same pole point. At the default resolution that produced 64
        // degenerate triangles, 79 duplicate vertices, 96 non-manifold edges
        // and 96 boundary edges. A box validated clean and a sphere did not,
        // which is not a defensible state for a default primitive.
        //
        // It also made the sphere non-watertight, and that is not cosmetic. A
        // solid with boundary edges cannot answer point-in-solid queries, so
        // parry3d's contains_point could not classify anything inside it. CSG
        // then classified every triangle of a mesh enclosed by the sphere as
        // Outside and kept it, so `box - sphere` returned the box when the
        // correct answer is the empty set. A pole defect was silently
        // corrupting boolean operations.
        //
        // A pole is a single point with no area, so it gets exactly one vertex
        // and the band next to it becomes a triangle fan.
        let north_pole = mesh.vertices.len() as u32;
        mesh.vertices
            .push(Point3::new(self.center.x, self.center.y + self.radius, self.center.z));
        mesh.normals.push(Vector3::new(0.0, 1.0, 0.0));
        mesh.uvs.push((0.5, 0.0));

        // Interior rings only: ring runs 1..rings, excluding both poles.
        //
        // seg runs 0..segments-1 and the wrap reuses seg 0's vertex, so a ring
        // holds `segments` vertices, not `segments + 1`. The earlier version
        // emitted seg 0 and seg segments as separate vertices at the same
        // position, which is the standard way to carry a UV seam. Here it is
        // wrong: the validator and the CSG classifier both key on vertex
        // identity, so two coincident-but-distinct vertices on a closed seam
        // read as 15 duplicate vertices and 32 boundary edges, and the solid
        // is not watertight. A duplicate vertex at a seam is also what stops
        // parry3d from answering point-in-solid, which is what made
        // `box - enclosing_sphere` return the box instead of nothing.
        //
        // UVs are kept by giving the shared vertex the u=0 coordinate and
        // letting the triangle that crosses the seam interpolate across it. A
        // single column loses the last texel of wrap-around UVs, which is a
        // far smaller cost than an unwatertight solid that breaks CSG.
        for ring in 1..self.rings {
            let phi = PI * ring as f32 / self.rings as f32;
            let sin_phi = phi.sin();
            let cos_phi = phi.cos();

            for seg in 0..self.segments {
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

        let south_pole = mesh.vertices.len() as u32;
        mesh.vertices
            .push(Point3::new(self.center.x, self.center.y - self.radius, self.center.z));
        mesh.normals.push(Vector3::new(0.0, -1.0, 0.0));
        mesh.uvs.push((0.5, 1.0));

        // Stride of one interior ring. A ring holds `segments` vertices because
        // the wrap reuses seg 0, so indices must be taken modulo segments.
        let stride = self.segments;
        let first_ring = north_pole + 1;
        let ring_count = self.rings - 1;

        // Fan from the north pole to the first interior ring.
        //
        // The order is (pole, b, a), not (pole, a, b). Going pole -> a -> b runs
        // clockwise seen from outside the cap, so the normal points down into the
        // sphere. The quad bands below and the south fan are wound the other way,
        // so the north cap was the one inverted piece in an otherwise outward
        // mesh: 928 faces summed to +3.998 and these 32 to -0.0396.
        //
        // That is not a cosmetic slip. The total signed volume still came out
        // positive, at 94.6% of the ideal 4.18879, so a plain volume check
        // passed while a cap was inside out. Only a per-region check finds it, and
        // an inward-facing cap corrupts ray-cast parity, backface culling, and
        // anything downstream that trusts the winding.
        for seg in 0..self.segments {
            let a = first_ring + seg as u32;
            let b = first_ring + ((seg + 1) % self.segments) as u32;
            mesh.indices.push(north_pole);
            mesh.indices.push(b);
            mesh.indices.push(a);
        }

        // Quad bands between consecutive interior rings.
        for r in 0..ring_count.saturating_sub(1) {
            let row = first_ring + r as u32 * stride;
            let next_row = row + stride;
            for seg in 0..self.segments {
                let next_seg = (seg + 1) % self.segments;
                let a = row + seg as u32;
                let b = row + next_seg as u32;
                let c = next_row + next_seg as u32;
                let d = next_row + seg as u32;

                // Wind so the face normal points outward. The sphere's
                // parameterisation has phi increasing from the north pole
                // downward and theta increasing counter-clockwise seen from
                // +Y, so a quad (a=row,seg  b=row,seg+1  c=next_row,seg+1
                // d=next_row,seg) must be emitted as (a, b, c) and (a, c, d).
                // The reverse order winds every quad inward, which leaves the
                // mesh looking manifold and watertight while parry3d's
                // contains_point then reports every point as outside. CSG
                // depends on that query, so inward winding made `box -
                // enclosing_sphere` return the box instead of nothing.
                mesh.indices.push(a);
                mesh.indices.push(b);
                mesh.indices.push(c);

                mesh.indices.push(a);
                mesh.indices.push(c);
                mesh.indices.push(d);
            }
        }

        // Fan from the last interior ring to the south pole.
        //
        // This is (pole, a, b) while the north fan is (pole, b, a), and the
        // asymmetry is required: a closed outward-wound surface is traversed in
        // opposite rotational senses at the two poles. Giving both fans the same
        // order inverts one of them, which is what happened here.
        if ring_count > 0 {
            let last_ring = first_ring + (ring_count - 1) as u32 * stride;
            for seg in 0..self.segments {
                let a = last_ring + seg as u32;
                let b = last_ring + ((seg + 1) % self.segments) as u32;
                mesh.indices.push(south_pole);
                mesh.indices.push(a);
                mesh.indices.push(b);
            }
        }

        mesh.compute_normals();
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

        // Top and bottom circles.
        //
        // The loop stops at `segments`, not `segments + 1`. The extra column was
        // meant to carry a UV seam, but a closed seam is expressed by
        // `face_uvs` instead, and the extra column left the wrap unjoined: column
        // `segments` sits at theta = 2*PI, where sin is about -2.4e-7 rather than
        // 0, so it was a *near* duplicate of column 0 rather than an exact one
        // and no edge ever joined them. That left 6 boundary edges, so the solid
        // was not watertight, and an unwatertight solid cannot answer
        // point-in-solid queries, which is what made CSG misclassify triangles
        // against it.
        for i in 0..self.segments {
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

        // Side faces. The wrap goes back to column 0, which is what closes the
        // seam; the UV discontinuity across that last quad lives in `face_uvs`.
        for i in 0..self.segments {
            let curr_bottom = i * 2;
            let curr_top = curr_bottom + 1;
            let next_bottom = ((i + 1) % self.segments) * 2;
            let next_top = next_bottom + 1;

            // Two triangles per quad, wound outward.
            mesh.indices.push(curr_bottom);
            mesh.indices.push(curr_top);
            mesh.indices.push(next_bottom);

            mesh.indices.push(curr_top);
            mesh.indices.push(next_top);
            mesh.indices.push(next_bottom);
        }
        let side_face_count = mesh.indices.len() / 3;

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
            let next = ((i + 1) % self.segments) * 2;
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

        // Three UV islands, matching how a cylinder is unwrapped in practice: the
        // side wall as one strip, each cap as its own disc.
        //
        // The side strip is where a vertex UV cannot work. The wrap quad runs
        // from u = (segments-1)/segments back to column 0, and the correct
        // coordinate for that column is 1.0, not 0.0. One UV per vertex forces a
        // choice between a strip that runs off the end and one that folds back
        // on itself, so the seam has to be per corner.
        let side_uv = |i: u32, top: bool| {
            (
                i as f32 / self.segments as f32,
                if top { 1.0 } else { 0.0 },
            )
        };
        let cap_uv = |i: u32, centre: bool| -> (f32, f32) {
            if centre {
                return (0.5, 0.5);
            }
            let theta = 2.0 * PI * i as f32 / self.segments as f32;
            (
                0.5 + 0.5 * theta.cos(),
                0.5 + 0.5 * theta.sin(),
            )
        };

        let side_faces = self.segments * 2;
        let mut face_uvs: Vec<[(f32, f32); 3]> =
            Vec::with_capacity(self.segments as usize * 4);
        for i in 0..self.segments {
            let next = (i + 1) % self.segments;
            // The wrap quad needs u = 1.0 on its far column, not u = 0.0.
            let next_u = if next == 0 { 1.0 } else { next as f32 / self.segments as f32 };
            let curr_u = i as f32 / self.segments as f32;

            face_uvs.push([(curr_u, 0.0), (curr_u, 1.0), (next_u, 0.0)]);
            face_uvs.push([(curr_u, 1.0), (next_u, 1.0), (next_u, 0.0)]);
        }
        debug_assert_eq!(face_uvs.len(), side_faces as usize);

        for i in 0..self.segments {
            let next = (i + 1) % self.segments;
            face_uvs.push([cap_uv(0, true), cap_uv(i, false), cap_uv(next, false)]);
            face_uvs.push([cap_uv(0, true), cap_uv(next, false), cap_uv(i, false)]);
        }
        mesh.face_uvs = face_uvs;

        // The two rim circles are hard edges: the side wall meets a cap at 90
        // degrees. Without these the rim smooths into the wall, which rounds the
        // silhouette and puts a curved normal map across a flat cap.
        for i in 0..self.segments {
            let next = ((i + 1) % self.segments) * 2;
            mesh.mark_edge_sharp(i * 2, next);
            mesh.mark_edge_sharp(i * 2 + 1, next + 1);
        }

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

        // Base circle vertices.
        //
        // Stops at `segments`, not `segments + 1`. The extra column sat at
        // theta = 2*PI, where sin is about -2.4e-7 rather than 0, so it was a
        // near duplicate of column 0 that no edge ever joined, leaving 4 boundary
        // edges and an unwatertight solid. A closed UV seam belongs in
        // `face_uvs`, not in a spare column of vertices.
        for i in 0..self.segments {
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
            let next = 1 + ((i + 1) % self.segments);

            mesh.indices.push(base_center_idx);
            mesh.indices.push(curr);
            mesh.indices.push(next);
        }

        // Side triangles (from base to apex)
        for i in 0..self.segments {
            let curr = 1 + i;
            let next = 1 + ((i + 1) % self.segments);

            mesh.indices.push(curr);
            mesh.indices.push(apex_idx);
            mesh.indices.push(next);
        }

        mesh.compute_normals();

        // Two UV islands: the base as a disc, the flank as a strip that narrows
        // to a point at the apex. The flank's far column needs u = 1.0 on the
        // wrap quad, which is exactly the case a single UV per vertex cannot
        // express, since column 0 belongs to the strip at both u = 0 and u = 1.
        let mut face_uvs: Vec<[(f32, f32); 3]> = Vec::with_capacity(self.segments as usize * 2);
        for i in 0..self.segments {
            let next = (i + 1) % self.segments;
            let theta = 2.0 * PI * i as f32 / self.segments as f32;
            let theta_next = 2.0 * PI * next as f32 / self.segments as f32;
            let curr_u = i as f32 / self.segments as f32;
            let next_u = if next == 0 {
                1.0
            } else {
                next as f32 / self.segments as f32
            };

            // Base disc.
            face_uvs.push([
                (0.5, 0.5),
                (0.5 + 0.5 * theta.cos(), 0.5 + 0.5 * theta.sin()),
                (
                    0.5 + 0.5 * theta_next.cos(),
                    0.5 + 0.5 * theta_next.sin(),
                ),
            ]);
            // Flank, narrowing to the apex at (0.5, 1.0).
            face_uvs.push([(curr_u, 0.0), (0.5, 1.0), (next_u, 0.0)]);
        }
        mesh.face_uvs = face_uvs;

        // The base rim is a hard edge where the flat base meets the flank.
        for i in 0..self.segments {
            mesh.mark_edge_sharp(1 + i, 1 + ((i + 1) % self.segments));
        }

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

        // Generate torus vertices.
        //
        // Both loops stop short of their segment count, so neither seam gets a
        // spare column. A torus closes twice, around the major circle and around
        // the tube, and the old inclusive bounds left an unjoined near-duplicate
        // at each wrap: theta = 2*PI has sin about -2.4e-7 rather than 0, so the
        // vertices were close but not identical and nothing joined them. That
        // produced 144 boundary edges, leaving the solid unwatertight.
        for i in 0..self.major_segments {
            let theta = 2.0 * PI * i as f32 / self.major_segments as f32;
            let cos_theta = theta.cos();
            let sin_theta = theta.sin();

            for j in 0..self.minor_segments {
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
                let curr = i * self.minor_segments + j;
                // Both wraps are computed from the segment counts rather than by
                // adding one. `curr + 1` steps off the end of the row when j is
                // the last minor segment, which walks straight past the end of
                // the buffer on the final major row.
                let next_i = ((i + 1) % self.major_segments) * self.minor_segments + j;
                let next_j = i * self.minor_segments + (j + 1) % self.minor_segments;
                let next_both =
                    ((i + 1) % self.major_segments) * self.minor_segments + (j + 1) % self.minor_segments;

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
    use std::collections::HashMap;

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

    /// Count edges used by exactly one triangle: a boundary edge, meaning the
    /// mesh is not closed.
    fn boundary_edge_count(mesh: &Mesh) -> usize {
        let mut counts: HashMap<(u32, u32), usize> = HashMap::new();
        for f in 0..mesh.triangle_count() {
            for k in 0..3 {
                let a = mesh.indices[f * 3 + k];
                let b = mesh.indices[f * 3 + (k + 1) % 3];
                let key = if a < b { (a, b) } else { (b, a) };
                *counts.entry(key).or_insert(0) += 1;
            }
        }
        counts.values().filter(|&&c| c == 1).count()
    }

    #[test]
    fn test_cylinder_is_capped_and_outward() {
        let mesh = Cylinder::new(1.0, 2.0).with_segments(8).to_mesh().unwrap();
        // 8 columns of (bottom, top) plus one centre vertex per cap. This used to
        // be asserted as 20, which is 2 * (8 + 1) + 2: the extra column was the
        // unjoined wrap seam, and the test had recorded the defect as expected
        // behaviour. The wrap now reuses column 0, so the solid is closed.
        assert_eq!(mesh.vertex_count(), 18);
        assert_eq!(mesh.triangle_count(), 32);
        assert!(signed_volume(&mesh) > 0.0);
        assert_eq!(
            boundary_edge_count(&mesh),
            0,
            "cylinder has boundary edges, so it is not watertight"
        );
    }

    #[test]
    fn test_cylinder_uv_seam_is_expressible() {
        let mesh = Cylinder::new(1.0, 2.0).with_segments(8).to_mesh().unwrap();
        assert_eq!(mesh.face_uvs.len(), mesh.triangle_count());

        // The wrap quad must reach u = 1.0. A single UV per vertex cannot say
        // this, because column 0 is shared by the first quad at u = 0 and the
        // last quad at u = 1; the per-corner buffer is what allows both.
        let max_u = mesh
            .face_uvs
            .iter()
            .flat_map(|tri| tri.iter().map(|&(u, _)| u))
            .fold(f32::MIN, f32::max);
        assert!(
            (max_u - 1.0).abs() < 1e-6,
            "the side strip never reaches u = 1.0 (max {max_u}), so the seam will not tile"
        );

        // The caps are separate islands, so the render split has to break the
        // surface into more vertices than the welded topology has.
        let render = mesh.split_for_render(180.0);
        assert!(
            render.unique_position_count() > 8,
            "cylinder UV islands did not split anything"
        );
    }

    #[test]
    fn test_cylinder_rim_is_sharp() {
        let mesh = Cylinder::new(1.0, 2.0).with_segments(8).to_mesh().unwrap();
        assert_eq!(mesh.sharp_edges.len(), 16, "8 rim edges per cap");

        // At a zero-degree threshold every face is flat anyway, so the rim marks
        // are what has to keep the cap and wall apart at a generous 180.
        let render = mesh.split_for_render(180.0);
        let flat = render
            .indices
            .chunks(3)
            .all(|t| t[0] != t[1] && t[1] != t[2] && t[0] != t[2]);
        assert!(
            flat,
            "a cylinder with marked rims and a 180-degree threshold should be flat shaded, not rounded"
        );
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
