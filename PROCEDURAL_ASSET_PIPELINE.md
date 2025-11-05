# VaultMind Forge - Procedural Asset Conversion Pipeline

## Overview

The **forge_converter** module handles bidirectional asset conversion for procedural generation workflows:

1. **INPUT CONVERSION**: Source formats → Standardized procedural generation format
2. **PROCEDURAL GENERATION**: Create/modify assets using forge modules
3. **OUTPUT CONVERSION**: Generated assets → Engine-specific formats

---

## Complete Conversion Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT CONVERSION PHASE                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  Source Assets (Various Formats)              │
    │  - FBX models from artist                     │
    │  - OBJ reference meshes                       │
    │  - PNG/TGA textures                           │
    │  - Blender scenes                             │
    │  - CAD files (STEP, IGES)                     │
    └───────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  forge_converter (INPUT)                      │
    │  - Normalize formats                          │
    │  - Extract metadata                           │
    │  - Validate compatibility                     │
    │  - Create procedural-ready assets             │
    └───────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  Standardized Procedural Format               │
    │  - GLTF/GLB (geometry)                        │
    │  - JSON (metadata)                            │
    │  - PNG (textures, normalized)                 │
    │  - Ready for procedural manipulation          │
    └───────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  PROCEDURAL GENERATION PHASE                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  forge_diffusion (AI Generation)              │
    │  - Generate new variations                    │
    │  - Style transfer                             │
    │  - Texture synthesis                          │
    └───────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  forge_semantic (Downscaling)                 │
    │  - Generate LOD levels                        │
    │  - Multi-resolution pyramids                  │
    └───────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  forge_sr (Upscaling)                         │
    │  - Enhance resolution                         │
    │  - Detail recovery                            │
    └───────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  forge_validator (Quality Check)              │
    │  - Validate generated assets                  │
    │  - Quality metrics                            │
    │  - Accept/reject based on thresholds          │
    └───────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  Generated Procedural Assets                  │
    │  - AI-generated textures                      │
    │  - Procedural variations                      │
    │  - Multi-resolution LODs                      │
    │  - Validated and ready for export             │
    └───────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT CONVERSION PHASE                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  forge_converter (OUTPUT)                     │
    │  - Convert to engine formats                  │
    │  - Apply engine-specific optimizations        │
    │  - Package with metadata                      │
    └───────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  Engine-Ready Assets                          │
    │  ├─ Unity: FBX + BC7 DDS + .mat              │
    │  ├─ Unreal: FBX + TGA + .uasset              │
    │  ├─ Godot: GLTF + WebP + .tres               │
    │  └─ Web: GLB + JPG + .json                   │
    └───────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  forge_packaging                              │
    │  - Create distribution packages               │
    │  - Include lineage metadata                   │
    │  - Generate manifests                         │
    └───────────────────────────────────────────────┘
                              ↓
    ┌───────────────────────────────────────────────┐
    │  Deployed to Engine/Editor                    │
    └───────────────────────────────────────────────┘
```

---

## Input Conversion Module

### Purpose
Convert various source formats into a standardized format suitable for procedural generation.

### Supported Input Formats

**3D Models:**
- FBX → GLTF (universal interchange)
- OBJ → GLTF (simple geometry)
- BLEND → GLTF (Blender exports)
- DAE → GLTF (Collada)
- STL → GLTF (CAD/3D printing)
- STEP/IGES → GLTF (via CAD converter)

**Textures:**
- PSD → PNG (flatten layers, preserve resolution)
- TIFF → PNG (normalize format)
- TGA → PNG (standardize)
- DDS → PNG (decompress)
- WebP → PNG (compatibility)

**Materials:**
- MTL → JSON (material properties)
- Blender materials → JSON (via Python API)
- Unity .mat → JSON (material export)

### Input Converter API

```python
from vaultmind_forge.forge_converter import InputConverter

converter = InputConverter(
    output_format="gltf",  # Standardized format
    output_dir="procedural/input"
)

# Convert source asset to procedural-ready format
result = converter.prepare_for_generation(
    source_path="source/artist_model.fbx",
    options={
        "extract_textures": True,
        "normalize_scale": True,
        "center_geometry": True,
        "generate_uvs": True,
        "extract_materials": True,
        "validation_level": "strict"
    }
)

