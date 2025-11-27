"""
VaultMind Forge - Generation Node Executors
Nodes that generate images using AI models
"""

from typing import Dict, List, Any
from pathlib import Path
import uuid
import logging

from backend.core.base_executor import NodeExecutor, InputSpec, OutputSpec
from backend.core.types import DataType


logger = logging.getLogger(__name__)


class SDXLGeneratorExecutor(NodeExecutor):
    """
    SDXL Generator Node - Generates images using Stable Diffusion XL.
    """

    @property
    def node_type(self) -> str:
        return "sdxlGenerator"

    @property
    def display_name(self) -> str:
        return "SDXL Generator"

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
                description="Text prompt for image generation"
            ),
            InputSpec(
                name="negative_prompt",
                type=DataType.TEXT,
                required=False,
                default="",
                description="Negative prompt (what to avoid)"
            ),
            InputSpec(
                name="width",
                type=DataType.NUMBER,
                required=False,
                default=1024,
                description="Image width in pixels"
            ),
            InputSpec(
                name="height",
                type=DataType.NUMBER,
                required=False,
                default=1024,
                description="Image height in pixels"
            ),
            InputSpec(
                name="steps",
                type=DataType.NUMBER,
                required=False,
                default=30,
                description="Number of denoising steps"
            ),
            InputSpec(
                name="cfg_scale",
                type=DataType.NUMBER,
                required=False,
                default=7.5,
                description="Classifier-free guidance scale"
            ),
            InputSpec(
                name="seed",
                type=DataType.SEED,
                required=False,
                default=-1,
                description="Random seed (-1 for random)"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="image",
                type=DataType.IMAGE,
                description="Generated image (file path)"
            ),
            OutputSpec(
                name="metadata",
                type=DataType.DICT,
                description="Generation metadata"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate image using SDXL"""
        from vaultmind_forge.forge_diffusion.sdxl_generator import SDXLGenerator
        from vaultmind_forge.forge_diffusion.generator import GenerationConfig

        # Get inputs
        prompt = self.get_input_value(inputs, "prompt")
        negative_prompt = self.get_input_value(inputs, "negative_prompt", "")
        width = int(self.get_input_value(inputs, "width", 1024))
        height = int(self.get_input_value(inputs, "height", 1024))
        steps = int(self.get_input_value(inputs, "steps", 30))
        cfg_scale = float(self.get_input_value(inputs, "cfg_scale", 7.5))
        seed = int(self.get_input_value(inputs, "seed", -1))

        logger.info(f"Generating SDXL image:")
        logger.info(f"  Prompt: {prompt[:80]}...")
        logger.info(f"  Resolution: {width}x{height}")
        logger.info(f"  Steps: {steps}, CFG: {cfg_scale}")

        # Initialize generator
        generator = SDXLGenerator()
        generator.initialize()

        # Create config
        config = GenerationConfig(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=cfg_scale,
            seed=seed if seed >= 0 else None
        )

        # Generate
        result = generator.generate(config)

        # Save image
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        image_path = output_dir / f"sdxl_{uuid.uuid4().hex[:8]}.png"
        result.images[0].save(image_path)

        logger.info(f"  ✓ Generated: {image_path}")

        # Build metadata
        metadata = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "resolution": f"{width}x{height}",
            "steps": steps,
            "cfg_scale": cfg_scale,
            "seed": result.seed if hasattr(result, 'seed') else seed,
            "model": "stabilityai/stable-diffusion-xl-base-1.0",
        }

        return {
            "image": str(image_path),
            "metadata": metadata
        }


if __name__ == "__main__":
    executor = SDXLGeneratorExecutor()
    print(f"SDXL Generator: {executor.node_type}")
    print(f"  Inputs: {[s.name for s in executor.input_spec]}")
    print(f"  Outputs: {[s.name for s in executor.output_spec]}")
