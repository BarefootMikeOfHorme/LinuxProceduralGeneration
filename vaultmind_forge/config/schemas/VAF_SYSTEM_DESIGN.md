# VaultMind Asset Format (VAF) System Design

## Overview

The VAF system uses **multiple specialized formats** to handle different stages and purposes of asset management. This multi-tier approach ensures efficiency, flexibility, and comprehensive data preservation.

---

## Format Tiers

### 1. **VAF-Catalog** (.vaf.catalog.json)
**Purpose**: Lightweight metadata and indexing
**Size**: ~2-10 KB per asset
**Use Case**: Fast searching, browsing, catalog generation

**Contains**:
- Asset ID, name, category, tags
- Basic statistics (polycount, texture count)
- Preview thumbnail reference
- File locations and references
- Minimal metadata for discovery

**Does NOT contain**:
- Actual geometry data
- Full texture data
- Material definitions

---

### 2. **VAF-Full** (.vaf.full.json + binary buffers)
**Purpose**: Complete asset representation with all data
**Size**: 100 KB - 100 MB per asset
**Use Case**: Archival, conversion, editing

**Contains**:
- Complete geometry (vertices, indices, normals, UVs)
- Full material definitions
- Texture references and metadata
- Rigging and skeleton data
- Animations
- Complete lineage and provenance

**Format Structure**:
```
asset_name/
  ├── asset.vaf.full.json     # Main descriptor
  ├── buffers/
  │   ├── geometry_0.bin      # Binary geometry data
  │   ├── geometry_1.bin
  │   └── animations.bin
  ├── textures/
  │   ├── base_color.png
  │   ├── normal.png
  │   └── roughness.png
  └── metadata/
      └── lineage.json
```

---

### 3. **VAF-Merge** (.vaf.merge.json)
**Purpose**: Combining multiple assets into unified collections
**Size**: Variable
**Use Case**: Scene composition, asset libraries, level building

**Contains**:
- References to multiple VAF-Full assets
- Merge instructions (transforms, overrides)
- Conflict resolution rules
- Shared resources optimization
- Combined bounding volumes

**Example**: Merging "character + clothing + weapons" into single scene-ready asset

---

### 4. **VAF-Binary** (.vafb)
**Purpose**: High-performance binary format
**Size**: Optimized (30-50% smaller than JSON equivalent)
**Use Case**: Runtime loading, game engine integration

**Contains**:
- Same data as VAF-Full
- Packed binary format
- Memory-mapped compatible
- Fast deserializat ion

**Features**:
- Platform-independent binary encoding
- Built-in compression
- Chunk-based streaming support

---

### 5. **VAF-Streaming** (.vaf.stream/)
**Purpose**: Progressive loading for large assets
**Size**: Split into chunks
**Use Case**: Web delivery, on-demand loading

**Structure**:
```
asset.vaf.stream/
  ├── manifest.json           # Asset manifest
  ├── lod0/                   # Highest detail
  │   ├── geometry.bin
  │   └── textures_4k/
  ├── lod1/                   # Medium detail
  ├── lod2/                   # Low detail
  └── preview/                # Ultra-low preview
      └── thumbnail.jpg
```

---

### 6. **VAF-Diff** (.vaf.diff.json)
**Purpose**: Asset versioning and incremental updates
**Size**: Minimal (only changes)
**Use Case**: Version control, iterative editing

**Contains**:
- Parent asset reference (hash)
- Delta/diff operations
- Changed properties only
- Transformation history

---

## Format Selection Guide

| **Task** | **Recommended Format** | **Why** |
|----------|------------------------|---------|
| Cataloging 1000s of assets | VAF-Catalog | Lightweight, fast to parse |
| Archiving source assets | VAF-Full | Complete data preservation |
| Combining character parts | VAF-Merge | Smart merging with conflict resolution |
| Game engine integration | VAF-Binary | Fast loading, optimized size |
| Web 3D viewer | VAF-Streaming | Progressive loading, LOD support |
| Tracking edits over time | VAF-Diff | Version control, minimal storage |

---

## Conversion Flow

### From Raw Downloads → VAF

```
Raw Asset (.fbx, .obj, .zip, etc.)
    ↓
[Intake & Extract]
    ↓
[Parse & Validate]
    ↓
[Normalize to VAF-Full]  ← Universal intermediate
    ↓
[Generate Derivatives]
    ├── VAF-Catalog (for indexing)
    ├── VAF-Binary (for runtime)
    └── VAF-Streaming (for web)
```

### VAF-Full as Universal Pivot

**VAF-Full** is the canonical format. All other formats derive from it:

```
        VAF-Full
           ↓
    ┌──────┼──────┐
    ↓      ↓      ↓
Catalog Binary Streaming
```

---

## Merging Strategy

### Asset Merging Rules

When combining multiple assets (e.g., character + outfit + weapon):

#### 1. **Mesh Merging**
- Combine vertex buffers
- Reindex indices
- Preserve UV channels
- Merge bounding boxes

#### 2. **Material Merging**
- Deduplicate identical materials
- Merge texture atlases where beneficial
- Preserve material slots and assignments

#### 3. **Rigging Merging**
- Unify skeleton hierarchies
- Resolve bone name conflicts
- Merge skin weights
- Combine animation clips

#### 4. **Conflict Resolution**
```json
{
  "merge_policy": {
    "material_conflicts": "prefer_source_a",
    "bone_conflicts": "rename_with_prefix",
    "texture_conflicts": "create_atlas",
    "animation_conflicts": "combine_tracks"
  }
}
```

