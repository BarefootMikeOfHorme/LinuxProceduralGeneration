"""
VaultMind Forge - AI Integration Module
Flexible AI backend system supporting multiple LLM providers
"""

from .base_ai import (
    BaseAI,
    AIBackend,
    AIRequest,
    AIResponse,
    AIError,
)

from .ai_manager import (
    AIManager,
    create_ai_manager,
)

from .model_manager import (
    ModelManager,
    ModelConfig,
    ModelRole,
    ModelState,
    ModelStatus,
    create_flux_loader,
    create_gpt_loader,
    create_unloader,
)

from .gpt_planner_backend import (
    GPTPlannerBackend,
)

from .dcft_backend import (
    DCFTBackend,
)

from .tiered_ai_manager import (
    TieredAIManager,
    TaskComplexity,
    create_tiered_ai_manager,
)

__all__ = [
    # Base AI
    "BaseAI",
    "AIBackend",
    "AIRequest",
    "AIResponse",
    "AIError",
    # AI Manager
    "AIManager",
    "create_ai_manager",
    # Model Manager
    "ModelManager",
    "ModelConfig",
    "ModelRole",
    "ModelState",
    "ModelStatus",
    "create_flux_loader",
    "create_gpt_loader",
    "create_unloader",
    # Backends
    "GPTPlannerBackend",
    "DCFTBackend",
    # Tiered System
    "TieredAIManager",
    "TaskComplexity",
    "create_tiered_ai_manager",
]

__version__ = "1.2.0"
