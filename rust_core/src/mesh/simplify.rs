//! Mesh simplification by quadric error metrics.
//!
//! Edge-collapse decimation in the sense of Garland and Heckbert (1997), with
//! the corrections that production use actually requires. Each exists because
//! omitting it produces a plausible-looking mesh that is wrong:
//!
//! - **Boundary preservation.** A vertex on an open boundary is penalised for
//!   *moving*. The usual alternative is to invent a plane quadric for the
//!   boundary, and that does not work: a boundary has no second face to define a
//!   plane, so any plane invented for it is arbitrary and usually evaluates to
//!   near-zero error, which means the simplifier eats the rim first, because
//!   rims are cheap. Penalising the displacement states the actual requirement.
//! - **Normal-flip rejection.** A collapse that reverses an adjacent triangle is
//!   rejected even when its quadric error is small. This is the main way a QEM
//!   simplifier yields a mesh that looks decimated but renders with holes.
//! - **Link condition.** A collapse is legal only when the vertices shared by its
//!   two endpoints' one-rings are exactly the vertices opposite the edge in its
//!   two faces. This is what keeps a closed mesh closed instead of welding
//!   unrelated sheets that merely pass near each other into a non-manifold mess.
//! - **Attribute error in the metric.** UV error is accumulated with the same
//!   area-weighted plane quadrics, in UV space, and added to the geometric error.
//!   A collapse that wrecks the texture is a bad collapse even when the
//!   silhouette survives, which is the same reasoning behind Nanite's "Lerp UVs"
//!   switch: once UVs are per corner, an attribute that cannot be interpolated
//!   makes the error unaccountable.
//!
//! Marked sharp edges are never collapsed, so creases authored through
//! [`crate::geometry::Mesh::mark_edge_sharp`] survive decimation instead of being
//! averaged away.
//!
//! # Cost
//!
//! A collapse refreshes the quadrics of the two-ring closure of the vertices it
//! touched, and requeues only that neighbourhood's edges. Faces are marked dead in
//! place rather than compacted, so face indices stay stable and the adjacency
//! bookkeeping stays simple; compaction happens once at the end. Accumulation is
//! idempotent because every disturbed face is reset-then-reaccumulated exactly
//! once, which is the usual way this algorithm corrupts its own error metric.

use crate::geometry::Mesh;
use crate::{GeometryError, Result};
use nalgebra::{Point3, Vector3};
use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashSet};

/// Penalty on displacing a vertex that lies on an open boundary.
///
/// Squared, so it composes with the quadric's own squared-distance units. Large
/// enough to lose to any interior collapse, small enough that squaring it into a
/// cost cannot overflow.
const BOUNDARY_PENALTY: f32 = 1.0e3;

/// Weight of UV error relative to geometric error.
///
/// Both terms are squared distances in their own units and UV units are
/// arbitrary, so the ratio is a judgement call. This one keeps texture
/// distortion from dominating on a unit-sized mesh while still rejecting
/// collapses that visibly tear a map.
const UV_ERROR_WEIGHT: f32 = 0.05;


/// Relative singularity threshold for the quadric's linear solve.
///
/// Compared against the magnitude of the block, not against zero, so it means the
/// same thing for a unit-sized mesh and one spanning a million units.
const SINGULAR_EPS: f64 = 1.0e-12;

/// Symmetric 4x4 quadric stored as its upper triangle.
///
/// `error(p)` sums the squared distances from `p` to the represented planes, and
/// minimising it over `p` gives the best replacement position for a collapse.
#[derive(Debug, Clone, Copy, Default)]
pub(crate) struct Quadric {
    a: f32,
    b: f32,
    c: f32,
    d: f32,
    e: f32,
    f: f32,
    g: f32,
    h: f32,
    i: f32,
    j: f32,
}

