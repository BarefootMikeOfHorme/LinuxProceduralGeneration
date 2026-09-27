//! Winding and volume tests for the built-in primitives.
//!
//! These exist because an inside-out primitive passes almost every other check.
//! Vertex and triangle counts are unchanged, the mesh is still closed and
//! watertight, the validator still reports it manifold, and a total signed volume
//! is still positive if the inverted part is small enough. What breaks is
//! quieter and worse: normals point into the solid, backface culling hides the
//! wrong half, and ray-cast parity for point-in-solid queries inverts.
//!
//! That is not hypothetical. The box was wound inward on all six faces, and the
//! sphere had both pole caps wound inward while its quads were correct. The
//! sphere's total volume still read +3.96 against an ideal 4.19, so a plain
//! volume assertion passed the whole time. Only a per-region check, and a normal
//! that must point away from the centroid, catch it.
//!
//! So each test here asserts three separate things: positive total volume,
//! volume close to the analytic ideal, and every face normal pointing outward.

use super::render::signed_volume;
use crate::geometry::primitives::{Box, Cone, Cylinder, Sphere, Torus};
use crate::geometry::Primitive;
use nalgebra::{Point3, Vector3};
use std::collections::{HashMap, HashSet};

/// Analytic volumes, for the "close to ideal" assertion.
fn ideal_volume(shape: &str) -> f64 {
    match shape {
        "box" => 1.0,
        "sphere" => 4.0 / 3.0 * std::f64::consts::PI,
        "cylinder" => std::f64::consts::PI * 2.0,
        // pi * r^2 * h / 3 with r = 1, h = 2.
        "cone" => 2.0 / 3.0 * std::f64::consts::PI,
        // 2 * pi^2 * R * r^2 with R = 2, r = 1. A torus needs a major radius
        // strictly greater than its minor radius or it degenerates to a circle
        // swept along a point, and the constructor rejects it.
        _ => 4.0 * std::f64::consts::PI * std::f64::consts::PI,
    }
}

