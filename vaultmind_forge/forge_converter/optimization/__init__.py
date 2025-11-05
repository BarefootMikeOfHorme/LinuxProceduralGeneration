"""
VaultMind Forge - Optimization

Asset optimization, LOD generation, and compression.
"""

from .math_utils import (
    CoordinateSystem,
    Vertex,
    QuadricError,
    LODCalculator,
    MeshDecimator,
    TextureOptimizer,
    CoordinateTransformer,
    UVOptimizer,
    COMPRESSION_BPP
)

__all__ = [
    # Enums
    'CoordinateSystem',

    # Data structures
    'Vertex',
    'QuadricError',

    # Calculators
    'LODCalculator',
    'MeshDecimator',
    'TextureOptimizer',
    'CoordinateTransformer',
    'UVOptimizer',

    # Constants
    'COMPRESSION_BPP'
]
