"""Native geometry extension contract tests.

The Rust/PyO3 core is a real, substantial surface: 35 exports covering
primitives, CSG, validation, size templates, and per-engine export. Nothing
tested any of it. The Python test suite passes whether the extension is present
or silently broken, so a native regression would only surface as a vague
geometry complaint at runtime.

These tests are skipped, not failed, when the extension is absent. That is the
distinction that matters: the extension is an optional runtime capability per
_native.py, and its absence is a supported configuration, not a defect. But
when it IS present, it has to work, and a broken build should fail here rather
than in someone's asset pipeline.

Note the API shape. ``vertex_count`` and ``triangle_count`` are properties, not
methods, and ``bounding_box`` IS a method. That asymmetry is real and is pinned
here so a binding change surfaces as a clear failure.
"""

from __future__ import annotations

import pytest

from types import ModuleType
from typing import Optional

from vaultmind_forge.forge_3d._native import NativeGeometryUnavailable, load_native

# Declared as Optional so the except branch can assign None. Without the
# annotation, the first assignment fixes the type to ModuleType and the None in
# the handler is a type error.
native: Optional[ModuleType]
NATIVE_ERROR: Optional[str]
try:
    native = load_native()
    NATIVE_ERROR = None
except NativeGeometryUnavailable as exc:  # pragma: no cover - env dependent
    native = None
    NATIVE_ERROR = str(exc)

requires_native = pytest.mark.skipif(
    native is None,
    reason=f"native geometry extension unavailable: {NATIVE_ERROR}",
)


def _ext() -> ModuleType:
    """The loaded extension, narrowed for the type checker.

    ``requires_native`` skips these tests when the extension is missing, but
    ``skipif`` is invisible to mypy, so a direct ``native.`` reference is a
    possible None dereference as far as the checker is concerned. Parametrised
    cases need a callable at decoration time, which is where that surfaces
    hardest, so the narrowing lives in one named place.
    """
    assert native is not None, "requires_native should have skipped this test"
    return native


# Every export the Python side is documented to rely on. A rename or removal in
# the Rust crate should fail here rather than at a call site.
EXPECTED_EXPORTS = (
    "create_box",
    "create_sphere",
    "create_cylinder",
    "create_cone",
    "create_plane",
    "csg_union",
    "csg_difference",
    "csg_intersection",
    "export_for_unity",
    "export_for_unreal",
    "export_for_godot",
    "Mesh",
    "MeshValidator",
    "get_all_templates",
)


class TestExtensionSurface:
    @requires_native
    def test_all_documented_exports_present(self):
        missing = [name for name in EXPECTED_EXPORTS if not hasattr(native, name)]
        assert not missing, f"native extension is missing exports: {missing}"

    @requires_native
    def test_module_reports_its_name(self):
        assert native.__name__ == "vaultmind_forge_core"

    def test_absent_extension_raises_the_declared_error(self):
        # Not a native test: this pins the failure mode when the capability is
        # missing, which is the supported configuration. The error must name
        # both remedies rather than being a bare ImportError.
        if native is not None:
            pytest.skip("native extension is present, cannot observe the absent path")
        with pytest.raises(NativeGeometryUnavailable) as caught:
            load_native()
        message = str(caught.value)
        assert "VAULTMIND_NATIVE_EXTENSION_PATH" in message
        assert "vaultmind_forge_core" in message


