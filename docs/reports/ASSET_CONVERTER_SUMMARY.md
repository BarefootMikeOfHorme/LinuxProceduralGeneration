# VaultMind Forge - Asset Converter Summary

## Quick Overview

The **forge_converter** module provides complete bidirectional asset conversion for procedural generation workflows.

---

## Directory Structure Created

```
assets/
├── source/                 # Original artist assets (FBX, OBJ, PSD, etc.)
├── procedural/
│   ├── input/             # Normalized for generation (GLTF + PNG)
│   ├── generated/         # AI-generated variations
│   └── output/            # Engine-ready exports
└── engines/
    ├── unity/             # Unity-optimized (FBX + DDS BC7 + .mat + .prefab)
    ├── unreal/            # Unreal-optimized (FBX + TGA + .uasset + LODs)
    ├── godot/             # Godot-optimized (GLTF + WebP + .tres)
    └── web/               # Web-optimized (GLB + JPG + Draco)
```

---

## Three-Phase Pipeline

### Phase 1: INPUT CONVERSION
```
Artist Assets (FBX, OBJ, PSD)
    ↓
InputConverter
    ↓
Standardized Format (GLTF + PNG + JSON metadata)
```

**Purpose:** Normalize diverse input formats for procedural generation

**Key Operations:**
- Format conversion (FBX/OBJ → GLTF)
- Coordinate system normalization (right-handed, Y-up)
- Scale normalization (1 unit = 1 meter)
- UV generation/validation
- Texture extraction (PSD → PNG)
- Material extraction (→ JSON)

### Phase 2: PROCEDURAL GENERATION
```
Normalized Assets
    ↓
forge_diffusion (AI generation)
    ↓
forge_semantic (LOD generation)
    ↓
forge_sr (upscaling)
    ↓
forge_validator (quality check)
    ↓
Validated Procedural Assets
```

**Purpose:** Generate, modify, and validate procedural content

**Integration:**
- Use standardized GLTF + PNG as input
- Generate variations with AI
- Create multi-resolution LODs
- Enhance with super-resolution
- Validate before export

### Phase 3: OUTPUT CONVERSION
```
Validated Assets
    ↓
OutputConverter
    ↓
Engine-Specific Formats (Unity, Unreal, Godot, Web)
    ↓
forge_packaging
    ↓
Distribution Packages
```

**Purpose:** Convert procedural assets to optimized engine formats

**Engine-Specific Outputs:**

| Engine  | Model  | Textures    | Materials | Extras          |
|---------|--------|-------------|-----------|-----------------|
| Unity   | FBX    | BC7/BC5 DDS | .mat      | .prefab, LODs   |
| Unreal  | FBX    | TGA, ORM    | .uasset   | Nanite, LODs    |
| Godot   | GLTF   | WebP        | .tres     | MultiMesh LODs  |
| Web     | GLB    | JPG/PNG     | .json     | Draco, multiple sizes |

---

## API Examples

### Input Conversion
```python
from vaultmind_forge.forge_converter import InputConverter

converter = InputConverter(output_dir="procedural/input")

# Convert artist FBX to standardized GLTF
result = converter.prepare_for_generation(
    source_path="source/character.fbx",
    options={
        "extract_textures": True,
        "normalize_scale": True,
        "generate_uvs": True
    }
)
# → procedural/input/character.gltf
# → procedural/input/textures/*.png
# → procedural/input/metadata/character.json
```

### Output Conversion
```python
from vaultmind_forge.forge_converter import OutputConverter, TargetEngine

converter = OutputConverter(output_base="engines")

# Export for Unity
result = converter.export_for_unity(
    model="procedural/generated/winner.gltf",
    textures=["procedural/generated/diffuse.png"],
    options={
        "texture_compression": "BC7",
        "generate_lods": True,
        "create_prefab": True
    }
)
# → engines/unity/winner.fbx
# → engines/unity/textures/diffuse_BC7.dds
# → engines/unity/materials/material.mat
# → engines/unity/winner.prefab
```

