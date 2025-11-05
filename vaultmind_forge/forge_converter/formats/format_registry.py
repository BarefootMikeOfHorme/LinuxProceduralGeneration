"""
VaultMind Forge - Format Registry
Adapted from DomainShell format_registry.rs

Manages format handlers for asset conversion.
Integrated with VaultMind Forge asset structure and lineage tracking.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib


# ============================================================================
# Asset Paths for VaultMind Forge Structure
# ============================================================================

class AssetPaths:
    """
    Centralized asset path management for VaultMind Forge.
    Maps to assets/ directory structure.
    """
    def __init__(self, base_path: Optional[Path] = None):
        self.base = base_path or Path(__file__).parents[3] / "assets"

        # Main directories
        self.source = self.base / "source"
        self.input = self.base / "input"
        self.generated = self.base / "generated"
        self.validated = self.base / "validated"
        self.output = self.base / "output"
        self.reference = self.base / "reference"
        self.temp = self.base / "temp"
        self.archive = self.base / "archive"

        # Source subdirectories
        self.source_models = self.source / "models"
        self.source_textures = self.source / "textures"
        self.source_materials = self.source / "materials"
        self.source_animations = self.source / "animations"

        # Input subdirectories
        self.input_models = self.input / "models"
        self.input_textures = self.input / "textures"
        self.input_metadata = self.input / "metadata"

        # Generated subdirectories
        self.generated_diffusion = self.generated / "diffusion"
        self.generated_semantic = self.generated / "semantic"
        self.generated_sr = self.generated / "sr"
        self.generated_video = self.generated / "video"

        # Output by engine
        self.output_unity = self.output / "unity"
        self.output_unreal = self.output / "unreal"
        self.output_godot = self.output / "godot"
        self.output_web = self.output / "web"
        self.output_blender = self.output / "blender"

    def ensure_all_exist(self):
        """Create all asset directories if they don't exist."""
        for attr_name in dir(self):
            if not attr_name.startswith('_'):
                attr = getattr(self, attr_name)
                if isinstance(attr, Path):
                    attr.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class FormatType(str, Enum):
    """Asset format types."""
    MODEL = "model"
    TEXTURE = "texture"
    ANIMATION = "animation"
    MATERIAL = "material"
    CAD = "cad"
    AUDIO = "audio"


class CompressionQuality(str, Enum):
    """Texture compression quality levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    LOSSLESS = "lossless"


@dataclass
class ConversionOptions:
    """Options for asset conversion."""
    compress: bool = True
    optimize_level: int = 5  # 0-10
    keep_materials: bool = True
    keep_animations: bool = True
    scale_factor: float = 1.0
    custom_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RepairOptions:
    """Options for mesh repair."""
    generate_normals: bool = True
    generate_uvs: bool = False
    triangulate: bool = True
    fix_holes: bool = True
    custom_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TextureOptions:
    """Options for texture conversion."""
    compression_quality: CompressionQuality = CompressionQuality.HIGH
    generate_mipmaps: bool = True
    flip_y: bool = False
    convert_to_srgb: bool = True
    resize_dimensions: Optional[tuple[int, int]] = None
    custom_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnimationOptions:
    """Options for animation conversion."""
    frame_rate: Optional[float] = None
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None
    loop_animation: bool = False
    custom_options: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Metadata Classes
# ============================================================================

@dataclass
class ModelMetadata:
    """Metadata for 3D models."""
    vertex_count: int = 0
    face_count: int = 0
    material_count: int = 0
    animation_count: int = 0
    bounding_box: List[float] = field(default_factory=lambda: [0.0] * 6)
    has_uvs: bool = False
    has_normals: bool = False
    has_tangents: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TextureMetadata:
    """Metadata for textures."""
    width: int = 0
    height: int = 0
    depth: int = 1
    channels: int = 4
    bits_per_channel: int = 8
    is_hdr: bool = False
    compression_format: Optional[str] = None
    color_space: str = "sRGB"

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AnimationMetadata:
    """Metadata for animations."""
    frame_count: int = 0
    duration: float = 0.0
    frame_rate: float = 30.0
    bone_count: int = 0
    track_count: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# Exceptions
# ============================================================================

class AssetError(Exception):
    """Base exception for asset operations."""
    pass


class FormatError(AssetError):
    """Format detection or parsing error."""
    pass


class ConversionError(AssetError):
    """Asset conversion error."""
    pass


class RepairError(AssetError):
    """Mesh repair error."""
    pass


# ============================================================================
# Format Handler Base Classes
# ============================================================================

class FormatHandler(ABC):
    """Base class for all format handlers."""

    @abstractmethod
    def get_name(self) -> str:
        """Get format name (e.g., 'FBX', 'PNG')."""
        pass

    @abstractmethod
    def get_extensions(self) -> List[str]:
        """Get supported file extensions (e.g., ['.fbx', '.FBX'])."""
        pass

    @abstractmethod
    def can_read(self) -> bool:
        """Can this handler read files?"""
        pass

    @abstractmethod
    def can_write(self) -> bool:
        """Can this handler write files?"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description."""
        pass

    @abstractmethod
    def detect_format(self, file_path: Path) -> bool:
        """Detect if file matches this format."""
        pass