@requires_native
class TestPrimitives:
    def test_box_has_correct_topology(self):
        mesh = native.create_box((1.0, 2.0, 3.0))
        # A box is 8 corners and 12 triangles. A wrong count means the Rust
        # primitive or its tessellation changed.
        assert mesh.vertex_count == 8
        assert mesh.triangle_count == 12

    def test_box_bounding_box_matches_requested_size(self):
        mesh = native.create_box((1.0, 2.0, 3.0))
        bounds = mesh.bounding_box()
        assert bounds is not None, "bounding_box() returned nothing for a valid mesh"

    def test_box_centre_offset_is_applied(self):
        centred = native.create_box((1.0, 1.0, 1.0), (5.0, 0.0, 0.0))
        assert centred.vertex_count == 8, "offsetting a box must not change topology"
        bounds = centred.bounding_box()
        assert bounds is not None

    def test_sphere_is_denser_than_a_box(self):
        sphere = native.create_sphere(1.0)
        box = native.create_box((2.0, 2.0, 2.0))
        assert (
            sphere.triangle_count > box.triangle_count
        ), "a sphere should tessellate to more triangles than a box"

    def test_degenerate_size_is_rejected(self):
        # A zero-extent primitive is not a valid solid. The Rust side must
        # refuse it rather than emitting a broken mesh that fails validation
        # much later.
        with pytest.raises(Exception):
            native.create_box((0.0, 1.0, 1.0))

    def test_sphere_is_watertight_with_no_degenerate_triangles(self):
        """The sphere pole and seam handling.

        to_mesh used to walk a (rings + 1) x (segments + 1) grid, so the first
        and last rows placed segments + 1 vertices on the same pole point, and
        the UV seam emitted two coincident-but-distinct vertices. That gave 64
        degenerate triangles, 79 duplicate vertices, 96 non-manifold edges and
        96 boundary edges. Poles are now single vertices with triangle fans, and
        the seam reuses seg 0.

        This mattered beyond tidiness. A solid with boundary edges cannot answer
        a point-in-solid query, and CSG depends on exactly that, so the defect
        silently broke every boolean operation.
        """
        report = native.MeshValidator().validate(native.create_sphere(1.0))
        assert report.degenerate_triangle_count == 0, "poles must not collapse"
        assert report.duplicate_vertex_count == 0, "the UV seam must be welded"
        assert report.non_manifold_edge_count == 0
        assert report.hole_count == 0
        assert report.is_manifold, "sphere must be manifold"
        assert report.is_watertight, "sphere must be a closed solid"
        assert report.is_valid, f"issues: {report.issues}"


@requires_native
class TestCsg:
    """CSG: containment cases resolve correctly, spanning cases refuse.

    The engine classifies each triangle as inside, outside, or spanning the
    other solid, and refuses rather than guessing when a triangle spans.

    - Containment cases are correct for all three operations, including a solid
      fully inside another and a solid fully containing another.
    - A triangle that genuinely straddles the other surface raises "boundary
      clipping is not implemented". That is honest. A real clipping
      implementation is still outstanding, and guessing would produce wrong
      geometry with no error.

    These cases were all silently wrong before. Point-inside classification
    always reported "outside", so every triangle was kept and difference
    returned its first operand unchanged for every input. The output looked
    plausible and valid, which is why the two defects below went unnoticed for
    so long.
    """

    def test_difference_of_enclosed_solid_is_empty(self):
        # Box half-extent 1.0 is entirely inside a radius-3 sphere, so
        # subtracting the sphere must leave nothing at all. This used to return
        # the box, because point-inside classification always reported "outside"
        # and every triangle was kept.
        result = native.csg_difference(
            native.create_box((2.0, 2.0, 2.0)), native.create_sphere(3.0)
        )
        assert (result.vertex_count, result.triangle_count) == (0, 0), (
            "subtracting an enclosing solid must leave an empty mesh, not the " "original operand"
        )

    def test_difference_with_fully_interior_solid_leaves_outer_solid(self):
        # A radius-1.5 sphere sits inside a 4-wide box. No triangle of the box is
        # inside the sphere, so all are kept. For a solid operand that is the
        # correct result; a caller wanting a hollow shell must pass a shell.
        outer = native.create_box((4.0, 4.0, 4.0))
        result = native.csg_difference(outer, native.create_sphere(1.5))
        assert (result.vertex_count, result.triangle_count) == (
            outer.vertex_count,
            outer.triangle_count,
        )

    def test_intersection_keeps_the_inner_operand(self):
        # The box contributes nothing and the sphere contributes everything. An
        # engine that only inspects the first operand returns nothing here.
        sphere = native.create_sphere(1.5)
        result = native.csg_intersection(native.create_box((4.0, 4.0, 4.0)), sphere)
        assert result.triangle_count == sphere.triangle_count, (
            "intersection of a solid with a fully-contained solid must be the " "inner solid"
        )

    def test_intersection_keeps_the_first_operand_when_it_is_inner(self):
        result = native.csg_intersection(
            native.create_sphere(3.0), native.create_box((2.0, 2.0, 2.0))
        )
        assert (result.vertex_count, result.triangle_count) == (8, 12)

    def test_union_of_disjoint_solids_keeps_both(self):
        a = native.create_box((2.0, 2.0, 2.0))
        b = native.create_box((1.0, 1.0, 1.0), (3.0, 0.0, 0.0))
        result = native.csg_union(a, b)
        assert (result.vertex_count, result.triangle_count) == (16, 24)
        assert native.MeshValidator().validate(result).is_valid

    def test_genuinely_spanning_difference_refuses(self):
        # Radius 2.5 against a 4-wide box crosses the box surface, so clipping
        # would be required. The engine must say so rather than guess.
        with pytest.raises(Exception) as caught:
            native.csg_difference(native.create_box((4.0, 4.0, 4.0)), native.create_sphere(2.5))
        assert (
            "not implemented" in str(caught.value).lower()
        ), f"expected an explicit 'not implemented' failure, got: {caught.value}"

    def test_genuinely_spanning_union_refuses(self):
        with pytest.raises(Exception) as caught:
            native.csg_union(native.create_box((4.0, 4.0, 4.0)), native.create_sphere(2.5))
        assert (
            "not implemented" in str(caught.value).lower()
        ), f"expected an explicit 'not implemented' failure, got: {caught.value}"


