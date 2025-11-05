# VaultMind Forge - Asset Converter Module Design

## Overview

The **forge_converter** module provides comprehensive asset conversion capabilities for multi-engine workflows, enabling seamless translation between different game engines and 3D formats while preserving quality and metadata.

---

## Module Architecture

### Core Components

```
vaultmind_forge/
└── forge_converter/
    ├── __init__.py                 # Module initialization
    ├── converter.py                # Main converter class
    ├── engines/                    # Engine-specific handlers
    │   ├── __init__.py
    │   ├── unity.py               # Unity asset conversion
    │   ├── unreal.py              # Unreal Engine conversion
    │   ├── godot.py               # Godot Engine conversion
    │   ├── blender.py             # Blender format handling
    │   └── web.py                 # Web formats (GLTF, GLB)
    ├── formats/                    # Format converters
    │   ├── __init__.py
    │   ├── model_formats.py       # 3D model conversions
    │   ├── texture_formats.py     # Texture conversions
    │   ├── animation_formats.py   # Animation conversions
    │   └── material_formats.py    # Material/shader conversions
    ├── optimization/               # Engine-specific optimizations
    │   ├── __init__.py
    │   ├── texture_optimizer.py   # Compression & atlasing
    │   ├── mesh_optimizer.py      # LOD generation, decimation
    │   └── material_optimizer.py  # Shader optimization
    └── README.md
```

---

## Engine-Specific Asset Storage Structure

### Recommended Directory Layout

```
assets/
├── source/                        # Original source assets (universal formats)
│   ├── models/
│   │   ├── characters/
│   │   │   ├── torso.fbx         # FBX source (universal)
│   │   │   └── torso.blend       # Blender source
│   │   ├── environments/
│   │   └── props/
│   ├── textures/
│   │   ├── characters/
│   │   │   ├── diffuse/          # PSD, TIFF, PNG (high-res)
│   │   │   ├── normal/
│   │   │   ├── roughness/
│   │   │   └── metallic/
│   │   └── environments/
│   ├── animations/
│   │   └── characters/
│   │       ├── walk.fbx
│   │       └── idle.fbx
│   └── audio/
│       ├── music/
│       └── sfx/
│
├── engines/                       # Engine-specific optimized assets
│   ├── unity/
│   │   ├── models/
│   │   │   └── characters/
│   │   │       ├── torso.fbx     # Unity-optimized FBX
│   │   │       └── torso.prefab  # Unity prefab
│   │   ├── textures/
│   │   │   └── characters/
│   │   │       ├── diffuse_BC7.dds    # Unity BC7 compressed
│   │   │       ├── normal_BC5.dds     # Unity BC5 compressed
│   │   │       └── metallic_BC4.dds   # Packed metallic/roughness
│   │   ├── materials/
│   │   │   └── character.mat     # Unity material
│   │   └── animations/
│   │       └── character.anim    # Unity animation clips
│   │
│   ├── unreal/
│   │   ├── models/
│   │   │   └── characters/
│   │   │       ├── torso.fbx     # Unreal-optimized FBX
│   │   │       └── torso_LODs/   # LOD meshes
│   │   │           ├── LOD0.fbx
│   │   │           ├── LOD1.fbx
│   │   │           └── LOD2.fbx
│   │   ├── textures/
│   │   │   └── characters/
│   │   │       ├── T_Character_D.tga      # Diffuse (Unreal naming)
│   │   │       ├── T_Character_N.tga      # Normal
│   │   │       ├── T_Character_ORM.tga    # Packed Occlusion/Roughness/Metallic
│   │   │       └── compressed/
│   │   │           ├── T_Character_D.uasset  # UE compressed textures
│   │   │           └── T_Character_N.uasset
│   │   ├── materials/
│   │   │   └── M_Character.uasset         # Unreal material
│   │   └── animations/
│   │       └── character_walk.uasset      # Unreal anim sequence
│   │
│   ├── godot/
│   │   ├── models/
│   │   │   └── characters/
│   │   │       ├── torso.gltf    # GLTF preferred for Godot
│   │   │       └── torso.dae     # Alternative: Collada
│   │   ├── textures/
│   │   │   └── characters/
│   │   │       ├── diffuse.webp  # Godot 4.x WebP support
│   │   │       ├── normal.webp
│   │   │       └── orm.webp      # Packed textures
│   │   ├── materials/
│   │   │   └── character.tres    # Godot material resource
│   │   └── animations/
│   │       └── walk.res          # Godot animation resource
│   │
│   ├── blender/
│   │   ├── scenes/
│   │   │   └── character_rig.blend
│   │   ├── assets/
│   │   │   ├── models/           # Linked library assets
│   │   │   ├── textures/
│   │   │   └── materials/
│   │   └── exports/              # Export staging
│   │
│   └── web/                       # Web/three.js optimized
│       ├── models/
│       │   └── characters/
│       │       ├── torso.glb     # Binary GLTF (optimized)
│       │       └── torso_draco.glb # Draco compressed
│       ├── textures/
│       │   └── characters/
│       │       ├── diffuse_1024.jpg    # Web-optimized sizes
│       │       ├── diffuse_512.jpg     # Multiple resolutions
│       │       └── diffuse_256.jpg
│       └── materials/
│           └── character.json    # Three.js material JSON
│
├── intermediate/                  # Conversion intermediates
│   ├── fbx_export/
│   ├── gltf_export/
│   └── temp/
│
└── metadata/                      # Asset metadata database
    ├── manifest.json              # Master asset manifest
    ├── conversion_logs/           # Conversion history
    └── engine_configs/            # Per-engine configuration
        ├── unity_config.json
        ├── unreal_config.json
        └── godot_config.json
```