impl Quadric {
    /// A quadric from the plane `ax + by + cz + d = 0`, scaled by `weight`.
    pub fn from_plane(a: f32, b: f32, c: f32, d: f32, weight: f32) -> Self {
        Self {
            a: a * a * weight,
            b: a * b * weight,
            c: a * c * weight,
            d: a * d * weight,
            e: b * b * weight,
            f: b * c * weight,
            g: b * d * weight,
            h: c * c * weight,
            i: c * d * weight,
            j: d * d * weight,
        }
    }

    /// A quadric from a triangle's plane, weighted by its area.
    ///
    /// Area weighting is what makes the metric a least-squares fit rather than an
    /// unweighted plane count, so a large triangle dominates its own vertices and
    /// a sliver barely contributes.
    pub fn from_triangle(v0: &Point3<f32>, v1: &Point3<f32>, v2: &Point3<f32>) -> Self {
        let cross = (v1 - v0).cross(&(v2 - v0));
        let twice_area = cross.norm();
        if twice_area <= 1e-20 {
            // A degenerate triangle has no well-defined plane. The zero quadric is
            // the honest answer; inventing one would bias every collapse touching
            // it toward an arbitrary direction.
            return Self::default();
        }
        let normal = cross / twice_area;
        Self::from_plane(
            normal.x,
            normal.y,
            normal.z,
            -normal.dot(&v0.coords),
            0.5 * twice_area,
        )
    }

    /// The area-weighted plane quadric of a triangle in UV space, lifted into the
    /// same 4x4 form with the third coordinate unused.
    pub fn from_uv_triangle(uv0: (f32, f32), uv1: (f32, f32), uv2: (f32, f32)) -> Self {
        let e1 = (uv1.0 - uv0.0, uv1.1 - uv0.1);
        let e2 = (uv2.0 - uv0.0, uv2.1 - uv0.1);
        let twice_area = (e1.0 * e2.1 - e1.1 * e2.0).abs();
        if twice_area <= 1e-20 {
            return Self::default();
        }
        let (nx, ny) = (e2.1 - e1.1, e1.0 - e2.0);
        let length = (nx * nx + ny * ny).sqrt();
        if length <= 1e-20 {
            return Self::default();
        }
        let (nx, ny) = (nx / length, ny / length);
        Self::from_plane(
            nx,
            ny,
            0.0,
            -(nx * uv0.0 + ny * uv0.1),
            0.5 * twice_area * UV_ERROR_WEIGHT,
        )
    }

    pub fn add(&self, other: &Self) -> Self {
        Self {
            a: self.a + other.a,
            b: self.b + other.b,
            c: self.c + other.c,
            d: self.d + other.d,
            e: self.e + other.e,
            f: self.f + other.f,
            g: self.g + other.g,
            h: self.h + other.h,
            i: self.i + other.i,
            j: self.j + other.j,
        }
    }

    /// Squared distance from `v` to the represented planes, never negative and
    /// never non-finite.
    ///
    /// The clamp matters: this is a sort key, and a sum of squares that rounds
    /// slightly negative, or overflows, would sort a bad collapse to the front.
    pub fn error(&self, v: &Point3<f32>) -> f32 {
        let (x, y, z) = (v.x, v.y, v.z);
        let value = self.a * x * x
            + 2.0 * self.b * x * y
            + 2.0 * self.c * x * z
            + 2.0 * self.d * x
            + self.e * y * y
            + 2.0 * self.f * y * z
            + 2.0 * self.g * y
            + self.h * z * z
            + 2.0 * self.i * z
            + self.j;
        if value.is_finite() {
            value.max(0.0)
        } else {
            f32::MAX
        }
    }

