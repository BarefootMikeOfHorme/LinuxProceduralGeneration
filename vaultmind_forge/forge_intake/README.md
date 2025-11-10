# forge_intake

**Automated asset intake, detection, and unified format conversion system.**

---

## Overview

The `forge_intake` module provides a complete pipeline for ingesting assets from various sources, detecting multi-version variants, and converting them into the standardized VAF (VaultMind Asset Format). It handles everything from initial file detection through final unified asset creation.

**Key Capabilities:**
- Real-time drop folder monitoring with auto-processing
- Multi-version asset detection and intelligent merging
- Support for 40+ file formats across 3D models, textures, and archives
- Background daemon service for persistent processing
- Batch processing of hundreds/thousands of assets
- Complete lineage tracking and provenance

---

## Features

### 1. Multi-Version Asset Detection
- Automatically groups different format versions of the same asset
- Example: `robot.fbx` + `robot.obj` + `robot.glb` → Single unified asset
- Intelligent name normalization (removes prefixes, version numbers, format suffixes)
- Priority-based format selection (glTF > FBX > USD > OBJ, etc.)

### 2. Intelligent Data Merging
- **Geometry**: Selects highest polycount (within reason)
- **Materials**: Uses most complete PBR data
- **Rigging**: Prefers most detailed skeleton
- **Animations**: Combines all unique animation clips
- **Textures**: Merges textures from all sources, deduplicated

### 3. Format Support

**3D Models:**
- glTF 2.0 (`.gltf`, `.glb`) - Priority 100/95
- FBX (`.fbx`) - Priority 90
- USD (`.usd`, `.usda`, `.usdc`, `.usdz`) - Priority 80-85
- COLLADA (`.dae`) - Priority 75
- Wavefront OBJ (`.obj`, `.mtl`) - Priority 70
- Blender (`.blend`) - Priority 60
- And 10+ more formats

**Textures:**
- PNG, JPG, TGA, BMP, TIFF, EXR, HDR, DDS, PSD

**Archives:**
- ZIP, RAR, 7Z, TAR, GZ, Unity packages

### 4. Real-Time Processing
- Watchdog-based file system monitoring
- File stability checking (waits for copy completion)
- Configurable batch processing (size and timeout)
- Multi-threaded processing for performance

### 5. Background Daemon
- Persistent service that survives reboots
- PID file management
- Graceful shutdown (SIGTERM/SIGINT handling)
- Status reporting (JSON file)
- Log file management

---

## Installation

```bash
pip install vaultmind-forge[intake]

# Or install specific dependencies
pip install watchdog rarfile pillow
```

---

## Quick Start

### Batch Process Existing Files

```python
from vaultmind_forge.forge_intake.batch_ingest_v2 import AssetIngestorV2

# Create ingestor
ingestor = AssetIngestorV2(
    downloads_dir="C:/Downloads",
    project_root="C:/Projects/MyAssets"
)

# Process all files
summary = ingestor.batch_process()

print(f"Processed {summary['processed']} assets")
print(f"Multi-version merges: {summary['multi_version_merges']}")
```

### Real-Time Drop Folder Monitoring

```python
from vaultmind_forge.forge_intake.drop_folder_monitor import DropFolderMonitor

# Create monitor
monitor = DropFolderMonitor(
    drop_folder="C:/AssetDropFolder",
    output_folder="C:/ProcessedAssets",
    auto_process=True,
    batch_size=10,
    batch_timeout=30.0
)

# Start monitoring (blocking)
monitor.run_interactive()
```

### Background Daemon Service

```bash
# Start daemon
python -m vaultmind_forge.forge_intake.forge_daemon start \
    "C:/AssetDropFolder" \
    "C:/ProcessedAssets"

# Check status
python -m vaultmind_forge.forge_intake.forge_daemon status

# Stop daemon
python -m vaultmind_forge.forge_intake.forge_daemon stop
```

---

## API Reference

### `AssetIngestorV2`

Main batch processing engine.

#### Constructor

