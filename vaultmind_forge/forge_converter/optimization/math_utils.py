"""
VaultMind Forge - Optimization Math Utilities

Precise mathematical calculations for asset optimization:
- Quadric error metrics for mesh decimation
- LOD distance and screen coverage calculations
- Texture compression ratios
- Coordinate system transformations
- UV optimization

IMPORTANT: All calculations must be mathematically precise.
These values directly affect visual quality and performance.
"""

from __future__ import annotations

import math
import numpy as np
from typing import Tuple, List, Optional
from dataclasses import dataclass
from enum import Enum


class CoordinateSystem(Enum):
    """3D coordinate system definitions"""
    RIGHT_HANDED_Y_UP = "right_handed_y_up"  # Unity, Maya, GLTF
    RIGHT_HANDED_Z_UP = "right_handed_z_up"  # Blender
    LEFT_HANDED_Y_UP = "left_handed_y_up"    # Unreal, DirectX
    LEFT_HANDED_Z_UP = "left_handed_z_up"    # 3ds Max


@dataclass
class Vertex:
    """3D vertex with position, normal, and UV coordinates"""
    position: np.ndarray  # [x, y, z]
    normal: np.ndarray    # [nx, ny, nz]
    uv: np.ndarray        # [u, v]

    def __post_init__(self):
        self.position = np.array(self.position, dtype=np.float64)
        self.normal = np.array(self.normal, dtype=np.float64)
        self.uv = np.array(self.uv, dtype=np.float64)


