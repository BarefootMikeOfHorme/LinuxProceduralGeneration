"""
VaultMind Forge - Complete Primitive Library (15 Primitives)
=============================================================

All 15 geometric primitives with fluent APIs, smart presets, and detail levels.

Primitives:
    Basic Shapes (5):
        - Box: Rectangular cuboid
        - Sphere: UV sphere
        - Cylinder: Cylinder with caps
        - Cone: Cone with circular base
        - Torus: Donut shape

    Extended Shapes (10):
        - Capsule: Cylinder with hemispherical caps
        - Pyramid: Square pyramid
        - Plane: Flat subdivided surface
        - Disc: Filled circle
        - Ring: Hollow circle/annulus
        - Tube: Hollow cylinder
        - Prism: Triangular/Hexagonal/Octagonal prism
        - Dome: Hemisphere
        - Tetrahedron: 4-sided platonic solid
        - Octahedron: 8-sided platonic solid

Usage:
    >>> from vaultmind_forge.forge_3d import primitives as prim
    >>>
    >>> # Simple creation
    >>> cone = prim.Cone(radius=1.0, height=2.0, detail="medium")
    >>> cone.to_unity("cone.obj")
    >>>
    >>> # Using presets
    >>> crate = prim.Box.preset("wooden_crate")
    >>> donut = prim.Torus.preset("food_donut")
    >>>
    >>> # Fluent chaining
    >>> capsule = prim.Capsule()\\
    ...     .radius(0.5)\\
    ...     .height(1.8)\\
    ...     .detail("high")\\
    ...     .build()\\
    ...     .export()\\
    ...     .to_all("exports/player_hull/")
"""

from typing import Optional, Union, Tuple, List, Dict, Any
from enum import Enum
from datetime import datetime

from ._native import load_native
from .mesh import Mesh


class _NativeProxy:
    """Load the native extension only when a geometry operation needs it."""

    def __getattr__(self, name):
        return getattr(load_native(), name)


_vfc = _NativeProxy()