```python
AssetIngestorV2(downloads_dir: str, project_root: str)
```

**Parameters:**
- `downloads_dir` - Directory containing files to process
- `project_root` - Project root directory (creates `assets/` subdirectory)

#### Methods

##### `batch_process(max_workers: int = 4) -> Dict`

Process all assets in downloads directory.

**Parameters:**
- `max_workers` - Number of parallel workers (default: 4)

**Returns:**
Dictionary containing:
- `total_input_files` - Number of files scanned
- `unique_assets` - Number of unique assets detected
- `processed` - Number successfully processed
- `multi_version_merges` - Number of multi-format merges
- `errors` - Number of failed assets

**Example:**
```python
ingestor = AssetIngestorV2("C:/Downloads", "C:/Projects")
summary = ingestor.batch_process(max_workers=8)

if summary['errors'] > 0:
    print(f"Errors occurred: {summary['error_details']}")
```

---

### `DropFolderMonitor`

Real-time file system monitoring with auto-processing.

#### Constructor

```python
DropFolderMonitor(
    drop_folder: str,
    output_folder: str,
    auto_process: bool = True,
    batch_size: int = 10,
    batch_timeout: float = 30.0
)
```

**Parameters:**
- `drop_folder` - Folder to monitor for new files
- `output_folder` - Destination for processed assets
- `auto_process` - Whether to automatically process detected files (default: True)
- `batch_size` - Process when this many files accumulated (default: 10)
- `batch_timeout` - Process after this many seconds even if batch incomplete (default: 30.0)

#### Methods

##### `start()`

Start monitoring (non-blocking).

##### `stop()`

Stop monitoring gracefully.

##### `run_interactive()`

Start monitoring in interactive mode (blocking). Press Ctrl+C to stop.

**Example:**
```python
monitor = DropFolderMonitor(
    "C:/DropFolder",
    "C:/Output",
    batch_size=5,
    batch_timeout=15.0
)

monitor.start()
# ... do other work ...
monitor.stop()
```

---

### `MultiVersionHandler`

Detects and merges multi-format asset variants.

#### Methods

##### `normalize_asset_name(filename: str) -> str`

Normalize filename to detect related variants.

**Examples:**
```python
handler = MultiVersionHandler()

handler.normalize_asset_name("10-robot_character.fbx")
# Returns: "robot_character"

handler.normalize_asset_name("uploads_files_123_robot-v2.obj")
# Returns: "robot"

handler.normalize_asset_name("rp_mei_posed_001_psd.zip")
# Returns: "rp_mei_posed_001"
```

##### `group_asset_variants(filepaths: List[Path]) -> Dict[str, List[AssetVariant]]`

Group files by normalized asset name.

**Returns:**
Dictionary mapping asset names to lists of variants.

**Example:**
```python
files = [
    Path("robot.fbx"),
    Path("robot.obj"),
    Path("robot.glb"),
    Path("spaceship.fbx")
]

groups = handler.group_asset_variants(files)
# Returns:
# {
#     "robot": [variant_fbx, variant_obj, variant_glb],
#     "spaceship": [variant_fbx]
# }
```

##### `merge_variants(variants: List[AssetVariant], asset_id: str) -> ConversionResult`

Merge multiple format variants into unified VAF.

**Returns:**
`ConversionResult` with:
- `status` - ConversionStatus enum (SUCCESS, PARTIAL, FAILED)
- `vaf_full` - Complete VAF-Full JSON
- `vaf_catalog` - VAF-Catalog JSON
- `warnings` - List of warning messages
- `errors` - List of error messages

---

### `UnifiedConverter`

Converts individual files to VAF format.

#### Methods

##### `convert(filepath: Path, asset_id: str) -> ConversionResult`

Convert single file to VAF.

**Example:**
```python
from vaultmind_forge.forge_intake.unified_converter import UnifiedConverter

converter = UnifiedConverter()
result = converter.convert(Path("model.fbx"), "a3f2b1c...")

if result.status == ConversionStatus.SUCCESS:
    print("VAF-Full:", result.vaf_full)
    print("VAF-Catalog:", result.vaf_catalog)
```