@requires_native
class TestValidation:
    def test_a_clean_box_validates(self):
        mesh = native.create_box((1.0, 1.0, 1.0))
        report = native.MeshValidator().validate(mesh)
        assert report.is_valid, f"a freshly created box should be valid, got: {report.issues}"
        assert report.is_watertight, "a box is a closed solid and must be watertight"

    def test_report_exposes_the_documented_fields(self):
        report = native.MeshValidator().validate(native.create_box((1.0, 1.0, 1.0)))
        for field in (
            "is_valid",
            "is_manifold",
            "is_watertight",
            "issues",
            "degenerate_triangle_count",
            "duplicate_vertex_count",
            "non_manifold_edge_count",
            "hole_count",
            "has_self_intersections",
        ):
            assert hasattr(report, field), f"ValidationReport is missing {field}"


@requires_native
class TestTemplates:
    def test_templates_are_returned_and_non_empty(self):
        templates = native.get_all_templates()
        assert templates is not None
        assert len(templates) > 0, "the size template catalogue should not be empty"

    def test_templates_can_be_filtered_by_category(self):
        by_category = native.get_templates_by_category("character")
        # A category with no members is legitimate; what must not happen is a
        # crash, or a non-list return.
        assert by_category is not None


@requires_native
class TestLoaderContract:
    def test_loader_does_not_mutate_sys_path_implicitly(self, monkeypatch):
        # _native.py promises that generated build directories are never added
        # to sys.path implicitly. Loading must not do it behind the caller's
        # back when the module is already importable.
        import sys

        before = list(sys.path)
        try:
            load_native()
        except NativeGeometryUnavailable:
            pass
        added = [entry for entry in sys.path if entry not in before]
        generated = [e for e in added if "target" in e and "rust_core" in e]
        assert not generated, f"loader added a generated build directory to sys.path: {generated}"


