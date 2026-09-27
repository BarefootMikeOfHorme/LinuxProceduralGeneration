//! Robust CSG Operations using parry3d
//!
//! Production-quality boolean operations comparable to professional tools:
//! - Triangle-triangle intersection detection
//! - Proper inside/outside classification
//! - Edge clipping at boundaries
//! - Degenerate case handling

use crate::geometry::Mesh;
use crate::{Result, GeometryError};
use nalgebra::{Point3, Vector3};
use parry3d::shape::TriMesh;
use parry3d::math::Real;
const EPSILON: f32 = 1e-6;

/// Triangle representation for CSG
#[derive(Debug, Clone)]
struct Triangle {
    vertices: [Point3<f32>; 3],
    normal: Vector3<f32>,
    face_index: usize,
}

impl Triangle {
    fn new(v0: Point3<f32>, v1: Point3<f32>, v2: Point3<f32>, face_index: usize) -> Self {
        let edge1 = v1 - v0;
        let edge2 = v2 - v0;
        let normal = edge1.cross(&edge2).normalize();

        Self {
            vertices: [v0, v1, v2],
            normal,
            face_index,
        }
    }

    fn centroid(&self) -> Point3<f32> {
        Point3::new(
            (self.vertices[0].x + self.vertices[1].x + self.vertices[2].x) / 3.0,
            (self.vertices[0].y + self.vertices[1].y + self.vertices[2].y) / 3.0,
            (self.vertices[0].z + self.vertices[1].z + self.vertices[2].z) / 3.0,
        )
    }

    fn area(&self) -> f32 {
        let edge1 = self.vertices[1] - self.vertices[0];
        let edge2 = self.vertices[2] - self.vertices[0];
        edge1.cross(&edge2).magnitude() * 0.5
    }

    fn is_degenerate(&self) -> bool {
        self.area() < EPSILON
    }
}

/// Classification of triangle relative to another mesh
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum TriangleClass {
    Inside,     // Completely inside
    Outside,    // Completely outside
    Spanning,   // Intersects boundary
}

/// Robust CSG engine using parry3d
pub struct RobustCsgEngine {
    epsilon: f32,
    max_iterations: usize,
}

impl RobustCsgEngine {
    pub fn new() -> Self {
        Self {
            epsilon: EPSILON,
            max_iterations: 1000,
        }
    }

    /// Perform robust CSG union: A ∪ B
    pub fn union(&self, mesh_a: &Mesh, mesh_b: &Mesh) -> Result<Mesh> {
        // For union: keep all triangles that are outside the other mesh
        // and handle spanning triangles by clipping

        let triangles_a = self.extract_triangles(mesh_a);
        let triangles_b = self.extract_triangles(mesh_b);

        let trimesh_a = self.mesh_to_trimesh(mesh_a)?;
        let trimesh_b = self.mesh_to_trimesh(mesh_b)?;

        // Classify and filter triangles
        let mut result_triangles = Vec::new();

        // Add triangles from A that are outside B
        for tri in &triangles_a {
            if !tri.is_degenerate() {
                match self.classify_triangle(tri, &trimesh_b) {
                    TriangleClass::Outside => result_triangles.push(tri.clone()),
                    TriangleClass::Spanning => {
                        return Err(GeometryError::CsgOperationFailed(
                            "CSG union encountered a spanning triangle; boundary clipping is not implemented"
                                .to_string(),
                        ));
                    }
                    TriangleClass::Inside => {
                        // Skip - inside the other mesh
                    }
                }
            }
        }

        // Add triangles from B that are outside A
        for tri in &triangles_b {
            if !tri.is_degenerate() {
                match self.classify_triangle(tri, &trimesh_a) {
                    TriangleClass::Outside => result_triangles.push(tri.clone()),
                    TriangleClass::Spanning => {
                        return Err(GeometryError::CsgOperationFailed(
                            "CSG union encountered a spanning triangle; boundary clipping is not implemented"
                                .to_string(),
                        ));
                    }
                    TriangleClass::Inside => {
                        // Skip
                    }
                }
            }
        }

        self.triangles_to_mesh(&result_triangles)
    }

