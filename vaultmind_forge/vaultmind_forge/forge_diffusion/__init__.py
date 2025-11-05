from __future__ import annotations

"""
VaultMind Forge - Diffusion Generation Module
Production-grade SDXL generation with ControlNet, IP-Adapter, and multi-pass support
"""

from .generator import (
    DiffusionGenerator,
    GenerationBackend,
    GenerationConfig,
    GenerationResult,
    HelperPassType,
    DiffusionGeneratorError,
    ModelNotLoadedError,
    InvalidConfigurationError,
    GenerationFailedError,
)

__all__ = [
    "DiffusionGenerator",
    "GenerationBackend",
    "GenerationConfig",
    "GenerationResult",
    "HelperPassType",
    "DiffusionGeneratorError",
    "ModelNotLoadedError",
    "InvalidConfigurationError",
    "GenerationFailedError",
]

__version__ = "1.0.0"