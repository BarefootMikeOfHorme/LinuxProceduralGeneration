"""
VaultMind Forge - Procedural Generation Module
High-level API for Rust-powered procedural generation

Provides easy access to:
- Noise textures (Perlin, Simplex, FBM)
- Heightmaps for terrain
- Billboard generation for game environments
- Seed variation generation
- Texture synthesis
- Comprehensive output structure for all media types

Performance: 25x faster than pure Python implementations
"""

from .generator import ProceduralGenerator
from .noise_types import NoiseType, NoisePreset
from .output_structure import OutputStructure, get_output_structure, ensure_output_directories
from .billboard_generator import (
    BillboardGenerator,
    BillboardType,
    MaterialType,
    WeatheringLevel,
    BillboardConfig,
    BILLBOARD_PRESETS
)

__all__ = [
    'ProceduralGenerator',
    'NoiseType',
    'NoisePreset',
    'OutputStructure',
    'get_output_structure',
    'ensure_output_directories',
    'BillboardGenerator',
    'BillboardType',
    'MaterialType',
    'WeatheringLevel',
    'BillboardConfig',
    'BILLBOARD_PRESETS',
]
