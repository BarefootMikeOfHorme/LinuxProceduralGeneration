"""
VaultMind Forge - OpenSCAD CSG Operations
=========================================

Constructive Solid Geometry (CSG) operations using OpenSCAD as engine.

Provides Python API for boolean operations:
    - union() - Combine multiple objects
    - difference() - Subtract objects
    - intersection() - Keep only overlapping parts
    - hull() - Create convex hull
    - minkowski() - Minkowski sum (rounded edges)

Usage:
    >>> from vaultmind_forge.forge_3d.primitives_all import Sphere, Box
    >>> from vaultmind_forge.forge_3d.openscad_csg import CSGBuilder
    >>>
    >>> # Hollow sphere
    >>> builder = CSGBuilder()
    >>> outer = Sphere(radius=2.0)
    >>> inner = Sphere(radius=1.8)
    >>> hollow_sphere = builder.difference(outer, inner)
    >>> hollow_sphere.to_unity("hollow_sphere.obj")
"""

from pathlib import Path
from typing import List, Tuple, Optional, Union
import tempfile

from .openscad_export import OpenSCADExporter
from .openscad_import import OpenSCADImporter


class CSGBuilder:
    """
    Constructive Solid Geometry builder using OpenSCAD.

    Performs boolean operations on VaultMind primitives.
    """

    def __init__(self, openscad_path: Optional[str] = None):
        """
        Initialize CSG builder.

        Args:
            openscad_path: Path to OpenSCAD executable (auto-detected if None)
        """
        self.exporter = OpenSCADExporter(openscad_path)
        self.importer = OpenSCADImporter(openscad_path)

        self.temp_dir = Path(tempfile.gettempdir()) / "vaultmind_csg"
        self.temp_dir.mkdir(exist_ok=True)

    def _primitives_to_scad(self, primitives: List[Tuple],
                           operation: str) -> str:
        """
        Convert primitives to SCAD script with CSG operation.

        Args:
            primitives: List of (primitive, position, rotation) tuples
            operation: CSG operation ("union", "difference", "intersection", "hull", "minkowski")

        Returns:
            SCAD script as string
        """
        scad_code = f"// VaultMind Forge - CSG {operation.title()}\n\n"

        # Generate module for each primitive
        for i, prim_data in enumerate(primitives):
            if len(prim_data) == 1:
                primitive = prim_data[0]
                position = (0, 0, 0)
                rotation = (0, 0, 0)
            elif len(prim_data) == 2:
                primitive, position = prim_data
                rotation = (0, 0, 0)
            else:
                primitive, position, rotation = prim_data

            # Generate module
            module_code = self.exporter.primitive_to_scad(
                primitive,
                name=f"obj{i}",
                parametric=False
            )

            # Extract just the geometry (remove comments)
            lines = [l for l in module_code.split('\n') if not l.strip().startswith('//')]
            geometry = '\n'.join(lines).strip()

            # Wrap with transforms
            x, y, z = position
            rx, ry, rz = rotation

            if rx != 0 or ry != 0 or rz != 0:
                scad_code += f"module obj{i}() {{\n"
                scad_code += f"    rotate([{rx}, {ry}, {rz}])\n"
                scad_code += f"        {geometry}\n"
                scad_code += "}\n\n"
            else:
                scad_code += f"module obj{i}() {{\n"
                scad_code += f"    {geometry}\n"
                scad_code += "}\n\n"

        # Generate operation
        scad_code += f"\n// Apply {operation}\n"
        scad_code += f"{operation}() {{\n"

        for i, prim_data in enumerate(primitives):
            if len(prim_data) >= 2:
                position = prim_data[1]
            else:
                position = (0, 0, 0)

            x, y, z = position
            scad_code += f"    translate([{x}, {y}, {z}]) obj{i}();\n"

        scad_code += "}\n"

        return scad_code

    def _execute_csg(self, scad_code: str, operation_name: str) -> 'Mesh':
        """
        Execute CSG operation and return mesh.

        Args:
            scad_code: SCAD script
            operation_name: Name for temp files

        Returns:
            Resulting mesh
        """
        # Write SCAD file
        scad_path = self.temp_dir / f"{operation_name}.scad"
        with open(scad_path, 'w') as f:
            f.write(scad_code)

        # Render to mesh
        print(f"[INFO] Executing CSG operation: {operation_name}")
        mesh = self.importer.scad_to_mesh(str(scad_path))

        return mesh

    def union(self, *primitives: Union[Tuple, object]) -> 'Mesh':
        """
        Combine multiple objects into one.

        Args:
            *primitives: Primitives as objects or (primitive, position) tuples

        Returns:
            Combined mesh

        Example:
            >>> base = Box(width=4, height=0.5, depth=4)
            >>> body = Cylinder(radius=1, height=3)
            >>> head = Sphere(radius=0.8)
            >>>
            >>> snowman = builder.union(
            ...     (base, (0, -1.75, 0)),
            ...     (body, (0, 0, 0)),
            ...     (head, (0, 2.0, 0))
            ... )
        """
        # Normalize input
        prim_list = []
        for p in primitives:
            if isinstance(p, tuple):
                prim_list.append(p)
            else:
                prim_list.append((p,))

        scad_code = self._primitives_to_scad(prim_list, "union")
        return self._execute_csg(scad_code, "union_result")

    def difference(self, base, *subtract) -> 'Mesh':
        """
        Subtract objects from base object.

        Args:
            base: Base primitive or (primitive, position) tuple
            *subtract: Objects to subtract

        Returns:
            Mesh with subtracted geometry

        Example:
            >>> # Hollow sphere
            >>> outer = Sphere(radius=2.0)
            >>> inner = Sphere(radius=1.8)
            >>> hollow = builder.difference(outer, inner)
            >>>
            >>> # Perforated tube
            >>> tube = Tube(outer_radius=1.0, inner_radius=0.8, height=4.0)
            >>> hole = Cylinder(radius=0.3, height=5.0)
            >>> perforated = builder.difference(
            ...     tube,
            ...     (hole, (0.6, 0, 0)),
            ...     (hole, (-0.6, 0, 0))
            ... )
        """
        # Normalize input
        if isinstance(base, tuple):
            prim_list = [base]
        else:
            prim_list = [(base,)]

        for s in subtract:
            if isinstance(s, tuple):
                prim_list.append(s)
            else:
                prim_list.append((s,))

        scad_code = self._primitives_to_scad(prim_list, "difference")
        return self._execute_csg(scad_code, "difference_result")

    def intersection(self, *primitives) -> 'Mesh':
        """
        Keep only overlapping parts of objects.

        Args:
            *primitives: Primitives to intersect

        Returns:
            Mesh of intersection

        Example:
            >>> # Cube-sphere intersection (rounded cube)
            >>> cube = Box(width=2, height=2, depth=2)
            >>> sphere = Sphere(radius=1.5)
            >>> rounded_cube = builder.intersection(cube, sphere)
        """
        # Normalize input
        prim_list = []
        for p in primitives:
            if isinstance(p, tuple):
                prim_list.append(p)
            else:
                prim_list.append((p,))

        scad_code = self._primitives_to_scad(prim_list, "intersection")
        return self._execute_csg(scad_code, "intersection_result")

    def hull(self, *primitives) -> 'Mesh':
        """
        Create convex hull around objects.

        The hull wraps around all objects like shrink-wrap.

        Args:
            *primitives: Primitives to wrap

        Returns:
            Convex hull mesh

        Example:
            >>> # Create organic shape by hulling spheres
            >>> s1 = (Sphere(radius=0.5), (0, 0, 0))
            >>> s2 = (Sphere(radius=0.5), (1, 1, 0))
            >>> s3 = (Sphere(radius=0.5), (2, 0, 0))
            >>> organic = builder.hull(s1, s2, s3)
        """
        # Normalize input
        prim_list = []
        for p in primitives:
            if isinstance(p, tuple):
                prim_list.append(p)
            else:
                prim_list.append((p,))

        scad_code = self._primitives_to_scad(prim_list, "hull")
        return self._execute_csg(scad_code, "hull_result")

    def minkowski(self, base, shape) -> 'Mesh':
        """
        Minkowski sum - rounds edges by sweeping shape around base.

        Useful for creating rounded/filleted edges.

        Args:
            base: Base primitive
            shape: Shape to sweep (usually small sphere)

        Returns:
            Rounded mesh

        Example:
            >>> # Round the edges of a cube
            >>> cube = Box(width=2, height=2, depth=2)
            >>> round_shape = Sphere(radius=0.1, detail="low")
            >>> rounded_cube = builder.minkowski(cube, round_shape)
        """
        # Normalize input
        base_prim = (base,) if not isinstance(base, tuple) else base
        shape_prim = (shape,) if not isinstance(shape, tuple) else shape

        scad_code = self._primitives_to_scad([base_prim, shape_prim], "minkowski")
        return self._execute_csg(scad_code, "minkowski_result")

    def custom_operation(self, scad_code: str, name: str = "custom") -> 'Mesh':
        """
        Execute custom SCAD code.

        For advanced operations not covered by standard CSG.

        Args:
            scad_code: Custom OpenSCAD script
            name: Operation name for temp files

        Returns:
            Resulting mesh

        Example:
            >>> code = '''
            ... // Custom twisted cylinder
            ... linear_extrude(height=10, twist=360, slices=50)
            ...     circle(r=1);
            ... '''
            >>> twisted = builder.custom_operation(code, "twisted_cylinder")
        """
        return self._execute_csg(scad_code, name)


