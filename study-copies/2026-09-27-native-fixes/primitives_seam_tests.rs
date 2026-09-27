//! Tests for the per-corner UV layer of the primitive generators.
//!
//! The property under test is the one that the box UV frame bug violated and
//! that a vertex count cannot see: **two coplanar triangles that share a corner
//! must give that corner the same UV.** A crease is allowed to split a corner,
//! because that is what a crease is for. A flat quad is not, and when it does,
//! the texture tears along the shared diagonal and the render split cannot merge
//! the two triangles no matter how it keys them.
//!
//! The second property is that a wrap actually reaches 1.0. A generator that
//! runs its segment loop to the segment count and then wraps by modulo has no
//! spare column of vertices, which is what keeps the solid watertight, and the
//! per-corner buffer is the only place the far side of the seam can be recorded.
//! A mesh that closes twice - a torus - has to do this in both directions.

use super::*;
use crate::geometry::primitives::{Box as PrimBox, Cone, Cylinder, Sphere, Torus};
use crate::geometry::Primitive;
use std::collections::HashMap;

/// Two faces are treated as coplanar when their normals agree this closely.
///
/// Loose enough for a sphere's near-flat bands, tight enough that a 90-degree
/// box edge or a cylinder's cap rim is never mistaken for flat.
const COPLANAR_DOT: f32 = 0.9999;

fn sample_meshes() -> Vec<(&'static str, Mesh)> {
    vec![
        (
            "box",
            PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0))
                .to_mesh()
                .unwrap(),
        ),
        ("sphere", Sphere::new(1.0).to_mesh().unwrap()),
        (
            "cylinder",
            Cylinder::new(1.0, 2.0).to_mesh().unwrap(),
        ),
        ("cone", Cone::new(1.0, 2.0).to_mesh().unwrap()),
        ("torus", Torus::new(2.0, 1.0).to_mesh().unwrap()),
    ]
}

/// Wide enough to catch a duplicate but not a genuine coincidence.
fn uv_of(mesh: &Mesh, face: usize, corner: usize) -> (u32, u32) {
    let uv = mesh.face_uvs[face][corner];
    (uv.0.to_bits(), uv.1.to_bits())
}

/// The vertex at `corner` of `face`.
fn corner_vertex(mesh: &Mesh, face: usize, corner: usize) -> u32 {
    mesh.indices[face * 3 + corner]
}

fn face_normal(mesh: &Mesh, face: usize) -> nalgebra::Vector3<f32> {
    let p = |k: usize| mesh.vertices[mesh.indices[face * 3 + k] as usize].coords;
    let cross = (p(1) - p(0)).cross(&(p(2) - p(0)));
    let length = cross.norm();
    if length > 0.0 {
        cross / length
    } else {
        cross
    }
}

#[test]
fn every_primitive_fills_the_per_corner_uv_layer() {
    for (name, mesh) in sample_meshes() {
        assert_eq!(
            mesh.face_uvs.len(),
            mesh.triangle_count(),
            "{name} has a per-corner UV layer that does not cover every face"
        );
    }
}

