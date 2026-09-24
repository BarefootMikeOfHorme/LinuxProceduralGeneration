"""
VaultMind Forge - 3D Mesh Generation Module

Supports:
- Geometric primitives (15 types with 60+ presets)
- Multi-engine export (Unity, Unreal, CryEngine, Lumix, Godot)
- Template-based batch generation
- mesh-xl-1.3b for AI mesh generation
- StdGEN for semantic decomposition
"""

# AI mesh generation (existing)
from .mesh_generator import (
    MeshGenerator,
    MeshGenerationConfig,
    MeshGenerationResult,
    MeshGenerationStage,
)

# Geometric primitives (new)
from .primitives_all import (
    Box, Sphere, Cylinder, Cone, Torus,
    Capsule, Pyramid, Plane, Disc, Ring,
    Tube, Prism, Dome, Tetrahedron, Octahedron,
    DetailLevel, PrimitiveBase,
)

from .mesh import Mesh, ExportChain

__all__ = [
    # AI Generation
    "MeshGenerator",
    "MeshGenerationConfig",
    "MeshGenerationResult",
    "MeshGenerationStage",

    # Basic Primitives
    "Box", "Sphere", "Cylinder", "Cone", "Torus",

    # Extended Primitives
    "Capsule", "Pyramid", "Plane", "Disc", "Ring",
    "Tube", "Prism", "Dome", "Tetrahedron", "Octahedron",

    # Helpers
    "Mesh", "ExportChain", "DetailLevel", "PrimitiveBase",
]

__version__ = "2.0.0"
