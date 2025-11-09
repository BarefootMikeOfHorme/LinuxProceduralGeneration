"""
VaultMind Forge - Procedural Generator
High-level API for Rust-powered procedural generation
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Tuple, List, Union
import numpy as np
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from forge_bots.native_bridge import get_native_bridge
from .noise_types import NoiseType, NoisePreset, get_preset
from .output_structure import get_output_structure, ensure_output_directories

logger = logging.getLogger(__name__)


class ProceduralGenerator:
    """
    High-level procedural generation API

    Provides easy access to Rust-powered procedural generation with 25x speedup
    over pure Python implementations.

    Example:
        >>> gen = ProceduralGenerator()
        >>> texture = gen.generate_texture('clouds', size=(512, 512), seed=42)
        >>> terrain = gen.generate_terrain('mountains', size=(1024, 1024))
        >>> save_as_image(texture, 'clouds.png')
    """

    def __init__(self, base_path: Optional[Path] = None, auto_create_dirs: bool = True):
        """
        Initialize procedural generator with native bridge

        Args:
            base_path: Base path for outputs (defaults to project assets)
            auto_create_dirs: Automatically create output directory structure
        """
        self.native = get_native_bridge()

        if not self.native.rust_available:
            raise RuntimeError(
                "Rust backend required for procedural generation. "
                "Please build the Rust validator module."
            )

        # Initialize output structure
        self.output = get_output_structure(base_path)

        if auto_create_dirs:
            dir_count = self.output.ensure_all_directories()
            logger.info(f"Created {dir_count} output directories")

        logger.info("Procedural generator initialized with Rust backend")

    def generate_texture(
        self,
        preset_or_type: Union[str, NoiseType],
        size: Tuple[int, int] = (512, 512),
        seed: int = 0,
        **kwargs
    ) -> np.ndarray:
        """
        Generate procedural texture

        Args:
            preset_or_type: Preset name ('clouds', 'marble', etc.) or NoiseType
            size: Texture size (width, height)
            seed: Random seed for reproducibility
            **kwargs: Additional parameters override preset values

        Returns:
            Grayscale texture as numpy array [0-255], shape (height, width)

        Example:
            >>> gen = ProceduralGenerator()
            >>> clouds = gen.generate_texture('clouds', size=(512, 512), seed=42)
            >>> custom = gen.generate_texture(NoiseType.PERLIN, size=(256, 256), octaves=8)
        """
        width, height = size

        # Handle preset
        if isinstance(preset_or_type, str):
            try:
                preset = get_preset(preset_or_type)
                noise_type = preset.noise_type
                params = {**preset.parameters, **kwargs}  # kwargs override preset
            except KeyError:
                # Maybe it's a noise type string
                try:
                    noise_type = NoiseType(preset_or_type)
                    params = kwargs
                except ValueError:
                    raise ValueError(
                        f"Unknown preset or noise type: {preset_or_type}. "
                        f"Use ProceduralGenerator.list_presets() to see available presets."
                    )
        else:
            noise_type = preset_or_type
            params = kwargs

        # Generate based on noise type
        if noise_type == NoiseType.PERLIN:
            return self._generate_perlin(width, height, seed, params)
        elif noise_type == NoiseType.SIMPLEX:
            return self._generate_simplex(width, height, seed, params)
        elif noise_type == NoiseType.PERLIN_ADVANCED:
            return self._generate_perlin_advanced(width, height, seed, params)
        else:
            raise ValueError(f"Invalid noise type for textures: {noise_type}")

    def generate_terrain(
        self,
        preset_or_params: Union[str, dict],
        size: Tuple[int, int] = (512, 512),
        seed: int = 0,
        **kwargs
    ) -> np.ndarray:
        """
        Generate terrain heightmap

        Args:
            preset_or_params: Preset name ('mountains', 'rolling_hills', etc.) or parameters dict
            size: Heightmap size (width, height)
            seed: Random seed for reproducibility
            **kwargs: Additional parameters override preset values

        Returns:
            Height values as numpy array [0.0-1.0], shape (height, width)

        Example:
            >>> gen = ProceduralGenerator()
            >>> mountains = gen.generate_terrain('mountains', size=(1024, 1024))
            >>> custom = gen.generate_terrain({'octaves': 6, 'lacunarity': 2.0})
        """
        width, height = size

        # Handle preset or parameters
        if isinstance(preset_or_params, str):
            preset = get_preset(preset_or_params)
            params = {**preset.parameters, **kwargs}
        else:
            params = {**preset_or_params, **kwargs}

        # Generate FBM heightmap
        return self._generate_fbm(width, height, seed, params)

    def generate_variations(
        self,
        preset_or_type: Union[str, NoiseType],
        count: int,
        size: Tuple[int, int] = (512, 512),
        base_seed: int = 0,
        **kwargs
    ) -> List[np.ndarray]:
        """
        Generate multiple texture variations from same preset

        Uses reproducible seed generation for consistent variations

        Args:
            preset_or_type: Preset name or NoiseType
            count: Number of variations to generate
            size: Texture size
            base_seed: Base seed for variation generation
            **kwargs: Additional parameters

        Returns:
            List of texture arrays

        Example:
            >>> gen = ProceduralGenerator()
            >>> variations = gen.generate_variations('clouds', count=5, size=(256, 256))
            >>> # Creates 5 cloud texture variations
        """
        # Generate variation seeds
        seeds = self.native.generate_seed_variations(base_seed, count)

        # Generate textures with different seeds
        textures = []
        for seed in seeds:
            texture = self.generate_texture(preset_or_type, size, seed, **kwargs)
            textures.append(texture)

        return textures

    # ========================================================================
    # INTERNAL GENERATION METHODS
    # ========================================================================

    def _generate_perlin(
        self,
        width: int,
        height: int,
        seed: int,
        params: dict
    ) -> np.ndarray:
        """Generate Perlin noise texture"""
        scale = params.get('scale', 4.0)
        octaves = params.get('octaves', 4)

        return self.native.generate_noise_texture(
            width=width,
            height=height,
            noise_type='perlin',
            scale=scale,
            octaves=octaves,
            seed=seed
        )

    def _generate_simplex(
        self,
        width: int,
        height: int,
        seed: int,
        params: dict
    ) -> np.ndarray:
        """Generate Simplex noise texture"""
        frequency = params.get('frequency', 0.01)

        return self.native.generate_noise_texture(
            width=width,
            height=height,
            noise_type='simplex',
            frequency=frequency,
            seed=seed
        )

    def _generate_perlin_advanced(
        self,
        width: int,
        height: int,
        seed: int,
        params: dict
    ) -> np.ndarray:
        """Generate advanced Perlin noise with contrast/brightness control"""
        scale = params.get('scale', 4.0)
        octaves = params.get('octaves', 4)
        contrast = params.get('contrast', 1.0)
        brightness = params.get('brightness', 0.0)

        return self.native.generate_noise_texture(
            width=width,
            height=height,
            noise_type='perlin_advanced',
            scale=scale,
            octaves=octaves,
            contrast=contrast,
            brightness=brightness,
            seed=seed
        )

    def _generate_fbm(
        self,
        width: int,
        height: int,
        seed: int,
        params: dict
    ) -> np.ndarray:
        """Generate FBM heightmap"""
        octaves = params.get('octaves', 6)
        lacunarity = params.get('lacunarity', 2.0)
        persistence = params.get('persistence', 0.5)

        return self.native.generate_heightmap(
            width=width,
            height=height,
            octaves=octaves,
            lacunarity=lacunarity,
            persistence=persistence,
            seed=seed
        )

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    @staticmethod
    def list_presets(category: str = 'all') -> dict:
        """
        List available presets

        Args:
            category: 'texture', 'terrain', or 'all'

        Returns:
            Dictionary of preset name -> description
        """
        from .noise_types import list_presets

        presets = list_presets(category)
        return {name: preset.description for name, preset in presets.items()}

    def save_texture_auto(
        self,
        texture: np.ndarray,
        filename: str,
        category: str = 'clouds',
        format: str = 'png'
    ) -> Path:
        """
        Save texture with automatic path resolution

        Args:
            texture: Texture array (uint8, shape (height, width))
            filename: Filename (without extension)
            category: Texture category (clouds, marble, wood, etc.)
            format: Image format (png, jpg, tga, etc.)

        Returns:
            Path where file was saved

        Example:
            >>> gen = ProceduralGenerator()
            >>> texture = gen.generate_texture('clouds', size=(512, 512))
            >>> path = gen.save_texture_auto(texture, 'my_clouds_01', category='clouds')
        """
        # Get appropriate output path
        output_dir = self.output.get_path('procedural', 'textures', category)

        # Add extension
        if not filename.endswith(f'.{format}'):
            filename = f"{filename}.{format}"

        output_path = output_dir / filename
        self.save_texture(texture, output_path)

        return output_path

    @staticmethod
    def save_texture(texture: np.ndarray, output_path: Path):
        """
        Save texture to image file

        Args:
            texture: Texture array (uint8, shape (height, width))
            output_path: Output file path
        """
        from PIL import Image

        if texture.dtype != np.uint8:
            texture = (texture * 255).astype(np.uint8)

        img = Image.fromarray(texture, mode='L')
        img.save(output_path)
        logger.info(f"Saved texture to {output_path}")

    def save_heightmap_auto(
        self,
        heightmap: np.ndarray,
        filename: str,
        terrain_type: str = 'mountains',
        format: str = 'png'
    ) -> Path:
        """
        Save heightmap with automatic path resolution

        Args:
            heightmap: Heightmap array (float32, range [0.0-1.0])
            filename: Filename (without extension)
            terrain_type: Terrain category (mountains, hills, plains, etc.)
            format: Image format (png, tga, exr, etc.)

        Returns:
            Path where file was saved

        Example:
            >>> gen = ProceduralGenerator()
            >>> terrain = gen.generate_terrain('mountains', size=(1024, 1024))
            >>> path = gen.save_heightmap_auto(terrain, 'epic_mountains_01', terrain_type='mountains')
        """
        # Get appropriate output path
        output_dir = self.output.get_path('procedural', 'terrain', terrain_type)

        # Add extension
        if not filename.endswith(f'.{format}'):
            filename = f"{filename}.{format}"

        output_path = output_dir / filename
        self.save_heightmap(heightmap, output_path)

        return output_path

    @staticmethod
    def save_heightmap(heightmap: np.ndarray, output_path: Path):
        """
        Save heightmap to image file (16-bit for better precision)

        Args:
            heightmap: Heightmap array (float32, range [0.0-1.0])
            output_path: Output file path
        """
        from PIL import Image

        # Convert to 16-bit for better precision
        heightmap_16bit = (heightmap * 65535).astype(np.uint16)

        img = Image.fromarray(heightmap_16bit, mode='I;16')
        img.save(output_path)
        logger.info(f"Saved heightmap to {output_path}")
