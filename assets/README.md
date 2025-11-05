# VaultMind Forge - Assets Directory Structure

## Purpose
Organized asset storage for the complete procedural generation pipeline.

## Structure Philosophy

**By Generation Type:** diffusion, semantic, sr, video
**By Endpoint:** unity, unreal, godot, web, blender
**By Stage:** source → input → generated → validated → output

---

## Directory Layout

```
assets/
├── source/              # Original artist assets (READ-ONLY)
├── input/               # Normalized for generation (GLTF + PNG standard)
├── generated/           # AI-generated variations (by type)
├── validated/           # Passed quality checks
├── output/              # Engine-ready exports
├── reference/           # Reference materials for generation
├── temp/                # Temporary working files
└── archive/             # Historical versions
```

See subdirectory READMEs for details.
