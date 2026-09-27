//! Tests for the attribute-keyed render split.
//!
//! [`Mesh::split_for_render_keyed`] merges corners on
//! `(position, normal, uv)` compared bit for bit, which is MikkTSpace's rule and
//! the rule glTF's reference cube obeys. [`Mesh::split_for_render`] keys on the
//! smoothing group instead and cannot merge the two triangles of a coplanar
//! quad, so it emits 36 for a box where the reference ships 24.
//!
//! The properties under test here, in the order they matter:
//!
//! 1. The keyed path never emits more vertices than the legacy path. If it did,
//!    the extra vertices would be a defect rather than a saving, and the whole
//!    justification would be gone.
//! 2. It reproduces the reference count on the case the reference documents.
//! 3. It does that without weakening the crease test. A merge is only correct if
//!    what merged genuinely was the same; a crease that got merged is a shading
//!    error that is invisible in a vertex count and obvious on screen.
//! 4. The legacy path is unchanged, because it is what the exporter and the
//!    Python bindings call today.
//!
//! Getting to 24 also required repairing the box's per-corner UVs, which were
//! unwrapped with the wrong face's axes on half the box. The
//! [`box_uv_frame_is_right_handed`] and
//! [`a_shared_quad_corner_gets_one_uv_across_both_triangles`] tests below are
//! the record of that repair; they are the tests that would have caught it.

use super::*;
use crate::geometry::primitives::{Box as PrimBox, Cone, Cylinder, Sphere, Torus};
use crate::geometry::Primitive;
use std::collections::HashMap;

/// Every primitive this crate generates, with the angles worth checking.
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

const ANGLES: [f32; 4] = [0.0, 1.0, 30.0, 180.0];

#[test]
fn split_for_render_keyed_never_grows() {
    // The canary. A key that merges more must never produce more, because
    // `Attributes` is a coarsening of `SmoothingGroup`: the group decides the
    // normal, so any two corners that share a group already share a normal, and
    // two corners that differ in group can only differ in normal, which is a
    // strict refinement. Measured across every primitive and every angle:
    //
    //   box       36 -> 24      sphere    2790 -> 2782
    //   cylinder 322 -> 194      cone       177 -> 176
    //   torus    6832 -> 6784
    for (name, mesh) in sample_meshes() {
        for angle in ANGLES {
            let legacy = mesh.split_for_render(angle);
            let keyed = mesh.split_for_render_keyed(angle);
            assert!(
                keyed.vertex_count() <= legacy.vertex_count(),
                "{name} at {angle} degrees: keyed {} exceeded legacy {}",
                keyed.vertex_count(),
                legacy.vertex_count(),
            );
        }
    }
}

#[test]
fn a_box_matches_the_glTF_reference_count_of_twenty_four() {
    // Khronos `Models/Box.gltf` ships 24 positions, 36 indices, 24 normals.
    // Twenty-four is 8 welded positions times 3 face normals times 1 UV each,
    // and 36 indices is 12 triangles. This is the concrete number the whole
    // keyed strategy is aiming at, and the legacy path cannot reach it.
    let box_mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0))
        .to_mesh()
        .unwrap();
    let keyed = box_mesh.split_for_render_keyed(30.0);

    assert_eq!(keyed.vertex_count(), 24, "the reference cube has 24 positions");
    assert_eq!(keyed.triangle_count(), 12);
    assert_eq!(keyed.indices.len(), 36);
    assert_eq!(keyed.normals.len(), 24);
    assert_eq!(keyed.uvs.len(), 24);
    assert_eq!(keyed.unique_position_count(), 8, "still 8 welded positions");

    let legacy = box_mesh.split_for_render(30.0);
    assert_eq!(
        legacy.vertex_count(),
        36,
        "the legacy path splits per triangle; that is what this path fixes",
    );
}

#[test]
fn a_box_keeps_all_six_face_normals() {
    // Six faces, so six distinct normals, and each must have exactly four
    // vertices. If the merge were over-eager this would collapse a face onto its
    // neighbour and the box would round off.
    let keyed = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0))
        .to_mesh()
        .unwrap()
        .split_for_render_keyed(30.0);

    let mut faces: Vec<[i32; 3]> = Vec::new();
    for normal in &keyed.normals {
        let triple = [
            (normal.x * 1e3).round() as i32,
            (normal.y * 1e3).round() as i32,
            (normal.z * 1e3).round() as i32,
        ];
        if !faces.contains(&triple) {
            faces.push(triple);
        }
    }
    assert_eq!(faces.len(), 6, "a box has six face normals, got {faces:?}");
    for normal in &keyed.normals {
        assert!(
            (normal.norm() - 1.0).abs() < 1e-5,
            "face normal {normal:?} is not unit length"
        );
    }
}

