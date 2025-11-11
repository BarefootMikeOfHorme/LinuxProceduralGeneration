"""
OpenAI Backend - OpenAI API

Supports GPT-4o, GPT-4o-mini, and other OpenAI models.
"""

from __future__ import annotations

import time
import logging
from typing import Optional

from .base_ai import BaseAI, AIRequest, AIResponse, AIError

logger = logging.getLogger(__name__)


class OpenAIBackend(BaseAI):
    """
    OpenAI API backend.

    Example:
        >>> backend = OpenAIBackend(
        ...     model="gpt-4o-mini",
        ...     api_key="your-api-key"
        ... )
        >>> backend.initialize()
        >>> request = AIRequest(prompt="Generate a prompt for a fantasy weapon")
        >>> response = backend.generate(request)
    """

    # Pricing per 1M tokens (USD)
    PRICING = {
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    }

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize OpenAI backend.

        Args:
            model: OpenAI model identifier
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        super().__init__(model=model, api_key=api_key)
        self.client = None

    def initialize(self) -> None:
        """Initialize OpenAI client"""
        if self._initialized:
            return

        try:
            try:
                import openai
            except ImportError:
                raise AIError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                )

            # Get API key
            api_key = self.api_key
            if not api_key:
                import os
                api_key = os.environ.get("OPENAI_API_KEY")

            if not api_key:
                raise AIError(
                    "No API key provided. Set OPENAI_API_KEY environment variable "
                    "or pass api_key parameter."
                )

            self.client = openai.OpenAI(api_key=api_key)
            self._initialized = True
            logger.info(f"OpenAI backend initialized: {self.model}")

        except Exception as e:
            raise AIError(f"Failed to initialize OpenAI: {e}") from e

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using OpenAI"""
        if not self._initialized:
            self.initialize()

        start_time = time.time()

        try:
            # Build messages
            messages = []

            if request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })

            messages.append({
                "role": "user",
                "content": request.prompt
            })

            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
            )

            content = response.choices[0].message.content

            # Calculate stats
            latency_ms = (time.time() - start_time) * 1000
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # Calculate cost
            pricing = self.PRICING.get(self.model, {"input": 2.5, "output": 10.0})
            cost = (
                (input_tokens / 1_000_000) * pricing["input"] +
                (output_tokens / 1_000_000) * pricing["output"]
            )

            # Update stats
            self._request_count += 1
            self._total_tokens += total_tokens
            self._total_cost += cost

            logger.debug(
                f"OpenAI generated {output_tokens} tokens "
                f"in {latency_ms:.0f}ms (cost: ${cost:.4f})"
            )

            return AIResponse(
                content=content,
                backend="openai",
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
            logger.error(f"OpenAI generation failed: {e}")
            raise AIError(f"Generation failed: {e}") from e

    def is_available(self) -> bool:
        """Check if OpenAI API is available"""
        if not self._initialized:
            try:
                self.initialize()
                return True
            except:
                return False
        return True
