"""
VaultMind Forge - OpenSCAD Export
=================================

Export VaultMind primitives to OpenSCAD .scad format for parametric CAD editing.

Features:
    - Convert all 15 primitives to OpenSCAD syntax
    - Export templates with editable parameters
    - Support for transformations (translate, rotate, scale)
    - Generate parametric modules
    - Launch OpenSCAD directly from Python

Usage:
    >>> from vaultmind_forge.forge_3d.primitives_all import Sphere
    >>> from vaultmind_forge.forge_3d.openscad_export import OpenSCADExporter
    >>>
    >>> sphere = Sphere.preset("basketball")
    >>> exporter = OpenSCADExporter()
    >>> exporter.export_primitive(sphere, "basketball.scad")
    >>> exporter.open_in_openscad("basketball.scad")
"""

from pathlib import Path
from typing import Union, List, Optional, Tuple
import subprocess
import sys

# Import all primitives
from .primitives_all import (
    Box, Sphere, Cylinder, Cone, Torus, Capsule, Pyramid,
    Plane, Disc, Ring, Tube, Prism, Dome, Tetrahedron, Octahedron
)


class OpenSCADExporter:
    """
    Export VaultMind primitives to OpenSCAD .scad format.

    Converts procedural geometry to parametric CAD scripts for visual editing.
    """

    def __init__(self, openscad_path: Optional[str] = None):
        """
        Initialize exporter.

        Args:
            openscad_path: Path to OpenSCAD executable (auto-detected if None)
        """
        if openscad_path is None:
            # Default Windows installation path
            self.openscad_path = r"C:\Program Files\OpenSCAD\openscad.exe"
        else:
            self.openscad_path = openscad_path

        self.openscad_available = Path(self.openscad_path).exists()

    def primitive_to_scad(self, primitive, name: str = "object",
                         parametric: bool = True) -> str:
        """
        Convert a primitive to OpenSCAD script.

        Args:
            primitive: VaultMind primitive instance
            name: Module name for parametric export
            parametric: Generate parametric module (True) or direct geometry (False)

        Returns:
            OpenSCAD script as string
        """
        # Get primitive type
        prim_type = type(primitive).__name__

        # Dispatch to appropriate converter
        if prim_type == "Box":
            return self._box_to_scad(primitive, name, parametric)
        elif prim_type == "Sphere":
            return self._sphere_to_scad(primitive, name, parametric)
        elif prim_type == "Cylinder":
            return self._cylinder_to_scad(primitive, name, parametric)
        elif prim_type == "Cone":
            return self._cone_to_scad(primitive, name, parametric)
        elif prim_type == "Torus":
            return self._torus_to_scad(primitive, name, parametric)
        elif prim_type == "Capsule":
            return self._capsule_to_scad(primitive, name, parametric)
        elif prim_type == "Pyramid":
            return self._pyramid_to_scad(primitive, name, parametric)
        elif prim_type == "Plane":
            return self._plane_to_scad(primitive, name, parametric)
        elif prim_type == "Disc":
            return self._disc_to_scad(primitive, name, parametric)
        elif prim_type == "Ring":
            return self._ring_to_scad(primitive, name, parametric)
        elif prim_type == "Tube":
            return self._tube_to_scad(primitive, name, parametric)
        elif prim_type == "Prism":
            return self._prism_to_scad(primitive, name, parametric)
        elif prim_type == "Dome":
            return self._dome_to_scad(primitive, name, parametric)
        elif prim_type == "Tetrahedron":
            return self._tetrahedron_to_scad(primitive, name, parametric)
        elif prim_type == "Octahedron":
            return self._octahedron_to_scad(primitive, name, parametric)
        else:
            raise ValueError(f"Unknown primitive type: {prim_type}")

    # ========================================================================
    # Primitive Converters
    # ========================================================================

    def _box_to_scad(self, box: Box, name: str, parametric: bool) -> str:
        """Convert Box to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Box
// Parametric module for easy editing

module {name}(width={box._width}, height={box._height}, depth={box._depth}) {{
    cube([width, height, depth], center=true);
}}

// Create instance
{name}();
"""
        else:
            return f"""// VaultMind Forge - Box
cube([{box._width}, {box._height}, {box._depth}], center=true);
"""

    def _sphere_to_scad(self, sphere: Sphere, name: str, parametric: bool) -> str:
        """Convert Sphere to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Sphere
// Parametric module for easy editing

module {name}(radius={sphere._radius}, segments={sphere._segments}) {{
    sphere(r=radius, $fn=segments);
}}

// Create instance
{name}();
"""
        else:
            return f"""// VaultMind Forge - Sphere
sphere(r={sphere._radius}, $fn={sphere._segments});
"""

    def _cylinder_to_scad(self, cylinder: Cylinder, name: str, parametric: bool) -> str:
        """Convert Cylinder to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Cylinder
// Parametric module for easy editing

module {name}(radius={cylinder._radius}, height={cylinder._height}, segments={cylinder._segments}) {{
    cylinder(h=height, r=radius, center=true, $fn=segments);
}}

// Create instance
{name}();
"""
        else:
            return f"""// VaultMind Forge - Cylinder
cylinder(h={cylinder._height}, r={cylinder._radius}, center=true, $fn={cylinder._segments});
"""

    def _cone_to_scad(self, cone: Cone, name: str, parametric: bool) -> str:
        """Convert Cone to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Cone
// Parametric module for easy editing

module {name}(radius={cone._radius}, height={cone._height}, segments={cone._segments}) {{
    cylinder(h=height, r1=radius, r2=0, center=true, $fn=segments);
}}

// Create instance
{name}();
"""
        else:
            return f"""// VaultMind Forge - Cone
cylinder(h={cone._height}, r1={cone._radius}, r2=0, center=true, $fn={cone._segments});
"""

    def _torus_to_scad(self, torus: Torus, name: str, parametric: bool) -> str:
        """Convert Torus to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Torus
// Parametric module for easy editing

module {name}(major_radius={torus._major_radius}, minor_radius={torus._minor_radius},
              major_segments={torus._major_segments}, minor_segments={torus._minor_segments}) {{
    rotate_extrude($fn=major_segments)
        translate([major_radius, 0, 0])
            circle(r=minor_radius, $fn=minor_segments);
}}

// Create instance
{name}();
"""
        else:
            return f"""// VaultMind Forge - Torus
rotate_extrude($fn={torus._major_segments})
    translate([{torus._major_radius}, 0, 0])
        circle(r={torus._minor_radius}, $fn={torus._minor_segments});
"""

    def _capsule_to_scad(self, capsule: Capsule, name: str, parametric: bool) -> str:
        """Convert Capsule to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Capsule
// Parametric module for easy editing

module {name}(radius={capsule._radius}, height={capsule._height}, segments={capsule._segments}) {{
    union() {{
        // Cylinder body
        cylinder(h=height, r=radius, center=true, $fn=segments);
        // Top hemisphere
        translate([0, 0, height/2])
            sphere(r=radius, $fn=segments);
        // Bottom hemisphere
        translate([0, 0, -height/2])
            sphere(r=radius, $fn=segments);
    }}
}}

// Create instance
{name}();
"""
        else:
            half_h = capsule._height / 2
            return f"""// VaultMind Forge - Capsule
union() {{
    cylinder(h={capsule._height}, r={capsule._radius}, center=true, $fn={capsule._segments});
    translate([0, 0, {half_h}])
        sphere(r={capsule._radius}, $fn={capsule._segments});
    translate([0, 0, {-half_h}])
        sphere(r={capsule._radius}, $fn={capsule._segments});
}}
"""

    def _pyramid_to_scad(self, pyramid: Pyramid, name: str, parametric: bool) -> str:
        """Convert Pyramid to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Pyramid
// Parametric module for easy editing

module {name}(base_size={pyramid._base_size}, height={pyramid._height}, sides={pyramid._sides}) {{
    cylinder(h=height, r1=base_size/2, r2=0, center=true, $fn=sides);
}}

// Create instance
{name}();
"""
        else:
            return f"""// VaultMind Forge - Pyramid
cylinder(h={pyramid._height}, r1={pyramid._base_size/2}, r2=0, center=true, $fn={pyramid._sides});
"""

    def _plane_to_scad(self, plane: Plane, name: str, parametric: bool) -> str:
        """Convert Plane to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Plane
// Parametric module for easy editing

module {name}(width={plane._width}, depth={plane._depth}, thickness=0.01) {{
    cube([width, thickness, depth], center=true);
}}

// Create instance
{name}();
"""
        else:
            return f"""// VaultMind Forge - Plane
cube([{plane._width}, 0.01, {plane._depth}], center=true);
"""

    def _disc_to_scad(self, disc: Disc, name: str, parametric: bool) -> str:
        """Convert Disc to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Disc
// Parametric module for easy editing

module {name}(radius={disc._radius}, segments={disc._segments}, thickness=0.1) {{
    cylinder(h=thickness, r=radius, center=true, $fn=segments);
}}

// Create instance
{name}();
"""
        else:
            return f"""// VaultMind Forge - Disc
cylinder(h=0.1, r={disc._radius}, center=true, $fn={disc._segments});
"""

    def _ring_to_scad(self, ring: Ring, name: str, parametric: bool) -> str:
        """Convert Ring to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Ring
// Parametric module for easy editing

module {name}(outer_radius={ring._outer_radius}, inner_radius={ring._inner_radius},
              segments={ring._segments}, thickness=0.1) {{
    difference() {{
        cylinder(h=thickness, r=outer_radius, center=true, $fn=segments);
        cylinder(h=thickness+0.01, r=inner_radius, center=true, $fn=segments);
    }}
}}

// Create instance
{name}();
"""
        else:
            return f"""// VaultMind Forge - Ring
difference() {{
    cylinder(h=0.1, r={ring._outer_radius}, center=true, $fn={ring._segments});
    cylinder(h=0.11, r={ring._inner_radius}, center=true, $fn={ring._segments});
}}
"""

    def _tube_to_scad(self, tube: Tube, name: str, parametric: bool) -> str:
        """Convert Tube to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Tube
// Parametric module for easy editing

module {name}(outer_radius={tube._outer_radius}, inner_radius={tube._inner_radius},
              height={tube._height}, segments={tube._segments}) {{
    difference() {{
        cylinder(h=height, r=outer_radius, center=true, $fn=segments);
        cylinder(h=height+0.01, r=inner_radius, center=true, $fn=segments);
    }}
}}

// Create instance
{name}();
"""
        else:
            return f"""// VaultMind Forge - Tube
difference() {{
    cylinder(h={tube._height}, r={tube._outer_radius}, center=true, $fn={tube._segments});
    cylinder(h={tube._height+0.01}, r={tube._inner_radius}, center=true, $fn={tube._segments});
}}
"""

    def _prism_to_scad(self, prism: Prism, name: str, parametric: bool) -> str:
        """Convert Prism to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Prism
// Parametric module for easy editing

module {name}(sides={prism._sides}, radius={prism._radius}, height={prism._height}) {{
    linear_extrude(height=height, center=true)
        circle(r=radius, $fn=sides);
}}

// Create instance
{name}();
"""
        else:
            return f"""// VaultMind Forge - Prism
linear_extrude(height={prism._height}, center=true)
    circle(r={prism._radius}, $fn={prism._sides});
"""

    def _dome_to_scad(self, dome: Dome, name: str, parametric: bool) -> str:
        """Convert Dome to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Dome
// Parametric module for easy editing

module {name}(radius={dome._radius}, segments={dome._segments}) {{
    difference() {{
        sphere(r=radius, $fn=segments);
        translate([0, 0, -radius])
            cube([radius*2+0.1, radius*2+0.1, radius*2], center=true);
    }}
}}

// Create instance
{name}();
"""
        else:
            r = dome._radius
            return f"""// VaultMind Forge - Dome
difference() {{
    sphere(r={r}, $fn={dome._segments});
    translate([0, 0, {-r}])
        cube([{r*2+0.1}, {r*2+0.1}, {r*2}], center=true);
}}
"""

    def _tetrahedron_to_scad(self, tetra: Tetrahedron, name: str, parametric: bool) -> str:
        """Convert Tetrahedron to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Tetrahedron
// Parametric module for easy editing

module {name}(size={tetra._size}) {{
    polyhedron(
        points = [
            [1, 1, 1], [-1, -1, 1], [-1, 1, -1], [1, -1, -1]
        ],
        faces = [
            [0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]
        ]
    );
    scale([size, size, size]) children();
}}

// Create instance
{name}() sphere(0.01);
"""
        else:
            s = tetra._size
            return f"""// VaultMind Forge - Tetrahedron
scale([{s}, {s}, {s}])
    polyhedron(
        points = [
            [1, 1, 1], [-1, -1, 1], [-1, 1, -1], [1, -1, -1]
        ],
        faces = [
            [0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]
        ]
    );
"""

    def _octahedron_to_scad(self, octa: Octahedron, name: str, parametric: bool) -> str:
        """Convert Octahedron to OpenSCAD"""
        if parametric:
            return f"""// VaultMind Forge - Octahedron
// Parametric module for easy editing

module {name}(size={octa._size}) {{
    polyhedron(
        points = [
            [1, 0, 0], [-1, 0, 0], [0, 1, 0],
            [0, -1, 0], [0, 0, 1], [0, 0, -1]
        ],
        faces = [
            [0, 2, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2],
            [1, 2, 5], [1, 5, 3], [1, 3, 4], [1, 4, 2]
        ]
    );
    scale([size, size, size]) children();
}}

// Create instance
{name}() sphere(0.01);
"""
        else:
            s = octa._size
            return f"""// VaultMind Forge - Octahedron
scale([{s}, {s}, {s}])
    polyhedron(
        points = [
            [1, 0, 0], [-1, 0, 0], [0, 1, 0],
            [0, -1, 0], [0, 0, 1], [0, 0, -1]
        ],
        faces = [
            [0, 2, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2],
            [1, 2, 5], [1, 5, 3], [1, 3, 4], [1, 4, 2]
        ]
    );
"""

    # ========================================================================
    # Export Methods
    # ========================================================================

    def export_primitive(self, primitive, output_path: str,
                        name: Optional[str] = None,
                        parametric: bool = True) -> str:
        """
        Export a primitive to .scad file.

        Args:
            primitive: VaultMind primitive instance
            output_path: Output .scad file path
            name: Module name (defaults to primitive type)
            parametric: Generate parametric module

        Returns:
            Path to exported file
        """
        # Default name from primitive type
        if name is None:
            name = type(primitive).__name__.lower()

        # Generate SCAD script
        scad_code = self.primitive_to_scad(primitive, name, parametric)

        # Ensure directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(output_path, 'w') as f:
            f.write(scad_code)

        print(f"[OK] Exported to: {output_path}")
        return str(output_path)

    def export_multiple(self, primitives: List[Tuple], output_path: str,
                       combine_method: str = "union") -> str:
        """
        Export multiple primitives to single .scad file.

        Args:
            primitives: List of (primitive, name, position) tuples
            output_path: Output .scad file path
            combine_method: "union", "separate", or "difference"

        Returns:
            Path to exported file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate header
        scad_code = "// VaultMind Forge - Multi-Object Export\n"
        scad_code += f"// Combined with: {combine_method}\n\n"

        # Generate modules for each primitive
        for i, (primitive, name, position) in enumerate(primitives):
            scad_code += self.primitive_to_scad(primitive, f"{name}_{i}", parametric=True)
            scad_code += "\n"

        # Generate combination code
        if combine_method == "union":
            scad_code += "\n// Combine all objects\nunion() {\n"
            for i, (_, name, position) in enumerate(primitives):
                x, y, z = position
                scad_code += f"    translate([{x}, {y}, {z}]) {name}_{i}();\n"
            scad_code += "}\n"

        elif combine_method == "separate":
            scad_code += "\n// Render all objects separately\n"
            for i, (_, name, position) in enumerate(primitives):
                x, y, z = position
                scad_code += f"translate([{x}, {y}, {z}]) {name}_{i}();\n"

        elif combine_method == "difference":
            scad_code += "\n// Subtract subsequent objects from first\ndifference() {\n"
            for i, (_, name, position) in enumerate(primitives):
                x, y, z = position
                scad_code += f"    translate([{x}, {y}, {z}]) {name}_{i}();\n"
            scad_code += "}\n"

        # Write file
        with open(output_path, 'w') as f:
            f.write(scad_code)

        print(f"[OK] Exported {len(primitives)} objects to: {output_path}")
        return str(output_path)

    def open_in_openscad(self, scad_path: str) -> bool:
        """
        Open .scad file in OpenSCAD application.

        Args:
            scad_path: Path to .scad file

        Returns:
            True if opened successfully
        """
        if not self.openscad_available:
            print(f"[WARNING] OpenSCAD not found at: {self.openscad_path}")
            print("[INFO] Set custom path: exporter.openscad_path = 'your/path'")
            return False

        try:
            subprocess.Popen([self.openscad_path, str(scad_path)])
            print(f"[OK] Opened in OpenSCAD: {scad_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to open OpenSCAD: {e}")
            return False


__all__ = ["OpenSCADExporter"]