    /// The point minimising this quadric, or `None` when the linear part is
    /// singular.
    ///
    /// Singular is normal on a flat region: every point of a plane minimises the
    /// distance to it, so the caller must fall back to an endpoint or the
    /// midpoint rather than divide by a near-zero determinant.
    pub fn minimiser(&self) -> Option<Point3<f32>> {
        let m = [
            [self.a as f64, self.b as f64, self.c as f64],
            [self.b as f64, self.e as f64, self.f as f64],
            [self.c as f64, self.f as f64, self.h as f64],
        ];
        let rhs = [-(self.d as f64), -(self.g as f64), -(self.i as f64)];

        let det = m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
        let scale = m[0][0].abs() + m[1][1].abs() + m[2][2].abs();
        if !det.is_finite() || det.abs() <= SINGULAR_EPS * scale.max(1.0e-30) {
            return None;
        }

        let c0 = rhs[0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (rhs[1] * m[2][2] - m[1][2] * rhs[2])
            + m[0][2] * (rhs[1] * m[2][1] - m[1][1] * rhs[2]);
        let c1 = m[0][0] * (rhs[1] * m[2][2] - m[1][2] * rhs[2])
            - rhs[0] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * rhs[2] - rhs[1] * m[2][0]);
        let c2 = m[0][0] * (m[1][1] * rhs[2] - rhs[1] * m[2][1])
            - m[0][1] * (m[1][0] * rhs[2] - rhs[1] * m[2][0])
            + rhs[0] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);

        let point = Point3::new((c0 / det) as f32, (c1 / det) as f32, (c2 / det) as f32);
        if point.x.is_finite() && point.y.is_finite() && point.z.is_finite() {
            Some(point)
        } else {
            None
        }
    }
}

/// A queued edge collapse, ordered so the cheapest is popped first.
#[derive(Debug, Clone, Copy)]
struct Candidate {
    error: f32,
    /// The endpoint that is absorbed.
    from: u32,
    /// The endpoint that survives, and moves to `target`.
    into: u32,
    target: Point3<f32>,
}

impl PartialEq for Candidate {
    fn eq(&self, other: &Self) -> bool {
        self.error == other.error && self.from == other.from && self.into == other.into
    }
}
impl Eq for Candidate {}
impl Ord for Candidate {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reversed, because `BinaryHeap` is a max-heap and the cheapest collapse
        // must come off first. The index tiebreak makes the order total, which
        // `BinaryHeap` requires in order to behave.
        other
            .error
            .partial_cmp(&self.error)
            .unwrap_or(Ordering::Equal)
            .then_with(|| other.from.cmp(&self.from))
            .then_with(|| other.into.cmp(&self.into))
    }
}
impl PartialOrd for Candidate {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// Working state for one simplification run.
struct Simplifier<'a> {
    source: &'a Mesh,
    /// Face geometry. Dead faces stay in place so indices remain stable.
    faces: Vec<[u32; 3]>,
    face_uvs: Vec<[(f32, f32); 3]>,
    face_alive: Vec<bool>,
    /// True when per-corner UVs were sampled from per-vertex UVs, so the output
    /// must not claim an authored per-corner layer.
    synthesised_face_uvs: bool,
    /// Live face indices per vertex.
    vertex_faces: Vec<Vec<usize>>,
    positions: Vec<Point3<f32>>,
    normals: Vec<Vector3<f32>>,
    quadrics: Vec<Quadric>,
    uv_quadrics: Vec<Quadric>,
    /// True when a vertex lies on an open boundary.
    on_boundary: Vec<bool>,
    live_faces: usize,
    sharp: Vec<(u32, u32)>,
}

