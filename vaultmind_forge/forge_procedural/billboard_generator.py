"""
VaultMind Forge - Procedural Billboard Generator
Generate realistic billboards, signs, and advertisements for game environments

Features:
- Multiple billboard types (commercial, industrial, road signs, posters)
- Procedural text generation and placement
- Weathering and aging effects
- Rust/grunge/dirt overlays
- Material variations (metal, wood, plastic, neon)
- Damage and wear patterns
- Engine-ready outputs (Unity, Unreal, Godot)
"""

from __future__ import annotations

import sys
import random
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Union, Literal
from dataclasses import dataclass
from enum import Enum
import numpy as np
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from forge_bots.native_bridge import get_native_bridge
from .output_structure import get_output_structure

logger = logging.getLogger(__name__)


class BillboardType(Enum):
    """Types of billboards that can be generated"""
    COMMERCIAL = "commercial"          # Store signs, advertisements
    INDUSTRIAL = "industrial"          # Warehouse, factory signs
    ROAD_SIGN = "road_sign"           # Street signs, directional
    POSTER = "poster"                 # Posters, flyers, notices
    NEON = "neon"                     # Neon signs (cyberpunk, retro)
    GRAFFITI = "graffiti"             # Street art, tags
    BILLBOARD = "billboard"           # Large outdoor advertisements
    WAYFINDING = "wayfinding"         # Building directories, maps
    WARNING = "warning"               # Caution, danger signs
    VINTAGE = "vintage"               # Old-timey, weathered signs


class MaterialType(Enum):
    """Billboard material types"""
    METAL = "metal"                   # Metal signs (rust, scratches)
    WOOD = "wood"                     # Wooden signs (grain, cracks)
    PLASTIC = "plastic"               # Plastic signs (fading, cracks)
    PAINTED_METAL = "painted_metal"   # Painted metal (peeling, rust)
    NEON_GLASS = "neon_glass"         # Glass neon tubes
    FABRIC = "fabric"                 # Canvas banners
    CONCRETE = "concrete"             # Concrete walls (graffiti base)
    PAPER = "paper"                   # Paper posters


class WeatheringLevel(Enum):
    """How weathered/aged the billboard is"""
    PRISTINE = 0.0                    # Brand new, perfect condition
    LIGHT = 0.25                      # Slight wear
    MODERATE = 0.5                    # Noticeable aging
    HEAVY = 0.75                      # Heavily weathered
    EXTREME = 1.0                     # Nearly destroyed


@dataclass
class BillboardConfig:
    """Configuration for billboard generation"""
    # Core settings
    billboard_type: BillboardType
    material: MaterialType
    weathering: WeatheringLevel

    # Size (in pixels for texture, meters for 3D)
    width: int = 1024
    height: int = 512

    # Visual properties
    base_color: Tuple[int, int, int] = (255, 255, 255)
    text_color: Tuple[int, int, int] = (0, 0, 0)
    background_noise: float = 0.1          # Texture variation

    # Weathering effects
    rust_amount: float = 0.0               # Rust overlay (0-1)
    dirt_amount: float = 0.0               # Dirt/grime (0-1)
    scratch_amount: float = 0.0            # Scratches (0-1)
    fade_amount: float = 0.0               # Color fading (0-1)
    crack_amount: float = 0.0              # Cracks/chips (0-1)

    # Text properties
    text_content: Optional[str] = None
    font_size: int = 72
    text_alignment: str = "center"

    # Seed for reproducibility
    seed: int = 0


