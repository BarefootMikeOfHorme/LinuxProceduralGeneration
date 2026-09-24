"""Trusted build123d capability adapter.

This module exposes fixed, trusted B-rep operations for LPG's default CAD
runtime. Arbitrary build123d source files must be executed by an isolated
worker, not imported into the main process.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .contracts import ConversionEnvelope, ConversionLossStatus


@dataclass(frozen=True)
class Build123DCapabilities:
    backend: str
    available: bool
    version: Optional[str]
    formats: Tuple[str, ...]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["formats"] = list(self.formats)
        return data


def get_build123d_capabilities() -> Build123DCapabilities:
    """Return build123d availability without importing optional geometry code."""
    try:
        import build123d
    except Exception as error:
        return Build123DCapabilities(
            backend="build123d",
            available=False,
            version=None,
            formats=(),
            error=str(error),
        )

    return Build123DCapabilities(
        backend="build123d",
        available=True,
        version=getattr(build123d, "__version__", "unknown"),
        formats=("step", "stl"),
    )


def create_build123d_box(
    size: Tuple[float, float, float],
    output_dir: str | Path,
    stem: str = "box",
) -> Dict[str, Any]:
    """Create a trusted build123d box and export STEP/STL.

    This is a fixed operation for smoke tests and capability validation. It is
    not a general-purpose evaluator for user-supplied build123d code.
    """
    capabilities = get_build123d_capabilities()
    if not capabilities.available:
        raise RuntimeError(
            f"build123d is unavailable: {capabilities.error or 'unknown import failure'}"
        )
    if len(size) != 3 or any(value <= 0 for value in size):
        raise ValueError("size must contain three positive dimensions")

    from build123d import Box, export_step, export_stl

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    step_path = output_path / f"{stem}.step"
    stl_path = output_path / f"{stem}.stl"
    part = Box(*size)
    export_step(part, str(step_path))
    export_stl(part, str(stl_path))

    return {
        "capabilities": capabilities.to_dict(),
        "step_path": str(step_path),
        "stl_path": str(stl_path),
        "size": list(size),
    }


def create_build123d_box_envelope(
    size: Tuple[float, float, float],
    output_dir: str | Path,
    asset_id: str = "build123d-box",
    target_engine: Optional[str] = None,
) -> ConversionEnvelope:
    """Create a fixed B-rep asset and return a GUI/API-safe envelope."""
    result = create_build123d_box(size, output_dir)
    step_path = Path(result["step_path"])
    stl_path = Path(result["stl_path"])
    validation = {
        "step": {
            "valid": step_path.is_file() and step_path.stat().st_size > 0,
            "bytes": step_path.stat().st_size if step_path.is_file() else 0,
        },
        "stl": {
            "valid": stl_path.is_file() and stl_path.stat().st_size > 0,
            "bytes": stl_path.stat().st_size if stl_path.is_file() else 0,
        },
    }
    valid = all(item["valid"] for item in validation.values())
    return ConversionEnvelope(
        asset_id=asset_id,
        source_format="build123d-python",
        target_engine=target_engine,
        target_format="step+stl",
        media_type="application/step",
        output_path=str(step_path),
        loss_status=(
            ConversionLossStatus.REINTERPRETED if valid else ConversionLossStatus.FAILED
        ),
        loss_reasons=[
            "STL is a tessellated approximation; STEP preserves the B-rep result"
        ],
        errors=[] if valid else ["build123d output validation failed"],
        metadata={
            "size": list(size),
            "stl_path": str(stl_path),
            "output_validation": validation,
        },
        provenance={
            "tool": "build123d",
            "tool_version": result["capabilities"]["version"],
            "operation": "trusted_fixed_box",
        },
    )