### Multi-Platform Export
```python
# Export to all platforms at once
results = converter.export_multi_platform(
    asset_path="procedural/generated/winner.gltf",
    targets={
        "unity": {"profile": "balanced"},
        "unreal": {"profile": "quality", "nanite": True},
        "web": {"profile": "optimized", "draco": True}
    }
)
```

---

## Complete Workflow Example

```python
# 1. INPUT: Convert artist asset
input_conv = InputConverter()
input_result = input_conv.prepare_for_generation("source/hero.fbx")

# 2. GENERATE: Create variations with AI
diffusion = DiffusionGenerator()
variations = diffusion.generate_variations(
    reference=input_result.textures["diffuse"],
    count=5
)

# 3. VALIDATE: Check quality
validator = AssetValidator()
validated = [v for v in variations if validator.validate(v).passed]

# 4. SELECT: Pick best variation
winner = max(validated, key=lambda v: v.score)

# 5. LODs: Generate multi-resolution
semantic = SemanticDownscaler()
lods = semantic.generate_lod_pyramid(winner, levels=[2048, 1024, 512])

# 6. ENHANCE: Optional super-resolution
sr = SuperResolutionUpscaler()
enhanced = sr.upscale(winner, target_size=4096)

# 7. OUTPUT: Export to engines
output_conv = OutputConverter()
exports = output_conv.export_multi_platform(
    model_path=input_result.gltf_path,
    texture_path=enhanced,
    lod_textures=lods,
    targets=["unity", "unreal", "web"]
)

# 8. PACKAGE: Create distributions
packager = AssetPackager()
for engine, result in exports.items():
    packager.package_for_engine(
        assets=result.output_files,
        engine=engine,
        output=f"dist/{engine}_pack.zip"
    )
```

---

## Format Conversion Quick Reference

### Models

| From      | To Unity | To Unreal | To Godot  | To Web    |
|-----------|----------|-----------|-----------|-----------|
| **FBX**   | Direct   | Direct    | → GLTF    | → GLTF    |
| **OBJ**   | Direct   | Direct    | Direct    | → GLTF    |
| **GLTF**  | → FBX    | Direct    | Native    | Native    |
| **BLEND** | → FBX    | → FBX     | → GLTF    | → GLTF    |

### Textures

| From    | To Unity | To Unreal | To Godot  | To Web    |
|---------|----------|-----------|-----------|-----------|
| **PNG** | → BC7    | → TGA     | → WebP    | → JPG     |
| **PSD** | → BC7    | → TGA     | → WebP    | → JPG     |
| **TGA** | → BC7    | Direct    | → WebP    | → JPG     |

---

## Conversion Profiles

### QUALITY Profile
- **Purpose:** Hero assets, cinematics
- **Texture:** 4096x4096, minimal compression
- **LODs:** 5 levels, conservative decimation
- **Suitable for:** PC/Console high-end

### BALANCED Profile (Default)
- **Purpose:** Standard game assets
- **Texture:** 2048x2048, BC7/BC5 compression
- **LODs:** 3 levels, moderate decimation
- **Suitable for:** Most platforms

### OPTIMIZED Profile
- **Purpose:** Mobile, web, background assets
- **Texture:** 1024x1024, aggressive compression
- **LODs:** 4 levels, aggressive decimation, atlasing
- **Suitable for:** Mobile, web browsers

---

## Integration with Forge Modules

### forge_diffusion
```python
# Generate texture → Export to engines
texture = forge_diffusion.generate(...)
converter.export_diffusion_result(texture, targets=["unity", "web"])
```

### forge_semantic
```python
# Generate LODs → Export with proper naming
lods = forge_semantic.generate_lods(texture)
converter.export_lod_set(lods, target_engine="unity")
```

