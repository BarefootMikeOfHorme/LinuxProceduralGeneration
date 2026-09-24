"""Canonical loss-aware asset conversion contracts.

The converter stacks in LPG are being consolidated around this contract. A
conversion must state what was preserved, approximated, dropped, or left
unverified; callers must not infer success from the mere presence of an output
file.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ConversionLossStatus(str, Enum):
    """Required outcome classification for a conversion."""

    EXACT = "exact"
    REINTERPRETED = "reinterpreted"
    APPROXIMATED = "approximated"
    LOSSY = "lossy"
    DROPPED = "dropped"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
    UNCHECKED = "unchecked"


class ConversionUnsupportedError(RuntimeError):
    """Raised when a requested conversion has no validated implementation."""


@dataclass
class ConversionEnvelope:
    """Provider-neutral result envelope for an asset conversion.

    ``loss_status`` is deliberately explicit. ``UNCHECKED`` is valid for a
    legacy or externally verified operation, but it is not equivalent to
    ``EXACT``.
    """

    schema_version: str = "1.0"
    asset_id: str = ""
    source_path: str = ""
    source_format: str = ""
    target_engine: Optional[str] = None
    target_format: Optional[str] = None
    media_type: str = "application/octet-stream"
    output_path: Optional[str] = None
    loss_status: ConversionLossStatus = ConversionLossStatus.UNCHECKED
    loss_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversionEnvelope":
        """Restore an envelope from its JSON-compatible dictionary form."""
        values = dict(data)
        values["loss_status"] = ConversionLossStatus(
            values.get("loss_status", ConversionLossStatus.UNCHECKED.value)
        )
        allowed = {
            "schema_version",
            "asset_id",
            "source_path",
            "source_format",
            "target_engine",
            "target_format",
            "media_type",
            "output_path",
            "loss_status",
            "loss_reasons",
            "warnings",
            "errors",
            "metadata",
            "provenance",
        }
        return cls(**{key: value for key, value in values.items() if key in allowed})

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-compatible representation of the envelope."""

        def normalize(value: Any) -> Any:
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, dict):
                return {key: normalize(item) for key, item in value.items()}
            if isinstance(value, list):
                return [normalize(item) for item in value]
            return value

        return normalize(asdict(self))