class ModelFormatHandler(FormatHandler):
    """Handler for 3D model formats."""

    @abstractmethod
    def convert_to(
        self,
        source_path: Path,
        target_path: Path,
        options: ConversionOptions
    ) -> None:
        """Convert model to this format."""
        pass

    @abstractmethod
    def optimize(
        self,
        source_path: Path,
        target_path: Path,
        level: int
    ) -> None:
        """Optimize model geometry."""
        pass

    @abstractmethod
    def repair(
        self,
        source_path: Path,
        target_path: Path,
        options: RepairOptions
    ) -> None:
        """Repair mesh issues."""
        pass

    @abstractmethod
    def get_metadata(self, source_path: Path) -> ModelMetadata:
        """Extract model metadata."""
        pass


class TextureFormatHandler(FormatHandler):
    """Handler for texture formats."""

    @abstractmethod
    def convert_to(
        self,
        source_path: Path,
        target_path: Path,
        options: TextureOptions
    ) -> None:
        """Convert texture to this format."""
        pass

    @abstractmethod
    def compress(
        self,
        source_path: Path,
        target_path: Path,
        quality: CompressionQuality
    ) -> None:
        """Compress texture."""
        pass

    @abstractmethod
    def resize(
        self,
        source_path: Path,
        target_path: Path,
        width: int,
        height: int
    ) -> None:
        """Resize texture."""
        pass

    @abstractmethod
    def get_metadata(self, source_path: Path) -> TextureMetadata:
        """Extract texture metadata."""
        pass


class AnimationFormatHandler(FormatHandler):
    """Handler for animation formats."""

    @abstractmethod
    def convert_to(
        self,
        source_path: Path,
        target_path: Path,
        options: AnimationOptions
    ) -> None:
        """Convert animation to this format."""
        pass

    @abstractmethod
    def extract_from_model(
        self,
        model_path: Path,
        target_path: Path
    ) -> None:
        """Extract animation from model file."""
        pass

    @abstractmethod
    def get_metadata(self, source_path: Path) -> AnimationMetadata:
        """Extract animation metadata."""
        pass


# ============================================================================
# Format Registry
# ============================================================================

