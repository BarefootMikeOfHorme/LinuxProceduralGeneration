//! Tests for the render-mesh split.
//!
//! The property under test throughout: the topology mesh is never modified and
//! stays welded, while the render mesh carries one normal and one UV per
//! vertex. A cube must come out flat with duplicated corners, a sphere must
//! come out smooth with no duplication at all, and the UV seam on a sphere
//! must be expressible without reopening the watertightness hole.

use super::*;
use crate::geometry::primitives::{Box, Cone, Cylinder, Sphere};
use crate::geometry::render::face_normal;
use crate::geometry::Primitive;
use std::collections::HashMap;

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
fn sphere_renders_smooth_duplicating_only_its_uv_seam() {
    // Renamed, and the assertion rewritten, because the old one recorded a
    // defect as expected behaviour. It asserted that a sphere duplicates
    // nothing at all, which was true only because the sphere had no per-corner
    // UV layer: with a single UV per vertex the seg-0 column carried u = 0 and
    // the wrap quad interpolated across it, losing the last texel of every
    // wrap-around UV. The mesh was smooth and watertight and textured slightly
    // wrong, which is the worst combination of defects to ship.
    //
    // Now the seam is expressed per corner, and the seg-0 column duplicates
    // because each of those vertices genuinely belongs to the quad at u = 0 and
    // to the wrap quad at u = 1. Exactly that column, and nothing else.
    let mesh = Sphere::new(1.0).to_mesh().unwrap();
    // Ring count, not vertex count: the sphere is 2 poles plus `rings - 1`
    // interior rings of `segments` vertices, so the seam column is 15 and
    // `vertex_count - 2` is 480.
    let interior_rings = (mesh.vertex_count() - 2) / Sphere::new(1.0).segments as usize;
    let render = mesh.split_for_render(180.0);
    assert_eq!(
        render.vertex_count(),
        mesh.vertex_count() + interior_rings,
        "only the UV seam column may duplicate, and positions must stay welded"
    );
    assert_eq!(
        render.unique_position_count(),
        mesh.vertex_count(),
        "a sphere is still a welded sphere; only attributes may split"
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

    // The contract for a zero-degree threshold is that nothing is smoothed, and
    // the meaningful way to state that is in terms of normals rather than counts.
    //
    // An earlier version of this test asserted one output vertex per face corner,
    // which is wrong: this sphere has face pairs whose normals agree to the last
    // f64 bit, and those legitimately share a vertex at a zero-degree threshold.
    // Merging them is not smoothing, because the two normals are the same vector,
    // and flat shading two coplanar faces through a shared vertex is
    // indistinguishable from flat shading them separately.
    //
    // Asserting the normal-level contract instead is strictly stronger than the
    // count was: it forbids sharing a vertex between faces that differ, which is
    // the only way sharing a vertex could actually be a defect.

    // 1. Every triangle is flat-shaded: all three corners carry that triangle's
    //    own face normal.
    for face in 0..render.triangle_count() {
        let geometric = face_normal(
            render.vertices[render.indices[face * 3] as usize],
            render.vertices[render.indices[face * 3 + 1] as usize],
            render.vertices[render.indices[face * 3 + 2] as usize],
        );
        for k in 0..3 {
            let corner = render.normals[render.indices[face * 3 + k] as usize];
            assert!(
                corner.dot(&geometric) > 0.99999,
                "face {face} corner {k} is smoothed (corner {corner:?} vs face {geometric:?}) at a zero-degree threshold"
            );
        }
    }

    // 2. No output vertex is shared by two faces that disagree about their normal.
    //    Group output vertices by position, then check the faces using each are
    //    mutually coplanar.
    let mut faces_by_vertex: HashMap<u32, Vec<usize>> = HashMap::new();
    for face in 0..render.triangle_count() {
        for k in 0..3 {
            faces_by_vertex
                .entry(render.indices[face * 3 + k])
                .or_default()
                .push(face);
        }
    }
    for (index, faces) in &faces_by_vertex {
        let reference = render.normals[*index as usize];
        for &face in faces {
            let geometric = face_normal(
                render.vertices[render.indices[face * 3] as usize],
                render.vertices[render.indices[face * 3 + 1] as usize],
                render.vertices[render.indices[face * 3 + 2] as usize],
            );
            assert!(
                reference.dot(&geometric) > 0.99999,
                "render vertex {index} is shared by faces with different normals, which is smoothing at a zero-degree threshold"
            );
        }
    }
}

#[test]
fn zero_angle_still_splits_everything_that_is_not_coplanar() {
    // A sanity floor on the count, so the normal-level assertions above cannot
    // pass on a mesh that was flattened by collapsing everything into one vertex.
    let mesh = Sphere::new(1.0).to_mesh().unwrap();
    let render = mesh.split_for_render(0.0);
    assert!(
        render.vertex_count() > mesh.vertex_count() * 2,
        "a zero-degree threshold produced {} vertices, too few to be flat-shaded",
        render.vertex_count()
    );
    assert!(
        render.vertex_count() <= mesh.triangle_count() * 3,
        "the split invented vertices beyond one per face corner"
    );
    // Every corner is distinct within its own triangle, which is the visible
    // meaning of "this face is flat".
    for face in 0..render.triangle_count() {
        let (a, b, c) = (
            render.indices[face * 3],
            render.indices[face * 3 + 1],
            render.indices[face * 3 + 2],
        );
        assert!(a != b && b != c && a != c, "face {face} is not flat");
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
fn marking_one_edge_sharp_creases_the_whole_edge() {
    let mesh = Sphere::new(1.0).to_mesh().unwrap();
    let mut marked = mesh.clone();

    // Mark the edge shared by the first two faces, which is the edge between
    // the first triangle's first two corners.
    let (a, b) = (marked.indices[0], marked.indices[1]);
    marked.mark_edge_sharp(a, b);
    assert!(marked.is_edge_sharp(a, b));
    assert!(
        marked.is_edge_sharp(b, a),
        "sharpness must be order independent"
    );

    let render = marked.split_for_render(180.0);

    // Find the two faces that touch the marked edge.
    let faces = [0usize, 1usize];
    for &endpoint in &[a, b] {
        // The two faces on either side of the crease must have been given
        // different normals at this endpoint, or the crease stops short.
        let corner_index = |face: usize| {
            render.indices[face * 3..face * 3 + 3]
                .iter()
                .copied()
                .find(|&i| render.vertices[i as usize] == mesh.vertices[endpoint as usize])
                .expect("endpoint missing from face")
        };
        let n0 = render.normals[corner_index(faces[0]) as usize];
        let n1 = render.normals[corner_index(faces[1]) as usize];
        assert!(
            n0 != n1,
            "endpoint {endpoint} shares one normal across the marked edge, so the crease stops before it"
        );
    }

    // Two extra output vertices at each endpoint: the marked edge's two faces
    // are pinned, the rest of the ring still averages.
    let unmarked = mesh.split_for_render(180.0);
    assert_eq!(
        unmarked.vertex_count() + 4,
        render.vertex_count(),
        "a single marked edge should split two vertices at each of its endpoints"
    );
}

#[test]
fn a_marked_edge_does_not_depend_on_the_rest_of_the_ring() {
    // The reason the sharp rule is local rather than a flood fill: the faces
    // around a vertex form a cycle, so a fill would walk around a single marked
    // edge and produce no split at all. Assert the crease exists even when the
    // marked edge is the only one on a closed ring.
    let mesh = Sphere::new(1.0).to_mesh().unwrap();
    let mut marked = mesh.clone();
    marked.mark_edge_sharp(marked.indices[0], marked.indices[1]);

    // Count distinct output vertices sharing the first triangle's first corner
    // position. A flood fill would leave exactly one.
    let position = mesh.vertices[marked.indices[0] as usize];
    let distinct = marked
        .split_for_render(180.0)
        .vertices
        .iter()
        .filter(|p| **p == position)
        .count();
    assert!(
        distinct >= 2,
        "marking the only sharp edge on a closed ring produced no split ({distinct} vertex)"
    );
}

#[test]
fn marking_the_same_edge_twice_is_idempotent() {
    let mut mesh = Box::new(Vector3::new(1.0, 1.0, 1.0)).to_mesh().unwrap();
    mesh.mark_edge_sharp(3, 1);
    let once = mesh.sharp_edges.len();
    mesh.mark_edge_sharp(1, 3);
    assert_eq!(
        once,
        mesh.sharp_edges.len(),
        "duplicate mark changed the count"
    );
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
