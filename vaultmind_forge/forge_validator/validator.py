"""
VaultMind Forge - Asset Validator
High-level validator interface with backend integration
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel

from .backends import get_backend


class ValidationResult(BaseModel):
    """Validation result for a single asset"""
    file: str
    score: float
    status: str
    checks: Dict[str, float] = {}


class Validator:
    """
    High-level asset validator with automatic backend selection

    Example:
        >>> validator = Validator(threshold=0.7)
        >>> result = validator.validate_asset("output/image.png")
        >>> print(f"Score: {result.score}, Status: {result.status}")
    """

    def __init__(self, threshold: float = 0.5, backend: Optional[object] = None):
        """
        Initialize validator

        Args:
            threshold: Minimum score for pass (0.0-1.0)
            backend: Optional specific backend, otherwise auto-select
        """
        self.backend = backend or get_backend()
        self.threshold = threshold

    def validate_asset(self, path: Path | str) -> ValidationResult:
        """
        Validate a single asset

        Args:
            path: Path to asset file

        Returns:
            ValidationResult with score, status, and detailed checks
        """
        p = Path(path)

        # Check if file exists
        if not p.exists():
            return ValidationResult(
                file=str(p),
                score=0.0,
                status="missing",
                checks={"file_exists": 0.0}
            )

        # Run backend validation
        try:
            checks = self.backend.validate(p)

            # Calculate overall score (average of all checks)
            if checks:
                score = sum(checks.values()) / len(checks)
            else:
                score = 0.0

            # Determine status
            status = "pass" if score >= self.threshold else "fail"

            return ValidationResult(
                file=str(p),
                score=round(score, 3),
                status=status,
                checks=checks
            )

        except Exception as e:
            return ValidationResult(
                file=str(p),
                score=0.0,
                status="error",
                checks={"error": 0.0, "error_message": str(e)}
            )

    def validate_batch(self, paths: list[Path | str]) -> list[ValidationResult]:
        """
        Validate multiple assets

        Args:
            paths: List of asset paths

        Returns:
            List of ValidationResult objects
        """
        return [self.validate_asset(p) for p in paths]

    def get_summary(self, results: list[ValidationResult]) -> Dict[str, any]:
        """
        Generate summary statistics from validation results

        Args:
            results: List of ValidationResult objects

        Returns:
            Dict with summary statistics
        """
        total = len(results)
        passed = sum(1 for r in results if r.status == "pass")
        failed = sum(1 for r in results if r.status == "fail")
        errors = sum(1 for r in results if r.status == "error")

        scores = [r.score for r in results if r.score > 0]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": round(passed / total, 3) if total > 0 else 0.0,
            "average_score": round(avg_score, 3),
        }
