"""
Ollama Backend - Local LLM inference via Ollama

Supports any model available in Ollama:
- Llama 3.2 (3B, 8B)
- Mistral (7B)
- Phi-3 (3.8B)
- And more...
"""

from __future__ import annotations

import time
import logging
from typing import Optional

from .base_ai import BaseAI, AIRequest, AIResponse, AIError

logger = logging.getLogger(__name__)


class OllamaBackend(BaseAI):
    """
    Ollama backend for local LLM inference.

    Example:
        >>> backend = OllamaBackend(model="llama3.2")
        >>> backend.initialize()
        >>> request = AIRequest(prompt="Generate a fantasy weapon description")
        >>> response = backend.generate(request)
        >>> print(response.content)
    """

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        """
        Initialize Ollama backend.

        Args:
            model: Ollama model name (e.g., "llama3.2", "mistral", "phi3")
            base_url: Ollama API endpoint
        """
        super().__init__(model=model, base_url=base_url)
        self.ollama_client = None

    def initialize(self) -> None:
        """Initialize Ollama connection"""
        if self._initialized:
            return

        try:
            # Try to import ollama
            try:
                import ollama
                self.ollama_client = ollama.Client(host=self.base_url)
            except ImportError:
                logger.warning(
                    "ollama package not installed. "
                    "Install with: pip install ollama"
                )
                raise AIError(
                    "Ollama package not installed. "
                    "Install with: pip install ollama"
                )

            # Test connection
            if not self.is_available():
                raise AIError(
                    f"Ollama not available at {self.base_url}. "
                    f"Make sure Ollama is running."
                )

            # Check if model exists
            try:
                models = self.ollama_client.list()
                model_names = [m['name'] for m in models.get('models', [])]

                if self.model not in model_names:
                    logger.warning(
                        f"Model '{self.model}' not found. "
                        f"Pull it with: ollama pull {self.model}"
                    )
            except Exception as e:
                logger.debug(f"Could not list models: {e}")

            self._initialized = True
            logger.info(f"Ollama backend initialized: {self.model}")

        except Exception as e:
            raise AIError(f"Failed to initialize Ollama: {e}") from e

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using Ollama"""
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

            # Call Ollama
            response = self.ollama_client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "num_predict": request.max_tokens,
                }
            )

            content = response['message']['content']

            # Calculate stats
            latency_ms = (time.time() - start_time) * 1000

            # Ollama doesn't provide token counts, estimate
            tokens_used = len(content.split()) * 1.3  # Rough estimate
            cost_estimate = 0.0  # Local = free

            # Update stats
            self._request_count += 1
            self._total_tokens += int(tokens_used)

            logger.debug(
                f"Ollama generated {int(tokens_used)} tokens "
                f"in {latency_ms:.0f}ms"
            )

            return AIResponse(
                content=content,
                backend="ollama",
                model=self.model,
                tokens_used=int(tokens_used),
                cost_estimate=cost_estimate,
                latency_ms=latency_ms,
                metadata={
                    "base_url": self.base_url,
                }
            )

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise AIError(f"Generation failed: {e}") from e

    def is_available(self) -> bool:
        """Check if Ollama is available"""
        if self.ollama_client is None:
            try:
                import ollama
                self.ollama_client = ollama.Client(host=self.base_url)
            except ImportError:
                return False

        try:
            # Try to list models
            self.ollama_client.list()
            return True
        except Exception:
            return False
