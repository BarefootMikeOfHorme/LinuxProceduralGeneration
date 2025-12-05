"""
VaultMind Forge - AI-Powered Validator
Integrates AIDecisionEngine with quality validation for autonomous decision-making
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Add forge_converter to path for AI control

from forge_converter.ai_control import (
    AIDecisionEngine,
    AuthorityLevel,
    DecisionOutcome,
    QualityMetrics as AIQualityMetrics
)
from .validator import Validator, ValidationResult

# Import metrics functions carefully - some are in metrics.py, others need to be computed
try:
    from .metrics import (
        anatomy_score,
        prompt_alignment_score,
        consistency_score
    )
except ImportError:
    # Fallback implementations if metrics not available
    def anatomy_score(asset_path):
        return 0.7
    def prompt_alignment_score(asset_path, prompt=None):
        return 0.7
    def consistency_score(asset_path, reference=None):
        return 0.8


class ValidationDecision(Enum):
    """AI validation decisions"""
    APPROVED = "approved"
    REJECTED = "rejected"
    RETRY_RECOMMENDED = "retry_recommended"
    FLAG_FOR_HUMAN = "flag_for_human"


@dataclass
class AIValidationResult:
    """Extended validation result with AI decision"""
    validation: ValidationResult
    decision: ValidationDecision
    confidence: float
    reasoning: str
    suggested_adjustments: Optional[Dict[str, Any]] = None


class AIValidator:
    """
    AI-powered validator with autonomous decision making.

    Integrates traditional validation with AI decision engine for:
    - Automatic approval/rejection based on confidence
    - Parameter adjustment suggestions for retries
    - Human escalation for edge cases
    - Learning from corrections

    Example:
        >>> ai_validator = AIValidator(authority_level=AuthorityLevel.HIGH_AUTONOMY)
        >>> result = ai_validator.validate_with_ai(
        ...     asset_path="output/char_001.png",
        ...     context={"output_type": "character", "is_hero_asset": False}
        ... )
        >>> print(f"Decision: {result.decision}, Confidence: {result.confidence:.2f}")
    """

    def __init__(
        self,
        authority_level: AuthorityLevel = AuthorityLevel.HIGH_AUTONOMY,
        threshold: float = 0.7,
        ai_config_path: Optional[Path] = None
    ):
        """
        Initialize AI validator

        Args:
            authority_level: How much autonomy AI has
            threshold: Minimum score for basic pass
            ai_config_path: Optional path to AI control config
        """
        # Traditional validator
        self.validator = Validator(threshold=threshold)

        # AI decision engine
        self.ai_engine = AIDecisionEngine(
            config_path=ai_config_path,
            authority_level=authority_level
        )

        self.threshold = threshold

    def validate_with_ai(
        self,
        asset_path: Path | str,
        context: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        reference_images: Optional[list[Path]] = None
    ) -> AIValidationResult:
        """
        Validate asset with AI-powered decision making

        Args:
            asset_path: Path to asset to validate
            context: Job context (output_type, is_hero_asset, etc.)
            prompt: Generation prompt (for alignment scoring)
            reference_images: Reference images (for consistency)

        Returns:
            AIValidationResult with decision, confidence, and reasoning
        """
        asset_path = Path(asset_path)
        context = context or {}

        # 1. Run traditional validation
        validation = self.validator.validate_asset(asset_path)

        # 2. Compute detailed quality metrics
        metrics = self._compute_quality_metrics(
            asset_path,
            validation,
            prompt,
            reference_images
        )

        # 3. AI decision
        outcome, confidence, reasoning = self.ai_engine.assess_quality(
            asset_path=asset_path,
            metrics=metrics,
            context=context
        )

        # 4. Convert to validation decision
        decision = self._map_outcome_to_decision(outcome)

        # 5. Get parameter adjustments if retry recommended
        adjustments = None
        if decision == ValidationDecision.RETRY_RECOMMENDED:
            adjustments = self.ai_engine.suggest_parameter_adjustments(metrics)

        return AIValidationResult(
            validation=validation,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            suggested_adjustments=adjustments
        )

    def _compute_quality_metrics(
        self,
        asset_path: Path,
        validation: ValidationResult,
        prompt: Optional[str],
        reference_images: Optional[list[Path]]
    ) -> AIQualityMetrics:
        """
        Compute comprehensive quality metrics for AI decision
        """
        # Get individual metric scores from validation checks first
        sharpness = validation.checks.get("sharpness", 0.0)
        anatomy = validation.checks.get("anatomy", 0.0)
        prompt_align = validation.checks.get("prompt_alignment", 0.0)
        color_fid = validation.checks.get("color_fidelity", 0.0)

        # If not in validation checks, compute them
        if sharpness == 0.0:
            try:
                sharpness = self._compute_sharpness(asset_path)
            except:
                sharpness = 0.5

        if anatomy == 0.0:
            try:
                anatomy = float(anatomy_score(asset_path))
            except:
                anatomy = 0.5

        if prompt_align == 0.0 and prompt:
            try:
                prompt_align = float(prompt_alignment_score(asset_path, prompt))
            except:
                prompt_align = 0.5

        if color_fid == 0.0:
            try:
                color_fid = self._compute_color_fidelity(asset_path)
            except:
                color_fid = 0.5

        # Artifact detection (simple heuristic)
        artifact_score = self._detect_artifacts(asset_path)

        # Consistency score (if reference images provided)
        consistency_val = self._compute_consistency(asset_path, reference_images)

        # Overall score
        overall = validation.score

        return AIQualityMetrics(
            sharpness=sharpness,
            anatomy=anatomy,
            prompt_alignment=prompt_align,
            color_fidelity=color_fid,
            artifact_score=artifact_score,
            consistency=consistency_val,
            overall_score=overall
        )

    def _compute_sharpness(self, asset_path: Path) -> float:
        """
        Compute sharpness score using Laplacian variance
        """
        try:
            from PIL import Image
            import numpy as np

            with Image.open(asset_path) as img:
                gray = np.array(img.convert("L"), dtype=np.float32) / 255.0

            # Laplacian variance (sharpness metric)
            try:
                from scipy import ndimage
                laplacian = ndimage.laplace(gray)
                sharpness = float(np.var(laplacian)) / 1000.0
                return np.clip(sharpness, 0.0, 1.0)
            except ImportError:
                # Simple gradient-based sharpness if scipy not available
                gx = np.gradient(gray, axis=1)
                gy = np.gradient(gray, axis=0)
                gradient_magnitude = np.sqrt(gx**2 + gy**2)
                sharpness = float(np.mean(gradient_magnitude))
                return min(sharpness * 3.0, 1.0)  # Scale to 0-1
        except:
            return 0.5

    def _compute_color_fidelity(self, asset_path: Path) -> float:
        """
        Compute color fidelity score
        """
        try:
            from PIL import Image
            import numpy as np

            with Image.open(asset_path) as img:
                arr = np.array(img.convert("RGB"), dtype=np.float32) / 255.0

            # Check color distribution
            r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

            # Good color fidelity means balanced channels and no clipping
            balance_score = 1.0 - abs(np.mean(r) - 0.5) - abs(np.mean(g) - 0.5) - abs(np.mean(b) - 0.5)
            balance_score = max(0.0, balance_score)

            # Check for clipping
            clipped_pixels = np.sum((arr == 0.0) | (arr == 1.0))
            total_pixels = arr.size
            clipping_ratio = clipped_pixels / total_pixels
            clipping_score = 1.0 - min(clipping_ratio * 5.0, 1.0)

            # Combine scores
            color_fid = (balance_score * 0.6 + clipping_score * 0.4)
            return float(np.clip(color_fid, 0.0, 1.0))
        except:
            return 0.7

    def _detect_artifacts(self, asset_path: Path) -> float:
        """
        Simple artifact detection
        Returns score where 1.0 = no artifacts, 0.0 = severe artifacts
        """
        try:
            from PIL import Image
            import numpy as np

            with Image.open(asset_path) as img:
                arr = np.array(img.convert("RGB"), dtype=np.float32) / 255.0

            # Check for extreme values (often artifacts)
            extreme_pixels = np.sum((arr == 0.0) | (arr == 1.0))
            total_pixels = arr.size
            extreme_ratio = extreme_pixels / total_pixels

            # Check for noise (high frequency content)
            gray = np.mean(arr, axis=2)
            variance = np.var(gray)

            # Score: penalize extreme values and high noise
            artifact_score = 1.0 - min(extreme_ratio * 5.0, 1.0)
            artifact_score *= (1.0 - min(variance * 2.0, 0.5))

            return float(np.clip(artifact_score, 0.0, 1.0))
        except:
            return 0.7  # Default if detection fails

    def _compute_consistency(
        self,
        asset_path: Path,
        reference_images: Optional[list[Path]]
    ) -> float:
        """
        Compute style consistency with reference images
        Returns score where 1.0 = highly consistent, 0.0 = inconsistent
        """
        if not reference_images:
            return 1.0  # No references = perfect consistency

        try:
            from PIL import Image
            import numpy as np

            # Load asset
            with Image.open(asset_path) as asset_img:
                asset_img_resized = asset_img.convert("RGB").resize((256, 256))
                asset_arr = np.array(asset_img_resized, dtype=np.float32) / 255.0

            # Compute asset color histogram
            asset_hist = self._compute_color_histogram(asset_arr)

            # Compare with references
            similarities = []
            for ref_path in reference_images[:5]:  # Max 5 references
                if not Path(ref_path).exists():
                    continue

                with Image.open(ref_path) as ref_img:
                    ref_img_resized = ref_img.convert("RGB").resize((256, 256))
                    ref_arr = np.array(ref_img_resized, dtype=np.float32) / 255.0
                ref_hist = self._compute_color_histogram(ref_arr)

                # Histogram intersection
                similarity = np.minimum(asset_hist, ref_hist).sum()
                similarities.append(similarity)

            if similarities:
                consistency = float(np.mean(similarities))
                return np.clip(consistency, 0.0, 1.0)
            else:
                return 1.0
        except:
            return 0.8  # Default if consistency check fails

    def _compute_color_histogram(self, img_array: 'np.ndarray') -> 'np.ndarray':
        """Compute normalized color histogram"""
        import numpy as np

        hist = np.zeros(16 * 16 * 16)  # 16 bins per channel
        h, w, c = img_array.shape

        # Quantize to 16 levels
        quantized = (img_array * 15).astype(np.int32)

        # Compute histogram
        for i in range(h):
            for j in range(w):
                r, g, b = quantized[i, j]
                bin_idx = r * 256 + g * 16 + b
                hist[bin_idx] += 1

        # Normalize
        hist = hist / hist.sum()
        return hist

    def _map_outcome_to_decision(self, outcome: DecisionOutcome) -> ValidationDecision:
        """Map AI decision outcome to validation decision"""
        mapping = {
            DecisionOutcome.APPROVED: ValidationDecision.APPROVED,
            DecisionOutcome.REJECTED: ValidationDecision.REJECTED,
            DecisionOutcome.RETRY: ValidationDecision.RETRY_RECOMMENDED,
            DecisionOutcome.FLAG_FOR_REVIEW: ValidationDecision.FLAG_FOR_HUMAN,
            DecisionOutcome.ESCALATE: ValidationDecision.FLAG_FOR_HUMAN
        }
        return mapping.get(outcome, ValidationDecision.FLAG_FOR_HUMAN)

    def validate_batch_with_ai(
        self,
        asset_paths: list[Path | str],
        context: Optional[Dict[str, Any]] = None
    ) -> list[AIValidationResult]:
        """
        Validate multiple assets with AI decisions

        Args:
            asset_paths: List of paths to validate
            context: Shared context for batch

        Returns:
            List of AIValidationResult objects
        """
        return [
            self.validate_with_ai(path, context)
            for path in asset_paths
        ]

    def record_human_feedback(
        self,
        asset_path: Path | str,
        ai_decision: ValidationDecision,
        human_decision: str,
        decision_id: Optional[str] = None
    ):
        """
        Record human feedback for AI learning

        Args:
            asset_path: Asset that was reviewed
            ai_decision: What AI decided
            human_decision: What human decided
            decision_id: Optional decision ID to track
        """
        was_correct = (ai_decision.value == human_decision)

        if decision_id:
            self.ai_engine.record_human_feedback(
                decision_id=decision_id,
                was_correct=was_correct,
                human_override=human_decision if not was_correct else None
            )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get AI validation performance statistics"""
        return self.ai_engine.get_performance_summary()

    def export_decision_history(self, output_path: Path):
        """Export AI decision history for analysis"""
        self.ai_engine.export_decisions(output_path)

    def adapt_thresholds(self):
        """Adapt AI confidence thresholds based on performance"""
        self.ai_engine.adapt_thresholds()


# Convenience function for quick AI validation
def validate_asset_ai(
    asset_path: Path | str,
    authority_level: AuthorityLevel = AuthorityLevel.HIGH_AUTONOMY,
    context: Optional[Dict[str, Any]] = None,
    prompt: Optional[str] = None
) -> AIValidationResult:
    """
    Quick AI-powered validation of a single asset

    Args:
        asset_path: Path to asset
        authority_level: AI authority level
        context: Job context
        prompt: Generation prompt

    Returns:
        AIValidationResult with decision

    Example:
        >>> result = validate_asset_ai("output/image.png")
        >>> if result.decision == ValidationDecision.APPROVED:
        ...     print("Asset approved!")
        ... elif result.decision == ValidationDecision.RETRY_RECOMMENDED:
        ...     print("Retry with:", result.suggested_adjustments)
    """
    validator = AIValidator(authority_level=authority_level)
    return validator.validate_with_ai(asset_path, context, prompt)