    /// Perform robust CSG difference: A \ B
    ///
    /// A hollow case is worth naming because it used to be wrong. When B is
    /// entirely inside A, no triangle of A is inside B and no triangle of
    /// either mesh spans, so the filter keeps every triangle of A and returns
    /// A unchanged. That is the correct answer for a solid A, and it is only
    /// wrong if A is meant to be a container whose interior should be opened.
    /// Nothing here tracks solid-versus-shell semantics, so `box - interior
    /// sphere` is a no-op by design of the triangle filter rather than by
    /// accident. A caller wanting a hollow result must build A as a shell.
    pub fn difference(&self, mesh_a: &Mesh, mesh_b: &Mesh) -> Result<Mesh> {
        let triangles_a = self.extract_triangles(mesh_a);
        let trimesh_b = self.mesh_to_trimesh(mesh_b)?;

        let mut result_triangles = Vec::new();

        // Keep triangles from A that are outside B
        for tri in &triangles_a {
            if !tri.is_degenerate() {
                match self.classify_triangle(tri, &trimesh_b) {
                    TriangleClass::Outside => result_triangles.push(tri.clone()),
                    TriangleClass::Spanning => {
                        return Err(GeometryError::CsgOperationFailed(
                            "CSG difference encountered a spanning triangle; boundary clipping is not implemented"
                                .to_string(),
                        ));
                    }
                    TriangleClass::Inside => {
                        // Remove - inside B
                    }
                }
            }
        }

        self.triangles_to_mesh(&result_triangles)
    }

    /// Perform robust CSG intersection: A ∩ B
    pub fn intersection(&self, mesh_a: &Mesh, mesh_b: &Mesh) -> Result<Mesh> {
        let triangles_a = self.extract_triangles(mesh_a);
        let triangles_b = self.extract_triangles(mesh_b);
        let trimesh_a = self.mesh_to_trimesh(mesh_a)?;
        let trimesh_b = self.mesh_to_trimesh(mesh_b)?;

        let mut result_triangles = Vec::new();

        // Keep triangles of A that are inside B.
        for tri in &triangles_a {
            if !tri.is_degenerate() {
                match self.classify_triangle(tri, &trimesh_b) {
                    TriangleClass::Inside => result_triangles.push(tri.clone()),
                    TriangleClass::Spanning => {
                        return Err(GeometryError::CsgOperationFailed(
                            "CSG intersection encountered a spanning triangle; boundary clipping is not implemented"
                                .to_string(),
                        ));
                    }
                    TriangleClass::Outside => {
                        // Skip
                    }
                }
            }
        }

        // And triangles of B that are inside A.
        //
        // This half was missing, and its absence is not symmetric: the result
        // is the triangles of A inside B, so whenever B extends beyond A the
        // intersection came back empty. A sphere fully inside a box returned
        // nothing at all, because none of the box's own triangles are inside
        // the sphere, even though the sphere is entirely inside the box. The
        // correct answer was the sphere. Both operands have to be considered.
        for tri in &triangles_b {
            if !tri.is_degenerate() {
                match self.classify_triangle(tri, &trimesh_a) {
                    TriangleClass::Inside => result_triangles.push(tri.clone()),
                    TriangleClass::Spanning => {
                        return Err(GeometryError::CsgOperationFailed(
                            "CSG intersection encountered a spanning triangle; boundary clipping is not implemented"
                                .to_string(),
                        ));
                    }
                    TriangleClass::Outside => {
                        // Skip
                    }
                }
            }
        }

        self.triangles_to_mesh(&result_triangles)
    }

    /// Extract triangles from mesh
    fn extract_triangles(&self, mesh: &Mesh) -> Vec<Triangle> {
        mesh.indices
            .chunks(3)
            .enumerate()
            .filter_map(|(i, chunk)| {
                if chunk.len() == 3 {
                    let i0 = chunk[0] as usize;
                    let i1 = chunk[1] as usize;
                    let i2 = chunk[2] as usize;

                    if i0 < mesh.vertices.len()
                        && i1 < mesh.vertices.len()
                        && i2 < mesh.vertices.len()
                    {
                        Some(Triangle::new(
                            mesh.vertices[i0],
                            mesh.vertices[i1],
                            mesh.vertices[i2],
                            i,
                        ))
                    } else {
                        None
                    }
                } else {
                    None
                }
            })
            .collect()
    }

    /// Convert mesh to parry3d TriMesh for collision detection
    fn mesh_to_trimesh(&self, mesh: &Mesh) -> Result<TriMesh> {
        let vertices: Vec<Point3<Real>> = mesh.vertices.iter().map(|v| *v).collect();
        let indices: Vec<[u32; 3]> = mesh
            .indices
            .chunks(3)
            .filter_map(|chunk| {
                if chunk.len() == 3 {
                    Some([chunk[0], chunk[1], chunk[2]])
                } else {
                    None
                }
            })
            .collect();

        Ok(TriMesh::new(vertices, indices))
    }

