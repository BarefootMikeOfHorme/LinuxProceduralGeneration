"""Environment and capability diagnostics for LPG setup/troubleshooting."""

from __future__ import annotations

import importlib.util
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Dict

from .build123d_adapter import get_build123d_capabilities
from .freecad_adapter import get_freecad_capabilities


def _command(name: str) -> Dict[str, Any]:
    path = shutil.which(name)
    return {"available": path is not None, "path": path}


def collect_doctor_report() -> Dict[str, Any]:
    """Collect non-mutating environment and optional-backend diagnostics."""
    try:
        from .cad_profiles import get_cad_profiles

        cad_profiles = [profile.to_dict() for profile in get_cad_profiles()]
    except Exception as error:
        cad_profiles = [{"error": str(error)}]

    return {
        "schema_version": "1.0",
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "lpg": {
            "package_path": str(Path(__file__).resolve().parents[2]),
        },
        "build123d": get_build123d_capabilities().to_dict(),
        "freecad": get_freecad_capabilities().to_dict(),
        "optional_commands": {
            "cargo": _command("cargo"),
            "openscad": _command("openscad"),
            "blender": _command("blender"),
            "ffmpeg": _command("ffmpeg"),
            "docker": _command("docker"),
        },
        "native_extension": {
            "available": importlib.util.find_spec("vaultmind_forge_core") is not None,
        },
        "cad_profiles": cad_profiles,
    }