impl<'a> Simplifier<'a> {
    fn new(mesh: &'a Mesh) -> Result<Self> {
        let face_count = mesh.triangle_count();
        if mesh.indices.len() != face_count * 3 {
            return Err(GeometryError::MeshProcessingError(
                "index buffer is not a whole number of triangles".to_string(),
            ));
        }
        for &index in &mesh.indices {
            if index as usize >= mesh.vertices.len() {
                return Err(GeometryError::MeshProcessingError(format!(
                    "index {index} is outside the {} available vertices",
                    mesh.vertices.len()
                )));
            }
        }

        let mut faces = Vec::with_capacity(face_count);
        for f in 0..face_count {
            faces.push([
                mesh.indices[f * 3],
                mesh.indices[f * 3 + 1],
                mesh.indices[f * 3 + 2],
            ]);
        }

        let has_per_vertex_uvs = mesh.uvs.len() == mesh.vertices.len();
        let (face_uvs, synthesised_face_uvs) = if mesh.face_uvs.len() == face_count {
            (mesh.face_uvs.clone(), false)
        } else {
            // Sample the per-vertex parameterisation at each corner, so a mesh
            // without per-corner UVs still simplifies without losing its texture
            // coordinates.
            let sampled = faces
                .iter()
                .map(|f| {
                    [
                        if has_per_vertex_uvs {
                            mesh.uvs[f[0] as usize]
                        } else {
                            (0.0, 0.0)
                        },
                        if has_per_vertex_uvs {
                            mesh.uvs[f[1] as usize]
                        } else {
                            (0.0, 0.0)
                        },
                        if has_per_vertex_uvs {
                            mesh.uvs[f[2] as usize]
                        } else {
                            (0.0, 0.0)
                        },
                    ]
                })
                .collect();
            (sampled, true)
        };

        let mut state = Self {
            source: mesh,
            faces,
            face_uvs,
            face_alive: vec![true; face_count],
            synthesised_face_uvs,
            vertex_faces: Vec::new(),
            positions: mesh.vertices.clone(),
            normals: if mesh.normals.len() == mesh.vertices.len() {
                mesh.normals.clone()
            } else {
                Vec::new()
            },
            quadrics: Vec::new(),
            uv_quadrics: Vec::new(),
            on_boundary: vec![false; mesh.vertices.len()],
            live_faces: face_count,
            sharp: mesh.sharp_edges.clone(),
        };
        state.vertex_faces = build_vertex_faces(&state.faces, mesh.vertices.len());
        state.quadrics = vec![Quadric::default(); mesh.vertices.len()];
        state.uv_quadrics = vec![Quadric::default(); mesh.vertices.len()];
        state.recompute_all();
        Ok(state)
    }

    /// Recompute every derived quantity. Used at the start of a run.
    fn recompute_all(&mut self) {
        for slot in self.quadrics.iter_mut() {
            *slot = Quadric::default();
        }
        for slot in self.uv_quadrics.iter_mut() {
            *slot = Quadric::default();
        }
        for f in 0..self.faces.len() {
            if self.face_alive[f] {
                self.accumulate_face(f);
            }
        }
        self.recompute_boundary();
    }

    /// Add face `f`'s plane quadrics to its three vertices.
    fn accumulate_face(&mut self, f: usize) {
        let face = self.faces[f];
        let quadric = Quadric::from_triangle(
            &self.positions[face[0] as usize],
            &self.positions[face[1] as usize],
            &self.positions[face[2] as usize],
        );
        let uv = self.face_uvs[f];
        let uv_quadric = Quadric::from_uv_triangle(uv[0], uv[1], uv[2]);
        for &corner in &face {
            let slot = corner as usize;
            self.quadrics[slot] = self.quadrics[slot].add(&quadric);
            self.uv_quadrics[slot] = self.uv_quadrics[slot].add(&uv_quadric);
        }
    }

    /// Mark which vertices sit on an open boundary.
    fn recompute_boundary(&mut self) {
        let mut counts: std::collections::HashMap<(u32, u32), usize> =
            std::collections::HashMap::new();
        for f in 0..self.faces.len() {
            if !self.face_alive[f] {
                continue;
            }
            for k in 0..3 {
                let a = self.faces[f][k];
                let b = self.faces[f][(k + 1) % 3];
                if a == b {
                    continue;
                }
                let key = if a < b { (a, b) } else { (b, a) };
                *counts.entry(key).or_insert(0) += 1;
            }
        }
        for flag in self.on_boundary.iter_mut() {
            *flag = false;
        }
        for (&(a, b), &count) in &counts {
            if count == 1 {
                self.on_boundary[a as usize] = true;
                self.on_boundary[b as usize] = true;
            }
        }
    }