@requires_native
class TestRenderSplit:
    """One welded mesh, two usable representations.

    A ``Mesh`` keeps positions welded so a closed solid stays manifold for CSG
    and collision. A renderer needs one normal and one UV per output vertex,
    which forces duplication at every crease and seam. These tests pin the
    derivation between the two.
    """

    def test_smooth_sphere_duplicates_only_its_uv_seam(self):
        sphere = native.create_sphere(1.0)
        render = sphere.split_for_render(180.0)

        # This used to assert that a smooth sphere duplicates nothing at all,
        # which recorded a defect as expected behaviour. It held only because
        # the sphere had no per-corner UV layer: with a single UV per vertex the
        # seg-0 column carried u = 0 and the wrap quad interpolated across it,
        # losing the last texel of every wrap-around UV. The mesh was smooth,
        # watertight, and textured slightly wrong.
        #
        # Now the seam is expressed per corner, and the seg-0 column has to
        # split: each of those vertices genuinely belongs to the quad at u = 0
        # and to the wrap quad at u = 1. So 482 + 15 = 497.
        #
        # The part that must not move is the position count. A sphere is a
        # welded sphere; only attributes may split, because CAD consumers and
        # the point-in-solid classifier both key on vertex identity.
        interior_rings = 15
        assert (
            render.vertex_count == sphere.vertex_count + interior_rings
        ), f"expected the UV seam column and nothing else: {render.vertex_count}"
        assert render.unique_position_count == sphere.vertex_count
        assert render.triangle_count == sphere.triangle_count

    def test_split_never_changes_topology(self):
        for name, mesh in [
            ("box", native.create_box((1.0, 1.0, 1.0))),
            ("sphere", native.create_sphere(1.0)),
            ("cylinder", native.create_cylinder(1.0, 2.0)),
            ("cone", native.create_cone(1.0, 2.0)),
            ("torus", native.create_torus(2.0, 1.0)),
        ]:
            render = mesh.split_for_render(180.0)
            assert render.triangle_count == mesh.triangle_count, name
            assert render.uvs.__len__() == render.vertex_count, name
            assert render.normals.__len__() == render.vertex_count, name
            # Positions stay welded: the render mesh may repeat a position, but
            # it never invents one that is not in the topology.
            source = {tuple(v) for v in mesh.vertices}
            for position in render.vertices:
                assert tuple(position) in source, f"{name} invented a position {position}"

    def test_cube_renders_flat_with_uv_islands(self):
        box = native.create_box((1.0, 1.0, 1.0))
        render = box.split_for_render(180.0)

        assert box.vertex_count == 8, "the topology must stay welded"
        assert box.sharp_edge_count == 12, "a cube has twelve hard edges"
        assert render.unique_position_count == 8, "positions must still be the 8 corners"
        assert render.vertex_count > 8, "flat shading must duplicate corners"

        # A planar box mapping puts each face's four corners at the unit square's
        # corners. Before per-corner UVs existed, every UV was (0, 0) and the cube
        # was untexturable.
        corners = {(round(u, 4), round(v, 4)) for u, v in render.uvs}
        assert corners == {(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)}

        # Exactly six distinct face normals, all axis aligned.
        directions = {tuple(round(c, 4) for c in n) for n in render.normals}
        assert len(directions) == 6, f"expected 6 face normals, got {directions}"
        for normal in directions:
            assert sorted(abs(c) for c in normal)[-1] == 1.0, normal

    def test_flat_shaded_faces_use_axis_aligned_normals(self):
        # A cube's face normal must equal its own plane normal, not an average
        # with its neighbours. This is what "Mark Sharp" buys.
        box = native.create_box((1.0, 1.0, 1.0))
        render = box.split_for_render(180.0)
        indices = render.indices
        positions = render.vertices
        for t in range(0, len(indices), 3):
            a, b, c = (positions[indices[t + k]] for k in range(3))
            u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
            v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
            normal = (
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0],
            )
            length = sum(component * component for component in normal) ** 0.5
            assert length > 1e-6, "degenerate face"
            shading = render.normals[indices[t]]
            dot = sum(n * s for n, s in zip(normal, shading)) / length
            assert dot > 0.999, f"face is smoothed, not flat: {dot}"

    def test_zero_angle_flattens_and_180_smoothes(self):
        sphere = native.create_sphere(1.0)
        flat = sphere.split_for_render(0.0)
        smooth = sphere.split_for_render(180.0)
        assert flat.vertex_count > smooth.vertex_count
        assert flat.triangle_count == smooth.triangle_count

    def test_negative_angle_behaves_as_180(self):
        sphere = native.create_sphere(1.0)
        assert (
            sphere.split_for_render(-1.0).vertex_count
            == sphere.split_for_render(180.0).vertex_count
        )


