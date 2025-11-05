"""
VaultMind Forge - USD (Universal Scene Description) Handler
Pixar USD export with stage layering, variants, and LIVRPS composition
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass
import logging

from .format_registry import (
    ModelFormatHandler,
    ModelMetadata,
    ConversionOptions,
    RepairOptions,
    FormatError,
    ConversionError
)

logger = logging.getLogger(__name__)


class USDLayerType(Enum):
    """USD layer types following LIVRPS composition arc system"""
    LOCAL = "local"              # Local opinions (strongest)
    INHERITS = "inherits"         # Class inheritance
    VARIANTS = "variants"         # Variant sets
    REFERENCES = "references"     # Reference other USD files
    PAYLOADS = "payloads"         # Deferred loading references
    SPECIALIZES = "specializes"   # Template specialization


@dataclass
class USDExportOptions:
    """USD export options"""
    # File format
    format: str = "usda"  # usda (ASCII) or usdc (binary)

    # Stage options
    up_axis: str = "Y"  # Y or Z
    meters_per_unit: float = 1.0
    frames_per_second: float = 24.0

    # Composition
    use_references: bool = True  # Use references for assets
    use_payloads: bool = False   # Use payloads for heavy assets
    create_variants: bool = True  # Create variant sets for LODs

    # Geometry
    export_normals: bool = True
    export_uvs: bool = True
    export_colors: bool = False
    triangulate: bool = False

    # Materials
    export_materials: bool = True
    material_binding_strength: str = "weakerThanDescendants"

    # Custom options
    custom: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom is None:
            self.custom = {}


class USDHandler(ModelFormatHandler):
    """
    USD (Universal Scene Description) format handler.

    Features:
    - FBX/OBJ → USD conversion
    - Stage layering with LIVRPS composition
    - Variant sets for LODs and material variations
    - Reference-based asset organization
    - MaterialX integration for materials
    - Timeline and animation support

    USD Composition Arcs (LIVRPS order, strongest to weakest):
    1. Local opinions - Direct edits on prims
    2. Inherits - Class inheritance
    3. Variants - Switchable variations
    4. References - External file inclusion
    5. Payloads - Deferred loading
    6. Specializes - Template specialization

    USD Spec: https://openusd.org/
    """

    def __init__(self):
        """Initialize USD handler"""
        self.usd_available = self._check_usd()

        if not self.usd_available:
            logger.warning(
                "USD library not available. Install with:\n"
                "  pip install usd-core\n"
                "Using fallback XML-based USDA writer"
            )

    def _check_usd(self) -> bool:
        """Check if USD library is available"""
        try:
            from pxr import Usd, UsdGeom, UsdShade
            return True
        except ImportError:
            return False

    # ========================================================================
    # FormatHandler Interface
    # ========================================================================

    def get_name(self) -> str:
        """Get format name"""
        return "USD"

    def get_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return ['.usd', '.usda', '.usdc', '.usdz', '.USD', '.USDA', '.USDC', '.USDZ']

    def can_read(self) -> bool:
        """Can this handler read files?"""
        return self.usd_available

    def can_write(self) -> bool:
        """Can this handler write files?"""
        return True  # Can write USDA fallback

    def get_description(self) -> str:
        """Get human-readable description"""
        return "Pixar USD - Universal Scene Description with layered composition"

    def detect_format(self, file_path: Path) -> bool:
        """
        Detect if file is valid USD.

        USD files:
        - USDA (ASCII): starts with "#usda 1.0"
        - USDC (binary): starts with "PXR-USDC"
        - USDZ: ZIP archive containing USD files
        """
        if not file_path.exists():
            return False

        try:
            with open(file_path, 'rb') as f:
                header = f.read(32)

                # Check for USDA
                if header.startswith(b'#usda'):
                    return True

                # Check for USDC
                if b'PXR-USDC' in header:
                    return True

                # Check for USDZ (ZIP archive)
                if header.startswith(b'PK\x03\x04'):
                    return file_path.suffix.lower() == '.usdz'

            return False
        except:
            return False

    # ========================================================================
    # ModelFormatHandler Interface
    # ========================================================================

    def convert_to(
        self,
        source_path: Path,
        target_path: Path,
        options: ConversionOptions
    ) -> None:
        """
        Convert model to USD format.

        Args:
            source_path: Input model file (FBX, OBJ, etc.)
            target_path: Output USD file
            options: Conversion options

        Raises:
            ConversionError: If conversion fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Create USD export options
        usd_options = USDExportOptions(
            format="usda" if target_path.suffix == ".usda" else "usdc",
            export_normals=True,
            export_uvs=True,
            export_materials=options.keep_materials,
            triangulate=False
        )

        if self.usd_available:
            self._convert_with_usd(source_path, target_path, usd_options)
        else:
            self._convert_with_fallback(source_path, target_path, usd_options)

        logger.info(f"Converted {source_path} → {target_path}")

    def optimize(
        self,
        source_path: Path,
        target_path: Path,
        level: int
    ) -> None:
        """
        Optimize USD stage (flatten layers, remove unused prims).

        Args:
            source_path: Input USD file
            target_path: Output optimized USD file
            level: Optimization level (0-10)

        Raises:
            ConversionError: If optimization fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if self.usd_available:
            from pxr import Usd

            # Open stage
            stage = Usd.Stage.Open(str(source_path))

            if level >= 5:
                # Flatten composition arcs
                stage.Flatten()

            # Export to target
            stage.Export(str(target_path))

            logger.info(f"Optimized USD: {source_path} → {target_path}")
        else:
            # Fallback: just copy
            import shutil
            shutil.copy(source_path, target_path)
            logger.warning("USD optimization requires usd-core library")

    def repair(
        self,
        source_path: Path,
        target_path: Path,
        options: RepairOptions
    ) -> None:
        """
        Repair USD stage (fix normals, validate structure).

        Args:
            source_path: Input USD file
            target_path: Output repaired USD file
            options: Repair options

        Raises:
            RepairError: If repair fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # USD stages are typically well-formed, but we can validate
        if self.usd_available:
            from pxr import Usd, UsdGeom

            stage = Usd.Stage.Open(str(source_path))

            # Validate all meshes
            for prim in stage.Traverse():
                if prim.IsA(UsdGeom.Mesh):
                    mesh = UsdGeom.Mesh(prim)

                    # Ensure normals if requested
                    if options.generate_normals:
                        if not mesh.GetNormalsAttr().HasValue():
                            # Compute normals
                            points = mesh.GetPointsAttr().Get()
                            face_vertex_counts = mesh.GetFaceVertexCountsAttr().Get()
                            face_vertex_indices = mesh.GetFaceVertexIndicesAttr().Get()

                            normals = self._compute_normals(
                                points,
                                face_vertex_counts,
                                face_vertex_indices
                            )
                            mesh.GetNormalsAttr().Set(normals)
                            mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)

            # Export repaired stage
            stage.Export(str(target_path))

            logger.info(f"Repaired USD: {source_path} → {target_path}")
        else:
            # Fallback: just copy
            import shutil
            shutil.copy(source_path, target_path)
            logger.warning("USD repair requires usd-core library")

    def _compute_normals(self, points, face_vertex_counts, face_vertex_indices):
        """Compute smooth vertex normals"""
        from pxr import Gf
        import numpy as np

        num_points = len(points)
        normals = [Gf.Vec3f(0, 0, 0) for _ in range(num_points)]

        # Accumulate face normals at vertices
        idx = 0
        for count in face_vertex_counts:
            # Get face vertices
            face_indices = face_vertex_indices[idx:idx+count]

            # Compute face normal
            v0 = np.array(points[face_indices[0]])
            v1 = np.array(points[face_indices[1]])
            v2 = np.array(points[face_indices[2]])

            edge1 = v1 - v0
            edge2 = v2 - v0
            face_normal = np.cross(edge1, edge2)
            face_normal = face_normal / (np.linalg.norm(face_normal) + 1e-8)

            # Accumulate at vertices
            for vert_idx in face_indices:
                normals[vert_idx] += Gf.Vec3f(face_normal[0], face_normal[1], face_normal[2])

            idx += count

        # Normalize
        for i in range(num_points):
            normals[i].Normalize()

        return normals

    def get_metadata(self, source_path: Path) -> ModelMetadata:
        """
        Extract USD stage metadata.

        Args:
            source_path: USD file to analyze

        Returns:
            ModelMetadata object

        Raises:
            FormatError: If metadata extraction fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        metadata = ModelMetadata()

        if self.usd_available:
            from pxr import Usd, UsdGeom

            try:
                stage = Usd.Stage.Open(str(source_path))

                total_verts = 0
                total_faces = 0

                # Traverse stage and count geometry
                for prim in stage.Traverse():
                    if prim.IsA(UsdGeom.Mesh):
                        mesh = UsdGeom.Mesh(prim)

                        points = mesh.GetPointsAttr().Get()
                        if points:
                            total_verts += len(points)

                        face_counts = mesh.GetFaceVertexCountsAttr().Get()
                        if face_counts:
                            total_faces += len(face_counts)

                metadata.vertex_count = total_verts
                metadata.face_count = total_faces

                # Check for normals/UVs
                for prim in stage.Traverse():
                    if prim.IsA(UsdGeom.Mesh):
                        mesh = UsdGeom.Mesh(prim)
                        if mesh.GetNormalsAttr().HasValue():
                            metadata.has_normals = True
                        # Check for UVs (primvars:st)
                        primvars = UsdGeom.PrimvarsAPI(mesh)
                        if primvars.GetPrimvar("st"):
                            metadata.has_uvs = True
                        break

                logger.info(f"Extracted metadata from {source_path}")

            except Exception as e:
                logger.error(f"Failed to extract USD metadata: {e}")
                raise FormatError(f"USD metadata extraction failed: {e}")

        return metadata

    # ========================================================================
    # USD-specific Features
    # ========================================================================

    def create_layered_stage(
        self,
        root_path: Path,
        layer_paths: Dict[USDLayerType, Path]
    ) -> None:
        """
        Create USD stage with LIVRPS layer composition.

        Args:
            root_path: Root USD file path
            layer_paths: Dictionary mapping layer types to file paths

        Example:
            >>> handler.create_layered_stage(
            ...     root_path=Path("scene.usda"),
            ...     layer_paths={
            ...         USDLayerType.REFERENCES: Path("assets/char.usda"),
            ...         USDLayerType.VARIANTS: Path("lods/char_lods.usda"),
            ...         USDLayerType.LOCAL: Path("overrides/char_anim.usda")
            ...     }
            ... )
        """
        if not self.usd_available:
            raise ConversionError("USD library required for layered stages")

        from pxr import Usd, Sdf

        # Create root stage
        stage = Usd.Stage.CreateNew(str(root_path))

        # Add sublayers in LIVRPS order
        root_layer = stage.GetRootLayer()

        # Local opinions (strongest) - added first
        if USDLayerType.LOCAL in layer_paths:
            root_layer.subLayerPaths.append(str(layer_paths[USDLayerType.LOCAL]))

        # Create root prim
        root_prim = stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(root_prim)

        # Add references
        if USDLayerType.REFERENCES in layer_paths:
            ref_path = layer_paths[USDLayerType.REFERENCES]
            root_prim.GetReferences().AddReference(str(ref_path))

        # Add payloads (deferred loading)
        if USDLayerType.PAYLOADS in layer_paths:
            payload_path = layer_paths[USDLayerType.PAYLOADS]
            root_prim.GetPayloads().AddPayload(str(payload_path))

        # Save stage
        stage.Save()

        logger.info(f"Created layered USD stage: {root_path}")

    def create_variant_set(
        self,
        stage_path: Path,
        prim_path: str,
        variant_set_name: str,
        variants: Dict[str, Path]
    ) -> None:
        """
        Create variant set for LODs or material variations.

        Args:
            stage_path: USD stage file
            prim_path: Path to prim (e.g., "/World/Character")
            variant_set_name: Name of variant set (e.g., "LOD")
            variants: Dictionary mapping variant names to USD files
                     Example: {"high": "char_high.usda", "low": "char_low.usda"}

        Example:
            >>> handler.create_variant_set(
            ...     stage_path=Path("scene.usda"),
            ...     prim_path="/World/Character",
            ...     variant_set_name="LOD",
            ...     variants={
            ...         "high": Path("assets/char_high.usda"),
            ...         "medium": Path("assets/char_medium.usda"),
            ...         "low": Path("assets/char_low.usda")
            ...     }
            ... )
        """
        if not self.usd_available:
            raise ConversionError("USD library required for variant sets")

        from pxr import Usd

        # Open or create stage
        if stage_path.exists():
            stage = Usd.Stage.Open(str(stage_path))
        else:
            stage = Usd.Stage.CreateNew(str(stage_path))

        # Get or create prim
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            prim = stage.DefinePrim(prim_path, "Xform")

        # Create variant set
        variant_sets = prim.GetVariantSets()
        variant_set = variant_sets.AddVariantSet(variant_set_name)

        # Add variants
        for variant_name, variant_file in variants.items():
            variant_set.AddVariant(variant_name)
            variant_set.SetVariantSelection(variant_name)

            # Edit variant
            with variant_set.GetVariantEditContext():
                # Reference variant file
                prim.GetReferences().AddReference(str(variant_file))

        # Set default variant (first one)
        first_variant = list(variants.keys())[0]
        variant_set.SetVariantSelection(first_variant)

        # Save stage
        stage.Save()

        logger.info(f"Created variant set '{variant_set_name}' with {len(variants)} variants")

    # ========================================================================
    # USD Conversion Implementation
    # ========================================================================

    def _convert_with_usd(
        self,
        source_path: Path,
        target_path: Path,
        options: USDExportOptions
    ) -> None:
        """Convert using USD library"""
        from pxr import Usd, UsdGeom

        # Load source mesh using trimesh
        try:
            import trimesh
            mesh = trimesh.load(str(source_path))
        except:
            raise ConversionError("Failed to load source mesh (trimesh required)")

        # Create USD stage
        stage = Usd.Stage.CreateNew(str(target_path))

        # Set stage metadata
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y if options.up_axis == "Y" else UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, options.meters_per_unit)

        # Create root prim
        root_prim = stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(root_prim)

        # Create mesh prim
        mesh_prim = UsdGeom.Mesh.Define(stage, "/World/Mesh")

        # Set points
        from pxr import Vt, Gf
        points = [Gf.Vec3f(v[0], v[1], v[2]) for v in mesh.vertices]
        mesh_prim.GetPointsAttr().Set(points)

        # Set face vertex counts and indices
        face_vertex_counts = [len(face) for face in mesh.faces]
        face_vertex_indices = mesh.faces.flatten().tolist()

        mesh_prim.GetFaceVertexCountsAttr().Set(face_vertex_counts)
        mesh_prim.GetFaceVertexIndicesAttr().Set(face_vertex_indices)

        # Set normals if available
        if options.export_normals and hasattr(mesh, 'vertex_normals'):
            normals = [Gf.Vec3f(n[0], n[1], n[2]) for n in mesh.vertex_normals]
            mesh_prim.GetNormalsAttr().Set(normals)
            mesh_prim.SetNormalsInterpolation(UsdGeom.Tokens.vertex)

        # Set UVs if available
        if options.export_uvs and hasattr(mesh.visual, 'uv'):
            uvs_data = mesh.visual.uv
            uvs = [Gf.Vec2f(uv[0], uv[1]) for uv in uvs_data]
            primvars = UsdGeom.PrimvarsAPI(mesh_prim)
            st_primvar = primvars.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray)
            st_primvar.Set(uvs)

        # Save stage
        stage.Save()

        logger.info(f"Converted to USD: {target_path}")

    def _convert_with_fallback(
        self,
        source_path: Path,
        target_path: Path,
        options: USDExportOptions
    ) -> None:
        """Convert using fallback USDA writer"""
        # Load mesh using trimesh
        try:
            import trimesh
            mesh = trimesh.load(str(source_path))
        except:
            raise ConversionError("Failed to load source mesh (trimesh required)")

        # Write basic USDA file
        with open(target_path, 'w') as f:
            f.write("#usda 1.0\n")
            f.write("(\n")
            f.write("    defaultPrim = \"World\"\n")
            f.write(f"    upAxis = \"{options.up_axis}\"\n")
            f.write(f"    metersPerUnit = {options.meters_per_unit}\n")
            f.write(")\n\n")

            f.write("def Xform \"World\"\n")
            f.write("{\n")
            f.write("    def Mesh \"Mesh\"\n")
            f.write("    {\n")

            # Write points
            f.write("        point3f[] points = [\n")
            for i, v in enumerate(mesh.vertices):
                f.write(f"            ({v[0]}, {v[1]}, {v[2]})")
                if i < len(mesh.vertices) - 1:
                    f.write(",\n")
                else:
                    f.write("\n")
            f.write("        ]\n")

            # Write face vertex counts
            f.write("        int[] faceVertexCounts = [")
            f.write(", ".join(["3"] * len(mesh.faces)))
            f.write("]\n")

            # Write face vertex indices
            f.write("        int[] faceVertexIndices = [\n")
            flat_faces = mesh.faces.flatten()
            for i, idx in enumerate(flat_faces):
                f.write(f"            {idx}")
                if i < len(flat_faces) - 1:
                    f.write(",\n")
                else:
                    f.write("\n")
            f.write("        ]\n")

            f.write("    }\n")
            f.write("}\n")

        logger.info(f"Wrote USDA file: {target_path}")