#[test]
fn coplanar_triangles_agree_on_every_shared_corner() {
    // The property the box violated. Half the box was unwrapped in the next
    // quad's frame, so a corner on a quad diagonal received two different UVs
    // from the two triangles that shared it. Nothing downstream could recover
    // from that: the texture tore along the diagonal, `u x v` stopped matching
    // the face normal, and the render split could not merge the pair.
    for (name, mesh) in sample_meshes() {
        // Index faces by their undirected edges so neighbours can be found
        // without assuming any particular triangle ordering.
        let mut by_edge: HashMap<(u32, u32), Vec<usize>> = HashMap::new();
        for f in 0..mesh.triangle_count() {
            for k in 0..3 {
                let a = corner_vertex(&mesh, f, k);
                let b = corner_vertex(&mesh, f, (k + 1) % 3);
                let key = if a < b { (a, b) } else { (b, a) };
                by_edge.entry(key).or_default().push(f);
            }
        }

        let mut quads_checked = 0usize;
        for f in 0..mesh.triangle_count() {
            for k in 0..3 {
                let a = corner_vertex(&mesh, f, k);
                let b = corner_vertex(&mesh, f, (k + 1) % 3);
                let key = if a < b { (a, b) } else { (b, a) };
                let Some(neighbours) = by_edge.get(&key) else {
                    continue;
                };
                for &g in neighbours {
                    if g <= f {
                        continue;
                    }
                    // A crease is a legitimate reason for the two corners to
                    // differ, so only coplanar pairs are held to this.
                    if face_normal(&mesh, f).dot(&face_normal(&mesh, g)) < COPLANAR_DOT {
                        continue;
                    }
                    // The two vertices this pair shares. A coplanar pair sharing
                    // two vertices is a quad split along its diagonal.
                    let shared: Vec<u32> = (0usize..3)
                        .map(|c| corner_vertex(&mesh, f, c))
                        .filter(|v| (0usize..3).map(|c| corner_vertex(&mesh, g, c)).any(|w| w == *v))
                        .collect();
                    if shared.len() < 2 {
                        continue;
                    }
                    quads_checked += 1;

                    for &vertex in &shared {
                        let in_f = (0usize..3)
                            .find(|&c| corner_vertex(&mesh, f, c) == vertex)
                            .unwrap();
                        let in_g = (0usize..3)
                            .find(|&c| corner_vertex(&mesh, g, c) == vertex)
                            .unwrap();
                        assert_eq!(
                            uv_of(&mesh, f, in_f),
                            uv_of(&mesh, g, in_g),
                            "{name}: vertex {vertex} is shared by coplanar faces {f} and \
                             {g} but got different UVs, so the texture tears across the \
                             shared diagonal and the pair can never be merged"
                        );
                    }
                }
            }
        }
        assert!(
            quads_checked > 0,
            "{name}: no coplanar quad pair was found, so this test is vacuous"
        );
    }
}

#[test]
fn a_crease_is_still_allowed_to_split_a_corner() {
    // The complement of the coplanar test, and the reason that one is allowed a
    // tolerance at all. A box edge is 90 degrees; if those two faces were forced
    // to agree, the box would round off. Restricting the coplanar test to flat
    // pairs is what stops it becoming a demand that every mesh be flat.
    let box_mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0))
        .to_mesh()
        .unwrap();
    let mut crossings = 0usize;
    for f in 0..box_mesh.triangle_count() {
        for g in (f + 1)..box_mesh.triangle_count() {
            // The corners each shared vertex occupies in f and in g. Only shared
            // corners are compared: a corner of f that g does not mention has no
            // UV in g to disagree with, and looking for one anyway is how this
            // test first panicked on an unwrap.
            let mut pairs: Vec<(usize, usize)> = Vec::new();
            for cf in 0usize..3 {
                let v = corner_vertex(&box_mesh, f, cf);
                if let Some(cg) = (0usize..3).find(|&cg| corner_vertex(&box_mesh, g, cg) == v) {
                    pairs.push((cf, cg));
                }
            }
            if pairs.len() != 2 {
                continue;
            }
            if face_normal(&box_mesh, f).dot(&face_normal(&box_mesh, g)) >= COPLANAR_DOT {
                continue;
            }
            crossings += 1;
            // The *pair* has to differ, not every corner in it. A unit box
            // produces a coincidence here: at the edge shared by the -Z and +X
            // faces, the corner (0.5, -0.5, -0.5) unwraps to (0, 0) in both
            // frames, because -Z maps u from -X and +X maps u from Y and both
            // land on 0 for that corner. That is arithmetic, not a bug, and it
            // costs nothing: the other corner of the pair differs, so the shared
            // edge still splits and the crease is still expressed. What must
            // never happen is the whole pair agreeing, which would weld two
            // faces of a 90-degree corner into one vertex.
            let all_equal = pairs
                .iter()
                .all(|(cf, cg)| uv_of(&box_mesh, f, *cf) == uv_of(&box_mesh, g, *cg));
            assert!(
                !all_equal,
                "faces {f} and {g} meet at 90 degrees and agree on the UV of every \
                 shared corner, so the crease is not expressed in the attribute \
                 layer and the corner cannot split"
            );
        }
    }
    assert!(
        crossings > 0,
        "a box has twelve creases, none of which were found"
    );
}