class CSGPresets:
    """
    Pre-built CSG operations for common use cases.
    """

    def __init__(self, builder: Optional[CSGBuilder] = None):
        self.builder = builder or CSGBuilder()

    def hollow_sphere(self, outer_radius: float, thickness: float,
                     detail: str = "high") -> 'Mesh':
        """Create hollow sphere"""
        from .primitives_all import Sphere

        outer = Sphere(radius=outer_radius, detail=detail)
        inner = Sphere(radius=outer_radius - thickness, detail=detail)

        return self.builder.difference(outer, inner)

    def hollow_cylinder(self, outer_radius: float, inner_radius: float,
                       height: float, detail: str = "high") -> 'Mesh':
        """Create hollow cylinder (tube)"""
        from .primitives_all import Cylinder

        outer = Cylinder(radius=outer_radius, height=height, detail=detail)
        inner = Cylinder(radius=inner_radius, height=height + 0.1, detail=detail)

        return self.builder.difference(outer, inner)

    def rounded_box(self, width: float, height: float, depth: float,
                   rounding: float = 0.1) -> 'Mesh':
        """Create box with rounded edges"""
        from .primitives_all import Box, Sphere

        box = Box(width=width - rounding * 2,
                 height=height - rounding * 2,
                 depth=depth - rounding * 2)
        round_shape = Sphere(radius=rounding, detail="low")

        return self.builder.minkowski(box, round_shape)

    def perforated_plate(self, width: float, height: float, thickness: float,
                        hole_radius: float, hole_spacing: float,
                        detail: str = "medium") -> 'Mesh':
        """Create plate with evenly spaced holes"""
        from .primitives_all import Box, Cylinder
        import math

        # Base plate
        plate = Box(width=width, height=thickness, depth=height)

        # Calculate hole positions
        holes = []
        x_count = int(width / hole_spacing)
        z_count = int(height / hole_spacing)

        x_start = -(x_count - 1) * hole_spacing / 2
        z_start = -(z_count - 1) * hole_spacing / 2

        for i in range(x_count):
            for j in range(z_count):
                x = x_start + i * hole_spacing
                z = z_start + j * hole_spacing
                hole = Cylinder(radius=hole_radius, height=thickness + 0.1, detail=detail)
                holes.append((hole, (x, 0, z)))

        # Subtract all holes
        return self.builder.difference(plate, *holes)

    def gear_wheel(self, outer_radius: float, inner_radius: float,
                  thickness: float, teeth: int = 12,
                  tooth_depth: float = 0.2) -> 'Mesh':
        """Create simple gear wheel"""
        from .primitives_all import Cylinder, Box
        import math

        # Base disc
        disc = Cylinder(radius=outer_radius, height=thickness, detail="high")

        # Inner hole
        hole = Cylinder(radius=inner_radius, height=thickness + 0.1, detail="high")

        # Create teeth as boxes
        tooth_boxes = []
        tooth_width = 2 * math.pi * outer_radius / (teeth * 2)

        for i in range(teeth):
            angle = (360 / teeth) * i
            tooth = Box(width=tooth_width, height=thickness, depth=tooth_depth * 2)

            # Position at edge
            x = (outer_radius + tooth_depth) * math.cos(math.radians(angle))
            z = (outer_radius + tooth_depth) * math.sin(math.radians(angle))

            tooth_boxes.append((tooth, (x, 0, z), (0, angle, 0)))

        # Add teeth to disc, subtract hole
        disc_with_teeth = self.builder.union((disc, (0, 0, 0)), *tooth_boxes)
        return self.builder.difference(disc_with_teeth, hole)


__all__ = ["CSGBuilder", "CSGPresets"]