### forge_sr
```python
# Upscale → Export in multiple resolutions
enhanced = forge_sr.upscale(texture, size=4096)
converter.export_with_mip_levels(enhanced, sizes=[4096, 2048, 1024])
```

### forge_validator
```python
# Validate → Only export if passed
if forge_validator.validate(asset).passed:
    converter.export_for_engine(asset, target="unity")
```

### forge_lineage
```python
# Track entire conversion pipeline
lineage.record_conversion_pipeline(
    input_conversion=input_result,
    generation=generation_result,
    output_conversion=export_results
)
```

---

## Engine-Specific Optimizations

### Unity
- Texture compression: BC7 (diffuse), BC5 (normal), BC4 (single channel)
- LOD screen percentages: [0.6, 0.3, 0.15]
- Materials: Standard/URP/HDRP shaders
- Mesh optimization: < 65k vertices per mesh

### Unreal Engine
- Texture naming: T_AssetName_Type (T_Character_D, T_Character_N)
- ORM packing: Occlusion + Roughness + Metallic in single texture
- Nanite support for high-poly static meshes
- Virtual texturing for large textures

### Godot
- GLTF preferred format (or GLB for embedded textures)
- WebP textures (Godot 4.x)
- BPTC compression (desktop), ETC2 (mobile)
- MultiMesh for LODs

### Web/Three.js
- GLB with Draco compression
- Aggressive decimation (< 50k triangles)
- JPG for diffuse (quality 85-90)
- Multiple texture sizes for responsive loading
- Max 1024x1024 (mobile), 2048x2048 (desktop)

---

## File Size Expectations

| Asset Type          | Source  | Unity    | Unreal   | Web      |
|---------------------|---------|----------|----------|----------|
| Character Model     | 10 MB   | 5 MB     | 6 MB     | 2 MB     |
| 2048x2048 Texture   | 12 MB   | 2 MB     | 4 MB     | 500 KB   |
| Environment (large) | 100 MB  | 50 MB    | 60 MB    | 10 MB    |

**Compression ratios:**
- Unity: ~0.5 (BC7 compression)
- Unreal: ~0.6 (TGA with ORM packing)
- Web: ~0.2 (Draco + JPG compression)

---

## Next Steps

### Implementation Priority

**High Priority:**
1. Implement InputConverter class with FBX → GLTF conversion
2. Implement OutputConverter class with GLTF → Unity export
3. Add texture conversion (PNG → DDS BC7 for Unity)
4. Integrate with forge_diffusion pipeline

**Medium Priority:**
5. Add Unreal export (GLTF → FBX + TGA + ORM packing)
6. Add Web export (GLTF → GLB + Draco)
7. Implement LOD generation
8. Add material conversion

**Future:**
9. Godot export
10. Blender integration
11. Batch conversion
12. CLI commands
13. REST API endpoints

---

## Files Created

1. **FORGE_CONVERTER_DESIGN.md** - Complete design specification
2. **PROCEDURAL_ASSET_PIPELINE.md** - Bidirectional pipeline documentation
3. **ASSET_CONVERTER_SUMMARY.md** - This quick reference
4. **vaultmind_forge/forge_converter/__init__.py** - Module initialization
5. **vaultmind_forge/forge_converter/converter.py** - Main converter class

---

## Configuration Files Needed

Create these in `vaultmind_forge/forge_converter/configs/`:

1. **unity_config.json** - Unity import settings
2. **unreal_config.json** - Unreal import settings
3. **godot_config.json** - Godot import settings
4. **web_config.json** - Web optimization settings

---

**Status:** ✅ Design Complete - Ready for Implementation

**Estimated Implementation Time:**
- Input conversion (basic): 1-2 days
- Output conversion (Unity): 2-3 days
- Output conversion (Unreal, Web): 2-3 days
- Integration with forge modules: 1-2 days
- Testing & documentation: 2-3 days
- **Total:** ~10-15 days

---

**End of Summary**
