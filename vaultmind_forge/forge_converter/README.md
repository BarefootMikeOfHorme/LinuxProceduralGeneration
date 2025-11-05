# forge_converter - Asset Conversion Module

## Overview
Bidirectional asset conversion for VaultMind Forge procedural generation pipeline.

## Structure
```
forge_converter/
├── __init__.py              # Module entry point
├── converter.py             # Main converter API
├── formats/                 # Format handlers
│   ├── format_registry.py   # Format detection & registry (from DomainShell)
│   └── __init__.py
├── engines/                 # Engine exporters
│   ├── structure_builder.py # Engine directory structures (from Comprehensive_Ai_Filter)
│   └── __init__.py
└── optimization/            # Optimization tools
    └── __init__.py
```

## Adapted Code

### From DomainShell (Rust → Python)
- **format_registry.py** - Format handler registry system
  - Adapted to use VaultMind Forge asset paths
  - Integrated with lineage tracking (checksum computation)
  - Python-native implementation with type hints

### From Comprehensive_Ai_Filter (Python)
- **structure_builder.py** - Engine directory structure generator
  - Adapted for VaultMind Forge output organization
  - Creates engine-specific folders (Unity, Unreal, Godot, Web, Blender)
  - Generates README files with conventions

## Integration with Asset Structure

Works with the assets/ directory:
```
assets/
├── source/      # Original assets → Input conversion
├── input/       # Normalized assets → Procedural generation
├── generated/   # AI-generated assets → Validation
├── validated/   # Quality-checked assets → Output conversion
└── output/      # Engine-ready assets
    ├── unity/
    ├── unreal/
    ├── godot/
    ├── web/
    └── blender/
```

## Usage Example

```python
from vaultmind_forge.forge_converter import AssetConverter
from vaultmind_forge.forge_converter.formats import FormatRegistry, AssetPaths
from vaultmind_forge.forge_converter.engines import EngineStructureBuilder

# Set up paths
paths = AssetPaths()
paths.ensure_all_exist()

# Create format registry
registry = FormatRegistry(asset_paths=paths)

# Create engine structures
builder = EngineStructureBuilder()
unity_path = builder.create_unity_structure("MyGame")

print(f"Unity assets: {unity_path}")
```

## Status
- ✅ Asset structure created and documented
- ✅ Format registry adapted from DomainShell
- ✅ Structure builder adapted from Comprehensive_Ai_Filter
- 🟡 Format handlers (to be implemented)
- 🟡 Engine-specific converters (to be implemented)
- 🟡 Optimization tools (to be implemented)

## Next Steps
1. Implement specific format handlers (FBX, GLTF, PNG, etc.)
2. Create engine-specific conversion logic
3. Add optimization tools (LOD, compression)
4. Integrate with forge_diffusion, forge_semantic, forge_sr
5. Add comprehensive tests