class FormatRegistry:
    """
    Central registry for all format handlers.
    Adapted from DomainShell, integrated with VaultMind Forge.
    """

    def __init__(self, asset_paths: Optional[AssetPaths] = None):
        """
        Initialize format registry.

        Args:
            asset_paths: Asset path manager (creates default if None)
        """
        self.asset_paths = asset_paths or AssetPaths()

        self.model_formats: Dict[str, ModelFormatHandler] = {}
        self.texture_formats: Dict[str, TextureFormatHandler] = {}
        self.animation_formats: Dict[str, AnimationFormatHandler] = {}

        # Ensure asset directories exist
        self.asset_paths.ensure_all_exist()

    # ========================================================================
    # Registration Methods
    # ========================================================================

    def register_model_format(self, handler: ModelFormatHandler) -> None:
        """Register a model format handler."""
        self.model_formats[handler.get_name().lower()] = handler

    def register_texture_format(self, handler: TextureFormatHandler) -> None:
        """Register a texture format handler."""
        self.texture_formats[handler.get_name().lower()] = handler

    def register_animation_format(self, handler: AnimationFormatHandler) -> None:
        """Register an animation format handler."""
        self.animation_formats[handler.get_name().lower()] = handler

    # ========================================================================
    # Retrieval Methods
    # ========================================================================

    def get_model_format(self, name: str) -> Optional[ModelFormatHandler]:
        """Get model format handler by name."""
        return self.model_formats.get(name.lower())

    def get_texture_format(self, name: str) -> Optional[TextureFormatHandler]:
        """Get texture format handler by name."""
        return self.texture_formats.get(name.lower())

    def get_animation_format(self, name: str) -> Optional[AnimationFormatHandler]:
        """Get animation format handler by name."""
        return self.animation_formats.get(name.lower())

    def get_all_handlers(self) -> List[FormatHandler]:
        """Get all registered format handlers."""
        handlers: List[FormatHandler] = []
        handlers.extend(self.model_formats.values())
        handlers.extend(self.texture_formats.values())
        handlers.extend(self.animation_formats.values())
        return handlers

    # ========================================================================
    # Detection Methods
    # ========================================================================

    def detect_format(self, file_path: Path) -> Optional[tuple[FormatType, str]]:
        """
        Detect format type and name from file.

        Returns:
            (FormatType, format_name) or None if unknown
        """
        if not file_path.exists():
            return None

        ext = file_path.suffix.lower()

        # Try extension-based detection first (faster)
        for handler in self.model_formats.values():
            if ext in [e.lower() for e in handler.get_extensions()]:
                if handler.detect_format(file_path):
                    return (FormatType.MODEL, handler.get_name())

        for handler in self.texture_formats.values():
            if ext in [e.lower() for e in handler.get_extensions()]:
                if handler.detect_format(file_path):
                    return (FormatType.TEXTURE, handler.get_name())

        for handler in self.animation_formats.values():
            if ext in [e.lower() for e in handler.get_extensions()]:
                if handler.detect_format(file_path):
                    return (FormatType.ANIMATION, handler.get_name())

        # Try content-based detection (slower but more reliable)
        for handler in self.get_all_handlers():
            if handler.detect_format(file_path):
                # Determine type
                if isinstance(handler, ModelFormatHandler):
                    return (FormatType.MODEL, handler.get_name())
                elif isinstance(handler, TextureFormatHandler):
                    return (FormatType.TEXTURE, handler.get_name())
                elif isinstance(handler, AnimationFormatHandler):
                    return (FormatType.ANIMATION, handler.get_name())

        return None

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def compute_checksum(self, file_path: Path) -> str:
        """
        Compute SHA-256 checksum for lineage tracking.

        Args:
            file_path: File to checksum

        Returns:
            Hexadecimal checksum string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def save_metadata(
        self,
        metadata: Any,
        output_path: Path,
        asset_id: Optional[str] = None
    ) -> Path:
        """
        Save metadata to JSON file in input/metadata/ directory.

        Args:
            metadata: Metadata object with to_dict() method
            output_path: Where the asset will be stored
            asset_id: Optional asset ID (generated if None)

        Returns:
            Path to saved metadata file
        """
        if asset_id is None:
            asset_id = output_path.stem

        metadata_path = self.asset_paths.input_metadata / f"{asset_id}.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        metadata_dict = metadata.to_dict() if hasattr(metadata, 'to_dict') else metadata

        # Add VaultMind Forge metadata
        forge_metadata = {
            "forge_version": "1.0.0",
            "asset_id": asset_id,
            "checksum": self.compute_checksum(output_path) if output_path.exists() else None,
            "metadata": metadata_dict
        }

        with open(metadata_path, 'w') as f:
            json.dump(forge_metadata, f, indent=2)

        return metadata_path

    def list_supported_formats(self) -> Dict[FormatType, List[str]]:
        """
        Get all supported formats by type.

        Returns:
            Dictionary mapping FormatType to list of format names
        """
        return {
            FormatType.MODEL: list(self.model_formats.keys()),
            FormatType.TEXTURE: list(self.texture_formats.keys()),
            FormatType.ANIMATION: list(self.animation_formats.keys())
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Create registry
    registry = FormatRegistry()

    # Asset paths are automatically set up
    print(f"Source models: {registry.asset_paths.source_models}")
    print(f"Input models: {registry.asset_paths.input_models}")
    print(f"Unity output: {registry.asset_paths.output_unity}")

    # List supported formats
    formats = registry.list_supported_formats()
    print("\nSupported formats:")
    for format_type, format_names in formats.items():
        print(f"  {format_type.value}: {format_names}")
