"""
VaultMind Forge - AI Control Framework

Intelligent AI-driven decision making throughout the asset pipeline:
- Quality assessment with confidence scoring
- Automatic parameter adjustment
- Smart retry strategies
- Human-in-loop when needed
- Learning from corrections
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import numpy as np


class AuthorityLevel(Enum):
    """AI authority levels"""
    FULL_AUTONOMOUS = "full_autonomous"    # AI decides everything
    HIGH_AUTONOMY = "high_autonomy"        # AI decides most, human reviews edge cases
    SUPERVISED = "supervised"              # AI suggests, human approves
    ADVISORY_ONLY = "advisory_only"        # AI only provides recommendations


class DecisionOutcome(Enum):
    """Possible decision outcomes"""
    APPROVED = "approved"
    REJECTED = "rejected"
    RETRY = "retry"
    FLAG_FOR_REVIEW = "flag_for_review"
    ESCALATE = "escalate"


@dataclass
class Decision:
    """Record of an AI decision"""
    decision_id: str
    decision_type: str
    timestamp: datetime
    input_data: Dict[str, Any]
    output: str
    confidence: float
    reasoning: str
    ai_method: str
    execution_time_ms: float
    human_reviewed: bool = False
    human_override: Optional[str] = None
    was_correct: Optional[bool] = None  # Filled in by feedback


@dataclass
class QualityMetrics:
    """Asset quality metrics for AI assessment"""
    sharpness: float
    anatomy: float  # For characters/organic
    prompt_alignment: float
    color_fidelity: float
    artifact_score: float  # 1.0 = no artifacts
    consistency: float
    overall_score: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "sharpness": self.sharpness,
            "anatomy": self.anatomy,
            "prompt_alignment": self.prompt_alignment,
            "color_fidelity": self.color_fidelity,
            "artifact_score": self.artifact_score,
            "consistency": self.consistency,
            "overall_score": self.overall_score
        }


class AIDecisionEngine:
    """
    Core AI decision engine for asset pipeline.
    Makes intelligent decisions based on quality metrics, context, and learned policies.
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        authority_level: AuthorityLevel = AuthorityLevel.HIGH_AUTONOMY,
        logger: Optional[logging.Logger] = None
    ):
        self.config = self._load_config(config_path) if config_path else {}
        self.authority_level = authority_level
        self.logger = logger or self._setup_logger()

        # Load thresholds from config
        thresholds = self.config.get("confidence_thresholds", {})
        self.threshold_auto_approve = thresholds.get("auto_approve", 0.85)
        self.threshold_auto_fix = thresholds.get("auto_fix", 0.75)
        self.threshold_flag = thresholds.get("flag_for_review", 0.60)
        self.threshold_reject = thresholds.get("auto_reject", 0.40)

        # Decision history for learning
        self.decision_history: List[Decision] = []

        # Performance tracking
        self.stats = {
            "total_decisions": 0,
            "auto_approved": 0,
            "flagged_for_review": 0,
            "auto_rejected": 0,
            "human_overrides": 0,
            "correct_predictions": 0
        }

    def _setup_logger(self) -> logging.Logger:
        """Set up default logger"""
        logger = logging.getLogger("VaultMindForge.AIControl")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)
        return logger

    def _load_config(self, config_path: Path) -> Dict:
        """Load AI control configuration"""
        with open(config_path, 'r') as f:
            return json.load(f)

    def assess_quality(
        self,
        asset_path: Path,
        metrics: QualityMetrics,
        context: Dict[str, Any]
    ) -> Tuple[DecisionOutcome, float, str]:
        """
        Assess asset quality and make autonomous decision.

        Args:
            asset_path: Path to asset being evaluated
            metrics: Quality metrics computed by validators
            context: Additional context (job type, requirements, etc.)

        Returns:
            (outcome, confidence, reasoning)
        """
        start_time = datetime.now()

        # Calculate overall confidence based on metrics
        confidence = self._calculate_confidence(metrics, context)

        # Make decision based on confidence and authority level
        outcome, reasoning = self._make_quality_decision(
            metrics, confidence, context
        )

        # Record decision
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        decision = Decision(
            decision_id=f"quality_{datetime.now().timestamp()}",
            decision_type="quality_assessment",
            timestamp=datetime.now(),
            input_data={
                "asset": str(asset_path),
                "metrics": metrics.to_dict(),
                "context": context
            },
            output=outcome.value,
            confidence=confidence,
            reasoning=reasoning,
            ai_method="ensemble",
            execution_time_ms=execution_time
        )
        self.decision_history.append(decision)
        self.stats["total_decisions"] += 1

        # Log decision
        self.logger.info(
            f"Quality assessment: {outcome.value} "
            f"(confidence: {confidence:.2f}) - {reasoning}"
        )

        return outcome, confidence, reasoning

    def _calculate_confidence(
        self,
        metrics: QualityMetrics,
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for decision.
        Uses ensemble of metric scores with contextual weighting.
        """
        # Base confidence from overall score
        base_confidence = metrics.overall_score

        # Adjust based on critical metrics
        critical_metrics = []

        # Check if any critical metric is failing
        if metrics.artifact_score < 0.8:
            critical_metrics.append("artifacts_detected")
        if metrics.prompt_alignment < 0.7:
            critical_metrics.append("poor_prompt_alignment")

        # Reduce confidence if critical failures
        if critical_metrics:
            base_confidence *= 0.7

        # Boost confidence if all metrics strong
        if all([
            metrics.sharpness > 0.8,
            metrics.artifact_score > 0.9,
            metrics.prompt_alignment > 0.85,
            metrics.consistency > 0.8
        ]):
            base_confidence = min(1.0, base_confidence * 1.1)

        # Context-based adjustments
        if context.get("is_hero_asset"):
            # Require higher confidence for hero assets
            base_confidence *= 0.9

        if context.get("attempt_number", 1) > 3:
            # Lower confidence if multiple retries already
            base_confidence *= 0.95

        return max(0.0, min(1.0, base_confidence))

    def _make_quality_decision(
        self,
        metrics: QualityMetrics,
        confidence: float,
        context: Dict[str, Any]
    ) -> Tuple[DecisionOutcome, str]:
        """
        Make quality decision based on confidence and metrics.

        Returns:
            (outcome, reasoning)
        """
        # Check authority level
        if self.authority_level == AuthorityLevel.ADVISORY_ONLY:
            return DecisionOutcome.FLAG_FOR_REVIEW, "Advisory mode - human approval required"

        # Check for hero assets requiring approval
        if context.get("is_hero_asset") and self.authority_level != AuthorityLevel.FULL_AUTONOMOUS:
            return DecisionOutcome.FLAG_FOR_REVIEW, "Hero asset - human review required by policy"

        # Decision tree based on confidence
        if confidence >= self.threshold_auto_approve:
            self.stats["auto_approved"] += 1
            return DecisionOutcome.APPROVED, self._explain_approval(metrics, confidence)

        elif confidence >= self.threshold_flag:
            self.stats["flagged_for_review"] += 1
            return DecisionOutcome.FLAG_FOR_REVIEW, self._explain_flag(metrics, confidence)

        elif confidence >= self.threshold_reject:
            # Between reject and flag - try to fix
            if self._can_auto_fix(metrics):
                return DecisionOutcome.RETRY, self._explain_retry(metrics)
            else:
                self.stats["flagged_for_review"] += 1
                return DecisionOutcome.FLAG_FOR_REVIEW, self._explain_flag(metrics, confidence)

        else:
            self.stats["auto_rejected"] += 1
            return DecisionOutcome.REJECTED, self._explain_rejection(metrics, confidence)

    def _explain_approval(self, metrics: QualityMetrics, confidence: float) -> str:
        """Generate explanation for approval"""
        strong_points = []
        if metrics.sharpness > 0.85:
            strong_points.append("excellent sharpness")
        if metrics.artifact_score > 0.9:
            strong_points.append("clean (no artifacts)")
        if metrics.prompt_alignment > 0.85:
            strong_points.append("strong prompt alignment")

        return f"Auto-approved (confidence: {confidence:.2f}). {', '.join(strong_points)}"

    def _explain_flag(self, metrics: QualityMetrics, confidence: float) -> str:
        """Generate explanation for flagging"""
        concerns = []
        if metrics.sharpness < 0.7:
            concerns.append(f"sharpness low ({metrics.sharpness:.2f})")
        if metrics.artifact_score < 0.8:
            concerns.append(f"artifacts detected ({metrics.artifact_score:.2f})")
        if metrics.prompt_alignment < 0.7:
            concerns.append(f"prompt alignment weak ({metrics.prompt_alignment:.2f})")

        return f"Flagged for review (confidence: {confidence:.2f}). Concerns: {', '.join(concerns)}"

    def _explain_rejection(self, metrics: QualityMetrics, confidence: float) -> str:
        """Generate explanation for rejection"""
        failures = []
        if metrics.sharpness < 0.5:
            failures.append("critically low sharpness")
        if metrics.artifact_score < 0.6:
            failures.append("severe artifacts")
        if metrics.prompt_alignment < 0.5:
            failures.append("poor prompt match")

        return f"Auto-rejected (confidence: {confidence:.2f}). Failures: {', '.join(failures)}"

    def _explain_retry(self, metrics: QualityMetrics) -> str:
        """Generate explanation for retry with suggested fixes"""
        adjustments = self.suggest_parameter_adjustments(metrics)
        return f"Retry recommended. Suggested adjustments: {adjustments}"

    def _can_auto_fix(self, metrics: QualityMetrics) -> bool:
        """Determine if metrics suggest an auto-fixable issue"""
        # Can potentially fix with parameter adjustment
        fixable_issues = [
            (metrics.sharpness < 0.7 and metrics.sharpness > 0.5),  # Slightly blurry
            (metrics.prompt_alignment < 0.75 and metrics.prompt_alignment > 0.6),  # Weak alignment
        ]
        return any(fixable_issues)

    def suggest_parameter_adjustments(
        self,
        metrics: QualityMetrics
    ) -> Dict[str, Any]:
        """
        AI-driven parameter adjustment suggestions.
        Uses learned policy to suggest parameter changes.
        """
        adjustments = {}

        # Sharpness issues
        if metrics.sharpness < 0.7:
            adjustments["cfg_scale"] = "+1.0"  # Increase guidance
            adjustments["steps"] = "+5"  # More denoising steps
            adjustments["reasoning"] = "Low sharpness - increase guidance and steps"

        # Prompt alignment issues
        if metrics.prompt_alignment < 0.75:
            adjustments["cfg_scale"] = "+1.5"
            adjustments["prompt"] = "emphasize_keywords"
            adjustments["reasoning"] = "Weak prompt alignment - boost CFG and emphasize keywords"

        # Artifact issues
        if metrics.artifact_score < 0.8:
            adjustments["sampler"] = "dpm_2m"  # More stable sampler
            adjustments["steps"] = "+10"
            adjustments["reasoning"] = "Artifacts detected - use more stable sampler"

        # Color issues
        if metrics.color_fidelity < 0.7:
            adjustments["color_correction"] = "auto"
            adjustments["reasoning"] = "Poor color fidelity - apply auto color correction"

        return adjustments

    def select_best_variation(
        self,
        variations: List[Tuple[Path, QualityMetrics]],
        context: Dict[str, Any]
    ) -> Tuple[int, float, str]:
        """
        AI-driven selection of best variation from batch.

        Args:
            variations: List of (path, metrics) tuples
            context: Job context

        Returns:
            (winner_index, confidence, reasoning)
        """
        if not variations:
            raise ValueError("No variations provided")

        # Calculate scores with contextual weighting
        scores = []
        for path, metrics in variations:
            score = self._calculate_variation_score(metrics, context)
            scores.append(score)

        # Select winner
        winner_idx = int(np.argmax(scores))
        winner_score = scores[winner_idx]

        # Calculate confidence based on score separation
        score_array = np.array(scores)
        score_std = np.std(score_array)
        confidence = winner_score * (1.0 - score_std)  # High confidence if clear winner

        # Generate reasoning
        winner_metrics = variations[winner_idx][1]
        reasoning = self._explain_winner_selection(
            winner_idx, winner_metrics, scores, context
        )

        self.logger.info(
            f"Selected variation {winner_idx} with score {winner_score:.2f} "
            f"(confidence: {confidence:.2f})"
        )

        return winner_idx, confidence, reasoning

    def _calculate_variation_score(
        self,
        metrics: QualityMetrics,
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate weighted score for variation.
        Weights adjusted based on job context.
        """
        # Base weights
        weights = {
            "sharpness": 0.2,
            "anatomy": 0.15,
            "prompt_alignment": 0.25,
            "color_fidelity": 0.15,
            "artifact_score": 0.15,
            "consistency": 0.1
        }

        # Adjust weights based on context
        output_type = context.get("output_type", "")
        if output_type == "character":
            weights["anatomy"] = 0.25
            weights["sharpness"] = 0.15
        elif output_type == "environment":
            weights["consistency"] = 0.2
            weights["anatomy"] = 0.05

        # Calculate weighted score
        score = (
            metrics.sharpness * weights["sharpness"] +
            metrics.anatomy * weights["anatomy"] +
            metrics.prompt_alignment * weights["prompt_alignment"] +
            metrics.color_fidelity * weights["color_fidelity"] +
            metrics.artifact_score * weights["artifact_score"] +
            metrics.consistency * weights["consistency"]
        )

        return score

    def _explain_winner_selection(
        self,
        winner_idx: int,
        winner_metrics: QualityMetrics,
        all_scores: List[float],
        context: Dict[str, Any]
    ) -> str:
        """Generate explanation for winner selection"""
        winner_score = all_scores[winner_idx]
        avg_score = np.mean(all_scores)

        # Identify strongest metrics
        strong_metrics = []
        if winner_metrics.sharpness > 0.85:
            strong_metrics.append("sharpness")
        if winner_metrics.prompt_alignment > 0.85:
            strong_metrics.append("prompt alignment")
        if winner_metrics.artifact_score > 0.9:
            strong_metrics.append("artifact-free")

        return (
            f"Variation {winner_idx} selected with score {winner_score:.2f} "
            f"({((winner_score - avg_score) / avg_score * 100):.1f}% above average). "
            f"Strongest: {', '.join(strong_metrics)}"
        )

    def record_human_feedback(
        self,
        decision_id: str,
        was_correct: bool,
        human_override: Optional[str] = None
    ):
        """
        Record human feedback on AI decision for learning.

        Args:
            decision_id: ID of the decision being reviewed
            was_correct: Whether AI decision was correct
            human_override: If overridden, what human decided
        """
        for decision in self.decision_history:
            if decision.decision_id == decision_id:
                decision.human_reviewed = True
                decision.was_correct = was_correct
                decision.human_override = human_override

                if was_correct:
                    self.stats["correct_predictions"] += 1
                else:
                    self.logger.info(
                        f"Human correction recorded for {decision_id}: "
                        f"AI said {decision.output}, human chose {human_override}"
                    )

                if human_override:
                    self.stats["human_overrides"] += 1

                break

    def adapt_thresholds(self):
        """
        Adapt confidence thresholds based on performance.
        Called periodically to improve accuracy.
        """
        if not self.config.get("learning_feedback", {}).get("adapt_thresholds", False):
            return

        reviewed = [d for d in self.decision_history if d.human_reviewed]
        if len(reviewed) < 20:
            return  # Need more data

        # Analyze false positives (AI approved, human rejected)
        false_positives = [
            d for d in reviewed
            if d.output == "approved" and not d.was_correct
        ]

        if len(false_positives) > len(reviewed) * 0.1:  # >10% false positive rate
            # Increase approval threshold
            old_threshold = self.threshold_auto_approve
            self.threshold_auto_approve = min(0.95, self.threshold_auto_approve + 0.02)
            self.logger.info(
                f"Adapted auto_approve threshold: {old_threshold:.2f} -> "
                f"{self.threshold_auto_approve:.2f} (reducing false positives)"
            )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get AI performance statistics"""
        total = self.stats["total_decisions"]
        if total == 0:
            return self.stats

        reviewed = len([d for d in self.decision_history if d.human_reviewed])
        accuracy = (
            self.stats["correct_predictions"] / reviewed
            if reviewed > 0 else 0.0
        )

        return {
            **self.stats,
            "accuracy_rate": accuracy,
            "auto_approval_rate": self.stats["auto_approved"] / total,
            "flag_rate": self.stats["flagged_for_review"] / total,
            "rejection_rate": self.stats["auto_rejected"] / total,
            "override_rate": self.stats["human_overrides"] / reviewed if reviewed > 0 else 0,
            "decisions_reviewed": reviewed
        }

    def export_decisions(self, output_path: Path):
        """Export decision history for analysis"""
        decisions_data = []
        for d in self.decision_history:
            decisions_data.append({
                "decision_id": d.decision_id,
                "decision_type": d.decision_type,
                "timestamp": d.timestamp.isoformat(),
                "output": d.output,
                "confidence": d.confidence,
                "reasoning": d.reasoning,
                "ai_method": d.ai_method,
                "execution_time_ms": d.execution_time_ms,
                "human_reviewed": d.human_reviewed,
                "was_correct": d.was_correct,
                "human_override": d.human_override
            })

        with open(output_path, 'w') as f:
            json.dump({
                "stats": self.get_performance_summary(),
                "decisions": decisions_data
            }, f, indent=2)

        self.logger.info(f"Exported {len(decisions_data)} decisions to {output_path}")