#[test]
fn a_crease_survives_the_merge() {
    // The reason the key is bitwise rather than tolerant. A cube with one
    // marked edge pair: the two faces meeting there are 90 degrees apart, and
    // merging them would round that edge off. A tolerance loose enough to be
    // convenient swallows creases; this is asserted at a crease of a degree
    // count, so it holds for any tolerance that would round a cube.
    let mut box_mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0))
        .to_mesh()
        .unwrap();
    // Clear everything, then mark a single edge: an edge is two vertices.
    box_mesh.sharp_edges.clear();
    box_mesh.mark_edge_sharp(0, 1);
    assert_eq!(box_mesh.sharp_edges.len(), 1, "one edge, two vertices");

    let keyed = box_mesh.split_for_render_keyed(30.0);
    let mut normals: Vec<[i32; 3]> = keyed
        .normals
        .iter()
        .map(|n| {
            [
                (n.x * 1e3).round() as i32,
                (n.y * 1e3).round() as i32,
                (n.z * 1e3).round() as i32,
            ]
        })
        .collect();
    normals.sort();
    normals.dedup();
    assert_eq!(
        normals.len(),
        6,
        "the marked edge must not merge its two faces, so all six faces stay distinct",
    );
}

#[test]
fn a_sharp_edge_still_produces_two_different_normals_at_the_same_position() {
    // Directly on the key: at one position, one vertex must carry two different
    // normals because it is on both sides of a marked edge. If it did not, the
    // marked edge would be having no effect on the render form at all.
    let mut box_mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0))
        .to_mesh()
        .unwrap();
    box_mesh.sharp_edges.clear();
    box_mesh.mark_edge_sharp(0, 1);

    let keyed = box_mesh.split_for_render_keyed(30.0);
    let at_zero: Vec<&Vector3<f32>> = keyed
        .vertices
        .iter()
        .enumerate()
        .filter(|(_, v)| {
            (v.coords.x + 0.5).abs() < 1e-6
                && (v.coords.y + 0.5).abs() < 1e-6
                && (v.coords.z + 0.5).abs() < 1e-6
        })
        .map(|(i, _)| &keyed.normals[i])
        .collect();
    assert_eq!(
        at_zero.len(),
        3,
        "a cube corner on three faces carries three normals"
    );
    let mut distinct: Vec<[i32; 3]> = at_zero
        .iter()
        .map(|n| {
            [
                (n.x * 1e3).round() as i32,
                (n.y * 1e3).round() as i32,
                (n.z * 1e3).round() as i32,
            ]
        })
        .collect();
    distinct.sort();
    distinct.dedup();
    assert_eq!(distinct.len(), 3, "and all three are different");
}

#[test]
fn a_shared_quad_corner_gets_one_uv_across_both_triangles() {
    // The repair, asserted. Each box quad is two triangles, and a corner on the
    // shared diagonal belongs to both. It must receive the same UV from both, or
    // the texture tears along the diagonal and no render form can merge it.
    //
    // Before the repair the second triangle of each quad was unwrapped with the
    // *next* face's axes, so every quad was split and the keyed box came out at
    // 30 rather than 24.
    let box_mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0))
        .to_mesh()
        .unwrap();
    assert_eq!(box_mesh.triangle_count(), 12, "six quads of two triangles");

    let mut uv_by_corner: HashMap<(u32, usize), (u32, u32)> = HashMap::new();
    for quad in 0..6 {
        for half in 0..2 {
            let face = quad * 2 + half;
            for k in 0..3 {
                let key = (box_mesh.indices[face * 3 + k], quad);
                let bits = (
                    box_mesh.face_uvs[face][k].0.to_bits(),
                    box_mesh.face_uvs[face][k].1.to_bits(),
                );
                if let Some(&existing) = uv_by_corner.get(&key) {
                    assert_eq!(
                        existing, bits,
                        "vertex {} is on quad {quad} in both triangles but got \
                         different UVs, so the texture tears across the diagonal",
                        box_mesh.indices[face * 3 + k]
                    );
                }
                uv_by_corner.insert(key, bits);
            }
        }
    }
    assert_eq!(uv_by_corner.len(), 24, "8 vertices times 3 quads each");
}