class BillboardGenerator:
    """
    Procedural billboard generator for game environments

    Generates complete billboards with:
    - Base material texture (metal, wood, plastic, etc.)
    - Weathering effects (rust, dirt, scratches, fading)
    - Optional text/graphics
    - Normal maps for 3D detail
    - Optional geometry (mesh) for placement

    Example:
        >>> gen = BillboardGenerator()
        >>>
        >>> # Generate a weathered industrial sign
        >>> billboard = gen.generate_billboard(
        ...     billboard_type=BillboardType.INDUSTRIAL,
        ...     material=MaterialType.PAINTED_METAL,
        ...     weathering=WeatheringLevel.HEAVY,
        ...     text_content="FACTORY 7",
        ...     size=(1024, 512)
        ... )
        >>>
        >>> # Save all billboard assets
        >>> paths = gen.save_billboard_complete(billboard, "factory_sign_01")
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize billboard generator

        Args:
            base_path: Base path for outputs
        """
        self.native = get_native_bridge()
        self.output = get_output_structure(base_path)

        logger.info("Billboard generator initialized")

    def generate_billboard(
        self,
        billboard_type: Union[BillboardType, str],
        material: Union[MaterialType, str] = MaterialType.PAINTED_METAL,
        weathering: Union[WeatheringLevel, float] = WeatheringLevel.MODERATE,
        text_content: Optional[str] = None,
        size: Tuple[int, int] = (1024, 512),
        seed: int = 0,
        **kwargs
    ) -> Dict[str, np.ndarray]:
        """
        Generate complete billboard with all textures

        Args:
            billboard_type: Type of billboard (commercial, industrial, etc.)
            material: Material type (metal, wood, plastic, etc.)
            weathering: Weathering level (0.0-1.0 or enum)
            text_content: Optional text to display
            size: Texture size (width, height)
            seed: Random seed
            **kwargs: Additional configuration parameters

        Returns:
            Dictionary containing:
                - 'diffuse': Main color/albedo texture
                - 'normal': Normal map for 3D detail
                - 'roughness': Roughness map
                - 'metallic': Metallic map (if metal material)
                - 'emissive': Emissive map (for neon signs)
                - 'opacity': Alpha mask (for posters, cutouts)
        """
        # Convert string inputs to enums
        if isinstance(billboard_type, str):
            billboard_type = BillboardType(billboard_type)
        if isinstance(material, str):
            material = MaterialType(material)
        if isinstance(weathering, float):
            # Find closest weathering level
            weathering = min(WeatheringLevel, key=lambda x: abs(x.value - weathering))

        width, height = size

        # Create configuration
        config = BillboardConfig(
            billboard_type=billboard_type,
            material=material,
            weathering=weathering,
            width=width,
            height=height,
            text_content=text_content,
            seed=seed,
            **kwargs
        )

        # Apply weathering effects to config
        self._apply_weathering_presets(config)

        # Generate base material
        diffuse = self._generate_base_material(config)

        # Generate normal map
        normal = self._generate_normal_map(config)

        # Generate roughness map
        roughness = self._generate_roughness_map(config)

        # Generate metallic map (for PBR)
        metallic = self._generate_metallic_map(config)

        # Apply weathering effects
        diffuse = self._apply_weathering(diffuse, config)

        # Add text if specified
        if text_content:
            diffuse = self._add_text(diffuse, config)

        # Generate emissive map (for neon signs)
        emissive = self._generate_emissive_map(config)

        # Generate opacity map (for cutouts)
        opacity = self._generate_opacity_map(config)

        result = {
            'diffuse': diffuse,
            'normal': normal,
            'roughness': roughness,
            'metallic': metallic,
            'emissive': emissive,
            'opacity': opacity,
            'config': config
        }

        logger.info(f"Generated {billboard_type.value} billboard: {width}x{height}")
        return result

    def generate_billboard_variations(
        self,
        billboard_type: Union[BillboardType, str],
        count: int = 5,
        size: Tuple[int, int] = (1024, 512),
        base_seed: int = 0,
        **kwargs
    ) -> List[Dict[str, np.ndarray]]:
        """
        Generate multiple billboard variations

        Args:
            billboard_type: Type of billboard
            count: Number of variations
            size: Texture size
            base_seed: Base seed for variations
            **kwargs: Additional parameters

        Returns:
            List of billboard dictionaries
        """
        # Generate variation seeds
        seeds = self.native.generate_seed_variations(base_seed, count)

        billboards = []
        for seed in seeds:
            billboard = self.generate_billboard(
                billboard_type=billboard_type,
                size=size,
                seed=seed,
                **kwargs
            )
            billboards.append(billboard)

        logger.info(f"Generated {count} billboard variations")
        return billboards

    # ========================================================================
    # MATERIAL GENERATION
    # ========================================================================

    def _generate_base_material(self, config: BillboardConfig) -> np.ndarray:
        """Generate base material texture using procedural noise"""
        width, height = config.width, config.height

        # Generate base noise pattern based on material
        if config.material == MaterialType.METAL:
            # Brushed metal pattern
            noise = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=2.0, octaves=4, seed=config.seed
            )

        elif config.material == MaterialType.WOOD:
            # Wood grain pattern
            noise = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=1.5, octaves=6, seed=config.seed
            )

        elif config.material == MaterialType.PLASTIC:
            # Smooth plastic with slight texture
            noise = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=8.0, octaves=2, seed=config.seed
            )

        elif config.material == MaterialType.PAINTED_METAL:
            # Slight texture under paint
            noise = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=4.0, octaves=3, seed=config.seed
            )

        elif config.material == MaterialType.CONCRETE:
            # Rough concrete texture
            noise = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=3.0, octaves=8, seed=config.seed
            )

        else:
            # Default texture
            noise = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=4.0, octaves=4, seed=config.seed
            )

        # Convert to RGB and apply base color
        base = np.stack([noise, noise, noise], axis=-1)

        # Apply base color tint
        r, g, b = config.base_color
        base = base.astype(np.float32) / 255.0
        base[..., 0] *= r / 255.0
        base[..., 1] *= g / 255.0
        base[..., 2] *= b / 255.0
        base = (base * 255).astype(np.uint8)

        return base

    def _generate_normal_map(self, config: BillboardConfig) -> np.ndarray:
        """Generate normal map for surface detail"""
        width, height = config.width, config.height

        # Generate height variation
        if config.material in [MaterialType.METAL, MaterialType.PAINTED_METAL]:
            # Subtle dents and scratches
            height_map = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=8.0, octaves=6, seed=config.seed + 1
            )
        elif config.material == MaterialType.WOOD:
            # Wood grain depth
            height_map = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=2.0, octaves=8, seed=config.seed + 1
            )
        else:
            # Generic surface variation
            height_map = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=5.0, octaves=4, seed=config.seed + 1
            )

        # Convert height map to normal map (simple Sobel approximation)
        # For now, create flat normal map (can be enhanced later)
        normal = np.zeros((height, width, 3), dtype=np.uint8)
        normal[..., 0] = 127  # R = X
        normal[..., 1] = 127  # G = Y
        normal[..., 2] = 255  # B = Z (pointing up)

        return normal

    def _generate_roughness_map(self, config: BillboardConfig) -> np.ndarray:
        """Generate roughness map"""
        width, height = config.width, config.height

        # Base roughness depends on material
        material_roughness = {
            MaterialType.METAL: 0.3,
            MaterialType.WOOD: 0.7,
            MaterialType.PLASTIC: 0.4,
            MaterialType.PAINTED_METAL: 0.5,
            MaterialType.NEON_GLASS: 0.1,
            MaterialType.FABRIC: 0.9,
            MaterialType.CONCRETE: 0.8,
            MaterialType.PAPER: 0.95,
        }

        base_rough = material_roughness.get(config.material, 0.5)

        # Add variation
        noise = self.native.generate_noise_texture(
            width, height, 'perlin',
            scale=6.0, octaves=4, seed=config.seed + 2
        )

        roughness = (base_rough * 255 + (noise.astype(np.float32) - 128) * 0.3).astype(np.uint8)
        roughness = np.clip(roughness, 0, 255)

        return roughness

    def _generate_metallic_map(self, config: BillboardConfig) -> np.ndarray:
        """Generate metallic map (PBR)"""
        width, height = config.width, config.height

        # Is this a metallic material?
        is_metallic = config.material in [MaterialType.METAL, MaterialType.PAINTED_METAL]

        if is_metallic:
            # Metallic with slight variation
            metallic = np.full((height, width), 220, dtype=np.uint8)
        else:
            # Non-metallic
            metallic = np.full((height, width), 0, dtype=np.uint8)

        return metallic

    def _generate_emissive_map(self, config: BillboardConfig) -> np.ndarray:
        """Generate emissive map (for glowing signs)"""
        width, height = config.width, config.height

        # Only neon signs emit light
        if config.billboard_type == BillboardType.NEON:
            # Create glowing areas (would be enhanced with actual neon tube patterns)
            emissive = np.full((height, width, 3), 50, dtype=np.uint8)
        else:
            # No emission
            emissive = np.zeros((height, width, 3), dtype=np.uint8)

        return emissive

    def _generate_opacity_map(self, config: BillboardConfig) -> np.ndarray:
        """Generate opacity/alpha mask"""
        width, height = config.width, config.height

        # Most billboards are fully opaque
        # Posters might have torn edges
        if config.billboard_type == BillboardType.POSTER and config.weathering.value > 0.5:
            # Create torn edges
            noise = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=10.0, octaves=4, seed=config.seed + 3
            )

            # Edge mask
            opacity = np.full((height, width), 255, dtype=np.uint8)

            # Apply tears at edges
            edge_width = int(width * 0.1)
            edge_height = int(height * 0.1)

            opacity[:edge_height, :] = np.minimum(opacity[:edge_height, :], noise[:edge_height, :])
            opacity[-edge_height:, :] = np.minimum(opacity[-edge_height:, :], noise[-edge_height:, :])
            opacity[:, :edge_width] = np.minimum(opacity[:, :edge_width], noise[:, :edge_width])
            opacity[:, -edge_width:] = np.minimum(opacity[:, -edge_width:], noise[:, -edge_width:])
        else:
            # Fully opaque
            opacity = np.full((height, width), 255, dtype=np.uint8)

        return opacity

    # ========================================================================
    # WEATHERING EFFECTS
    # ========================================================================

    def _apply_weathering_presets(self, config: BillboardConfig):
        """Apply weathering presets based on weathering level"""
        level = config.weathering.value

        # Scale effects based on weathering level
        config.rust_amount = level * 0.6 if config.material in [MaterialType.METAL, MaterialType.PAINTED_METAL] else 0
        config.dirt_amount = level * 0.5
        config.scratch_amount = level * 0.4
        config.fade_amount = level * 0.3
        config.crack_amount = level * 0.5 if config.material in [MaterialType.CONCRETE, MaterialType.WOOD] else level * 0.2

    def _apply_weathering(self, diffuse: np.ndarray, config: BillboardConfig) -> np.ndarray:
        """Apply weathering effects to diffuse texture"""
        result = diffuse.copy().astype(np.float32)
        height, width = result.shape[:2]

        # Apply rust
        if config.rust_amount > 0:
            rust_noise = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=3.0, octaves=6, seed=config.seed + 10
            ).astype(np.float32) / 255.0

            rust_color = np.array([139, 69, 19], dtype=np.float32)  # Rust brown
            rust_mask = (rust_noise > (1.0 - config.rust_amount)).astype(np.float32)

            for c in range(3):
                result[..., c] = result[..., c] * (1 - rust_mask) + rust_color[c] * rust_mask

        # Apply dirt/grime
        if config.dirt_amount > 0:
            dirt_noise = self.native.generate_noise_texture(
                width, height, 'perlin',
                scale=5.0, octaves=8, seed=config.seed + 11
            ).astype(np.float32) / 255.0

            dirt_darkening = 1.0 - (dirt_noise * config.dirt_amount * 0.5)
            result *= dirt_darkening[..., np.newaxis]

        # Apply fading
        if config.fade_amount > 0:
            # Fade towards white/gray
            fade_target = 200.0
            result = result * (1 - config.fade_amount) + fade_target * config.fade_amount

        # Apply scratches
        if config.scratch_amount > 0:
            # Vertical scratches (common on signs)
            for _ in range(int(config.scratch_amount * 20)):
                x = random.randint(0, width - 1)
                scratch_width = random.randint(1, 3)
                scratch_color = random.randint(180, 220)

                result[:, x:x+scratch_width, :] = scratch_color

        result = np.clip(result, 0, 255).astype(np.uint8)
        return result

    def _add_text(self, diffuse: np.ndarray, config: BillboardConfig) -> np.ndarray:
        """Add text to billboard (placeholder - would use PIL/font rendering)"""
        # This is a placeholder - real implementation would use PIL ImageFont
        # For now, just return the diffuse as-is
        logger.warning("Text rendering not yet implemented - requires PIL fonts")
        return diffuse

    # ========================================================================
    # SAVING & EXPORT
    # ========================================================================

    def save_billboard_complete(
        self,
        billboard: Dict[str, np.ndarray],
        name: str,
        billboard_type: Optional[str] = None,
        output_format: str = 'png'
    ) -> Dict[str, Path]:
        """
        Save complete billboard with all texture maps

        Args:
            billboard: Billboard dictionary from generate_billboard()
            name: Base name for files
            billboard_type: Optional billboard type override (commercial, industrial, etc.)
            output_format: Image format (png, tga, etc.)

        Returns:
            Dictionary of saved paths
        """
        from PIL import Image

        # Determine billboard type from config if not specified
        if billboard_type is None and 'config' in billboard:
            config = billboard['config']
            type_map = {
                BillboardType.COMMERCIAL: 'commercial',
                BillboardType.INDUSTRIAL: 'industrial',
                BillboardType.ROAD_SIGN: 'road_signs',
                BillboardType.POSTER: 'posters',
                BillboardType.NEON: 'neon',
                BillboardType.GRAFFITI: 'graffiti',
                BillboardType.BILLBOARD: 'large_billboards',
                BillboardType.WAYFINDING: 'wayfinding',
                BillboardType.WARNING: 'warning',
                BillboardType.VINTAGE: 'vintage',
            }
            billboard_type = type_map.get(config.billboard_type, 'commercial')

        # Get billboard output directory
        billboard_dir = self.output.get_path('environments', 'billboards', billboard_type)
        billboard_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = {}

        # Save each texture map
        for map_type in ['diffuse', 'normal', 'roughness', 'metallic', 'emissive', 'opacity']:
            if map_type in billboard:
                texture = billboard[map_type]

                # Convert to PIL Image
                if len(texture.shape) == 2:
                    # Grayscale
                    img = Image.fromarray(texture, mode='L')
                else:
                    # RGB
                    img = Image.fromarray(texture, mode='RGB')

                # Save
                filename = f"{name}_{map_type}.{output_format}"
                filepath = billboard_dir / filename
                img.save(filepath)

                saved_paths[map_type] = filepath
                logger.info(f"Saved {map_type} map: {filepath}")

        return saved_paths


# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================

BILLBOARD_PRESETS = {
    'rusty_industrial': BillboardConfig(
        billboard_type=BillboardType.INDUSTRIAL,
        material=MaterialType.PAINTED_METAL,
        weathering=WeatheringLevel.HEAVY,
        base_color=(180, 180, 200),
        text_color=(255, 255, 0),
    ),

    'clean_commercial': BillboardConfig(
        billboard_type=BillboardType.COMMERCIAL,
        material=MaterialType.PLASTIC,
        weathering=WeatheringLevel.LIGHT,
        base_color=(255, 255, 255),
        text_color=(0, 0, 0),
    ),

    'neon_cyberpunk': BillboardConfig(
        billboard_type=BillboardType.NEON,
        material=MaterialType.NEON_GLASS,
        weathering=WeatheringLevel.MODERATE,
        base_color=(20, 20, 30),
        text_color=(0, 255, 255),
    ),

    'weathered_road_sign': BillboardConfig(
        billboard_type=BillboardType.ROAD_SIGN,
        material=MaterialType.METAL,
        weathering=WeatheringLevel.MODERATE,
        base_color=(255, 200, 0),
        text_color=(0, 0, 0),
    ),

    'torn_poster': BillboardConfig(
        billboard_type=BillboardType.POSTER,
        material=MaterialType.PAPER,
        weathering=WeatheringLevel.HEAVY,
        base_color=(245, 245, 220),
        text_color=(50, 50, 50),
    ),
}
