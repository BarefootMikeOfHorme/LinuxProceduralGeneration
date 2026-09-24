"""Optional FreeCAD detection and capability metadata.

FreeCAD is an external application. LPG detects an existing installation but
never installs or starts it implicitly.
"""

from __future__ import annotations

import os
import platform
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class FreeCADCapabilities:
    backend: str
    available: bool
    executable: Optional[str]
    headless_executable: Optional[str]
    platform: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _candidates() -> list[Path]:
    values = []
    configured = os.getenv("FREECAD_PATH")
    if configured:
        values.append(Path(configured).expanduser())
    for command in ("FreeCADCmd", "freecadcmd", "FreeCAD", "freecad"):
        discovered = shutil.which(command)
        if discovered:
            values.append(Path(discovered))

    system = platform.system()
    if system == "Windows":
        for root in (os.getenv("ProgramFiles"), os.getenv("ProgramFiles(x86)")):
            if root:
                values.append(Path(root) / "FreeCAD" / "bin" / "FreeCADCmd.exe")
                values.append(Path(root) / "FreeCAD" / "bin" / "FreeCAD.exe")
    elif system == "Darwin":
        values.extend(
            [
                Path("/Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd"),
                Path("/Applications/FreeCAD.app/Contents/MacOS/FreeCAD"),
            ]
        )
    else:
        values.extend(
            [
                Path("/usr/bin/freecadcmd"),
                Path("/usr/bin/freecad"),
                Path("/usr/local/bin/freecadcmd"),
                Path("/usr/local/bin/freecad"),
            ]
        )
    return values


def get_freecad_capabilities() -> FreeCADCapabilities:
    """Detect FreeCAD without launching it or changing the system."""
    candidates = _candidates()
    headless = next(
        (path for path in candidates if path.name.lower() in {"freecadcmd", "freecadcmd.exe"} and path.is_file()),
        None,
    )
    gui = next(
        (path for path in candidates if path.name.lower() in {"freecad", "freecad.exe"} and path.is_file()),
        None,
    )
    available = headless is not None or gui is not None
    return FreeCADCapabilities(
        backend="freecad",
        available=available,
        executable=str(gui) if gui is not None else None,
        headless_executable=str(headless) if headless is not None else None,
        platform=platform.system(),
        error=None if available else "FreeCAD executable not found",
    )