---

## Format Conversion Matrix

### 3D Models

| Source Format | Unity        | Unreal       | Godot        | Blender      | Web          |
|---------------|--------------|--------------|--------------|--------------|--------------|
| **FBX**       | ✅ Direct    | ✅ Direct    | ⚠️ via GLTF  | ✅ Direct    | ⚠️ via GLTF  |
| **OBJ**       | ✅ Direct    | ✅ Direct    | ✅ Direct    | ✅ Direct    | ⚠️ via GLTF  |
| **GLTF/GLB**  | ⚠️ Plugin    | ✅ Direct    | ✅ Preferred | ✅ Direct    | ✅ Native    |
| **BLEND**     | ⚠️ via FBX   | ⚠️ via FBX   | ⚠️ via GLTF  | ✅ Native    | ⚠️ via GLTF  |
| **DAE**       | ✅ Direct    | ⚠️ Legacy    | ✅ Direct    | ✅ Direct    | ⚠️ via GLTF  |
| **STL**       | ✅ Direct    | ✅ Direct    | ✅ Direct    | ✅ Direct    | ⚠️ via GLTF  |
| **3DS**       | ⚠️ Legacy    | ⚠️ Legacy    | ⚠️ via OBJ   | ✅ Direct    | ❌ No        |

**Legend:**
- ✅ Direct: Native support, no conversion needed
- ⚠️ via: Requires intermediate conversion
- ❌ No: Not recommended/supported

### Texture Formats

| Source Format | Unity (DDS)  | Unreal (TGA) | Godot (WebP) | Blender      | Web (JPG/PNG) |
|---------------|--------------|--------------|--------------|--------------|---------------|
| **PNG**       | ✅ → BC7     | ✅ → TGA     | ✅ → WebP    | ✅ Native    | ✅ Optimize   |
| **TGA**       | ✅ → BC7     | ✅ Native    | ✅ → WebP    | ✅ Direct    | ✅ → JPG/PNG  |
| **TIFF**      | ✅ → BC7     | ✅ → TGA     | ✅ → WebP    | ✅ Native    | ✅ → JPG/PNG  |
| **PSD**       | ⚠️ Flatten   | ⚠️ Flatten   | ⚠️ Flatten   | ✅ Native    | ⚠️ Flatten    |
| **EXR**       | ✅ HDR       | ✅ Native    | ✅ Direct    | ✅ Native    | ⚠️ → RGBE    |
| **DDS**       | ✅ Native    | ✅ Direct    | ⚠️ → WebP    | ✅ Direct    | ❌ Convert    |
| **WebP**      | ⚠️ → BC7     | ⚠️ → TGA     | ✅ Native    | ✅ Direct    | ✅ Native     |

### Recommended Compression Per Engine

**Unity:**
- Diffuse/Albedo: BC7 (high quality) or BC1 (memory constrained)
- Normal Maps: BC5 (2-channel)
- Metallic/Roughness: BC4 (single channel) or packed BC7
- UI/Sprites: ASTC (mobile), BC7 (desktop)

**Unreal:**
- Diffuse/Albedo: BC7 or DXT5 (legacy)
- Normal Maps: BC5
- ORM (Occlusion/Roughness/Metallic): Packed BC7
- HDR: BC6H

**Godot:**
- General: WebP (Godot 4.x), PNG (Godot 3.x)
- Normal Maps: BPTC (desktop), ETC2 (mobile)
- HDR: RGBE or EXR

