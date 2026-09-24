# VaultMind Forge - OpenSCAD Integration Plan

**Date:** December 14, 2025
**Status:** Planned
**OpenSCAD Path:** `C:\Program Files\OpenSCAD\openscad.exe`

---

## Overview

OpenSCAD is an **open-source parametric CAD editor** that uses a scripting language for declarative geometry. We can integrate it as a visual editor for our parametric primitive system, enabling:

1. **Export VaultMind primitives → .scad files** for editing in OpenSCAD
2. **Import .scad files → VaultMind meshes** for game asset pipeline
3. **Live preview** of parametric designs before export
4. **Round-trip editing** between VaultMind and OpenSCAD

---

## Current Status

### ✅ What We Have:

**Inspired by OpenSCAD:**
- Declarative geometry approach in our Rust engine
- Parametric primitives (Box, Sphere, Cylinder, Cone, Torus, etc.)
- Builder pattern for primitive configuration
- Template system for variations

**Reference:** `docs/GEOMETRY_ENGINE.md` line 7:
> "Inspired by: Ice Engine's Meshmerizer module, **OpenSCAD's declarative geometry**, and Lumix Engine's compilation patterns."

### ❌ What We Don't Have:

- **No .scad export** from our primitives
- **No .scad import** into our system
- **No OpenSCAD executable integration**
- **No visual CAD editor** for parametric design

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  VAULTMIND FORGE                            │
│                                                             │
│  ┌────────────────┐          ┌──────────────────┐          │
│  │  Primitives    │◄────────►│  OpenSCAD        │          │
│  │  (Python/Rust) │  Export  │  Integration     │          │
│  │                │  .scad   │                  │          │
│  │  • Box         │          │  • Export .scad  │          │
│  │  • Sphere      │          │  • Import .scad  │          │
│  │  • Cylinder    │  Import  │  • Call OpenSCAD │          │
│  │  • Torus       │  mesh    │  • Render preview│          │
│  │  • etc.        │          │                  │          │
│  └────────────────┘          └──────────────────┘          │
│         │                             │                     │
│         ▼                             ▼                     │
│  ┌──────────────────────────────────────────┐              │
│  │         OPENSCAD EXECUTABLE              │              │
│  │  C:\Program Files\OpenSCAD\openscad.exe  │              │
│  │                                          │              │
│  │  • Visual parametric CAD editing        │              │
│  │  • CSG operations (union/diff/intersect)│              │
│  │  • Export to STL/OBJ/OFF/AMF/3MF        │              │
│  └──────────────────────────────────────────┘              │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────┐              │
│  │    GAME ASSET PIPELINE                   │              │
│  │  • SmartObject wrapping                  │              │
│  │  • GameProperties attachment             │              │
│  │  • Multi-engine export                   │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Export to OpenSCAD (.scad)

**Goal:** Convert our primitives to OpenSCAD script format

#### 1.1 Create SCAD Exporter

```python
# vaultmind_forge/forge_3d/openscad_export.py

class OpenSCADExporter:
    """Export VaultMind primitives to .scad format"""

    def primitive_to_scad(self, primitive, name="object"):
        """Convert primitive to OpenSCAD code"""

        if isinstance(primitive, Box):
            return self._box_to_scad(primitive)
        elif isinstance(primitive, Sphere):
            return self._sphere_to_scad(primitive)
        elif isinstance(primitive, Cylinder):
            return self._cylinder_to_scad(primitive)
        # ... etc

    def _box_to_scad(self, box):
        """Box → cube()"""
        size = box._size
        center = box._center or (0, 0, 0)

        return f"""
translate([{center[0]}, {center[1]}, {center[2]}])
    cube([{size[0]}, {size[1]}, {size[2]}], center=true);
"""

    def _sphere_to_scad(self, sphere):
        """Sphere → sphere()"""
        return f"""
sphere(r={sphere._radius}, $fn={sphere._segments});
"""

    def _cylinder_to_scad(self, cylinder):
        """Cylinder → cylinder()"""
        return f"""
cylinder(h={cylinder._height}, r={cylinder._radius}, $fn={cylinder._segments});
"""

    def template_to_scad(self, template):
        """Export template with parameters"""
        scad_code = f"""
// VaultMind Forge Template: {template.name}
// Generated: {datetime.now()}

// Parameters
{template.name}_height = {template.base_params.get('height', 1.0)};
{template.name}_radius = {template.base_params.get('radius', 0.5)};
$fn = {template.base_params.get('detail', 32)};

// Geometry
{self.primitive_to_scad(template.primitive, template.name)}
"""
        return scad_code
```

