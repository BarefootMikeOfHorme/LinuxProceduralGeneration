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

# Import format handlers
from .fbx_handler import FBXHandler
from .dds_handler import DDSHandler
from .materialx_handler import MaterialXHandler, MaterialParameters, ShaderModel
from .usd_handler import USDHandler, USDLayerType, USDExportOptions


def create_registry_with_handlers() -> FormatRegistry:
    """
    Create FormatRegistry with all handlers registered.

    Returns:
        FormatRegistry with FBX, DDS, USD handlers

    Example:
        >>> registry = create_registry_with_handlers()
        >>> formats = registry.list_supported_formats()
        >>> print(formats)
        {FormatType.MODEL: ['fbx', 'usd'], FormatType.TEXTURE: ['dds']}
    """
    registry = FormatRegistry()

    # Register model handlers
    registry.register_model_format(FBXHandler())
    registry.register_model_format(USDHandler())

    # Register texture handlers
    registry.register_texture_format(DDSHandler())

    return registry


__all__ = [
    # Core classes
    'FormatRegistry',
    'AssetPaths',
    'create_registry_with_handlers',

    # Enums
    'FormatType',
    'CompressionQuality',
    'ShaderModel',
    'USDLayerType',

    # Handler base classes
    'FormatHandler',
    'ModelFormatHandler',
    'TextureFormatHandler',
    'AnimationFormatHandler',

    # Concrete handlers
    'FBXHandler',
    'DDSHandler',
    'MaterialXHandler',
    'USDHandler',

    # Options
    'ConversionOptions',
    'RepairOptions',
    'TextureOptions',
    'AnimationOptions',
    'USDExportOptions',

    # Metadata and parameters
    'ModelMetadata',
    'TextureMetadata',
    'AnimationMetadata',
    'MaterialParameters',

    # Exceptions
    'AssetError',
    'FormatError',
    'ConversionError',
    'RepairError'
]
