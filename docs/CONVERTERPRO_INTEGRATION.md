# ConverterPro Integration

## Overview

ConverterPro has been successfully integrated into VaultMind Forge as a set of processing nodes in the web UI.

## Location

**ConverterPro Path**: `C:\Users\Administrator\Desktop\ConverterProv1`

## What is ConverterPro?

ConverterPro (AssetConverterPro AD v1.0.0) is an advanced digital asset conversion and management system with:

- **Asset Scanning**: Scan and catalog assets across file systems
- **Format Conversion**: Convert assets between different formats and game engines
- **Export System**: Package and export assets to various formats
- **Web Crawling**: Ethical web scraping for legacy content
- **Archive Processing**: Handle compressed files and document archives

### Key Components

1. **INDEX.py** - Local file system monitoring
2. **ARCHIVE.py** - Archive handler for compressed files
3. **SCOUT.py** - Asset crawler with systematic organization
4. **SPIDER.py** - Core scanning engine
5. **SCRAPE.py** - Ethical web crawler

## Integration

### New Nodes Added

ConverterPro has been integrated as **3 new processing nodes** in the VaultMind Forge web UI:

#### 1. ConverterPro Scan Node
**Type**: `converterProScan`
**Category**: Processing
**Purpose**: Scan and catalog assets using ConverterPro

**Inputs**:
- `path` (text, required) - Path to scan for assets
- `recursive` (boolean, optional, default: true) - Scan recursively
- `database` (text, optional, default: "assets.db") - Database file for catalog

**Outputs**:
- `database` (text) - Path to asset database
- `summary` (dict) - Scan summary

#### 2. ConverterPro Convert Node
**Type**: `converterProConvert`
**Category**: Processing
**Purpose**: Convert assets between formats/engines

**Inputs**:
- `source` (text, required) - Source asset or directory
- `engine` (text, optional, default: "generic") - Target engine (unity, unreal, godot, generic)
- `format` (text, optional) - Target format (auto-detect if not specified)
- `recursive` (boolean, optional, default: false) - Process directories recursively

**Outputs**:
- `output_path` (text) - Path to converted assets
- `metadata` (dict) - Conversion metadata

#### 3. ConverterPro Export Node
**Type**: `converterProExport`
**Category**: Processing
**Purpose**: Export assets to specific formats

**Inputs**:
- `source` (text, required) - Source asset directory
- `format` (text, optional, default: "vaf") - Export format (vaf, zip, etc.)

**Outputs**:
- `output_path` (text) - Path to exported package
- `metadata` (dict) - Export metadata

## Implementation Files

### Created Files

1. **`backend/executors/converter_pro_nodes.py`** - New executor nodes for ConverterPro
   - ConverterProScanExecutor
   - ConverterProConvertExecutor
   - ConverterProExportExecutor

### Modified Files

2. **`backend/core/registry.py`** - Updated to register ConverterPro nodes
   - Added import and registration of ConverterPro executors
   - Graceful error handling if ConverterPro is unavailable

## How It Works

The integration uses subprocess calls to execute ConverterPro's CLI:

```python
# Example: Scan assets
subprocess.run([
    sys.executable,
    "C:/Users/Administrator/Desktop/ConverterProv1/cli.py",
    "scan",
    scan_path,
    "--database", database,
    "--recursive"
], ...)
```

This allows VaultMind Forge to leverage ConverterPro's capabilities through the web UI.

## Usage in Web UI

Once the backend restarts, you'll see 3 new nodes in the Processing category:

1. **ConverterPro Scan** - Drag from node palette to scan assets
2. **ConverterPro Convert** - Drag to convert between formats/engines
3. **ConverterPro Export** - Drag to export/package assets

### Example Workflow

```
[Text Input: "D:/Assets/Models"]
    ↓
[ConverterPro Scan]
    ↓ (database)
[ConverterPro Convert: engine=unity]
    ↓ (output_path)
[ConverterPro Export: format=vaf]
    ↓ (output_path)
[Save/Archive]
```

## Testing

To test the integration:

1. Open web UI: http://localhost:3000
2. Create a new workflow
3. Add a "Text Input" node with a path to scan
4. Add a "ConverterPro Scan" node
5. Connect them and execute (F5)
6. Check backend logs for ConverterPro output

## Error Handling

The integration includes:
- Try/catch blocks for missing ConverterPro
- Subprocess error handling
- Detailed logging of ConverterPro output
- Graceful degradation if ConverterPro is unavailable

## Benefits

✅ **Unified Interface**: Access ConverterPro through VaultMind Forge web UI
✅ **Workflow Integration**: Combine with other forge_* modules
✅ **Node-Based**: Visual programming interface for conversions
✅ **Error Handling**: Robust error reporting and logging
✅ **Flexible**: Supports all ConverterPro CLI features

## Future Enhancements

Potential improvements:
- [ ] Real-time progress tracking
- [ ] Async execution with progress bars
- [ ] Direct Python imports (instead of subprocess)
- [ ] Web UI for ConverterPro settings
- [ ] Batch processing support
- [ ] Integration with forge_lineage for tracking

## Documentation

For more details on ConverterPro:
- Main README: `C:\Users\Administrator\Desktop\ConverterProv1\docs\source_readmes\README.md`
- CLI help: `python C:\Users\Administrator\Desktop\ConverterProv1\cli.py --help`

---

**Status**: ✅ **INTEGRATED** (2025-12-04)

**Integration Points**:
- Backend executors: `backend/executors/converter_pro_nodes.py`
- Registry: `backend/core/registry.py`
- Web UI: Automatic (via node registry)