fn mesh_for(shape: &str) -> crate::geometry::Mesh {
    match shape {
        "box" => Box::new(Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap(),
        "sphere" => Sphere::new(1.0).to_mesh().unwrap(),
        "cylinder" => Cylinder::new(1.0, 2.0).to_mesh().unwrap(),
        "cone" => Cone::new(1.0, 2.0).to_mesh().unwrap(),
        _ => Torus::new(2.0, 1.0).to_mesh().unwrap(),
    }
}

const SHAPES: [&str; 5] = ["box", "sphere", "cylinder", "cone", "torus"];

#[test]
fn every_primitive_is_wound_outward() {
    for shape in SHAPES {
        let mesh = mesh_for(shape);
        let volume = signed_volume(&mesh);
        assert!(
            volume > 0.0,
            "{shape} has negative signed volume {volume}, so it is inside out"
        );
    }
}

#[test]
fn every_primitive_volume_is_within_a_sane_band_of_the_analytic_value() {
    // This is a coarse sanity band, deliberately. It exists to catch a shape
    // that is wildly wrong, not to be the sharp winding check: that job belongs
    // to `every_primitive_face_normal_points_outward`, which localises an
    // inverted face exactly, and to the per-region pole test below.
    //
    // The band cannot be tight in both directions. A faceted mesh is inscribed,
    // so it measures under the ideal solid, and how far under depends on the
    // tessellation: this sphere reads 98.4% of ideal at 32 segments and 16 rings,
    // while a 16-sided tube section already costs the torus about 2.5% before
    // the major direction is counted. A box, by contrast, is exact rather than
    // inscribed, so its volume equals the ideal to within float error and an
    // "always under" assertion would fail it.
    for shape in SHAPES {
        let mesh = mesh_for(shape);
        let volume = signed_volume(&mesh);
        let ideal = ideal_volume(shape);
        let ratio = volume / ideal;
        assert!(
            ratio > 0.9,
            "{shape} volume {volume} is less than 90% of the ideal {ideal}"
        );
        assert!(
            ratio <= 1.0001,
            "{shape} volume {volume} exceeds the ideal {ideal}, so the mesh circumscribes the solid"
        );
    }
}

#[test]
fn the_sphere_reads_near_its_analytic_volume() {
    // The sphere gets a tighter check than the shared band allows, because this
    // is the shape the pole defect actually shipped in. With both pole caps
    // inverted it read 94.6% of ideal, which is inside the band above and
    // outside this one.
    let mesh = Sphere::new(1.0).to_mesh().unwrap();
    let ideal = 4.0 / 3.0 * std::f64::consts::PI;
    let ratio = signed_volume(&mesh) / ideal;
    assert!(
        ratio > 0.97,
        "sphere volume ratio {ratio} is too low; an inverted pole cap reads about 0.946"
    );
    assert!(
        ratio <= 1.0001,
        "sphere volume ratio {ratio} exceeds the ideal"
    );
}

/// The direction a face or vertex normal should point at a point on the surface.
///
/// For a box, sphere, cylinder, or cone that is simply away from the centroid:
/// those solids are star-shaped about their centre, so "outward" and "away from
/// the middle" are the same thing everywhere on the surface.
///
/// A torus is not, and reusing the centroid rule there is a trap. The inner half
/// of the tube faces the central hole, which is toward the centroid, and that is
/// correct. A torus normal has to be measured against the tube's own centreline
/// instead, which is the circle of radius `major_radius` lying in the XZ plane,
/// since the torus axis is Y.
fn outward_reference(shape: &str, mesh: &crate::geometry::Mesh, p: Point3<f32>) -> Vector3<f32> {
    if shape != "torus" {
        let centre = mesh
            .vertices
            .iter()
            .fold(Point3::origin(), |acc, v| acc + v.coords)
            / mesh.vertices.len() as f32;
        return p.coords - centre.coords;
    }
    // The tube centreline is the circle of radius `major_radius` in the XZ
    // plane, at the shape's own centre height, which is the origin here. Using
    // the surface point's own Y instead puts the reference point on the surface
    // itself wherever the tube is at its widest, and the reference collapses to
    // zero.
    let rho = (p.x * p.x + p.z * p.z).sqrt();
    if rho < 1e-6 {
        // On the axis the surface is undefined; any direction is as good as
        // another and this never happens for a valid torus.
        return Vector3::new(0.0, 1.0, 0.0);
    }
    let major = 2.0f32;
    p.coords - Vector3::new(major * p.x / rho, 0.0, major * p.z / rho)
}

#[test]
fn every_primitive_face_normal_points_outward() {
    for shape in SHAPES {
        let mesh = mesh_for(shape);
        for face in 0..mesh.triangle_count() {
            let a = mesh.vertices[mesh.indices[face * 3] as usize];
            let b = mesh.vertices[mesh.indices[face * 3 + 1] as usize];
            let c = mesh.vertices[mesh.indices[face * 3 + 2] as usize];
            let normal = crate::geometry::render::face_normal(a, b, c);
            assert!(
                normal.norm() > 0.5,
                "{shape} face {face} is degenerate, so it has no usable normal"
            );
            // Use the face centre rather than any single corner, which can sit
            // exactly on the reference surface.
            let face_centre = (a.coords + b.coords + c.coords) / 3.0;
            let outward = outward_reference(shape, &mesh, Point3::from(face_centre));
            let alignment = normal.dot(&outward);
            assert!(
                alignment > 0.0,
                "{shape} face {face} normal points inward (alignment {alignment})"
            );
        }
    }
}

#[test]
fn every_primitive_vertex_normal_points_outward() {
    for shape in SHAPES {
        let mesh = mesh_for(shape);
        for (i, n) in mesh.normals.iter().enumerate() {
            assert!(
                (n.norm() - 1.0).abs() < 1e-3,
                "{shape} vertex {i} normal is not unit length: {}",
                n.norm()
            );
            let outward = outward_reference(shape, &mesh, mesh.vertices[i]);
            assert!(
                n.dot(&outward) > 0.0,
                "{shape} vertex {i} normal points inward"
            );
        }
    }
}

#[test]
fn the_sphere_pole_fans_agree_with_its_bands() {
    // A whole-mesh volume check cannot localise a single inverted cap, because
    // the bands around it are large enough to keep the total positive. This
    // splits the sphere at its poles and checks each region on its own, which is
    // the only way the defect was found.
    let mesh = Sphere::new(1.0).to_mesh().unwrap();

    let mut extremes: Vec<(f32, u32)> = mesh
        .vertices
        .iter()
        .enumerate()
        .map(|(i, v)| (v.y, i as u32))
        .collect();
    extremes.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    let south = extremes.first().unwrap().1;
    let north = extremes.last().unwrap().1;

    let contribution =
        |set: &[usize]| -> f64 { set.iter().map(|&f| face_signed_volume(&mesh, f)).sum() };

    for (label, pole) in [("north", north), ("south", south)] {
        let fan: Vec<usize> = (0..mesh.triangle_count())
            .filter(|&f| (0..3).any(|k| mesh.indices[f * 3 + k] == pole))
            .collect();
        let total = contribution(&fan);
        assert!(
            total > 0.0,
            "the {label} pole fan is inverted: {total} over {} faces",
            fan.len()
        );
    }
}

/// Edges used by exactly one triangle, and edges used by more than two.
///
/// A boundary edge means the surface has a hole; a non-manifold edge means more
/// than two faces meet along it. Either one makes the solid unusable for CSG and
/// collision even when the mesh looks correct on screen.
fn edge_defects(mesh: &crate::geometry::Mesh) -> (usize, usize) {
    let mut counts: HashMap<(u32, u32), usize> = HashMap::new();
    for f in 0..mesh.triangle_count() {
        for k in 0..3 {
            let a = mesh.indices[f * 3 + k];
            let b = mesh.indices[f * 3 + (k + 1) % 3];
            let key = if a < b { (a, b) } else { (b, a) };
            *counts.entry(key).or_insert(0) += 1;
        }
    }
    let boundary = counts.values().filter(|&&c| c == 1).count();
    let non_manifold = counts.values().filter(|&&c| c > 2).count();
    (boundary, non_manifold)
}

#[test]
fn every_primitive_is_watertight() {
    for shape in SHAPES {
        let mesh = mesh_for(shape);
        let (boundary, non_manifold) = edge_defects(&mesh);
        assert_eq!(
            boundary, 0,
            "{shape} has {boundary} boundary edges, so the solid is not watertight"
        );
        assert_eq!(
            non_manifold, 0,
            "{shape} has {non_manifold} non-manifold edges"
        );
    }
}

#[test]
fn no_primitive_has_coincident_vertices() {
    // A seam is often closed by adding a spare column of vertices at the wrap.
    // At theta = 2*PI, sin is about -2.4e-7 rather than 0, so the extra column is
    // a *near* duplicate rather than an exact one, which defeats the naive
    // "welded, therefore fine" check and leaves the surface open. Cylinder, cone,
    // and torus all shipped that way.
    for shape in SHAPES {
        let mesh = mesh_for(shape);
        let mut seen: HashSet<[u32; 3]> = HashSet::new();
        let mut coincident = 0usize;
        for v in &mesh.vertices {
            let key = [v.x.to_bits(), v.y.to_bits(), v.z.to_bits()];
            if !seen.insert(key) {
                coincident += 1;
            }
        }
        assert_eq!(
            coincident, 0,
            "{shape} has {coincident} exactly coincident vertices"
        );
    }
}

fn face_signed_volume(mesh: &crate::geometry::Mesh, face: usize) -> f64 {
    let a = mesh.vertices[mesh.indices[face * 3] as usize].coords;
    let b = mesh.vertices[mesh.indices[face * 3 + 1] as usize].coords;
    let c = mesh.vertices[mesh.indices[face * 3 + 2] as usize].coords;
    (a.x as f64 * (b.y as f64 * c.z as f64 - b.z as f64 * c.y as f64)
        - a.y as f64 * (b.x as f64 * c.z as f64 - b.z as f64 * c.x as f64)
        + a.z as f64 * (b.x as f64 * c.y as f64 - b.y as f64 * c.x as f64))
        / 6.0
}
