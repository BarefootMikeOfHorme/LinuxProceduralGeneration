# Input Assets (Normalized for Generation)

## Purpose
Standardized formats ready for procedural generation.
All assets converted to GLTF + PNG + JSON metadata.

## Standard Formats
- **Models:** GLTF (.gltf or .glb)
- **Textures:** PNG (power-of-2, sRGB/Linear)
- **Materials:** JSON (PBR properties)
- **Metadata:** JSON (asset info)

## Directory Structure
```
models/             # GLTF models (normalized)
textures/           # PNG textures (standardized)
materials/          # JSON material definitions
metadata/           # Asset metadata
```

## Normalization Rules
1. **Coordinate System:** Right-handed, Y-up
2. **Scale:** 1 unit = 1 meter
3. **Origin:** Centered at (0,0,0)
4. **UVs:** 0-1 range, no overlaps
5. **Textures:** Power-of-2, max 2048x2048 for input

## Usage
1. Assets auto-converted from `assets/source/`
2. Ready for forge_diffusion, forge_semantic, forge_sr
3. Metadata includes generation hints

## Example Metadata
```json
{
  "asset_id": "uuid",
  "source_file": "source/models/character.fbx",
  "normalized_at": "2025-11-04T12:00:00Z",
  "geometry": {
    "vertices": 10000,
    "triangles": 18000,
    "has_uvs": true
  },
  "procedural_hints": {
    "suitable_for_variation": true,
    "lod_candidate": true
  }
}
```