@requires_native
class TestPrimitiveWatertightness:
    """Every primitive must be a closed, correctly wound solid.

    An unwatertight solid cannot answer point-in-solid queries, so CSG
    misclassifies triangles against it. That is not theoretical: cylinder, cone,
    and torus each shipped with an unjoined seam column, because the wrap vertex
    sat at theta = 2*PI where sin is about -2.4e-7 rather than 0, making it a
    *near* duplicate that no edge ever joined.
    """

    @staticmethod
    def _edge_defects(mesh):
        seen = {}
        indices = mesh.indices
        for t in range(0, len(indices), 3):
            for k in range(3):
                a, b = indices[t + k], indices[t + (k + 1) % 3]
                key = (a, b) if a < b else (b, a)
                seen[key] = seen.get(key, 0) + 1
        boundary = [e for e, c in seen.items() if c == 1]
        non_manifold = [e for e, c in seen.items() if c > 2]
        return boundary, non_manifold

    @pytest.mark.parametrize(
        "name, mesh",
        [
            ("box", lambda: _ext().create_box((1.0, 1.0, 1.0))),
            ("sphere", lambda: _ext().create_sphere(1.0)),
            ("cylinder", lambda: _ext().create_cylinder(1.0, 2.0)),
            ("cone", lambda: _ext().create_cone(1.0, 2.0)),
            ("torus", lambda: _ext().create_torus(2.0, 1.0)),
        ],
    )
    def test_primitive_is_closed_and_manifold(self, name, mesh):
        built = mesh()
        boundary, non_manifold = self._edge_defects(built)
        assert not boundary, f"{name} has {len(boundary)} boundary edges: {boundary[:8]}"
        assert not non_manifold, f"{name} has {len(non_manifold)} non-manifold edges"

    @pytest.mark.parametrize(
        "name, mesh",
        [
            ("box", lambda: _ext().create_box((1.0, 1.0, 1.0))),
            ("sphere", lambda: _ext().create_sphere(1.0)),
            ("cylinder", lambda: _ext().create_cylinder(1.0, 2.0)),
            ("cone", lambda: _ext().create_cone(1.0, 2.0)),
            ("torus", lambda: _ext().create_torus(2.0, 1.0)),
        ],
    )
    def test_primitive_normals_point_outward(self, name, mesh):
        built = mesh()
        positions = built.vertices
        centre = [sum(p[axis] for p in positions) / len(positions) for axis in range(3)]
        for i, normal in enumerate(built.normals):
            outward = [positions[i][axis] - centre[axis] for axis in range(3)]
            dot = sum(n * o for n, o in zip(normal, outward))
            # A torus has a hole, so its inner surface legitimately faces the
            # centre. The assertion is only meaningful for the star-shaped
            # solids, and the torus is excluded rather than quietly excused.
            if name == "torus":
                continue
            assert dot > 0.0, f"{name} vertex {i} normal points inward: {dot}"


@requires_native
class TestObjExportCarriesAttributes:
    def test_export_writes_real_uvs_and_no_negative_zero(self, tmp_path):
        box = native.create_box((1.0, 1.0, 1.0))
        path = tmp_path / "cube.obj"
        box.export_obj(str(path))
        text = path.read_text(encoding="utf-8")

        vt = [line for line in text.splitlines() if line.startswith("vt ")]
        vn = [line for line in text.splitlines() if line.startswith("vn ")]
        faces = [line for line in text.splitlines() if line.startswith("f ")]

        assert len(faces) == 12, "a cube has twelve triangles"
        assert len(vt) == len(vn), "position, UV, and normal streams must line up"
        # Negative zero would spell one normal direction two ways, which is how a
        # cube came to export six distinct faces as seven. It has to be tested per
        # token: "-0.5" is a legitimate coordinate that contains the substring.
        for line in text.splitlines():
            for token in line.split():
                assert token != "-0", f"negative zero reached the export: {line!r}"
        assert len(set(vn)) == 6, f"a cube has six face normals: {sorted(set(vn))}"
        for line in faces:
            for reference in line.split()[1:]:
                assert reference.count("/") == 2, f"incomplete face reference {reference}"