#### 1.2 Usage Example

```python
from vaultmind_forge.forge_3d import primitives_all as prim
from vaultmind_forge.forge_3d.openscad_export import OpenSCADExporter

# Create primitive
cone = prim.Cone(radius=1.0, height=2.0, detail="high")

# Export to .scad
exporter = OpenSCADExporter()
scad_code = exporter.primitive_to_scad(cone)

with open("cone.scad", "w") as f:
    f.write(scad_code)

# Open in OpenSCAD for visual editing
import subprocess
subprocess.Popen([
    "C:/Program Files/OpenSCAD/openscad.exe",
    "cone.scad"
])
```

### Phase 2: Import from OpenSCAD

**Goal:** Parse .scad files and convert to VaultMind primitives

#### 2.1 SCAD Parser

```python
# vaultmind_forge/forge_3d/openscad_import.py

import re
import subprocess
from pathlib import Path

class OpenSCADImporter:
    """Import .scad files as VaultMind meshes"""

    def __init__(self, openscad_path="C:/Program Files/OpenSCAD/openscad.exe"):
        self.openscad_path = openscad_path

    def scad_to_mesh(self, scad_file, output_format="obj"):
        """
        Render .scad file to mesh using OpenSCAD executable

        OpenSCAD command line:
        openscad -o output.obj input.scad
        """
        scad_path = Path(scad_file)
        output_path = scad_path.with_suffix(f".{output_format}")

        # Call OpenSCAD to render
        result = subprocess.run([
            self.openscad_path,
            "-o", str(output_path),
            str(scad_path)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"OpenSCAD rendering failed: {result.stderr}")

        # Load the rendered mesh
        from vaultmind_forge.forge_3d.mesh import Mesh
        # (Would need to implement OBJ loading)
        return output_path

    def parse_scad_parameters(self, scad_file):
        """Extract parameters from .scad file"""
        with open(scad_file, 'r') as f:
            content = f.read()

        params = {}
        # Parse parameter assignments
        # height = 2.0;
        # radius = 1.0;
        for match in re.finditer(r'(\w+)\s*=\s*([\d.]+)\s*;', content):
            param_name = match.group(1)
            param_value = float(match.group(2))
            params[param_name] = param_value

        return params
```

#### 2.2 Usage Example

```python
from vaultmind_forge.forge_3d.openscad_import import OpenSCADImporter

importer = OpenSCADImporter()

# User edits cone.scad in OpenSCAD, saves
# Import back into VaultMind
mesh_path = importer.scad_to_mesh("cone.scad", output_format="obj")

# Load parameters
params = importer.parse_scad_parameters("cone.scad")
print(f"Parameters: {params}")  # {'height': 2.5, 'radius': 1.2}

# Wrap in SmartObject
from vaultmind_forge.forge_3d.smart_object import SmartObject
obj = SmartObject.from_file(mesh_path, name="edited_cone")
obj.save_json("cone_meta.json")
```

### Phase 3: Live Preview Integration

**Goal:** Real-time preview of parametric changes

#### 3.1 Interactive Parameter Editor

