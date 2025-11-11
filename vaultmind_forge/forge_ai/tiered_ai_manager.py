"""
Tiered AI Manager - Three-tier AI system with intelligent routing

Architecture:
1. Helper AI (Ollama) - Quick classifications, simple tasks (5% of AI calls)
2. Executive AI (DCFT) - Tool use, task coordination, main decisions (80% of AI calls)
3. Planner AI (GPT-20B) - Deep planning, research, complex reasoning (15% of AI calls)

Routing Strategy:
- Agents decide autonomously (75% of all decisions)
- Simple AI tasks → Helper (Ollama) - Free
- Standard AI tasks → Executive (DCFT) - Fast, capable
- Complex AI tasks → Planner (GPT-20B) - Powerful, deep reasoning

Cost savings: ~96% vs using GPT-20B for everything
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any
from enum import Enum

from .base_ai import AIRequest, AIResponse, AIError
from .model_manager import ModelManager
from .ollama_backend import OllamaBackend
from .dcft_backend import DCFTBackend
from .gpt_planner_backend import GPTPlannerBackend

logger = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"           # Quick classifications, yes/no
    STANDARD = "standard"       # Tool use, structured output, decisions
    COMPLEX = "complex"         # Multi-step planning, deep reasoning


class TieredAIManager:
    """
    Three-tier AI system with intelligent routing.

    Automatically routes requests to the appropriate model based on complexity:
    - SIMPLE → Helper (Ollama) - Free, quick
    - STANDARD → Executive (DCFT) - Fast, capable
    - COMPLEX → Planner (GPT-20B) - Powerful, deep

    Example:
        >>> manager = TieredAIManager()
        >>> manager.initialize()
        >>>
        >>> # Simple task (goes to Ollama)
        >>> request = AIRequest(
        ...     prompt="Is this texture resolution appropriate? 1024x1024",
        ...     complexity=TaskComplexity.SIMPLE
        ... )
        >>> response = manager.generate(request)  # Uses Ollama
        >>>
        >>> # Standard task (goes to DCFT)
        >>> request = AIRequest(
        ...     prompt="Evaluate this texture quality and suggest improvements",
        ...     complexity=TaskComplexity.STANDARD
        ... )
        >>> response = manager.generate(request)  # Uses DCFT
        >>>
        >>> # Complex task (goes to GPT-20B)
        >>> request = AIRequest(
        ...     prompt="Plan a complete generation strategy for 100 diverse assets",
        ...     complexity=TaskComplexity.COMPLEX
        ... )
        >>> response = manager.generate(request)  # Uses GPT-20B
    """

    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
        # Helper AI config
        helper_model: str = "llama3.2",
        enable_helper: bool = True,
        # Executive AI config
        executive_model: str = "sizzlebop/oh-dcft-v3.1-claude-3-5-haiku-20241022-qwen-Q8_0-GGUF",
        executive_memory_gb: float = 8.0,
        keep_executive_loaded: bool = True,  # Keep main model loaded
        # Planner AI config
        planner_model: str = "openai/gpt-oss-20b",
        planner_memory_gb: float = 12.0,
        enable_planner: bool = True,
    ):
        """
        Initialize tiered AI manager.

        Args:
            model_manager: Shared ModelManager (or create new one)
            helper_model: Ollama model for simple tasks
            enable_helper: Enable helper tier
            executive_model: DCFT model for main tasks
            executive_memory_gb: VRAM for executive model
            keep_executive_loaded: Keep executive model loaded
            planner_model: GPT model for complex tasks
            planner_memory_gb: VRAM for planner model
            enable_planner: Enable planner tier
        """
        self.model_manager = model_manager
        self._owns_manager = False

        # Configuration
        self.enable_helper = enable_helper
        self.enable_planner = enable_planner
        self.keep_executive_loaded = keep_executive_loaded

        # Backends
        self.helper: Optional[OllamaBackend] = None
        self.executive: Optional[DCFTBackend] = None
        self.planner: Optional[GPTPlannerBackend] = None

        # Config storage
        self._helper_model = helper_model
        self._executive_model = executive_model
        self._executive_memory_gb = executive_memory_gb
        self._planner_model = planner_model
        self._planner_memory_gb = planner_memory_gb

        # Stats
        self._total_requests = 0
        self._helper_requests = 0
        self._executive_requests = 0
        self._planner_requests = 0

        logger.info(
            f"TieredAIManager created: "
            f"helper={'enabled' if enable_helper else 'disabled'}, "
            f"executive={executive_model}, "
            f"planner={'enabled' if enable_planner else 'disabled'}"
        )

    def initialize(self) -> None:
        """Initialize all tiers"""
        # Create ModelManager if not provided
        if self.model_manager is None:
            total_memory = self._executive_memory_gb + self._planner_memory_gb
            self.model_manager = ModelManager(
                max_total_memory_gb=total_memory * 1.2,  # Some headroom
                auto_unload=True,
                unload_delay=60.0,
            )
            self._owns_manager = True
            logger.info(f"Created ModelManager ({total_memory * 1.2:.0f}GB budget)")

        # Initialize helper (Ollama)
        if self.enable_helper:
            try:
                self.helper = OllamaBackend(model=self._helper_model)
                self.helper.initialize()
                logger.info(f"Helper tier initialized: {self._helper_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize helper: {e}")
                self.enable_helper = False

        # Initialize executive (DCFT)
        try:
            self.executive = DCFTBackend(
                model=self._executive_model,
                model_manager=self.model_manager,
                max_memory_gb=self._executive_memory_gb,
                keep_loaded=self.keep_executive_loaded,
            )
            self.executive.initialize()
            logger.info(f"Executive tier initialized: {self._executive_model}")
        except Exception as e:
            raise AIError(f"Failed to initialize executive (required): {e}") from e

        # Initialize planner (GPT-20B)
        if self.enable_planner:
            try:
                self.planner = GPTPlannerBackend(
                    model=self._planner_model,
                    model_manager=self.model_manager,
                    max_memory_gb=self._planner_memory_gb,
                    keep_loaded=False,  # Load on-demand for complex tasks
                )
                self.planner.initialize()
                logger.info(f"Planner tier initialized: {self._planner_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize planner: {e}")
                self.enable_planner = False

        logger.info("TieredAIManager initialization complete")

    def generate(self, request: AIRequest) -> AIResponse:
        """
        Generate response using appropriate tier.

        Routing logic:
        1. Check request.context for "complexity" hint
        2. Route to appropriate tier based on complexity
        3. Fall back to next tier if current fails

        Args:
            request: AI request with optional complexity hint

        Returns:
            AIResponse from appropriate tier
        """
        self._total_requests += 1

        # Determine complexity
        complexity = self._determine_complexity(request)

        # Route to appropriate tier
        try:
            if complexity == TaskComplexity.SIMPLE and self.helper:
                logger.debug("Routing to helper tier (simple task)")
                response = self.helper.generate(request)
                self._helper_requests += 1
                return response

            elif complexity == TaskComplexity.COMPLEX and self.planner:
                logger.debug("Routing to planner tier (complex task)")
                response = self.planner.generate(request)
                self._planner_requests += 1
                return response

            else:
                # Standard complexity or fallback
                logger.debug("Routing to executive tier (standard task)")
                response = self.executive.generate(request)
                self._executive_requests += 1
                return response

        except Exception as e:
            logger.warning(f"Tier failed: {e}, trying fallback...")

            # Fallback logic
            if complexity == TaskComplexity.SIMPLE:
                # Simple → Try executive
                if self.executive:
                    response = self.executive.generate(request)
                    self._executive_requests += 1
                    return response

            elif complexity == TaskComplexity.STANDARD:
                # Standard → Try planner or helper
                if self.planner:
                    response = self.planner.generate(request)
                    self._planner_requests += 1
                    return response
                elif self.helper:
                    response = self.helper.generate(request)
                    self._helper_requests += 1
                    return response

            # All fallbacks failed
            raise AIError(f"All tiers failed: {e}") from e

    def _determine_complexity(self, request: AIRequest) -> TaskComplexity:
        """
        Determine task complexity.

        Priority:
        1. Explicit hint in request.context["complexity"]
        2. Heuristics based on prompt characteristics
        """
        # Check explicit hint
        if "complexity" in request.context:
            complexity_str = request.context["complexity"]
            if isinstance(complexity_str, TaskComplexity):
                return complexity_str
            try:
                return TaskComplexity(complexity_str)
            except ValueError:
                pass

        # Heuristics
        prompt_lower = request.prompt.lower()

        # Simple indicators
        simple_keywords = [
            "is this", "does this", "can this", "should this",
            "yes or no", "true or false", "valid or invalid",
            "classify", "categorize",
        ]
        if any(kw in prompt_lower for kw in simple_keywords):
            return TaskComplexity.SIMPLE

        # Complex indicators
        complex_keywords = [
            "plan", "strategy", "research", "analyze deeply",
            "multi-step", "comprehensive", "detailed analysis",
            "compare multiple", "evaluate all",
        ]
        if any(kw in prompt_lower for kw in complex_keywords):
            return TaskComplexity.COMPLEX

        # Check length (very long = complex)
        if len(request.prompt) > 500:
            return TaskComplexity.COMPLEX

        # Default to standard (executive)
        return TaskComplexity.STANDARD

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        stats = {
            "total_requests": self._total_requests,
            "helper_requests": self._helper_requests,
            "executive_requests": self._executive_requests,
            "planner_requests": self._planner_requests,
            "routing": {
                "helper_rate": (
                    self._helper_requests / self._total_requests
                    if self._total_requests > 0
                    else 0.0
                ),
                "executive_rate": (
                    self._executive_requests / self._total_requests
                    if self._total_requests > 0
                    else 0.0
                ),
                "planner_rate": (
                    self._planner_requests / self._total_requests
                    if self._total_requests > 0
                    else 0.0
                ),
            },
        }

        # Add backend stats
        if self.helper:
            stats["helper"] = self.helper.get_stats()

        if self.executive:
            stats["executive"] = self.executive.get_model_stats()

        if self.planner:
            stats["planner"] = self.planner.get_model_stats()

        # Add model manager stats
        if self.model_manager:
            stats["model_manager"] = self.model_manager.get_stats()

        return stats

    def shutdown(self) -> None:
        """Shutdown all tiers"""
        logger.info("Shutting down TieredAIManager...")

        if self.helper:
            self.helper.shutdown()

        if self.executive:
            self.executive.shutdown()

        if self.planner:
            self.planner.shutdown()

        if self._owns_manager and self.model_manager:
            self.model_manager.shutdown()

        logger.info("TieredAIManager shutdown complete")

    def __repr__(self) -> str:
        return (
            f"TieredAIManager("
            f"helper={'enabled' if self.enable_helper else 'disabled'}, "
            f"executive={self._executive_model}, "
            f"planner={'enabled' if self.enable_planner else 'disabled'})"
        )


def create_tiered_ai_manager(
    preset: str = "full",
    **kwargs
) -> TieredAIManager:
    """
    Quick helper to create tiered AI manager with common presets.

    Args:
        preset: Configuration preset:
            - "full": All three tiers (helper + executive + planner)
            - "executive-only": Just DCFT executive (fast, capable)
            - "executive-planner": DCFT + GPT-20B (no helper)
            - "minimal": Just Ollama helper (free, limited)
        **kwargs: Override any configuration

    Returns:
        Configured TieredAIManager

    Example:
        >>> # Full system (recommended)
        >>> manager = create_tiered_ai_manager(preset="full")
        >>>
        >>> # Executive only (fast, single model)
        >>> manager = create_tiered_ai_manager(preset="executive-only")
        >>>
        >>> # Custom configuration
        >>> manager = create_tiered_ai_manager(
        ...     preset="full",
        ...     executive_model="path/to/custom/model",
        ...     planner_memory_gb=16.0
        ... )
    """
    if preset == "full":
        # All three tiers (recommended)
        config = {
            "enable_helper": True,
            "enable_planner": True,
            "keep_executive_loaded": True,
        }

    elif preset == "executive-only":
        # Just DCFT (fast, single model)
        config = {
            "enable_helper": False,
            "enable_planner": False,
            "keep_executive_loaded": True,
        }

    elif preset == "executive-planner":
        # DCFT + GPT-20B (no helper)
        config = {
            "enable_helper": False,
            "enable_planner": True,
            "keep_executive_loaded": True,
        }

    elif preset == "minimal":
        # Just Ollama (free, limited)
        config = {
            "enable_helper": True,
            "enable_planner": False,
            "keep_executive_loaded": False,
        }

    else:
        raise ValueError(
            f"Unknown preset: {preset}. "
            f"Use 'full', 'executive-only', 'executive-planner', or 'minimal'"
        )

    # Merge with kwargs
    config.update(kwargs)

    return TieredAIManager(**config)
