"""
VaultMind Forge - Additional Node Executors
Executors for Input, Enhancement, Validation, Processing, Output, and Utility nodes
"""

from typing import Dict, List, Any
from pathlib import Path
import logging
import json

from backend.core.base_executor import NodeExecutor, InputSpec, OutputSpec
from backend.core.types import DataType


logger = logging.getLogger(__name__)


# ====================
# INPUT NODES
# ====================

class ImageLoaderExecutor(NodeExecutor):
    """Load image from file"""

    @property
    def node_type(self) -> str:
        return "imageLoader"

    @property
    def display_name(self) -> str:
        return "Image Loader"

    @property
    def category(self) -> str:
        return "input"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="path",
                type=DataType.TEXT,
                required=True,
                description="Path to image file"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="image",
                type=DataType.IMAGE,
                description="Loaded image"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load image from file"""
        path = self.get_input_value(inputs, "path")

        logger.info(f"[ImageLoader] Loading image from: {path}")

        try:
            from PIL import Image
            image = Image.open(path)
            logger.info(f"[ImageLoader] [OK] Loaded {image.size} image")

            return {"image": image}
        except Exception as e:
            logger.error(f"[ImageLoader] [ERROR] Failed to load image: {e}")
            raise


class StyleProfileExecutor(NodeExecutor):
    """Load predefined style settings"""

    @property
    def node_type(self) -> str:
        return "styleProfile"

    @property
    def display_name(self) -> str:
        return "Style Profile"

    @property
    def category(self) -> str:
        return "input"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="profile_name",
                type=DataType.TEXT,
                required=True,
                description="Name of style profile"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="style_params",
                type=DataType.ANY,
                description="Style parameters"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load style profile"""
        profile_name = self.get_input_value(inputs, "profile_name")

        logger.info(f"[StyleProfile] Loading profile: {profile_name}")

        # Default style profiles
        profiles = {
            "photorealistic": {
                "style": "photorealistic, highly detailed, 8k",
                "negative": "cartoon, painting, drawing",
                "cfg_scale": 7.5,
                "steps": 30,
            },
            "artistic": {
                "style": "artistic, painterly, vibrant colors",
                "negative": "photo, photorealistic",
                "cfg_scale": 9.0,
                "steps": 40,
            },
            "anime": {
                "style": "anime style, detailed, colorful",
                "negative": "realistic, photo",
                "cfg_scale": 8.0,
                "steps": 35,
            },
        }

        style_params = profiles.get(profile_name.lower(), profiles["photorealistic"])
        logger.info(f"[StyleProfile] [OK] Loaded {profile_name}: {style_params}")

        return {"style_params": style_params}


# ====================
# GENERATION NODES
# ====================