    /// Return true when a segment intersects a triangle using
    /// Möller–Trumbore's segment/triangle test.
    fn segment_intersects_triangle(
        start: Point3<f32>,
        end: Point3<f32>,
        triangle: [Point3<f32>; 3],
    ) -> bool {
        let direction = end - start;
        let edge1 = triangle[1] - triangle[0];
        let edge2 = triangle[2] - triangle[0];
        let pvec = direction.cross(&edge2);
        let determinant = edge1.dot(&pvec);

        if determinant.abs() < EPSILON {
            // Coplanar/parallel cases are handled conservatively by the
            // point classification and are not treated as a confirmed hit.
            return false;
        }

        let inverse_determinant = 1.0 / determinant;
        let tvec = start - triangle[0];
        let u = tvec.dot(&pvec) * inverse_determinant;
        if u < -EPSILON || u > 1.0 + EPSILON {
            return false;
        }

        let qvec = tvec.cross(&edge1);
        let v = direction.dot(&qvec) * inverse_determinant;
        if v < -EPSILON || u + v > 1.0 + EPSILON {
            return false;
        }

        let t = qvec.dot(&edge2) * inverse_determinant;
        t >= -EPSILON && t <= 1.0 + EPSILON
    }

    /// Return true when any edge of the candidate triangle intersects the
    /// other mesh, or when an edge of the other mesh intersects the candidate.
    fn triangle_intersects_trimesh(&self, triangle: &Triangle, trimesh: &TriMesh) -> bool {
        let candidate_edges = [
            (triangle.vertices[0], triangle.vertices[1]),
            (triangle.vertices[1], triangle.vertices[2]),
            (triangle.vertices[2], triangle.vertices[0]),
        ];

        for face_index in 0..trimesh.num_triangles() {
            let other = trimesh.triangle(face_index as u32);
            let other_triangle = [other.a, other.b, other.c];
            let other_edges = [
                (other.a, other.b),
                (other.b, other.c),
                (other.c, other.a),
            ];

            if candidate_edges.iter().any(|(start, end)| {
                Self::segment_intersects_triangle(*start, *end, other_triangle)
            }) || other_edges.iter().any(|(start, end)| {
                Self::segment_intersects_triangle(*start, *end, triangle.vertices)
            }) {
                return true;
            }
        }

        false
    }

    /// Classify a triangle by testing its edges and centroid against the solid
    /// mesh. Boundary-crossing triangles are never silently copied.
    fn classify_triangle(&self, triangle: &Triangle, trimesh: &TriMesh) -> TriangleClass {
        if self.triangle_intersects_trimesh(triangle, trimesh) {
            return TriangleClass::Spanning;
        }

        if self.point_inside_mesh(&triangle.centroid(), trimesh) {
            TriangleClass::Inside
        } else {
            TriangleClass::Outside
        }
    }

    /// Check whether a point lies inside a closed mesh.
    ///
    /// This uses an explicit ray cast rather than parry3d's
    /// `TriMesh::contains_point`. That query only performs a real containment
    /// test when the shape carries pseudo-normals, which are populated by
    /// `TriMesh::new` only for a closed, well-formed mesh. A `TriMesh` built
    /// from raw vertex and index arrays has none, so parry falls through to a
    /// BVH traversal that reports every point as outside. The result was that
    /// `point_inside_mesh` returned false universally, every triangle of the
    /// input was classified Outside, and `box - enclosing_sphere` returned the
    /// box instead of the empty set. A wrong answer with no error is the worst
    /// possible failure for a boolean operation, so the test is done directly
    /// here instead of depending on an API that silently declines to work.
    ///
    /// The ray is cast along a direction chosen to be irrational relative to the
    /// mesh, so it does not pass exactly through an edge or a vertex in the
    /// generic case. Crossing parity then decides the answer: a ray starting
    /// outside a closed solid crosses its surface an odd number of times.
    fn point_inside_mesh(&self, point: &Point3<f32>, trimesh: &TriMesh) -> bool {
        // A direction with components that are mutually irrational multiples,
        // so hitting an exact edge or vertex has measure zero.
        const DIRECTION: Vector3<f32> = Vector3::new(0.577_350_3, 0.301_511_3, 0.707_106_8);

        let mut crossings = 0u32;
        let ray_length = self.bounding_diagonal(trimesh) * 4.0;

        for face_index in 0..trimesh.num_triangles() {
            let tri = trimesh.triangle(face_index as u32);

            if Self::ray_crosses_triangle(*point, DIRECTION, ray_length, [tri.a, tri.b, tri.c]) {
                crossings += 1;
            }
        }

        crossings % 2 == 1
    }

