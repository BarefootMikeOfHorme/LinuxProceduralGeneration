"""
VaultMind Forge - Format Handlers

Format detection, conversion, and metadata extraction.
"""

from .format_registry import (
    FormatRegistry,
    FormatType,
    FormatHandler,
    ModelFormatHandler,
    TextureFormatHandler,
    AnimationFormatHandler,
    ConversionOptions,
    RepairOptions,
    TextureOptions,
    AnimationOptions,
    ModelMetadata,
    TextureMetadata,
    AnimationMetadata,
    AssetError,
    FormatError,
    ConversionError,
    RepairError,
    CompressionQuality,
    AssetPaths
)

__all__ = [
    # Core classes
    'FormatRegistry',
    'AssetPaths',

    # Enums
    'FormatType',
    'CompressionQuality',

    # Handler base classes
    'FormatHandler',
    'ModelFormatHandler',
    'TextureFormatHandler',
    'AnimationFormatHandler',

    # Options
    'ConversionOptions',
    'RepairOptions',
    'TextureOptions',
    'AnimationOptions',

    # Metadata
    'ModelMetadata',
    'TextureMetadata',
    'AnimationMetadata',

    # Exceptions
    'AssetError',
    'FormatError',
    'ConversionError',
    'RepairError'
]
