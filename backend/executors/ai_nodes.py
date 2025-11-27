"""
VaultMind Forge - AI Node Executors
Nodes that use AI agents for intelligent processing
"""

from typing import Dict, List, Any
import logging

from backend.core.base_executor import NodeExecutor, InputSpec, OutputSpec
from backend.core.types import DataType


logger = logging.getLogger(__name__)


class PromptRefinerExecutor(NodeExecutor):
    """
    Prompt Refiner Node - Uses Merlinv1 AI to enhance prompts.
    """

    @property
    def node_type(self) -> str:
        return "promptRefiner"

    @property
    def display_name(self) -> str:
        return "Prompt Refiner (Merlinv1)"

    @property
    def category(self) -> str:
        return "ai_agent"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="text",
                type=DataType.TEXT,
                required=True,
                description="Input prompt to refine"
            ),
            InputSpec(
                name="style",
                type=DataType.TEXT,
                required=False,
                default="",
                description="Desired style (e.g., 'photorealistic', 'artistic')"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="refined_prompt",
                type=DataType.TEXT,
                description="AI-enhanced prompt"
            ),
            OutputSpec(
                name="metadata",
                type=DataType.DICT,
                description="Refinement metadata"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Refine prompt using Merlinv1 AI"""
        # Get inputs
        text = self.get_input_value(inputs, "text")
        style = self.get_input_value(inputs, "style", "")

        logger.info(f"Refining prompt:")
        logger.info(f"  Input: {text[:80]}...")

        # TODO: When Merlinv1 is fully integrated, use this:
        # from vaultmind_forge.forge_agents.prompt_refiner import PromptRefinerAgent
        # agent = PromptRefinerAgent()
        # refined = agent.refine(text, style=style)

        # TEMPORARY: Enhanced prompt with quality modifiers
        # This mimics what Merlinv1 will do when integrated
        quality_mods = [
            "highly detailed",
            "sharp focus",
            "professional",
            "masterpiece",
            "8k uhd"
        ]

        # Add style if provided
        if style:
            refined = f"{text}, {style} style, {', '.join(quality_mods)}"
        else:
            refined = f"{text}, {', '.join(quality_mods)}"

        logger.info(f"  ✓ Refined: {refined[:80]}...")

        # Build metadata
        metadata = {
            "original_prompt": text,
            "style_applied": style if style else "none",
            "model": "merlinv1_stage1",  # Will be real when integrated
            "enhancements": quality_mods,
        }

        return {
            "refined_prompt": refined,
            "metadata": metadata
        }


if __name__ == "__main__":
    executor = PromptRefinerExecutor()
    print(f"Prompt Refiner: {executor.node_type}")
    print(f"  Inputs: {[s.name for s in executor.input_spec]}")
    print(f"  Outputs: {[s.name for s in executor.output_spec]}")