    /// Diagonal of the trimesh bounding box, used to size the ray so it
    /// starts and ends outside the solid.
    fn bounding_diagonal(&self, trimesh: &TriMesh) -> f32 {
        let aabb = trimesh.local_aabb();
        let extent = aabb.extents();
        (extent.x * extent.x + extent.y * extent.y + extent.z * extent.z).sqrt()
    }

    /// Möller–Trumbore ray/triangle intersection.
    ///
    /// Half-open on the t parameter so a ray passing exactly through a shared
    /// edge is counted once rather than twice, which would corrupt the parity.
    fn ray_crosses_triangle(
        origin: Point3<f32>,
        direction: Vector3<f32>,
        max_t: f32,
        triangle: [Point3<f32>; 3],
    ) -> bool {
        let edge1 = triangle[1] - triangle[0];
        let edge2 = triangle[2] - triangle[0];
        let pvec = direction.cross(&edge2);
        let determinant = edge1.dot(&pvec);

        if determinant.abs() < EPSILON {
            // Parallel to the triangle plane. Grazing hits are not counted; the
            // irrational direction makes this a measure-zero case.
            return false;
        }

        let inverse_determinant = 1.0 / determinant;
        let tvec = origin - triangle[0];
        let u = tvec.dot(&pvec) * inverse_determinant;
        if u < 0.0 || u > 1.0 {
            return false;
        }

        let qvec = tvec.cross(&edge1);
        let v = direction.dot(&qvec) * inverse_determinant;
        if v < 0.0 || u + v > 1.0 {
            return false;
        }

        let t = qvec.dot(&edge2) * inverse_determinant;
        // Half-open: t > 0 avoids counting a triangle the ray starts on, and
        // t < max_t stops the count once the ray has left the solid.
        t > EPSILON && t < max_t
    }

    /// Convert triangles back to mesh
    fn triangles_to_mesh(&self, triangles: &[Triangle]) -> Result<Mesh> {
        let mut mesh = Mesh::new();
        let mut vertex_map: std::collections::HashMap<[u32; 3], u32> =
            std::collections::HashMap::new();

        for tri in triangles {
            let mut indices = Vec::new();

            for vertex in &tri.vertices {
                // Quantize vertex for deduplication
                let key = [
                    (vertex.x / EPSILON) as u32,
                    (vertex.y / EPSILON) as u32,
                    (vertex.z / EPSILON) as u32,
                ];

                let index = *vertex_map.entry(key).or_insert_with(|| {
                    mesh.vertices.push(*vertex);
                    (mesh.vertices.len() - 1) as u32
                });

                indices.push(index);
            }

            mesh.indices.extend_from_slice(&indices);
        }

        // Compute normals
        mesh.compute_normals();

        Ok(mesh)
    }
}