    fn is_sharp(&self, a: u32, b: u32) -> bool {
        let key = if a < b { (a, b) } else { (b, a) };
        self.sharp.contains(&key)
    }

    /// Combined cost of collapsing `from` into `into`, and where `into` lands.
    ///
    /// Candidate positions are the quadric minimiser, both endpoints, and the
    /// midpoint. Taking the endpoints as well as the minimiser matters: on a flat
    /// region the minimiser is singular, and on a long thin feature it can sit
    /// far outside the edge.
    fn evaluate(&self, from: u32, into: u32) -> Option<Candidate> {
        if from == into {
            return None;
        }
        let geometric = self.quadrics[from as usize].add(&self.quadrics[into as usize]);
        let uv_combined = self.uv_quadrics[from as usize].add(&self.uv_quadrics[into as usize]);

        let mut options: Vec<Point3<f32>> = Vec::with_capacity(4);
        options.push(self.positions[from as usize]);
        options.push(self.positions[into as usize]);
        options.push(Point3::from(
            (self.positions[from as usize].coords + self.positions[into as usize].coords) * 0.5,
        ));
        if let Some(p) = geometric.minimiser() {
            options.push(p);
        }

        let mut best: Option<(f32, Point3<f32>)> = None;
        for point in options {
            let mut error = geometric.error(&point);
            // UV error at the position the surviving corner will take, which is
            // the same choice `apply` makes, so the cost predicts the outcome.
            if let Some(uv) = self.vertex_uv(into) {
                error += uv_combined.error(&Point3::new(uv.0, uv.1, 0.0));
            }
            // Boundary vertices are penalised for moving at all.
            for endpoint in [from, into] {
                if self.on_boundary[endpoint as usize] {
                    let moved = (point - self.positions[endpoint as usize]).norm();
                    error += BOUNDARY_PENALTY * moved * moved;
                }
            }
            if !error.is_finite() {
                continue;
            }
            let better = match best {
                None => true,
                Some((current, _)) => error < current,
            };
            if better {
                best = Some((error, point));
            }
        }

        let (error, target) = best?;
        Some(Candidate {
            error,
            from,
            into,
            target,
        })
    }


    /// The UV a vertex contributes, taken from its first live incident face.
    fn vertex_uv(&self, vertex: u32) -> Option<(f32, f32)> {
        if !self.face_uvs.is_empty() {
            for &f in &self.vertex_faces[vertex as usize] {
                if !self.face_alive[f] {
                    continue;
                }
                let face = self.faces[f];
                for k in 0..3 {
                    if face[k] == vertex {
                        return Some(self.face_uvs[f][k]);
                    }
                }
            }
            return Some((0.0, 0.0));
        }
        if self.source.uvs.len() == self.source.vertices.len() {
            Some(self.source.uvs[vertex as usize])
        } else {
            None
        }
    }

    /// The two faces meeting at an edge, with the vertex opposite the edge in
    /// each. `None` unless there are exactly two, so an open or non-manifold edge
    /// is never treated as an interior edge.
    fn interior_edge_faces(&self, a: u32, b: u32) -> Option<[(usize, u32); 2]> {
        let mut found: Vec<(usize, u32)> = Vec::with_capacity(3);
        for f in 0..self.faces.len() {
            if !self.face_alive[f] {
                continue;
            }
            let face = self.faces[f];
            if face.contains(&a) && face.contains(&b) {
                let opposite = face
                    .iter()
                    .copied()
                    .find(|&c| c != a && c != b)
                    .unwrap_or(a);
                found.push((f, opposite));
                if found.len() > 2 {
                    return None;
                }
            }
        }
        if found.len() == 2 {
            Some([found[0], found[1]])
        } else {
            None
        }
    }

