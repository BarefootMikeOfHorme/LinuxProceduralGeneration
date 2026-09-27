"""
VaultMind Forge - AI-Powered Validator
Integrates AIDecisionEngine with quality validation for autonomous decision-making
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Inert note, kept deliberately rather than deleted. These two were imported
# but unreferenced. They are recorded so the intent is not lost and so whoever
# needs them does not rediscover that the import was already considered.
#
# sys    - LPG has real Windows/WSL divergence, so platform detection is a
#          genuine need in this codebase, not a hypothetical one. Known
#          instances today: al1scan.exe vs al1scan (forge_l1.py), the cp1252
#          console workaround, Scripts/ vs bin/ venv layout, and the
#          ProgramFiles-based OpenSCAD/FreeCAD discovery. If this validator
#          ever needs to report or branch on the host platform, sys.platform is
#          the hook; sys.executable is the other likely one, for locating the
#          interpreter actually running validation.
#          This module needs neither today: it does PIL/numpy/scipy arithmetic
#          on a caller-supplied Path, with no subprocess, no binary lookup and
#          no path construction, so it has nothing to branch on.
# Tuple  - held for the case where a metric accessor grows a multi-value
#          return (score plus the reason it failed, say) where a heterogeneous
#          shape reads better than a dataclass. Not used today.
#
# import sys
# from typing import Tuple

# numpy, Pillow and scipy are declared core dependencies in pyproject.toml.
# They are imported here, once, at module scope rather than re-imported inside
# each scoring method. The previous per-method imports sat inside try blocks
# whose handlers returned fixed mid-range scores, so any failure to import a
# core dependency silently degraded the validator into one that approved
# everything. A missing core dependency is an environment fault and belongs at
# import time, where it is visible.
import numpy as np
from PIL import Image, UnidentifiedImageError
from scipy import ndimage

logger = logging.getLogger(__name__)

from ..forge_converter.ai_control import (
    AIDecisionEngine,
    AuthorityLevel,
    DecisionOutcome,
    QualityMetrics as AIQualityMetrics
)
from .validator import Validator, ValidationResult

# These metrics are built on numpy and Pillow, both declared as core
# dependencies in pyproject.toml. There is no legitimate state in which they
# are unavailable, so the import is direct and a failure is reported rather
# than absorbed. The previous guard substituted constant scores here, which
# meant a broken install produced a validator that passed every asset with a
# fabricated 0.7 instead of failing.
from .metrics import (
    anatomy_score,
    prompt_alignment_score,
    consistency_score
)


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
        # Get individual metric scores from validation checks first.
        # `None` means "the validator did not report this check"; 0.0 is a
        # real, meaningful score. The previous code used `== 0.0` as the
        # absent-test sentinel, so a genuine zero was indistinguishable from
        # a missing check and got silently recomputed.
        sharpness = validation.checks.get("sharpness")
        anatomy = validation.checks.get("anatomy")
        prompt_align = validation.checks.get("prompt_alignment")
        color_fid = validation.checks.get("color_fidelity")

        # If the validator did not report a check, compute it here. An
        # unexpected failure leaves the metric at 0.0 and is logged. It is not
        # defaulted to 0.5: that is a passing score, and a crash inside a
        # metric is not evidence that the asset is average.
        if sharpness is None:
            try:
                sharpness = self._compute_sharpness(asset_path)
            except Exception as exc:
                logger.warning("sharpness computation raised for %s: %s", asset_path, exc)
                sharpness = 0.0

        if anatomy is None:
            try:
                anatomy = float(anatomy_score(asset_path))
            except Exception as exc:
                logger.warning("anatomy computation raised for %s: %s", asset_path, exc)
                anatomy = 0.0

        if prompt_align is None and prompt:
            try:
                prompt_align = float(prompt_alignment_score(asset_path, prompt))
            except Exception as exc:
                logger.warning("prompt alignment computation raised for %s: %s", asset_path, exc)
                prompt_align = 0.0

        if color_fid is None:
            try:
                color_fid = self._compute_color_fidelity(asset_path)
            except Exception as exc:
                logger.warning("color fidelity computation raised for %s: %s", asset_path, exc)
                color_fid = 0.0

        # prompt_alignment is only measurable when a prompt was supplied, so it
        # is the one metric that can still be absent here. Resolve it to 0.0
        # explicitly rather than passing None into the metrics contract, and
        # coerce the rest so a caller that stored ints or Decimals upstream
        # still gets a clean float.
        if prompt_align is None:
            prompt_align = 0.0

        # Artifact detection (simple heuristic)
        artifact_score = self._detect_artifacts(asset_path)

        # Consistency score (if reference images provided)
        consistency_val = self._compute_consistency(asset_path, reference_images)

        # Overall score
        overall = validation.score

        return AIQualityMetrics(
            sharpness=float(sharpness),
            anatomy=float(anatomy),
            prompt_alignment=float(prompt_align),
            color_fidelity=float(color_fid),
            artifact_score=float(artifact_score),
            consistency=float(consistency_val),
            overall_score=float(overall)
        )

    def _compute_sharpness(self, asset_path: Path) -> float:
        """
        Compute sharpness score using Laplacian variance.

        An asset that cannot be read or decoded scores 0.0 and is logged.
        It does not score a mid-range default: this is a quality gate, and a
        file the validator cannot measure has not been shown to be good.
        """
        try:
            with Image.open(asset_path) as img:
                gray = np.array(img.convert("L"), dtype=np.float32) / 255.0

            laplacian = ndimage.laplace(gray)
            sharpness = float(np.var(laplacian)) / 1000.0
            return float(np.clip(sharpness, 0.0, 1.0))
        except (OSError, UnidentifiedImageError, ValueError) as exc:
            # Unreadable or corrupt input. Scored as a failure on purpose.
            logger.warning("sharpness unmeasurable for %s: %s", asset_path, exc)
            return 0.0

    def _compute_color_fidelity(self, asset_path: Path) -> float:
        """
        Compute color fidelity score.

        Returns 0.0 for an unreadable asset, with the reason logged, rather
        than a passing default that would let a corrupt file through.
        """
        try:
            with Image.open(asset_path) as img:
                arr = np.array(img.convert("RGB"), dtype=np.float32) / 255.0

            # Check color distribution
            r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

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
        except (OSError, UnidentifiedImageError, ValueError) as exc:
            logger.warning("color fidelity unmeasurable for %s: %s", asset_path, exc)
            return 0.0

    def _detect_artifacts(self, asset_path: Path) -> float:
        """
        Simple artifact detection
        Returns score where 1.0 = no artifacts, 0.0 = severe artifacts

        An unreadable asset returns 0.0 and is logged, rather than the 0.7
        default that previously let undecodable files pass artifact scoring.
        """
        try:
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
        except (OSError, UnidentifiedImageError, ValueError) as exc:
            logger.warning("artifact detection failed for %s: %s", asset_path, exc)
            return 0.0

    def _compute_consistency(
        self,
        asset_path: Path,
        reference_images: Optional[list[Path]]
    ) -> float:
        """
        Compute style consistency with reference images
        Returns score where 1.0 = highly consistent, 0.0 = inconsistent

        An unreadable asset returns 0.0 and is logged, rather than the 0.8
        default that previously reported near-perfect consistency for a file
        that could not be opened.
        """
        if not reference_images:
            return 1.0  # No references = perfect consistency

        try:
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
                return float(np.clip(consistency, 0.0, 1.0))
            else:
                return 1.0
        except (OSError, UnidentifiedImageError, ValueError) as exc:
            logger.warning("consistency unmeasurable for %s: %s", asset_path, exc)
            return 0.0

    def _compute_color_histogram(self, img_array: np.ndarray) -> np.ndarray:
        """Compute normalized color histogram"""
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
