"""
VaultMind Forge - Asset Converter Module

Comprehensive asset conversion for multi-engine workflows.
Supports conversion between different game engines and 3D formats
while preserving quality and metadata.
"""

from enum import Enum
from typing import List, Dict, Optional

__version__ = "1.0.0"
__author__ = "VaultMind Forge"


class ConversionProfile(Enum):
    """Conversion quality profiles."""
    QUALITY = "quality"        # Maximum fidelity, minimal compression
    BALANCED = "balanced"      # Good quality with reasonable sizes
    OPTIMIZED = "optimized"    # Maximum performance/size optimization


class TargetEngine(Enum):
    """Supported target engines."""
    UNITY = "unity"
    UNREAL = "unreal"
    GODOT = "godot"
    BLENDER = "blender"
    WEB = "web"                # Web/Three.js


class AssetType(Enum):
    """Asset type classification."""
    MODEL_3D = "model_3d"
    TEXTURE = "texture"
    ANIMATION = "animation"
    MATERIAL = "material"
    AUDIO = "audio"


# Import main converter class
try:
    from .converter import AssetConverter, ConversionResult
    __all__ = [
        'AssetConverter',
        'ConversionResult',
        'ConversionProfile',
        'TargetEngine',
        'AssetType'
    ]
except ImportError:
    # Module not yet fully implemented
    __all__ = [
        'ConversionProfile',
        'TargetEngine',
        'AssetType'
    ]


def get_supported_engines() -> List[str]:
    """Get list of supported target engines."""
    return [engine.value for engine in TargetEngine]


def get_supported_profiles() -> List[str]:
    """Get list of available conversion profiles."""
    return [profile.value for profile in ConversionProfile]


def get_module_info() -> Dict[str, str]:
    """Get module information."""
    return {
        "name": "forge_converter",
        "version": __version__,
        "author": __author__,
        "description": "Multi-engine asset conversion system",
        "supported_engines": get_supported_engines(),
        "supported_profiles": get_supported_profiles()
    }
