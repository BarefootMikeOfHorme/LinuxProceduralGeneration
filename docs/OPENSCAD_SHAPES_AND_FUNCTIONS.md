# VaultMind CAD - New Shapes and Functions for OpenSCAD
================================================================

## Overview

This document outlines the new shapes, functions, and features we'll add to our customized OpenSCAD to integrate seamlessly with VaultMind Forge.

## New Primitive Shapes

### Current OpenSCAD Primitives (Built-in)
```openscad
// Basic shapes
cube([x, y, z], center=true);
sphere(r=radius, $fn=segments);
cylinder(h=height, r=radius, $fn=segments);
polyhedron(points=[...], faces=[...]);

// 2D shapes
circle(r=radius, $fn=segments);
square([x, y], center=true);
polygon(points=[...]);

// Transformations
translate([x, y, z]) { ... }
rotate([rx, ry, rz]) { ... }
scale([sx, sy, sz]) { ... }

// CSG operations
union() { ... }
difference() { ... }
intersection() { ... }
hull() { ... }
minkowski() { ... }
```

### VaultMind Primitives to Add

#### 1. Cone (Enhanced)
```openscad
// Current (using cylinder):
cylinder(h=2, r1=1, r2=0, $fn=32);

// New VaultMind version:
vm_cone(radius=1, height=2, detail="high");
vm_cone(preset="traffic_cone");
vm_cone(radius=1, height=2, segments=32);
```

#### 2. Torus
```openscad
// Current (complex rotate_extrude):
rotate_extrude($fn=48)
    translate([2, 0, 0])
        circle(r=0.5, $fn=24);

// New VaultMind version:
vm_torus(major_radius=2, minor_radius=0.5, detail="high");
vm_torus(preset="donut");
vm_torus(major_radius=2, minor_radius=0.5,
         major_segments=48, minor_segments=24);
```

#### 3. Capsule
```openscad
// Current (complex union):
union() {
    cylinder(h=2, r=0.5, $fn=32);
    translate([0, 0, 1]) sphere(r=0.5, $fn=32);
    translate([0, 0, -1]) sphere(r=0.5, $fn=32);
}

// New VaultMind version:
vm_capsule(radius=0.5, height=2, detail="high");
vm_capsule(preset="pill");
```

#### 4. Tube (Hollow Cylinder)
```openscad
// Current (difference):
difference() {
    cylinder(h=4, r=1.0, $fn=64);
    cylinder(h=4.1, r=0.8, $fn=64);
}

// New VaultMind version:
vm_tube(outer_radius=1.0, inner_radius=0.8, height=4, detail="high");
vm_tube(preset="pipe");
```

#### 5. Ring (Flat Torus)
```openscad
// Current (difference of cylinders):
difference() {
    cylinder(h=0.1, r=2.0, $fn=64);
    cylinder(h=0.2, r=1.5, $fn=64);
}

// New VaultMind version:
vm_ring(outer_radius=2.0, inner_radius=1.5, thickness=0.1, detail="high");
vm_ring(preset="coin_edge");
```

#### 6. Dome (Hemisphere)
```openscad
// Current (difference):
difference() {
    sphere(r=2, $fn=64);
    translate([0, 0, -2])
        cube([5, 5, 4], center=true);
}

// New VaultMind version:
vm_dome(radius=2, detail="high");
vm_dome(preset="helmet");
```

#### 7. Pyramid
```openscad
// Current (cylinder with r2=0):
cylinder(h=2, r1=1, r2=0, $fn=4);

// New VaultMind version:
vm_pyramid(base_size=2, height=2, sides=4);
vm_pyramid(preset="egyptian");
vm_pyramid(preset="tent");
```

#### 8. Prism (Extruded Polygon)
```openscad
// Current (linear_extrude):
linear_extrude(height=3)
    circle(r=1, $fn=6);

// New VaultMind version:
vm_prism(sides=6, radius=1, height=3);
vm_prism(preset="hexagonal_column");
```

#### 9. Disc (Flat Circle)
```openscad
// Current:
cylinder(h=0.1, r=2, $fn=64);

// New VaultMind version:
vm_disc(radius=2, thickness=0.1, detail="high");
vm_disc(preset="coin");
```

#### 10. Tetrahedron
```openscad
// Current (polyhedron):
polyhedron(
    points = [[1,1,1], [-1,-1,1], [-1,1,-1], [1,-1,-1]],
    faces = [[0,1,2], [0,3,1], [0,2,3], [1,3,2]]
);

// New VaultMind version:
vm_tetrahedron(size=1);
vm_tetrahedron(preset="d4_die");
```

