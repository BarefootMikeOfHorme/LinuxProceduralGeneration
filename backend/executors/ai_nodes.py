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

        logger.info(f"[PromptRefiner] Refining prompt:")
        logger.info(f"  Input: {text[:80]}...")

        # Use PromptRefinerAgent with Merlinv1
        try:
            from vaultmind_forge.forge_agents.prompt_refiner import PromptRefinerAgent

            # Create agent (will auto-load Merlinv1 if available)
            agent = PromptRefinerAgent(
                use_merlinv1=True,
                min_confidence_threshold=0.7,
            )

            # Refine the prompt
            refinement = agent.refine_prompt(
                original_prompt=text,
                style=style if style else None,
            )

            refined = refinement.refined_prompt
            method = "merlinv1_ai" if agent.merlinv1_available else "rule_based"

            logger.info(f"  [OK] Refined ({method}): {refined[:80]}...")
            logger.info(f"       Confidence: {refinement.confidence:.2f}")
            logger.info(f"       Reasoning: {refinement.reasoning}")

            # Build metadata
            metadata = {
                "original_prompt": text,
                "style_applied": style if style else "none",
                "method": method,
                "model": "merlinv1_stage1" if agent.merlinv1_available else "rule_based",
                "confidence": refinement.confidence,
                "reasoning": refinement.reasoning,
                "refinements_added": refinement.refinements_added,
                "negative_prompt": refinement.negative_prompt,
            }

            return {
                "refined_prompt": refined,
                "metadata": metadata
            }

        except Exception as e:
            # Fallback to basic enhancement if agent fails
            logger.error(f"[PromptRefiner] Agent failed, using fallback: {e}")

            quality_mods = ["highly detailed", "sharp focus", "professional"]
            if style:
                refined = f"{text}, {style} style, {', '.join(quality_mods)}"
            else:
                refined = f"{text}, {', '.join(quality_mods)}"

            metadata = {
                "original_prompt": text,
                "style_applied": style if style else "none",
                "method": "fallback",
                "model": "fallback",
                "enhancements": quality_mods,
                "error": str(e),
            }

            return {
                "refined_prompt": refined,
                "metadata": metadata
            }