---

### `ForgeDaemon`

Background daemon service.

#### Constructor

```python
ForgeDaemon(
    drop_folder: str,
    output_folder: str,
    pid_file: Optional[str] = None,
    log_file: Optional[str] = None,
    status_file: Optional[str] = None
)
```

#### Methods

##### `start()`

Start daemon (blocking until stopped).

##### `stop()`

Stop daemon gracefully.

##### `get_status() -> dict`

Get current daemon status.

**Returns:**
Dictionary with daemon state, uptime, statistics.

---

## Configuration

### Format Priority

Customize format priorities in `format_registry.py`:

```python
FORMAT_REGISTRY = {
    ".gltf": FormatSpec(
        extension=".gltf",
        priority=100,  # Adjust priority here
        supports_geometry=True,
        # ...
    ),
    # ...
}
```

### Batch Processing

Tune batch processing performance:

```python
ingestor = AssetIngestorV2(downloads_dir, project_root)

# More workers = faster parallel processing
summary = ingestor.batch_process(max_workers=16)
```

### Drop Folder Tuning

```python
monitor = DropFolderMonitor(
    drop_folder="...",
    output_folder="...",
    batch_size=20,        # Larger batches = less overhead
    batch_timeout=60.0    # Longer timeout = fewer partial batches
)
```

---

## Examples

### Example 1: Process Downloads Folder

```python
from vaultmind_forge.forge_intake.batch_ingest_v2 import AssetIngestorV2

ingestor = AssetIngestorV2(
    downloads_dir="C:/Users/Me/Downloads",
    project_root="C:/Projects/GameAssets"
)

print("Starting batch ingestion...")
summary = ingestor.batch_process()

print(f"\n✓ Complete!")
print(f"  Input files: {summary['total_input_files']}")
print(f"  Unique assets: {summary['unique_assets']}")
print(f"  Multi-version merges: {summary['multi_version_merges']}")

# Check output
# C:/Projects/GameAssets/assets/vaf_full/*.vaf.full.json
# C:/Projects/GameAssets/assets/catalog/*.vaf.catalog.json
```

### Example 2: Monitor Folder with Custom Settings

```python
from vaultmind_forge.forge_intake.drop_folder_monitor import DropFolderMonitor
import signal
import sys

# Create monitor
monitor = DropFolderMonitor(
    drop_folder="C:/AssetInbox",
    output_folder="C:/ProcessedAssets",
    batch_size=5,
    batch_timeout=15.0
)

# Setup graceful shutdown
def signal_handler(sig, frame):
    print("\nShutting down...")
    monitor.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Start monitoring
print("Monitoring C:/AssetInbox")
print("Drop assets and they'll auto-process!")
print("Press Ctrl+C to stop\n")

monitor.run_interactive()
```

### Example 3: Daemon Service (Production)

```bash
# production_daemon.sh

# Start daemon
python -m vaultmind_forge.forge_intake.forge_daemon start \
    "/data/asset_inbox" \
    "/data/processed_assets" \
    --pid-file "/var/run/forge_daemon.pid" \
    --log-file "/var/log/forge_daemon.log"

# Monitor with cron (every 5 minutes)
*/5 * * * * python -m vaultmind_forge.forge_intake.forge_daemon status >> /var/log/forge_status.log
```

### Example 4: Multi-Version Merging

Input files:
```
Downloads/
├── robot_character.fbx     (has rigging + animations)
├── robot_character.obj     (has high-poly geometry)
├── robot_character.glb     (has optimized materials)
└── robot_character.blend   (source file)
```