#### 11. Octahedron
```openscad
// Current (complex polyhedron):
polyhedron(
    points = [[1,0,0], [-1,0,0], [0,1,0], [0,-1,0], [0,0,1], [0,0,-1]],
    faces = [[0,2,4], [0,4,3], [0,3,5], [0,5,2],
             [1,2,5], [1,5,3], [1,3,4], [1,4,2]]
);

// New VaultMind version:
vm_octahedron(size=1);
vm_octahedron(preset="d8_die");
```

#### 12. Plane (Flat Rectangle)
```openscad
// Current:
cube([10, 0.1, 10], center=true);

// New VaultMind version:
vm_plane(width=10, depth=10, thickness=0.1);
vm_plane(preset="floor");
```

## New Functions

### Detail Level System
```openscad
// Instead of manually setting $fn everywhere
vm_set_detail("high");  // Sets global detail level

// Per-object override
vm_sphere(radius=2, detail="ultra");

// Detail levels:
// - "very_low"    (6 segments)
// - "low"         (8 segments)
// - "medium_low"  (16 segments)
// - "medium"      (32 segments)
// - "medium_high" (48 segments)
// - "high"        (64 segments)
// - "very_high"   (128 segments)
// - "ultra"       (256 segments)
```

### Preset System
```openscad
// Load preset configurations
vm_cone(preset="traffic_cone");
vm_torus(preset="donut");
vm_capsule(preset="pill");
vm_tube(preset="pipe");

// List available presets
vm_list_presets("cone");
// Output: ["traffic_cone", "wizard_hat", "ice_cream_cone", "party_hat"]

// Get preset parameters
vm_get_preset_params("cone", "traffic_cone");
// Output: {radius: 0.3, height: 0.7, detail: "medium"}
```

### LOD (Level of Detail) Generation
```openscad
// Generate multiple LOD levels automatically
vm_generate_lods(
    object = vm_sphere(radius=2),
    levels = ["high", "medium", "low", "very_low"],
    output_prefix = "sphere_lod"
);
// Outputs: sphere_lod_high.obj, sphere_lod_medium.obj, etc.
```

### Batch Export
```openscad
// Export to multiple game engines at once
vm_export_all_engines(
    object = vm_cone(preset="traffic_cone"),
    base_name = "traffic_cone"
);
// Outputs: traffic_cone_unity.obj, traffic_cone_unreal.obj, etc.
```

### Smart Transformations
```openscad
// Game-engine aware transformations
vm_transform_for_unity() { ... }     // Y-up, left-handed
vm_transform_for_unreal() { ... }    // Z-up, left-handed, 100x scale
vm_transform_for_godot() { ... }     // Y-up, right-handed
```

### Material/Color Functions
```openscad
// Attach color metadata
vm_set_color_scheme(
    name = "epic_flame",
    primary = "#FF4500",
    secondary = "#FFD700",
    accent = "#8B0000",
    metallic = 0.9,
    roughness = 0.3,
    emission = 0.5
);

// Apply material template
vm_apply_material("iron");
vm_apply_material("leather");
vm_apply_material("mythril");
```

### Game Property Functions
```openscad
// Attach game properties
vm_set_object_type("DESTRUCTIBLE");
vm_set_physics_type("DYNAMIC");
vm_set_stat("health", 100);
vm_set_stat("armor", 50);
vm_add_buff("Fire Resistance", "PASSIVE", duration=0);
```

### CSG Enhancements
```openscad
// Rounded boolean operations
vm_union_rounded(radius=0.1) {
    cube([2, 2, 2]);
    translate([1, 1, 1]) sphere(r=1);
}

// Chamfered boolean operations
vm_difference_chamfered(distance=0.2) {
    cube([3, 3, 3]);
    sphere(r=1.5);
}

// Smooth blending
vm_blend(blend_radius=0.3) {
    sphere(r=1);
    translate([1.5, 0, 0]) sphere(r=1);
}
```

### Array/Pattern Functions
```openscad
// Linear array
vm_linear_array(count=5, spacing=2, axis=[1, 0, 0]) {
    vm_cone(preset="traffic_cone");
}

// Circular array
vm_circular_array(count=8, radius=5) {
    vm_capsule(preset="pill");
}

// Grid array
vm_grid_array(rows=3, cols=3, spacing=[2, 2]) {
    vm_cube(size=1);
}

// Randomized placement
vm_scatter(count=20, area=[10, 10], seed=42) {
    vm_sphere(radius=0.5);
}
```

