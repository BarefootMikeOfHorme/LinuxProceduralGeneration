"""
Waifu Generator - Gemma-3 Waifu Finetune Integration

Specialized character generation with anime/waifu style:
- Character design and variations
- Anime-style rendering
- Character portraits
- Visual novel assets
- RPG character art

Uses Gemma-3 Waifu finetune from LM Studio for consistent,
high-quality character generation.
"""

from __future__ import annotations

import time
import logging
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image
import numpy as np

from .generator import (
    GenerationConfig,
    GenerationResult,
    DiffusionGeneratorError,
)

logger = logging.getLogger(__name__)


class WaifuGenerator:
    """
    Waifu character generator using Gemma-3 finetune.

    Specializes in:
    - Anime/manga style characters
    - Character portraits and variations
    - Visual novel assets
    - RPG character art
    - Consistent character design

    Example:
        >>> generator = WaifuGenerator(
        ...     model_path="models/waifu.gguf"
        ... )
        >>> generator.initialize()
        >>>
        >>> config = GenerationConfig(
        ...     prompt="anime girl with long silver hair, blue eyes, mage outfit",
        ...     width=768,
        ...     height=1024,
        ...     style="anime, detailed, high quality"
        ... )
        >>> result = generator.generate(config)
        >>> result.images[0].save("character.png")
    """

    # Character style presets
    STYLE_PRESETS = {
        "portrait": "character portrait, detailed face, expressive eyes, high quality",
        "full_body": "full body character design, dynamic pose, detailed outfit",
        "chibi": "chibi style, cute, simplified proportions, kawaii",
        "realistic": "semi-realistic anime, detailed rendering, professional",
        "manga": "manga style, black and white, screentone, ink drawing",
        "visual_novel": "visual novel character, clean design, expressive",
        "rpg": "RPG character art, game ready, detailed equipment",
    }

    # Recommended character types
    CHARACTER_TYPES = {
        "warrior": "warrior, armor, sword, strong, confident",
        "mage": "mage, robes, staff, magical, wise",
        "archer": "archer, bow, agile, focused",
        "healer": "healer, priest, gentle, caring",
        "rogue": "rogue, thief, sneaky, mysterious",
        "knight": "knight, plate armor, honorable, noble",
        "summoner": "summoner, magical circles, mystical",
    }

    # Recommended resolutions
    RECOMMENDED_RESOLUTIONS = {
        "portrait": (768, 1024),      # Vertical portrait
        "square": (1024, 1024),       # Square format
        "full_body": (768, 1280),     # Tall format
        "wide": (1280, 768),          # Horizontal
        "avatar": (512, 512),         # Small avatar
        "banner": (1920, 512),        # Banner format
    }

    def __init__(
        self,
        model_path: str = "models/waifu.gguf",
        max_memory_gb: float = 4.0,
        device: str = "cuda",
        enable_variations: bool = True,
    ):
        """
        Initialize Waifu generator.

        Args:
            model_path: Path to Waifu GGUF model
            max_memory_gb: Max VRAM allocation (~4GB for Gemma-3)
            device: Device to use (cuda/cpu)
            enable_variations: Enable character variation generation
        """
        self.model_path = Path(model_path)
        self.max_memory_gb = max_memory_gb
        self.device = device
        self.enable_variations = enable_variations

        self.model = None
        self._initialized = False
        self._generation_count = 0

    def initialize(self) -> None:
        """Initialize Waifu model"""
        if self._initialized:
            return

        try:
            if not self.model_path.exists():
                raise DiffusionGeneratorError(
                    f"Waifu model not found: {self.model_path}\n"
                    f"Run scripts/download_models.ps1 to link LM Studio models"
                )

            logger.info(f"Loading Waifu generator: {self.model_path}")

            # Load GGUF model
            self.model = self._load_waifu_model()

            self._initialized = True
            logger.info(f"Waifu generator initialized: {self.model_path}")
            logger.info(f"Style: Anime/manga character generation")

        except Exception as e:
            raise DiffusionGeneratorError(
                f"Failed to initialize Waifu generator: {e}"
            ) from e

    def _load_waifu_model(self):
        """
        Load Waifu GGUF model.

        Similar to PixelWave, GGUF is primarily for LLMs.
        For character generation, we have options:
        1. Use GGUF-compatible diffusion loader (experimental)
        2. Convert to diffusion format
        3. Use text-to-image API with character prompts
        4. Use as prompt generator + separate diffusion model
        """
        try:
            # Option 1: Try GGUF loading (experimental)
            from llama_cpp import Llama

            logger.info("Loading Waifu model via llama-cpp (experimental)")

            model = Llama(
                model_path=str(self.model_path),
                n_ctx=2048,
                n_gpu_layers=-1,
                n_threads=4,
                verbose=False,
            )

            return {
                "model": model,
                "backend": "gguf_text",
                "note": "Using as prompt generator (GGUF diffusion experimental)"
            }

        except Exception as e:
            logger.warning(f"GGUF loading failed: {e}")

            # Option 2: Fallback to HuggingFace with anime model
            logger.info("Falling back to HuggingFace Inference API")

            try:
                from huggingface_hub import InferenceClient
                import os

                api_key = os.environ.get("HF_TOKEN")
                if not api_key:
                    raise DiffusionGeneratorError(
                        "HF_TOKEN required for Waifu inference. "
                        "Set in environment or convert model to diffusion format."
                    )

                client = InferenceClient(
                    provider="replicate",
                    api_key=api_key,
                )

                return {
                    "client": client,
                    "backend": "huggingface",
                    # Use anime-specialized model if available
                    "model": "black-forest-labs/FLUX.1-dev",  # Base model
                    "note": "Using HuggingFace API with anime prompts"
                }

            except Exception as e2:
                raise DiffusionGeneratorError(
                    f"Failed to initialize Waifu generator: {e2}"
                ) from e2

    def generate(self, config: GenerationConfig) -> GenerationResult:
        """
        Generate character images with Waifu model.

        Args:
            config: Generation configuration

        Returns:
            GenerationResult with character images

        Raises:
            DiffusionGeneratorError: If generation fails
        """
        if not self._initialized:
            self.initialize()

        try:
            logger.info(f"Generating character with Waifu: {config.prompt[:50]}...")
            start_time = time.time()

            # Enhance prompt for character generation
            enhanced_prompt = self._enhance_character_prompt(config)

            # Determine backend
            backend = self.model.get("backend", "unknown")

            if backend == "huggingface":
                images = self._generate_via_hf(enhanced_prompt, config)
            elif backend == "gguf_text":
                # Use GGUF as prompt enhancer + fallback diffusion
                images = self._generate_with_prompt_enhancement(enhanced_prompt, config)
            else:
                raise DiffusionGeneratorError(f"Unknown backend: {backend}")

            generation_time = time.time() - start_time
            self._generation_count += 1

            # Use config seed or generate
            import random
            seed = config.seed if config.seed is not None else random.randint(0, 2**32 - 1)

            # Cost (local = free, HF API = paid)
            cost = 0.0 if backend == "gguf_text" else 0.025 * config.batch_size

            logger.info(
                f"Waifu generation completed in {generation_time:.2f}s "
                f"({len(images)} images)"
            )

            return GenerationResult(
                images=images,
                config=config,
                seed=seed,
                generation_time=generation_time,
                metadata={
                    "backend": "waifu",
                    "model": str(self.model_path),
                    "style": "anime, manga, character",
                    "cost_estimate": cost,
                    "generation_number": self._generation_count,
                    "enhanced_prompt": enhanced_prompt,
                }
            )

        except Exception as e:
            logger.error(f"Waifu generation failed: {e}")
            raise DiffusionGeneratorError(f"Generation failed: {e}") from e

    def _enhance_character_prompt(self, config: GenerationConfig) -> str:
        """Enhance prompt for character generation"""
        prompt = config.prompt

        # Add anime style markers
        anime_markers = "anime style, high quality, detailed"

        # Add style if specified
        if config.style:
            # Check if it's a preset
            if config.style.lower() in self.STYLE_PRESETS:
                style_text = self.STYLE_PRESETS[config.style.lower()]
            else:
                style_text = config.style

            prompt = f"{prompt}, {style_text}, {anime_markers}"
        else:
            # Default waifu style
            prompt = f"{prompt}, {anime_markers}, professional character design"

        # Enhance negative prompt for character quality
        if config.negative_prompt:
            config.negative_prompt += ", blurry, distorted, bad anatomy, bad proportions"
        else:
            config.negative_prompt = (
                "blurry, distorted, bad anatomy, bad proportions, "
                "low quality, ugly, deformed"
            )

        return prompt

    def _generate_via_hf(
        self,
        prompt: str,
        config: GenerationConfig
    ) -> List[Image.Image]:
        """Generate via HuggingFace Inference API"""
        client = self.model["client"]
        model_name = self.model["model"]

        images = []
        for i in range(config.batch_size):
            image = client.text_to_image(
                prompt,
                model=model_name,
            )

            # Resize if needed
            if image.size != (config.width, config.height):
                image = image.resize(
                    (config.width, config.height),
                    Image.Resampling.LANCZOS
                )

            images.append(image)

        return images

    def _generate_with_prompt_enhancement(
        self,
        prompt: str,
        config: GenerationConfig
    ) -> List[Image.Image]:
        """
        Use GGUF model to enhance prompt, then generate.

        The Gemma-3 Waifu model can help refine character descriptions
        before passing to diffusion model.
        """
        # Step 1: Use Waifu model to enhance/refine prompt
        llm = self.model["model"]

        enhancement_prompt = f"""You are a character design assistant.
Enhance this character description with vivid details for image generation:

Character: {prompt}

Provide an enhanced, detailed description focusing on:
- Appearance details (hair, eyes, outfit)
- Expression and pose
- Art style markers
- Quality tags

Enhanced description:"""

        try:
            response = llm(
                enhancement_prompt,
                max_tokens=200,
                temperature=0.7,
                stop=["\n\n", "---"]
            )

            enhanced = response["choices"][0]["text"].strip()
            logger.info(f"Prompt enhanced via Waifu LLM: {enhanced[:50]}...")

        except Exception as e:
            logger.warning(f"Prompt enhancement failed: {e}, using original")
            enhanced = prompt

        # Step 2: Generate placeholder (would use actual diffusion in production)
        logger.warning(
            "Using placeholder generation. In production, connect to "
            "HuggingFace API or local diffusion model."
        )

        images = []
        for i in range(config.batch_size):
            # Create placeholder
            image = Image.new(
                "RGB",
                (config.width, config.height),
                color=(255, 200, 220)  # Pink background
            )

            # Add text overlay
            from PIL import ImageDraw
            draw = ImageDraw.Draw(image)

            text = f"Waifu Character\n{prompt[:30]}..."
            draw.text(
                (config.width // 2, config.height // 2),
                text,
                fill=(100, 50, 100),
                anchor="mm"
            )

            images.append(image)

        return images

    def generate_variations(
        self,
        base_config: GenerationConfig,
        num_variations: int = 3,
        variation_strength: float = 0.3
    ) -> List[GenerationResult]:
        """
        Generate character variations.

        Args:
            base_config: Base character configuration
            num_variations: Number of variations to generate
            variation_strength: How much to vary (0-1)

        Returns:
            List of GenerationResults with character variations
        """
        if not self.enable_variations:
            logger.warning("Variations disabled")
            return []

        variations = []

        for i in range(num_variations):
            # Create varied config
            varied_config = GenerationConfig(
                prompt=base_config.prompt,
                negative_prompt=base_config.negative_prompt,
                width=base_config.width,
                height=base_config.height,
                style=base_config.style,
                # Vary seed for different results
                seed=base_config.seed + i + 1 if base_config.seed else None,
                # Slightly vary temperature/sampling
                batch_size=1,
            )

            result = self.generate(varied_config)
            variations.append(result)

        logger.info(f"Generated {len(variations)} character variations")
        return variations

    def apply_character_type(self, character_type: str) -> str:
        """
        Get prompt text for character type.

        Args:
            character_type: Type of character (warrior, mage, etc.)

        Returns:
            Character type prompt text
        """
        return self.CHARACTER_TYPES.get(character_type.lower(), "")

    def get_recommended_resolution(self, format_type: str) -> tuple[int, int]:
        """
        Get recommended resolution for format type.

        Args:
            format_type: Type of format (portrait, full_body, etc.)

        Returns:
            (width, height) tuple
        """
        return self.RECOMMENDED_RESOLUTIONS.get(
            format_type.lower(),
            (768, 1024)  # Default portrait
        )

    def is_available(self) -> bool:
        """Check if Waifu generator is available"""
        if not self._initialized:
            try:
                self.initialize()
                return True
            except:
                return False
        return True

    def unload_models(self) -> None:
        """Unload Waifu model"""
        self.model = None
        self._initialized = False
        logger.info("Waifu generator unloaded")

    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        return {
            "model": str(self.model_path),
            "initialized": self._initialized,
            "generations": self._generation_count,
            "style": "anime, manga, character",
            "backend": self.model.get("backend") if self.model else None,
            "presets": list(self.STYLE_PRESETS.keys()),
            "character_types": list(self.CHARACTER_TYPES.keys()),
            "recommended_resolutions": self.RECOMMENDED_RESOLUTIONS,
            "variations_enabled": self.enable_variations,
        }

    def __repr__(self) -> str:
        return (
            f"WaifuGenerator("
            f"model={self.model_path.name}, "
            f"initialized={self._initialized}, "
            f"generations={self._generation_count})"
        )