class ParameterOptimizerExecutor(NodeExecutor):
    """
    Parameter Optimizer Node - Autonomous parameter tuning agent.
    Optimizes generation parameters based on context and quality requirements.
    """

    @property
    def node_type(self) -> str:
        return "parameterOptimizer"

    @property
    def display_name(self) -> str:
        return "Parameter Optimizer (Agent)"

    @property
    def category(self) -> str:
        return "ai_agent"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="current_params",
                type=DataType.DICT,
                required=True,
                description="Current generation parameters (steps, cfg_scale, sampler, etc.)"
            ),
            InputSpec(
                name="output_type",
                type=DataType.TEXT,
                required=False,
                default="standard",
                description="Asset type: character, background, texture, standard"
            ),
            InputSpec(
                name="quality_level",
                type=DataType.TEXT,
                required=False,
                default="standard",
                description="Quality level: draft, standard, high, ultra"
            ),
            InputSpec(
                name="attempt_num",
                type=DataType.NUMBER,
                required=False,
                default=1,
                description="Current attempt number (for retry logic)"
            ),
            InputSpec(
                name="is_hero_asset",
                type=DataType.BOOLEAN,
                required=False,
                default=False,
                description="Is this a hero/showcase asset?"
            ),
            InputSpec(
                name="time_budget",
                type=DataType.TEXT,
                required=False,
                default="balanced",
                description="Time budget: fast, balanced, quality"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="optimized_params",
                type=DataType.DICT,
                description="Optimized generation parameters"
            ),
            OutputSpec(
                name="metadata",
                type=DataType.DICT,
                description="Optimization metadata (changes, reasoning, confidence)"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize parameters using ParameterOptimizerAgent"""
        # Get inputs
        current_params = self.get_input_value(inputs, "current_params")
        output_type = self.get_input_value(inputs, "output_type", "standard")
        quality_level = self.get_input_value(inputs, "quality_level", "standard")
        attempt_num = int(self.get_input_value(inputs, "attempt_num", 1))
        is_hero_asset = self.get_input_value(inputs, "is_hero_asset", False)
        time_budget = self.get_input_value(inputs, "time_budget", "balanced")

        logger.info(f"[ParameterOptimizer] Optimizing parameters:")
        logger.info(f"  Type: {output_type}, Quality: {quality_level}, Attempt: {attempt_num}")

        try:
            from vaultmind_forge.forge_agents.parameter_optimizer import ParameterOptimizerAgent

            # Create agent
            agent = ParameterOptimizerAgent()

            # Build context
            context = {
                "output_type": output_type,
                "quality_level": quality_level,
                "is_hero_asset": is_hero_asset,
                "time_budget": time_budget,
            }

            # Optimize parameters
            optimization = agent.optimize_parameters(
                current_params=current_params,
                context=context,
                attempt_num=attempt_num,
            )

            logger.info(f"  [OK] Parameters optimized:")
            logger.info(f"       Confidence: {optimization.confidence:.2f}")
            logger.info(f"       Changes: {len(optimization.changes_made)}")
            for change in optimization.changes_made:
                logger.info(f"         - {change}")

            # Build metadata
            metadata = {
                "original_params": optimization.original_params,
                "changes_made": optimization.changes_made,
                "confidence": optimization.confidence,
                "reasoning": optimization.reasoning,
                "expected_improvement": optimization.expected_improvement,
            }

            return {
                "optimized_params": optimization.optimized_params,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"[ParameterOptimizer] Agent failed: {e}")
            # Fallback: return original params
            return {
                "optimized_params": current_params,
                "metadata": {
                    "error": str(e),
                    "fallback": True,
                }
            }


class QualityGuardianExecutor(NodeExecutor):
    """
    Quality Guardian Node - Autonomous quality assessment and fixing agent.
    Analyzes images and automatically fixes common quality issues.
    """

    @property
    def node_type(self) -> str:
        return "qualityGuardian"

    @property
    def display_name(self) -> str:
        return "Quality Guardian (Agent)"

    @property
    def category(self) -> str:
        return "ai_agent"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="image",
                type=DataType.IMAGE,
                required=True,
                description="Image to assess quality"
            ),
            InputSpec(
                name="auto_fix",
                type=DataType.BOOLEAN,
                required=False,
                default=True,
                description="Automatically fix detected issues"
            ),
            InputSpec(
                name="quality_threshold",
                type=DataType.NUMBER,
                required=False,
                default=0.7,
                description="Minimum acceptable quality (0.0-1.0)"
            ),
            InputSpec(
                name="prompt",
                type=DataType.TEXT,
                required=False,
                default="",
                description="Original prompt (for alignment checking)"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="image",
                type=DataType.IMAGE,
                description="Fixed image (if auto_fix enabled)"
            ),
            OutputSpec(
                name="decision",
                type=DataType.TEXT,
                description="Quality decision: APPROVE, FIX, RETRY, REJECT"
            ),
            OutputSpec(
                name="quality_score",
                type=DataType.NUMBER,
                description="Overall quality score (0.0-1.0)"
            ),
            OutputSpec(
                name="metadata",
                type=DataType.DICT,
                description="Quality report with metrics, issues, and fixes"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Assess and fix image quality using QualityGuardianAgent"""
        # Get inputs
        image = self.get_input_value(inputs, "image")
        auto_fix = self.get_input_value(inputs, "auto_fix", True)
        quality_threshold = float(self.get_input_value(inputs, "quality_threshold", 0.7))
        prompt = self.get_input_value(inputs, "prompt", "")

        logger.info(f"[QualityGuardian] Assessing image quality (threshold: {quality_threshold:.2f})")

        try:
            from vaultmind_forge.forge_agents.quality_guardian import QualityGuardianAgent

            # Create agent
            agent = QualityGuardianAgent(
                min_quality_threshold=quality_threshold,
                auto_fix_enabled=auto_fix,
            )

            # Assess quality
            decision = agent.assess_quality(
                asset_path=image,  # Can be PIL Image or path
                prompt=prompt if prompt else None,
            )

            logger.info(f"  [OK] Quality assessed:")
            logger.info(f"       Score: {decision.overall_quality:.2f}")
            logger.info(f"       Decision: {decision.action}")
            logger.info(f"       Issues found: {len(decision.issues)}")

            # Get fixed image if auto-fix applied
            output_image = image
            fixes_applied = []

            if auto_fix and decision.fixes_to_apply:
                logger.info(f"       Applying {len(decision.fixes_to_apply)} fixes...")
                fixed_image, report = agent.apply_fixes(image, decision.fixes_to_apply)
                output_image = fixed_image
                fixes_applied = report.fixes_applied
                logger.info(f"       Quality after fixes: {report.after_quality:.2f}")

            # Build metadata
            metadata = {
                "quality_score": decision.overall_quality,
                "decision": decision.action,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "issues_found": len(decision.issues),
                "issues": [
                    {
                        "type": issue.issue_type,
                        "severity": issue.severity,
                        "description": issue.description,
                    }
                    for issue in decision.issues
                ],
                "fixes_applied": fixes_applied,
                "metrics": decision.metrics,
            }

            return {
                "image": output_image,
                "decision": decision.action,
                "quality_score": decision.overall_quality,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"[QualityGuardian] Agent failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: return original image with low confidence
            return {
                "image": image,
                "decision": "UNKNOWN",
                "quality_score": 0.5,
                "metadata": {
                    "error": str(e),
                    "fallback": True,
                }
            }


if __name__ == "__main__":
    # Test executors
    executors = [
        PromptRefinerExecutor(),
        ParameterOptimizerExecutor(),
        QualityGuardianExecutor(),
    ]

    for executor in executors:
        print(f"{executor.display_name}: {executor.node_type}")
        print(f"  Inputs: {[s.name for s in executor.input_spec]}")
        print(f"  Outputs: {[s.name for s in executor.output_spec]}")
        print()