**Web/Three.js:**
- Diffuse: JPG (lossy, smaller) or PNG (transparency)
- Compressed: Basis Universal (.basis) for all platforms
- Max size: 1024x1024 (2048x2048 for hero assets)

---

## Converter Module API

### Python API

```python
from vaultmind_forge.forge_converter import AssetConverter, ConversionProfile

# Initialize converter
converter = AssetConverter(
    source_dir="assets/source",
    output_base="assets/engines"
)

# Convert asset for specific engine
result = converter.convert(
    asset_path="source/models/characters/torso.fbx",
    target_engine="unity",
    profile=ConversionProfile.OPTIMIZED,  # OPTIMIZED, BALANCED, QUALITY
    options={
        "generate_lods": True,
        "lod_levels": 3,
        "texture_compression": "BC7",
        "max_texture_size": 2048,
        "preserve_materials": True
    }
)

# Batch conversion for multiple engines
results = converter.batch_convert(
    asset_path="source/models/characters/torso.fbx",
    target_engines=["unity", "unreal", "godot", "web"],
    profile=ConversionProfile.BALANCED
)

# Convert entire directory tree
converter.convert_project(
    source_dir="assets/source",
    target_engines=["unity", "unreal"],
    parallel=True,
    workers=4
)
```

### Node.js API (via Python Bridge)

```javascript
import { AssetConverter } from './forge/converter.js';

const converter = new AssetConverter({
    mode: 'python-bridge',
    sourceDir: 'assets/source',
    outputBase: 'assets/engines'
});

// Convert single asset
const result = await converter.convert({
    assetPath: 'source/models/characters/torso.fbx',
    targetEngine: 'unity',
    profile: 'optimized',
    options: {
        generateLods: true,
        lodLevels: 3,
        textureCompression: 'BC7'
    }
});

// Batch convert
const results = await converter.batchConvert({
    assetPath: 'source/models/characters/torso.fbx',
    targetEngines: ['unity', 'unreal', 'godot'],
    profile: 'balanced'
});

// Monitor conversion progress
converter.on('progress', (event) => {
    console.log(`Converting: ${event.file} - ${event.progress}%`);
});

converter.on('complete', (result) => {
    console.log(`Completed: ${result.outputPath}`);
});
```

---

## Conversion Profiles

### QUALITY
- Maximum fidelity preservation
- Minimal compression
- Full material/texture preservation
- Suitable for: Hero assets, cinematics, showcases

**Settings:**
```yaml
textures:
  compression: minimal
  max_size: 4096
  format: lossless
models:
  lod_levels: 5
  decimation: conservative
  preserve_all_attributes: true
```

### BALANCED (Default)
- Good quality with reasonable file sizes
- Standard compression
- Suitable for: Most game assets

**Settings:**
```yaml
textures:
  compression: BC7/BC5
  max_size: 2048
  format: compressed
models:
  lod_levels: 3
  decimation: moderate
  preserve_uvs_normals_materials: true
```

### OPTIMIZED
- Maximum performance/file size optimization
- Aggressive compression
- Suitable for: Mobile, background assets, large-scale environments

**Settings:**
```yaml
textures:
  compression: BC1/ETC2
  max_size: 1024
  format: highly_compressed
  atlas: true
models:
  lod_levels: 4
  decimation: aggressive
  merge_materials: true
```

---

## Engine-Specific Optimization Rules

### Unity Optimizations

1. **Textures:**
   - Convert to BC7/BC5 for desktop
   - Convert to ASTC for mobile
   - Generate mipmaps
   - Texture atlasing for UI/sprites

2. **Models:**
   - Optimize meshes (< 65k vertices per mesh)
   - Generate LOD groups
   - Merge static meshes where possible
   - Enable read/write only when needed

3. **Materials:**
   - Use Standard/URP/HDRP shaders
   - Pack metallic/smoothness into single texture
   - Minimize shader keywords

### Unreal Optimizations

1. **Textures:**
   - Follow T_ naming convention
   - Pack ORM (Occlusion/Roughness/Metallic)
   - Use BC7 for diffuse, BC5 for normals
   - Virtual texturing for large textures

2. **Models:**
   - Generate LODs (4-5 levels typical)
   - Optimize lightmap UVs
   - Enable nanite for high-poly static meshes
   - Collision mesh generation

3. **Materials:**
   - Use material instances over unique materials
   - Parameter-driven materials
   - Master material approach

### Godot Optimizations