class TestKeyedRenderSplit:
    """The attribute-keyed split, which is MikkTSpace's rule.

    The reference is Khronos `Models/Box.gltf`: 24 positions, 36 indices. The
    legacy split keys on the smoothing group, so the two triangles of a coplanar
    quad are always different groups and it emits 36. The keyed split merges on
    `(position, normal, uv)` compared bit for bit, and gets to 24.
    """

    def test_box_matches_the_gltf_reference_count(self):
        box = native.create_box((1.0, 1.0, 1.0))
        render = box.split_for_render_keyed(30.0)
        assert (
            render.vertex_count == 24
        ), f"the reference glTF cube has 24 positions, got {render.vertex_count}"
        assert render.triangle_count == 12
        assert len(render.indices) == 36

    def test_keyed_never_emits_more_than_legacy(self):
        shapes = [
            ("box", native.create_box((1.0, 1.0, 1.0))),
            ("sphere", native.create_sphere(1.0)),
            ("cylinder", native.create_cylinder(1.0, 2.0)),
            ("cone", native.create_cone(1.0, 2.0)),
            ("torus", native.create_torus(2.0, 1.0)),
        ]
        for name, mesh in shapes:
            for angle in (0.0, 30.0, 180.0):
                legacy = mesh.split_for_render(angle)
                keyed = mesh.split_for_render_keyed(angle)
                assert keyed.vertex_count <= legacy.vertex_count, (
                    f"{name} at {angle} degrees: keyed {keyed.vertex_count} "
                    f"exceeded legacy {legacy.vertex_count}"
                )

    def test_keyed_keeps_positions_welded(self):
        # Splitting duplicates attributes, never positions. A render form that
        # broke the weld would mean the source mesh was modified.
        for mesh in (native.create_box((1.0, 1.0, 1.0)), native.create_sphere(1.0)):
            keyed = mesh.split_for_render_keyed(30.0)
            assert keyed.unique_position_count == mesh.vertex_count, (
                f"{keyed.unique_position_count} welded positions in the render "
                f"form against {mesh.vertex_count} in the source"
            )

    def test_a_smooth_sphere_is_identical_either_way(self):
        # The case where the two strategies should agree exactly, and the guard
        # against a change to the shared fan or UV logic leaking into one path.
        sphere = native.create_sphere(1.0)
        legacy = sphere.split_for_render(30.0)
        keyed = sphere.split_for_render_keyed(30.0)
        assert keyed.vertex_count == legacy.vertex_count
        assert list(keyed.indices) == list(legacy.indices)

    def test_creases_survive(self):
        # Merging must never round off an edge. A cube has six face normals; if
        # any two merged, the box would have a bevelled edge.
        box = native.create_box((1.0, 1.0, 1.0))
        for angle in (0.0, 30.0, 180.0):
            render = box.split_for_render_keyed(angle)
            normals = {tuple(round(c, 3) for c in n) for n in render.normals}
            assert len(normals) == 6, (
                f"at {angle} degrees got {len(normals)} distinct normals, "
                f"expected 6: {sorted(normals)}"
            )


