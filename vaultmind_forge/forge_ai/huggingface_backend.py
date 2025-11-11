"""
Hugging Face Backend - Hugging Face Inference API

Supports:
- Hugging Face Inference API (serverless)
- Multiple providers (Replicate, AWS, etc.)
- Text generation models (Llama, Mistral, etc.)
- Large context models available

For image generation, see forge_diffusion/huggingface_diffusion.py
"""

from __future__ import annotations

import time
import logging
from typing import Optional

from .base_ai import BaseAI, AIRequest, AIResponse, AIError

logger = logging.getLogger(__name__)


class HuggingFaceBackend(BaseAI):
    """
    Hugging Face Inference API backend.

    Supports serverless inference with multiple providers:
    - Replicate
    - AWS
    - Direct HF inference

    Example:
        >>> backend = HuggingFaceBackend(
        ...     model="meta-llama/Llama-3.2-3B-Instruct",
        ...     provider="replicate"
        ... )
        >>> backend.initialize()
        >>> request = AIRequest(prompt="Generate a weapon description")
        >>> response = backend.generate(request)
    """

    # Pricing estimates (approximate, varies by provider)
    PRICING_ESTIMATES = {
        # Per 1M tokens (approximate)
        "meta-llama/Llama-3.2-3B-Instruct": {"input": 0.1, "output": 0.3},
        "meta-llama/Llama-3.2-8B-Instruct": {"input": 0.2, "output": 0.6},
        "mistralai/Mistral-7B-Instruct-v0.3": {"input": 0.2, "output": 0.6},
        "mistralai/Mixtral-8x7B-Instruct-v0.1": {"input": 0.5, "output": 1.5},
    }

    def __init__(
        self,
        model: str = "meta-llama/Llama-3.2-3B-Instruct",
        provider: str = "replicate",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Hugging Face backend.

        Args:
            model: HuggingFace model identifier
            provider: Inference provider (replicate, aws, etc.)
            api_key: HF token (or set HF_TOKEN env var)
        """
        super().__init__(model=model, api_key=api_key)
        self.provider = provider
        self.client = None

    def initialize(self) -> None:
        """Initialize Hugging Face client"""
        if self._initialized:
            return

        try:
            try:
                from huggingface_hub import InferenceClient
            except ImportError:
                raise AIError(
                    "huggingface_hub package not installed. "
                    "Install with: pip install huggingface_hub"
                )

            # Get API key
            api_key = self.api_key
            if not api_key:
                import os
                api_key = os.environ.get("HF_TOKEN")

            if not api_key:
                raise AIError(
                    "No HF token provided. Set HF_TOKEN environment variable "
                    "or pass api_key parameter. Get token from: huggingface.co/settings/tokens"
                )

            # Create client
            self.client = InferenceClient(
                provider=self.provider,
                api_key=api_key,
            )

            self._initialized = True
            logger.info(f"HuggingFace backend initialized: {self.model} via {self.provider}")

        except Exception as e:
            raise AIError(f"Failed to initialize HuggingFace: {e}") from e

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using Hugging Face"""
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

            # Call Hugging Face
            response_text = ""

            # Use chat completion if available
            try:
                completion = self.client.chat_completion(
                    messages=messages,
                    model=self.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                )

                if hasattr(completion, 'choices') and len(completion.choices) > 0:
                    response_text = completion.choices[0].message.content
                else:
                    response_text = str(completion)

            except Exception as e:
                logger.warning(f"Chat completion failed, trying text generation: {e}")

                # Fallback to text generation
                full_prompt = request.prompt
                if request.system_prompt:
                    full_prompt = f"{request.system_prompt}\n\n{request.prompt}"

                response_text = self.client.text_generation(
                    full_prompt,
                    model=self.model,
                    max_new_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                )

            # Calculate stats
            latency_ms = (time.time() - start_time) * 1000

            # Estimate tokens (HF doesn't always provide counts)
            input_tokens = len(request.prompt.split()) * 1.3
            output_tokens = len(response_text.split()) * 1.3
            total_tokens = int(input_tokens + output_tokens)

            # Estimate cost
            pricing = self.PRICING_ESTIMATES.get(
                self.model,
                {"input": 0.2, "output": 0.6}  # Default estimate
            )
            cost = (
                (input_tokens / 1_000_000) * pricing["input"] +
                (output_tokens / 1_000_000) * pricing["output"]
            )

            # Update stats
            self._request_count += 1
            self._total_tokens += total_tokens
            self._total_cost += cost

            logger.debug(
                f"HuggingFace generated ~{int(output_tokens)} tokens "
                f"in {latency_ms:.0f}ms (cost: ${cost:.4f})"
            )

            return AIResponse(
                content=response_text,
                backend="huggingface",
                model=self.model,
                tokens_used=total_tokens,
                cost_estimate=cost,
                latency_ms=latency_ms,
                metadata={
                    "provider": self.provider,
                }
            )

        except Exception as e:
            logger.error(f"HuggingFace generation failed: {e}")
            raise AIError(f"Generation failed: {e}") from e

    def is_available(self) -> bool:
        """Check if HuggingFace is available"""
        if not self._initialized:
            try:
                self.initialize()
                return True
            except:
                return False
        return True
