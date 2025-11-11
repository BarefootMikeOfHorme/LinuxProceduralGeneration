"""
AI Manager - Unified interface for all AI backends

Handles:
- Backend selection and fallback
- Request routing
- Usage tracking
- Cost management
"""

from __future__ import annotations

import logging
from typing import Optional, List
from pathlib import Path

from .base_ai import BaseAI, AIBackend, AIRequest, AIResponse, AIError
from .ollama_backend import OllamaBackend
from .claude_backend import ClaudeBackend
from .openai_backend import OpenAIBackend

logger = logging.getLogger(__name__)


class AIManager:
    """
    Unified AI manager supporting multiple backends with fallback.

    Example:
        >>> # Try Ollama first (free), fallback to Claude
        >>> manager = AIManager(
        ...     primary_backend=AIBackend.OLLAMA,
        ...     fallback_backend=AIBackend.CLAUDE
        ... )
        >>> manager.initialize()
        >>> request = AIRequest(prompt="Generate a weapon description")
        >>> response = manager.generate(request)
    """

    def __init__(
        self,
        primary_backend: AIBackend = AIBackend.OLLAMA,
        fallback_backend: Optional[AIBackend] = None,
        **backend_configs
    ):
        """
        Initialize AI Manager.

        Args:
            primary_backend: Primary AI backend to use
            fallback_backend: Fallback backend if primary fails
            **backend_configs: Backend-specific configs (e.g., api_key, model)
        """
        self.primary_backend_type = primary_backend
        self.fallback_backend_type = fallback_backend
        self.backend_configs = backend_configs

        # Backends
        self.primary_backend: Optional[BaseAI] = None
        self.fallback_backend: Optional[BaseAI] = None

        # Stats
        self._total_requests = 0
        self._primary_requests = 0
        self._fallback_requests = 0

        logger.info(
            f"AIManager created: primary={primary_backend.value}, "
            f"fallback={fallback_backend.value if fallback_backend else 'none'}"
        )

    def initialize(self) -> None:
        """Initialize AI backends"""
        # Initialize primary backend
        self.primary_backend = self._create_backend(self.primary_backend_type)

        try:
            self.primary_backend.initialize()
            logger.info(f"Primary backend initialized: {self.primary_backend_type.value}")
        except Exception as e:
            logger.warning(f"Failed to initialize primary backend: {e}")

            if self.fallback_backend_type is None:
                raise AIError("Primary backend unavailable and no fallback configured")

        # Initialize fallback if configured
        if self.fallback_backend_type:
            self.fallback_backend = self._create_backend(self.fallback_backend_type)

            try:
                self.fallback_backend.initialize()
                logger.info(f"Fallback backend initialized: {self.fallback_backend_type.value}")
            except Exception as e:
                logger.warning(f"Failed to initialize fallback backend: {e}")

    def generate(self, request: AIRequest) -> AIResponse:
        """
        Generate response using available backend.

        Tries primary first, falls back if needed.

        Args:
            request: AI request

        Returns:
            AIResponse

        Raises:
            AIError: If all backends fail
        """
        self._total_requests += 1

        # Try primary backend
        if self.primary_backend and self.primary_backend.is_available():
            try:
                response = self.primary_backend.generate(request)
                self._primary_requests += 1
                logger.debug(f"Request handled by primary backend: {response.backend}")
                return response
            except Exception as e:
                logger.warning(f"Primary backend failed: {e}")

                if self.fallback_backend is None:
                    raise AIError(f"Primary backend failed and no fallback: {e}") from e

        # Try fallback backend
        if self.fallback_backend and self.fallback_backend.is_available():
            try:
                logger.info("Using fallback backend")
                response = self.fallback_backend.generate(request)
                self._fallback_requests += 1
                logger.debug(f"Request handled by fallback backend: {response.backend}")
                return response
            except Exception as e:
                logger.error(f"Fallback backend failed: {e}")
                raise AIError(f"All backends failed: {e}") from e

        raise AIError("No available backends")

    def _create_backend(self, backend_type: AIBackend) -> BaseAI:
        """Create backend instance"""
        # Extract backend-specific configs
        configs = self.backend_configs.copy()

        if backend_type == AIBackend.OLLAMA:
            model = configs.pop("ollama_model", "llama3.2")
            base_url = configs.pop("ollama_url", "http://localhost:11434")
            return OllamaBackend(model=model, base_url=base_url)

        elif backend_type == AIBackend.CLAUDE:
            model = configs.pop("claude_model", "claude-3-5-sonnet-20241022")
            api_key = configs.pop("claude_api_key", None)
            return ClaudeBackend(model=model, api_key=api_key)

        elif backend_type == AIBackend.OPENAI:
            model = configs.pop("openai_model", "gpt-4o-mini")
            api_key = configs.pop("openai_api_key", None)
            return OpenAIBackend(model=model, api_key=api_key)

        else:
            raise ValueError(f"Unknown backend: {backend_type}")

    def get_stats(self) -> dict:
        """Get usage statistics"""
        stats = {
            "total_requests": self._total_requests,
            "primary_requests": self._primary_requests,
            "fallback_requests": self._fallback_requests,
            "fallback_rate": (
                self._fallback_requests / self._total_requests
                if self._total_requests > 0
                else 0.0
            ),
        }

        if self.primary_backend:
            stats["primary_backend"] = self.primary_backend.get_stats()

        if self.fallback_backend:
            stats["fallback_backend"] = self.fallback_backend.get_stats()

        return stats

    def shutdown(self) -> None:
        """Shutdown all backends"""
        if self.primary_backend:
            self.primary_backend.shutdown()

        if self.fallback_backend:
            self.fallback_backend.shutdown()

        logger.info("AIManager shutdown complete")

    def __repr__(self) -> str:
        return (
            f"AIManager("
            f"primary={self.primary_backend_type.value}, "
            f"fallback={self.fallback_backend_type.value if self.fallback_backend_type else 'none'})"
        )


