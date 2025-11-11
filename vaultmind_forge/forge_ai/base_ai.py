"""
Base AI Interface - Abstract interface for all AI backends

Supports:
- Ollama (local)
- Claude API (Anthropic)
- OpenAI API
- Custom providers
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AIBackend(str, Enum):
    """Available AI backends"""
    OLLAMA = "ollama"           # Local Ollama
    CLAUDE = "claude"           # Anthropic Claude
    OPENAI = "openai"           # OpenAI GPT
    MOCK = "mock"               # Mock for testing


@dataclass
class AIRequest:
    """Request to AI backend"""

    # Core prompt
    prompt: str
    system_prompt: Optional[str] = None

    # Context
    context: Dict[str, Any] = field(default_factory=dict)

    # Generation parameters
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 0.9

    # Metadata
    task_type: str = "general"  # planning, refinement, analysis, etc.
    priority: str = "normal"    # low, normal, high


@dataclass
class AIResponse:
    """Response from AI backend"""

    # Generated content
    content: str

    # Metadata
    backend: str
    model: str
    tokens_used: int
    cost_estimate: float  # USD
    latency_ms: float

    # Additional info
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIError(Exception):
    """Base exception for AI errors"""
    pass


class BaseAI(ABC):
    """
    Abstract base class for AI backends.

    All AI providers must implement this interface.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize AI backend.

        Args:
            model: Model identifier
            api_key: API key (if required)
            base_url: Base URL (if required)
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

        self._initialized = False
        self._request_count = 0
        self._total_tokens = 0
        self._total_cost = 0.0

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the AI backend.

        Raises:
            AIError: If initialization fails
        """
        pass

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """
        Generate response from AI.

        Args:
            request: AI request

        Returns:
            AIResponse with generated content

        Raises:
            AIError: If generation fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if backend is available.

        Returns:
            True if backend can be used
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "backend": self.__class__.__name__,
            "model": self.model,
            "requests": self._request_count,
            "total_tokens": self._total_tokens,
            "total_cost": self._total_cost,
        }

    def shutdown(self) -> None:
        """Shutdown backend and cleanup resources"""
        self._initialized = False
        logger.info(f"{self.__class__.__name__} shutdown")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"model={self.model}, "
            f"initialized={self._initialized})"
        )
