"""
SDXL Generator Node - Wraps forge_diffusion SDXL generator

Example of how to expose any forge_* module as a node.
"""

from ..base_node import (
    BaseNode,
    NodeInput,
    NodeOutput,
    NodeMetadata,
    NodeCategory,
    DataType,
)
from typing import Dict, Any


class SDXLGeneratorNode(BaseNode):
    """
    SDXL Image Generation Node

    Generates images using Stable Diffusion XL with full control over:
    - Prompt and negative prompt
    - Image dimensions
    - Generation parameters (steps, CFG, etc.)
    - ControlNet conditioning
    """

    METADATA = NodeMetadata(
        display_name="SDXL Generator",
        description="Generate high-quality images using Stable Diffusion XL",
        category=NodeCategory.GENERATION,
        help_text="""
        The SDXL Generator creates images from text prompts using SDXL.

        **Tips:**
        - Use detailed prompts for better results
        - Negative prompts help avoid unwanted elements
        - Higher steps = better quality but slower
        - CFG scale controls prompt adherence (7-9 is typical)

        **Keyboard Shortcuts:**
        - Ctrl+G: Generate preview
        - Ctrl+R: Regenerate with new seed
        - Ctrl+E: Edit prompt in external editor
        """,
        tutorial_url="https://docs.vaultmind.forge/nodes/sdxl-generator",
        shortcuts={
            "generate_preview": "Ctrl+G",
            "regenerate": "Ctrl+R",
            "edit_prompt": "Ctrl+E",
        },
        icon="🎨",
        color="#E91E63",
        ai_controllable=True,
    )

    INPUTS = [
        NodeInput(
            name="prompt",
            data_type=DataType.TEXT,
            description="Main prompt describing what to generate",
            required=True,
            tooltip="Describe your image in detail. Example: 'a majestic dragon perched on a mountain peak, fantasy art'",
            help_url="https://docs.vaultmind.forge/prompting-guide",
        ),
        NodeInput(
            name="negative_prompt",
            data_type=DataType.TEXT,
            description="Things to avoid in the image",
            required=False,
            default_value="ugly, blurry, low quality",
            tooltip="List unwanted elements separated by commas",
        ),
        NodeInput(
            name="width",
            data_type=DataType.NUMBER,
            description="Image width in pixels",
            default_value=1024,
            min_value=512,
            max_value=2048,
            tooltip="SDXL works best at 1024x1024",
        ),
        NodeInput(
            name="height",
            data_type=DataType.NUMBER,
            description="Image height in pixels",
            default_value=1024,
            min_value=512,
            max_value=2048,
        ),
        NodeInput(
            name="steps",
            data_type=DataType.NUMBER,
            description="Number of denoising steps",
            default_value=30,
            min_value=1,
            max_value=150,
            tooltip="More steps = higher quality but slower. 20-40 is good.",
        ),
        NodeInput(
            name="cfg_scale",
            data_type=DataType.NUMBER,
            description="Classifier-free guidance scale",
            default_value=7.5,
            min_value=1.0,
            max_value=20.0,
            tooltip="How closely to follow the prompt. 7-9 is typical.",
        ),
        NodeInput(
            name="seed",
            data_type=DataType.NUMBER,
            description="Random seed for reproducibility",
            default_value=-1,
            tooltip="-1 for random seed, or specific number for reproducible results",
        ),
        NodeInput(
            name="style_preset",
            data_type=DataType.TEXT,
            description="Style preset",
            default_value="none",
            options=["none", "anime", "photographic", "digital-art", "3d-model"],
            tooltip="Quick style presets. 'none' for custom styling.",
        ),
    ]

    OUTPUTS = [
        NodeOutput(
            name="image",
            data_type=DataType.IMAGE,
            description="Generated image",
            tooltip="The generated image (PIL Image format)",
        ),
        NodeOutput(
            name="metadata",
            data_type=DataType.ANY,
            description="Generation metadata (prompt, seed, etc.)",
            tooltip="Metadata for lineage tracking",
        ),
    ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SDXL generation"""
        import time
        start_time = time.time()

        # Validate inputs
        valid, errors = self.validate_inputs(inputs)
        if not valid:
            raise ValueError(f"Invalid inputs: {', '.join(errors)}")

        try:
            # Import actual generator (lazy import)
            from ...forge_diffusion.sdxl_generator import SDXLGenerator

            # Create generator instance
            generator = SDXLGenerator()

            # Generate image
            result = generator.generate(
                prompt=inputs["prompt"],
                negative_prompt=inputs.get("negative_prompt", ""),
                width=inputs.get("width", 1024),
                height=inputs.get("height", 1024),
                num_inference_steps=inputs.get("steps", 30),
                guidance_scale=inputs.get("cfg_scale", 7.5),
                seed=inputs.get("seed", -1),
            )

            # Track execution time
            self.execution_time_ms = (time.time() - start_time) * 1000

            # Return outputs
            return {
                "image": result["image"],
                "metadata": {
                    "prompt": inputs["prompt"],
                    "negative_prompt": inputs.get("negative_prompt"),
                    "seed": result.get("seed"),
                    "steps": inputs.get("steps"),
                    "cfg_scale": inputs.get("cfg_scale"),
                    "execution_time_ms": self.execution_time_ms,
                },
            }

        except Exception as e:
            self.last_error = str(e)
            raise RuntimeError(f"SDXL generation failed: {e}") from e
