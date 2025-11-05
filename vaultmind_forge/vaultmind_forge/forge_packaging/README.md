# forge_packaging

Production-grade asset packaging with compression, metadata, and integrity verification for VaultMind Forge.

## Features

- **ZIP Compression**: Configurable compression levels (0-9)
- **SHA-256 Checksums**: Automatic integrity verification
- **Metadata Embedding**: Include job info, lineage data, etc.
- **Manifest Generation**: Detailed asset listings with checksums
- **Extract & Verify**: Unpack with optional integrity checks
- **Error Handling**: Comprehensive exception handling

## Quick Start

### Basic Packaging

```python
from vaultmind_forge.forge_packaging import AssetPackager
from pathlib import Path

# Initialize packager
packager = AssetPackager(compression_level=6)

# Package assets
assets = [
    Path("output/image1.png"),
    Path("output/image2.png"),
]

info = packager.package_assets(
    assets=assets,
    output_path=Path("output/assets.zip"),
    metadata={"job_id": "job-123"}
)

print(f"Packaged {info.asset_count} assets")
print(f"Compression: {info.compression_ratio*100:.1f}%")
```

### Quick Package Utility

```python
from vaultmind_forge.forge_packaging import quick_package

package_path = quick_package(
    assets=[Path("img1.png"), Path("img2.png")],
    output_dir=Path("output"),
    package_name="my_assets.zip"
)
```

## License

Part of VaultMind Forge - See main LICENSE file.