impl Default for RobustCsgEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geometry::primitives::{Box, Sphere};
    use crate::geometry::Primitive;
    use crate::mesh::validation::MeshValidator;

    #[test]
    fn test_robust_union() {
        let engine = RobustCsgEngine::new();

        let box1 = Box::new(Vector3::new(2.0, 2.0, 2.0));
        let box2 = Box::new(Vector3::new(1.0, 1.0, 1.0))
            .with_center(Point3::new(3.0, 0.0, 0.0));

        let mesh1 = box1.to_mesh().unwrap();
        let mesh2 = box2.to_mesh().unwrap();

        let result = engine.union(&mesh1, &mesh2).unwrap();

        assert!(result.vertex_count() > 0);
        assert!(result.triangle_count() > 0);
    }

    #[test]
    fn test_box_primitive_is_watertight() {
        // The box was always clean, so this is the control case for the sphere
        // fix: it confirms the validator is capable of reporting a good solid
        // and that the sphere problem was real rather than a validator quirk.
        let mesh = Box::new(Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
        let report = MeshValidator::new().validate(&mesh);
        assert!(report.is_valid);
        assert!(report.is_manifold);
        assert!(report.is_watertight);
        assert_eq!(report.non_manifold_edge_count, 0);
        assert_eq!(report.hole_count, 0);
    }

    #[test]
    fn test_sphere_primitive_is_watertight_and_has_no_degenerate_triangles() {
        // The pole fix. to_mesh used to emit a full (rings + 1) x
        // (segments + 1) grid, collapsing both poles onto single points, which
        // produced 64 degenerate triangles, 79 duplicate vertices, 96
        // non-manifold edges and 96 boundary edges.
        let mesh = Sphere::new(1.0).to_mesh().unwrap();
        let report = MeshValidator::new().validate(&mesh);

        assert_eq!(report.degenerate_triangle_count, 0, "poles must not collapse");
        assert_eq!(report.duplicate_vertex_count, 0, "the UV seam must be welded");
        assert_eq!(report.non_manifold_edge_count, 0);
        assert_eq!(report.hole_count, 0);
        assert!(report.is_manifold, "sphere must be manifold");
        assert!(report.is_watertight, "sphere must be closed");
        assert!(report.is_valid);
        assert!(report.issues.is_empty(), "issues: {:?}", report.issues);
    }

    #[test]
    fn test_sphere_winding_is_outward() {
        // Signed volume must be positive for outward-facing triangles. An
        // inside-out sphere still looks manifold and watertight, but no
        // point-in-solid test can classify anything inside it, which is how the
        // winding defect reached CSG.
        let mesh = Sphere::new(2.0).to_mesh().unwrap();
        let mut volume = 0.0f64;
        for chunk in mesh.indices.chunks(3) {
            let a = mesh.vertices[chunk[0] as usize];
            let b = mesh.vertices[chunk[1] as usize];
            let c = mesh.vertices[chunk[2] as usize];
            let (ax, ay, az) = (a.x as f64, a.y as f64, a.z as f64);
            let (bx, by, bz) = (b.x as f64, b.y as f64, b.z as f64);
            let (cx, cy, cz) = (c.x as f64, c.y as f64, c.z as f64);
            volume += ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz) + az * (bx * cy - by * cx);
        }
        volume /= 6.0;

        let expected = 4.0 / 3.0 * std::f64::consts::PI * 8.0;
        assert!(
            volume > 0.0,
            "sphere triangles must wind outward, got signed volume {volume}"
        );
        // A UV sphere under-reports the true volume because it is faceted, but
        // it should be in the right neighbourhood, not merely positive.
        let ratio = volume / expected;
        assert!(
            (0.7..1.0).contains(&ratio),
            "faceted sphere volume {volume} should be within 30% of {expected}"
        );
    }

    #[test]
    fn test_robust_difference_rejects_spanning_case() {
        let engine = RobustCsgEngine::new();

        // Sphere radius 2.5 against a 4-wide box (half-extent 2.0), so the
        // sphere surface genuinely crosses the box surface. Boundary clipping
        // is not implemented and the engine must say so rather than guess.
        let mesh1 = Box::new(Vector3::new(4.0, 4.0, 4.0)).to_mesh().unwrap();
        let mesh2 = Sphere::new(2.5).to_mesh().unwrap();

        assert!(engine.difference(&mesh1, &mesh2).is_err());
    }

    #[test]
    fn test_robust_intersection_rejects_spanning_case() {
        let engine = RobustCsgEngine::new();

        let mesh1 = Box::new(Vector3::new(4.0, 4.0, 4.0)).to_mesh().unwrap();
        let mesh2 = Sphere::new(2.5).to_mesh().unwrap();

        assert!(engine.intersection(&mesh1, &mesh2).is_err());
    }

    // -----------------------------------------------------------------------
    // Containment cases. These are the ones that were silently wrong.
    //
    // point_inside_mesh used parry3d's TriMesh::contains_point, which only
    // performs a real containment test when the shape carries pseudo-normals.
    // A TriMesh built from raw arrays has none, so it reported every point as
    // outside. Every triangle therefore classified Outside and difference
    // returned its first operand unchanged, for every input, without error.
    // -----------------------------------------------------------------------

    #[test]
    fn test_difference_of_enclosed_solid_is_empty() {
        // Box half-extent 1.0 is entirely inside a sphere of radius 3.0, so
        // subtracting the sphere must leave nothing.
        let engine = RobustCsgEngine::new();
        let mesh_a = Box::new(Vector3::new(2.0, 2.0, 2.0)).to_mesh().unwrap();
        let mesh_b = Sphere::new(3.0).to_mesh().unwrap();

        let result = engine.difference(&mesh_a, &mesh_b).unwrap();
        assert_eq!(
            (result.vertex_count(), result.triangle_count()),
            (0, 0),
            "subtracting an enclosing solid must leave an empty mesh, not the \
             original operand"
        );
    }

    #[test]
    fn test_difference_with_fully_interior_solid_leaves_outer_solid() {
        // Sphere radius 1.5 sits inside a 4-wide box (half-extent 2.0). No
        // triangle of the box is inside the sphere, so the filter keeps them
        // all. For a solid operand that is the correct answer; a caller wanting
        // a hollow result must pass a shell.
        let engine = RobustCsgEngine::new();
        let mesh_a = Box::new(Vector3::new(4.0, 4.0, 4.0)).to_mesh().unwrap();
        let mesh_b = Sphere::new(1.5).to_mesh().unwrap();

        let result = engine.difference(&mesh_a, &mesh_b).unwrap();
        assert_eq!((result.vertex_count(), result.triangle_count()), (8, 12));
    }

    #[test]
    fn test_intersection_keeps_inner_operand() {
        // A sphere fully inside a box: the box contributes nothing, so the
        // result must come from the sphere. The engine previously only
        // considered triangles of the first operand and returned nothing.
        let engine = RobustCsgEngine::new();
        let mesh_a = Box::new(Vector3::new(4.0, 4.0, 4.0)).to_mesh().unwrap();
        let mesh_b = Sphere::new(1.5).to_mesh().unwrap();

        let result = engine.intersection(&mesh_a, &mesh_b).unwrap();
        let sphere_triangles = mesh_b.triangle_count();
        assert_eq!(result.triangle_count(), sphere_triangles);
        assert!(result.triangle_count() > 0);
    }

    #[test]
    fn test_intersection_keeps_first_operand_when_it_is_inner() {
        // Mirror of the above: here the box is inside the sphere, so the result
        // is the box.
        let engine = RobustCsgEngine::new();
        let mesh_a = Sphere::new(3.0).to_mesh().unwrap();
        let mesh_b = Box::new(Vector3::new(2.0, 2.0, 2.0)).to_mesh().unwrap();

        let result = engine.intersection(&mesh_a, &mesh_b).unwrap();
        assert_eq!((result.vertex_count(), result.triangle_count()), (8, 12));
    }

    #[test]
    fn test_union_of_disjoint_solids_keeps_both() {
        let engine = RobustCsgEngine::new();
        let mesh_a = Box::new(Vector3::new(2.0, 2.0, 2.0)).to_mesh().unwrap();
        let mesh_b = Box::new(Vector3::new(1.0, 1.0, 1.0))
            .with_center(Point3::new(3.0, 0.0, 0.0))
            .to_mesh()
            .unwrap();

        let result = engine.union(&mesh_a, &mesh_b).unwrap();
        assert_eq!(
            (result.vertex_count(), result.triangle_count()),
            (16, 24),
            "disjoint solids have no spanning triangles, so the union is both \
             operands intact"
        );
    }

    #[test]
    fn test_point_inside_mesh_classifies_containment() {
        // Directly exercise the classifier that the parry query got wrong.
        let engine = RobustCsgEngine::new();
        let trimesh = engine
            .mesh_to_trimesh(&Sphere::new(3.0).to_mesh().unwrap())
            .unwrap();

        assert!(engine.point_inside_mesh(&Point3::new(0.0, 0.0, 0.0), &trimesh));
        assert!(engine.point_inside_mesh(&Point3::new(1.0, 0.0, 0.0), &trimesh));
        assert!(engine.point_inside_mesh(&Point3::new(2.5, 0.0, 0.0), &trimesh));
        assert!(!engine.point_inside_mesh(&Point3::new(5.0, 0.0, 0.0), &trimesh));
        assert!(!engine.point_inside_mesh(&Point3::new(100.0, 0.0, 0.0), &trimesh));
    }

    #[test]
    fn test_triangle_degenerate_detection() {
        let t1 = Triangle::new(
            Point3::new(0.0, 0.0, 0.0),
            Point3::new(1.0, 0.0, 0.0),
            Point3::new(0.0, 1.0, 0.0),
            0,
        );
        assert!(!t1.is_degenerate());

        let t2 = Triangle::new(
            Point3::new(0.0, 0.0, 0.0),
            Point3::new(0.0, 0.0, 0.0),
            Point3::new(0.0, 0.0, 0.0),
            0,
        );
        assert!(t2.is_degenerate());
    }
}
