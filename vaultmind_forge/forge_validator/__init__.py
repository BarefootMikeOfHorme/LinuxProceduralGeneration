from __future__ import annotations

"""
VaultMind Forge - Validator Module
Quality validation with AI-powered decision making
"""

from .validator import Validator, ValidationResult
from .ai_validator import (
    AIValidator,
    AIValidationResult,
    ValidationDecision,
    validate_asset_ai
)

__all__ = [
    # Traditional validation
    "Validator",
    "ValidationResult",

    # AI-powered validation
    "AIValidator",
    "AIValidationResult",
    "ValidationDecision",
    "validate_asset_ai"
]

__version__ = "1.0.0"