def create_ai_manager(
    mode: str = "local",
    **kwargs
) -> AIManager:
    """
    Quick helper to create AI manager with common configurations.

    Args:
        mode: Configuration mode:
            - "local": Ollama only (free)
            - "cloud": Claude or OpenAI (paid)
            - "hybrid": Ollama primary, Claude fallback (cost-efficient)
        **kwargs: Additional backend configs

    Returns:
        Configured AIManager

    Example:
        >>> # Local-only (free)
        >>> manager = create_ai_manager(mode="local")

        >>> # Hybrid (Ollama first, Claude fallback)
        >>> manager = create_ai_manager(
        ...     mode="hybrid",
        ...     claude_api_key="your-key"
        ... )

        >>> # Cloud-only
        >>> manager = create_ai_manager(
        ...     mode="cloud",
        ...     backend="claude",
        ...     claude_api_key="your-key"
        ... )
    """
    if mode == "local":
        # Ollama only (free)
        manager = AIManager(
            primary_backend=AIBackend.OLLAMA,
            fallback_backend=None,
            **kwargs
        )

    elif mode == "hybrid":
        # Ollama primary (free), cloud fallback (cost-efficient)
        cloud_backend = AIBackend.CLAUDE  # Default to Claude
        if "backend" in kwargs:
            if kwargs["backend"] == "openai":
                cloud_backend = AIBackend.OPENAI
            kwargs.pop("backend")

        manager = AIManager(
            primary_backend=AIBackend.OLLAMA,
            fallback_backend=cloud_backend,
            **kwargs
        )

    elif mode == "cloud":
        # Cloud only (paid)
        cloud_backend = AIBackend.CLAUDE
        if "backend" in kwargs:
            if kwargs["backend"] == "openai":
                cloud_backend = AIBackend.OPENAI
            kwargs.pop("backend")

        manager = AIManager(
            primary_backend=cloud_backend,
            fallback_backend=None,
            **kwargs
        )

    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'local', 'hybrid', or 'cloud'")

    return manager
