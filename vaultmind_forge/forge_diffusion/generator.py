"""
VaultMind Forge - SDXL Diffusion Generator
Production-grade image generation with ControlNet, IP-Adapter, and multi-pass support

Pass 1: Foundation & Structure ✓
Pass 2: Core Implementation
- SDXL pipeline loading
- Generation execution
- Refiner integration
- Memory optimization
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from PIL import Image

# Set up module logger
logger = logging.getLogger(__name__)


class GenerationBackend(str, Enum):
    """Available generation backends"""
    SDXL_BASE = "sdxl_base"
    SDXL_TURBO = "sdxl_turbo"
    SD_1_5 = "sd_1_5"
    KANDINSKY = "kandinsky"
    PLACEHOLDER = "placeholder"


class HelperPassType(str, Enum):
    """Helper pass types for controlled generation"""
    DEPTH_MAP = "depth_map"
    CANNY_EDGE = "canny_edge"
    POSE_SKELETON = "pose_skeleton"
    SEGMENTATION = "segmentation"
    NORMAL_MAP = "normal_map"
    LINE_ART = "line_art"
    SCRIBBLE = "scribble"
    COLOR_PALETTE = "color_palette"
    IP_ADAPTER = "ip_adapter"


@dataclass
class GenerationConfig:
    """
    Configuration for diffusion generation

    Attributes:
        prompt: Main generation prompt
        negative_prompt: Negative prompt for guidance
        width: Output width (must be multiple of 64)
        height: Output height (must be multiple of 64)
        steps: Number of diffusion steps (20-100)
        guidance_scale: CFG scale (1.0-20.0, typical 7.5)
        seed: Random seed for reproducibility (None = random)
        batch_size: Number of images per generation
        use_refiner: Use SDXL refiner for enhancement
        refiner_start: Refiner start step ratio (0.8-0.95)
        helper_passes: List of helper passes to apply
        controlnet_conditioning_scale: ControlNet strength (0.0-2.0)
        ip_adapter_scale: IP-Adapter strength (0.0-1.0)
    """
    prompt: str
    negative_prompt: str = "low quality, blurry, distorted, bad anatomy, watermark"
    width: int = 1024
    height: int = 1024
    steps: int = 30
    guidance_scale: float = 7.5
    seed: Optional[int] = None
    batch_size: int = 1
    use_refiner: bool = False
    refiner_start: float = 0.85
    helper_passes: List[HelperPassType] = field(default_factory=list)
    controlnet_conditioning_scale: float = 1.0
    ip_adapter_scale: float = 0.5

    def __post_init__(self):
        """Validate configuration parameters"""
        if self.width % 64 != 0 or self.height % 64 != 0:
            raise ValueError(
                f"Width and height must be multiples of 64, got {self.width}x{self.height}"
            )

        if not (20 <= self.steps <= 100):
            logger.warning(
                f"Steps {self.steps} outside recommended range [20, 100]"
            )

        if not (1.0 <= self.guidance_scale <= 20.0):
            logger.warning(
                f"Guidance scale {self.guidance_scale} outside typical range [1.0, 20.0]"
            )


@dataclass
class GenerationResult:
    """
    Result from generation operation

    Attributes:
        images: List of generated PIL Images
        config: Configuration used for generation
        seed: Actual seed used (useful when seed was None)
        generation_time: Time taken in seconds
        helper_images: Dict of helper pass images (depth maps, etc.)
        metadata: Additional metadata
    """
    images: List[Image.Image]
    config: GenerationConfig
    seed: int
    generation_time: float
    helper_images: Dict[str, Image.Image] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DiffusionGeneratorError(Exception):
    """Base exception for generator errors"""
    pass


class ModelNotLoadedError(DiffusionGeneratorError):
    """Raised when attempting generation without loaded model"""
    pass


class InvalidConfigurationError(DiffusionGeneratorError):
    """Raised when configuration is invalid"""
    pass


class GenerationFailedError(DiffusionGeneratorError):
    """Raised when generation fails"""
    pass


class DiffusionGenerator:
    """
    Production-grade SDXL diffusion generator with advanced features

    Features:
    - SDXL base + refiner support
    - ControlNet integration (depth, canny, pose, etc.)
    - IP-Adapter for style transfer
    - Multi-pass generation with validation
    - Helper pass generation and caching
    - Memory management and optimization
    - Comprehensive error handling

    Example:
        >>> generator = DiffusionGenerator(backend=GenerationBackend.SDXL_BASE)
        >>> generator.load_models(device="cuda")
        >>> config = GenerationConfig(
        ...     prompt="a serene forest landscape",
        ...     width=1024,
        ...     height=1024,
        ...     steps=30
        ... )
        >>> result = generator.generate(config)
        >>> result.images[0].save("output.png")
    """

    def __init__(
        self,
        backend: GenerationBackend = GenerationBackend.SDXL_BASE,
        cache_dir: Optional[Path] = None,
        device: Optional[str] = None,
        dtype: torch.dtype = torch.float16,
    ):
        """
        Initialize diffusion generator

        Args:
            backend: Generation backend to use
            cache_dir: Directory for model cache
            device: Device to run on ('cuda', 'cpu', or None for auto)
            dtype: Data type for model weights
        """
        self.backend = backend
        self.cache_dir = cache_dir or Path.home() / ".cache" / "vaultmind_forge"
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = dtype

        # Model components (loaded lazily)
        self.pipe = None
        self.refiner_pipe = None
        self.controlnet_models: Dict[HelperPassType, Any] = {}
        self.ip_adapter = None

        # Generation state
        self._is_loaded = False
        self._generation_count = 0

        logger.info(
            f"Initialized DiffusionGenerator: backend={backend.value}, "
            f"device={self.device}, dtype={dtype}"
        )

    def load_models(
        self,
        device: Optional[str] = None,
        enable_xformers: bool = True,
        enable_attention_slicing: bool = True,
        enable_cpu_offload: bool = False,
    ) -> None:
        """
        Load diffusion models and prepare for generation

        Args:
            device: Override device setting
            enable_xformers: Enable xFormers memory efficient attention
            enable_attention_slicing: Enable attention slicing for memory efficiency
            enable_cpu_offload: Enable sequential CPU offload for low VRAM

        Raises:
            ModelNotLoadedError: If model loading fails
        """
        if self._is_loaded:
            logger.warning("Models already loaded, skipping")
            return

        try:
            logger.info(f"Loading models for backend: {self.backend.value}")
            start_time = time.time()

            if device:
                self.device = device

            # Load main pipeline (implementation in Pass 2)
            self._load_main_pipeline()

            # Apply optimizations
            self._apply_optimizations(
                enable_xformers=enable_xformers,
                enable_attention_slicing=enable_attention_slicing,
                enable_cpu_offload=enable_cpu_offload,
            )

            self._is_loaded = True
            load_time = time.time() - start_time
            logger.info(f"Models loaded successfully in {load_time:.2f}s")

        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise ModelNotLoadedError(f"Model loading failed: {e}") from e

    def generate(
        self,
        config: GenerationConfig,
        callback: Optional[Callable[[int, int], None]] = None,
    ) -> GenerationResult:
        """
        Generate images from configuration

        Args:
            config: Generation configuration
            callback: Optional progress callback(step, total_steps)

        Returns:
            GenerationResult with images and metadata

        Raises:
            ModelNotLoadedError: If models not loaded
            GenerationFailedError: If generation fails
        """
        if not self._is_loaded:
            raise ModelNotLoadedError("Models not loaded. Call load_models() first")

        try:
            logger.info(f"Starting generation: {config.prompt[:50]}...")
            start_time = time.time()

            # Generate (implementation in Pass 2)
            images, seed = self._run_generation(config, callback)

            generation_time = time.time() - start_time
            self._generation_count += 1

            logger.info(
                f"Generation completed in {generation_time:.2f}s "
                f"(seed={seed}, count={len(images)})"
            )

            return GenerationResult(
                images=images,
                config=config,
                seed=seed,
                generation_time=generation_time,
                metadata={
                    "backend": self.backend.value,
                    "device": self.device,
                    "generation_number": self._generation_count,
                }
            )

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise GenerationFailedError(f"Generation failed: {e}") from e

    def generate_multi_pass(
        self,
        config: GenerationConfig,
        num_passes: int = 3,
        validator: Optional[Callable[[Image.Image], Tuple[bool, float]]] = None,
        min_score: float = 0.7,
    ) -> Tuple[GenerationResult, List[GenerationResult]]:
        """
        Generate multiple variations and select best

        Args:
            config: Generation configuration
            num_passes: Number of variations to generate
            validator: Optional validation function(image) -> (passed, score)
            min_score: Minimum score threshold

        Returns:
            Tuple of (best_result, all_results)
        """
        if not self._is_loaded:
            raise ModelNotLoadedError("Models not loaded")

        logger.info(f"Starting multi-pass generation: {num_passes} passes")

        all_results = []
        best_result = None
        best_score = -1.0

        for i in range(num_passes):
            # Generate new seed for each pass
            pass_config = GenerationConfig(**config.__dict__)
            pass_config.seed = None if config.seed is None else config.seed + i

            result = self.generate(pass_config)

            # Validate if validator provided
            if validator:
                passed, score = validator(result.images[0])
                result.metadata["validation_passed"] = passed
                result.metadata["validation_score"] = score

                if score > best_score and score >= min_score:
                    best_score = score
                    best_result = result
            else:
                # No validator, use first result
                if best_result is None:
                    best_result = result

            all_results.append(result)

            logger.info(
                f"Pass {i+1}/{num_passes} completed"
                + (f" (score={result.metadata.get('validation_score', 'N/A')})" if validator else "")
            )

        if best_result is None:
            logger.warning("No results passed validation, using first result")
            best_result = all_results[0]

        return best_result, all_results

    def unload_models(self) -> None:
        """Unload models and free memory"""
        if not self._is_loaded:
            return

        logger.info("Unloading models")

        del self.pipe
        del self.refiner_pipe
        self.controlnet_models.clear()

        self.pipe = None
        self.refiner_pipe = None
        self._is_loaded = False

        # Force garbage collection
        import gc
        gc.collect()

        if self.device == "cuda":
            torch.cuda.empty_cache()

        logger.info("Models unloaded, memory freed")

    # Private methods (implemented in later passes)

    def _load_main_pipeline(self) -> None:
        """Load main diffusion pipeline (Pass 2: Implementation)"""
        logger.info(f"Loading {self.backend.value} pipeline...")

        if self.backend == GenerationBackend.PLACEHOLDER:
            # Placeholder mode - no models needed
            logger.info("Placeholder mode - no models loaded")
            return

        try:
            from diffusers import (
                StableDiffusionXLPipeline,
                StableDiffusionXLImg2ImgPipeline,
                DiffusionPipeline,
            )
        except ImportError as e:
            raise ModelNotLoadedError(
                "diffusers library not installed. Install with: pip install diffusers"
            ) from e

        if self.backend == GenerationBackend.SDXL_BASE:
            # Load SDXL base model
            model_id = "stabilityai/stable-diffusion-xl-base-1.0"
            self.pipe = StableDiffusionXLPipeline.from_pretrained(
                model_id,
                torch_dtype=self.dtype,
                use_safetensors=True,
                variant="fp16" if self.dtype == torch.float16 else None,
                cache_dir=self.cache_dir,
            )
            self.pipe = self.pipe.to(self.device)

            # Optionally load refiner
            refiner_id = "stabilityai/stable-diffusion-xl-refiner-1.0"
            try:
                self.refiner_pipe = DiffusionPipeline.from_pretrained(
                    refiner_id,
                    torch_dtype=self.dtype,
                    use_safetensors=True,
                    variant="fp16" if self.dtype == torch.float16 else None,
                    cache_dir=self.cache_dir,
                )
                self.refiner_pipe = self.refiner_pipe.to(self.device)
                logger.info("SDXL refiner loaded")
            except Exception as e:
                logger.warning(f"Could not load refiner: {e}")
                self.refiner_pipe = None

        elif self.backend == GenerationBackend.SDXL_TURBO:
            # SDXL Turbo (faster, fewer steps)
            model_id = "stabilityai/sdxl-turbo"
            self.pipe = StableDiffusionXLPipeline.from_pretrained(
                model_id,
                torch_dtype=self.dtype,
                use_safetensors=True,
                variant="fp16" if self.dtype == torch.float16 else None,
                cache_dir=self.cache_dir,
            )
            self.pipe = self.pipe.to(self.device)

        else:
            raise NotImplementedError(f"Backend {self.backend.value} not yet implemented")

    def _apply_optimizations(
        self,
        enable_xformers: bool,
        enable_attention_slicing: bool,
        enable_cpu_offload: bool,
    ) -> None:
        """Apply memory and speed optimizations (Pass 2: Implementation)"""
        if self.backend == GenerationBackend.PLACEHOLDER:
            return

        if self.pipe is None:
            return

        # Enable xFormers memory efficient attention
        if enable_xformers:
            try:
                self.pipe.enable_xformers_memory_efficient_attention()
                logger.debug("xFormers memory efficient attention enabled")
            except Exception as e:
                logger.debug(f"Could not enable xFormers: {e}")

        # Enable attention slicing for lower VRAM
        if enable_attention_slicing:
            try:
                self.pipe.enable_attention_slicing()
                logger.debug("Attention slicing enabled")
            except Exception as e:
                logger.debug(f"Could not enable attention slicing: {e}")

        # Enable CPU offload for very low VRAM
        if enable_cpu_offload:
            try:
                self.pipe.enable_sequential_cpu_offload()
                logger.debug("Sequential CPU offload enabled")
            except Exception as e:
                logger.debug(f"Could not enable CPU offload: {e}")

        # Enable VAE slicing
        try:
            if hasattr(self.pipe, 'enable_vae_slicing'):
                self.pipe.enable_vae_slicing()
                logger.debug("VAE slicing enabled")
        except Exception:
            pass

    def _run_generation(
        self,
        config: GenerationConfig,
        callback: Optional[Callable[[int, int], None]],
    ) -> Tuple[List[Image.Image], int]:
        """Execute generation pipeline (Pass 2: Implementation)"""

        # Handle seed
        if config.seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(config.seed)
            seed = config.seed
        else:
            # Random seed
            seed = torch.randint(0, 2**32 - 1, (1,)).item()
            generator = torch.Generator(device=self.device).manual_seed(seed)

        # Placeholder mode
        if self.backend == GenerationBackend.PLACEHOLDER:
            return self._generate_placeholder(config, seed), seed

        # Actual diffusion generation
        if self.pipe is None:
            raise ModelNotLoadedError("Pipeline not loaded")

        try:
            # Base generation
            output = self.pipe(
                prompt=config.prompt,
                negative_prompt=config.negative_prompt,
                width=config.width,
                height=config.height,
                num_inference_steps=config.steps,
                guidance_scale=config.guidance_scale,
                num_images_per_prompt=config.batch_size,
                generator=generator,
                callback=callback,
                output_type="pil" if not config.use_refiner else "latent",
            )

            images = output.images if not config.use_refiner else []

            # Refiner pass
            if config.use_refiner and self.refiner_pipe is not None:
                logger.debug("Running refiner pass...")
                refiner_output = self.refiner_pipe(
                    prompt=config.prompt,
                    negative_prompt=config.negative_prompt,
                    image=output.images,
                    num_inference_steps=int(config.steps * (1 - config.refiner_start)),
                    generator=generator,
                )
                images = refiner_output.images

            return images, seed

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise GenerationFailedError(f"SDXL generation failed: {e}") from e

    def _generate_placeholder(self, config: GenerationConfig, seed: int) -> List[Image.Image]:
        """Generate placeholder images for testing (Pass 2: Implementation)"""
        import hashlib

        images = []
        for i in range(config.batch_size):
            # Generate deterministic color from prompt and seed
            hash_input = f"{config.prompt}_{seed}_{i}".encode()
            hash_hex = hashlib.md5(hash_input).hexdigest()

            r = int(hash_hex[0:2], 16)
            g = int(hash_hex[2:4], 16)
            b = int(hash_hex[4:6], 16)

            # Create colored image
            img = Image.new("RGB", (config.width, config.height), color=(r, g, b))

            # Add text label (requires PIL ImageDraw)
            try:
                from PIL import ImageDraw, ImageFont

                draw = ImageDraw.Draw(img)
                text = f"Placeholder\n{config.width}x{config.height}\nSeed: {seed}"
                draw.text((20, 20), text, fill=(255, 255, 255))
            except Exception:
                pass

            images.append(img)

        return images

    def __repr__(self) -> str:
        return (
            f"DiffusionGenerator(backend={self.backend.value}, "
            f"device={self.device}, loaded={self._is_loaded})"
        )