#[test]
fn a_sphere_wrap_reaches_u_one() {
    // The seam is only useful if the far side is recorded. Before the
    // per-corner layer, the seg-0 vertex carried u = 0 and the wrap quad
    // interpolated across it, losing the last texel of every wrap-around UV.
    let sphere = Sphere::new(1.0).to_mesh().unwrap();
    let max_u = sphere
        .face_uvs
        .iter()
        .flat_map(|face| face.iter())
        .map(|uv| uv.0)
        .fold(f32::MIN, f32::max);
    assert_eq!(
        max_u, 1.0,
        "the sphere's wrap never reaches u = 1.0, so the seam UV is incomplete"
    );
    let max_v = sphere
        .face_uvs
        .iter()
        .flat_map(|face| face.iter())
        .map(|uv| uv.1)
        .fold(f32::MIN, f32::max);
    assert_eq!(max_v, 1.0, "and v never reaches the south pole");
}

#[test]
fn a_torus_wrap_reaches_one_in_both_directions() {
    // A torus closes twice, so it has two seams, and a generator that only
    // handled the major one would still tile wrong around the tube.
    let torus = Torus::new(2.0, 1.0).to_mesh().unwrap();
    let max_u = torus
        .face_uvs
        .iter()
        .flat_map(|face| face.iter())
        .map(|uv| uv.0)
        .fold(f32::MIN, f32::max);
    let max_v = torus
        .face_uvs
        .iter()
        .flat_map(|face| face.iter())
        .map(|uv| uv.1)
        .fold(f32::MIN, f32::max);
    assert_eq!(max_u, 1.0, "the major wrap never reaches u = 1.0");
    assert_eq!(max_v, 1.0, "the minor wrap never reaches v = 1.0");
}

/// A flat strip of `across` by `along` quads whose u axis wraps at 1.0.
///
/// Built here rather than taken from a primitive because the property is only
/// well defined where there is no island singularity. A sphere's north pole
/// sits at u = 0.5 with its neighbour at u = 1/32, a step of 15/32 that is
/// entirely correct; a cylinder's cap is polar and its centre is at u = 0.5.
/// Encoding "skip the singular corners" needs a definition of singular, and in
/// a closed triangle mesh every vertex has degree three or more, so any such
/// threshold is arbitrary. Testing the property on a construction where it is
/// unambiguous, and testing the primitives' seams separately, is honest rather
/// than convenient.
fn uniform_strip(across: u32, along: u32) -> Mesh {
    let mut mesh = Mesh::new();
    // Vertex order is row-major, so the index of (row, column) is
    // `row * across + column`. Getting this wrong while the UVs stay correct is
    // exactly the cone's bug, in miniature: the parallel array no longer
    // describes the geometry it is supposed to annotate.
    for row in 0..along {
        for column in 0..across {
            let u = column as f32 / across as f32;
            let v = row as f32 / along as f32;
            mesh.vertices.push(Point3::new(u, v, 0.0));
        }
    }
    let at = |row: u32, column: u32| (row * across + column) as u32;
    let mut face_uvs: Vec<[(f32, f32); 3]> = Vec::new();
    for column in 0..across {
        // The wrap column unwraps to u = 1.0 rather than to 0.0, which is the
        // case a per-vertex UV cannot express and the reason this strip exists.
        let u0 = column as f32 / across as f32;
        let u1 = (column + 1) as f32 / across as f32;
        for row in 0..along {
            let next_row = (row + 1) % along;
            let next_column = (column + 1) % across;
            let v0 = row as f32 / along as f32;
            let v1 = (row + 1) as f32 / along as f32;
            let a = at(row, column);
            let b = at(row, next_column);
            let c = at(next_row, next_column);
            let d = at(next_row, column);
            mesh.indices.extend_from_slice(&[a, b, c]);
            face_uvs.push([(u0, v0), (u1, v0), (u1, v1)]);
            mesh.indices.extend_from_slice(&[a, c, d]);
            face_uvs.push([(u0, v0), (u1, v1), (u0, v1)]);
        }
    }
    mesh.face_uvs = face_uvs;
    mesh
}

