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

from .agent_pipeline import (
    AgentIntegratedPipeline,
    AgentPipelineConfig,
    AgentPipelineResult,
    create_quick_pipeline,
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
    "AgentIntegratedPipeline",
    "AgentPipelineConfig",
    "AgentPipelineResult",
    "create_quick_pipeline",
]

__version__ = "1.0.0"