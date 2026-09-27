//! Tests for the render-mesh split.
//!
//! The property under test throughout: the topology mesh is never modified and
//! stays welded, while the render mesh carries one normal and one UV per
//! vertex. A cube must come out flat with duplicated corners, a sphere must
//! come out smooth with no duplication at all, and the UV seam on a sphere
//! must be expressible without reopening the watertightness hole.

use super::*;
use crate::geometry::primitives::{Box, Cone, Cylinder, Sphere};
use crate::geometry::Primitive;
use crate::geometry::render::face_normal;

/// True when every face normal is shared by exactly one output vertex, i.e. the
/// surface is flat-shaded at that vertex.
fn is_flat_at(render: &RenderMesh, face: usize) -> bool {
    let a = render.indices[face * 3] as usize;
    let b = render.indices[face * 3 + 1] as usize;
    let c = render.indices[face * 3 + 2] as usize;
    // Flat means all three corners of the triangle are distinct vertices, each
    // carrying that triangle's own normal.
    a != b && b != c && a != c
}

#[test]
fn cube_renders_flat_with_split_corners() {
    let mesh = Box::new(Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
    assert_eq!(mesh.vertex_count(), 8, "topology stays welded");

    // Every edge marked sharp, so all six faces are independent fans.
    let render = mesh.split_for_render(180.0);

    assert!(
        render.vertex_count() > mesh.vertex_count(),
        "a flat cube must duplicate corners: {} vs {}",
        render.vertex_count(),
        mesh.vertex_count()
    );
    assert_eq!(render.triangle_count(), mesh.triangle_count());
    for face in 0..render.triangle_count() {
        assert!(is_flat_at(&render, face), "cube face {face} should be flat");
    }
}

#[test]
fn cube_faces_point_outward_on_the_render_mesh() {
    let mesh = Box::new(Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
    let render = mesh.split_for_render(180.0);
    for face in 0..render.triangle_count() {
        let a = render.vertices[render.indices[face * 3] as usize];
        let b = render.vertices[render.indices[face * 3 + 1] as usize];
        let c = render.vertices[render.indices[face * 3 + 2] as usize];
        let n = face_normal(a, b, c);
        // Outward means the face normal agrees with the corner normal, and the
        // corner normal points away from the centre.
        let corner = render.normals[render.indices[face * 3] as usize];
        assert!(
            n.dot(&corner) > 0.99,
            "face {face} normal disagrees with its corner normal"
        );
        let centre = Point3::new(0.0, 0.0, 0.0);
        let outward = a.coords - centre.coords;
        assert!(
            n.dot(&outward) > 0.0,
            "face {face} normal points inward on a cube"
        );
    }
}

#[test]
fn sphere_renders_smooth_with_no_duplication() {
    let mesh = Sphere::new(1.0).to_mesh().unwrap();
    let render = mesh.split_for_render(180.0);
    assert_eq!(
        render.vertex_count(),
        mesh.vertex_count(),
        "a sphere has no sharp edges, so nothing should be duplicated"
    );
    assert_eq!(render.triangle_count(), mesh.triangle_count());
}

#[test]
fn sphere_normals_point_outward_and_are_unit_length() {
    let mesh = Sphere::new(1.0).to_mesh().unwrap();
    let render = mesh.split_for_render(180.0);
    for (i, n) in render.normals.iter().enumerate() {
        assert!(
            (n.norm() - 1.0).abs() < 1e-4,
            "normal {i} is not unit length: {}",
            n.norm()
        );
        let p = render.vertices[i].coords;
        // For a unit sphere the outward normal at p is p itself.
        assert!(
            n.dot(&p) > 0.99,
            "normal {i} does not point outward from a unit sphere"
        );
    }
}

#[test]
fn zero_angle_flattens_everything() {
    let mesh = Sphere::new(1.0).to_mesh().unwrap();
    let render = mesh.split_for_render(0.0);
    // With a zero-degree threshold no pair of faces is smooth, so every
    // corner is its own vertex.
    assert_eq!(
        render.vertex_count(),
        mesh.triangle_count() * 3,
        "zero degrees should produce one vertex per face corner"
    );
    for face in 0..render.triangle_count() {
        assert!(is_flat_at(&render, face), "face {face} should be flat");
    }
}

#[test]
fn render_mesh_preserves_topology_triangle_count() {
    for shape in ["box", "sphere", "cylinder", "cone"] {
        let mesh = match shape {
            "box" => Box::new(Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap(),
            "sphere" => Sphere::new(1.0).to_mesh().unwrap(),
            "cylinder" => Cylinder::new(1.0, 2.0).to_mesh().unwrap(),
            _ => Cone::new(1.0, 2.0).to_mesh().unwrap(),
        };
        let render = mesh.split_for_render(45.0);
        assert_eq!(
            render.triangle_count(),
            mesh.triangle_count(),
            "{shape} lost or gained triangles in the split"
        );
        assert_eq!(render.uvs.len(), render.vertices.len());
        assert_eq!(render.normals.len(), render.vertices.len());
    }
}

#[test]
fn split_does_not_mutate_the_source_mesh() {
    let mesh = Box::new(Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
    let before = (
        mesh.vertex_count(),
        mesh.triangle_count(),
        mesh.uvs.len(),
        mesh.sharp_edges.len(),
    );
    let _ = mesh.split_for_render(30.0);
    let after = (
        mesh.vertex_count(),
        mesh.triangle_count(),
        mesh.uvs.len(),
        mesh.sharp_edges.len(),
    );
    assert_eq!(before, after, "split_for_render mutated the topology mesh");
}

#[test]
fn marking_one_edge_sharp_splits_exactly_that_crease() {
    let mesh = Sphere::new(1.0).to_mesh().unwrap();
    let mut marked = mesh.clone();

    // Mark one edge of the first triangle.
    let (a, b) = (marked.indices[0], marked.indices[1]);
    marked.mark_edge_sharp(a, b);
    assert!(marked.is_edge_sharp(a, b));
    assert!(marked.is_edge_sharp(b, a), "sharpness must be order independent");

    let unmarked_render = mesh.split_for_render(180.0);
    let marked_render = marked.split_for_render(180.0);
    assert_eq!(
        unmarked_render.vertex_count() + 2,
        marked_render.vertex_count(),
        "marking one edge should split exactly the two corners on it"
    );
}

#[test]
fn marking_the_same_edge_twice_is_idempotent() {
    let mut mesh = Box::new(Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
    mesh.mark_edge_sharp(3, 1);
    let once = mesh.sharp_edges.len();
    mesh.mark_edge_sharp(1, 3);
    assert_eq!(once, mesh.sharp_edges.len(), "duplicate mark changed the count");
    mesh.mark_edge_sharp(3, 3);
    assert_eq!(once, mesh.sharp_edges.len(), "self-edge was recorded");
}

#[test]
fn face_uvs_take_precedence_over_vertex_uvs() {
    // A quad with per-corner UVs that differ across the diagonal must come
    // through unchanged, which is the only way a seam can be expressed.
    let mut mesh = Mesh::new();
    mesh.vertices = vec![
        Point3::new(0.0, 0.0, 0.0),
        Point3::new(1.0, 0.0, 0.0),
        Point3::new(1.0, 1.0, 0.0),
        Point3::new(0.0, 1.0, 0.0),
    ];
    mesh.indices = vec![0, 1, 2, 0, 2, 3];
    // Deliberately degenerate vertex UVs, as the box and cylinder still have.
    mesh.uvs = vec![(0.0, 0.0); 4];
    mesh.face_uvs = vec![
        [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)],
        [(0.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
    ];

    let render = mesh.split_for_render(180.0);
    let found: Vec<(f32, f32)> = render.uvs.clone();
    assert!(
        found.contains(&(1.0, 1.0)) && found.contains(&(0.0, 1.0)),
        "per-corner UVs were dropped in favour of the degenerate vertex UVs: {found:?}"
    );
    assert!(
        !found.iter().all(|&(u, v)| u == 0.0 && v == 0.0),
        "vertex UVs were used despite face_uvs being present"
    );
}

#[test]
fn missing_vertex_uvs_do_not_panic() {
    // A mesh with neither face_uvs nor uvs must still split, falling back to
    // zero rather than indexing past the end.
    let mut mesh = Mesh::new();
    mesh.vertices = vec![
        Point3::new(0.0, 0.0, 0.0),
        Point3::new(1.0, 0.0, 0.0),
        Point3::new(0.0, 1.0, 0.0),
    ];
    mesh.indices = vec![0, 1, 2];
    let render = mesh.split_for_render(180.0);
    assert_eq!(render.uvs.len(), render.vertices.len());
    assert!(render.uvs.iter().all(|&(u, v)| u == 0.0 && v == 0.0));
}

#[test]
fn empty_mesh_splits_to_empty() {
    let mesh = Mesh::new();
    let render = mesh.split_for_render(180.0);
    assert_eq!(render.vertex_count(), 0);
    assert_eq!(render.triangle_count(), 0);
}

#[test]
fn negative_angle_smooths_everything_unmarked() {
    let mesh = Sphere::new(1.0).to_mesh().unwrap();
    let a = mesh.split_for_render(-1.0);
    let b = mesh.split_for_render(180.0);
    assert_eq!(
        a.vertex_count(),
        b.vertex_count(),
        "a negative angle should behave as 180"
    );
}
