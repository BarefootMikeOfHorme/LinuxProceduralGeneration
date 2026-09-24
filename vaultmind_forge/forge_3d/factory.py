"""
VaultMind Forge - Template & Batch Generation System
====================================================

Parametric templates, variation generation, and batch asset creation.

Features:
    - Template definitions with parameters
    - Variation generation (randomize within ranges)
    - Asset collections (organize related assets)
    - Theme/style application (faction aesthetics)
    - Batch export to multiple engines

Examples:
    >>> # Define a template
    >>> factory = Factory()
    >>> pillar_template = factory.create_template(
    ...     "gothic_pillar",
    ...     base_primitive="Cylinder",
    ...     params={"radius": 0.8, "height": 5.0, "detail": "high"}
    ... )
    >>>
    >>> # Generate variations
    >>> pillars = pillar_template.generate_variations(
    ...     count=20,
    ...     randomize={"radius": (0.6, 1.0), "height": (4.0, 6.0)}
    ... )
    >>>
    >>> # Create asset collection
    >>> collection = AssetCollection("medieval_props")
    >>> collection.add_template(pillar_template, count=10)
    >>> collection.export_all(["unity", "unreal"])
"""

import random
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from pathlib import Path
from datetime import datetime
import json

from . import primitives_all as prim
from .mesh import Mesh