@dataclass
class QuadricError:
    """Quadric error matrix for mesh decimation (Garland-Heckbert 1997)"""
    # Q = [a, b, c, d]^T * [a, b, c, d] where ax + by + cz + d = 0
    matrix: np.ndarray  # 4x4 symmetric matrix

    def __init__(self, a: float = 0, b: float = 0, c: float = 0, d: float = 0):
        """Initialize from plane equation ax + by + cz + d = 0"""
        plane = np.array([a, b, c, d], dtype=np.float64)
        # Q = plane^T * plane (outer product)
        self.matrix = np.outer(plane, plane)

    @classmethod
    def from_triangle(cls, v1: np.ndarray, v2: np.ndarray, v3: np.ndarray) -> QuadricError:
        """Compute quadric from triangle vertices"""
        # Compute triangle normal
        edge1 = v2 - v1
        edge2 = v3 - v1
        normal = np.cross(edge1, edge2)
        normal_length = np.linalg.norm(normal)

        if normal_length < 1e-10:
            # Degenerate triangle
            return cls(0, 0, 0, 0)

        normal = normal / normal_length

        # Plane equation: nx*x + ny*y + nz*z + d = 0
        # d = -(nx*x1 + ny*y1 + nz*z1)
        d = -np.dot(normal, v1)

        return cls(normal[0], normal[1], normal[2], d)

    def __add__(self, other: QuadricError) -> QuadricError:
        """Add two quadric matrices"""
        result = QuadricError()
        result.matrix = self.matrix + other.matrix
        return result

    def compute_error(self, vertex: np.ndarray) -> float:
        """
        Compute quadric error for a vertex position.
        Error = v^T * Q * v where v = [x, y, z, 1]
        """
        v = np.array([vertex[0], vertex[1], vertex[2], 1.0], dtype=np.float64)
        error = np.dot(v, np.dot(self.matrix, v))
        return max(0.0, error)  # Ensure non-negative

    def optimal_position(self, v1: np.ndarray, v2: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Find optimal vertex position for edge collapse (v1, v2).
        Solves: Q * v = 0

        Returns:
            (optimal_position, error)
        """
        # Try to solve Q * [x, y, z, 1]^T = 0
        # This is the position that minimizes quadric error

        # Build matrix for solution
        A = self.matrix.copy()
        A[3, :] = [0, 0, 0, 1]  # Set last row to [0,0,0,1]

        try:
            # Solve for optimal position
            b = np.array([0, 0, 0, 1], dtype=np.float64)
            v_optimal = np.linalg.solve(A, b)
            optimal_pos = v_optimal[:3]
            error = self.compute_error(optimal_pos)

            return optimal_pos, error
        except np.linalg.LinAlgError:
            # Matrix is singular, use midpoint instead
            midpoint = (v1 + v2) / 2.0
            error = self.compute_error(midpoint)
            return midpoint, error


class LODCalculator:
    """LOD distance and screen coverage calculations"""

    @staticmethod
    def screen_coverage_to_distance(
        screen_coverage: float,
        object_radius: float,
        fov_degrees: float = 60.0,
        screen_height: int = 1080
    ) -> float:
        """
        Calculate camera distance for a given screen coverage percentage.

        Args:
            screen_coverage: Target screen coverage (0.0-1.0)
            object_radius: Bounding sphere radius of object
            fov_degrees: Vertical field of view in degrees
            screen_height: Screen height in pixels

        Returns:
            Camera distance from object center
        """
        if screen_coverage <= 0:
            return float('inf')

        # Convert FOV to radians
        fov_rad = math.radians(fov_degrees)

        # Calculate distance
        # screen_size = 2 * object_radius (when object fills screen)
        # At distance d: tan(fov/2) = (screen_size/2) / d
        # d = (screen_size/2) / tan(fov/2)

        # Desired screen size = object_radius * 2 * screen_coverage
        desired_screen_size = object_radius * 2.0 * screen_coverage

        # Calculate distance
        distance = (desired_screen_size / 2.0) / math.tan(fov_rad / 2.0)

        return max(distance, 0.01)  # Ensure positive distance

    @staticmethod
    def distance_to_screen_coverage(
        distance: float,
        object_radius: float,
        fov_degrees: float = 60.0
    ) -> float:
        """
        Calculate screen coverage percentage at a given distance.

        Args:
            distance: Camera distance from object
            object_radius: Bounding sphere radius
            fov_degrees: Vertical field of view in degrees

        Returns:
            Screen coverage (0.0-1.0)
        """
        if distance <= 0:
            return 1.0

        fov_rad = math.radians(fov_degrees)

        # Screen height at this distance
        screen_size_at_distance = 2.0 * distance * math.tan(fov_rad / 2.0)

        # Object size on screen
        object_screen_size = object_radius * 2.0

        # Coverage percentage
        coverage = object_screen_size / screen_size_at_distance

        return min(max(coverage, 0.0), 1.0)  # Clamp to [0, 1]

    @staticmethod
    def calculate_lod_distances(
        object_radius: float,
        lod_screen_coverages: List[float],
        fov_degrees: float = 60.0,
        screen_height: int = 1080
    ) -> List[float]:
        """
        Calculate LOD switching distances for each LOD level.

        Args:
            object_radius: Bounding sphere radius
            lod_screen_coverages: List of screen coverage thresholds per LOD
            fov_degrees: Vertical field of view
            screen_height: Screen height in pixels

        Returns:
            List of distances where each LOD should activate
        """
        distances = []
        for coverage in lod_screen_coverages:
            dist = LODCalculator.screen_coverage_to_distance(
                coverage, object_radius, fov_degrees, screen_height
            )
            distances.append(dist)

        return distances


class MeshDecimator:
    """Mesh decimation using quadric error metrics"""

    @staticmethod
    def calculate_target_poly_count(
        current_poly_count: int,
        reduction_percentage: float
    ) -> int:
        """
        Calculate target polygon count from reduction percentage.

        Args:
            current_poly_count: Current number of polygons
            reduction_percentage: Reduction (0.0 = no reduction, 1.0 = maximum)

        Returns:
            Target polygon count
        """
        reduction_percentage = max(0.0, min(1.0, reduction_percentage))
        target = int(current_poly_count * (1.0 - reduction_percentage))
        return max(target, 4)  # Minimum 4 triangles (tetrahedron)

    @staticmethod
    def calculate_reduction_percentage(
        current_poly_count: int,
        target_poly_count: int
    ) -> float:
        """
        Calculate reduction percentage from target poly count.

        Args:
            current_poly_count: Current number of polygons
            target_poly_count: Target number of polygons

        Returns:
            Reduction percentage (0.0-1.0)
        """
        if current_poly_count <= 0:
            return 0.0

        reduction = 1.0 - (target_poly_count / current_poly_count)
        return max(0.0, min(1.0, reduction))


class TextureOptimizer:
    """Texture size and compression calculations"""

    @staticmethod
    def calculate_mipmap_sizes(
        base_width: int,
        base_height: int,
        num_levels: int = -1
    ) -> List[Tuple[int, int]]:
        """
        Calculate mipmap chain dimensions.

        Args:
            base_width: Base texture width
            base_height: Base texture height
            num_levels: Number of mip levels (-1 = full chain to 1x1)

        Returns:
            List of (width, height) tuples for each mip level
        """
        mip_levels = [(base_width, base_height)]

        width = base_width
        height = base_height

        max_levels = int(math.log2(max(base_width, base_height))) + 1
        if num_levels < 0:
            num_levels = max_levels
        else:
            num_levels = min(num_levels, max_levels)

        for _ in range(num_levels - 1):
            width = max(1, width // 2)
            height = max(1, height // 2)
            mip_levels.append((width, height))

            if width == 1 and height == 1:
                break

        return mip_levels

    @staticmethod
    def calculate_memory_usage(
        width: int,
        height: int,
        bits_per_pixel: int,
        include_mipmaps: bool = True
    ) -> int:
        """
        Calculate texture memory usage in bytes.

        Args:
            width: Texture width
            height: Texture height
            bits_per_pixel: Bits per pixel (e.g., 32 for RGBA8, 8 for BC4)
            include_mipmaps: Include mipmap chain in calculation

        Returns:
            Total memory usage in bytes
        """
        bytes_per_pixel = bits_per_pixel / 8.0
        base_size = int(width * height * bytes_per_pixel)

        if not include_mipmaps:
            return base_size

        # Mipmap chain adds ~33% (sum of 1/4 + 1/16 + 1/64 + ...)
        # Exact formula: sum from i=0 to infinity of (1/4)^i = 4/3
        total_size = int(base_size * 4.0 / 3.0)

        return total_size

    @staticmethod
    def compression_ratio(
        uncompressed_bpp: int,
        compressed_bpp: int
    ) -> float:
        """
        Calculate compression ratio.

        Args:
            uncompressed_bpp: Uncompressed bits per pixel
            compressed_bpp: Compressed bits per pixel

        Returns:
            Compression ratio (e.g., 4.0 means 4:1 compression)
        """
        if compressed_bpp == 0:
            return 0.0
        return uncompressed_bpp / compressed_bpp

    @staticmethod
    def next_power_of_two(value: int) -> int:
        """Round up to next power of two"""
        if value <= 0:
            return 1
        return 2 ** math.ceil(math.log2(value))

    @staticmethod
    def resize_to_power_of_two(
        width: int,
        height: int,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        Resize texture to power-of-two dimensions.

        Args:
            width: Current width
            height: Current height
            max_width: Maximum width constraint
            max_height: Maximum height constraint

        Returns:
            (new_width, new_height) as power-of-two dimensions
        """
        new_width = TextureOptimizer.next_power_of_two(width)
        new_height = TextureOptimizer.next_power_of_two(height)

        if max_width is not None:
            new_width = min(new_width, max_width)

        if max_height is not None:
            new_height = min(new_height, max_height)

        return new_width, new_height


class CoordinateTransformer:
    """Coordinate system transformations"""

    # Transformation matrices between coordinate systems
    TRANSFORMS = {
        (CoordinateSystem.RIGHT_HANDED_Y_UP, CoordinateSystem.RIGHT_HANDED_Z_UP): np.array([
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, -1, 0, 0],
            [0, 0, 0, 1]
        ], dtype=np.float64),

        (CoordinateSystem.RIGHT_HANDED_Y_UP, CoordinateSystem.LEFT_HANDED_Y_UP): np.array([
            [-1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float64),

        (CoordinateSystem.RIGHT_HANDED_Z_UP, CoordinateSystem.RIGHT_HANDED_Y_UP): np.array([
            [1, 0, 0, 0],
            [0, 0, -1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1]
        ], dtype=np.float64),
    }

    @classmethod
    def transform_vertex(
        cls,
        vertex: np.ndarray,
        from_system: CoordinateSystem,
        to_system: CoordinateSystem,
        scale: float = 1.0
    ) -> np.ndarray:
        """
        Transform vertex from one coordinate system to another.

        Args:
            vertex: Vertex position [x, y, z]
            from_system: Source coordinate system
            to_system: Target coordinate system
            scale: Unit scale factor

        Returns:
            Transformed vertex position
        """
        if from_system == to_system and scale == 1.0:
            return vertex.copy()

        # Get transformation matrix
        key = (from_system, to_system)
        if key in cls.TRANSFORMS:
            matrix = cls.TRANSFORMS[key]
        else:
            # Identity if no specific transform defined
            matrix = np.eye(4, dtype=np.float64)

        # Apply scale
        if scale != 1.0:
            scale_matrix = np.eye(4, dtype=np.float64)
            scale_matrix[0:3, 0:3] *= scale
            matrix = np.dot(scale_matrix, matrix)

        # Transform vertex
        v = np.array([vertex[0], vertex[1], vertex[2], 1.0], dtype=np.float64)
        transformed = np.dot(matrix, v)

        return transformed[:3]


class UVOptimizer:
    """UV coordinate optimization"""

    @staticmethod
    def calculate_uv_area(uvs: List[Tuple[float, float]]) -> float:
        """
        Calculate area of UV triangle.

        Args:
            uvs: List of 3 UV coordinates [(u1,v1), (u2,v2), (u3,v3)]

        Returns:
            UV triangle area
        """
        if len(uvs) != 3:
            return 0.0

        u1, v1 = uvs[0]
        u2, v2 = uvs[1]
        u3, v3 = uvs[2]

        # Shoelace formula
        area = abs((u1 * (v2 - v3) + u2 * (v3 - v1) + u3 * (v1 - v2)) / 2.0)

        return area

    @staticmethod
    def detect_uv_overlap(
        uv_triangles: List[List[Tuple[float, float]]],
        tolerance: float = 1e-6
    ) -> float:
        """
        Detect UV overlap percentage.

        Args:
            uv_triangles: List of UV triangles
            tolerance: Overlap detection tolerance

        Returns:
            Overlap percentage (0.0-1.0)
        """
        # Simple implementation - real version would use spatial indexing
        total_area = sum(UVOptimizer.calculate_uv_area(tri) for tri in uv_triangles)

        if total_area == 0:
            return 0.0

        # This is a simplified placeholder
        # Full implementation would check for actual triangle intersections
        return 0.0  # TODO: Implement proper overlap detection


# Compression format bits per pixel (for memory calculations)
COMPRESSION_BPP = {
    'bc1': 4,   # DXT1
    'bc3': 8,   # DXT5
    'bc4': 4,   # Single channel
    'bc5': 8,   # Two channel (normal maps)
    'bc7': 8,   # High quality
    'etc2': 4,  # Mobile
    'astc': 8,  # Mobile (can vary)
    'rgba8': 32,
    'rgb8': 24,
    'rg8': 16,
    'r8': 8,
}
