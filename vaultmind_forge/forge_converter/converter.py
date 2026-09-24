"""
VaultMind Forge - Asset Converter Core

Main converter class for asset conversion operations.
"""

import os
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from . import ConversionProfile, TargetEngine, AssetType
from .contracts import (
    ConversionEnvelope,
    ConversionLossStatus,
    ConversionUnsupportedError,
)


@dataclass
class ConversionOptions:
    """Options for asset conversion."""
    generate_lods: bool = True
    lod_levels: int = 3
    texture_compression: Optional[str] = None
    max_texture_size: int = 2048
    preserve_materials: bool = True
    preserve_animations: bool = True
    optimize_mesh: bool = True
    generate_colliders: bool = False
    custom_options: Dict = None

    def __post_init__(self):
        if self.custom_options is None:
            self.custom_options = {}


@dataclass
class ConversionResult:
    """Result of an asset conversion operation."""
    success: bool
    source_path: str
    output_path: Optional[str] = None
    target_engine: Optional[str] = None
    profile: Optional[str] = None
    processing_time_ms: float = 0.0
    file_size_original: int = 0
    file_size_output: int = 0
    compression_ratio: float = 0.0
    optimizations_applied: List[str] = None
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict = None
    source_format: Optional[str] = None
    target_format: Optional[str] = None
    loss_status: ConversionLossStatus = ConversionLossStatus.UNCHECKED
    loss_reasons: List[str] = None

    def __post_init__(self):
        if self.optimizations_applied is None:
            self.optimizations_applied = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.loss_reasons is None:
            self.loss_reasons = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        """Convert result to a JSON-compatible dictionary."""
        data = asdict(self)
        data["loss_status"] = self.loss_status.value
        return data

    def to_envelope(self) -> ConversionEnvelope:
        """Return the canonical loss-aware conversion envelope."""
        return ConversionEnvelope(
            asset_id=str(self.metadata.get("asset_id", "")),
            source_path=self.source_path,
            source_format=self.source_format or "",
            target_engine=self.target_engine,
            target_format=self.target_format,
            output_path=self.output_path,
            loss_status=self.loss_status,
            loss_reasons=list(self.loss_reasons),
            warnings=list(self.warnings),
            errors=list(self.errors),
            metadata={
                **self.metadata,
                "processing_time_ms": self.processing_time_ms,
                "file_size_original": self.file_size_original,
                "file_size_output": self.file_size_output,
                "compression_ratio": self.compression_ratio,
                "optimizations_applied": list(self.optimizations_applied),
            },
            provenance={
                "tool": "forge_converter.AssetConverter",
                "operation": "convert",
                "profile": self.profile,
                "target_engine": self.target_engine,
            },
        )