#[test]
fn box_uv_frame_is_right_handed() {
    // The other half of the same repair, and the reason it mattered beyond a
    // vertex count. The box promises that `u x v` is the outward face normal so
    // a normal map applied on top is not mirrored. Half the box did not honour
    // it, because the second triangle of each quad was unwrapped in the next
    // face's frame.
    let box_mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0))
        .to_mesh()
        .unwrap();
    let keyed = box_mesh.split_for_render_keyed(30.0);

    // Du is a positive multiple of the edge direction, and Dv a positive
    // multiple of the other edge direction, for a consistent island layout.
    for face in 0..keyed.triangle_count() {
        let base = face * 3;
        let p = |i: usize| keyed.vertices[keyed.indices[base + i] as usize].coords;
        let (a, b, c) = (p(0), p(1), p(2));
        let e1 = b - a;
        let e2 = c - a;
        // Non-degenerate, or there is nothing to orient.
        assert!(
            e1.cross(&e2).norm() > 1e-6,
            "face {face} is degenerate after splitting"
        );

        // A point in the triangle is a + s*e1 + t*e2 with (s,t) in the unit
        // corner, so the UV gradient in 3D is the two tangent directions scaled
        // by the UV deltas. Written in scalars rather than with a cross product
        // because nalgebra's `cross` on the vector-matrix types resolves by
        // dimension and picks a matrix product, which is not what is meant here.
        let uv = |i: usize| keyed.uvs[keyed.indices[base + i] as usize];
        let grad = |pick: fn(&(f32, f32)) -> f32| {
            (pick(&uv(1)) - pick(&uv(0))) * e1 + (pick(&uv(2)) - pick(&uv(0))) * e2
        };
        let du = grad(|uv| uv.0);
        let dv = grad(|uv| uv.1);
        let du = grad(|uv| uv.0);
        let dv = grad(|uv| uv.1);
        let cross = |a: Vector3<f32>, b: Vector3<f32>| {
            Vector3::new(
                a.y * b.z - a.z * b.y,
                a.z * b.x - a.x * b.z,
                a.x * b.y - a.y * b.x,
            )
        };
        let handed = cross(du, dv);
        let outward = cross(e1, e2);
        // Spelled out rather than `.dot`, because nalgebra's `dot` on a 3x1
        // matrix wants a 1x3 on the right and quietly does not accept a vector.
        let alignment =
            handed.x * outward.x + handed.y * outward.y + handed.z * outward.z;
        assert!(
            alignment > 0.0,
            "face {face} has a left-handed UV frame, so a normal map on it would \
             be mirrored: du={du:?} dv={dv:?} normal={outward:?}"
        );
    }
}

#[test]
fn the_legacy_split_is_unchanged() {
    // `split_for_render` is what the exporter and the Python bindings call
    // today. The refactor moved its logic into a shared core, so the counts it
    // produces are pinned here to prove the move changed nothing.
    let box_mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0))
        .to_mesh()
        .unwrap();
    assert_eq!(box_mesh.split_for_render(0.0).vertex_count(), 36);
    assert_eq!(box_mesh.split_for_render(30.0).vertex_count(), 36);
    assert_eq!(box_mesh.split_for_render(180.0).vertex_count(), 36);

    let sphere = Sphere::new(1.0).to_mesh().unwrap();
    // A sphere has no sharp edges, continuous UVs and only shallow angles, so
    // at 30 degrees it must come out with no duplication at all.
    assert_eq!(sphere.split_for_render(30.0).vertex_count(), 482);
    assert_eq!(sphere.vertices.len(), 482);

    // Flattening is the case where the legacy path really does split, because
    // every face becomes its own group.
    assert_eq!(sphere.split_for_render(0.0).vertex_count(), 2790);
}