#[test]
fn a_uniform_strip_steps_by_exactly_one_segment_including_the_wrap() {
    // Uniform spacing is what makes a tiled texture line up, and it has to hold
    // on the wrap quad too - the one whose far side sits at 1.0 rather than at
    // 1/n. An off-by-one there is invisible in a vertex count and glaring in a
    // render.
    for (across, along) in [(4u32, 2u32), (8, 3), (16, 5), (32, 4)] {
        let mesh = uniform_strip(across, along);
        let step = 1.0 / across as f32;
        let mut wraps = 0usize;
        for (f, face) in mesh.face_uvs.iter().enumerate() {
            for k in 0usize..3 {
                let delta = (face[(k + 1) % 3].0 - face[k].0).abs();
                // The edge of a quad triangle that runs along v has a u step of
                // zero by definition. Only the u-aligned edges carry spacing
                // information, so only they are held to the segment step.
                if delta < f32::EPSILON {
                    continue;
                }
                assert!(
                    (delta - step).abs() < 1e-6,
                    "{across}x{along} face {f}: a u step of {delta} is not one \
                     segment ({step})"
                );
            }
            if face.iter().any(|uv| uv.0 > 1.0 - step) {
                wraps += 1;
            }
        }
        assert!(wraps > 0, "{across}x{along}: the wrap quad was never examined");

        // The v axis is checked as a set rather than as steps, because a
        // triangle's u-aligned edge has a v step of zero by definition and
        // asserting on it would reject every correct strip.
        let mut vs: Vec<f32> = mesh.face_uvs.iter().flat_map(|f| f.iter()).map(|uv| uv.1).collect();
        vs.sort_by(|a, b| a.partial_cmp(b).unwrap());
        vs.dedup_by(|a, b| (*a - *b).abs() < 1e-6);
        let expected = along + 1;
        assert_eq!(
            vs.len(),
            expected as usize,
            "{across}x{along}: v should land on exactly {expected} grid lines, got {vs:?}"
        );
        for (i, v) in vs.iter().enumerate() {
            let want = i as f32 / along as f32;
            assert!(
                (v - want).abs() < 1e-6,
                "{across}x{along}: v grid line {i} is at {v}, expected {want}"
            );
        }
    }
}

#[test]
fn a_wrap_quad_keeps_its_far_column_at_one_and_near_at_one_minus_a_segment() {
    // Spelled out because this is the exact shape of the defect the whole
    // per-corner layer exists to prevent: a wrap that interpolates across the
    // seam instead of stepping onto it.
    let across = 8u32;
    let mesh = uniform_strip(across, 3);
    let near = 1.0 - 1.0 / across as f32;
    let mut saw_wrap = false;
    for face in &mesh.face_uvs {
        let us: Vec<f32> = face.iter().map(|uv| uv.0).collect();
        if !us.iter().any(|u| (*u - 1.0).abs() < f32::EPSILON) {
            continue;
        }
        saw_wrap = true;
        // Every corner of a wrap triangle sits on the last two grid lines, and
        // no further back. The check is on the *set* rather than on a sorted
        // pair because a wrap quad's two triangles have u sets of
        // {near, 1, 1} and {near, near, 1}: one of them legitimately has two
        // corners on the far line, so demanding the middle value be `near`
        // would reject a correct strip.
        for u in us {
            assert!(
                (u - 1.0).abs() < 1e-6 || (u - near).abs() < 1e-6,
                "a wrap triangle has a corner at u = {u}, which is neither the far \
                 line (1.0) nor the one before it ({near}); the wrap reached past \
                 the end of the grid or stopped short of it"
            );
        }
    }
    assert!(saw_wrap, "no face reached u = 1.0, so the wrap was not exercised");
}

#[test]
fn all_uvs_stay_inside_the_unit_square() {
    for (name, mesh) in sample_meshes() {
        for (f, face) in mesh.face_uvs.iter().enumerate() {
            for (k, uv) in face.iter().enumerate() {
                assert!(
                    uv.0 >= 0.0 && uv.0 <= 1.0 && uv.1 >= 0.0 && uv.1 <= 1.0,
                    "{name} face {f} corner {k} has uv {uv:?}, outside the unit square"
                );
            }
        }
    }
}

