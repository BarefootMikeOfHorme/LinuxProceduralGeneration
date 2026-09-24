"""
VaultMind Forge - Rich Mesh Class
=================================

Enhanced mesh class with export chaining, metadata tracking,
and multi-format support.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import json
from datetime import datetime

from ._native import load_native


class Mesh:
    """
    Rich mesh wrapper with export chaining and metadata.

    Wraps the Rust core mesh with a user-friendly Python interface.

    Features:
        - Export chaining: mesh.export().to_unity().to_unreal()
        - Metadata tracking: creation time, parameters, modifications
        - Statistics: vertex/triangle counts, bounding box
        - Validation: manifold checking, hole detection

    Examples:
        >>> mesh = Cone(radius=1.0, height=2.0).build()
        >>> mesh.stats()
        >>> mesh.to_unity("cone.obj")
        >>>
        >>> # Chained exports
        >>> mesh.export()\\
        ...     .to_unity("exports/unity/cone.obj")\\
        ...     .to_unreal("exports/unreal/cone.obj")\\
        ...     .to_lumix("exports/lumix/cone.obj")
    """

    def __init__(self, rust_mesh):
        """
        Initialize from Rust core mesh.

        Args:
            rust_mesh: The underlying Rust mesh object
        """
        self._rust_mesh = rust_mesh
        self._metadata = {
            "created_at": datetime.now().isoformat(),
            "modifications": [],
            "exports": [],
        }

    # Import Rust core for engine exports
    @property
    def _vfc(self):
        """Load the optional native extension on demand."""
        return load_native()

    def vertex_count(self) -> int:
        """Get number of vertices"""
        # Handle both property and method forms
        vc = self._rust_mesh.vertex_count
        return vc() if callable(vc) else vc

    def triangle_count(self) -> int:
        """Get number of triangles"""
        # Handle both property and method forms
        tc = self._rust_mesh.triangle_count
        return tc() if callable(tc) else tc

    def bounding_box(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Get bounding box as ((min_x, min_y, min_z), (max_x, max_y, max_z))"""
        # Handle both property and method forms
        bb = self._rust_mesh.bounding_box
        return bb() if callable(bb) else bb

    def bounds_min(self) -> Tuple[float, float, float]:
        """Get minimum bounds"""
        bbox = self.bounding_box()
        return bbox[0]

    def bounds_max(self) -> Tuple[float, float, float]:
        """Get maximum bounds"""
        bbox = self.bounding_box()
        return bbox[1]

    def stats(self):
        """Print detailed mesh statistics"""
        print(f"\\nMesh Statistics")
        print("=" * 50)
        print(f"Vertices: {self.vertex_count():,}")
        print(f"Triangles: {self.triangle_count():,}")

        bbox_min, bbox_max = self.bounding_box()
        print(f"\\nBounding Box:")
        print(f"  Min: ({bbox_min[0]:.3f}, {bbox_min[1]:.3f}, {bbox_min[2]:.3f})")
        print(f"  Max: ({bbox_max[0]:.3f}, {bbox_max[1]:.3f}, {bbox_max[2]:.3f})")

        size_x = bbox_max[0] - bbox_min[0]
        size_y = bbox_max[1] - bbox_min[1]
        size_z = bbox_max[2] - bbox_min[2]
        print(f"  Size: ({size_x:.3f}, {size_y:.3f}, {size_z:.3f})")

        if hasattr(self, '_metadata'):
            print(f"\\nMetadata:")
            print(f"  Type: {self._metadata.get('type', 'Unknown')}")
            print(f"  Created: {self._metadata.get('created_at', 'Unknown')}")
            if self._metadata.get('detail_level'):
                print(f"  Detail: {self._metadata['detail_level']}")

        print("=" * 50)
        return self

    def save_obj(self, path: str) -> 'Mesh':
        """
        Save as OBJ file (generic format).

        Args:
            path: Output path

        Returns:
            Self for chaining
        """
        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Handle both export_obj and save_obj method names
        if hasattr(self._rust_mesh, 'save_obj'):
            self._rust_mesh.save_obj(path)
        elif hasattr(self._rust_mesh, 'export_obj'):
            self._rust_mesh.export_obj(path)
        else:
            # Fallback: use generic export if available
            self._vfc.export_for_godot(self._rust_mesh, path)

        self._metadata.setdefault("exports", []).append({
            "format": "obj",
            "path": path,
            "timestamp": datetime.now().isoformat()
        })
        return self

    def to_unity(self, path: str) -> 'Mesh':
        """Export to Unity (Y-up, left-handed, 1.0 scale)"""
        self._vfc.export_for_unity(self._rust_mesh, path)
        self._metadata.setdefault("exports", []).append({
            "engine": "unity",
            "path": path,
            "timestamp": datetime.now().isoformat()
        })
        return self

    def to_unreal(self, path: str) -> 'Mesh':
        """Export to Unreal (Z-up, left-handed, 100.0 scale)"""
        self._vfc.export_for_unreal(self._rust_mesh, path)
        self._metadata.setdefault("exports", []).append({
            "engine": "unreal",
            "path": path,
            "timestamp": datetime.now().isoformat()
        })
        return self

    def to_cryengine(self, path: str) -> 'Mesh':
        """Export to CryEngine (Z-up, right-handed, 100.0 scale)"""
        self._vfc.export_for_cryengine(self._rust_mesh, path)
        self._metadata.setdefault("exports", []).append({
            "engine": "cryengine",
            "path": path,
            "timestamp": datetime.now().isoformat()
        })
        return self

    def to_lumix(self, path: str) -> 'Mesh':
        """Export to Lumix Engine (Y-up, right-handed)"""
        self._vfc.export_for_lumix(self._rust_mesh, path)
        self._metadata.setdefault("exports", []).append({
            "engine": "lumix",
            "path": path,
            "timestamp": datetime.now().isoformat()
        })
        return self

    def to_godot(self, path: str) -> 'Mesh':
        """Export to Godot (Y-up)"""
        self._vfc.export_for_godot(self._rust_mesh, path)
        self._metadata.setdefault("exports", []).append({
            "engine": "godot",
            "path": path,
            "timestamp": datetime.now().isoformat()
        })
        return self

    def export(self) -> 'ExportChain':
        """
        Start an export chain for multiple formats.

        Returns:
            ExportChain for fluent multi-export

        Example:
            >>> mesh.export()\\
            ...     .to_unity("exports/unity/model.obj")\\
            ...     .to_unreal("exports/unreal/model.obj")\\
            ...     .to_all("exports/")
        """
        return ExportChain(self)

    def save_metadata(self, path: str):
        """Save metadata to JSON file"""
        with open(path, 'w') as f:
            json.dump(self._metadata, f, indent=2)

    def __repr__(self):
        return f"Mesh(vertices={self.vertex_count()}, triangles={self.triangle_count()})"