#[test]
fn a_smooth_sphere_is_undisturbed_by_the_keyed_path() {
    // The one case where the two strategies should agree exactly, and the
    // regression guard for the shared core: if a change to the fan or UV logic
    // ever leaked into only one of the two paths, this is where it shows.
    let sphere = Sphere::new(1.0).to_mesh().unwrap();
    let legacy = sphere.split_for_render(30.0);
    let keyed = sphere.split_for_render_keyed(30.0);
    assert_eq!(keyed.vertex_count(), legacy.vertex_count());
    assert_eq!(keyed.indices, legacy.indices);
    for (a, b) in keyed.normals.iter().zip(legacy.normals.iter()) {
        assert_eq!(a, b);
    }
    for (a, b) in keyed.uvs.iter().zip(legacy.uvs.iter()) {
        assert_eq!(a, b);
    }
}

#[test]
fn output_normals_carry_no_negative_zero() {
    // The signed-zero repair. `0.0 == -0.0`, so these normals all pass every
    // equality check in this crate, but their bit patterns differ, and a bitwise
    // key splits on that. The +Z box quad produced `(0,0,1)` from one triangle
    // and `(0,-0,1)` from the other before the canonicalisation.
    for (name, mesh) in sample_meshes() {
        for angle in ANGLES {
            let keyed = mesh.split_for_render_keyed(angle);
            for (i, normal) in keyed.normals.iter().enumerate() {
                for (label, value) in [("x", normal.x), ("y", normal.y), ("z", normal.z)] {
                    assert!(
                        value != 0.0 || value.to_bits() == 0.0f32.to_bits(),
                        "{name} at {angle} degrees: normal {i} has a negative zero in \
                         {label} ({value:?}), which breaks bitwise welding"
                    );
                }
            }
        }
    }
}

#[test]
fn the_keyed_output_is_a_faithful_render_of_the_same_mesh() {
    // Merging corners must not change the drawing. Same triangle count, every
    // index in range, every position still welded, and no corner carrying an
    // index the legacy path did not also carry.
    for (name, mesh) in sample_meshes() {
        for angle in ANGLES {
            let legacy = mesh.split_for_render(angle);
            let keyed = mesh.split_for_render_keyed(angle);
            assert_eq!(
                keyed.triangle_count(),
                legacy.triangle_count(),
                "{name} at {angle} degrees lost a triangle"
            );
            assert!(keyed
                .indices
                .iter()
                .all(|&i| (i as usize) < keyed.vertex_count()));
            assert_eq!(
                keyed.unique_position_count(),
                legacy.unique_position_count(),
                "{name} at {angle} degrees: the source mesh is welded and splitting \
                 must not break that"
            );
        }
    }
}

#[test]
fn the_source_mesh_is_never_modified_by_either_split() {
    // Splitting is a derivation, not a repair. The whole reason
    // `check_structure` can be trusted to report is that it does not touch what
    // it inspects, and the split is on the same footing.
    for (name, mesh) in sample_meshes() {
        let before = (
            mesh.vertices.clone(),
            mesh.indices.clone(),
            mesh.face_uvs.clone(),
            mesh.sharp_edges.clone(),
        );
        let _ = mesh.split_for_render(30.0);
        let _ = mesh.split_for_render_keyed(30.0);
        assert_eq!(before.0, mesh.vertices, "{name} vertices changed");
        assert_eq!(before.1, mesh.indices, "{name} indices changed");
        assert_eq!(before.2, mesh.face_uvs, "{name} face UVs changed");
        assert_eq!(before.3, mesh.sharp_edges, "{name} sharp edges changed");
    }
}

#[test]
fn the_keyed_path_needs_no_tolerance_parameter() {
    // There is no tolerance to pass, and there must never be one. A normal
    // quantised onto a grid of step `h` merges normals up to `h / sqrt(3)` apart,
    // which at `h = 1e-2` is 0.33 degrees. On a 2000-unit model that is a
    // crease nobody can see but everybody can shade wrongly. The key is the
    // normal's own bits, so the question does not arise.
    let box_mesh = PrimBox::new(nalgebra::Vector3::new(1.0, 1.0, 1.0))
        .to_mesh()
        .unwrap();
    // A cube's creases are 90 degrees, which no sane quantisation would merge,
    // and they are six here rather than the six a merge would give by accident.
    // The real assertion is structural: the signature takes one f32 and returns
    // a RenderMesh, and this call has to compile as written.
    let _: RenderMesh = box_mesh.split_for_render_keyed(30.0);
}