class DetailLevel(Enum):
    """Named detail levels for intuitive control"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM_LOW = "medium_low"
    MEDIUM = "medium"
    MEDIUM_HIGH = "medium_high"
    HIGH = "high"
    VERY_HIGH = "very_high"
    ULTRA = "ultra"


# Segment counts for each detail level
DETAIL_SEGMENTS = {
    DetailLevel.VERY_LOW: 6,
    DetailLevel.LOW: 8,
    DetailLevel.MEDIUM_LOW: 16,
    DetailLevel.MEDIUM: 32,
    DetailLevel.MEDIUM_HIGH: 48,
    DetailLevel.HIGH: 64,
    DetailLevel.VERY_HIGH: 128,
    DetailLevel.ULTRA: 256,
}


class PrimitiveBase:
    """Base class for all primitives with common functionality"""

    def __init__(self):
        self._metadata = {
            "created_at": datetime.now().isoformat(),
            "type": self.__class__.__name__,
            "parameters": {},
            "detail_level": None,
        }

    def _build_mesh(self) -> Mesh:
        """Override in subclasses"""
        raise NotImplementedError

    def build(self) -> Mesh:
        """Build and return mesh with metadata"""
        mesh = self._build_mesh()
        mesh._metadata.update(self._metadata)
        return mesh

    def preview(self):
        """Show quick stats"""
        mesh = self.build()
        mesh.stats()
        return self

    # Direct export shortcuts
    def to_unity(self, path: str) -> Mesh:
        return self.build().to_unity(path)

    def to_unreal(self, path: str) -> Mesh:
        return self.build().to_unreal(path)

    def to_lumix(self, path: str) -> Mesh:
        return self.build().to_lumix(path)

    def to_cryengine(self, path: str) -> Mesh:
        return self.build().to_cryengine(path)

    def to_godot(self, path: str) -> Mesh:
        return self.build().to_godot(path)


# ============================================================================
# BASIC PRIMITIVES (5)
# ============================================================================

class Box(PrimitiveBase):
    """
    Box/Cuboid primitive.

    Presets: wooden_crate, ammo_box, shipping_container, dice, brick
    """
    PRESETS = {
        "wooden_crate": {"size": (1.0, 1.0, 1.0)},
        "ammo_box": {"size": (0.6, 0.3, 0.4)},
        "shipping_container": {"size": (12.0, 2.5, 2.5)},
        "dice": {"size": (0.02, 0.02, 0.02)},
        "brick": {"size": (0.2, 0.1, 0.1)},
    }

    def __init__(self, size: Union[float, Tuple[float, float, float]] = 1.0,
                 center: Optional[Tuple[float, float, float]] = None):
        super().__init__()
        self._size = (size, size, size) if isinstance(size, (int, float)) else size
        self._center = center
        self._metadata["parameters"] = {"size": self._size, "center": center}

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_box(self._size, center=self._center))


class Sphere(PrimitiveBase):
    """
    UV Sphere primitive.

    Presets: basketball, tennis_ball, marble, planet, atom
    """
    PRESETS = {
        "basketball": {"radius": 0.12, "detail": "medium"},
        "tennis_ball": {"radius": 0.033, "detail": "medium"},
        "marble": {"radius": 0.01, "detail": "high"},
        "planet": {"radius": 10.0, "detail": "very_high"},
        "atom": {"radius": 0.001, "detail": "low"},
    }

    def __init__(self, radius: float = 1.0, detail: Union[str, Tuple[int, int]] = "medium",
                 center: Optional[Tuple[float, float, float]] = None):
        super().__init__()
        self._radius = radius
        self._center = center
        self._set_detail(detail)
        self._metadata["parameters"] = {
            "radius": radius, "segments": self._segments,
            "rings": self._rings, "center": center
        }

    def _set_detail(self, detail):
        if isinstance(detail, tuple):
            self._segments, self._rings = detail
            self._metadata["detail_level"] = "custom"
        else:
            level = DetailLevel(detail.lower())
            base = DETAIL_SEGMENTS[level]
            self._segments = base
            self._rings = max(8, base // 2)
            self._metadata["detail_level"] = detail

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_sphere(
            self._radius, center=self._center,
            segments=self._segments, rings=self._rings
        ))


class Cylinder(PrimitiveBase):
    """
    Cylinder with caps.

    Presets: barrel, pipe, can, pillar, pylon
    """
    PRESETS = {
        "barrel": {"radius": 0.4, "height": 0.8, "detail": "medium"},
        "pipe": {"radius": 0.05, "height": 2.0, "detail": "low"},
        "can": {"radius": 0.03, "height": 0.12, "detail": "medium"},
        "pillar": {"radius": 0.3, "height": 3.0, "detail": "high"},
        "pylon": {"radius": 0.2, "height": 1.2, "detail": "medium"},
    }

    def __init__(self, radius: float = 1.0, height: float = 2.0,
                 detail: Union[str, int] = "medium",
                 center: Optional[Tuple[float, float, float]] = None):
        super().__init__()
        self._radius = radius
        self._height = height
        self._center = center
        self._set_detail(detail)
        self._metadata["parameters"] = {
            "radius": radius, "height": height,
            "segments": self._segments, "center": center
        }

    def _set_detail(self, detail):
        if isinstance(detail, int):
            self._segments = detail
            self._metadata["detail_level"] = "custom"
        else:
            level = DetailLevel(detail.lower())
            self._segments = DETAIL_SEGMENTS[level]
            self._metadata["detail_level"] = detail

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_cylinder(
            self._radius, self._height,
            center=self._center, segments=self._segments
        ))


class Cone(PrimitiveBase):
    """
    Cone with circular base.

    Presets: traffic_cone, wizard_hat, ice_cream_cone, party_hat
    """
    PRESETS = {
        "traffic_cone": {"radius": 0.3, "height": 0.7, "detail": "medium"},
        "wizard_hat": {"radius": 0.4, "height": 1.2, "detail": "high"},
        "ice_cream_cone": {"radius": 0.15, "height": 0.4, "detail": "medium"},
        "party_hat": {"radius": 0.2, "height": 0.5, "detail": "low"},
    }

    def __init__(self, radius: float = 1.0, height: float = 2.0,
                 detail: Union[str, int] = "medium",
                 center: Optional[Tuple[float, float, float]] = None):
        super().__init__()
        self._radius = radius
        self._height = height
        self._center = center
        self._set_detail(detail)
        self._metadata["parameters"] = {
            "radius": radius, "height": height,
            "segments": self._segments, "center": center
        }

    def _set_detail(self, detail):
        if isinstance(detail, int):
            self._segments = detail
            self._metadata["detail_level"] = "custom"
        else:
            level = DetailLevel(detail.lower())
            self._segments = DETAIL_SEGMENTS[level]
            self._metadata["detail_level"] = detail

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_cone(
            self._radius, self._height,
            center=self._center, segments=self._segments
        ))


class Torus(PrimitiveBase):
    """
    Torus/Donut shape.

    Presets: food_donut, life_preserver, halo, tire, ring
    """
    PRESETS = {
        "food_donut": {"major_radius": 0.8, "minor_radius": 0.3, "detail": "high"},
        "life_preserver": {"major_radius": 1.2, "minor_radius": 0.15, "detail": "medium"},
        "halo": {"major_radius": 0.6, "minor_radius": 0.05, "detail": "very_high"},
        "tire": {"major_radius": 1.0, "minor_radius": 0.25, "detail": "medium"},
        "ring": {"major_radius": 0.5, "minor_radius": 0.05, "detail": "high"},
    }

    def __init__(self, major_radius: float = 1.5, minor_radius: float = 0.5,
                 detail: Union[str, Tuple[int, int]] = "medium",
                 center: Optional[Tuple[float, float, float]] = None):
        super().__init__()
        self._major_radius = major_radius
        self._minor_radius = minor_radius
        self._center = center
        self._set_detail(detail)
        self._metadata["parameters"] = {
            "major_radius": major_radius, "minor_radius": minor_radius,
            "major_segments": self._major_segments,
            "minor_segments": self._minor_segments, "center": center
        }

    def _set_detail(self, detail):
        if isinstance(detail, tuple):
            self._major_segments, self._minor_segments = detail
            self._metadata["detail_level"] = "custom"
        else:
            level = DetailLevel(detail.lower())
            base = DETAIL_SEGMENTS[level]
            self._major_segments = base
            self._minor_segments = max(8, base // 2)
            self._metadata["detail_level"] = detail

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_torus(
            self._major_radius, self._minor_radius,
            center=self._center,
            major_segments=self._major_segments,
            minor_segments=self._minor_segments
        ))


# ============================================================================
# EXTENDED PRIMITIVES (10)
# ============================================================================

class Capsule(PrimitiveBase):
    """
    Capsule - cylinder with hemispherical caps.

    Presets: player_hull, pill, bullet, medicine_capsule
    """
    PRESETS = {
        "player_hull": {"radius": 0.5, "height": 1.8, "detail": "low"},
        "pill": {"radius": 0.2, "height": 0.6, "detail": "medium"},
        "bullet": {"radius": 0.05, "height": 0.15, "detail": "low"},
        "medicine_capsule": {"radius": 0.15, "height": 0.4, "detail": "high"},
    }

    def __init__(self, radius: float = 0.5, height: float = 2.0,
                 detail: Union[str, Tuple[int, int]] = "medium"):
        super().__init__()
        self._radius = radius
        self._height = height
        self._set_detail(detail)
        self._metadata["parameters"] = {
            "radius": radius, "height": height,
            "rings": self._rings, "segments": self._segments
        }

    def _set_detail(self, detail):
        if isinstance(detail, tuple):
            self._rings, self._segments = detail
            self._metadata["detail_level"] = "custom"
        else:
            level = DetailLevel(detail.lower())
            base = DETAIL_SEGMENTS[level]
            self._rings = max(4, base // 4)
            self._segments = max(8, base // 2)
            self._metadata["detail_level"] = detail

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_capsule(
            self._radius, self._height,
            rings=self._rings, segments=self._segments
        ))


class Pyramid(PrimitiveBase):
    """
    Square pyramid.

    Presets: egyptian, step_pyramid, tent, roof
    """
    PRESETS = {
        "egyptian": {"base_size": 10.0, "height": 6.5},
        "step_pyramid": {"base_size": 8.0, "height": 4.0},
        "tent": {"base_size": 2.0, "height": 2.5},
        "roof": {"base_size": 5.0, "height": 2.0},
    }

    def __init__(self, base_size: float = 2.0, height: float = 2.0):
        super().__init__()
        self._base_size = base_size
        self._height = height
        self._metadata["parameters"] = {"base_size": base_size, "height": height}

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_pyramid(self._base_size, self._height))


class Plane(PrimitiveBase):
    """
    Flat subdivided plane.

    Presets: floor, wall, ceiling, terrain_tile
    """
    PRESETS = {
        "floor": {"width": 10.0, "depth": 10.0},
        "wall": {"width": 5.0, "depth": 3.0},
        "ceiling": {"width": 10.0, "depth": 10.0},
        "terrain_tile": {"width": 100.0, "depth": 100.0},
    }

    def __init__(self, width: float = 2.0, depth: float = 2.0):
        super().__init__()
        self._width = width
        self._depth = depth
        self._metadata["parameters"] = {"width": width, "depth": depth}

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_plane(self._width, self._depth))


class Disc(PrimitiveBase):
    """
    Filled circle disc.

    Presets: coin, button, plate, manhole_cover
    """
    PRESETS = {
        "coin": {"radius": 0.012},
        "button": {"radius": 0.015},
        "plate": {"radius": 0.15},
        "manhole_cover": {"radius": 0.4},
    }

    def __init__(self, radius: float = 1.0):
        super().__init__()
        self._radius = radius
        self._metadata["parameters"] = {"radius": radius}

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_disc(self._radius))


class Ring(PrimitiveBase):
    """
    Hollow circle/annulus.

    Presets: washer, gasket, arena, moat
    """
    PRESETS = {
        "washer": {"inner_radius": 0.01, "outer_radius": 0.02},
        "gasket": {"inner_radius": 0.05, "outer_radius": 0.08},
        "arena": {"inner_radius": 10.0, "outer_radius": 12.0},
        "moat": {"inner_radius": 5.0, "outer_radius": 8.0},
    }

    def __init__(self, inner_radius: float = 0.5, outer_radius: float = 1.0):
        super().__init__()
        self._inner_radius = inner_radius
        self._outer_radius = outer_radius
        self._metadata["parameters"] = {
            "inner_radius": inner_radius,
            "outer_radius": outer_radius
        }

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_ring(self._inner_radius, self._outer_radius))


class Tube(PrimitiveBase):
    """
    Hollow cylinder.

    Presets: pipe_segment, straw, telescope, cannon
    """
    PRESETS = {
        "pipe_segment": {"inner_radius": 0.04, "outer_radius": 0.05, "height": 1.0},
        "straw": {"inner_radius": 0.003, "outer_radius": 0.004, "height": 0.2},
        "telescope": {"inner_radius": 0.03, "outer_radius": 0.035, "height": 0.5},
        "cannon": {"inner_radius": 0.08, "outer_radius": 0.12, "height": 2.0},
    }

    def __init__(self, inner_radius: float = 0.4, outer_radius: float = 0.5,
                 height: float = 2.0):
        super().__init__()
        self._inner_radius = inner_radius
        self._outer_radius = outer_radius
        self._height = height
        self._metadata["parameters"] = {
            "inner_radius": inner_radius,
            "outer_radius": outer_radius,
            "height": height
        }

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_tube(
            self._inner_radius, self._outer_radius, self._height
        ))


class Prism(PrimitiveBase):
    """
    Prism - 3/6/8 sided.

    Presets: triangular_tent, hex_column, octa_column, crystal
    """
    PRESETS = {
        "triangular_tent": {"radius": 1.0, "height": 2.0, "sides": 3},
        "hex_column": {"radius": 0.5, "height": 3.0, "sides": 6},
        "octa_column": {"radius": 0.6, "height": 2.5, "sides": 8},
        "crystal": {"radius": 0.2, "height": 0.8, "sides": 6},
    }

    def __init__(self, radius: float = 1.0, height: float = 2.0, sides: int = 6):
        super().__init__()
        if sides not in [3, 6, 8]:
            raise ValueError("Prism sides must be 3, 6, or 8")
        self._radius = radius
        self._height = height
        self._sides = sides
        self._metadata["parameters"] = {
            "radius": radius, "height": height, "sides": sides
        }

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_prism(self._radius, self._height, self._sides))


class Dome(PrimitiveBase):
    """
    Hemisphere dome.

    Presets: planetarium, igloo, radar_dome, observatory
    """
    PRESETS = {
        "planetarium": {"radius": 15.0},
        "igloo": {"radius": 2.0},
        "radar_dome": {"radius": 5.0},
        "observatory": {"radius": 8.0},
    }

    def __init__(self, radius: float = 1.0):
        super().__init__()
        self._radius = radius
        self._metadata["parameters"] = {"radius": radius}

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_dome(self._radius))


class Tetrahedron(PrimitiveBase):
    """
    4-sided platonic solid.

    Presets: d4_die, spike, caltrops
    """
    PRESETS = {
        "d4_die": {"size": 0.02},
        "spike": {"size": 0.3},
        "caltrops": {"size": 0.1},
    }

    def __init__(self, size: float = 1.0):
        super().__init__()
        self._size = size
        self._metadata["parameters"] = {"size": size}

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_tetrahedron(self._size))


class Octahedron(PrimitiveBase):
    """
    8-sided platonic solid.

    Presets: d8_die, gem, crystal_shard
    """
    PRESETS = {
        "d8_die": {"size": 0.02},
        "gem": {"size": 0.05},
        "crystal_shard": {"size": 0.15},
    }

    def __init__(self, size: float = 1.0):
        super().__init__()
        self._size = size
        self._metadata["parameters"] = {"size": size}

    @classmethod
    def preset(cls, name: str):
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown preset '{name}'. Available: {', '.join(cls.PRESETS.keys())}")
        return cls(**cls.PRESETS[name])

    def _build_mesh(self) -> Mesh:
        return Mesh(_vfc.create_octahedron(self._size))


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Basic primitives
    "Box", "Sphere", "Cylinder", "Cone", "Torus",
    # Extended primitives
    "Capsule", "Pyramid", "Plane", "Disc", "Ring",
    "Tube", "Prism", "Dome", "Tetrahedron", "Octahedron",
    # Helpers
    "DetailLevel", "PrimitiveBase",
]
