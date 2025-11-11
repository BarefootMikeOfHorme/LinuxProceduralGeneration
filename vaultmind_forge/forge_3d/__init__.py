"""
VaultMind Forge - 3D Mesh Generation Module

Supports:
- mesh-xl-1.3b for 3D mesh generation
- StdGEN for semantic decomposition
- Multi-view reconstruction
- Texture to 3D mesh conversion
"""

from .mesh_generator import (
    MeshGenerator,
    MeshGenerationConfig,
    MeshGenerationResult,
    MeshGenerationStage,
)

__all__ = [
    "MeshGenerator",
    "MeshGenerationConfig",
    "MeshGenerationResult",
    "MeshGenerationStage",
]

__version__ = "1.0.0"
