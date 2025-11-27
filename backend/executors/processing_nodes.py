"""
VaultMind Forge - Processing Node Executors
Nodes that process and transform images/media
"""

from typing import Dict, List, Any
from pathlib import Path
import uuid
import logging

from backend.core.base_executor import NodeExecutor, InputSpec, OutputSpec
from backend.core.types import DataType


logger = logging.getLogger(__name__)


class SuperResolutionExecutor(NodeExecutor):
    """
    Super Resolution Node - Upscales images using AI.
    """

    @property
    def node_type(self) -> str:
        return "superResolution"

    @property
    def display_name(self) -> str:
        return "Super Resolution"

    @property
    def category(self) -> str:
        return "processing"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="image",
                type=DataType.IMAGE,
                required=True,
                description="Input image (file path)"
            ),
            InputSpec(
                name="scale",
                type=DataType.NUMBER,
                required=False,
                default=2,
                description="Upscale factor (2x, 4x)"
            ),
            InputSpec(
                name="quality",
                type=DataType.TEXT,
                required=False,
                default="balanced",
                description="Quality preset (fast, balanced, best)"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="image",
                type=DataType.IMAGE,
                description="Upscaled image (file path)"
            ),
            OutputSpec(
                name="metadata",
                type=DataType.DICT,
                description="Upscaling metadata"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Upscale image using AI super resolution"""
        from vaultmind_forge.forge_sr.upscaler import SuperResolutionUpscaler, SRQuality

        # Get inputs
        image_path = self.get_input_value(inputs, "image")
        scale = int(self.get_input_value(inputs, "scale", 2))
        quality_str = self.get_input_value(inputs, "quality", "balanced")

        # Convert quality string to enum
        quality_map = {
            "fast": SRQuality.FAST,
            "balanced": SRQuality.BALANCED,
            "best": SRQuality.BEST
        }
        quality = quality_map.get(quality_str, SRQuality.BALANCED)

        logger.info(f"Upscaling image:")
        logger.info(f"  Input: {image_path}")
        logger.info(f"  Scale: {scale}x, Quality: {quality_str}")

        # Initialize upscaler
        upscaler = SuperResolutionUpscaler()

        # Create output path
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"upscaled_{uuid.uuid4().hex[:8]}.png"

        # Upscale
        result = upscaler.upscale(
            input_path=Path(image_path),
            output_path=output_path,
            quality=quality
        )

        logger.info(f"  ✓ Upscaled: {output_path}")

        # Build metadata
        metadata = {
            "input_image": str(image_path),
            "scale_factor": result.scale_factor,
            "quality": quality_str,
            "input_resolution": f"{result.input_size[0]}x{result.input_size[1]}" if hasattr(result, 'input_size') else "unknown",
            "output_resolution": f"{result.output_size[0]}x{result.output_size[1]}" if hasattr(result, 'output_size') else "unknown",
        }

        return {
            "image": str(output_path),
            "metadata": metadata
        }


if __name__ == "__main__":
    executor = SuperResolutionExecutor()
    print(f"Super Resolution: {executor.node_type}")
    print(f"  Inputs: {[s.name for s in executor.input_spec]}")
    print(f"  Outputs: {[s.name for s in executor.output_spec]}")