### Measurement Functions
```openscad
// Get bounding box
bbox = vm_bounding_box(vm_sphere(radius=2));
echo("Min:", bbox.min, "Max:", bbox.max);

// Get volume
volume = vm_volume(vm_cube(size=2));
echo("Volume:", volume);  // 8

// Get surface area
area = vm_surface_area(vm_sphere(radius=1));
echo("Area:", area);  // ~12.566

// Center of mass
com = vm_center_of_mass(my_object);
```

### Validation Functions
```openscad
// Check if mesh is manifold
is_valid = vm_is_manifold(my_object);
echo("Manifold:", is_valid);

// Check for holes
has_holes = vm_has_holes(my_object);
echo("Has holes:", has_holes);

// Validate for game engine
issues = vm_validate_for_unity(my_object);
// Returns: ["non-manifold edges", "flipped normals", etc.]
```

### Template Functions
```openscad
// Apply complete template
vm_apply_template(
    base_object = vm_cube(size=2),
    material = "iron",
    genre = "fantasy",
    rarity = "epic"
);

// Generate variations
vm_generate_variations(
    base_object = vm_sphere(radius=1),
    materials = ["leather", "iron", "mythril"],
    rarities = ["common", "rare", "epic"],
    output_dir = "variations/"
);
// Generates: leather_common.obj, leather_rare.obj, iron_common.obj, etc.
```

### Utility Functions
```openscad
// Quick preview modes
vm_preview_wireframe();
vm_preview_normals();
vm_preview_uv();

// Snap to grid
vm_snap_to_grid(my_object, grid_size=0.5);

// Align objects
vm_align(obj1, obj2, mode="center");  // center, min, max
vm_align_to_origin(my_object);

// Merge nearby vertices
vm_merge_vertices(my_object, threshold=0.001);

// Flip normals
vm_flip_normals(my_object);

// Recalculate normals
vm_recalculate_normals(my_object, smooth=true);
```

## Integration Features

### 1. SmartObject Properties
```openscad
// Define object type and auto-configure
vm_smart_object(
    name = "traffic_cone",
    type = "INTERACTIVE",
    geometry = vm_cone(preset="traffic_cone")
);
// Auto-sets: physics=DYNAMIC, render=OPAQUE, mass=5.0, etc.
```

### 2. Asset Metadata
```openscad
// Embed complete metadata
vm_asset(
    name = "Epic Sword",
    category = "weapon",
    tags = ["sword", "melee", "epic"],
    geometry = my_sword_model
) {
    // Stats
    vm_stat("damage", 50);
    vm_stat("attack_speed", 1.5);
    vm_stat("durability", 200);

    // Color scheme
    vm_color_scheme("epic_blade",
        primary="#C0C0FF",
        metallic=1.0,
        emission=0.3
    );

    // Buffs
    vm_buff("Frost Damage", "PASSIVE", frost_damage=15);

    // Equipment
    vm_equipment_slot("MAIN_HAND", position=[0, 0, 0]);
}
```

### 3. Multi-File Projects
```openscad
// Import VaultMind library
use <vaultmind.scad>

// Import other assets
use <assets/base_models.scad>
use <assets/materials.scad>

// Compose complex assets
vm_composite_asset("full_armor_set") {
    vm_import("helmet.obj");
    vm_import("chestplate.obj");
    vm_import("leggings.obj");
    vm_import("boots.obj");
}
```

### 4. Version Control Metadata
```openscad
// Embed version info
vm_version_info(
    version = "1.2.3",
    author = "VaultMind Studio",
    created = "2025-12-14",
    modified = "2025-12-14",
    description = "Epic flame sword with particle effects"
);
```

### 5. Export Pipeline Control
```openscad
// Fine-tune export settings
vm_export_settings(
    unity = {
        scale: 1.0,
        coordinate_system: "Y-up-LH",
        merge_vertices: true
    },
    unreal = {
        scale: 100.0,
        coordinate_system: "Z-up-LH",
        collision_mesh: true
    }
);
```

## C++ Implementation Strategy