    /// The link condition: the vertices common to the two endpoints' one-rings
    /// must be exactly the two vertices opposite the edge.
    ///
    /// When it holds the collapse cannot weld two sheets that merely pass near
    /// each other, which is what turns a valid input into a non-manifold output.
    /// Only defined for an edge with exactly two faces, so a boundary edge
    /// returns false and is handled by the boundary penalty instead.
    fn link_condition_holds(&self, a: u32, b: u32) -> bool {
        let Some(pair) = self.interior_edge_faces(a, b) else {
            return false;
        };
        let mut shared: Vec<u32> = Vec::new();
        for &(f, _) in &pair {
            for &corner in &self.faces[f] {
                if corner != a && corner != b {
                    shared.push(corner);
                }
            }
        }
        shared.sort_unstable();
        shared.dedup();
        let mut required = [pair[0].1, pair[1].1];
        required.sort_unstable();
        shared == required
    }

    /// Reject a collapse that would reverse an adjacent triangle.
    fn preserves_orientation(&self, from: u32, into: u32, target: &Point3<f32>) -> bool {
        for f in 0..self.faces.len() {
            if !self.face_alive[f] {
                continue;
            }
            let face = self.faces[f];
            let touches_from = face.contains(&from);
            let touches_into = face.contains(&into);
            // A face containing both endpoints is removed by the collapse, so it
            // cannot flip.
            if touches_from && touches_into {
                continue;
            }
            if !touches_from && !touches_into {
                continue;
            }

            let before = [
                self.positions[face[0] as usize],
                self.positions[face[1] as usize],
                self.positions[face[2] as usize],
            ];
            // Replace by index, not by position: the two endpoints can already
            // share a position, and matching on position moves the wrong corner.
            let mut after = before;
            for k in 0..3 {
                if face[k] == from || face[k] == into {
                    after[k] = *target;
                }
            }

            let n_before = (before[1] - before[0]).cross(&(before[2] - before[0]));
            let n_after = (after[1] - after[0]).cross(&(after[2] - after[0]));
            if n_before.norm() <= 1e-20 || n_after.norm() <= 1e-20 {
                continue;
            }
            // A flip is a reversal, not merely a change of direction. A face may
            // legitimately steepen as it is dragged toward the collapse target.
            if n_before.dot(&n_after) <= 0.0 {
                return false;
            }
        }
        true
    }

    /// Queue both orientations of an edge. The link condition is symmetric but the
    /// surviving vertex, and therefore attribute interpolation, is not.
    fn evaluate_pair(&self, a: u32, b: u32, queue: &mut BinaryHeap<Candidate>) {
        if a == b {
            return;
        }
        if let Some(candidate) = self.evaluate(a, b) {
            queue.push(candidate);
        }
        if let Some(candidate) = self.evaluate(b, a) {
            queue.push(candidate);
        }
    }

    /// Apply one accepted collapse, then refresh what it disturbed.
    fn apply(&mut self, candidate: &Candidate, queue: &mut BinaryHeap<Candidate>) {
        let from = candidate.from;
        let into = candidate.into;

        // Re-point every live face that used `from` at `into`, and kill the faces
        // that end up naming the same vertex twice.
        let incident = std::mem::take(&mut self.vertex_faces[from as usize]);
        let mut touched: Vec<usize> = Vec::new();
        for f in incident {
            if !self.face_alive[f] {
                continue;
            }
            let face = self.faces[f];
            // Tested before the remap, because after it the face no longer
            // records that it referenced both endpoints.
            let collapses_to_sliver = face.contains(&into);
            let mut next = face;
            for corner in next.iter_mut() {
                if *corner == from {
                    *corner = into;
                }
            }
            if collapses_to_sliver {
                self.face_alive[f] = false;
                self.live_faces -= 1;
                continue;
            }
            self.faces[f] = next;
            self.vertex_faces[into as usize].push(f);
            touched.push(f);
        }

        // Carry the normal across, re-normalised. Averaging is safe because a
        // marked sharp edge is never collapsed, so the merged endpoints always
        // belong to the same smooth region.
        if !self.normals.is_empty() {
            let blended = self.normals[from as usize] + self.normals[into as usize];
            if blended.norm() > 1e-20 {
                self.normals[into as usize] = blended.normalize();
            }
        }

        self.positions[into as usize] = candidate.target;
        self.on_boundary[from as usize] = false;

        self.refresh_neighbourhood(&touched, queue);
    }