```python
# vaultmind_forge/forge_editors/openscad_editor.py

from PyQt5.QtWidgets import QMainWindow, QSlider, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
import subprocess
import tempfile

class OpenSCADParametricEditor(QMainWindow):
    """Interactive parametric editor using OpenSCAD"""

    def __init__(self, primitive):
        super().__init__()
        self.primitive = primitive
        self.temp_scad = tempfile.NamedTemporaryFile(
            suffix=".scad", delete=False, mode='w'
        )

        self.init_ui()
        self.start_openscad_preview()

    def init_ui(self):
        """Create parameter sliders"""
        layout = QVBoxLayout()

        # Height slider
        self.height_slider = QSlider()
        self.height_slider.setRange(10, 500)  # 0.1 to 5.0
        self.height_slider.setValue(int(self.primitive._height * 100))
        self.height_slider.valueChanged.connect(self.update_preview)

        self.height_label = QLabel(f"Height: {self.primitive._height}")
        layout.addWidget(self.height_label)
        layout.addWidget(self.height_slider)

        # Radius slider
        self.radius_slider = QSlider()
        self.radius_slider.setRange(10, 300)
        self.radius_slider.setValue(int(self.primitive._radius * 100))
        self.radius_slider.valueChanged.connect(self.update_preview)

        self.radius_label = QLabel(f"Radius: {self.primitive._radius}")
        layout.addWidget(self.radius_label)
        layout.addWidget(self.radius_slider)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def update_preview(self):
        """Regenerate .scad and update OpenSCAD preview"""
        height = self.height_slider.value() / 100.0
        radius = self.radius_slider.value() / 100.0

        self.height_label.setText(f"Height: {height:.2f}")
        self.radius_label.setText(f"Radius: {radius:.2f}")

        # Generate .scad with new parameters
        scad_code = f"""
$fn = 64;
cylinder(h={height}, r={radius});
"""
        self.temp_scad.seek(0)
        self.temp_scad.write(scad_code)
        self.temp_scad.flush()

        # OpenSCAD auto-reloads changed files

    def start_openscad_preview(self):
        """Launch OpenSCAD in preview mode"""
        self.openscad_process = subprocess.Popen([
            "C:/Program Files/OpenSCAD/openscad.exe",
            self.temp_scad.name
        ])
```

### Phase 4: CSG Operations via OpenSCAD

**Goal:** Use OpenSCAD for boolean operations

```python
class OpenSCADCSG:
    """CSG operations using OpenSCAD"""

    def union(self, primitives, output_file="union.obj"):
        """Boolean union using OpenSCAD"""
        scad_code = "union() {\n"
        for prim in primitives:
            scad_code += "    " + self._to_scad(prim) + "\n"
        scad_code += "}"

        return self._render(scad_code, output_file)

    def difference(self, base, cutouts, output_file="difference.obj"):
        """Boolean difference using OpenSCAD"""
        scad_code = "difference() {\n"
        scad_code += "    " + self._to_scad(base) + "\n"
        for cutout in cutouts:
            scad_code += "    " + self._to_scad(cutout) + "\n"
        scad_code += "}"

        return self._render(scad_code, output_file)

    def intersection(self, primitives, output_file="intersection.obj"):
        """Boolean intersection using OpenSCAD"""
        scad_code = "intersection() {\n"
        for prim in primitives:
            scad_code += "    " + self._to_scad(prim) + "\n"
        scad_code += "}"

        return self._render(scad_code, output_file)
```

---

## Usage Workflows

### Workflow 1: Parametric Design

```python
# 1. Create parametric primitive in VaultMind
cone = prim.Cone(radius=1.0, height=2.0, detail="high")

# 2. Export to OpenSCAD for visual editing
exporter = OpenSCADExporter()
exporter.export(cone, "designs/cone.scad")

# 3. Open in OpenSCAD, adjust parameters visually
subprocess.Popen(["openscad", "designs/cone.scad"])

# User adjusts in OpenSCAD GUI, saves

# 4. Import modified design
importer = OpenSCADImporter()
mesh = importer.scad_to_mesh("designs/cone.scad")

# 5. Continue with game pipeline
obj = SmartObject.from_file(mesh, name="wizard_hat")
obj.export_for_engine("unity", "outputs/hats/")
```

### Workflow 2: CSG Modeling

```python
# Create primitives
base = prim.Box(size=2.0)
hole = prim.Cylinder(radius=0.5, height=2.5)

# Use OpenSCAD for CSG
csg = OpenSCADCSG()
result = csg.difference(base, [hole], "box_with_hole.obj")

# Load result and continue pipeline
obj = SmartObject.from_file(result, name="mounting_bracket")
```

