"""CAD capability/profile metadata for setup clients and the future wizard."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CadProfile:
    profile_id: str
    display_name: str
    backend: str
    install_kind: str
    default: bool
    description: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


CAD_PROFILES: Dict[str, CadProfile] = {
    "build123d": CadProfile(
        profile_id="build123d",
        display_name="build123d",
        backend="build123d",
        install_kind="python_dependency",
        default=True,
        description="Default Python B-rep CAD-as-code runtime using OCP/OpenCascade.",
    ),
    "freecad": CadProfile(
        profile_id="freecad",
        display_name="FreeCAD",
        backend="freecad",
        install_kind="external_application",
        default=False,
        description="Optional GUI and FreeCADCmd worker for documents, assemblies, STEP, IGES, and FCStd.",
    ),
    "openscad": CadProfile(
        profile_id="openscad",
        display_name="OpenSCAD",
        backend="openscad",
        install_kind="external_application",
        default=False,
        description="Optional procedural CSG worker for .scad, STL, 3MF, and related outputs.",
    ),
    "blender": CadProfile(
        profile_id="blender",
        display_name="Blender",
        backend="blender",
        install_kind="external_application",
        default=False,
        description="Optional scene, rendering, animation, and visual asset worker.",
    ),
}


def get_cad_profiles() -> List[CadProfile]:
    return list(CAD_PROFILES.values())


def get_default_cad_profile() -> CadProfile:
    return next(profile for profile in CAD_PROFILES.values() if profile.default)