    /// Recompute quadrics for everything a collapse disturbed, and requeue its
    /// edges.
    fn refresh_neighbourhood(&mut self, touched: &[usize], queue: &mut BinaryHeap<Candidate>) {
        // A face's quadric is added to all three of its vertices, so recomputing
        // one vertex means every vertex sharing any of its faces must be reset
        // first or those contributions are counted twice. That set is the
        // two-ring closure of the touched vertices, which is bounded and is what
        // keeps the accumulation idempotent.
        let mut dirty: Vec<bool> = vec![false; self.positions.len()];
        let mut pending: Vec<u32> = Vec::new();
        let mut note = |v: u32, dirty: &mut Vec<bool>, pending: &mut Vec<u32>| {
            if !dirty[v as usize] {
                dirty[v as usize] = true;
                pending.push(v);
            }
        };
        for f in touched {
            if !self.face_alive[*f] {
                continue;
            }
            for &corner in &self.faces[*f] {
                note(corner, &mut dirty, &mut pending);
            }
        }
        let mut head = 0usize;
        while head < pending.len() {
            let v = pending[head];
            head += 1;
            let incident: Vec<usize> = self.vertex_faces[v as usize]
                .iter()
                .copied()
                .filter(|&f| self.face_alive[f])
                .collect();
            for f in incident {
                for &corner in &self.faces[f] {
                    note(corner, &mut dirty, &mut pending);
                }
            }
        }

        for &v in &pending {
            self.quadrics[v as usize] = Quadric::default();
            self.uv_quadrics[v as usize] = Quadric::default();
        }
        // Accumulate each disturbed face exactly once.
        let mut accumulated: Vec<bool> = vec![false; self.faces.len()];
        for &v in &pending {
            let incident: Vec<usize> = self.vertex_faces[v as usize]
                .iter()
                .copied()
                .filter(|&f| self.face_alive[f])
                .collect();
            for f in incident {
                if accumulated[f] {
                    continue;
                }
                accumulated[f] = true;
                self.accumulate_face(f);
            }
        }

        self.recompute_boundary();

        for &f in touched {
            if !self.face_alive[f] {
                continue;
            }
            let face = self.faces[f];
            for k in 0..3 {
                let a = face[k];
                let b = face[(k + 1) % 3];
                if a != b && !self.is_sharp(a, b) {
                    self.evaluate_pair(a, b, queue);
                }
            }
        }
    }

    /// Compact the survivors into a fresh mesh.
    ///
    /// Liveness is decided from the faces rather than from a flag, so an isolated
    /// vertex can never be emitted.
    fn finish(self) -> Mesh {
        let mut remap = vec![u32::MAX; self.positions.len()];
        let mut out = Mesh::new();

        for f in 0..self.faces.len() {
            if !self.face_alive[f] {
                continue;
            }
            for &corner in &self.faces[f] {
                let slot = corner as usize;
                if remap[slot] == u32::MAX {
                    remap[slot] = out.vertices.len() as u32;
                    out.vertices.push(self.positions[slot]);
                    if !self.normals.is_empty() {
                        out.normals.push(self.normals[slot]);
                    }
                    if self.source.uvs.len() == self.source.vertices.len() {
                        out.uvs.push(self.source.uvs[slot]);
                    }
                }
            }
        }

        for f in 0..self.faces.len() {
            if !self.face_alive[f] {
                continue;
            }
            let face = self.faces[f];
            out.indices.push(remap[face[0] as usize]);
            out.indices.push(remap[face[1] as usize]);
            out.indices.push(remap[face[2] as usize]);
            out.face_uvs.push(self.face_uvs[f]);
            if self.source.materials.len() >= self.faces.len() {
                out.materials.push(self.source.materials[f]);
            }
        }

        // Only claim a per-corner UV layer if the source had one. Synthesised
        // values must not be presented as authored data.
        if self.synthesised_face_uvs {
            out.face_uvs.clear();
        }

        if out.normals.len() != out.vertices.len() {
            out.compute_normals();
        }

        // A sharp edge survives only if both endpoints did, remapped.
        for &(a, b) in &self.sharp {
            let (x, y) = (remap[a as usize], remap[b as usize]);
            if x != u32::MAX && y != u32::MAX {
                out.mark_edge_sharp(x, y);
            }
        }

        out
    }
}

