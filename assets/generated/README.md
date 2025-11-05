# Generated Assets (By Type)

## Purpose
AI-generated and procedurally-created variations.
Organized by generation method.

## Directory Structure

### diffusion/ - AI Image Generation
```
diffusion/
├── textures/           # SDXL-generated texture maps
│   ├── {job_id}/
│   │   ├── variation_001.png
│   │   ├── variation_002.png
│   │   └── variation_003.png
│   └── metadata.json
├── images/             # Standalone images
└── variations/         # Multi-pass variations
```

**Storage Pattern:**
- Each generation job gets unique folder
- All variations stored together
- Winner selected via forge_validator
- Rejected variations tracked for analysis

### semantic/ - Downscaling & LODs
```
semantic/
├── lods/               # Level-of-detail pyramids
│   ├── {asset_id}/
│   │   ├── LOD0_2048.png  # Full detail
│   │   ├── LOD1_1024.png
│   │   ├── LOD2_512.png
│   │   └── LOD3_256.png
│   └── metadata.json
└── downscaled/         # General downscaling
```

**Storage Pattern:**
- One directory per source asset
- LOD levels named consistently
- Metadata tracks quality metrics

### sr/ - Super Resolution
```
sr/
├── upscaled/           # Standard upscaling
│   ├── {source}_2x.png
│   ├── {source}_4x.png
│   └── {source}_8x.png
└── enhanced/           # Tile-based enhancement
    └── {source}_tiled_8k.png
```

**Storage Pattern:**
- Suffix indicates scale factor
- Tiled results marked separately
- Original source reference in metadata

### video/ - Video Generation
```
video/
├── sequences/          # Frame sequences
│   ├── {sequence_id}/
│   │   ├── frame_0001.png
│   │   ├── frame_0002.png
│   │   └── ...
│   └── metadata.json
└── animations/         # Rendered videos
    └── {sequence_id}.mp4
```

**Storage Pattern:**
- Frame sequences kept separately
- Final renders in animations/
- Metadata includes FPS, duration

## Naming Convention
```
{generation_type}_{job_id}_{variation}_{timestamp}.{ext}

Examples:
diffusion_job123_var001_20251104120000.png
semantic_asset456_LOD2_512_20251104120000.png
sr_texture789_4x_20251104120000.png
```

## Metadata Template
```json
{
  "generation_type": "diffusion",
  "job_id": "job-123",
  "variation": "001",
  "timestamp": "2025-11-04T12:00:00Z",
  "source_asset": "input/textures/character_diffuse.png",
  "model": "SDXL-base-1.0",
  "prompt": "fantasy armor, detailed, 4k",
  "settings": {
    "steps": 30,
    "cfg_scale": 7.5,
    "seed": 42
  }
}
```