1. **Textures:**
   - WebP for Godot 4.x
   - Mipmaps for 3D, no mipmaps for 2D
   - BPTC compression for desktop
   - ETC2 for mobile

2. **Models:**
   - GLTF preferred format
   - Embed textures in GLB
   - LOD via MultiMesh or GLTF LOD extension

3. **Materials:**
   - Use StandardMaterial3D
   - Pack textures (ORM workflow)
   - Shader caching

### Web (Three.js) Optimizations

1. **Textures:**
   - JPG for diffuse (quality 85-90)
   - PNG only for transparency
   - Basis Universal for multi-platform
   - Max 1024x1024 (mobile), 2048x2048 (desktop)

2. **Models:**
   - GLB with Draco compression
   - Aggressive decimation (< 50k triangles)
   - Single draw call per object

3. **Materials:**
   - PBR materials only
   - Minimize unique materials
   - Texture atlasing

---

## Metadata & Lineage Integration

### Asset Conversion Record

```json
{
  "conversion_id": "uuid",
  "timestamp": "2025-11-04T12:00:00Z",
  "source_asset": {
    "path": "source/models/characters/torso.fbx",
    "format": "FBX",
    "size": 1048576,
    "checksum": "sha256_hash"
  },
  "conversions": [
    {
      "target_engine": "unity",
      "profile": "balanced",
      "output_path": "engines/unity/models/characters/torso.fbx",
      "output_size": 524288,
      "compression_ratio": 0.5,
      "processing_time_ms": 2500,
      "optimizations_applied": [
        "lod_generation",
        "texture_compression_BC7",
        "material_optimization"
      ],
      "lod_meshes": [
        { "level": 0, "vertices": 10000, "triangles": 18000 },
        { "level": 1, "vertices": 5000, "triangles": 9000 },
        { "level": 2, "vertices": 2500, "triangles": 4500 }
      ],
      "textures": [
        {
          "type": "diffuse",
          "source": "source/textures/characters/diffuse.tga",
          "output": "engines/unity/textures/characters/diffuse_BC7.dds",
          "compression": "BC7",
          "original_size": [2048, 2048],
          "output_size": [2048, 2048],
          "file_size_reduction": 0.75
        }
      ]
    },
    {
      "target_engine": "unreal",
      "profile": "balanced",
      "output_path": "engines/unreal/models/characters/torso.fbx",
      "... similar metadata ..."
    }
  ],
  "lineage": {
    "lineage_id": "source_asset_lineage_id",
    "parent": "original_creation_lineage_id",
    "operation": "multi_engine_conversion",
    "metadata": {
      "purpose": "multi_platform_deployment",
      "target_platforms": ["PC", "Console", "Mobile", "Web"]
    }
  }
}
```

---

## Implementation Phases

### Phase 1: Core Infrastructure ✅
- [x] Asset storage structure design
- [x] Conversion matrix documentation
- [x] Engine-specific optimization rules

### Phase 2: Basic Converters
- [ ] Implement model format converters (FBX ↔ GLTF ↔ OBJ)
- [ ] Implement texture format converters (PNG → DDS/TGA/WebP)
- [ ] Basic Unity/Unreal/Godot support

### Phase 3: Optimization Pipeline
- [ ] LOD generation
- [ ] Texture compression
- [ ] Material optimization
- [ ] Mesh decimation

### Phase 4: Advanced Features
- [ ] Texture atlasing
- [ ] Batch conversion
- [ ] Progress monitoring
- [ ] Error recovery

### Phase 5: Integration
- [ ] forge_lineage integration
- [ ] forge_validator integration
- [ ] forge_packaging for engine-specific packages
- [ ] REST API endpoints

---

## Example Workflows

### Workflow 1: Multi-Platform Game Asset

```python
from vaultmind_forge.forge_converter import AssetConverter
from vaultmind_forge.forge_validator import AssetValidator
from vaultmind_forge.forge_lineage import LineageTracker

# Initialize
converter = AssetConverter()
validator = AssetValidator()
lineage = LineageTracker()

# Create lineage for conversion job
lineage_id = lineage.start_conversion_job(
    source="source/models/characters/hero.fbx",
    targets=["unity", "unreal", "web"]
)

# Convert for each platform
platforms = {
    "unity": {"profile": "balanced", "target": "PC/Console"},
    "unreal": {"profile": "quality", "target": "PC/Console"},
    "web": {"profile": "optimized", "target": "Browser"}
}

results = {}
for engine, config in platforms.items():
    # Convert
    result = converter.convert(
        asset_path="source/models/characters/hero.fbx",
        target_engine=engine,
        profile=config["profile"]
    )

    # Validate
    validation = validator.validate(result.output_path)

    # Track in lineage
    lineage.record_conversion(
        lineage_id=lineage_id,
        engine=engine,
        result=result,
        validation=validation
    )

    results[engine] = result

# Package for each platform
for engine, result in results.items():
    packager.package_for_engine(
        assets=[result.output_path],
        engine=engine,
        output=f"packages/{engine}_character_pack.zip"
    )

lineage.complete_conversion_job(lineage_id, results)
```