# Result contains:
# - result.gltf_path: Converted GLTF model
# - result.textures: Extracted textures as PNG
# - result.materials: Material data as JSON
# - result.metadata: Asset metadata for generation
```

### Input Normalization Rules

**Geometry:**
- Convert to right-handed coordinate system (Y-up)
- Normalize scale (1 unit = 1 meter)
- Center at origin
- Ensure valid UVs (0-1 range)
- Remove degenerate geometry
- Validate manifold meshes

**Textures:**
- Convert to PNG (lossless)
- Normalize to power-of-2 dimensions (if needed)
- sRGB color space for diffuse/albedo
- Linear color space for normal/data maps
- Extract channels from packed textures

**Materials:**
- Extract PBR properties
- Normalize to metallic/roughness workflow
- Store as JSON with references to textures

---

## Procedural Generation Standards

### Standard Procedural Format

**Directory Structure:**
```
procedural/
├── input/              # Normalized inputs
│   ├── models/
│   │   └── asset.gltf
│   ├── textures/
│   │   ├── diffuse.png
│   │   ├── normal.png
│   │   └── roughness.png
│   └── metadata/
│       └── asset.json
│
├── generated/          # Generated variations
│   ├── variations/
│   │   ├── var_001/
│   │   ├── var_002/
│   │   └── var_003/
│   └── validated/      # Passed validation
│       └── winner/
│
└── output/             # Engine-ready exports
    ├── unity/
    ├── unreal/
    └── web/
```

### Metadata Schema

```json
{
  "asset_id": "uuid",
  "source_file": "original.fbx",
  "conversion_date": "2025-11-04T12:00:00Z",
  "normalization": {
    "coordinate_system": "right_handed_y_up",
    "scale_factor": 1.0,
    "units": "meters",
    "centered": true
  },
  "geometry": {
    "vertices": 10000,
    "triangles": 18000,
    "has_uvs": true,
    "has_normals": true,
    "is_manifold": true,
    "bounding_box": {
      "min": [-1.0, 0.0, -1.0],
      "max": [1.0, 2.0, 1.0]
    }
  },
  "textures": [
    {
      "type": "diffuse",
      "path": "textures/diffuse.png",
      "resolution": [2048, 2048],
      "color_space": "sRGB"
    },
    {
      "type": "normal",
      "path": "textures/normal.png",
      "resolution": [2048, 2048],
      "color_space": "linear"
    }
  ],
  "materials": [
    {
      "name": "main_material",
      "pbr_properties": {
        "base_color": [1.0, 1.0, 1.0, 1.0],
        "metallic": 0.0,
        "roughness": 0.5,
        "normal_scale": 1.0
      },
      "texture_maps": {
        "diffuse": "textures/diffuse.png",
        "normal": "textures/normal.png",
        "roughness": "textures/roughness.png"
      }
    }
  ],
  "procedural_hints": {
    "suitable_for_variation": true,
    "lod_candidate": true,
    "texture_synthesis_ready": true,
    "style_transfer_compatible": true
  }
}
```

---

## Output Conversion Module

### Purpose
Convert procedurally generated assets into engine-specific optimized formats.

### Output Converter API

```python
from vaultmind_forge.forge_converter import OutputConverter
from vaultmind_forge.forge_converter import TargetEngine, ConversionProfile

converter = OutputConverter(
    source_dir="procedural/generated/validated/winner",
    output_base="procedural/output"
)

# Convert for specific engine
result = converter.export_for_engine(
    asset_path="procedural/generated/validated/winner/model.gltf",
    target_engine=TargetEngine.UNITY,
    profile=ConversionProfile.BALANCED,
    options={
        "generate_lods": True,
        "lod_count": 3,
        "texture_compression": "BC7",
        "max_texture_size": 2048,
        "create_prefab": True,
        "include_materials": True
    }
)