### New Primitives (C++ Classes)
```cpp
// vaultmind_primitives.h
namespace VaultMind {
    class Cone : public Geometry {
        double radius, height;
        int segments;

        shared_ptr<PolySet> toPolySet() const override;
        BoundingBox getBoundingBox() const override;
    };

    class Torus : public Geometry {
        double major_radius, minor_radius;
        int major_segments, minor_segments;

        shared_ptr<PolySet> toPolySet() const override;
    };

    class Capsule : public Geometry {
        double radius, height;
        int segments;

        shared_ptr<PolySet> toPolySet() const override;
    };

    // ... more primitives
}
```

### Built-in Functions (C++)
```cpp
// vaultmind_functions.cpp
Value vm_cone(const Context *ctx, const EvalContext *evalctx) {
    // Parse parameters
    double radius = evalctx->getArgValue("radius").toDouble();
    double height = evalctx->getArgValue("height").toDouble();
    string detail = evalctx->getArgValue("detail").toString();

    // Create cone geometry
    auto cone = make_shared<VaultMind::Cone>(radius, height,
                                              detailToSegments(detail));
    return Value(cone);
}

// Register function
void register_vaultmind_functions() {
    Builtins::init("vm_cone", new BuiltinFunction(&vm_cone));
    Builtins::init("vm_torus", new BuiltinFunction(&vm_torus));
    // ... more functions
}
```

### Preset System (JSON Data)
```json
// vaultmind_presets.json
{
    "cone": {
        "traffic_cone": {
            "radius": 0.3,
            "height": 0.7,
            "detail": "medium"
        },
        "wizard_hat": {
            "radius": 0.4,
            "height": 1.2,
            "detail": "high"
        }
    },
    "torus": {
        "food_donut": {
            "major_radius": 1.0,
            "minor_radius": 0.3,
            "detail": "high"
        }
    }
}
```

### Metadata System (C++ Classes)
```cpp
// vaultmind_metadata.h
class AssetMetadata {
    string name;
    ObjectType type;
    PhysicsType physics;
    map<string, double> stats;
    vector<ColorScheme> color_schemes;
    vector<Buff> buffs;

    void exportToJSON(const string &path);
    void exportToYAML(const string &path);
};
```

## Priority Implementation Order

### Phase 1: Core Primitives
1. ✅ vm_cone() - Traffic cones, wizard hats, ice cream cones
2. ✅ vm_torus() - Donuts, rings, tires
3. ✅ vm_capsule() - Pills, bullets, rolling pins
4. ✅ vm_tube() - Pipes, hollow cylinders
5. ✅ vm_dome() - Helmets, igloos, half-spheres

### Phase 2: Detail & Presets
1. ✅ Detail level system (very_low to ultra)
2. ✅ Preset system (JSON-based)
3. ✅ vm_list_presets()
4. ✅ vm_get_preset_params()

### Phase 3: Game Integration
1. ✅ vm_set_object_type()
2. ✅ vm_set_stat()
3. ✅ vm_color_scheme()
4. ✅ vm_export_all_engines()

### Phase 4: Advanced Features
1. ✅ LOD generation
2. ✅ Template system
3. ✅ Array/pattern functions
4. ✅ Validation functions

## Testing Strategy

### Unit Tests
```cpp
TEST(VaultMindPrimitives, ConeBasic) {
    auto cone = VaultMind::Cone(1.0, 2.0, 32);
    EXPECT_EQ(cone.getVertexCount(), 33);  // 32 base + 1 apex
}

TEST(VaultMindPrimitives, TorusManifold) {
    auto torus = VaultMind::Torus(2.0, 0.5, 48, 24);
    EXPECT_TRUE(torus.isManifold());
}
```

### Integration Tests
```openscad
// test_vaultmind.scad
assert(vm_version() == "1.0.0");

cone = vm_cone(preset="traffic_cone");
assert(vm_is_manifold(cone));

bbox = vm_bounding_box(cone);
assert(bbox.max.z > 0.6);
```

## Documentation Requirements

### User Documentation
- Primitive reference (all vm_* functions)
- Preset catalog (with images)
- Tutorial: Basic shapes
- Tutorial: Game asset creation
- Tutorial: Batch generation

### Developer Documentation
- C++ API reference
- Adding new primitives guide
- Preset format specification
- Plugin development guide

## Success Criteria

- ✅ All 15 VaultMind primitives implemented in C++
- ✅ 60+ presets available
- ✅ Detail level system working
- ✅ Game property metadata export
- ✅ Multi-engine export working
- ✅ Performance: <100ms for complex primitives
- ✅ All primitives are manifold (no holes/gaps)
- ✅ Backward compatible with standard OpenSCAD syntax
