"""
LM Studio Backend - Connect to LM Studio Local Server

Uses LM Studio's OpenAI-compatible local API server.
This is the proper way to use LM Studio models without needing to:
- Install llama-cpp-python (requires C++ build tools)
- Load GGUF files directly
- Deal with model management

Just run LM Studio's local server and this backend connects to it.

Setup:
1. Open LM Studio
2. Load your model (TeichAI, PixelWave, etc.)
3. Start the local server (default: http://localhost:1234)
4. This backend connects automatically
"""

from __future__ import annotations

import time
import logging
from typing import Optional, Dict, Any
import requests

from .base_ai import BaseAI, AIRequest, AIResponse, AIError

logger = logging.getLogger(__name__)


class LMStudioBackend(BaseAI):
    """
    LM Studio backend using local API server.

    Connects to LM Studio's OpenAI-compatible API running on localhost.

    Example:
        >>> # Start LM Studio server first with TeichAI model loaded
        >>> backend = LMStudioBackend(
        ...     base_url="http://localhost:1234/v1",
        ...     model="teichai"  # Model name in LM Studio
        ... )
        >>> backend.initialize()
        >>>
        >>> request = AIRequest(prompt="Explain quantum computing")
        >>> response = backend.generate(request)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        model: str = "local-model",  # LM Studio uses this as default
        timeout: int = 120,
    ):
        """
        Initialize LM Studio backend.

        Args:
            base_url: LM Studio API URL (default: http://localhost:1234/v1)
            model: Model identifier in LM Studio
            timeout: Request timeout in seconds
        """
        super().__init__(model=model)

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def initialize(self) -> None:
        """Initialize and verify LM Studio connection"""
        if self._initialized:
            return

        try:
            # Test connection
            models_url = f"{self.base_url}/models"

            logger.info(f"Connecting to LM Studio at {self.base_url}")

            response = requests.get(models_url, timeout=5)

            if response.status_code != 200:
                raise AIError(
                    f"LM Studio server not responding correctly: {response.status_code}\n"
                    f"Make sure LM Studio is running with local server started."
                )

            # Get available models
            data = response.json()
            available_models = [m.get('id', 'unknown') for m in data.get('data', [])]

            logger.info(f"Connected to LM Studio")
            logger.info(f"Available models: {available_models}")

            # Use first available model if model not specified
            if self.model == "local-model" and available_models:
                self.model = available_models[0]
                logger.info(f"Using model: {self.model}")

            self._initialized = True

        except requests.exceptions.ConnectionError:
            raise AIError(
                "Cannot connect to LM Studio server.\n"
                "Make sure:\n"
                "1. LM Studio is running\n"
                "2. Local server is started (click 'Start Server' in LM Studio)\n"
                "3. Server is running on http://localhost:1234"
            )
        except Exception as e:
            raise AIError(f"Failed to initialize LM Studio backend: {e}") from e

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using LM Studio"""
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

            # Call LM Studio API (OpenAI-compatible)
            completions_url = f"{self.base_url}/chat/completions"

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "stream": False,
            }

            logger.debug(f"Sending request to LM Studio: {request.prompt[:50]}...")

            response = requests.post(
                completions_url,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code != 200:
                raise AIError(
                    f"LM Studio API error: {response.status_code}\n{response.text}"
                )

            data = response.json()

            # Extract response
            content = data['choices'][0]['message']['content']

            # Extract token usage
            usage = data.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', input_tokens + output_tokens)

            latency_ms = (time.time() - start_time) * 1000

            # Update stats
            self._request_count += 1
            self._total_tokens += total_tokens
            # LM Studio is local/free
            self._total_cost += 0.0

            logger.debug(
                f"LM Studio generated {output_tokens} tokens in {latency_ms:.0f}ms"
            )

            return AIResponse(
                content=content,
                backend="lmstudio",
                model=self.model,
                tokens_used=total_tokens,
                cost_estimate=0.0,  # Local = free
                latency_ms=latency_ms,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "server": self.base_url,
                }
            )

        except requests.exceptions.Timeout:
            raise AIError(
                f"LM Studio request timed out after {self.timeout}s. "
                f"Try increasing timeout or using a smaller model."
            )
        except requests.exceptions.RequestException as e:
            raise AIError(f"LM Studio request failed: {e}") from e
        except Exception as e:
            logger.error(f"LM Studio generation failed: {e}")
            raise AIError(f"Generation failed: {e}") from e

    def is_available(self) -> bool:
        """Check if LM Studio server is available"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                timeout=2
            )
            return response.status_code == 200
        except:
            return False

    def shutdown(self) -> None:
        """Shutdown (no-op for HTTP client)"""
        self._initialized = False
        logger.info("LM Studio backend disconnected")

    def __repr__(self) -> str:
        return (
            f"LMStudioBackend("
            f"url={self.base_url}, "
            f"model={self.model}, "
            f"initialized={self._initialized})"
        )