# Multi-platform export
results = converter.export_multi_platform(
    asset_path="procedural/generated/validated/winner/model.gltf",
    targets={
        "unity": {"profile": "balanced", "mobile": False},
        "unreal": {"profile": "quality", "nanite": True},
        "web": {"profile": "optimized", "draco": True}
    }
)
```

### Engine-Specific Conversions

#### Unity Export
```python
unity_export = converter.export_for_unity(
    model="winner/model.gltf",
    textures=["winner/diffuse.png", "winner/normal.png"],
    options={
        "model_format": "fbx",              # Convert GLTF → FBX
        "texture_format": "dds",            # Convert PNG → DDS
        "diffuse_compression": "BC7",       # High quality diffuse
        "normal_compression": "BC5",        # Optimized normals
        "create_prefab": True,              # Generate .prefab
        "lod_screen_percentages": [0.6, 0.3, 0.15],
        "generate_colliders": False
    }
)
# Outputs:
# - unity/model.fbx
# - unity/textures/diffuse_BC7.dds
# - unity/textures/normal_BC5.dds
# - unity/materials/material.mat
# - unity/model.prefab
```

#### Unreal Export
```python
unreal_export = converter.export_for_unreal(
    model="winner/model.gltf",
    textures=["winner/diffuse.png", "winner/normal.png"],
    options={
        "model_format": "fbx",              # Convert GLTF → FBX
        "texture_format": "tga",            # Convert PNG → TGA
        "pack_orm": True,                   # Pack Occlusion/Roughness/Metallic
        "naming_convention": "unreal",      # T_AssetName_Type
        "lod_count": 4,
        "nanite_enabled": True,
        "generate_collision": "UCX",
        "lightmap_uvs": True
    }
)
# Outputs:
# - unreal/model.fbx
# - unreal/model_LOD0.fbx
# - unreal/model_LOD1.fbx
# - unreal/textures/T_Model_D.tga (diffuse)
# - unreal/textures/T_Model_N.tga (normal)
# - unreal/textures/T_Model_ORM.tga (packed)
# - unreal/materials/M_Model.uasset (material)
```

#### Godot Export
```python
godot_export = converter.export_for_godot(
    model="winner/model.gltf",
    textures=["winner/diffuse.png", "winner/normal.png"],
    options={
        "model_format": "gltf",             # Keep GLTF (preferred)
        "texture_format": "webp",           # Convert PNG → WebP (Godot 4)
        "webp_quality": 90,
        "pack_textures": True,              # Pack into GLB
        "lod_method": "multimesh",          # Use MultiMesh for LODs
        "generate_tres_material": True      # Create .tres material
    }
)
# Outputs:
# - godot/model.glb (or .gltf with separate textures)
# - godot/textures/diffuse.webp
# - godot/textures/normal.webp
# - godot/materials/material.tres
```

#### Web/Three.js Export
```python
web_export = converter.export_for_web(
    model="winner/model.gltf",
    textures=["winner/diffuse.png", "winner/normal.png"],
    options={
        "model_format": "glb",              # Binary GLTF
        "use_draco": True,                  # Draco compression
        "texture_format": "jpg",            # Lossy for diffuse
        "jpg_quality": 90,
        "max_texture_size": 1024,           # Web optimization
        "generate_multiple_sizes": True,    # Responsive sizes
        "sizes": [1024, 512, 256],
        "optimize_for_streaming": True
    }
)
# Outputs:
# - web/model.glb (Draco compressed)
# - web/model_draco.glb
# - web/textures/diffuse_1024.jpg
# - web/textures/diffuse_512.jpg
# - web/textures/diffuse_256.jpg
# - web/materials/material.json (Three.js format)
```

---

## Complete Workflow Example

### Procedural Character Generation Pipeline

```python
from vaultmind_forge.forge_converter import InputConverter, OutputConverter
from vaultmind_forge.forge_diffusion import DiffusionGenerator
from vaultmind_forge.forge_semantic import SemanticDownscaler
from vaultmind_forge.forge_sr import SuperResolutionUpscaler
from vaultmind_forge.forge_validator import AssetValidator
from vaultmind_forge.forge_lineage import LineageTracker

# ===== PHASE 1: INPUT CONVERSION =====
print("Phase 1: Converting input assets...")

input_converter = InputConverter(output_dir="procedural/input")

# Convert artist's FBX model to standardized GLTF
input_result = input_converter.prepare_for_generation(
    source_path="source/artist_character.fbx",
    options={
        "extract_textures": True,
        "normalize_scale": True,
        "center_geometry": True,
        "generate_uvs": True,
        "validation_level": "strict"
    }
)

print(f"✓ Input converted: {input_result.gltf_path}")
print(f"✓ Textures extracted: {len(input_result.textures)} files")

# ===== PHASE 2: PROCEDURAL GENERATION =====
print("\nPhase 2: Procedural generation...")

# Initialize lineage tracking
lineage = LineageTracker()
lineage_id = lineage.start_generation_job(
    source=input_result.gltf_path,
    type="character_variation"
)

# Step 1: Generate texture variations with AI
diffusion_gen = DiffusionGenerator()

texture_variations = diffusion_gen.generate_texture_variations(
    reference_texture=input_result.textures["diffuse"],
    style="fantasy_armor",
    count=5,
    metadata={"lineage_id": lineage_id}
)