class TestPerCornerUvLayer:
    """The per-corner UV buffer every primitive now fills.

    A per-corner layer is a parallel array: `face_uvs[f]` annotates face `f`,
    and if the two are built in different orders the texture lands on the wrong
    triangle. Nothing about that is visible in a vertex count, a winding check
    or a topology check, which is why it needs its own tests.
    """

    def test_every_primitive_fills_the_layer(self):
        for name, mesh in [
            ("box", native.create_box((1.0, 1.0, 1.0))),
            ("sphere", native.create_sphere(1.0)),
            ("cylinder", native.create_cylinder(1.0, 2.0)),
            ("cone", native.create_cone(1.0, 2.0)),
            ("torus", native.create_torus(2.0, 1.0)),
        ]:
            assert len(mesh.face_uvs) == mesh.triangle_count, (
                f"{name}: the per-corner UV layer covers {len(mesh.face_uvs)} of "
                f"{mesh.triangle_count} faces"
            )
            for face in mesh.face_uvs:
                assert len(face) == 3

    def test_the_cone_layer_is_in_face_order(self):
        # The regression. The cone emits all `segments` base disc triangles and
        # then all `segments` flank triangles, but the layer used to be built by
        # interleaving a disc UV and a flank UV per iteration. So `face_uvs[f]`
        # was the wrong face for every odd f and for everything after it, and
        # only the first entry happened to line up.
        #
        # The two islands are trivially distinguishable: a disc triangle has the
        # cap centre at exactly (0.5, 0.5) and a flank triangle has the apex at
        # exactly (0.5, 1.0). If the order is right, the first half of the faces
        # are all disc and the second half are all flank.
        cone = native.create_cone(1.0, 2.0)
        faces = cone.face_uvs
        half = len(faces) // 2

        def has(face, point):
            return any(abs(uv[0] - point[0]) < 1e-6 and abs(uv[1] - point[1]) < 1e-6 for uv in face)

        # The cap centre is the unambiguous marker: (0.5, 0.5). The apex at
        # (0.5, 1.0) cannot be used to tell the islands apart, because the polar
        # disc is inscribed in the unit square and its rim passes through exactly
        # that point - disc_uv at a quarter turn lands on (0.5, 1.0). A rim
        # point and an apex are genuinely the same pair of numbers.
        #
        # So the assertion is that precisely the first half of the faces carry
        # the cap centre, and that they are the first half and not some other
        # half. That is non-vacuous: if the layer were interleaved, these markers
        # would alternate and the index set would not be a prefix.
        marked = [i for i, face in enumerate(faces) if has(face, (0.5, 0.5))]
        assert marked == list(range(half)), (
            f"the {half} faces carrying the cap centre are {marked[:8]}..., not the "
            f"first {half}, so the UV layer is not in face order"
        )
        for index, face in enumerate(faces[half:], start=half):
            assert any(abs(uv[1] - 1.0) < 1e-6 for uv in face), (
                f"face {index} is in the flank half but no corner sits on the apex "
                f"row v = 1.0: {face}"
            )
            assert not has(face, (0.5, 0.5)), (
                f"face {index} is in the flank half but carries the cap centre at "
                f"(0.5, 0.5), so the UV layer is out of order: {face}"
            )

    def test_a_sphere_wrap_reaches_one(self):
        # The seam is only useful if the far side is recorded. Before the layer
        # existed, the seg-0 vertex carried u = 0 and the wrap interpolated across
        # it, losing the last texel of every wrap-around UV.
        sphere = native.create_sphere(1.0)
        us = [uv[0] for face in sphere.face_uvs for uv in face]
        vs = [uv[1] for face in sphere.face_uvs for uv in face]
        assert max(us) == pytest.approx(1.0), "the sphere's u wrap never reaches 1.0"
        assert max(vs) == pytest.approx(1.0), "and v never reaches the south pole"
        assert min(us) == pytest.approx(0.0)

    def test_a_torus_wrap_reaches_one_in_both_directions(self):
        # A torus closes twice, so it has two seams. Handling only the major one
        # would still tile wrong around the tube.
        torus = native.create_torus(2.0, 1.0)
        us = [uv[0] for face in torus.face_uvs for uv in face]
        vs = [uv[1] for face in torus.face_uvs for uv in face]
        assert max(us) == pytest.approx(1.0), "the major wrap never reaches u = 1.0"
        assert max(vs) == pytest.approx(1.0), "the minor wrap never reaches v = 1.0"

    def test_all_uvs_stay_inside_the_unit_square(self):
        for name, mesh in [
            ("box", native.create_box((1.0, 1.0, 1.0))),
            ("sphere", native.create_sphere(1.0)),
            ("cylinder", native.create_cylinder(1.0, 2.0)),
            ("cone", native.create_cone(1.0, 2.0)),
            ("torus", native.create_torus(2.0, 1.0)),
        ]:
            for index, face in enumerate(mesh.face_uvs):
                for corner, uv in enumerate(face):
                    assert 0.0 <= uv[0] <= 1.0 and 0.0 <= uv[1] <= 1.0, (
                        f"{name} face {index} corner {corner} has uv {uv}, outside "
                        f"the unit square"
                    )

    def test_joining_the_seams_did_not_cost_a_welded_position(self):
        # The regression guard for the whole pass. Expressing a seam in the
        # attribute layer must not reopen the watertightness hole that a spare
        # column of vertices used to cause, and must not move a vertex.
        for name, mesh in [
            ("box", native.create_box((1.0, 1.0, 1.0))),
            ("sphere", native.create_sphere(1.0)),
            ("cylinder", native.create_cylinder(1.0, 2.0)),
            ("cone", native.create_cone(1.0, 2.0)),
            ("torus", native.create_torus(2.0, 1.0)),
        ]:
            report = native.MeshValidator().validate(mesh)
            assert report.is_watertight, f"{name} is no longer watertight: {report.issues}"
            assert (
                report.non_manifold_edge_count == 0
            ), f"{name} has {report.non_manifold_edge_count} non-manifold edges"
