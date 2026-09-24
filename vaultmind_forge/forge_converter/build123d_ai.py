"""AI-facing, constrained build123d planning and execution.

The planner accepts structured primitive operations and boolean intent. It does
not accept or execute arbitrary Python source. A separate worker boundary is
required for user-authored build123d programs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .build123d_adapter import get_build123d_capabilities
from .contracts import ConversionEnvelope, ConversionLossStatus


class Build123DPlanError(ValueError):
    """Raised when an AI CAD plan violates the allowlisted contract."""


@dataclass(frozen=True)
class Build123DOperation:
    operation: str
    parameters: Mapping[str, Any]
    combine: str = "add"


@dataclass(frozen=True)
class Build123DPlan:
    name: str = "ai-build123d-model"
    operations: Tuple[Build123DOperation, ...] = field(default_factory=tuple)
    output_formats: Tuple[str, ...] = ("step", "stl")


_OPERATIONSchemas: Dict[str, Dict[str, Any]] = {
    "box": {
        "required": ("size",),
        "properties": {"size": "positive_vector3"},
    },
    "cylinder": {
        "required": ("radius", "height"),
        "properties": {"radius": "positive_number", "height": "positive_number"},
    },
    "sphere": {
        "required": ("radius",),
        "properties": {"radius": "positive_number"},
    },
    "cone": {
        "required": ("bottom_radius", "top_radius", "height"),
        "properties": {
            "bottom_radius": "non_negative_number",
            "top_radius": "non_negative_number",
            "height": "positive_number",
        },
    },
    "torus": {
        "required": ("major_radius", "minor_radius"),
        "properties": {
            "major_radius": "positive_number",
            "minor_radius": "positive_number",
        },
    },
}

_COMBINATIONS = {"add", "subtract", "intersect"}
_OUTPUT_FORMATS = {"step", "stl"}


def _positive(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise Build123DPlanError(f"{field_name} must be numeric") from error
    if not math.isfinite(number) or number <= 0:
        raise Build123DPlanError(f"{field_name} must be finite and greater than zero")
    return number


def _non_negative(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise Build123DPlanError(f"{field_name} must be numeric") from error
    if not math.isfinite(number) or number < 0:
        raise Build123DPlanError(f"{field_name} must be finite and non-negative")
    return number


def _validate_parameters(operation: str, parameters: Mapping[str, Any]) -> Dict[str, Any]:
    schema = _OPERATIONSchemas.get(operation)
    if schema is None:
        raise Build123DPlanError(f"unsupported build123d operation: {operation}")

    unknown = set(parameters) - set(schema["properties"])
    if unknown:
        raise Build123DPlanError(
            f"{operation} has unsupported parameters: {', '.join(sorted(unknown))}"
        )
    missing = set(schema["required"]) - set(parameters)
    if missing:
        raise Build123DPlanError(
            f"{operation} is missing parameters: {', '.join(sorted(missing))}"
        )

    validated: Dict[str, Any] = {}
    for name, value in parameters.items():
        if name == "size":
            if not isinstance(value, (list, tuple)) or len(value) != 3:
                raise Build123DPlanError("box.size must contain exactly three numbers")
            validated[name] = [_positive(item, f"box.size[{index}]") for index, item in enumerate(value)]
        elif name in {"bottom_radius", "top_radius"}:
            validated[name] = _non_negative(value, f"{operation}.{name}")
        else:
            validated[name] = _positive(value, f"{operation}.{name}")

    if operation == "torus" and validated["major_radius"] <= validated["minor_radius"]:
        raise Build123DPlanError("torus.major_radius must be greater than minor_radius")
    return validated


def plan_from_dict(data: Mapping[str, Any]) -> Build123DPlan:
    """Parse and validate an AI-provided structured plan."""
    if not isinstance(data, Mapping):
        raise Build123DPlanError("plan must be an object")
    operations_data = data.get("operations")
    if not isinstance(operations_data, Sequence) or isinstance(operations_data, (str, bytes)):
        raise Build123DPlanError("plan.operations must be a list")
    if not 1 <= len(operations_data) <= 32:
        raise Build123DPlanError("plan.operations must contain between 1 and 32 operations")

    name = str(data.get("name", "ai-build123d-model"))
    if not name or Path(name).name != name or name in {".", ".."}:
        raise Build123DPlanError("plan.name must be a simple file-safe name")

    operations: List[Build123DOperation] = []
    for index, item in enumerate(operations_data):
        if not isinstance(item, Mapping):
            raise Build123DPlanError(f"operation {index} must be an object")
        operation = item.get("operation")
        parameters = item.get("parameters")
        combine = item.get("combine", "add")
        if not isinstance(operation, str) or not isinstance(parameters, Mapping):
            raise Build123DPlanError(f"operation {index} requires operation and parameters")
        if combine not in _COMBINATIONS:
            raise Build123DPlanError(f"operation {index} has invalid combine mode")
        if index == 0 and combine != "add":
            raise Build123DPlanError("the first operation must use combine='add'")
        operations.append(
            Build123DOperation(
                operation=operation,
                parameters=_validate_parameters(operation, parameters),
                combine=combine,
            )
        )

    output_formats = tuple(data.get("output_formats", ("step", "stl")))
    if not output_formats or any(fmt not in _OUTPUT_FORMATS for fmt in output_formats):
        raise Build123DPlanError("output_formats must contain only step and/or stl")

    return Build123DPlan(
        name=name,
        operations=tuple(operations),
        output_formats=output_formats,
    )


def get_ai_tool_manifest() -> Dict[str, Any]:
    """Return a provider-neutral manifest for AI tool discovery."""
    return {
        "name": "lpg.build123d",
        "description": "Create an allowlisted build123d B-rep model from structured operations.",
        "version": "1.0",
        "input_schema": {
            "type": "object",
            "required": ["operations"],
            "properties": {
                "name": {"type": "string"},
                "operations": {"type": "array", "minItems": 1, "maxItems": 32},
                "output_formats": {
                    "type": "array",
                    "items": {"enum": sorted(_OUTPUT_FORMATS)},
                },
            },
        },
        "operations": _OPERATIONSchemas,
        "combination_modes": sorted(_COMBINATIONS),
        "safety": {
            "arbitrary_python": False,
            "allowed_backends": ["build123d"],
            "untrusted_source": "worker_only",
        },
        "example": {
            "name": "plate-with-hole-placeholder",
            "operations": [
                {
                    "operation": "box",
                    "parameters": {"size": [40, 20, 4]},
                    "combine": "add",
                }
            ],
            "output_formats": ["step", "stl"],
        },
    }


def _make_part(operation: Build123DOperation) -> Any:
    from build123d import Box, Cone, Cylinder, Sphere, Torus

    parameters = operation.parameters
    if operation.operation == "box":
        return Box(*parameters["size"])
    if operation.operation == "cylinder":
        return Cylinder(parameters["radius"], parameters["height"])
    if operation.operation == "sphere":
        return Sphere(parameters["radius"])
    if operation.operation == "cone":
        return Cone(
            parameters["bottom_radius"],
            parameters["top_radius"],
            parameters["height"],
        )
    if operation.operation == "torus":
        return Torus(parameters["major_radius"], parameters["minor_radius"])
    raise Build123DPlanError(f"unsupported build123d operation: {operation.operation}")


def execute_plan(
    plan: Build123DPlan | Mapping[str, Any],
    output_dir: str | Path,
) -> ConversionEnvelope:
    """Execute a validated structured plan and return a conversion envelope."""
    if isinstance(plan, Build123DPlan):
        plan = plan_from_dict(
            {
                "name": plan.name,
                "operations": [
                    {
                        "operation": operation.operation,
                        "parameters": dict(operation.parameters),
                        "combine": operation.combine,
                    }
                    for operation in plan.operations
                ],
                "output_formats": list(plan.output_formats),
            }
        )
    else:
        plan = plan_from_dict(plan)

    capabilities = get_build123d_capabilities()
    if not capabilities.available:
        return ConversionEnvelope(
            asset_id=plan.name,
            source_format="build123d-plan",
            target_format=",".join(plan.output_formats),
            loss_status=ConversionLossStatus.FAILED,
            errors=[f"build123d unavailable: {capabilities.error}"],
            provenance={"tool": "build123d", "operation": "structured_plan"},
        )

    result = None
    for index, operation in enumerate(plan.operations):
        part = _make_part(operation)
        if result is None:
            result = part
        elif operation.combine == "add":
            result = result + part
        elif operation.combine == "subtract":
            result = result - part
        else:
            result = result & part

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    outputs: Dict[str, str] = {}
    from build123d import export_step, export_stl

    for output_format in plan.output_formats:
        destination = output_path / f"{plan.name}.{output_format}"
        if output_format == "step":
            export_step(result, str(destination))
        else:
            export_stl(result, str(destination))
        outputs[output_format] = str(destination)

    validation = {
        output_format: {
            "valid": Path(path).is_file() and Path(path).stat().st_size > 0,
            "bytes": Path(path).stat().st_size if Path(path).is_file() else 0,
        }
        for output_format, path in outputs.items()
    }
    valid = all(item["valid"] for item in validation.values())
    return ConversionEnvelope(
        asset_id=plan.name,
        source_format="build123d-plan",
        target_format=",".join(plan.output_formats),
        media_type="application/step" if "step" in outputs else "model/stl",
        output_path=outputs.get("step") or outputs.get("stl"),
        loss_status=ConversionLossStatus.REINTERPRETED if valid else ConversionLossStatus.FAILED,
        loss_reasons=["STL is tessellated; STEP preserves the B-rep result"],
        errors=[] if valid else ["build123d output validation failed"],
        metadata={
            "operations": [operation.__dict__ for operation in plan.operations],
            "outputs": outputs,
            "output_validation": validation,
        },
        provenance={
            "tool": "build123d",
            "tool_version": capabilities.version,
            "operation": "structured_plan",
        },
    )
