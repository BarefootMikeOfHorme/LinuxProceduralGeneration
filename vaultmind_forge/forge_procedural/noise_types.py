"""
Noise type definitions and presets for procedural generation
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any


class NoiseType(Enum):
    """Available noise generation algorithms"""
    PERLIN = "perlin"
    SIMPLEX = "simplex"
    PERLIN_ADVANCED = "perlin_advanced"
    FBM = "fbm"


@dataclass
class NoisePreset:
    """Predefined noise configuration presets"""
    name: str
    noise_type: NoiseType
    parameters: Dict[str, Any]
    description: str


# ============================================================================
# TEXTURE PRESETS
# ============================================================================

CLOUDS = NoisePreset(
    name="clouds",
    noise_type=NoiseType.PERLIN,
    parameters={
        'scale': 6.0,
        'octaves': 6,
    },
    description="Soft, billowing clouds"
)

MARBLE = NoisePreset(
    name="marble",
    noise_type=NoiseType.PERLIN_ADVANCED,
    parameters={
        'scale': 3.0,
        'octaves': 8,
        'contrast': 1.5,
        'brightness': 0.2,
    },
    description="Marble-like veined texture"
)

WOOD_GRAIN = NoisePreset(
    name="wood_grain",
    noise_type=NoiseType.PERLIN,
    parameters={
        'scale': 2.0,
        'octaves': 5,
    },
    description="Natural wood grain pattern"
)

WATER = NoisePreset(
    name="water",
    noise_type=NoiseType.SIMPLEX,
    parameters={
        'frequency': 0.02,
    },
    description="Water surface ripples"
)

FIRE = NoisePreset(
    name="fire",
    noise_type=NoiseType.SIMPLEX,
    parameters={
        'frequency': 0.03,
    },
    description="Fire-like turbulent pattern"
)

SMOKE = NoisePreset(
    name="smoke",
    noise_type=NoiseType.SIMPLEX,
    parameters={
        'frequency': 0.01,
    },
    description="Smooth smoke pattern"
)

# ============================================================================
# TERRAIN PRESETS
# ============================================================================

ROLLING_HILLS = NoisePreset(
    name="rolling_hills",
    noise_type=NoiseType.FBM,
    parameters={
        'octaves': 4,
        'lacunarity': 2.0,
        'persistence': 0.5,
    },
    description="Gentle rolling hills terrain"
)

MOUNTAINS = NoisePreset(
    name="mountains",
    noise_type=NoiseType.FBM,
    parameters={
        'octaves': 8,
        'lacunarity': 2.2,
        'persistence': 0.6,
    },
    description="Rugged mountain terrain"
)

DESERT_DUNES = NoisePreset(
    name="desert_dunes",
    noise_type=NoiseType.FBM,
    parameters={
        'octaves': 5,
        'lacunarity': 1.8,
        'persistence': 0.4,
    },
    description="Sand dune patterns"
)

ROCKY = NoisePreset(
    name="rocky",
    noise_type=NoiseType.FBM,
    parameters={
        'octaves': 10,
        'lacunarity': 2.5,
        'persistence': 0.7,
    },
    description="Rocky, detailed terrain"
)

# ============================================================================
# PRESET REGISTRY
# ============================================================================

TEXTURE_PRESETS = {
    'clouds': CLOUDS,
    'marble': MARBLE,
    'wood_grain': WOOD_GRAIN,
    'water': WATER,
    'fire': FIRE,
    'smoke': SMOKE,
}

TERRAIN_PRESETS = {
    'rolling_hills': ROLLING_HILLS,
    'mountains': MOUNTAINS,
    'desert_dunes': DESERT_DUNES,
    'rocky': ROCKY,
}

ALL_PRESETS = {**TEXTURE_PRESETS, **TERRAIN_PRESETS}


def get_preset(name: str) -> NoisePreset:
    """
    Get preset by name

    Args:
        name: Preset name

    Returns:
        NoisePreset

    Raises:
        KeyError: If preset not found
    """
    if name not in ALL_PRESETS:
        available = ', '.join(ALL_PRESETS.keys())
        raise KeyError(f"Preset '{name}' not found. Available: {available}")

    return ALL_PRESETS[name]


def list_presets(category: str = 'all') -> Dict[str, NoisePreset]:
    """
    List available presets

    Args:
        category: 'texture', 'terrain', or 'all'

    Returns:
        Dictionary of presets
    """
    if category == 'texture':
        return TEXTURE_PRESETS
    elif category == 'terrain':
        return TERRAIN_PRESETS
    else:
        return ALL_PRESETS
