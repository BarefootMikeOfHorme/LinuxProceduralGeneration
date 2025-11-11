"""
Parameter Optimizer Agent - Autonomous generation parameter tuning

This agent autonomously optimizes generation parameters (steps, CFG, sampler, etc.)
based on output type, attempt history, and quality requirements.

Capabilities:
- Adjusts parameters based on asset complexity
- Tunes for speed vs quality tradeoffs
- Selects optimal sampler for output type
- Adapts parameters based on failure patterns
- Learns successful parameter combinations
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from .base_agent import (
    BaseAgent,
    AgentDecision,
    AgentCapability,
    EscalationReason,
)

logger = logging.getLogger(__name__)


@dataclass
class ParameterOptimization:
    """Result of parameter optimization"""
    original_params: Dict[str, Any]
    optimized_params: Dict[str, Any]
    changes_made: List[str]
    confidence: float
    reasoning: str
    expected_improvement: float  # 0.0-1.0 estimate


class ParameterOptimizerAgent(BaseAgent):
    """
    Autonomous parameter optimization agent.

    Optimizes generation parameters without requiring main AI consultation.
    """

    def __init__(
        self,
        min_confidence_threshold: float = 0.7,
        learning_enabled: bool = True,
        metrics_path: Optional[Path] = None,
    ):
        """
        Initialize Parameter Optimizer Agent.

        Args:
            min_confidence_threshold: Minimum confidence to auto-apply optimizations
            learning_enabled: Enable learning from successful optimizations
            metrics_path: Path to save metrics
        """
        super().__init__(
            name="Parameter Optimizer",
            capabilities=[AgentCapability.PARAMETER_TUNING],
        )

        self.confidence_threshold = min_confidence_threshold
        self.learning_enabled = learning_enabled
        self.metrics_path = metrics_path

        # Parameter ranges and recommendations
        self.parameter_specs = {
            "steps": {
                "min": 15,
                "max": 100,
                "optimal_ranges": {
                    "draft": (15, 25),
                    "standard": (25, 35),
                    "high_quality": (35, 50),
                    "ultra": (50, 100),
                },
            },
            "cfg_scale": {
                "min": 1.0,
                "max": 20.0,
                "optimal_ranges": {
                    "loose": (3.0, 5.0),
                    "balanced": (7.0, 9.0),
                    "strict": (10.0, 15.0),
                },
            },
            "denoise_strength": {
                "min": 0.0,
                "max": 1.0,
                "optimal_ranges": {
                    "subtle": (0.1, 0.3),
                    "moderate": (0.4, 0.6),
                    "strong": (0.7, 0.9),
                },
            },
        }

        # Sampler recommendations by use case
        self.sampler_recommendations = {
            # Speed priority
            "fast": ["Euler a", "DPM++ 2M", "LCM"],

            # Quality priority
            "quality": ["DPM++ 2M Karras", "DPM++ SDE Karras", "UniPC"],

            # Specific use cases
            "photorealistic": ["DPM++ 2M Karras", "DPM++ SDE Karras"],
            "anime": ["Euler a", "DPM++ 2M"],
            "artistic": ["DPM++ SDE Karras", "DDIM"],
            "iterative": ["Euler a", "Heun"],

            # Default fallback
            "default": ["DPM++ 2M Karras"],
        }

        # Track successful parameter combinations
        self.successful_params: Dict[str, List[Dict[str, Any]]] = {}

    def optimize_parameters(
        self,
        current_params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        attempt_num: int = 1,
        failed_metrics: Optional[Dict[str, float]] = None,
    ) -> ParameterOptimization:
        """
        Optimize generation parameters based on context and failures.

        Args:
            current_params: Current generation parameters
            context: Context (output_type, style, quality_level, etc.)
            attempt_num: Current attempt number (for retry logic)
            failed_metrics: Quality metrics from failed attempt

        Returns:
            ParameterOptimization with optimized params and reasoning
        """
        optimized = current_params.copy()
        changes = []
        reasoning_parts = []

        # Extract context
        output_type = context.get("output_type", "standard") if context else "standard"
        quality_level = context.get("quality_level", "standard") if context else "standard"
        style = context.get("style") if context else None
        is_hero = context.get("is_hero_asset", False) if context else False
        time_budget = context.get("time_budget", "balanced") if context else "balanced"

        # 1. Adjust for retry attempts
        if attempt_num > 1:
            step_increase = self._calculate_retry_adjustment(attempt_num, "steps")
            if "steps" in optimized:
                old_steps = optimized["steps"]
                optimized["steps"] = min(
                    optimized["steps"] + step_increase,
                    self.parameter_specs["steps"]["max"]
                )
                if optimized["steps"] != old_steps:
                    changes.append(f"steps: {old_steps} → {optimized['steps']}")
                    reasoning_parts.append(f"Increased steps for attempt #{attempt_num}")

            # Adjust CFG slightly on retry
            if "cfg_scale" in optimized:
                old_cfg = optimized["cfg_scale"]
                optimized["cfg_scale"] = min(
                    optimized["cfg_scale"] + 0.5,
                    self.parameter_specs["cfg_scale"]["max"]
                )
                if optimized["cfg_scale"] != old_cfg:
                    changes.append(f"cfg_scale: {old_cfg:.1f} → {optimized['cfg_scale']:.1f}")
                    reasoning_parts.append("Increased CFG for stronger guidance")

        # 2. Optimize based on output type
        if output_type in ["character", "hero"]:
            # Characters need more detail
            if "steps" not in optimized or optimized.get("steps", 20) < 30:
                old = optimized.get("steps", 20)
                optimized["steps"] = 35
                changes.append(f"steps: {old} → 35")
                reasoning_parts.append("Character assets need more detail steps")

        elif output_type in ["background", "environment"]:
            # Can use fewer steps for backgrounds
            if "steps" in optimized and optimized["steps"] > 30:
                old = optimized["steps"]
                optimized["steps"] = 28
                changes.append(f"steps: {old} → 28")
                reasoning_parts.append("Background assets can use fewer steps")

        elif output_type in ["texture", "material"]:
            # Textures need good quality but not extreme
            if "steps" not in optimized:
                optimized["steps"] = 30
                changes.append("steps: → 30")
                reasoning_parts.append("Standard texture quality")

        # 3. Adjust for quality level
        if quality_level == "draft":
            if "steps" in optimized and optimized["steps"] > 25:
                old = optimized["steps"]
                optimized["steps"] = 20
                changes.append(f"steps: {old} → 20")
                reasoning_parts.append("Draft quality - reduced steps")

        elif quality_level in ["high", "ultra"]:
            if "steps" in optimized and optimized["steps"] < 35:
                old = optimized["steps"]
                optimized["steps"] = 40 if quality_level == "high" else 50
                changes.append(f"steps: {old} → {optimized['steps']}")
                reasoning_parts.append(f"{quality_level} quality - increased steps")

        # 4. Hero assets get priority treatment
        if is_hero:
            if "steps" in optimized and optimized["steps"] < 40:
                old = optimized["steps"]
                optimized["steps"] = 45
                changes.append(f"steps: {old} → 45")
                reasoning_parts.append("Hero asset - maximum quality")

        # 5. Optimize sampler selection
        sampler_change = self._optimize_sampler(optimized, style, time_budget, output_type)
        if sampler_change:
            changes.append(sampler_change)
            reasoning_parts.append("Optimized sampler selection")

        # 6. Adjust based on failed metrics
        if failed_metrics:
            metric_adjustments = self._adjust_for_failures(optimized, failed_metrics)
            changes.extend(metric_adjustments)
            if metric_adjustments:
                reasoning_parts.append("Adjusted for quality failures")

        # 7. Time budget optimization
        if time_budget == "fast":
            # Reduce steps, use faster sampler
            if "steps" in optimized and optimized["steps"] > 25:
                old = optimized["steps"]
                optimized["steps"] = max(20, optimized["steps"] - 10)
                changes.append(f"steps: {old} → {optimized['steps']}")
                reasoning_parts.append("Fast mode - reduced steps")

        # Calculate confidence and expected improvement
        confidence = self._calculate_optimization_confidence(
            current_params,
            optimized,
            changes,
            context,
            attempt_num,
        )

        expected_improvement = self._estimate_improvement(changes, failed_metrics)

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No optimization needed"

        # Track decision
        decision = AgentDecision(
            action="OPTIMIZE" if changes else "KEEP",
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "original_params": current_params,
                "optimized_params": optimized,
                "changes": changes,
            }
        )
        self.record_decision(decision)

        return ParameterOptimization(
            original_params=current_params,
            optimized_params=optimized,
            changes_made=changes,
            confidence=confidence,
            reasoning=reasoning,
            expected_improvement=expected_improvement,
        )

    def _calculate_retry_adjustment(self, attempt_num: int, param_name: str) -> int:
        """Calculate how much to adjust parameter on retry"""
        if param_name == "steps":
            # Increase steps by 5 per attempt, cap at 20 total increase
            return min((attempt_num - 1) * 5, 20)
        return 0

    def _optimize_sampler(
        self,
        params: Dict[str, Any],
        style: Optional[str],
        time_budget: str,
        output_type: str,
    ) -> Optional[str]:
        """Optimize sampler selection"""
        current_sampler = params.get("sampler")

        # Determine optimal sampler
        if time_budget == "fast":
            recommended = self.sampler_recommendations["fast"]
        elif style and style in self.sampler_recommendations:
            recommended = self.sampler_recommendations[style]
        elif output_type == "character":
            recommended = self.sampler_recommendations["quality"]
        else:
            recommended = self.sampler_recommendations["default"]

        # Pick first recommendation if current isn't in list
        optimal_sampler = recommended[0]

        if current_sampler != optimal_sampler:
            params["sampler"] = optimal_sampler
            return f"sampler: {current_sampler} → {optimal_sampler}"

        return None

    def _adjust_for_failures(
        self,
        params: Dict[str, Any],
        failed_metrics: Dict[str, float]
    ) -> List[str]:
        """Adjust parameters based on quality failures"""
        adjustments = []

        # Low overall quality - increase steps and CFG
        if failed_metrics.get("overall_quality", 1.0) < 0.5:
            if "steps" in params and params["steps"] < 40:
                old = params["steps"]
                params["steps"] = min(params["steps"] + 10, 50)
                adjustments.append(f"steps: {old} → {params['steps']} (low quality)")

            if "cfg_scale" in params and params["cfg_scale"] < 9.0:
                old = params["cfg_scale"]
                params["cfg_scale"] = min(params["cfg_scale"] + 1.0, 12.0)
                adjustments.append(f"cfg_scale: {old:.1f} → {params['cfg_scale']:.1f} (low quality)")

        # Weak prompt alignment - increase CFG
        if failed_metrics.get("prompt_alignment", 1.0) < 0.7:
            if "cfg_scale" in params and params["cfg_scale"] < 10.0:
                old = params["cfg_scale"]
                params["cfg_scale"] = min(params["cfg_scale"] + 1.5, 12.0)
                adjustments.append(f"cfg_scale: {old:.1f} → {params['cfg_scale']:.1f} (alignment)")

        return adjustments

    def _calculate_optimization_confidence(
        self,
        original: Dict[str, Any],
        optimized: Dict[str, Any],
        changes: List[str],
        context: Optional[Dict[str, Any]],
        attempt_num: int,
    ) -> float:
        """Calculate confidence in optimization"""
        confidence = 0.6  # Base confidence

        # More changes = higher confidence (we know what to adjust)
        confidence += min(len(changes) * 0.05, 0.2)

        # Retries = higher confidence (we know something failed)
        if attempt_num > 1:
            confidence += 0.1

        # If we have clear context, higher confidence
        if context:
            if "output_type" in context:
                confidence += 0.05
            if "quality_level" in context:
                confidence += 0.05

        return min(max(confidence, 0.0), 1.0)

    def _estimate_improvement(
        self,
        changes: List[str],
        failed_metrics: Optional[Dict[str, float]]
    ) -> float:
        """Estimate expected quality improvement (0.0-1.0)"""
        if not changes:
            return 0.0

        # Base improvement per change
        improvement = len(changes) * 0.05

        # Higher improvement if we're addressing specific failures
        if failed_metrics:
            severe_failures = sum(1 for v in failed_metrics.values() if isinstance(v, (int, float)) and v < 0.5)
            improvement += severe_failures * 0.1

        return min(improvement, 0.5)  # Cap at 50% expected improvement

    def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """
        Make decision (required by BaseAgent).
        For Parameter Optimizer, the decision is made in optimize_parameters().
        """
        current_params = context.get("current_params", {})
        attempt_num = context.get("attempt_num", 1)
        failed_metrics = context.get("failed_metrics")

        optimization = self.optimize_parameters(
            current_params,
            context=context,
            attempt_num=attempt_num,
            failed_metrics=failed_metrics,
        )

        return AgentDecision(
            action="OPTIMIZE" if optimization.changes_made else "KEEP",
            confidence=optimization.confidence,
            reasoning=optimization.reasoning,
            metadata={
                "optimized_params": optimization.optimized_params,
                "changes": optimization.changes_made,
                "expected_improvement": optimization.expected_improvement,
            },
            escalation_reason=EscalationReason.LOW_CONFIDENCE if optimization.confidence < self.confidence_threshold else None,
        )

    def calculate_confidence(
        self,
        context: Dict[str, Any],
        proposed_action: str
    ) -> float:
        """Calculate confidence for proposed action"""
        return self._calculate_optimization_confidence(
            original=context.get("current_params", {}),
            optimized=context.get("optimized_params", {}),
            changes=context.get("changes", []),
            context=context,
            attempt_num=context.get("attempt_num", 1),
        )
