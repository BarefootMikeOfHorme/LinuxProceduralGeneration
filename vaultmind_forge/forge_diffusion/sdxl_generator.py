"""
SDXL Generator - Stable Diffusion XL via Diffusers

Real, working SDXL implementation using diffusers library.
No GGUF, no C++ compiler needed - just pip install.

This is the solution for image generation on Windows without build tools.
"""

from __future__ import annotations

import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image

from .generator import (
    GenerationConfig,
    GenerationResult,
    DiffusionGeneratorError,
)

logger = logging.getLogger(__name__)


class SDXLGenerator:
    """
    SDXL (Stable Diffusion XL) generator using diffusers.

    Works out of the box on Windows without C++ build tools.
    Downloads models automatically on first use.

    Example:
        >>> generator = SDXLGenerator()
        >>> generator.initialize()  # Downloads SDXL on first run
        >>>
        >>> config = GenerationConfig(
        ...     prompt="a futuristic cityscape at sunset",
        ...     width=1024,
        ...     height=1024
        ... )
        >>> result = generator.generate(config)
        >>> result.images[0].save("city.png")
    """

    def __init__(
        self,
        model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
        refiner_id: Optional[str] = None,  # "stabilityai/stable-diffusion-xl-refiner-1.0"
        device: str = "cuda",
        cache_dir: Optional[str] = None,
        use_safetensors: bool = True,
    ):
        """
        Initialize SDXL generator.

        Args:
            model_id: HuggingFace model ID for SDXL base
            refiner_id: Optional refiner model ID
            device: Device to use (cuda/cpu)
            cache_dir: Cache directory for models
            use_safetensors: Use safetensors format
        """
        self.model_id = model_id
        self.refiner_id = refiner_id
        self.device = device
        self.cache_dir = cache_dir
        self.use_safetensors = use_safetensors

        self.pipeline = None
        self.refiner = None
        self._initialized = False
        self._generation_count = 0

    def initialize(self) -> None:
        """Initialize SDXL pipeline"""
        if self._initialized:
            return

        try:
            logger.info("Initializing SDXL generator...")
            logger.info(f"Model: {self.model_id}")
            logger.info(f"Device: {self.device}")

            # Check dependencies
            try:
                from diffusers import StableDiffusionXLPipeline
                import torch
            except ImportError as e:
                raise DiffusionGeneratorError(
                    "Missing dependencies. Install with:\n"
                    "pip install diffusers transformers accelerate torch\n"
                    f"Error: {e}"
                )

            # Detect device
            if self.device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA not available, falling back to CPU")
                self.device = "cpu"

            logger.info(f"Loading SDXL base model (this may take a few minutes first time)...")

            # Load base pipeline
            self.pipeline = StableDiffusionXLPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=self.use_safetensors,
                cache_dir=self.cache_dir,
            )

            self.pipeline = self.pipeline.to(self.device)

            # Enable memory optimizations
            if self.device == "cuda":
                try:
                    self.pipeline.enable_model_cpu_offload()
                    logger.info("Enabled CPU offload for VRAM optimization")
                except:
                    pass

                try:
                    self.pipeline.enable_vae_slicing()
                    logger.info("Enabled VAE slicing for memory optimization")
                except:
                    pass

            # Load refiner if specified
            if self.refiner_id:
                logger.info(f"Loading SDXL refiner model...")
                from diffusers import StableDiffusionXLImg2ImgPipeline

                self.refiner = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                    self.refiner_id,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    use_safetensors=self.use_safetensors,
                    cache_dir=self.cache_dir,
                )
                self.refiner = self.refiner.to(self.device)

                if self.device == "cuda":
                    try:
                        self.refiner.enable_model_cpu_offload()
                        self.refiner.enable_vae_slicing()
                    except:
                        pass

                logger.info("Refiner loaded")

            self._initialized = True
            logger.info("SDXL generator initialized successfully")

        except Exception as e:
            raise DiffusionGeneratorError(
                f"Failed to initialize SDXL: {e}"
            ) from e

    def generate(self, config: GenerationConfig) -> GenerationResult:
        """
        Generate images with SDXL.

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
            logger.info(f"Generating with SDXL: {config.prompt[:50]}...")
            start_time = time.time()

            # Prepare generation parameters
            generator = None
            if config.seed is not None:
                import torch
                generator = torch.Generator(device=self.device).manual_seed(config.seed)

            # Generate base images
            logger.debug(f"Running base generation ({config.batch_size} images)...")
            output = self.pipeline(
                prompt=config.prompt,
                negative_prompt=config.negative_prompt,
                width=config.width,
                height=config.height,
                num_inference_steps=config.num_inference_steps,
                guidance_scale=config.guidance_scale,
                num_images_per_prompt=config.batch_size,
                generator=generator,
            )

            images = output.images

            # Refine if refiner available
            if self.refiner and len(images) > 0:
                logger.debug(f"Running refiner pass...")
                refined_images = []

                for img in images:
                    refined = self.refiner(
                        prompt=config.prompt,
                        image=img,
                        num_inference_steps=config.num_inference_steps // 2,
                        strength=0.3,  # Low strength for refinement
                        generator=generator,
                    )
                    refined_images.append(refined.images[0])

                images = refined_images

            generation_time = time.time() - start_time
            self._generation_count += config.batch_size

            # Use provided seed or generate
            import random
            seed = config.seed if config.seed is not None else random.randint(0, 2**32 - 1)

            logger.info(
                f"SDXL generation completed in {generation_time:.2f}s "
                f"({len(images)} images)"
            )

            return GenerationResult(
                images=images,
                config=config,
                seed=seed,
                generation_time=generation_time,
                metadata={
                    "backend": "sdxl",
                    "model": self.model_id,
                    "refiner": self.refiner_id if self.refiner else None,
                    "device": self.device,
                    "generation_number": self._generation_count,
                }
            )

        except Exception as e:
            logger.error(f"SDXL generation failed: {e}")
            raise DiffusionGeneratorError(f"Generation failed: {e}") from e

    def is_available(self) -> bool:
        """Check if SDXL is available"""
        if not self._initialized:
            try:
                self.initialize()
                return True
            except:
                return False
        return True

    def unload_models(self) -> None:
        """Unload SDXL models to free memory"""
        if self.pipeline:
            try:
                import torch
                del self.pipeline
                if self.refiner:
                    del self.refiner
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                logger.info("SDXL models unloaded")
            except:
                pass

        self.pipeline = None
        self.refiner = None
        self._initialized = False

    def get_stats(self) -> Dict[str, Any]:
        """Get generator statistics"""
        return {
            "model_id": self.model_id,
            "refiner_id": self.refiner_id,
            "device": self.device,
            "initialized": self._initialized,
            "generation_count": self._generation_count,
            "has_refiner": self.refiner is not None,
        }

    def __repr__(self) -> str:
        return (
            f"SDXLGenerator("
            f"model={self.model_id}, "
            f"device={self.device}, "
            f"initialized={self._initialized})"
        )
