# VaultMind Forge - Layering System Research & Architecture
**Created:** 2025-11-26
**Purpose:** Design AI-driven layered asset creation for 2D, 3D, video, and game environments

---

## Executive Summary

VaultMind Forge currently lacks hierarchical composition capabilities. This document researches industry-standard layering systems and designs VAF 2.0 with:
- **2D image layers** (PSD-style blend modes, masks)
- **3D scene graphs** (glTF/USD hierarchies)
- **Smart objects** (Unity prefab-style instances)
- **AI training** for teaching models to create complex layered scenes

---

## Research Findings

### 1. Image Layering Systems (PSD/GIMP/Krita)

**Sources:** [Adobe Photoshop Layers](https://helpx.adobe.com/photoshop/using/layer-opacity-blending.html), [psd-tools API](https://psd-tools.readthedocs.io/en/latest/reference/psd_tools.api.layers.html)

**Technical Structure:**

**Layer Records:**
```python
class ImageLayer:
    bounds: Rect  # top, left, bottom, right
    blend_mode: BlendMode  # NORMAL, MULTIPLY, SCREEN, etc.
    opacity: int  # 0-255 (0=transparent, 255=opaque)
    channels: List[Channel]  # 0=red, 1=green, 2=blue, -1=alpha, -2=mask
    name: str
    effects: List[Effect]  # drop shadow, glow, bevel
    masks: List[Mask]  # user mask, vector mask
    clipping: bool  # clip to layer below
    parent_group: Optional[LayerGroup]
```

**Blend Modes:**
- **Normal, Multiply, Screen, Overlay** - Standard compositing
- **Color Dodge, Color Burn** - Dramatic lighting effects
- **Soft Light, Hard Light** - Contrast adjustments
- **Difference, Exclusion** - Inversion effects

**Masks:**
- **Layer mask** - Controls transparency per-pixel (grayscale)
- **Vector mask** - Clean scalable edges (paths)
- **Clipping mask** - Use shape of one layer to mask another

**Key Insights:**
- Layers stack bottom-to-top
- Each layer has independent blend mode + opacity
- Masks are non-destructive (original data preserved)
- Channel IDs: 0=R, 1=G, 2=B, -1=transparency, -2=user mask

---

### 2. 3D Scene Graphs (glTF/USD)

**Sources:** [glTF 2.0 Spec](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html), [glTF Scene Nodes Tutorial](https://github.com/KhronosGroup/glTF-Tutorials/blob/main/gltfTutorial/gltfTutorial_004_ScenesNodes.md), [USD Concept Mapping](https://docs.omniverse.nvidia.com/usd/latest/technical_reference/conceptual_data_mapping/glTF_concept_mapping_example.html)

**glTF Scene Graph:**
```json
{
  "scenes": [{
    "name": "MainScene",
    "nodes": [0, 1, 2]  // Root nodes
  }],
  "nodes": [
    {
      "name": "Character",
      "children": [3, 4],  // Head, Body
      "translation": [0, 0, 0],
      "rotation": [0, 0, 0, 1],  // Quaternion
      "scale": [1, 1, 1],
      "mesh": 5
    },
    {
      "name": "Head",
      "translation": [0, 1.5, 0],
      "mesh": 6
    }
  ]
}
```

**Transform Hierarchy:**
- Parent transforms multiply from bottom-to-top
- Child transform is **relative to parent**
- Final world transform = Parent * Child
- Supports: translation, rotation (quaternion), scale

**Node Structure:**
```python
class SceneNode:
    name: str
    children: List[int]  # Child node indices
    transform: Matrix4x4  # Local transform
    mesh: Optional[int]  # Mesh reference
    camera: Optional[int]
    light: Optional[int]
    extensions: Dict  # Custom data
```

**Key Insights:**
- Scene = collection of root nodes
- Node = point in hierarchy (may have mesh/camera/light)
- Transform inheritance via parent-child relationships
- glTF → USD mapping: Node ≈ Prim, Scene ≈ Stage

---

### 3. Game Engine Smart Objects (Unity Prefabs)

**Sources:** [Unity Prefabs Manual](https://docs.unity3d.com/Manual/Prefabs.html), [Prefab Guide](https://medium.com/@yalcinnomercann/unity-game-engine-a-guide-to-prefabs-552b7c1092b8)

**Prefab System:**
```csharp
// Prefab definition (template)
class Prefab {
    GameObject template;  // The master copy
    GUID assetGUID;  // Unique identifier
    List<Component> components;  // Scripts, renderers, etc.
    Transform hierarchy;  // Child objects
}

// Prefab instance (in scene)
class PrefabInstance {
    GUID prefabGUID;  // References template
    Dictionary<string, object> overrides;  // Per-instance modifications
    Transform worldTransform;  // Position in scene
}
```

**Instance Referencing:**
- Unity stores only **GUID** of prefab in instance
- Prefab fully loads with dependencies when needed
- Changes to prefab **auto-update all instances**
- Instances can have **overrides** (per-instance values)

**Architectural Constraints:**
- **Cannot store scene references in prefabs** (prefabs are templates)
- **Prefabs cannot reference specific scene objects** (would break reusability)

**Solutions for References:**
- **Dependency injection** at instantiation time
- **ScriptableObjects** as prefab databases
- **Reference managers** with static lookups
- **Event systems** for loose coupling

**Key Insights:**
- Prefab = reusable template (one definition)
- Instance = live copy in scene (many uses)
- Changes propagate: template edit → all instances update
- Memory efficient: stores GUID, not full copy

---

### 4. Photoshop Smart Objects

**Sources:** [Adobe Smart Objects](https://helpx.adobe.com/photoshop/desktop/create-manage-layers/smart-objects/create-embedded-smart-objects.html), [Smart Object Workflow](https://photoshopcafe.com/tutorials/Smart-object/smart-object_photoshop.htm)

**Smart Object Types:**

**Embedded Smart Object:**
```python
class EmbeddedSmartObject:
    original_data: bytes  # Full source file (PSD, AI, etc.)
    rendered_preview: Image  # Rasterized version for display
    transform: Matrix  # Scale, rotate, warp
    filters: List[SmartFilter]  # Non-destructive effects
```

**Linked Smart Object:**
```python
class LinkedSmartObject:
    source_file_path: str  # External file path
    last_modified: timestamp
    rendered_preview: Image
    transform: Matrix
    filters: List[SmartFilter]

    def update_if_changed(self):
        if source_file_modified_since(self.last_modified):
            reload_from_source()
```

**Non-Destructive Workflow:**
- **Transform** without quality loss (scale, rotate, warp)
- **Replace contents** - all instances update
- **Edit source** - double-click to edit original
- **Apply filters** non-destructively (Smart Filters)

**Reusable Components:**
- Create **icons, buttons, logos** as smart objects
- Place **multiple copies** in document
- **Edit once** → changes apply to all copies
- Perfect for **templates and themes**

**Key Insights:**
- Smart objects preserve original data (non-destructive)
- Linked objects auto-update when source changes
- Embedded objects store full source within file
- Parametric-like: edit source, all instances update

---

## VAF 2.0 Layer System Architecture

### Design Goals

1. **Universal Layers** - Works for 2D, 3D, video, game scenes
2. **AI Trainable** - Structure AI can learn to generate
3. **Smart Objects** - Instance referencing with auto-updates
4. **Non-Destructive** - Original data always preserved
5. **Python/Rust/C++ Compatible** - All three can read/write

### Core Data Structures

**Base Layer:**
```python
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

class LayerType(Enum):
    IMAGE_2D = "image_2d"
    MESH_3D = "mesh_3d"
    VIDEO = "video"
    AUDIO = "audio"
    GROUP = "group"
    SMART_OBJECT = "smart_object"
    REFERENCE = "reference"

class BlendMode(Enum):
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    SOFT_LIGHT = "soft_light"
    # ... 20+ more

@dataclass
class Transform:
    """3D transform (works for 2D when z=0)"""
    translation: [float, float, float] = (0, 0, 0)
    rotation: [float, float, float, float] = (0, 0, 0, 1)  # Quaternion
    scale: [float, float, float] = (1, 1, 1)

    def to_matrix(self) -> Matrix4x4:
        """Convert to 4x4 matrix"""
        pass

@dataclass
class Layer:
    """Universal layer for all asset types"""

    # Identity
    id: str  # UUID
    name: str
    type: LayerType

    # Hierarchy
    parent_id: Optional[str]  # Parent layer (None = root)
    children: List[str]  # Child layer IDs

    # Transform
    transform: Transform  # Local transform (relative to parent)

    # Visibility & Blending
    visible: bool = True
    opacity: float = 1.0  # 0.0-1.0
    blend_mode: BlendMode = BlendMode.NORMAL

    # Masks
    masks: List['Mask'] = []
    clipping: bool = False  # Clip to layer below

    # Content (polymorphic based on type)
    content: Dict[str, Any]  # Type-specific data

    # Smart object reference
    smart_object_ref: Optional[str] = None  # GUID of template
    smart_object_overrides: Dict[str, Any] = {}  # Per-instance mods

    # Metadata
    metadata: Dict[str, Any] = {}
    locked: bool = False

    def get_world_transform(self, layer_tree: 'LayerTree') -> Transform:
        """Calculate final world-space transform"""
        if self.parent_id is None:
            return self.transform

        parent = layer_tree.get_layer(self.parent_id)
        parent_world = parent.get_world_transform(layer_tree)
        return parent_world @ self.transform  # Matrix multiply
```

**Mask:**
```python
@dataclass
class Mask:
    type: str  # "bitmap", "vector", "gradient"
    data: Any  # Mask-specific data
    inverted: bool = False
    feather: float = 0.0  # Edge softness in pixels
    density: float = 1.0  # Mask strength 0-1
```

**Smart Object Template:**
```python
@dataclass
class SmartObjectTemplate:
    """Reusable template definition"""

    guid: str  # Unique identifier
    name: str
    type: LayerType

    # Embedded or linked
    storage_type: str  # "embedded" or "linked"
    source_file: Optional[str]  # Path if linked
    embedded_data: Optional[bytes]  # Full source if embedded

    # Default content
    default_content: Dict[str, Any]

    # Parameters (for procedural generation)
    parameters: Dict[str, 'Parameter'] = {}

    # Layer structure (for complex objects)
    layers: List[Layer] = []  # Can contain sub-layers

    @classmethod
    def create_instance(cls, guid: str, overrides: Dict = {}) -> Layer:
        """Create instance referencing this template"""
        return Layer(
            id=generate_uuid(),
            name=f"{cls.name}_instance",
            type=cls.type,
            smart_object_ref=guid,
            smart_object_overrides=overrides,
            content=cls.default_content.copy()
        )

@dataclass
class Parameter:
    """Parametric control for procedural generation"""
    name: str
    type: str  # "float", "int", "color", "string"
    default: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""
```

**Layer Tree:**
```python
class LayerTree:
    """Hierarchical layer structure"""

    def __init__(self):
        self.layers: Dict[str, Layer] = {}
        self.root_ids: List[str] = []
        self.smart_templates: Dict[str, SmartObjectTemplate] = {}

    def add_layer(self, layer: Layer, parent_id: Optional[str] = None):
        """Add layer to tree"""
        self.layers[layer.id] = layer

        if parent_id is None:
            self.root_ids.append(layer.id)
        else:
            parent = self.layers[parent_id]
            parent.children.append(layer.id)
            layer.parent_id = parent_id

    def get_layer(self, layer_id: str) -> Optional[Layer]:
        return self.layers.get(layer_id)

    def traverse_depth_first(self, callback, start_ids: List[str] = None):
        """DFS traversal"""
        if start_ids is None:
            start_ids = self.root_ids

        for layer_id in start_ids:
            layer = self.layers[layer_id]
            callback(layer)
            self.traverse_depth_first(callback, layer.children)

    def flatten(self) -> List[Layer]:
        """Get all layers in render order (bottom-to-top)"""
        result = []
        self.traverse_depth_first(lambda L: result.append(L))
        return result

    def register_smart_template(self, template: SmartObjectTemplate):
        """Register reusable template"""
        self.smart_templates[template.guid] = template

    def instantiate_smart_object(self, template_guid: str,
                                  parent_id: Optional[str] = None,
                                  overrides: Dict = {}) -> Layer:
        """Create instance of smart object"""
        template = self.smart_templates[template_guid]
        instance = template.create_instance(template_guid, overrides)
        self.add_layer(instance, parent_id)
        return instance

    def update_smart_instances(self, template_guid: str):
        """Update all instances when template changes"""
        for layer in self.layers.values():
            if layer.smart_object_ref == template_guid:
                # Re-apply template content with overrides
                self.refresh_smart_instance(layer)
```

### Type-Specific Content Schemas

**2D Image Layer:**
```python
ImageLayerContent = {
    "type": "image_2d",
    "image_data": bytes,  # PNG/JPEG encoded
    "width": int,
    "height": int,
    "channels": ["r", "g", "b", "a"],
    "effects": [
        {"type": "drop_shadow", "offset": [2, 2], "blur": 4, "color": [0,0,0,128]},
        {"type": "glow", "radius": 10, "color": [255,255,0,128]}
    ]
}
```

**3D Mesh Layer:**
```python
MeshLayerContent = {
    "type": "mesh_3d",
    "mesh_data": bytes,  # glTF/FBX encoded
    "materials": [
        {"name": "MainMaterial", "albedo": [1,1,1], "metallic": 0.5}
    ],
    "bones": [],  # Skeletal animation
    "morph_targets": []  # Blend shapes
}
```

**Video Layer:**
```python
VideoLayerContent = {
    "type": "video",
    "video_data": bytes,  # MP4 encoded
    "duration": float,  # Seconds
    "frame_rate": 30.0,
    "audio_tracks": [],
    "start_time": 0.0,  # Offset in timeline
    "speed": 1.0  # Playback speed multiplier
}
```

**Group Layer:**
```python
GroupLayerContent = {
    "type": "group",
    "pass_through": bool,  # Blend children as one layer
    "collapse_effects": bool  # Apply effects to group or individual children
}
```

---

## VAF 2.0 File Format

**JSON Structure:**
```json
{
  "vaf_version": "2.0",
  "format_type": "layered",

  "metadata": {
    "created": "2025-11-26T10:00:00Z",
    "modified": "2025-11-26T12:00:00Z",
    "author": "VaultMind Forge AI",
    "description": "Cyberpunk city scene with 12 layers",
    "lineage": {
      "parent_assets": ["asset_001.vaf", "asset_002.vaf"],
      "generation_params": {...},
      "ai_model": "merlinv1_stage2"
    }
  },

  "canvas": {
    "width": 3840,
    "height": 2160,
    "depth": 100,  // For 3D scenes
    "units": "pixels",
    "color_space": "sRGB"
  },

  "smart_templates": {
    "building_template_001": {
      "guid": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Cyberpunk Building",
      "type": "mesh_3d",
      "storage_type": "embedded",
      "embedded_data": "base64_encoded_glb_data...",
      "parameters": {
        "height": {"type": "float", "default": 50.0, "min": 10, "max": 200},
        "neon_color": {"type": "color", "default": [0, 255, 255]}
      }
    }
  },

  "layers": [
    {
      "id": "layer_bg",
      "name": "Background Sky",
      "type": "image_2d",
      "parent_id": null,
      "children": [],
      "transform": {
        "translation": [0, 0, -100],
        "rotation": [0, 0, 0, 1],
        "scale": [1, 1, 1]
      },
      "visible": true,
      "opacity": 1.0,
      "blend_mode": "normal",
      "content": {
        "type": "image_2d",
        "embedded_file": "sky_gradient.png",
        "width": 3840,
        "height": 2160
      }
    },
    {
      "id": "layer_city_group",
      "name": "City Buildings",
      "type": "group",
      "parent_id": null,
      "children": ["layer_building_1", "layer_building_2", "layer_building_3"],
      "transform": {"translation": [0, 0, 0], "rotation": [0, 0, 0, 1], "scale": [1, 1, 1]},
      "visible": true,
      "opacity": 1.0,
      "content": {"type": "group", "pass_through": false}
    },
    {
      "id": "layer_building_1",
      "name": "Building Instance 1",
      "type": "mesh_3d",
      "parent_id": "layer_city_group",
      "transform": {"translation": [-50, 0, 0], "rotation": [0, 0, 0, 1], "scale": [1, 1.5, 1]},
      "visible": true,
      "smart_object_ref": "building_template_001",
      "smart_object_overrides": {
        "height": 75.0,
        "neon_color": [255, 0, 255]
      }
    },
    {
      "id": "layer_building_2",
      "name": "Building Instance 2",
      "type": "mesh_3d",
      "parent_id": "layer_city_group",
      "transform": {"translation": [50, 0, 0], "rotation": [0, 0.707, 0, 0.707], "scale": [1, 2, 1]},
      "visible": true,
      "smart_object_ref": "building_template_001",
      "smart_object_overrides": {
        "height": 100.0,
        "neon_color": [0, 255, 255]
      }
    },
    {
      "id": "layer_effects",
      "name": "Atmospheric Effects",
      "type": "image_2d",
      "parent_id": null,
      "transform": {"translation": [0, 0, 50], "rotation": [0, 0, 0, 1], "scale": [1, 1, 1]},
      "visible": true,
      "opacity": 0.7,
      "blend_mode": "screen",
      "masks": [
        {"type": "gradient", "direction": [0, -1], "feather": 100}
      ],
      "content": {
        "type": "image_2d",
        "procedural": "particle_system",
        "params": {"count": 10000, "size": [1, 3], "color": [200, 200, 255]}
      }
    }
  ]
}
```

**Binary Format (for performance):**
```
VAF2 Header (64 bytes)
├─ Magic: "VAF2" (4 bytes)
├─ Version: 2.0 (4 bytes)
├─ Metadata offset (8 bytes)
├─ Layer tree offset (8 bytes)
├─ Smart templates offset (8 bytes)
├─ Embedded assets offset (8 bytes)
└─ Checksum (32 bytes SHA-256)

Metadata Section
├─ JSON metadata (compressed)

Layer Tree Section
├─ Layer count (4 bytes)
├─ Layer records (variable)
│   ├─ Layer ID (16 bytes UUID)
│   ├─ Name length + name (variable)
│   ├─ Transform (52 bytes: 3×vec3 + quaternion)
│   ├─ Flags (4 bytes: visible, locked, etc.)
│   ├─ Content offset (8 bytes)
│   └─ Children count + IDs (variable)

Smart Templates Section
├─ Template count (4 bytes)
├─ Template records (variable)

Embedded Assets Section
├─ Asset count (4 bytes)
├─ Asset blocks (variable)
│   ├─ Asset ID (16 bytes)
│   ├─ Type (PNG/GLB/MP4) (4 bytes)
│   ├─ Size (8 bytes)
│   └─ Data (variable)
```

---

## AI Training for Layered Generation

### Training Data Structure

**Goal:** Teach AI to generate complete scenes with proper layer hierarchies

**Training Example Format:**
```json
{
  "prompt": "cyberpunk city at night with neon lights",
  "target_output": {
    "layer_structure": [
      {
        "name": "sky_gradient",
        "type": "background",
        "z_order": 0,
        "generation_prompt": "dark purple to black gradient sky, stars",
        "blend_mode": "normal"
      },
      {
        "name": "distant_buildings",
        "type": "3d_mesh_group",
        "z_order": 1,
        "count": 20,
        "generation_prompt": "tall cyberpunk skyscrapers, silhouettes",
        "smart_object": "building_template",
        "variation_params": {
          "height": [50, 200],
          "width": [20, 40],
          "neon_color": "random_from_palette"
        }
      },
      {
        "name": "mid_buildings",
        "type": "3d_mesh_group",
        "z_order": 2,
        "count": 10,
        "generation_prompt": "detailed cyberpunk buildings with windows, signs",
        "detail_level": "high"
      },
      {
        "name": "street_level",
        "type": "image_2d",
        "z_order": 3,
        "generation_prompt": "busy street, cars, pedestrians, market stalls",
        "lighting": "neon reflections on wet pavement"
      },
      {
        "name": "atmospheric_fog",
        "type": "procedural_particles",
        "z_order": 4,
        "blend_mode": "screen",
        "opacity": 0.6,
        "params": {"density": 5000, "size": [2, 8], "color": [100, 150, 200]}
      },
      {
        "name": "lens_effects",
        "type": "post_process",
        "z_order": 5,
        "effects": ["bloom", "chromatic_aberration", "vignette"]
      }
    ]
  }
}
```

**AI Model Architecture:**

```python
class LayeredSceneGenerator:
    """AI model that generates complete layered scenes"""

    def __init__(self):
        # Base generator (Merlinv1 or SDXL)
        self.base_generator = Merlinv1Backend()

        # Scene structure planner
        self.scene_planner = TransformerModel(
            input_dim=768,  # Text embedding
            output_dim=1024,  # Scene structure tokens
            layers=12
        )

        # Layer generators (specialized per type)
        self.generators = {
            "background": SDXLBackgroundGenerator(),
            "3d_mesh": Mesh3DGenerator(),
            "image_2d": SDXL2DGenerator(),
            "procedural": ProceduralGenerator()
        }

    def generate(self, prompt: str) -> LayerTree:
        """Generate complete layered scene from prompt"""

        # 1. Plan scene structure
        scene_plan = self.scene_planner.plan(prompt)
        # Output: List of layers with types, positions, prompts

        # 2. Create layer tree
        tree = LayerTree()

        # 3. Generate each layer
        for layer_spec in scene_plan:
            generator = self.generators[layer_spec.type]

            # Generate layer content
            content = generator.generate(
                prompt=layer_spec.prompt,
                params=layer_spec.params
            )

            # Create layer
            layer = Layer(
                id=generate_uuid(),
                name=layer_spec.name,
                type=layer_spec.type,
                transform=layer_spec.transform,
                blend_mode=layer_spec.blend_mode,
                opacity=layer_spec.opacity,
                content=content
            )

            tree.add_layer(layer, parent_id=layer_spec.parent_id)

        # 4. If using smart objects, create templates
        for template_spec in scene_plan.smart_templates:
            template = self.create_smart_template(template_spec)
            tree.register_smart_template(template)

            # Create instances
            for instance_spec in template_spec.instances:
                tree.instantiate_smart_object(
                    template.guid,
                    parent_id=instance_spec.parent_id,
                    overrides=instance_spec.overrides
                )

        return tree
```

**Training Approach:**

1. **Dataset:** 100K+ scenes with manual layer annotations
2. **Phase 1:** Train scene planner (structure prediction)
3. **Phase 2:** Train specialized generators per layer type
4. **Phase 3:** End-to-end fine-tuning
5. **Reward:** Quality scores from forge_validator + user feedback

---

## Implementation Roadmap

### Phase 1: Core Layer System (Week 1-2)

**Python Implementation:**
```bash
vaultmind_forge/forge_layering/
├── __init__.py
├── layer.py           # Layer, Transform, Mask classes
├── layer_tree.py      # LayerTree hierarchy
├── smart_objects.py   # SmartObjectTemplate, Parameter
├── blend_modes.py     # Blend mode implementations
├── serialization.py   # JSON/binary VAF2 read/write
└── tests/
    └── test_layer_system.py
```

**Tasks:**
- [x] Define Layer data structure
- [x] Implement Transform math (matrix ops)
- [x] Build LayerTree with parent/child
- [x] Add blend mode calculations
- [x] JSON serialization

### Phase 2: Smart Objects (Week 3)

**Tasks:**
- [ ] SmartObjectTemplate system
- [ ] Instance creation & overrides
- [ ] Template update propagation
- [ ] Embedded vs linked storage
- [ ] Parameter system for procedural generation

### Phase 3: Type-Specific Implementations (Week 4-5)

**2D Image Layers:**
- [ ] PSD-style layer compositing
- [ ] Mask support (bitmap, vector, gradient)
- [ ] Effect system (drop shadow, glow, etc.)
- [ ] Channel operations

**3D Mesh Layers:**
- [ ] glTF scene graph import/export
- [ ] Transform hierarchy rendering
- [ ] Material system
- [ ] LOD support

**Video Layers:**
- [ ] Timeline system
- [ ] Frame-accurate compositing
- [ ] Audio track support

### Phase 4: AI Integration (Week 6-8)

**Scene Planner:**
- [ ] Train on annotated scenes dataset
- [ ] Layer count/type prediction
- [ ] Spatial arrangement planning
- [ ] Prompt decomposition per layer

**Layer Generators:**
- [ ] Background generator (gradients, skies)
- [ ] 3D mesh generator (buildings, objects)
- [ ] 2D detail generator (textures, decals)
- [ ] Procedural effect generator (particles, fog)

### Phase 5: Node System Integration (Week 9)

**New Nodes:**
- [ ] Layer Creator (creates layers in tree)
- [ ] Layer Compositor (renders layer stack)
- [ ] Smart Object Instantiator
- [ ] Scene Structure Planner (AI)
- [ ] Layer Effect Applier

### Phase 6: Production (Week 10)

**Testing:**
- [ ] Generate 1000 layered scenes
- [ ] Validate with forge_validator
- [ ] User testing & feedback
- [ ] Performance optimization

**Documentation:**
- [ ] VAF 2.0 format specification
- [ ] API documentation
- [ ] Tutorial: Creating layered scenes
- [ ] Tutorial: Training AI for scene generation

---

## Example Use Cases

### Use Case 1: AI-Generated Game Environment

**Input:** "medieval fantasy village, 30 buildings, market square, castle in background"

**Output (VAF 2.0 with layers):**
```
Scene: Medieval Village (47 layers)
├─ Background Group (3 layers)
│  ├─ Sky Gradient
│  ├─ Mountain Silhouettes
│  └─ Distant Forest
├─ Castle Group (12 layers)
│  ├─ Castle Base (mesh)
│  ├─ Tower 1-4 (smart object instances)
│  ├─ Walls (mesh)
│  └─ Flags (animated)
├─ Village Group (25 layers)
│  ├─ Building instances (20×) [SMART OBJECT]
│  │  ├─ Template: "medieval_house"
│  │  ├─ Variations: roof color, size, door style
│  │  └─ Auto-placed on terrain
│  ├─ Market stalls (5×)
│  └─ Town square (ground texture)
└─ Foreground Effects (7 layers)
   ├─ Atmospheric haze (particles)
   ├─ Sunbeams (volumetric)
   ├─ Depth of field mask
   └─ Color grading
```

**Smart Object Benefits:**
- Edit "medieval_house" template → all 20 instances update
- Memory efficient: 1 mesh definition, 20 transforms
- Consistent style across village
- Easy to add/remove buildings

### Use Case 2: Full Movie Scene

**Input:** "sci-fi space battle, two capital ships, fighter swarm, explosion effects"

**Output:**
```
Scene: Space Battle (103 layers)
├─ Background Nebula (5 layers, 8K resolution)
├─ Star Field (procedural, 50K particles)
├─ Capital Ship 1 (18 layers)
│  ├─ Hull (mesh with PBR materials)
│  ├─ Engine glow (emission layer, bloom)
│  ├─ Windows (light sources)
│  ├─ Turrets 1-8 (smart objects, animated)
│  └─ Shield effect (animated shader)
├─ Capital Ship 2 (18 layers, same structure)
├─ Fighter Squadron (40 instances)
│  ├─ Template: "fighter_model_01"
│  ├─ Flight paths (animated transforms)
│  └─ Variations: squadron colors
├─ Explosions (12 layers)
│  ├─ Flash (additive blend)
│  ├─ Fireball (mesh with volumetrics)
│  ├─ Debris (particle system)
│  └─ Shockwave (animated sphere)
└─ Post Effects (10 layers)
   ├─ Lens flare
   ├─ Motion blur
   ├─ Chromatic aberration
   └─ Film grain
```

**Timeline Integration:**
- Each layer has start_time, duration
- Animations stored per-layer
- Render outputs frame sequence
- Editable in timeline view

### Use Case 3: Huge Native 3D Image with Depth

**Input:** "panoramic city view, 360° environment, 100+ buildings, day-night cycle"

**Output:**
```
Scene: City Panorama 360° (250+ layers)
├─ Sky Dome (HDR, time-of-day variants)
├─ Distant City Ring (80 buildings)
│  ├─ LOD0: Simple boxes (far distance)
│  ├─ Smart templates: 5 building types
│  └─ Instanced 80 times in circular pattern
├─ Mid City Belt (50 buildings)
│  ├─ LOD1: Detailed models
│  ├─ Windows, balconies, AC units
│  └─ Neon signs (emissive)
├─ Close Buildings (20 buildings)
│  ├─ LOD2: Maximum detail
│  ├─ Interior visible through windows
│  └─ Rooftop details
├─ Street Level (30 layers)
│  ├─ Roads (mesh with textures)
│  ├─ Sidewalks
│  ├─ Street lights (instances)
│  ├─ Cars (smart objects, varied)
│  └─ Pedestrians
├─ Lighting Group (20 layers)
│  ├─ Sunlight (directional, animated)
│  ├─ Street lights (point lights ×100)
│  ├─ Building windows (area lights)
│  └─ Neon signs (emissive materials)
└─ Atmospheric Effects (15 layers)
   ├─ Volumetric fog
   ├─ Clouds (animated)
   ├─ Rain/snow (particle systems)
   └─ Light rays
```

**Smart Features:**
- **LOD system:** Auto-switches detail based on distance
- **Day/night cycle:** Lighting layers animate over time
- **Procedural placement:** AI arranges buildings realistically
- **Instance optimization:** 250 buildings = ~15 unique models

---

## Technical Challenges & Solutions

### Challenge 1: Memory Management (Large Scenes)

**Problem:** 250-layer scene with 100MB per layer = 25GB RAM

**Solutions:**
1. **Lazy loading:** Only load visible layers
2. **Streaming:** Load layers as needed during render
3. **Proxy previews:** Low-res thumbnails for UI, full-res on demand
4. **Smart object sharing:** Embedded data loaded once, shared by instances
5. **Compressed storage:** zstd compression for embedded assets

### Challenge 2: Render Performance

**Problem:** Compositing 250 layers in real-time

**Solutions:**
1. **GPU acceleration:** Rust/C++ renderers with GPU shaders
2. **Layer caching:** Cache rendered groups if unchanged
3. **Dirty flagging:** Only re-render modified layers
4. **Parallel rendering:** Multi-threaded layer composition
5. **Tiled rendering:** Render in chunks for huge resolutions

### Challenge 3: AI Training Data

**Problem:** Need 100K+ annotated layered scenes

**Solutions:**
1. **Synthetic generation:** Procedurally generate training scenes
2. **Reverse engineering:** Import PSD/Blender files, extract layers
3. **Semi-supervised:** AI suggests layers, human validates
4. **Transfer learning:** Start from Merlinv1, fine-tune for structure
5. **Active learning:** Focus on hard examples (complex scenes)

### Challenge 4: Cross-Language Support (Python/Rust/C++)

**Problem:** Rust needs to read/write same VAF2 format as Python

**Solutions:**
1. **Shared schema:** JSON schema defines format
2. **Binary layout:** Document exact byte layout
3. **Validation suite:** Cross-language test files
4. **Bindings:** PyO3 for Rust↔Python, pybind11 for C++↔Python
5. **Reference implementation:** Python is source of truth

---

## Success Metrics

### Functional Metrics
- ✅ Create 2D layered images (10-50 layers)
- ✅ Create 3D scenes with hierarchy (50-200 nodes)
- ✅ Smart object instances update when template changes
- ✅ AI generates structured scenes from text prompts
- ✅ Export to PSD, glTF, USD, Unity prefabs

### Performance Metrics
- ⚡ Load 100-layer scene: <2 seconds
- ⚡ Composite 50 layers: 60 FPS at 1080p
- ⚡ Smart object update (100 instances): <500ms
- ⚡ VAF2 file size: <50% larger than flat equivalent

### AI Quality Metrics
- 🎯 Scene structure accuracy: >85% (matches human layout)
- 🎯 Layer count prediction: ±3 layers of optimal
- 🎯 Smart object usage: >60% of repeated elements
- 🎯 Prompt decomposition: <10% hallucination rate

---

## References

**Image Layering:**
- [Adobe Photoshop Layer Opacity](https://helpx.adobe.com/photoshop/using/layer-opacity-blending.html)
- [psd-tools Documentation](https://psd-tools.readthedocs.io/en/latest/reference/psd_tools.api.layers.html)
- [Layered PSD Files Explained](https://ultida.com/what-is-a-layered-psd-file/)

**3D Scene Graphs:**
- [glTF 2.0 Specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)
- [glTF Scene Nodes Tutorial](https://github.com/KhronosGroup/glTF-Tutorials/blob/main/gltfTutorial/gltfTutorial_004_ScenesNodes.md)
- [USD Concept Mapping](https://docs.omniverse.nvidia.com/usd/latest/technical_reference/conceptual_data_mapping/glTF_concept_mapping_example.html)
- [WebGL Scene Graph](https://webglfundamentals.org/webgl/lessons/webgl-scene-graph.html)

**Game Engine Smart Objects:**
- [Unity Prefabs Manual](https://docs.unity3d.com/Manual/Prefabs.html)
- [Unity Prefab Guide](https://medium.com/@yalcinnomercann/unity-game-engine-a-guide-to-prefabs-552b7c1092b8)

**Photoshop Smart Objects:**
- [Adobe Smart Objects](https://helpx.adobe.com/photoshop/desktop/create-manage-layers/smart-objects/create-embedded-smart-objects.html)
- [Smart Object Workflow](https://photoshopcafe.com/tutorials/Smart-object/smart-object_photoshop.htm)

---

**Status:** ✅ Research Complete, Design Ready
**Next Step:** Begin Phase 1 implementation (core layer system)
**Estimated Total Time:** 10 weeks to production-ready layering system

---

**END OF LAYERING SYSTEM RESEARCH**