# Step 2: Validate generated textures
validator = AssetValidator()
validated_textures = []

for texture in texture_variations:
    validation = validator.validate(texture.path)
    if validation.passed:
        validated_textures.append(texture)

print(f"✓ Generated {len(texture_variations)} variations")
print(f"✓ Validated: {len(validated_textures)} passed")

# Step 3: Select best variation
winner = max(validated_textures, key=lambda t: t.validation_score)
print(f"✓ Winner selected: score {winner.validation_score}")

# Step 4: Generate LOD levels with semantic downscaler
downscaler = SemanticDownscaler()

lod_textures = downscaler.generate_lod_pyramid(
    source_texture=winner.path,
    levels=[2048, 1024, 512, 256],
    preserve_features=True
)

print(f"✓ Generated {len(lod_textures)} LOD levels")

# Step 5: Enhance with super resolution (optional)
upscaler = SuperResolutionUpscaler()

enhanced_texture = upscaler.upscale(
    source=winner.path,
    target_size=4096,
    method="tile_based"
)

print(f"✓ Enhanced texture to 4096x4096")

# ===== PHASE 3: OUTPUT CONVERSION =====
print("\nPhase 3: Converting to engine formats...")

output_converter = OutputConverter(output_base="procedural/output")

# Export for multiple platforms
export_results = output_converter.export_multi_platform(
    model_path=input_result.gltf_path,
    texture_path=winner.path,
    lod_textures=lod_textures,
    targets={
        "unity": {
            "profile": "balanced",
            "generate_lods": True,
            "texture_compression": "BC7",
            "create_prefab": True
        },
        "unreal": {
            "profile": "quality",
            "pack_orm": True,
            "nanite_enabled": True,
            "lod_count": 4
        },
        "web": {
            "profile": "optimized",
            "use_draco": True,
            "max_texture_size": 1024
        }
    }
)

# Record in lineage
for engine, result in export_results.items():
    lineage.record_export(
        lineage_id=lineage_id,
        engine=engine,
        export_result=result
    )

print(f"✓ Exported to {len(export_results)} platforms")

# ===== PHASE 4: PACKAGING =====
print("\nPhase 4: Creating distribution packages...")

from vaultmind_forge.forge_packaging import AssetPackager

packager = AssetPackager()

for engine, result in export_results.items():
    package_path = packager.package_for_engine(
        assets=result.output_files,
        engine=engine,
        metadata={
            "lineage_id": lineage_id,
            "generation_date": "2025-11-04",
            "asset_type": "procedural_character",
            "lod_levels": len(lod_textures)
        },
        output=f"dist/{engine}_character_pack.zip"
    )

    print(f"✓ Packaged for {engine}: {package_path}")

# Complete lineage
lineage.complete_generation_job(lineage_id, export_results)

print("\n✅ Complete pipeline finished!")
print(f"📊 Lineage ID: {lineage_id}")
print(f"📦 Packages created: {len(export_results)}")
```

---

## Integration with Existing Modules

### forge_diffusion Integration
```python
# After generating textures/images with diffusion
diffusion_result = forge_diffusion.generate(...)

# Convert generated assets to engine formats
converter.export_diffusion_result(
    diffusion_result=diffusion_result,
    target_engines=["unity", "unreal", "web"]
)
```

### forge_semantic Integration
```python
# Generate LODs with semantic downscaler
lod_pyramid = forge_semantic.generate_lods(texture, levels=[2048, 1024, 512])

# Export LODs with proper naming for each engine
converter.export_lod_set(
    lod_pyramid=lod_pyramid,
    target_engine="unity",
    lod_naming_convention="unity"  # texture_LOD0, texture_LOD1, etc.
)
```

### forge_validator Integration
```python
# Validate before conversion
validation = forge_validator.validate(asset)

if validation.passed:
    # Only convert validated assets
    converter.export_for_engine(asset, target_engine="unity")
else:
    print(f"Asset failed validation: {validation.errors}")
```

---

## Next Implementation Steps

1. ✅ Design bidirectional conversion pipeline
2. ⬜ Implement InputConverter class
3. ⬜ Implement OutputConverter class
4. ⬜ Add format-specific converters (FBX, GLTF, etc.)
5. ⬜ Integrate with forge_diffusion
6. ⬜ Integrate with forge_semantic
7. ⬜ Integrate with forge_sr
8. ⬜ Add engine-specific optimizations
9. ⬜ Create CLI commands
10. ⬜ Add REST API endpoints

---

**End of Procedural Asset Pipeline Documentation**