---

## Schema Inheritance

All VAF formats share a common base:

```
VAF-Base (common fields)
  ├── VAF-Catalog (extends: minimal)
  ├── VAF-Full (extends: complete)
  ├── VAF-Merge (extends: full + merge rules)
  ├── VAF-Binary (extends: full + binary encoding)
  ├── VAF-Streaming (extends: full + chunks)
  └── VAF-Diff (extends: base + delta ops)
```

---

## Inter-Format Conversion Matrix

| From / To | Catalog | Full | Merge | Binary | Stream | Diff |
|-----------|---------|------|-------|--------|--------|------|
| **Catalog** | — | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Full** | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| **Merge** | ✅ | ✅ | — | ✅ | ✅ | ✅ |
| **Binary** | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| **Stream** | ✅ | ✅ | ❌ | ✅ | — | ✅ |
| **Diff** | ❌ | ✅* | ❌ | ❌ | ❌ | — |

*\*Requires applying diff to parent first*

---

## Storage Strategy

### Asset Library Organization

```
assets/
  ├── catalog/
  │   └── index.vaf.catalog.json    # Master catalog (all assets)
  ├── vaf_full/
  │   ├── characters/
  │   │   └── robot_001/
  │   │       ├── asset.vaf.full.json
  │   │       └── buffers/
  │   └── vehicles/
  ├── vaf_binary/                    # Compiled for engines
  ├── vaf_streaming/                 # Web-ready chunks
  └── lineage/                       # Version history (diffs)
```

### Deduplication Strategy

- **Content-Addressed Storage**: Same texture used by 100 models? Store once, reference everywhere
- **Shared Buffer Pool**: Common geometry chunks (cubes, spheres) stored once
- **Texture Atlases**: Combine small textures intelligently

---

## Example: Complete Intake Flow

### Input: `robot_character.zip`
**Contains**:
- `robot.fbx` (geometry + rigging)
- `textures/` (10 PNG files)
- `animations/` (5 FBX animation clips)

### Processing Steps:

1. **Extract archive** → temp directory
2. **Parse FBX** → intermediate data structures
3. **Generate VAF-Full**:
   ```json
   {
     "vaf_version": "1.0.0",
     "asset": {
       "id": "a3f2b1...",
       "name": "Robot Character",
       "type": "model_3d",
       "category": "characters"
     },
     "geometry": {
       "meshes": [...],
       "statistics": {
         "total_vertices": 15234,
         "total_triangles": 28991
       }
     },
     "materials": {...},
     "rigging": {...},
     "animations": [...]
   }
   ```

4. **Generate derivatives**:
   - **VAF-Catalog** (lightweight reference)
   - **VAF-Binary** (engine-ready)
   - **Thumbnail** (preview image)

5. **Update master catalog**
6. **Log lineage**

---

## Merge Example: Character Customization

### Input Assets:
- `base_character.vaf.full.json` (body)
- `outfit_scifi.vaf.full.json` (clothing)
- `weapon_rifle.vaf.full.json` (weapon)

### Merge Operation:
```json
{
  "vaf_version": "1.0.0",
  "merge_type": "composite",
  "sources": [
    {
      "asset_id": "base_character_hash",
      "role": "primary",
      "transform": { "position": [0,0,0], "rotation": [0,0,0,1], "scale": [1,1,1] }
    },
    {
      "asset_id": "outfit_scifi_hash",
      "role": "attachment",
      "attach_to": "primary",
      "merge_materials": true
    },
    {
      "asset_id": "weapon_rifle_hash",
      "role": "attachment",
      "attach_to": "primary.bones.hand_r",
      "transform": { "position": [0.1, 0, 0] }
    }
  ],
  "merge_rules": {
    "material_policy": "combine",
    "texture_atlas": {
      "enabled": true,
      "max_size": [2048, 2048]
    },
    "skeleton": {
      "merge_animations": true,
      "bone_prefix_conflicts": true
    }
  },
  "output": {
    "asset": { /* merged asset data */ }
  }
}
```

**Result**: Single VAF-Full with combined geometry, unified skeleton, merged materials

---

## Extension Points

### Custom VAF Extensions

Each VAF format supports extensions:

```json
{
  "vaf_version": "1.0.0",
  "extensions": {
    "VAF_physics": {
      "colliders": [...],
      "rigid_bodies": [...]
    },
    "VAF_lod": {
      "levels": [...]
    },
    "VAF_custom_game_data": {
      // Custom fields
    }
  }
}
```

---

## Performance Targets

| Format | Parse Time (avg) | Memory Overhead | Disk Size (relative) |
|--------|------------------|-----------------|----------------------|
| VAF-Catalog | <1ms | 5 KB | 1× (baseline) |
| VAF-Full | 10-100ms | 1-10 MB | 100× |
| VAF-Binary | 5-20ms | 0.5-5 MB | 50× (compressed) |
| VAF-Streaming (LOD0) | 50-200ms | Progressive | 150× (uncompressed) |

---

## Summary

The VAF system provides:

✅ **Flexibility**: Multiple formats for different needs
✅ **Efficiency**: Lightweight catalogs, optimized binaries
✅ **Completeness**: Full-fidelity archival format
✅ **Mergeability**: Smart asset composition
✅ **Interoperability**: Easy conversion between formats
✅ **Scalability**: Handles 1 asset or 100,000 assets

**Core Philosophy**: One canonical format (VAF-Full), many specialized derivatives