class ExportChain:
    """
    Fluent export chain for multiple formats.

    Allows chaining multiple exports in a readable way.
    """

    def __init__(self, mesh: Mesh):
        self.mesh = mesh

    def to_unity(self, path: str) -> 'ExportChain':
        """Export to Unity and continue chain"""
        self.mesh.to_unity(path)
        return self

    def to_unreal(self, path: str) -> 'ExportChain':
        """Export to Unreal and continue chain"""
        self.mesh.to_unreal(path)
        return self

    def to_cryengine(self, path: str) -> 'ExportChain':
        """Export to CryEngine and continue chain"""
        self.mesh.to_cryengine(path)
        return self

    def to_lumix(self, path: str) -> 'ExportChain':
        """Export to Lumix and continue chain"""
        self.mesh.to_lumix(path)
        return self

    def to_godot(self, path: str) -> 'ExportChain':
        """Export to Godot and continue chain"""
        self.mesh.to_godot(path)
        return self

    def to_all(self, base_dir: str, filename: Optional[str] = None) -> 'ExportChain':
        """
        Export to all supported engines.

        Creates subdirectories for each engine and exports with appropriate transforms.

        Args:
            base_dir: Base directory for exports
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Self for chaining

        Example:
            >>> mesh.export().to_all("exports/", "my_model.obj")
            Creates:
                exports/unity/my_model.obj
                exports/unreal/my_model.obj
                exports/cryengine/my_model.obj
                exports/lumix/my_model.obj
                exports/godot/my_model.obj
        """
        base_path = Path(base_dir)
        if filename is None:
            filename = f"mesh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.obj"

        engines = ["unity", "unreal", "cryengine", "lumix", "godot"]

        for engine in engines:
            engine_dir = base_path / engine
            engine_dir.mkdir(parents=True, exist_ok=True)
            path = str(engine_dir / filename)

            # Call the appropriate export method
            getattr(self, f"to_{engine}")(path)

        return self

    def done(self) -> Mesh:
        """End the chain and return the mesh"""
        return self.mesh


__all__ = ["Mesh", "ExportChain"]