/// Faces joined into UV islands, plus the island count.
///
/// Two faces are in the same island when they share an index edge *and* carry
/// the same UV at both ends of it. Matching UVs is the join condition rather
/// than a shared vertex alone, because a crease splits attributes on purpose
/// and a multi-island layout is entitled to opposite handedness per island.
fn uv_islands(mesh: &Mesh) -> (Vec<usize>, usize) {
    let face_count = mesh.triangle_count();
    let mut parent: Vec<usize> = (0..face_count).collect();
    fn find(parent: &mut [usize], mut v: usize) -> usize {
        while parent[v] != v {
            parent[v] = parent[parent[v]];
            v = parent[v];
        }
        v
    }
    let mut by_edge: HashMap<(u32, u32), Vec<usize>> = HashMap::new();
    for f in 0..face_count {
        for k in 0usize..3 {
            let a = corner_vertex(mesh, f, k);
            let b = corner_vertex(mesh, f, (k + 1) % 3);
            let key = if a < b { (a, b) } else { (b, a) };
            by_edge.entry(key).or_default().push(f);
        }
    }
    for faces in by_edge.values() {
        for pair in faces.windows(2) {
            let (f, g) = (pair[0], pair[1]);
            // Do they agree in UV across the shared edge?
            let uv_of_corner = |face: usize, vertex: u32| -> Option<(u32, u32)> {
                (0usize..3)
                    .find(|&c| corner_vertex(mesh, face, c) == vertex)
                    .map(|c| uv_of(mesh, face, c))
            };
            let endpoints: Vec<u32> = (0usize..3)
                .map(|c| corner_vertex(mesh, f, c))
                .filter(|v| (0usize..3).any(|c| corner_vertex(mesh, g, c) == *v))
                .collect();
            if endpoints.len() != 2 {
                continue;
            }
            let agrees = endpoints.iter().all(|v| {
                uv_of_corner(f, *v).is_some() && uv_of_corner(f, *v) == uv_of_corner(g, *v)
            });
            if !agrees {
                continue;
            }
            let (ra, rb) = (find(&mut parent, f), find(&mut parent, g));
            if ra != rb {
                parent[ra] = rb;
            }
        }
    }
    let mut label = vec![usize::MAX; face_count];
    let mut islands = 0usize;
    for f in 0..face_count {
        if label[f] == usize::MAX {
            let root = find(&mut parent, f);
            for g in 0..face_count {
                if find(&mut parent, g) == root {
                    label[g] = islands;
                }
            }
            islands += 1;
        }
    }
    (label, islands)
}

#[test]
fn the_uv_frame_handedness_is_uniform_within_each_uv_island() {
    // Not "outward", which would be wrong for a torus and for a polar disc. The
    // real invariant is consistency *within an island*: a normal map mirrors on
    // the faces whose frame disagrees with their neighbours, so a mesh that
    // mixes the two signs inside one island is broken even though every face
    // looks correct in isolation.
    //
    // Across islands, mixed signs are correct and expected. A cylinder's cap
    // disc is polar and its side is a strip; nothing obliges those two to share
    // a handedness, and the first version of this test asserted that they did
    // and so failed on correct geometry.
    for (name, mesh) in sample_meshes() {
        let (label, island_count) = uv_islands(&mesh);
        let mut signs: Vec<Option<i8>> = vec![None; island_count];
        for f in 0..mesh.triangle_count() {
            let p = |k: usize| mesh.vertices[mesh.indices[f * 3 + k] as usize].coords;
            let e1 = p(1) - p(0);
            let e2 = p(2) - p(0);
            let uv = |k: usize| mesh.face_uvs[f][k];
            let du = (uv(1).0 - uv(0).0) * e1 + (uv(2).0 - uv(0).0) * e2;
            let dv = (uv(1).1 - uv(0).1) * e1 + (uv(2).1 - uv(0).1) * e2;
            let cross = |a: nalgebra::Vector3<f32>, b: nalgebra::Vector3<f32>| {
                nalgebra::Vector3::new(
                    a.y * b.z - a.z * b.y,
                    a.z * b.x - a.x * b.z,
                    a.x * b.y - a.y * b.x,
                )
            };
            let alignment = cross(du, dv).dot(&cross(e1, e2));
            // Too flat for the frame to have a direction, e.g. a pole triangle.
            if alignment.abs() < 1e-9 {
                continue;
            }
            let sign = if alignment > 0.0 { 1i8 } else { -1i8 };
            let island = label[f];
            match signs[island] {
                None => signs[island] = Some(sign),
                Some(existing) => assert_eq!(
                    existing, sign,
                    "{name}: UV island {island} is right-handed on some faces and \
                     left-handed on others, so a normal map would mirror on part \
                     of it"
                ),
            }
        }
        assert!(
            signs.iter().any(|s| s.is_some()),
            "{name}: no island produced a usable UV frame, so this test is vacuous"
        );
    }
}