### Workflow 3: Template Library

```python
# Create parametric template
template = Template("adjustable_pillar", "Cylinder", {
    "radius": 0.5,
    "height": 3.0,
    "detail": "high"
})

# Export to .scad with parameters
exporter = OpenSCADExporter()
scad_code = exporter.template_to_scad(template)

# .scad file becomes:
# pillar_radius = 0.5;
# pillar_height = 3.0;
# $fn = 64;
# cylinder(r=pillar_radius, h=pillar_height);

# User can adjust parameters in OpenSCAD or text editor
# Then batch-generate variations
```

---

## File Formats

### .scad File Structure

```openscad
// VaultMind Forge Export
// Template: medieval_pillar
// Generated: 2025-12-14

// Parameters (user-editable)
pillar_height = 3.0;
pillar_radius = 0.5;
pillar_detail = 64;

// Quality settings
$fn = pillar_detail;

// Geometry
cylinder(h=pillar_height, r=pillar_radius);
```

### Round-Trip Metadata

```json
{
  "openscad_source": "designs/pillar.scad",
  "parameters": {
    "pillar_height": 3.0,
    "pillar_radius": 0.5,
    "pillar_detail": 64
  },
  "last_edited": "2025-12-14T10:30:00",
  "vaultmind_template": "medieval_pillar",
  "exported_mesh": "outputs/pillar.obj"
}
```

---

## Benefits

### For Artists:
- **Visual parametric editing** instead of code
- **Familiar CAD interface** (OpenSCAD)
- **Precise dimensions** for architectural/technical models
- **CSG operations** for complex shapes

### For Programmers:
- **Declarative geometry** in .scad scripts
- **Version control friendly** (text-based .scad files)
- **Parametric templates** for batch generation
- **Scriptable** via command-line OpenSCAD

### For Pipeline:
- **Open-source** (no licensing costs)
- **Cross-platform** (Windows/Mac/Linux)
- **Mature ecosystem** (20+ years development)
- **Well-documented** format

---

## Dependencies

```python
# requirements.txt additions
# (OpenSCAD is external executable, no Python deps needed)

# For advanced integration (optional):
solidpython2  # Python → OpenSCAD generator
# pip install solidpython2
```

### SolidPython Alternative

Instead of writing .scad directly, use SolidPython:

```python
from solid import *

# Create geometry in Python
cone = cylinder(r=1.0, h=2.0, segments=64)

# Export to .scad
scad_render_to_file(cone, "cone.scad")
```

---

## Implementation Priority

### Phase 1: Essential (High Priority)
- ✅ OpenSCAD installed: `C:\Program Files\OpenSCAD\openscad.exe`
- ⏳ Basic .scad export for primitives
- ⏳ Command-line rendering (scad → obj)
- ⏳ Parameter extraction from .scad

### Phase 2: Integration (Medium Priority)
- ⏳ Template → .scad export
- ⏳ Round-trip metadata tracking
- ⏳ Batch export for template variations

### Phase 3: Advanced (Low Priority)
- ⏳ Interactive parameter editor (PyQt5)
- ⏳ CSG operations via OpenSCAD
- ⏳ SolidPython integration
- ⏳ Live preview mode

---

## Next Steps

1. **Create `vaultmind_forge/forge_3d/openscad_export.py`**
   - Implement primitive → .scad conversion
   - Template export with parameters

2. **Create `vaultmind_forge/forge_3d/openscad_import.py`**
   - Command-line rendering integration
   - Parameter parsing

3. **Add to geometry examples**
   - Example: Export primitives to .scad
   - Example: CSG via OpenSCAD
   - Example: Round-trip editing workflow

4. **Documentation**
   - User guide for OpenSCAD integration
   - Template creation guide
   - CSG workflow examples

---

**Status:** Planned
**Priority:** High (Artist-friendly parametric CAD editor)
**OpenSCAD Version:** Installed at `C:\Program Files\OpenSCAD\openscad.exe`
**License:** GPL (OpenSCAD), compatible with VaultMind Forge usage

---

*VaultMind Forge + OpenSCAD = Professional Parametric CAD Pipeline* 🎯