Process:
```python
from vaultmind_forge.forge_intake.batch_ingest_v2 import AssetIngestorV2

ingestor = AssetIngestorV2("Downloads", "Projects")
summary = ingestor.batch_process()

# Output shows:
# [>>] robot_character (4 variants)
#     Multi-version: 4 formats detected
#       - .glb    (priority: 95)  ← Primary
#       - .fbx    (priority: 90)  ← Has animations
#       - .obj    (priority: 70)  ← High poly
#       - .blend  (priority: 60)
#
#     Merging...
#       ✓ Using materials from .glb
#       ✓ Using rigging from .fbx
#       ✓ Using animations from .fbx
#       ✓ Using geometry from .obj (highest polycount)
#
#     [+] Success! Asset created
```

Output:
```
Projects/assets/
├── vaf_full/a3f2b1c4....vaf.full.json       (merged data)
├── catalog/a3f2b1c4....vaf.catalog.json     (index)
└── lineage/a3f2b1c4....json                 (provenance)
```

---

## Architecture

### Pipeline Flow

```
Input Sources
    ↓
File Detection (drop folder / batch scan)
    ↓
Archive Extraction (ZIP, RAR, etc.)
    ↓
Asset Grouping (multi-version detection)
    ↓
Format Conversion (per variant)
    ↓
Intelligent Merging (best data from each)
    ↓
VAF Generation (Full + Catalog + Lineage)
    ↓
Output Storage
```

### Component Interaction

```
DropFolderMonitor
    │
    ├─> AssetDropHandler (watchdog events)
    │       └─> Stability Checker (background thread)
    │
    └─> Processing Queue
            │
            ├─> MultiVersionHandler
            │       ├─> Asset Normalization
            │       ├─> Variant Grouping
            │       └─> Merge Strategy
            │
            └─> UnifiedConverter
                    ├─> Format Detection
                    ├─> Parser Selection
                    └─> VAF Generation
```

### File Organization

```
assets/
├── input/              # Extracted source files
├── vaf_full/           # Complete VAF assets
│   └── {hash}.vaf.full.json
├── catalog/            # Lightweight indexes
│   └── {hash}.vaf.catalog.json
├── lineage/            # Provenance tracking
│   └── {hash}.json
└── metadata/           # Processing metadata
    └── ingestion_summary.json
```

---

## See Also

- [VAF System Design](../../vaultmind_forge/config/schemas/VAF_SYSTEM_DESIGN.md) - Complete VAF format specification
- [Format Registry](./format_registry.py) - All supported formats and priorities
- [Complete Pipeline](../../VAULTMIND_FORGE_PIPELINE.md) - End-to-end pipeline documentation
- [Quick Start Guide](../../QUICK_START.md) - Getting started with asset processing

---

## Performance Considerations

### Batch Processing
- Typical throughput: 50-200 assets/minute (depending on sizes and formats)
- Archive extraction adds 2-5 seconds per archive
- Multi-version merging adds 1-2 seconds per asset

### Drop Folder
- File stability delay: 2 seconds (configurable)
- Batch timeout prevents indefinite waiting
- Multi-threading handles concurrent operations

### Daemon Service
- Minimal resource usage when idle
- Status updates every 60 seconds
- Graceful shutdown preserves in-progress batches

---

## Troubleshooting

### "watchdog not installed"
```bash
pip install watchdog
```

### "rarfile not installed"
```bash
pip install rarfile
```

### Daemon won't start
```bash
# Check for existing instance
python -m vaultmind_forge.forge_intake.forge_daemon status

# Force stop
python -m vaultmind_forge.forge_intake.forge_daemon stop
```

### Files not processing
- Verify file formats are supported (see format_registry.py)
- Check file stability timeout (default 2 seconds)
- Review daemon logs: `type forge_daemon.log`
- Ensure proper permissions on directories

### Conversion failures
- Check source file integrity
- Verify format is actually supported
- Look for corruption in archives
- Review error details in summary JSON

---

## Version History

- **0.4.0** (2025-11-09) - Initial release
  - Multi-version asset detection
  - 40+ format support
  - Drop folder monitoring
  - Daemon service
  - VAF generation

---

## License

MIT License - See LICENSE.md for details.

## Contributing

See CONTRIBUTING.md for guidelines.