/// Which faces each vertex touches.
fn build_vertex_faces(faces: &[[u32; 3]], vertex_count: usize) -> Vec<Vec<usize>> {
    let mut vertex_faces = vec![Vec::new(); vertex_count];
    for (f, face) in faces.iter().enumerate() {
        for &corner in face {
            vertex_faces[corner as usize].push(f);
        }
    }
    vertex_faces
}

/// Simplify `mesh` to at most `target_triangles` by quadric error metrics.
///
/// Returns an error rather than a partial result when the target cannot be
/// reached. A mesh that quietly missed its triangle budget is worse than a
/// refusal, because the caller cannot tell the two apart.
pub fn simplify(mesh: &Mesh, target_triangles: usize) -> Result<Mesh> {
    let start_faces = mesh.triangle_count();
    if target_triangles >= start_faces {
        return Ok(mesh.clone());
    }
    if target_triangles < 4 {
        return Err(GeometryError::InvalidParameters(format!(
            "cannot reduce a triangle mesh to {target_triangles} triangles; a closed solid needs at least 4"
        )));
    }
    if mesh.vertices.is_empty() {
        return Err(GeometryError::MeshProcessingError(
            "cannot simplify a mesh with no vertices".to_string(),
        ));
    }

    let mut state = Simplifier::new(mesh)?;
    let mut queue: BinaryHeap<Candidate> = BinaryHeap::with_capacity(state.faces.len() * 4);

    {
        let mut pairs: HashSet<(u32, u32)> = HashSet::new();
        for f in 0..state.faces.len() {
            if !state.face_alive[f] {
                continue;
            }
            let face = state.faces[f];
            for k in 0..3 {
                let (a, b) = (face[k], face[(k + 1) % 3]);
                if a != b {
                    pairs.insert(if a < b { (a, b) } else { (b, a) });
                }
            }
        }
        let mut sorted: Vec<(u32, u32)> = pairs.into_iter().collect();
        sorted.sort_unstable();
        for (a, b) in sorted {
            if !state.is_sharp(a, b) {
                state.evaluate_pair(a, b, &mut queue);
            }
        }
    }

    // A rejected candidate is genuinely dead: the topology it referred to is gone
    // or illegal. A pass in which every remaining candidate is rejected means the
    // target is unreachable, not that we ran out of patience, so this budget only
    // exists to bound a pathological mesh.
    let reject_budget = state.live_faces * 8 + 1024;
    let mut rejects = 0usize;

    while state.live_faces > target_triangles {
        let Some(candidate) = queue.pop() else {
            break;
        };
        let (from, into) = (candidate.from, candidate.into);

        if from == into || state.vertex_faces[from as usize].is_empty() {
            continue;
        }
        if state.is_sharp(from, into) {
            continue;
        }
        if !state.link_condition_holds(from, into)
            || !state.preserves_orientation(from, into, &candidate.target)
        {
            rejects += 1;
            if rejects > reject_budget {
                break;
            }
            continue;
        }
        state.apply(&candidate, &mut queue);
    }

    if state.live_faces > target_triangles {
        return Err(GeometryError::MeshProcessingError(format!(
            "QEM simplification reached {} triangles but the target was {target_triangles}; \
             every remaining candidate is being rejected, which usually means the input is \
             already non-manifold or the target is below what this shape can reach",
            state.live_faces
        )));
    }

    Ok(state.finish())
}
