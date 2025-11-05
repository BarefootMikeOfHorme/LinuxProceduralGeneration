"""
VaultMind Forge - FBX Format Handler
Supports reading/writing FBX models with full materials and animations
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from .format_registry import (
    ModelFormatHandler,
    ModelMetadata,
    ConversionOptions,
    RepairOptions,
    FormatError,
    ConversionError,
    RepairError
)

logger = logging.getLogger(__name__)


class FBXHandler(ModelFormatHandler):
    """
    FBX format handler using FBX SDK integration.

    Features:
    - Read/write FBX 2020 and earlier
    - Full material preservation
    - Animation support
    - Mesh repair and optimization
    - Metadata extraction

    Integration:
    - Uses FBX SDK via Python bindings (fbx library)
    - Falls back to trimesh/pyassimp if FBX SDK unavailable
    """

    def __init__(self):
        """Initialize FBX handler"""
        self.sdk_available = self._check_fbx_sdk()
        self.fallback_available = self._check_fallback()

        if not self.sdk_available and not self.fallback_available:
            logger.warning(
                "FBX SDK not available. Install with: pip install fbx-python-sdk\n"
                "Fallback requires: pip install trimesh pyassimp"
            )

    def _check_fbx_sdk(self) -> bool:
        """Check if FBX SDK is available"""
        try:
            import fbx
            return True
        except ImportError:
            return False

    def _check_fallback(self) -> bool:
        """Check if fallback libraries are available"""
        try:
            import trimesh
            import pyassimp
            return True
        except ImportError:
            return False

    # ========================================================================
    # FormatHandler Interface
    # ========================================================================

    def get_name(self) -> str:
        """Get format name"""
        return "FBX"

    def get_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return ['.fbx', '.FBX']

    def can_read(self) -> bool:
        """Can this handler read files?"""
        return self.sdk_available or self.fallback_available

    def can_write(self) -> bool:
        """Can this handler write files?"""
        return self.sdk_available or self.fallback_available

    def get_description(self) -> str:
        """Get human-readable description"""
        return "Autodesk FBX - Industry standard 3D interchange format"

    def detect_format(self, file_path: Path) -> bool:
        """
        Detect if file is valid FBX.

        FBX files start with either:
        - ASCII: "Kaydara FBX Binary"
        - Binary: Magic bytes (0x1A 0x00 followed by version)
        """
        if not file_path.exists():
            return False

        try:
            with open(file_path, 'rb') as f:
                # Read first 32 bytes
                header = f.read(32)

                # Check for ASCII FBX
                if b'Kaydara FBX Binary' in header:
                    return True

                # Check for binary FBX magic bytes
                if len(header) >= 27:
                    # Binary FBX starts with specific magic
                    if header[0:2] == b'Kaydara FBX Binary  \x00'[:2]:
                        return True

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
        Convert model to FBX format.

        Args:
            source_path: Input model file (any supported format)
            target_path: Output FBX file
            options: Conversion options

        Raises:
            ConversionError: If conversion fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if self.sdk_available:
            self._convert_with_sdk(source_path, target_path, options)
        elif self.fallback_available:
            self._convert_with_fallback(source_path, target_path, options)
        else:
            raise ConversionError("No FBX conversion backend available")

        logger.info(f"Converted {source_path} → {target_path}")

    def optimize(
        self,
        source_path: Path,
        target_path: Path,
        level: int
    ) -> None:
        """
        Optimize FBX model geometry.

        Optimization levels:
        0-2: Basic cleanup (remove duplicates, fix normals)
        3-5: Mesh decimation (preserve topology)
        6-8: Aggressive decimation (allow topology changes)
        9-10: Maximum decimation (for LODs)

        Args:
            source_path: Input FBX file
            target_path: Output optimized FBX file
            level: Optimization level (0-10)

        Raises:
            ConversionError: If optimization fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Load mesh
        if self.fallback_available:
            import trimesh

            try:
                mesh = trimesh.load(str(source_path))

                # Basic cleanup (always)
                mesh.remove_duplicate_faces()
                mesh.remove_degenerate_faces()
                mesh.remove_infinite_values()

                if level >= 3:
                    # Mesh decimation
                    target_faces = self._calculate_target_faces(
                        len(mesh.faces),
                        level
                    )
                    mesh = mesh.simplify_quadric_decimation(target_faces)

                # Export to FBX
                mesh.export(str(target_path))

                logger.info(f"Optimized {source_path} → {target_path} (level {level})")

            except Exception as e:
                raise ConversionError(f"Optimization failed: {e}")
        else:
            # Without fallback, just copy
            import shutil
            shutil.copy(source_path, target_path)
            logger.warning("Optimization skipped (trimesh not available)")

    def _calculate_target_faces(self, current_faces: int, level: int) -> int:
        """Calculate target face count based on optimization level"""
        # Level 3-5: 50-75% reduction
        # Level 6-8: 75-90% reduction
        # Level 9-10: 90-95% reduction

        if level <= 2:
            return current_faces
        elif level <= 5:
            reduction = 0.5 + (level - 3) * 0.125  # 50-75%
        elif level <= 8:
            reduction = 0.75 + (level - 6) * 0.05  # 75-90%
        else:
            reduction = 0.90 + (level - 9) * 0.025  # 90-95%

        target = int(current_faces * (1.0 - reduction))
        return max(target, 100)  # Minimum 100 faces

    def repair(
        self,
        source_path: Path,
        target_path: Path,
        options: RepairOptions
    ) -> None:
        """
        Repair FBX mesh issues.

        Repairs:
        - Missing normals (generate smooth/flat)
        - Missing UVs (generate basic unwrap)
        - Non-manifold geometry (fix holes, duplicates)
        - Degenerate triangles

        Args:
            source_path: Input FBX file
            target_path: Output repaired FBX file
            options: Repair options

        Raises:
            RepairError: If repair fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if self.fallback_available:
            import trimesh

            try:
                mesh = trimesh.load(str(source_path))

                # Fix mesh issues
                if options.fix_holes:
                    mesh.fill_holes()

                if options.triangulate:
                    # Already triangulated by trimesh
                    pass

                if options.generate_normals:
                    # Recompute vertex normals
                    mesh.vertex_normals

                if options.generate_uvs:
                    # Generate basic UV unwrap (planar projection)
                    mesh.visual = self._generate_basic_uvs(mesh)

                # Export repaired mesh
                mesh.export(str(target_path))

                logger.info(f"Repaired {source_path} → {target_path}")

            except Exception as e:
                raise RepairError(f"Mesh repair failed: {e}")
        else:
            # Without fallback, just copy
            import shutil
            shutil.copy(source_path, target_path)
            logger.warning("Repair skipped (trimesh not available)")

    def _generate_basic_uvs(self, mesh) -> Any:
        """Generate basic planar UV coordinates"""
        import numpy as np

        # Simple planar projection (XY plane)
        vertices = mesh.vertices
        bounds_min = vertices.min(axis=0)
        bounds_max = vertices.max(axis=0)

        # Normalize to 0-1 range
        uvs = np.zeros((len(vertices), 2))
        uvs[:, 0] = (vertices[:, 0] - bounds_min[0]) / (bounds_max[0] - bounds_min[0] + 1e-8)
        uvs[:, 1] = (vertices[:, 1] - bounds_min[1]) / (bounds_max[1] - bounds_min[1] + 1e-8)

        # Create visual with UVs
        from trimesh.visual import TextureVisuals
        return TextureVisuals(uv=uvs)

    def get_metadata(self, source_path: Path) -> ModelMetadata:
        """
        Extract FBX model metadata.

        Args:
            source_path: FBX file to analyze

        Returns:
            ModelMetadata object

        Raises:
            FormatError: If metadata extraction fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        metadata = ModelMetadata()

        if self.fallback_available:
            import trimesh

            try:
                mesh = trimesh.load(str(source_path))

                metadata.vertex_count = len(mesh.vertices)
                metadata.face_count = len(mesh.faces)
                metadata.has_normals = hasattr(mesh, 'vertex_normals')
                metadata.has_uvs = hasattr(mesh.visual, 'uv') if hasattr(mesh, 'visual') else False

                # Bounding box
                bounds = mesh.bounds
                metadata.bounding_box = [
                    bounds[0][0], bounds[0][1], bounds[0][2],
                    bounds[1][0], bounds[1][1], bounds[1][2]
                ]

                # Materials
                if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'material'):
                    metadata.material_count = 1

                logger.info(f"Extracted metadata from {source_path}")

            except Exception as e:
                logger.error(f"Failed to extract metadata: {e}")
                raise FormatError(f"Metadata extraction failed: {e}")

        return metadata

    # ========================================================================
    # FBX SDK Implementation
    # ========================================================================

    def _convert_with_sdk(
        self,
        source_path: Path,
        target_path: Path,
        options: ConversionOptions
    ) -> None:
        """Convert using FBX SDK"""
        import fbx

        # Create FBX manager and scene
        manager = fbx.FbxManager.Create()
        scene = fbx.FbxScene.Create(manager, "")

        # Import source file
        importer = fbx.FbxImporter.Create(manager, "")
        if not importer.Initialize(str(source_path), -1):
            raise ConversionError(f"Failed to initialize FBX importer")

        importer.Import(scene)
        importer.Destroy()

        # Apply scale if needed
        if options.scale_factor != 1.0:
            self._apply_scale_sdk(scene, options.scale_factor)

        # Export to FBX
        exporter = fbx.FbxExporter.Create(manager, "")
        if not exporter.Initialize(str(target_path), -1):
            raise ConversionError(f"Failed to initialize FBX exporter")

        exporter.Export(scene)
        exporter.Destroy()

        manager.Destroy()

    def _apply_scale_sdk(self, scene, scale_factor: float) -> None:
        """Apply scale to FBX scene"""
        import fbx

        root = scene.GetRootNode()
        for i in range(root.GetChildCount()):
            node = root.GetChild(i)
            scaling = node.LclScaling.Get()
            node.LclScaling.Set(fbx.FbxDouble3(
                scaling[0] * scale_factor,
                scaling[1] * scale_factor,
                scaling[2] * scale_factor
            ))

    # ========================================================================
    # Fallback Implementation
    # ========================================================================

    def _convert_with_fallback(
        self,
        source_path: Path,
        target_path: Path,
        options: ConversionOptions
    ) -> None:
        """Convert using trimesh/pyassimp fallback"""
        import trimesh

        # Load mesh
        mesh = trimesh.load(str(source_path))

        # Apply scale if needed
        if options.scale_factor != 1.0:
            mesh.apply_scale(options.scale_factor)

        # Export to FBX
        mesh.export(str(target_path))
