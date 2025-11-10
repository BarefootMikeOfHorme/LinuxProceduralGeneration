"""
VaultMind Forge - Format Conversion Registry
============================================

Central registry mapping all supported input formats to VAF (VaultMind Asset Format).
Defines how each format is parsed, what data is extracted, and how it's unified.
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


class FormatFamily(Enum):
    """High-level format families"""
    GEOMETRY = "geometry"           # 3D models
    TEXTURE = "texture"             # Images/textures
    MATERIAL = "material"           # Material definitions
    SCENE = "scene"                 # Complete scenes
    ANIMATION = "animation"         # Animation data
    ARCHIVE = "archive"             # Compressed archives
    COMPOSITE = "composite"         # Multi-asset packages


@dataclass
class FormatSpec:
    """Specification for a file format"""
    extension: str
    family: FormatFamily
    description: str

    # Capabilities
    supports_geometry: bool = False
    supports_materials: bool = False
    supports_textures: bool = False
    supports_rigging: bool = False
    supports_animations: bool = False
    supports_scenes: bool = False

    # Format characteristics
    is_binary: bool = True
    is_proprietary: bool = False
    is_archive: bool = False

    # Extraction method
    parser: Optional[str] = None  # Name of parser to use
    converter_tool: Optional[str] = None  # External tool if needed

    # Target engines
    native_engines: List[str] = None

    # Priority for format selection (higher = preferred)
    priority: int = 50


# Complete format registry
FORMAT_REGISTRY: Dict[str, FormatSpec] = {
    # === GEOMETRY FORMATS ===

    # glTF/GLB - Modern standard, highest priority
    ".gltf": FormatSpec(
        extension=".gltf",
        family=FormatFamily.GEOMETRY,
        description="glTF 2.0 JSON - Modern interchange format",
        supports_geometry=True,
        supports_materials=True,
        supports_textures=True,
        supports_rigging=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=False,
        parser="gltf_parser",
        native_engines=["unity", "unreal", "godot", "blender"],
        priority=100  # Highest - this is our preferred intermediate
    ),

    ".glb": FormatSpec(
        extension=".glb",
        family=FormatFamily.GEOMETRY,
        description="glTF 2.0 Binary - Self-contained binary glTF",
        supports_geometry=True,
        supports_materials=True,
        supports_textures=True,
        supports_rigging=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=True,
        parser="gltf_parser",
        native_engines=["unity", "unreal", "godot", "blender"],
        priority=95
    ),

    # FBX - Industry standard
    ".fbx": FormatSpec(
        extension=".fbx",
        family=FormatFamily.GEOMETRY,
        description="Autodesk FBX - Industry standard interchange",
        supports_geometry=True,
        supports_materials=True,
        supports_textures=True,
        supports_rigging=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=True,
        is_proprietary=True,
        parser="fbx_parser",
        converter_tool="blender",  # Use Blender to convert
        native_engines=["unity", "unreal", "blender"],
        priority=90
    ),

    # OBJ - Simple, widely supported
    ".obj": FormatSpec(
        extension=".obj",
        family=FormatFamily.GEOMETRY,
        description="Wavefront OBJ - Simple mesh format",
        supports_geometry=True,
        supports_materials=True,
        is_binary=False,
        parser="obj_parser",
        native_engines=["unity", "unreal", "godot", "blender"],
        priority=70
    ),

    # COLLADA
    ".dae": FormatSpec(
        extension=".dae",
        family=FormatFamily.GEOMETRY,
        description="COLLADA - XML-based interchange",
        supports_geometry=True,
        supports_materials=True,
        supports_textures=True,
        supports_rigging=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=False,
        parser="collada_parser",
        native_engines=["unity", "godot", "blender"],
        priority=75
    ),

    # USD formats - High-end production
    ".usd": FormatSpec(
        extension=".usd",
        family=FormatFamily.GEOMETRY,
        description="Universal Scene Description - Production format",
        supports_geometry=True,
        supports_materials=True,
        supports_textures=True,
        supports_rigging=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=False,
        parser="usd_parser",
        native_engines=["blender", "unreal"],
        priority=85
    ),

    ".usda": FormatSpec(
        extension=".usda",
        family=FormatFamily.GEOMETRY,
        description="USD ASCII - Human-readable USD",
        supports_geometry=True,
        supports_materials=True,
        supports_textures=True,
        supports_rigging=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=False,
        parser="usd_parser",
        native_engines=["blender", "unreal"],
        priority=80
    ),

    ".usdc": FormatSpec(
        extension=".usdc",
        family=FormatFamily.GEOMETRY,
        description="USD Crate - Binary USD",
        supports_geometry=True,
        supports_materials=True,
        supports_textures=True,
        supports_rigging=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=True,
        parser="usd_parser",
        native_engines=["blender", "unreal"],
        priority=80
    ),

    ".usdz": FormatSpec(
        extension=".usdz",
        family=FormatFamily.GEOMETRY,
        description="USD Zip - Packaged USD",
        supports_geometry=True,
        supports_materials=True,
        supports_textures=True,
        supports_rigging=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=True,
        is_archive=True,
        parser="usd_parser",
        native_engines=["blender", "unreal"],
        priority=85
    ),

    # Blender native
    ".blend": FormatSpec(
        extension=".blend",
        family=FormatFamily.SCENE,
        description="Blender native format",
        supports_geometry=True,
        supports_materials=True,
        supports_textures=True,
        supports_rigging=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=True,
        is_proprietary=True,
        parser="blend_parser",
        converter_tool="blender",
        native_engines=["blender"],
        priority=60
    ),

    # DCC-specific formats
    ".c4d": FormatSpec(
        extension=".c4d",
        family=FormatFamily.SCENE,
        description="Cinema 4D native",
        supports_geometry=True,
        supports_materials=True,
        supports_rigging=True,
        supports_animations=True,
        is_binary=True,
        is_proprietary=True,
        converter_tool="blender",
        priority=50
    ),

    ".ma": FormatSpec(
        extension=".ma",
        family=FormatFamily.SCENE,
        description="Maya ASCII",
        supports_geometry=True,
        supports_materials=True,
        supports_rigging=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=False,
        is_proprietary=True,
        converter_tool="blender",
        priority=55
    ),

    ".mb": FormatSpec(
        extension=".mb",
        family=FormatFamily.SCENE,
        description="Maya Binary",
        supports_geometry=True,
        supports_materials=True,
        supports_rigging=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=True,
        is_proprietary=True,
        converter_tool="blender",
        priority=55
    ),

    ".max": FormatSpec(
        extension=".max",
        family=FormatFamily.SCENE,
        description="3ds Max native",
        supports_geometry=True,
        supports_materials=True,
        supports_rigging=True,
        supports_animations=True,
        is_binary=True,
        is_proprietary=True,
        converter_tool="blender",
        priority=50
    ),

    ".3ds": FormatSpec(
        extension=".3ds",
        family=FormatFamily.GEOMETRY,
        description="3D Studio legacy format",
        supports_geometry=True,
        supports_materials=True,
        is_binary=True,
        parser="3ds_parser",
        priority=40
    ),

    # Point cloud / scanning formats
    ".ply": FormatSpec(
        extension=".ply",
        family=FormatFamily.GEOMETRY,
        description="Polygon File Format - Point clouds",
        supports_geometry=True,
        is_binary=True,
        parser="ply_parser",
        priority=60
    ),

    ".stl": FormatSpec(
        extension=".stl",
        family=FormatFamily.GEOMETRY,
        description="Stereolithography - 3D printing",
        supports_geometry=True,
        is_binary=True,
        parser="stl_parser",
        priority=50
    ),

    ".x3d": FormatSpec(
        extension=".x3d",
        family=FormatFamily.SCENE,
        description="X3D - Web3D standard",
        supports_geometry=True,
        supports_materials=True,
        supports_animations=True,
        supports_scenes=True,
        is_binary=False,
        parser="x3d_parser",
        priority=55
    ),

    # === MATERIAL FORMATS ===

    ".mtl": FormatSpec(
        extension=".mtl",
        family=FormatFamily.MATERIAL,
        description="OBJ Material Library",
        supports_materials=True,
        supports_textures=True,
        is_binary=False,
        parser="mtl_parser",
        priority=60
    ),

    ".mat": FormatSpec(
        extension=".mat",
        family=FormatFamily.MATERIAL,
        description="Material definition file",
        supports_materials=True,
        is_binary=False,
        parser="mat_parser",
        priority=50
    ),

    # === TEXTURE FORMATS ===

    ".png": FormatSpec(
        extension=".png",
        family=FormatFamily.TEXTURE,
        description="PNG - Lossless compression",
        supports_textures=True,
        is_binary=True,
        parser="image_parser",
        priority=90
    ),

    ".jpg": FormatSpec(
        extension=".jpg",
        family=FormatFamily.TEXTURE,
        description="JPEG - Lossy compression",
        supports_textures=True,
        is_binary=True,
        parser="image_parser",
        priority=70
    ),

    ".jpeg": FormatSpec(
        extension=".jpeg",
        family=FormatFamily.TEXTURE,
        description="JPEG - Lossy compression",
        supports_textures=True,
        is_binary=True,
        parser="image_parser",
        priority=70
    ),

    ".tga": FormatSpec(
        extension=".tga",
        family=FormatFamily.TEXTURE,
        description="Targa - Uncompressed or RLE",
        supports_textures=True,
        is_binary=True,
        parser="image_parser",
        priority=75
    ),

    ".bmp": FormatSpec(
        extension=".bmp",
        family=FormatFamily.TEXTURE,
        description="Bitmap - Uncompressed",
        supports_textures=True,
        is_binary=True,
        parser="image_parser",
        priority=50
    ),

    ".tiff": FormatSpec(
        extension=".tiff",
        family=FormatFamily.TEXTURE,
        description="TIFF - Flexible format",
        supports_textures=True,
        is_binary=True,
        parser="image_parser",
        priority=80
    ),

    ".exr": FormatSpec(
        extension=".exr",
        family=FormatFamily.TEXTURE,
        description="OpenEXR - HDR format",
        supports_textures=True,
        is_binary=True,
        parser="image_parser",
        priority=95
    ),

    ".hdr": FormatSpec(
        extension=".hdr",
        family=FormatFamily.TEXTURE,
        description="Radiance HDR",
        supports_textures=True,
        is_binary=True,
        parser="image_parser",
        priority=85
    ),

    ".dds": FormatSpec(
        extension=".dds",
        family=FormatFamily.TEXTURE,
        description="DirectDraw Surface - Compressed textures",
        supports_textures=True,
        is_binary=True,
        parser="image_parser",
        priority=70
    ),

    ".psd": FormatSpec(
        extension=".psd",
        family=FormatFamily.TEXTURE,
        description="Photoshop Document",
        supports_textures=True,
        is_binary=True,
        parser="image_parser",
        priority=60
    ),

    # === ARCHIVE FORMATS ===

    ".zip": FormatSpec(
        extension=".zip",
        family=FormatFamily.ARCHIVE,
        description="ZIP archive",
        is_binary=True,
        is_archive=True,
        parser="archive_parser",
        priority=80
    ),

    ".rar": FormatSpec(
        extension=".rar",
        family=FormatFamily.ARCHIVE,
        description="RAR archive",
        is_binary=True,
        is_archive=True,
        parser="archive_parser",
        priority=75
    ),

    ".7z": FormatSpec(
        extension=".7z",
        family=FormatFamily.ARCHIVE,
        description="7-Zip archive",
        is_binary=True,
        is_archive=True,
        parser="archive_parser",
        priority=80
    ),

    ".tar": FormatSpec(
        extension=".tar",
        family=FormatFamily.ARCHIVE,
        description="TAR archive",
        is_binary=True,
        is_archive=True,
        parser="archive_parser",
        priority=70
    ),

    ".gz": FormatSpec(
        extension=".gz",
        family=FormatFamily.ARCHIVE,
        description="GZip compressed",
        is_binary=True,
        is_archive=True,
        parser="archive_parser",
        priority=70
    ),

    # === ENGINE PACKAGES ===

    ".unitypackage": FormatSpec(
        extension=".unitypackage",
        family=FormatFamily.COMPOSITE,
        description="Unity asset package",
        supports_geometry=True,
        supports_materials=True,
        supports_textures=True,
        is_binary=True,
        is_archive=True,
        parser="unity_package_parser",
        native_engines=["unity"],
        priority=85
    ),
}


class FormatRegistry:
    """Central registry for format handling"""

    @staticmethod
    def get_spec(extension: str) -> Optional[FormatSpec]:
        """Get format specification"""
        return FORMAT_REGISTRY.get(extension.lower())

    @staticmethod
    def is_supported(extension: str) -> bool:
        """Check if format is supported"""
        return extension.lower() in FORMAT_REGISTRY

    @staticmethod
    def get_by_family(family: FormatFamily) -> List[FormatSpec]:
        """Get all formats in a family"""
        return [
            spec for spec in FORMAT_REGISTRY.values()
            if spec.family == family
        ]

    @staticmethod
    def get_geometry_formats() -> Set[str]:
        """Get all geometry format extensions"""
        return {
            ext for ext, spec in FORMAT_REGISTRY.items()
            if spec.supports_geometry
        }

    @staticmethod
    def get_texture_formats() -> Set[str]:
        """Get all texture format extensions"""
        return {
            ext for ext, spec in FORMAT_REGISTRY.items()
            if spec.supports_textures or spec.family == FormatFamily.TEXTURE
        }

    @staticmethod
    def get_archive_formats() -> Set[str]:
        """Get all archive format extensions"""
        return {
            ext for ext, spec in FORMAT_REGISTRY.items()
            if spec.is_archive
        }

    @staticmethod
    def select_best_format(available: List[str], purpose: str = "geometry") -> Optional[str]:
        """
        Select the best format from available options.
        Returns the format with highest priority for the given purpose.
        """
        if not available:
            return None

        # Filter to supported formats
        supported = [ext for ext in available if ext.lower() in FORMAT_REGISTRY]
        if not supported:
            return None

        # Sort by priority (descending)
        sorted_formats = sorted(
            supported,
            key=lambda ext: FORMAT_REGISTRY[ext.lower()].priority,
            reverse=True
        )

        return sorted_formats[0]

    @staticmethod
    def get_conversion_path(from_format: str, to_format: str = ".gltf") -> List[str]:
        """
        Determine the conversion path from one format to another.
        Returns list of intermediate formats/tools needed.
        """
        from_spec = FORMAT_REGISTRY.get(from_format.lower())
        to_spec = FORMAT_REGISTRY.get(to_format.lower())

        if not from_spec or not to_spec:
            return []

        # Direct conversion possible?
        if from_spec.parser and to_format == ".gltf":
            return [from_spec.parser, "gltf_export"]

        # Need converter tool?
        if from_spec.converter_tool:
            return [from_spec.converter_tool, "gltf_export"]

        return []


def print_registry_summary():
    """Print summary of registered formats"""
    print("VaultMind Asset Format Registry")
    print("=" * 60)

    for family in FormatFamily:
        formats = FormatRegistry.get_by_family(family)
        print(f"\n{family.value.upper()} ({len(formats)} formats)")
        print("-" * 60)

        for spec in sorted(formats, key=lambda s: s.priority, reverse=True):
            caps = []
            if spec.supports_geometry: caps.append("geo")
            if spec.supports_materials: caps.append("mat")
            if spec.supports_textures: caps.append("tex")
            if spec.supports_rigging: caps.append("rig")
            if spec.supports_animations: caps.append("anim")

            print(f"  {spec.extension:15} [{spec.priority:3}] {', '.join(caps):20} - {spec.description}")


if __name__ == "__main__":
    print_registry_summary()
