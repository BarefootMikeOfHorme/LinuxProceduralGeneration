"""
VaultMind Forge - Unified Format Converter
===========================================

Converts all input formats into standardized VAF (VaultMind Asset Format) representations.
Handles: GLB, GLTF, FBX, OBJ, BLEND, USD, DAE, archives, and more.

Architecture:
    Input Format → Parser → Intermediate Representation → VAF-Full → VAF Derivatives
                                                              ↓
                                                    ┌─────────┼─────────┐
                                                    ↓         ↓         ↓
                                              VAF-Catalog VAF-Binary VAF-Stream
"""

import json
import struct
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from .format_registry import FormatRegistry, FormatSpec, FormatFamily


class ConversionStatus(Enum):
    """Status of conversion operation"""
    SUCCESS = "success"
    PARTIAL = "partial"  # Some data extracted, but not complete
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


@dataclass
class ConversionResult:
    """Result of a format conversion"""
    status: ConversionStatus
    vaf_full: Optional[Dict] = None
    vaf_catalog: Optional[Dict] = None
    warnings: List[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


class IntermediateRepresentation:
    """
    Intermediate representation that all parsers convert to.
    This is the universal pivot format before creating VAF.
    """

    def __init__(self):
        # Asset identity
        self.name: str = ""
        self.source_format: str = ""
        self.source_file: str = ""

        # Geometry data
        self.meshes: List[Dict] = []
        self.total_vertices: int = 0
        self.total_triangles: int = 0

        # Materials and textures
        self.materials: List[Dict] = []
        self.textures: List[Dict] = []

        # Rigging and animation
        self.skeleton: Optional[Dict] = None
        self.animations: List[Dict] = []

        # Metadata
        self.has_normals: bool = False
        self.has_uvs: bool = False
        self.has_vertex_colors: bool = False
        self.has_rigging: bool = False
        self.has_animations: bool = False

        # Scene data
        self.scene_nodes: List[Dict] = []
        self.cameras: List[Dict] = []
        self.lights: List[Dict] = []

    def to_vaf_full(self, asset_id: str) -> Dict:
        """Convert intermediate representation to VAF-Full format"""

        # Classify polycount
        polycount_category = self._classify_polycount(self.total_triangles)

        # Determine quality estimate
        quality = self._estimate_quality()

        vaf = {
            "vaf_version": "1.0.0",

            "asset": {
                "id": asset_id,
                "name": self.name,
                "type": "model_3d" if self.meshes else "unknown",
                "category": "uncategorized",  # Will be inferred later
                "tags": [],
            },

            "geometry": {
                "meshes": self.meshes,
                "statistics": {
                    "total_vertices": self.total_vertices,
                    "total_triangles": self.total_triangles,
                    "polycount_category": polycount_category,
                    "has_normals": self.has_normals,
                    "has_uvs": self.has_uvs,
                    "has_vertex_colors": self.has_vertex_colors,
                }
            },

            "materials": {
                "definitions": self.materials,
                "textures": self.textures,
            },

            "rigging": {
                "skeleton": self.skeleton,
            } if self.skeleton else {},

            "animations": self.animations,

            "metadata": {
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "stage": "extracted",
                "quality": quality,
                "source": {
                    "format": self.source_format,
                    "filename": self.source_file,
                }
            },

            "lineage": {
                "origin_hash": asset_id,
                "transformations": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "operation": "conversion",
                        "tool": "unified_converter",
                        "from_format": self.source_format,
                        "to_format": "vaf_full",
                    }
                ],
                "parent_assets": [],
            }
        }

        return vaf

    def _classify_polycount(self, triangles: int) -> str:
        """Classify polygon count"""
        if triangles < 1000:
            return "very-low"
        elif triangles < 10000:
            return "low"
        elif triangles < 50000:
            return "medium"
        elif triangles < 200000:
            return "high"
        elif triangles < 1000000:
            return "very-high"
        else:
            return "extreme"

    def _estimate_quality(self) -> str:
        """Estimate asset quality based on available data"""
        score = 0

        if self.has_normals:
            score += 1
        if self.has_uvs:
            score += 1
        if self.textures:
            score += 2
        if self.materials:
            score += 1
        if self.has_rigging:
            score += 2
        if self.animations:
            score += 1

        if score >= 7:
            return "ultra"
        elif score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        elif score >= 1:
            return "low"
        else:
            return "unknown"