class AssetConverter:
    """
    Main asset converter class.

    Handles conversion of assets between different game engines and formats.
    """

    def __init__(
        self,
        source_dir: Optional[str] = None,
        output_base: Optional[str] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize the asset converter.

        Args:
            source_dir: Base directory for source assets
            output_base: Base directory for output assets
            config: Optional configuration dictionary
        """
        self.source_dir = Path(source_dir) if source_dir else Path.cwd() / "assets" / "source"
        self.output_base = Path(output_base) if output_base else Path.cwd() / "assets" / "engines"
        self.config = config or {}

        # Ensure directories exist
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.output_base.mkdir(parents=True, exist_ok=True)

        # Load engine configurations
        self.engine_configs = self._load_engine_configs()

    def _load_engine_configs(self) -> Dict:
        """Load engine-specific configurations."""
        config_dir = Path(__file__).parent / "configs"
        configs = {}

        if config_dir.exists():
            for config_file in config_dir.glob("*_config.json"):
                engine_name = config_file.stem.replace("_config", "")
                try:
                    with open(config_file, 'r') as f:
                        configs[engine_name] = json.load(f)
                except Exception as e:
                    print(f"Warning: Failed to load config for {engine_name}: {e}")

        return configs

    def _get_profile_settings(self, profile: ConversionProfile) -> Dict:
        """Get settings for a conversion profile."""
        profiles = {
            ConversionProfile.QUALITY: {
                "texture_compression": "minimal",
                "max_texture_size": 4096,
                "lod_levels": 5,
                "mesh_decimation": "conservative",
                "preserve_all": True
            },
            ConversionProfile.BALANCED: {
                "texture_compression": "BC7",
                "max_texture_size": 2048,
                "lod_levels": 3,
                "mesh_decimation": "moderate",
                "preserve_all": False
            },
            ConversionProfile.OPTIMIZED: {
                "texture_compression": "BC1",
                "max_texture_size": 1024,
                "lod_levels": 4,
                "mesh_decimation": "aggressive",
                "atlas_textures": True
            }
        }
        return profiles.get(profile, profiles[ConversionProfile.BALANCED])

    def _detect_asset_type(self, asset_path: Path) -> AssetType:
        """Detect the type of asset from file extension."""
        ext = asset_path.suffix.lower()

        model_exts = {'.fbx', '.obj', '.gltf', '.glb', '.dae', '.blend', '.stl', '.3ds'}
        texture_exts = {'.png', '.jpg', '.jpeg', '.tga', '.tiff', '.psd', '.dds', '.exr', '.webp'}
        animation_exts = {'.anim', '.fbx'}  # FBX can contain animations
        audio_exts = {'.wav', '.mp3', '.ogg', '.flac'}

        if ext in model_exts:
            return AssetType.MODEL_3D
        elif ext in texture_exts:
            return AssetType.TEXTURE
        elif ext in animation_exts:
            return AssetType.ANIMATION
        elif ext in audio_exts:
            return AssetType.AUDIO
        else:
            return AssetType.MODEL_3D  # Default

    def convert(
        self,
        asset_path: Union[str, Path],
        target_engine: Union[str, TargetEngine],
        profile: Union[str, ConversionProfile] = ConversionProfile.BALANCED,
        options: Optional[ConversionOptions] = None
    ) -> ConversionResult:
        """
        Convert an asset for a target engine.

        Args:
            asset_path: Path to source asset
            target_engine: Target engine (unity, unreal, godot, web, blender)
            profile: Conversion profile (quality, balanced, optimized)
            options: Optional conversion options

        Returns:
            ConversionResult with conversion details
        """
        start_time = time.time()

        # Normalize inputs
        asset_path = Path(asset_path)
        if isinstance(target_engine, str):
            target_engine = TargetEngine(target_engine)
        if isinstance(profile, str):
            profile = ConversionProfile(profile)

        # Create result object
        result = ConversionResult(
            success=False,
            source_path=str(asset_path),
            target_engine=target_engine.value,
            profile=profile.value,
            source_format=asset_path.suffix.lower().lstrip("."),
        )

        # Validate source file exists
        if not asset_path.exists():
            result.loss_status = ConversionLossStatus.FAILED
            result.errors.append(f"Source file not found: {asset_path}")
            return result

        # Get file size
        result.file_size_original = asset_path.stat().st_size

        # Detect asset type
        asset_type = self._detect_asset_type(asset_path)

        # Get profile settings
        profile_settings = self._get_profile_settings(profile)

        # Merge options
        if options is None:
            options = ConversionOptions()

        # A texture adapter may request an explicit output format. This keeps
        # the default path shape stable while allowing real image conversion.
        requested_texture_format = None
        if asset_type == AssetType.TEXTURE:
            requested_texture_format = options.custom_options.get("target_format")

        # Create output directory
        output_dir = self.output_base / target_engine.value
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine output path (preserve directory structure if asset is in source_dir)
        try:
            relative_path = asset_path.relative_to(self.source_dir)
            output_path = output_dir / relative_path
        except ValueError:
            # Asset is not in source_dir, just use filename
            output_path = output_dir / asset_path.name

        if requested_texture_format:
            normalized_format = str(requested_texture_format).lower().lstrip(".")
            output_path = output_path.with_suffix(f".{normalized_format}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.target_format = output_path.suffix.lower().lstrip(".")

        # Perform conversion based on asset type and target engine
        try:
            if asset_type == AssetType.MODEL_3D:
                self._convert_model(asset_path, output_path, target_engine, profile_settings, options, result)
            elif asset_type == AssetType.TEXTURE:
                self._convert_texture(asset_path, output_path, target_engine, profile_settings, options, result)
            elif asset_type == AssetType.ANIMATION:
                self._convert_animation(asset_path, output_path, target_engine, profile_settings, options, result)
            else:
                result.loss_status = ConversionLossStatus.UNSUPPORTED
                result.errors.append(f"Unsupported asset type: {asset_type}")
                return result

            if not output_path.exists():
                result.loss_status = ConversionLossStatus.FAILED
                result.errors.append(f"Conversion adapter did not produce output: {output_path}")
                return result

            from .validation import validate_output

            validation = validate_output(output_path)
            result.metadata["output_validation"] = validation.to_dict()
            if not validation.valid:
                result.loss_status = ConversionLossStatus.FAILED
                result.errors.extend(validation.errors)
                return result

            result.success = True
            result.output_path = str(output_path)

            # Calculate metrics
            if output_path.exists():
                result.file_size_output = output_path.stat().st_size
                if result.file_size_original > 0:
                    result.compression_ratio = result.file_size_output / result.file_size_original

        except ConversionUnsupportedError as error:
            result.loss_status = ConversionLossStatus.UNSUPPORTED
            result.errors.append(str(error))
        except Exception as e:
            result.loss_status = ConversionLossStatus.FAILED
            result.errors.append(f"Conversion failed: {str(e)}")

        # Calculate processing time
        result.processing_time_ms = (time.time() - start_time) * 1000

        return result

    def _convert_model(
        self,
        source: Path,
        output: Path,
        target_engine: TargetEngine,
        settings: Dict,
        options: ConversionOptions,
        result: ConversionResult
    ):
        """Convert an OBJ asset through the native geometry path."""
        if source.suffix.lower() != ".obj" or output.suffix.lower() != ".obj":
            raise ConversionUnsupportedError(
                "Only OBJ-to-OBJ model conversion is currently validated"
            )

        from ..forge_3d._native import load_native

        native = load_native()
        rust_mesh = native.load_obj(str(source))
        if target_engine == TargetEngine.UNITY:
            native.export_for_unity(rust_mesh, str(output))
        elif target_engine == TargetEngine.UNREAL:
            native.export_for_unreal(rust_mesh, str(output))
        elif target_engine == TargetEngine.GODOT:
            native.export_for_godot(rust_mesh, str(output))
        else:
            rust_mesh.export_obj(str(output))

        result.loss_status = ConversionLossStatus.REINTERPRETED
        result.loss_reasons.append(
            "OBJ groups, smoothing, and material semantics are not preserved"
        )
        result.optimizations_applied.append("native_obj_reimport_export")
        result.metadata.update(
            {
                "adapter": "native_obj",
                "source_vertex_count": rust_mesh.vertex_count,
                "source_triangle_count": rust_mesh.triangle_count,
            }
        )

    def _convert_texture(
        self,
        source: Path,
        output: Path,
        target_engine: TargetEngine,
        settings: Dict,
        options: ConversionOptions,
        result: ConversionResult
    ):
        """Convert a texture through Pillow with explicit loss reporting."""
        from PIL import Image

        target_format = output.suffix.lower().lstrip(".")
        format_names = {
            "png": "PNG",
            "jpg": "JPEG",
            "jpeg": "JPEG",
            "webp": "WEBP",
            "tif": "TIFF",
            "tiff": "TIFF",
            "bmp": "BMP",
        }
        save_format = format_names.get(target_format)
        if save_format is None:
            raise ConversionUnsupportedError(
                f"Image output format '.{target_format}' is not validated"
            )

        with Image.open(source) as image:
            image.load()
            source_mode = image.mode
            if save_format == "JPEG" and source_mode not in {"RGB", "L"}:
                raise ConversionUnsupportedError(
                    f"JPEG output does not support source mode {source_mode}"
                )

            save_options = {}
            if save_format == "JPEG":
                save_options = {"quality": 95, "subsampling": 0}
            elif save_format == "WEBP":
                save_options = {"lossless": True}
            image.save(output, format=save_format, **save_options)

        result.metadata.update(
            {
                "adapter": "pillow_image",
                "source_mode": source_mode,
                "target_format": save_format,
            }
        )
        if save_format == "JPEG":
            result.loss_status = ConversionLossStatus.LOSSY
            result.loss_reasons.append("JPEG encoding is lossy")
        else:
            result.loss_status = ConversionLossStatus.REINTERPRETED
            result.loss_reasons.append(
                "Pixel data is preserved, but ancillary image metadata is not guaranteed"
            )

    def _convert_animation(
        self,
        source: Path,
        output: Path,
        target_engine: TargetEngine,
        settings: Dict,
        options: ConversionOptions,
        result: ConversionResult
    ):
        """Convert animation asset."""
        raise ConversionUnsupportedError(
            f"Animation conversion for {target_engine.value} is not implemented; "
            "use a validated media adapter instead of copying the source"
        )

    def batch_convert(
        self,
        asset_path: Union[str, Path],
        target_engines: List[Union[str, TargetEngine]],
        profile: Union[str, ConversionProfile] = ConversionProfile.BALANCED,
        options: Optional[ConversionOptions] = None
    ) -> Dict[str, ConversionResult]:
        """
        Convert a single asset for multiple target engines.

        Args:
            asset_path: Path to source asset
            target_engines: List of target engines
            profile: Conversion profile
            options: Optional conversion options

        Returns:
            Dictionary mapping engine name to ConversionResult
        """
        results = {}

        for engine in target_engines:
            if isinstance(engine, str):
                engine = TargetEngine(engine)

            result = self.convert(asset_path, engine, profile, options)
            results[engine.value] = result

        return results

    def convert_project(
        self,
        source_dir: Optional[Union[str, Path]] = None,
        target_engines: Optional[List[Union[str, TargetEngine]]] = None,
        profile: Union[str, ConversionProfile] = ConversionProfile.BALANCED,
        parallel: bool = False,
        workers: int = 4,
        file_filter: Optional[callable] = None
    ) -> Dict[str, List[ConversionResult]]:
        """
        Convert an entire project directory.

        Args:
            source_dir: Source directory to convert (defaults to self.source_dir)
            target_engines: List of target engines
            profile: Conversion profile
            parallel: Whether to use parallel processing
            workers: Number of parallel workers
            file_filter: Optional filter function for files

        Returns:
            Dictionary mapping engine name to list of ConversionResults
        """
        if source_dir is None:
            source_dir = self.source_dir
        else:
            source_dir = Path(source_dir)

        if target_engines is None:
            target_engines = [TargetEngine.UNITY, TargetEngine.UNREAL, TargetEngine.WEB]

        results = {engine.value if isinstance(engine, TargetEngine) else engine: []
                   for engine in target_engines}

        # Find all assets
        asset_files = []
        for pattern in ['**/*.fbx', '**/*.obj', '**/*.gltf', '**/*.png', '**/*.tga']:
            asset_files.extend(source_dir.glob(pattern))

        # Apply filter if provided
        if file_filter:
            asset_files = [f for f in asset_files if file_filter(f)]

        # Convert each asset
        for asset_file in asset_files:
            batch_results = self.batch_convert(asset_file, target_engines, profile)

            for engine, result in batch_results.items():
                results[engine].append(result)

        return results


def main():
    """Example usage of AssetConverter."""
    converter = AssetConverter(
        source_dir="assets/source",
        output_base="assets/engines"
    )

    # Example: Convert a model for Unity
    result = converter.convert(
        asset_path="assets/source/models/character.fbx",
        target_engine=TargetEngine.UNITY,
        profile=ConversionProfile.BALANCED
    )

    print(f"Conversion {'succeeded' if result.success else 'failed'}")
    if result.output_path:
        print(f"Output: {result.output_path}")
    if result.errors:
        print(f"Errors: {result.errors}")


if __name__ == "__main__":
    main()
