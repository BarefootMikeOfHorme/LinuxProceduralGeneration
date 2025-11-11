"""
Claude Backend - Anthropic Claude API

Supports Claude 3.5 Sonnet, Haiku, and Opus models.
"""

from __future__ import annotations

import time
import logging
from typing import Optional

from .base_ai import BaseAI, AIRequest, AIResponse, AIError

logger = logging.getLogger(__name__)


class ClaudeBackend(BaseAI):
    """
    Claude API backend.

    Example:
        >>> backend = ClaudeBackend(
        ...     model="claude-3-5-sonnet-20241022",
        ...     api_key="your-api-key"
        ... )
        >>> backend.initialize()
        >>> request = AIRequest(prompt="Help me plan an asset generation pipeline")
        >>> response = backend.generate(request)
    """

    # Pricing per 1M tokens (USD)
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0},
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    }

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Claude backend.

        Args:
            model: Claude model identifier
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        """
        super().__init__(model=model, api_key=api_key)
        self.client = None

    def initialize(self) -> None:
        """Initialize Claude API client"""
        if self._initialized:
            return

        try:
            try:
                import anthropic
            except ImportError:
                raise AIError(
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
                )

            # Get API key
            api_key = self.api_key
            if not api_key:
                import os
                api_key = os.environ.get("ANTHROPIC_API_KEY")

            if not api_key:
                raise AIError(
                    "No API key provided. Set ANTHROPIC_API_KEY environment variable "
                    "or pass api_key parameter."
                )

            self.client = anthropic.Anthropic(api_key=api_key)
            self._initialized = True
            logger.info(f"Claude backend initialized: {self.model}")

        except Exception as e:
            raise AIError(f"Failed to initialize Claude: {e}") from e

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using Claude"""
        if not self._initialized:
            self.initialize()

        start_time = time.time()

        try:
            # Build message
            message = self.client.messages.create(
                model=self.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system=request.system_prompt if request.system_prompt else None,
                messages=[
                    {"role": "user", "content": request.prompt}
                ]
            )

            content = message.content[0].text

            # Calculate stats
            latency_ms = (time.time() - start_time) * 1000
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            # Calculate cost
            pricing = self.PRICING.get(self.model, {"input": 3.0, "output": 15.0})
            cost = (
                (input_tokens / 1_000_000) * pricing["input"] +
                (output_tokens / 1_000_000) * pricing["output"]
            )

            # Update stats
            self._request_count += 1
            self._total_tokens += total_tokens
            self._total_cost += cost

            logger.debug(
                f"Claude generated {output_tokens} tokens "
                f"in {latency_ms:.0f}ms (cost: ${cost:.4f})"
            )

            return AIResponse(
                content=content,
                backend="claude",
                model=self.model,
                tokens_used=total_tokens,
                cost_estimate=cost,
                latency_ms=latency_ms,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }
            )

        except Exception as e:
            logger.error(f"Claude generation failed: {e}")
            raise AIError(f"Generation failed: {e}") from e

    def is_available(self) -> bool:
        """Check if Claude API is available"""
        if not self._initialized:
            try:
                self.initialize()
                return True
            except:
                return False
        return True