class Template:
    """
    Parametric template for generating variations of an asset.

    A template defines a base primitive type and configurable parameters,
    allowing batch generation of similar but varied assets.

    Examples:
        >>> # Create template
        >>> template = Template(
        ...     name="storage_crate",
        ...     primitive_type="Box",
        ...     base_params={"size": 1.0}
        ... )
        >>>
        >>> # Generate single asset
        >>> crate = template.generate()
        >>>
        >>> # Generate variations
        >>> crates = template.generate_variations(
        ...     count=25,
        ...     randomize={"size": (0.8, 1.2)}
        ... )
    """

    def __init__(
        self,
        name: str,
        primitive_type: str,
        base_params: Dict[str, Any],
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Initialize template.

        Args:
            name: Template name
            primitive_type: Primitive class name (e.g., "Box", "Cylinder")
            base_params: Default parameters for the primitive
            description: Optional description
            tags: Optional tags for organization
        """
        self.name = name
        self.primitive_type = primitive_type
        self.base_params = base_params.copy()
        self.description = description or f"{name} template"
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()

        # Validate primitive type exists
        if not hasattr(prim, primitive_type):
            raise ValueError(
                f"Unknown primitive type: {primitive_type}. "
                f"Available: {', '.join(prim.__all__)}"
            )

    def generate(self, **override_params) -> Mesh:
        """
        Generate a single mesh from this template.

        Args:
            **override_params: Parameters to override base_params

        Returns:
            Generated Mesh

        Example:
            >>> template = Template("pillar", "Cylinder", {"radius": 0.5, "height": 3.0})
            >>> tall_pillar = template.generate(height=5.0)
        """
        # Merge base params with overrides
        params = self.base_params.copy()
        params.update(override_params)

        # Get primitive class
        primitive_class = getattr(prim, self.primitive_type)

        # Create primitive
        primitive = primitive_class(**params)

        # Build mesh and add template metadata
        mesh = primitive.build()
        mesh._metadata["template"] = self.name
        mesh._metadata["template_params"] = params

        return mesh

    def generate_variations(
        self,
        count: int,
        randomize: Optional[Dict[str, Union[Tuple[float, float], List[Any]]]] = None,
        seed: Optional[int] = None
    ) -> List[Mesh]:
        """
        Generate multiple variations of this template.

        Args:
            count: Number of variations to generate
            randomize: Dict of parameter ranges to randomize
                      - For numeric: (min, max) tuple
                      - For categorical: list of options
            seed: Random seed for reproducibility

        Returns:
            List of generated meshes

        Examples:
            >>> # Numeric randomization
            >>> variations = template.generate_variations(
            ...     count=20,
            ...     randomize={"radius": (0.4, 0.8), "height": (2.5, 3.5)}
            ... )
            >>>
            >>> # Categorical randomization
            >>> variations = template.generate_variations(
            ...     count=10,
            ...     randomize={"detail": ["low", "medium", "high"]}
            ... )
        """
        if seed is not None:
            random.seed(seed)

        variations = []

        for i in range(count):
            # Start with base params
            variant_params = self.base_params.copy()

            # Apply randomization
            if randomize:
                for param, value_range in randomize.items():
                    if isinstance(value_range, tuple) and len(value_range) == 2:
                        # Numeric range: (min, max)
                        min_val, max_val = value_range
                        variant_params[param] = random.uniform(min_val, max_val)
                    elif isinstance(value_range, list):
                        # Categorical: pick random option
                        variant_params[param] = random.choice(value_range)

            # Generate mesh
            mesh = self.generate(**variant_params)
            mesh._metadata["variation_index"] = i
            mesh._metadata["variation_of"] = self.name

            variations.append(mesh)

        return variations

    def apply_theme(self, theme: Dict[str, Any]) -> 'Template':
        """
        Apply a theme/style to this template.

        Creates a new template with theme parameters applied.

        Args:
            theme: Theme parameters to merge with base params

        Returns:
            New template with theme applied

        Example:
            >>> dwarven_theme = {"detail": "high", "size_multiplier": 1.2}
            >>> dwarven_pillar = pillar_template.apply_theme(dwarven_theme)
        """
        themed_params = self.base_params.copy()

        # Apply theme parameters
        for key, value in theme.items():
            if key == "size_multiplier" and "size" in themed_params:
                themed_params["size"] *= value
            elif key == "radius_multiplier" and "radius" in themed_params:
                themed_params["radius"] *= value
            elif key == "height_multiplier" and "height" in themed_params:
                themed_params["height"] *= value
            else:
                themed_params[key] = value

        # Create new themed template
        themed_template = Template(
            name=f"{self.name}_themed",
            primitive_type=self.primitive_type,
            base_params=themed_params,
            description=f"{self.description} (themed)",
            tags=self.tags + ["themed"]
        )

        return themed_template

    def save(self, path: str):
        """Save template definition to JSON"""
        data = {
            "name": self.name,
            "primitive_type": self.primitive_type,
            "base_params": self.base_params,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'Template':
        """Load template definition from JSON"""
        with open(path, 'r') as f:
            data = json.load(f)

        return cls(
            name=data["name"],
            primitive_type=data["primitive_type"],
            base_params=data["base_params"],
            description=data.get("description"),
            tags=data.get("tags")
        )

    def __repr__(self):
        return f"Template('{self.name}', {self.primitive_type}, {len(self.base_params)} params)"


class AssetCollection:
    """
    Collection of related assets for batch management and export.

    Organizes multiple assets (from templates or direct creation) and
    provides batch export, naming, and organization capabilities.

    Examples:
        >>> # Create collection
        >>> collection = AssetCollection("medieval_props")
        >>>
        >>> # Add from templates
        >>> collection.add_template(crate_template, count=25, prefix="crate")
        >>> collection.add_template(barrel_template, count=15, prefix="barrel")
        >>>
        >>> # Add direct meshes
        >>> collection.add_mesh("special_item", unique_mesh)
        >>>
        >>> # Export all to multiple engines
        >>> collection.export_all(["unity", "unreal"], output_dir="assets/")
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize asset collection.

        Args:
            name: Collection name
            description: Optional description
        """
        self.name = name
        self.description = description or f"{name} asset collection"
        self.assets: Dict[str, Mesh] = {}
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "templates_used": [],
            "total_assets": 0
        }

    def add_mesh(self, name: str, mesh: Mesh) -> 'AssetCollection':
        """
        Add a single mesh to the collection.

        Args:
            name: Asset name (used for filename)
            mesh: Mesh to add

        Returns:
            Self for chaining
        """
        self.assets[name] = mesh
        self.metadata["total_assets"] = len(self.assets)
        return self

    def add_template(
        self,
        template: Template,
        count: int = 1,
        prefix: Optional[str] = None,
        **variation_kwargs
    ) -> 'AssetCollection':
        """
        Add assets from a template to the collection.

        Args:
            template: Template to generate from
            count: Number of variations to generate
            prefix: Prefix for asset names
            **variation_kwargs: Passed to template.generate_variations()

        Returns:
            Self for chaining

        Example:
            >>> collection.add_template(
            ...     crate_template,
            ...     count=20,
            ...     prefix="crate",
            ...     randomize={"size": (0.8, 1.2)}
            ... )
        """
        prefix = prefix or template.name

        # Generate variations
        if count == 1:
            meshes = [template.generate()]
        else:
            meshes = template.generate_variations(count, **variation_kwargs)

        # Add to collection
        for i, mesh in enumerate(meshes):
            name = f"{prefix}_{i:03d}" if count > 1 else prefix
            self.assets[name] = mesh

        # Track template usage
        if template.name not in self.metadata["templates_used"]:
            self.metadata["templates_used"].append(template.name)

        self.metadata["total_assets"] = len(self.assets)

        return self

    def add_preset_batch(
        self,
        primitive_type: str,
        preset_names: List[str],
        prefix: Optional[str] = None
    ) -> 'AssetCollection':
        """
        Add multiple presets from a primitive type.

        Args:
            primitive_type: Primitive class name (e.g., "Box", "Cone")
            preset_names: List of preset names to add
            prefix: Optional prefix for asset names

        Returns:
            Self for chaining

        Example:
            >>> collection.add_preset_batch(
            ...     "Cone",
            ...     ["traffic_cone", "wizard_hat", "party_hat"],
            ...     prefix="cone"
            ... )
        """
        primitive_class = getattr(prim, primitive_type)
        prefix = prefix or primitive_type.lower()

        for preset_name in preset_names:
            mesh = primitive_class.preset(preset_name).build()
            name = f"{prefix}_{preset_name}"
            self.assets[name] = mesh

        self.metadata["total_assets"] = len(self.assets)

        return self

    def filter(self, predicate: Callable[[str, Mesh], bool]) -> 'AssetCollection':
        """
        Create a new collection with filtered assets.

        Args:
            predicate: Function that takes (name, mesh) and returns bool

        Returns:
            New filtered collection

        Example:
            >>> # Filter high-poly assets
            >>> high_poly = collection.filter(
            ...     lambda name, mesh: mesh.triangle_count() > 1000
            ... )
        """
        filtered = AssetCollection(f"{self.name}_filtered")

        for name, mesh in self.assets.items():
            if predicate(name, mesh):
                filtered.add_mesh(name, mesh)

        return filtered

    def export_all(
        self,
        engines: List[str],
        output_dir: str = "exports",
        create_manifest: bool = True
    ) -> Dict[str, List[str]]:
        """
        Export all assets to specified engines.

        Args:
            engines: List of engine names ("unity", "unreal", etc.)
            output_dir: Base output directory
            create_manifest: Whether to create export manifest

        Returns:
            Dict mapping engine names to list of exported file paths

        Example:
            >>> paths = collection.export_all(
            ...     engines=["unity", "unreal", "lumix"],
            ...     output_dir="game_assets/props"
            ... )
        """
        output_base = Path(output_dir)
        export_map = {engine: [] for engine in engines}
        manifest_data = {
            "collection": self.name,
            "timestamp": datetime.now().isoformat(),
            "total_assets": len(self.assets),
            "engines": engines,
            "exports": []
        }

        # Export each asset to each engine
        for asset_name, mesh in self.assets.items():
            asset_exports = {}

            for engine in engines:
                # Create engine directory
                engine_dir = output_base / engine
                engine_dir.mkdir(parents=True, exist_ok=True)

                # Export path
                filename = f"{asset_name}.obj"
                filepath = engine_dir / filename

                # Export using appropriate method
                export_method = getattr(mesh, f"to_{engine}")
                export_method(str(filepath))

                export_map[engine].append(str(filepath))
                asset_exports[engine] = str(filepath)

                print(f"[OK] {asset_name:30s} -> {engine:10s} ({mesh.triangle_count():,} tris)")

            # Add to manifest
            manifest_data["exports"].append({
                "name": asset_name,
                "vertices": mesh.vertex_count(),
                "triangles": mesh.triangle_count(),
                "paths": asset_exports,
                "metadata": mesh._metadata
            })

        # Save manifest
        if create_manifest:
            manifest_path = output_base / f"{self.name}_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f, indent=2)
            print(f"\\n[OK] Manifest saved: {manifest_path}")

        print(f"\\n[OK] Exported {len(self.assets)} assets to {len(engines)} engines")

        return export_map

    def stats(self):
        """Print collection statistics"""
        print(f"\\nAsset Collection: {self.name}")
        print("=" * 70)
        print(f"Total Assets: {len(self.assets)}")
        print(f"Templates Used: {', '.join(self.metadata['templates_used']) or 'None'}")

        if self.assets:
            total_verts = sum(m.vertex_count() for m in self.assets.values())
            total_tris = sum(m.triangle_count() for m in self.assets.values())
            print(f"\\nTotal Vertices: {total_verts:,}")
            print(f"Total Triangles: {total_tris:,}")
            print(f"Average Tris/Asset: {total_tris // len(self.assets):,}")

        print("=" * 70)

    def __len__(self):
        return len(self.assets)

    def __repr__(self):
        return f"AssetCollection('{self.name}', {len(self.assets)} assets)"


class Factory:
    """
    Central factory for creating templates and managing asset generation.

    Provides high-level interface for template management and batch generation.

    Examples:
        >>> factory = Factory()
        >>>
        >>> # Register templates
        >>> factory.register_template("crate", "Box", {"size": 1.0})
        >>> factory.register_template("pillar", "Cylinder", {"radius": 0.5, "height": 3.0})
        >>>
        >>> # Generate from templates
        >>> crates = factory.generate("crate", count=20, randomize={"size": (0.8, 1.2)})
        >>>
        >>> # Create collections
        >>> props = factory.create_collection("level_props")
        >>> props.add_template(factory.get_template("crate"), count=15)
    """

    def __init__(self):
        """Initialize factory with empty template registry"""
        self.templates: Dict[str, Template] = {}

    def register_template(
        self,
        name: str,
        primitive_type: str,
        base_params: Dict[str, Any],
        **kwargs
    ) -> Template:
        """
        Register a new template.

        Args:
            name: Template name
            primitive_type: Primitive class name
            base_params: Base parameters
            **kwargs: Additional template arguments

        Returns:
            Created template
        """
        template = Template(name, primitive_type, base_params, **kwargs)
        self.templates[name] = template
        return template

    def get_template(self, name: str) -> Template:
        """Get registered template by name"""
        if name not in self.templates:
            raise KeyError(f"Template '{name}' not found. Available: {list(self.templates.keys())}")
        return self.templates[name]

    def generate(self, template_name: str, count: int = 1, **kwargs) -> Union[Mesh, List[Mesh]]:
        """
        Generate from a registered template.

        Args:
            template_name: Name of registered template
            count: Number to generate
            **kwargs: Passed to template.generate_variations()

        Returns:
            Single mesh if count=1, list otherwise
        """
        template = self.get_template(template_name)

        if count == 1:
            return template.generate()
        else:
            return template.generate_variations(count, **kwargs)

    def create_collection(self, name: str, **kwargs) -> AssetCollection:
        """Create a new asset collection"""
        return AssetCollection(name, **kwargs)

    def list_templates(self):
        """Print registered templates"""
        print(f"\\nRegistered Templates ({len(self.templates)}):")
        print("=" * 70)
        for name, template in self.templates.items():
            print(f"  {name:20s} - {template.primitive_type:15s} ({template.description})")
        print("=" * 70)


__all__ = ["Template", "AssetCollection", "Factory"]