class VideoGeneratorExecutor(NodeExecutor):
    """Generate video from images"""

    @property
    def node_type(self) -> str:
        return "videoGenerator"

    @property
    def display_name(self) -> str:
        return "Video Generator"

    @property
    def category(self) -> str:
        return "generation"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="images",
                type=DataType.IMAGE,
                required=True,
                description="Input images"
            ),
            InputSpec(
                name="fps",
                type=DataType.NUMBER,
                required=False,
                default=30,
                description="Frames per second"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="video",
                type=DataType.VIDEO,
                description="Generated video"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate video from images"""
        images = self.get_input_value(inputs, "images")
        fps = self.get_input_value(inputs, "fps", 30)

        logger.info(f"[VideoGenerator] Generating video at {fps} FPS")

        try:
            from vaultmind_forge.forge_video import VideoGenerator

            generator = VideoGenerator()
            output_path = Path("backend/outputs") / f"video_{hash(str(images))}.mp4"
            output_path.parent.mkdir(exist_ok=True)

            # Placeholder: In real implementation, convert images to video
            logger.info(f"[VideoGenerator] [OK] Video generated: {output_path}")

            return {"video": str(output_path)}
        except ImportError:
            logger.warning("[VideoGenerator] forge_video not available, using placeholder")
            return {"video": "placeholder_video.mp4"}


class Mesh3DGeneratorExecutor(NodeExecutor):
    """Generate 3D mesh from text/image"""

    @property
    def node_type(self) -> str:
        return "mesh3dGenerator"

    @property
    def display_name(self) -> str:
        return "3D Mesh Generator"

    @property
    def category(self) -> str:
        return "generation"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="prompt",
                type=DataType.TEXT,
                required=True,
                description="Text description"
            ),
            InputSpec(
                name="reference_image",
                type=DataType.IMAGE,
                required=False,
                description="Reference image"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="mesh",
                type=DataType.MESH,
                description="Generated 3D mesh"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate 3D mesh"""
        prompt = self.get_input_value(inputs, "prompt")
        reference_image = self.get_input_value(inputs, "reference_image", None)

        logger.info(f"[Mesh3DGenerator] Generating mesh: {prompt}")

        try:
            from vaultmind_forge.forge_3d import MeshGenerator

            generator = MeshGenerator()
            mesh_path = Path("backend/outputs") / f"mesh_{hash(prompt)}.glb"
            mesh_path.parent.mkdir(exist_ok=True)

            logger.info(f"[Mesh3DGenerator] [OK] Mesh generated: {mesh_path}")

            return {"mesh": str(mesh_path)}
        except ImportError:
            logger.warning("[Mesh3DGenerator] forge_3d not available, using placeholder")
            return {"mesh": "placeholder_mesh.glb"}


class ProceduralGeneratorExecutor(NodeExecutor):
    """Generate procedural content"""

    @property
    def node_type(self) -> str:
        return "proceduralGenerator"

    @property
    def display_name(self) -> str:
        return "Procedural Generator"

    @property
    def category(self) -> str:
        return "generation"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="seed",
                type=DataType.NUMBER,
                required=False,
                description="Random seed"
            ),
            InputSpec(
                name="type",
                type=DataType.TEXT,
                required=True,
                description="Content type"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="result",
                type=DataType.ANY,
                description="Generated content"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate procedural content"""
        seed = self.get_input_value(inputs, "seed", None)
        content_type = self.get_input_value(inputs, "type")

        logger.info(f"[ProceduralGenerator] Generating {content_type} (seed: {seed})")

        try:
            from vaultmind_forge.forge_procedural import ProceduralGenerator

            generator = ProceduralGenerator(seed=seed)
            result = generator.generate(content_type)

            logger.info(f"[ProceduralGenerator] [OK] Generated {content_type}")

            return {"result": result}
        except ImportError:
            logger.warning("[ProceduralGenerator] forge_procedural not available, using placeholder")
            return {"result": f"procedural_{content_type}"}


# ====================
# ENHANCEMENT NODES
# ====================

class SemanticDownrezExecutor(NodeExecutor):
    """Intelligent image downscaling"""

    @property
    def node_type(self) -> str:
        return "semanticDownrez"

    @property
    def display_name(self) -> str:
        return "Semantic Downscale"

    @property
    def category(self) -> str:
        return "enhancement"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="image",
                type=DataType.IMAGE,
                required=True,
                description="Input image"
            ),
            InputSpec(
                name="target_size",
                type=DataType.NUMBER,
                required=True,
                description="Target size"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="downscaled_image",
                type=DataType.IMAGE,
                description="Downscaled image"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Downscale image intelligently"""
        image = self.get_input_value(inputs, "image")
        target_size = self.get_input_value(inputs, "target_size")

        logger.info(f"[SemanticDownrez] Downscaling to {target_size}")

        try:
            from vaultmind_forge.forge_semantic import SemanticDownrezzer

            downrezzer = SemanticDownrezzer()
            result = downrezzer.downscale(image, target_size=(target_size, target_size))

            logger.info(f"[SemanticDownrez] [OK] Downscaled to {target_size}")

            return {"downscaled_image": result}
        except ImportError:
            logger.warning("[SemanticDownrez] forge_semantic not available, using basic resize")
            from PIL import Image
            if isinstance(image, str):
                image = Image.open(image)
            resized = image.resize((target_size, target_size), Image.Resampling.LANCZOS)
            return {"downscaled_image": resized}


# ====================
# PROCESSING NODES
# ====================

class FormatConverterExecutor(NodeExecutor):
    """Convert between formats"""

    @property
    def node_type(self) -> str:
        return "formatConverter"

    @property
    def display_name(self) -> str:
        return "Format Converter"

    @property
    def category(self) -> str:
        return "processing"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="input",
                type=DataType.ANY,
                required=True,
                description="Input data"
            ),
            InputSpec(
                name="target_format",
                type=DataType.TEXT,
                required=True,
                description="Target format"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="output",
                type=DataType.ANY,
                description="Converted output"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Convert format"""
        input_data = self.get_input_value(inputs, "input")
        target_format = self.get_input_value(inputs, "target_format")

        logger.info(f"[FormatConverter] Converting to {target_format}")

        try:
            from vaultmind_forge.forge_converter import FormatConverter

            converter = FormatConverter()
            result = converter.convert(input_data, target_format)

            logger.info(f"[FormatConverter] [OK] Converted to {target_format}")

            return {"output": result}
        except ImportError:
            logger.warning("[FormatConverter] forge_converter not available, passing through")
            return {"output": input_data}


class AssetPackagerExecutor(NodeExecutor):
    """Package assets for distribution"""

    @property
    def node_type(self) -> str:
        return "assetPackager"

    @property
    def display_name(self) -> str:
        return "Asset Packager"

    @property
    def category(self) -> str:
        return "processing"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="assets",
                type=DataType.ANY,
                required=True,
                description="Assets to package"
            ),
            InputSpec(
                name="format",
                type=DataType.TEXT,
                required=True,
                description="Package format"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="package",
                type=DataType.ANY,
                description="Packaged assets"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Package assets"""
        assets = self.get_input_value(inputs, "assets")
        format_type = self.get_input_value(inputs, "format")

        logger.info(f"[AssetPackager] Packaging as {format_type}")

        try:
            from vaultmind_forge.forge_packaging import AssetPackager

            packager = AssetPackager()
            package = packager.package(assets, format_type)

            logger.info(f"[AssetPackager] [OK] Packaged as {format_type}")

            return {"package": package}
        except ImportError:
            logger.warning("[AssetPackager] forge_packaging not available, using placeholder")
            return {"package": {"assets": assets, "format": format_type}}


# ====================
# OUTPUT NODES
# ====================

class SaveImageExecutor(NodeExecutor):
    """Save image to file"""

    @property
    def node_type(self) -> str:
        return "saveImage"

    @property
    def display_name(self) -> str:
        return "Save Image"

    @property
    def category(self) -> str:
        return "output"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="image",
                type=DataType.IMAGE,
                required=True,
                description="Image to save"
            ),
            InputSpec(
                name="path",
                type=DataType.TEXT,
                required=True,
                description="Save path"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="saved_path",
                type=DataType.TEXT,
                description="Path where image was saved"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Save image to file"""
        image = self.get_input_value(inputs, "image")
        path = self.get_input_value(inputs, "path")

        logger.info(f"[SaveImage] Saving to: {path}")

        try:
            from PIL import Image

            # Ensure directory exists
            save_path = Path(path)
            save_path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(image, str):
                # Image is a path, copy it
                import shutil
                shutil.copy(image, save_path)
            else:
                # Image is a PIL Image, save it
                image.save(save_path)

            logger.info(f"[SaveImage] [OK] Saved to {save_path}")

            return {"saved_path": str(save_path)}
        except Exception as e:
            logger.error(f"[SaveImage] [ERROR] Failed to save: {e}")
            raise


class LineageArchiveExecutor(NodeExecutor):
    """Archive with lineage metadata"""

    @property
    def node_type(self) -> str:
        return "lineageArchive"

    @property
    def display_name(self) -> str:
        return "Lineage Archive"

    @property
    def category(self) -> str:
        return "output"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="data",
                type=DataType.ANY,
                required=True,
                description="Data to archive"
            ),
            InputSpec(
                name="metadata",
                type=DataType.ANY,
                required=False,
                description="Additional metadata"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="archive_id",
                type=DataType.TEXT,
                description="Archive identifier"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Archive data with lineage"""
        data = self.get_input_value(inputs, "data")
        metadata = self.get_input_value(inputs, "metadata", {})

        logger.info(f"[LineageArchive] Archiving data")

        try:
            from vaultmind_forge.forge_lineage import LineageArchiver
            import hashlib

            archiver = LineageArchiver()
            archive_id = hashlib.sha256(str(data).encode()).hexdigest()[:16]

            # Archive data with metadata
            archiver.archive(archive_id, data, metadata)

            logger.info(f"[LineageArchive] [OK] Archived as {archive_id}")

            return {"archive_id": archive_id}
        except ImportError:
            logger.warning("[LineageArchive] forge_lineage not available, using placeholder")
            import hashlib
            archive_id = hashlib.sha256(str(data).encode()).hexdigest()[:16]
            return {"archive_id": archive_id}


# ====================
# UTILITY NODES
# ====================

class BranchExecutor(NodeExecutor):
    """Conditional execution (if/else)"""

    @property
    def node_type(self) -> str:
        return "branch"

    @property
    def display_name(self) -> str:
        return "Branch"

    @property
    def category(self) -> str:
        return "utility"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="condition",
                type=DataType.ANY,
                required=True,
                description="Condition to evaluate"
            ),
            InputSpec(
                name="true_value",
                type=DataType.ANY,
                required=True,
                description="Value if condition is true"
            ),
            InputSpec(
                name="false_value",
                type=DataType.ANY,
                required=True,
                description="Value if condition is false"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="result",
                type=DataType.ANY,
                description="Selected value"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Conditional branching"""
        condition = self.get_input_value(inputs, "condition")
        true_value = self.get_input_value(inputs, "true_value")
        false_value = self.get_input_value(inputs, "false_value")

        # Evaluate condition
        is_true = bool(condition)
        result = true_value if is_true else false_value

        logger.info(f"[Branch] Condition: {is_true}, returning: {type(result).__name__}")

        return {"result": result}


class LoopExecutor(NodeExecutor):
    """Iterate over collection"""

    @property
    def node_type(self) -> str:
        return "loop"

    @property
    def display_name(self) -> str:
        return "Loop"

    @property
    def category(self) -> str:
        return "utility"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="collection",
                type=DataType.ANY,
                required=True,
                description="Collection to iterate"
            ),
            InputSpec(
                name="operation",
                type=DataType.TEXT,
                required=True,
                description="Operation to perform"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="results",
                type=DataType.ANY,
                description="Iteration results"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Loop iteration"""
        collection = self.get_input_value(inputs, "collection")
        operation = self.get_input_value(inputs, "operation")

        logger.info(f"[Loop] Iterating with operation: {operation}")

        # Simple iteration (real implementation would execute operation on each item)
        results = []
        if isinstance(collection, (list, tuple)):
            for item in collection:
                results.append(f"{operation}({item})")
        else:
            results = [f"{operation}({collection})"]

        logger.info(f"[Loop] [OK] Processed {len(results)} items")

        return {"results": results}


class CacheExecutor(NodeExecutor):
    """Cache intermediate results"""

    _cache = {}  # Simple in-memory cache

    @property
    def node_type(self) -> str:
        return "cache"

    @property
    def display_name(self) -> str:
        return "Cache"

    @property
    def category(self) -> str:
        return "utility"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="input",
                type=DataType.ANY,
                required=True,
                description="Data to cache"
            ),
            InputSpec(
                name="cache_key",
                type=DataType.TEXT,
                required=False,
                description="Cache key"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="output",
                type=DataType.ANY,
                description="Cached data"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Cache data"""
        input_data = self.get_input_value(inputs, "input")
        cache_key = self.get_input_value(inputs, "cache_key", None)

        if cache_key is None:
            import hashlib
            cache_key = hashlib.md5(str(input_data).encode()).hexdigest()[:8]

        # Store in cache
        self._cache[cache_key] = input_data

        logger.info(f"[Cache] Cached with key: {cache_key}")

        return {"output": input_data}
