"""Independent output validation for LPG conversion adapters.

These checks intentionally do not call the native geometry loader. They verify
that an emitted file is structurally readable by an independent path before a
conversion is considered validated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List


class OutputValidationStatus(str, Enum):
    VALID = "valid"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


@dataclass
class OutputValidation:
    path: str
    format: str
    status: OutputValidationStatus
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return self.status == OutputValidationStatus.VALID

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["valid"] = self.valid
        return data


def _parse_obj_index(value: str, count: int, line_number: int, label: str, errors: List[str]) -> int:
    try:
        raw = int(value)
    except ValueError:
        errors.append(f"line {line_number}: invalid {label} index {value!r}")
        return -1

    if raw == 0:
        errors.append(f"line {line_number}: OBJ indices cannot be zero")
        return -1

    resolved = raw - 1 if raw > 0 else count + raw
    if resolved < 0 or resolved >= count:
        errors.append(f"line {line_number}: {label} index {raw} is out of range")
        return -1
    return resolved


def validate_obj_output(path: str | Path) -> OutputValidation:
    """Validate OBJ vertices, attributes, faces, and index ranges."""
    path = Path(path)
    result = OutputValidation(str(path), "obj", OutputValidationStatus.FAILED)
    if not path.is_file():
        result.errors.append("output file does not exist")
        return result

    vertices = 0
    uvs = 0
    normals = 0
    faces = 0
    triangles = 0

    try:
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split()
            directive = fields[0]

            if directive == "v":
                if len(fields) < 4:
                    result.errors.append(f"line {line_number}: vertex requires x/y/z")
                else:
                    vertices += 1
            elif directive == "vt":
                if len(fields) < 3:
                    result.errors.append(f"line {line_number}: UV requires u/v")
                else:
                    uvs += 1
            elif directive == "vn":
                if len(fields) < 4:
                    result.errors.append(f"line {line_number}: normal requires x/y/z")
                else:
                    normals += 1
            elif directive == "f":
                corners = fields[1:]
                if len(corners) < 3:
                    result.errors.append(f"line {line_number}: face requires at least three corners")
                    continue
                faces += 1
                triangles += len(corners) - 2
                for corner in corners:
                    values = corner.split("/")
                    if _parse_obj_index(values[0], vertices, line_number, "vertex", result.errors) < 0:
                        continue
                    if len(values) > 1 and values[1]:
                        _parse_obj_index(values[1], uvs, line_number, "UV", result.errors)
                    if len(values) > 2 and values[2]:
                        _parse_obj_index(values[2], normals, line_number, "normal", result.errors)
            else:
                result.warnings.append(f"line {line_number}: ignored directive {directive!r}")

        if vertices == 0:
            result.errors.append("OBJ contains no vertices")
        if faces == 0:
            result.errors.append("OBJ contains no faces")
        if not result.errors:
            result.status = OutputValidationStatus.VALID
        result.metadata.update(
            {
                "vertices": vertices,
                "uvs": uvs,
                "normals": normals,
                "faces": faces,
                "triangles": triangles,
            }
        )
    except (OSError, UnicodeError) as error:
        result.errors.append(f"failed to read OBJ: {error}")

    return result


def validate_image_output(path: str | Path) -> OutputValidation:
    """Validate an image using Pillow's independent decoder."""
    path = Path(path)
    result = OutputValidation(str(path), path.suffix.lower().lstrip("."), OutputValidationStatus.FAILED)
    if not path.is_file():
        result.errors.append("output file does not exist")
        return result

    try:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            result.metadata.update(
                {
                    "format": image.format,
                    "width": image.width,
                    "height": image.height,
                    "mode": image.mode,
                }
            )
        result.status = OutputValidationStatus.VALID
    except Exception as error:
        result.errors.append(f"image validation failed: {error}")

    return result


def validate_output(path: str | Path) -> OutputValidation:
    """Dispatch independent validation based on output extension."""
    path = Path(path)
    extension = path.suffix.lower().lstrip(".")
    if extension == "obj":
        return validate_obj_output(path)
    if extension in {"png", "jpg", "jpeg", "webp", "tif", "tiff", "bmp"}:
        return validate_image_output(path)
    return OutputValidation(
        str(path),
        extension,
        OutputValidationStatus.UNSUPPORTED,
        errors=[f"no independent validator for '.{extension}' output"],
    )