class UnifiedConverter:
    """
    Main converter that routes files to appropriate parsers based on format.
    """

    def __init__(self):
        self.registry = FormatRegistry()

    def convert(self, filepath: Path, asset_id: str) -> ConversionResult:
        """
        Convert any supported format to VAF.

        Args:
            filepath: Path to source file
            asset_id: SHA256 hash identifier

        Returns:
            ConversionResult with VAF data
        """
        ext = filepath.suffix.lower()
        spec = self.registry.get_spec(ext)

        if not spec:
            return ConversionResult(
                status=ConversionStatus.UNSUPPORTED,
                errors=[f"Unsupported format: {ext}"]
            )

        # Route to appropriate parser based on format family
        try:
            if spec.family == FormatFamily.GEOMETRY:
                ir = self._parse_geometry(filepath, spec)
            elif spec.family == FormatFamily.SCENE:
                ir = self._parse_scene(filepath, spec)
            elif spec.family == FormatFamily.TEXTURE:
                ir = self._parse_texture(filepath, spec)
            elif spec.family == FormatFamily.MATERIAL:
                ir = self._parse_material(filepath, spec)
            else:
                return ConversionResult(
                    status=ConversionStatus.UNSUPPORTED,
                    errors=[f"No parser for format family: {spec.family}"]
                )

            # Convert IR to VAF-Full
            vaf_full = ir.to_vaf_full(asset_id)

            # Generate VAF-Catalog
            vaf_catalog = self._generate_catalog(vaf_full, filepath)

            return ConversionResult(
                status=ConversionStatus.SUCCESS,
                vaf_full=vaf_full,
                vaf_catalog=vaf_catalog,
            )

        except Exception as e:
            return ConversionResult(
                status=ConversionStatus.FAILED,
                errors=[f"Conversion failed: {str(e)}"]
            )

    def _parse_geometry(self, filepath: Path, spec: FormatSpec) -> IntermediateRepresentation:
        """Parse geometry formats (OBJ, FBX, GLTF, etc.)"""
        ir = IntermediateRepresentation()
        ir.name = filepath.stem
        ir.source_format = spec.extension
        ir.source_file = filepath.name

        # Route to format-specific parser
        if spec.extension == ".obj":
            self._parse_obj(filepath, ir)
        elif spec.extension in [".gltf", ".glb"]:
            self._parse_gltf(filepath, ir)
        elif spec.extension == ".fbx":
            self._parse_fbx(filepath, ir)
        elif spec.extension == ".dae":
            self._parse_collada(filepath, ir)
        elif spec.extension in [".usd", ".usda", ".usdc", ".usdz"]:
            self._parse_usd(filepath, ir)
        elif spec.extension == ".stl":
            self._parse_stl(filepath, ir)
        elif spec.extension == ".ply":
            self._parse_ply(filepath, ir)
        else:
            # Placeholder for unsupported geometry formats
            self._parse_generic_geometry(filepath, ir)

        return ir

    def _parse_scene(self, filepath: Path, spec: FormatSpec) -> IntermediateRepresentation:
        """Parse scene formats (BLEND, C4D, MA, etc.)"""
        ir = IntermediateRepresentation()
        ir.name = filepath.stem
        ir.source_format = spec.extension
        ir.source_file = filepath.name

        # Most scene formats require external tools
        # For now, extract basic metadata
        self._parse_generic_scene(filepath, ir)

        return ir

    def _parse_texture(self, filepath: Path, spec: FormatSpec) -> IntermediateRepresentation:
        """Parse texture/image formats"""
        ir = IntermediateRepresentation()
        ir.name = filepath.stem
        ir.source_format = spec.extension
        ir.source_file = filepath.name

        # Add texture metadata
        try:
            from PIL import Image
            with Image.open(filepath) as img:
                texture = {
                    "id": filepath.stem,
                    "name": filepath.name,
                    "path": str(filepath),
                    "format": spec.extension,
                    "resolution": {
                        "width": img.width,
                        "height": img.height,
                    },
                    "color_space": "srgb",  # Default assumption
                }
                ir.textures.append(texture)
        except Exception as e:
            # PIL not available or image couldn't be opened
            pass

        return ir

    def _parse_material(self, filepath: Path, spec: FormatSpec) -> IntermediateRepresentation:
        """Parse material definition formats"""
        ir = IntermediateRepresentation()
        ir.name = filepath.stem
        ir.source_format = spec.extension
        ir.source_file = filepath.name

        if spec.extension == ".mtl":
            self._parse_mtl(filepath, ir)

        return ir

    # =========================================================================
    # Format-Specific Parsers
    # =========================================================================

    def _parse_obj(self, filepath: Path, ir: IntermediateRepresentation):
        """Parse Wavefront OBJ file (basic implementation)"""
        vertices = []
        normals = []
        uvs = []
        faces = []

        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split()
                    if not parts:
                        continue

                    if parts[0] == 'v':  # Vertex
                        vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    elif parts[0] == 'vn':  # Normal
                        normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    elif parts[0] == 'vt':  # UV
                        uvs.append([float(parts[1]), float(parts[2])])
                    elif parts[0] == 'f':  # Face
                        faces.append(parts[1:])

            # Build mesh
            mesh = {
                "name": filepath.stem,
                "vertices": {
                    "count": len(vertices),
                    "positions": vertices,  # In real implementation, reference binary buffer
                    "normals": normals if normals else None,
                    "uvs": [uvs] if uvs else [],
                },
                "indices": {
                    "count": len(faces) * 3,  # Simplified
                    "data": faces,
                }
            }

            ir.meshes.append(mesh)
            ir.total_vertices = len(vertices)
            ir.total_triangles = len(faces)
            ir.has_normals = bool(normals)
            ir.has_uvs = bool(uvs)

        except Exception as e:
            print(f"[WARN] OBJ parsing error: {e}")

    def _parse_gltf(self, filepath: Path, ir: IntermediateRepresentation):
        """Parse glTF/GLB format (basic implementation)"""
        try:
            # For .gltf (JSON)
            if filepath.suffix == ".gltf":
                with open(filepath, 'r') as f:
                    gltf_data = json.load(f)

                # Extract basic info
                if "meshes" in gltf_data:
                    for mesh_data in gltf_data["meshes"]:
                        mesh = {
                            "name": mesh_data.get("name", "mesh"),
                            "vertices": {"count": 0},  # Would need to parse accessors
                        }
                        ir.meshes.append(mesh)

                ir.has_normals = True  # glTF typically has normals
                ir.has_uvs = True

            # For .glb (binary), would need proper binary parsing
            else:
                ir.has_normals = True
                ir.has_uvs = True

        except Exception as e:
            print(f"[WARN] glTF parsing error: {e}")

    def _parse_fbx(self, filepath: Path, ir: IntermediateRepresentation):
        """Parse FBX format (requires external library)"""
        # FBX is binary/proprietary - would need fbx library or Blender
        # For now, just mark as present
        ir.has_normals = True
        ir.has_uvs = True
        print(f"[INFO] FBX parsing requires external tool (Blender/FBX SDK)")

    def _parse_collada(self, filepath: Path, ir: IntermediateRepresentation):
        """Parse COLLADA (.dae) format"""
        # XML-based, would parse with xml.etree.ElementTree
        ir.has_normals = True
        ir.has_uvs = True
        print(f"[INFO] COLLADA parsing not yet implemented")

    def _parse_usd(self, filepath: Path, ir: IntermediateRepresentation):
        """Parse USD formats"""
        # Would require USD library
        ir.has_normals = True
        ir.has_uvs = True
        print(f"[INFO] USD parsing requires Pixar USD library")

    def _parse_stl(self, filepath: Path, ir: IntermediateRepresentation):
        """Parse STL format (basic implementation)"""
        # STL is simple triangle format
        ir.has_normals = True  # STL has per-face normals
        ir.has_uvs = False  # STL doesn't support UVs
        print(f"[INFO] STL parsing not yet fully implemented")

    def _parse_ply(self, filepath: Path, ir: IntermediateRepresentation):
        """Parse PLY format"""
        ir.has_normals = False
        ir.has_uvs = False
        ir.has_vertex_colors = True  # PLY often has vertex colors
        print(f"[INFO] PLY parsing not yet fully implemented")

    def _parse_mtl(self, filepath: Path, ir: IntermediateRepresentation):
        """Parse OBJ material file"""
        try:
            with open(filepath, 'r') as f:
                current_material = None

                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split()
                    if not parts:
                        continue

                    if parts[0] == 'newmtl':
                        if current_material:
                            ir.materials.append(current_material)
                        current_material = {
                            "name": parts[1],
                            "shader_model": "phong",
                            "parameters": {},
                            "textures": {},
                        }
                    elif current_material and parts[0] == 'map_Kd':
                        current_material["textures"]["base_color"] = {"path": parts[1]}

                if current_material:
                    ir.materials.append(current_material)

        except Exception as e:
            print(f"[WARN] MTL parsing error: {e}")

    def _parse_generic_geometry(self, filepath: Path, ir: IntermediateRepresentation):
        """Fallback for unknown geometry formats"""
        print(f"[INFO] Generic geometry parser for {filepath.suffix}")

    def _parse_generic_scene(self, filepath: Path, ir: IntermediateRepresentation):
        """Fallback for unknown scene formats"""
        print(f"[INFO] Generic scene parser for {filepath.suffix}")

    def _generate_catalog(self, vaf_full: Dict, filepath: Path) -> Dict:
        """Generate VAF-Catalog from VAF-Full"""
        asset = vaf_full["asset"]
        geometry = vaf_full.get("geometry", {})
        materials = vaf_full.get("materials", {})
        metadata = vaf_full.get("metadata", {})

        stats = geometry.get("statistics", {})

        catalog = {
            "vaf_type": "catalog",
            "vaf_version": "1.0.0",
            "asset_id": asset["id"],
            "name": asset["name"],
            "type": asset["type"],
            "category": asset["category"],
            "tags": asset.get("tags", []),
            "created": metadata.get("created"),
            "modified": metadata.get("modified"),
            "stage": metadata.get("stage", "extracted"),
            "quality": metadata.get("quality", "unknown"),

            "statistics": {
                "vertices": stats.get("total_vertices", 0),
                "triangles": stats.get("total_triangles", 0),
                "materials": len(materials.get("definitions", [])),
                "textures": len(materials.get("textures", [])),
                "animations": len(vaf_full.get("animations", [])),
            },

            "polycount_category": stats.get("polycount_category", "unknown"),

            "capabilities": {
                "has_geometry": bool(geometry.get("meshes")),
                "has_materials": bool(materials.get("definitions")),
                "has_textures": bool(materials.get("textures")),
                "has_rigging": bool(vaf_full.get("rigging")),
                "has_animations": bool(vaf_full.get("animations")),
                "has_lod": False,
            },

            "formats": {
                "source": {
                    "format": metadata.get("source", {}).get("format"),
                    "filename": filepath.name,
                    "size_bytes": filepath.stat().st_size,
                },
                "vaf_full": {
                    "available": True,
                    "path": None,  # Will be set when saved
                },
            },

            "lineage": vaf_full.get("lineage", {}),
        }

        return catalog


# =============================================================================
# Convenience Functions
# =============================================================================

def convert_file(filepath: Path, asset_id: str) -> ConversionResult:
    """
    Convenience function to convert a single file.

    Args:
        filepath: Path to file
        asset_id: Asset identifier (SHA256 hash)

    Returns:
        ConversionResult
    """
    converter = UnifiedConverter()
    return converter.convert(filepath, asset_id)


def batch_convert(filepaths: List[Path], asset_ids: List[str]) -> List[ConversionResult]:
    """
    Convert multiple files in batch.

    Args:
        filepaths: List of file paths
        asset_ids: Corresponding asset IDs

    Returns:
        List of ConversionResults
    """
    converter = UnifiedConverter()
    results = []

    for filepath, asset_id in zip(filepaths, asset_ids):
        result = converter.convert(filepath, asset_id)
        results.append(result)

    return results
