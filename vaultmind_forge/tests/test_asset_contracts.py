import json
from pathlib import Path

from PIL import Image

from vaultmind_forge.forge_converter import (
    ConversionEnvelope,
    ConversionLossStatus,
    get_build123d_capabilities,
    create_build123d_box_envelope,
    execute_isolated_plan,
    execute_plan,
    get_ai_tool_manifest,
    plan_from_dict,
    get_cad_profiles,
    get_default_cad_profile,
    get_freecad_capabilities,
    collect_doctor_report,
    validate_output,
)
from vaultmind_forge.forge_intake.unified_converter import (
    ConversionStatus,
    UnifiedConverter,
)


def test_build123d_ai_manifest_and_structured_plan(tmp_path: Path):
    manifest = get_ai_tool_manifest()
    assert manifest["safety"]["arbitrary_python"] is False
    assert "box" in manifest["operations"]

    plan = plan_from_dict(
        {
            "name": "plate",
            "operations": [
                {
                    "operation": "box",
                    "parameters": {"size": [40, 20, 4]},
                },
                {
                    "operation": "cylinder",
                    "parameters": {"radius": 2, "height": 10},
                    "combine": "subtract",
                },
            ],
        }
    )
    result = execute_plan(plan, tmp_path)

    assert result.loss_status.value == "reinterpreted"
    assert Path(result.output_path).is_file()


def test_build123d_structured_plan_runs_in_worker(tmp_path: Path):
    result = execute_isolated_plan(
        {
            "name": "worker-box",
            "operations": [
                {
                    "operation": "box",
                    "parameters": {"size": [2, 3, 4]},
                }
            ],
            "output_formats": ["step", "stl"],
        },
        tmp_path,
        timeout_seconds=30,
    )

    assert result.loss_status.value == "reinterpreted"
    assert Path(result.output_path).is_file()


def test_doctor_report_is_non_secret_and_structured():
    report = collect_doctor_report()
    assert report["schema_version"] == "1.0"
    assert report["build123d"]["available"] is True
    assert "optional_commands" in report
    assert "api_key" not in str(report).lower()


def test_cad_profile_registry_marks_build123d_default():
    assert get_default_cad_profile().profile_id == "build123d"
    profiles = {profile.profile_id: profile for profile in get_cad_profiles()}
    assert profiles["freecad"].default is False
    assert profiles["openscad"].install_kind == "external_application"


def test_freecad_detection_is_side_effect_free():
    capabilities = get_freecad_capabilities()
    assert capabilities.backend == "freecad"
    assert isinstance(capabilities.available, bool)
    if not capabilities.available:
        assert capabilities.error


def test_intake_placeholder_format_is_explicitly_unsupported(tmp_path: Path):
    source = tmp_path / "model.dae"
    source.write_text("<COLLADA/>", encoding="utf-8")

    result = UnifiedConverter().convert(source, "asset-2")

    assert result.status == ConversionStatus.UNSUPPORTED
    assert result.to_envelope("asset-2").loss_status.value == "unsupported"


def test_build123d_default_capability():
    capabilities = get_build123d_capabilities()
    assert capabilities.available
    assert capabilities.backend == "build123d"
    assert "step" in capabilities.formats
    assert "stl" in capabilities.formats


def test_build123d_fixed_operation_returns_gui_safe_envelope(tmp_path: Path):
    envelope = create_build123d_box_envelope(
        (1.0, 2.0, 3.0),
        tmp_path,
        asset_id="box-1",
        target_engine="godot",
    )

    assert envelope.asset_id == "box-1"
    assert envelope.target_engine == "godot"
    assert envelope.target_format == "step+stl"
    assert envelope.loss_status.value == "reinterpreted"
    assert Path(envelope.output_path).is_file()
    assert envelope.metadata["output_validation"]["step"]["valid"]


def test_envelope_serializes_loss_status(tmp_path: Path):
    envelope = ConversionEnvelope(
        asset_id="asset-1",
        source_path=str(tmp_path / "source.obj"),
        source_format="obj",
        target_format="vaf",
        loss_status=ConversionLossStatus.REINTERPRETED,
    )

    encoded = json.dumps(envelope.to_dict())
    assert '"loss_status": "reinterpreted"' in encoded


def test_independent_obj_validator_rejects_out_of_range_faces(tmp_path: Path):
    output = tmp_path / "invalid.obj"
    output.write_text("v 0 0 0\nf 1 2 3\n", encoding="utf-8")

    result = validate_output(output)

    assert not result.valid
    assert result.metadata["vertices"] == 1
    assert result.errors


def test_independent_image_validator_accepts_valid_image(tmp_path: Path):
    output = tmp_path / "valid.png"
    Image.new("RGB", (4, 4), (10, 20, 30)).save(output)

    result = validate_output(output)

    assert result.valid
    assert result.metadata["width"] == 4
    assert result.metadata["height"] == 4


def test_intake_result_exposes_canonical_envelope(tmp_path: Path):
    source = tmp_path / "triangle.obj"
    source.write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n",
        encoding="utf-8",
    )

    result = UnifiedConverter().convert(source, "asset-1")
    envelope = result.to_envelope("asset-1")

    assert result.status == ConversionStatus.SUCCESS
    assert envelope.source_format == ".obj"
    assert envelope.target_format == "vaf"
    assert envelope.loss_status == ConversionLossStatus.REINTERPRETED
    assert envelope.warnings
