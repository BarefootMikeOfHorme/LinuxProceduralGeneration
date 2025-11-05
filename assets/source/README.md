# Source Assets (READ-ONLY)

## Purpose
Original artist-created assets in their native formats.
**DO NOT MODIFY** - these are the source of truth.

## Supported Formats

### Models
- **FBX** - Industry standard, animation support
- **OBJ** - Simple geometry, universally supported
- **BLEND** - Blender native files
- **DAE** - Collada format
- **STL** - CAD/3D printing models

### Textures
- **PSD** - Photoshop layered files (source)
- **TGA** - Targa format
- **PNG** - Lossless compressed
- **TIFF** - High quality uncompressed

### Directory Structure
```
models/
├── characters/     # Character models (humanoid, creatures)
├── environments/   # Terrain, buildings, landscapes
├── props/          # Objects, items, furniture
└── vehicles/       # Cars, ships, aircraft

textures/
├── diffuse/        # Base color/albedo maps
├── normal/         # Normal maps
├── roughness/      # Surface roughness
├── metallic/       # Metallic maps
└── ambient_occlusion/  # AO maps

materials/          # Material definitions (MTL, etc.)
animations/         # Animation files (FBX, BVH)
audio/
├── music/          # Background music
└── sfx/            # Sound effects
```

## Usage
1. Import artist assets here
2. Run `forge_converter` to normalize → `assets/input/`
3. Never modify originals - always work on copies