### Workflow 2: Automated Texture Pipeline

```python
from vaultmind_forge.forge_converter import TextureConverter

converter = TextureConverter()

# Process character texture set
texture_set = {
    "diffuse": "source/textures/hero_diffuse.tga",
    "normal": "source/textures/hero_normal.tga",
    "roughness": "source/textures/hero_roughness.tga",
    "metallic": "source/textures/hero_metallic.tga"
}

# Convert for Unity (BC compression)
unity_textures = converter.convert_texture_set(
    textures=texture_set,
    target_engine="unity",
    options={
        "diffuse_compression": "BC7",
        "normal_compression": "BC5",
        "pack_metallic_roughness": True,  # Pack into single texture
        "generate_mipmaps": True
    }
)

# Convert for Web (JPG/PNG optimization)
web_textures = converter.convert_texture_set(
    textures=texture_set,
    target_engine="web",
    options={
        "diffuse_format": "jpg",
        "diffuse_quality": 90,
        "normal_format": "png",
        "max_size": 1024,
        "generate_multiple_sizes": [1024, 512, 256]  # For responsive loading
    }
)
```

---

## External Tool Integration

### Blender Python API
```python
# For automated exports from Blender
import bpy
from vaultmind_forge.forge_converter.engines.blender import BlenderExporter

exporter = BlenderExporter()

# Export to multiple formats
exporter.export_scene(
    blend_file="source/scenes/character_rig.blend",
    formats=["fbx", "gltf", "obj"],
    output_dir="intermediate/blender_export/"
)
```

### Unity Asset Processor
```csharp
// Unity editor script for automated import settings
using UnityEditor;
using VaultmindForge.Unity;

public class AutoAssetProcessor : AssetPostprocessor
{
    void OnPreprocessModel()
    {
        ModelImporter importer = (ModelImporter)assetImporter;

        // Apply Vaultmind Forge import settings
        VaultmindForgeSettings.ApplyModelImportSettings(importer);
    }

    void OnPreprocessTexture()
    {
        TextureImporter importer = (TextureImporter)assetImporter;

        // Apply compression settings
        VaultmindForgeSettings.ApplyTextureImportSettings(importer);
    }
}
```

---

## Performance Benchmarks (Target)

| Operation              | Asset Size | Processing Time | Memory Usage |
|------------------------|------------|-----------------|--------------|
| FBX → GLTF             | 10 MB      | < 5 sec         | < 500 MB     |
| Texture BC7 Compress   | 2048x2048  | < 2 sec         | < 200 MB     |
| LOD Generation (3)     | 50k verts  | < 10 sec        | < 1 GB       |
| Batch Convert (10)     | 100 MB     | < 60 sec        | < 2 GB       |

---

## Configuration Example

**unity_config.json:**
```json
{
  "engine": "unity",
  "version": "2022.3 LTS",
  "textures": {
    "default_compression": "BC7",
    "normal_compression": "BC5",
    "mobile_compression": "ASTC",
    "max_size": 2048,
    "generate_mipmaps": true,
    "streaming_mipmaps": false
  },
  "models": {
    "import_format": "fbx",
    "optimize_mesh": true,
    "read_write_enabled": false,
    "generate_colliders": false,
    "mesh_compression": "medium",
    "lod_settings": {
      "generate_lods": true,
      "lod_count": 3,
      "lod_screen_percentages": [0.6, 0.3, 0.15]
    }
  },
  "materials": {
    "default_shader": "Standard",
    "extract_materials": true,
    "material_location": "materials/"
  },
  "animations": {
    "import_animations": true,
    "bake_animations": false,
    "optimize_game_objects": true
  }
}
```

---

## Next Steps

1. ✅ Design complete - Ready for implementation
2. ⬜ Implement core converter classes
3. ⬜ Add format-specific converters
4. ⬜ Integrate with existing forge modules
5. ⬜ Create REST API endpoints
6. ⬜ Add CLI commands
7. ⬜ Build comprehensive test suite
8. ⬜ Documentation and examples

---

**End of Design Document**