#[test]
fn a_cylinder_really_does_have_more_than_one_uv_island() {
    // Guards the guard. The test above only means something if islands are
    // actually being distinguished, and a cylinder is the case that forces it:
    // its cap disc and its side strip share no vertex at all.
    let cylinder = Cylinder::new(1.0, 2.0).to_mesh().unwrap();
    let (_, islands) = uv_islands(&cylinder);
    assert!(
        islands >= 2,
        "a cylinder's cap and flank should be separate UV islands, got {islands}"
    );
}

#[test]
fn a_sphere_render_form_duplicates_only_its_uv_seam() {
    // The honest cost of a correct wrap, stated as a contract rather than as a
    // bare number.
    //
    // A sphere at a smoothing angle has no creases, so the only corners that can
    // duplicate are the ones a per-corner attribute forces apart. That is
    // exactly the seg-0 column, one vertex per interior ring, because each of
    // those belongs to the quad at u = 0 and to the wrap quad at u = 1.
    //
    // The old buffer gave those vertices a single u = 0 and interpolated across
    // the wrap, which produced 482 output vertices and a texture that lost the
    // last texel of every wrap. Positions stay welded either way, which is the
    // part CAD consumers care about.
    let sphere = Sphere::new(1.0).to_mesh().unwrap();
    // 2 poles plus `rings - 1` interior rings of `segments` vertices each, so
    // the seam column is the *ring* count, not the vertex count. Dividing by
    // segments matters: `vertex_count - 2` is 480 and the answer is 15.
    let interior_rings = (sphere.vertices.len() - 2) / Sphere::new(1.0).segments as usize;
    let render = sphere.split_for_render(30.0);

    assert_eq!(
        render.vertex_count(),
        sphere.vertices.len() + interior_rings,
        "expected the seam column and nothing else to duplicate"
    );
    assert_eq!(
        render.unique_position_count(),
        sphere.vertices.len(),
        "positions must stay welded; only attributes may split"
    );
    assert_eq!(render.triangle_count(), sphere.triangle_count());
}

#[test]
fn a_torus_render_form_duplicates_only_its_two_seams() {
    // A torus closes twice. The major wrap splits the i = 0 row and the minor
    // wrap splits the j = 0 column, and the corner where they meet splits four
    // ways rather than two, so the count is not the sum of the two rows.
    //
    //   (minor - 1) + (major - 1) + 3
    //
    // for a 48x24 torus: 23 + 47 + 3 = 73, and 1152 + 73 = 1225.
    let torus = Torus::new(2.0, 1.0).to_mesh().unwrap();
    let major = 48u32;
    let minor = 24u32;
    assert_eq!(torus.vertices.len(), (major * minor) as usize);

    let render = torus.split_for_render(30.0);
    let expected = torus.vertices.len() + (minor - 1) as usize + (major - 1) as usize + 3;
    assert_eq!(
        render.vertex_count(),
        expected,
        "expected the two seam columns and the corner that splits four ways"
    );
    assert_eq!(
        render.unique_position_count(),
        torus.vertices.len(),
        "positions must stay welded; only attributes may split"
    );
    assert_eq!(render.triangle_count(), torus.triangle_count());
}

#[test]
fn adding_the_uv_layer_did_not_cost_a_single_welded_position() {
    // The regression guard for the whole pass. Joining the sphere and torus
    // seams in the attribute layer must not reopen the watertightness hole that
    // a spare column of vertices used to cause, and it must not move a vertex.
    for (name, mesh) in sample_meshes() {
        let report = crate::mesh::structure::check_structure(&mesh);
        assert!(
            report.is_structurally_valid(),
            "{name} is no longer a valid closed solid with its per-corner UVs: {:?}",
            report.issues()
        );
    }
}
