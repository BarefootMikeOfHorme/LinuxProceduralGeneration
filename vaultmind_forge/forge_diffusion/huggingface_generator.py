"""
Hugging Face Diffusion Generator - FLUX.1 and other HF models

Supports state-of-the-art models via Hugging Face Inference API:
- FLUX.1-dev (Black Forest Labs)
- FLUX.1-schnell (faster variant)
- Stable Diffusion XL
- And more...

No local GPU required - runs serverless!
"""

from __future__ import annotations

import time
import logging
from typing import Optional, List
from PIL import Image

from .generator import (
    GenerationConfig,
    GenerationResult,
    DiffusionGeneratorError,
)

logger = logging.getLogger(__name__)


class HuggingFaceDiffusionGenerator:
    """
    Hugging Face-based diffusion generator using serverless inference.

    Supports FLUX.1 and other cutting-edge models without local GPU.

    Example:
        >>> generator = HuggingFaceDiffusionGenerator(
        ...     model="black-forest-labs/FLUX.1-dev",
        ...     provider="replicate"
        ... )
        >>> generator.initialize()
        >>> config = GenerationConfig(
        ...     prompt="astronaut riding a horse",
        ...     width=1024,
        ...     height=1024
        ... )
        >>> result = generator.generate(config)
        >>> result.images[0].save("output.png")
    """

    # Recommended models
    RECOMMENDED_MODELS = {
        "flux_dev": "black-forest-labs/FLUX.1-dev",       # Best quality
        "flux_schnell": "black-forest-labs/FLUX.1-schnell", # Faster
        "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",
    }

    # Pricing estimates (per image, approximate)
    PRICING_ESTIMATES = {
        "black-forest-labs/FLUX.1-dev": 0.025,      # ~$0.025 per image
        "black-forest-labs/FLUX.1-schnell": 0.01,   # ~$0.01 per image
        "stabilityai/stable-diffusion-xl-base-1.0": 0.015,
    }

    def __init__(
        self,
        model: str = "black-forest-labs/FLUX.1-dev",
        provider: str = "replicate",
        api_key: Optional[str] = None,
    ):
        """
        Initialize HuggingFace diffusion generator.

        Args:
            model: HuggingFace model identifier
            provider: Inference provider (replicate, etc.)
            api_key: HF token (or set HF_TOKEN env var)
        """
        self.model = model
        self.provider = provider
        self.api_key = api_key

        self.client = None
        self._initialized = False
        self._generation_count = 0

    def initialize(self) -> None:
        """Initialize HuggingFace client"""
        if self._initialized:
            return

        try:
            try:
                from huggingface_hub import InferenceClient
            except ImportError:
                raise DiffusionGeneratorError(
                    "huggingface_hub package not installed. "
                    "Install with: pip install huggingface_hub"
                )

            # Get API key
            api_key = self.api_key
            if not api_key:
                import os
                api_key = os.environ.get("HF_TOKEN")

            if not api_key:
                raise DiffusionGeneratorError(
                    "No HF token provided. Set HF_TOKEN environment variable. "
                    "Get token from: huggingface.co/settings/tokens"
                )

            # Create client
            self.client = InferenceClient(
                provider=self.provider,
                api_key=api_key,
            )

            self._initialized = True
            logger.info(
                f"HuggingFace diffusion initialized: {self.model} via {self.provider}"
            )

        except Exception as e:
            raise DiffusionGeneratorError(
                f"Failed to initialize HuggingFace: {e}"
            ) from e

    def generate(self, config: GenerationConfig) -> GenerationResult:
        """
        Generate images using HuggingFace Inference API.

        Args:
            config: Generation configuration

        Returns:
            GenerationResult with generated images

        Raises:
            DiffusionGeneratorError: If generation fails
        """
        if not self._initialized:
            self.initialize()

        try:
            logger.info(f"Generating with HuggingFace: {config.prompt[:50]}...")
            start_time = time.time()

            images = []

            for i in range(config.batch_size):
                # Generate image
                image = self.client.text_to_image(
                    config.prompt,
                    model=self.model,
                    # Note: Not all parameters supported by all models
                    # FLUX.1 has its own parameter set
                )

                # Resize if needed
                if image.size != (config.width, config.height):
                    image = image.resize(
                        (config.width, config.height),
                        Image.Resampling.LANCZOS
                    )

                images.append(image)

            generation_time = time.time() - start_time
            self._generation_count += 1

            # Use config seed or generate random
            import random
            seed = config.seed if config.seed is not None else random.randint(0, 2**32 - 1)

            # Estimate cost
            cost_per_image = self.PRICING_ESTIMATES.get(self.model, 0.02)
            total_cost = cost_per_image * config.batch_size

            logger.info(
                f"HuggingFace generation completed in {generation_time:.2f}s "
                f"({config.batch_size} images, ~${total_cost:.3f})"
            )

            return GenerationResult(
                images=images,
                config=config,
                seed=seed,
                generation_time=generation_time,
                metadata={
                    "backend": "huggingface",
                    "model": self.model,
                    "provider": self.provider,
                    "cost_estimate": total_cost,
                    "generation_number": self._generation_count,
                }
            )

        except Exception as e:
            logger.error(f"HuggingFace generation failed: {e}")
            raise DiffusionGeneratorError(f"Generation failed: {e}") from e

    def is_available(self) -> bool:
        """Check if HuggingFace is available"""
        if not self._initialized:
            try:
                self.initialize()
                return True
            except:
                return False
        return True

    def unload_models(self) -> None:
        """Cleanup (no-op for serverless)"""
        self._initialized = False
        logger.info("HuggingFace diffusion generator unloaded")

    def __repr__(self) -> str:
        return (
            f"HuggingFaceDiffusionGenerator("
            f"model={self.model}, "
            f"provider={self.provider}, "
            f"initialized={self._initialized})"
        )
