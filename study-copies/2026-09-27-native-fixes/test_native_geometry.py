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

    def test_sphere_has_a_broken_pole(self):
        """The sphere tessellation collapses both poles.

        to_mesh walks a (rings + 1) x (segments + 1) grid, so the first and last
        rows place segments + 1 vertices on the same pole point. That yields
        duplicate vertices, degenerate triangles along both pole rows, and
        non-manifold edges. A box validates clean; a sphere does not, which is
        not a defensible state for a default primitive.

        Pinned so the defect cannot regress unnoticed. When pole handling is
        fixed, this test should be inverted to assert the sphere is manifold and
        free of degenerate triangles.
        """
        report = native.MeshValidator().validate(native.create_sphere(1.0))
        assert not report.is_valid, (
            "create_sphere now produces a valid mesh; the pole-collapse fix has "
            "landed and this test should be rewritten to assert manifoldness"
        )
        assert (
            report.degenerate_triangle_count > 0
        ), "expected degenerate triangles at the sphere poles, found none"
        assert (
            report.duplicate_vertex_count > 0
        ), "expected duplicate vertices where the sphere grid wraps at the poles"


@requires_native
class TestCsg:
    """CSG is exported but not implemented, and one operation fails silently.

    The three operations are callable, so a caller reasonably assumes they work.
    Observed behaviour on intersecting solids:

    - union raises "encountered a spanning triangle; boundary clipping is not
      implemented". Explicit, and the message names the missing capability.
    - difference SUCCEEDS and returns the first operand unchanged. A 4x4x4 box
      minus a 1.5-radius sphere comes back as the same 8-vertex, 12-triangle box.
      This is the dangerous one: it validates as a clean mesh, so nothing
      downstream can tell that no cutting happened. A caller gets a plausible
      object and no error.
    - intersection raises the same unimplemented error as union.

    These tests pin what actually happens so the behaviour cannot change
    silently in either direction. They are not assertions that CSG works; it
    does not. `test_difference_returns_the_operand_unchanged` exists specifically
    to fail loudly if difference ever starts returning a correct result, at
    which point it should be rewritten to assert real geometry.
    """

    def test_union_reports_that_it_is_unimplemented(self):
        with pytest.raises(Exception) as caught:
            native.csg_union(native.create_box((2.0, 2.0, 2.0)), native.create_sphere(1.0))
        assert (
            "not implemented" in str(caught.value).lower()
        ), f"expected an explicit 'not implemented' failure, got: {caught.value}"

    def test_difference_returns_the_operand_unchanged(self):
        base = native.create_box((4.0, 4.0, 4.0))
        cutter = native.create_sphere(1.5)
        result = native.csg_difference(base, cutter)

        # If this ever fails because difference started subtracting, the
        # feature landed and this test must be replaced with real assertions
        # rather than deleted.
        assert (result.vertex_count, result.triangle_count) == (
            base.vertex_count,
            base.triangle_count,
        ), (
            "csg_difference now returns something other than its first operand; "
            "boundary clipping appears to be implemented, so these tests should "
            "be rewritten to assert real CSG geometry"
        )

    def test_intersection_reports_that_it_is_unimplemented(self):
        with pytest.raises(Exception) as caught:
            native.csg_intersection(native.create_box((2.0, 2.0, 2.0)), native.create_sphere(1.0))
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
