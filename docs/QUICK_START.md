# VaultMind Forge - Quick Start Guide

## What You Have Now

A complete, automated asset processing system that:
- ✅ Monitors drop folders in real-time
- ✅ Detects and merges multiple format versions of the same asset
- ✅ Converts 40+ file formats to unified VAF standard
- ✅ Runs as a background daemon/service
- ✅ Handles file locking and graceful shutdowns
- ✅ Tracks complete lineage and metadata
- ✅ Ready to process your 603 downloaded files

---

## Three Ways to Use It

### 1. Process Existing Downloads (One-Time Batch)

Process all 603 files in your Downloads folder:

```bash
cd C:\Users\Administrator\Desktop\Projects\LPG
python -m vaultmind_forge.forge_intake.batch_ingest_v2
```

**What happens:**
- Scans Downloads folder
- Extracts all archives (ZIP, RAR)
- Groups multi-format assets (e.g., robot.fbx + robot.obj → 1 asset)
- Converts everything to VAF
- Saves to `assets/vaf_full/` and `assets/catalog/`

**Expected output:**
```
[+] Found 603 files
[+] Total files after extraction: ~1800+
[+] Found ~300 unique assets
[+] Multi-version merges: ~150
[+] Successfully processed: ~300 assets
```

---

### 2. Drop Folder (Real-Time Monitoring)

Monitor a folder and auto-process any files dropped into it:

```bash
# Create drop folder
mkdir C:\AssetDropFolder

# Start monitoring (blocks terminal)
python -m vaultmind_forge.forge_intake.drop_folder_monitor ^
    "C:\AssetDropFolder" ^
    "C:\ProcessedAssets" ^
    --batch-size 10 ^
    --batch-timeout 30
```

**What happens:**
- Watches `C:\AssetDropFolder` for new files
- Waits 2 seconds for file stability (copying complete)
- Batches files (10 at a time or after 30 seconds)
- Auto-detects multi-version assets
- Processes and saves to `C:\ProcessedAssets`

**To test:**
- Drop `robot.fbx` into `C:\AssetDropFolder` → auto-processed
- Drop `robot.obj` 5 seconds later → merged with robot.fbx

---

### 3. Background Daemon (Persistent Service)

Run as a background service that survives reboots:

```bash
# Start daemon
python -m vaultmind_forge.forge_intake.forge_daemon start ^
    "C:\AssetDropFolder" ^
    "C:\ProcessedAssets"

# Check status
python -m vaultmind_forge.forge_intake.forge_daemon status

# Stop daemon
python -m vaultmind_forge.forge_intake.forge_daemon stop

# Restart daemon
python -m vaultmind_forge.forge_intake.forge_daemon restart ^
    "C:\AssetDropFolder" ^
    "C:\ProcessedAssets"
```

**What happens:**
- Runs in background (doesn't block terminal)
- Survives terminal closes
- Writes logs to `forge_daemon.log`
- Status updates every 60 seconds
- Graceful shutdown on Ctrl+C or SIGTERM

**Daemon files created:**
- `forge_daemon.pid` - Process ID
- `forge_daemon.log` - Log file
- `forge_daemon_status.json` - Current status

---

## Example Workflow

### Scenario: You have a character in 4 formats

**Input files:**
```
Downloads/
├── robot_character.fbx      (has rigging + animations)
├── robot_character.obj      (high-poly geometry)
├── robot_character.glb      (optimized materials)
└── robot_character.blend    (source file)
```

**Processing:**
```bash
python -m vaultmind_forge.forge_intake.batch_ingest_v2
```

**System output:**
```
[>>] robot_character (4 variants)
    Multi-version: 4 formats detected
      - .glb    (priority: 95)  ← Selected as primary
      - .fbx    (priority: 90)  ← Has rigging/animations
      - .obj    (priority: 70)  ← Has high-poly geo
      - .blend  (priority: 60)

    Merging strategy:
      ✓ Using materials from .glb (most complete PBR)
      ✓ Using rigging from .fbx (most bones)
      ✓ Using animations from .fbx (walking, running clips)
      ✓ Comparing geometry... using .obj (highest polycount)

    [+] Success! Asset created
```

**Output files:**
```
assets/
├── vaf_full/
│   └── a3f2b1c4....vaf.full.json      (complete asset data)
├── catalog/
│   └── a3f2b1c4....vaf.catalog.json   (lightweight index)
└── lineage/
    └── a3f2b1c4....json                (provenance tracking)
```

**VAF-Catalog contents:**
```json
{
  "asset_id": "a3f2b1c4...",
  "name": "Robot Character",
  "type": "model_3d",
  "category": "characters",
  "statistics": {
    "vertices": 25891,
    "triangles": 48723,
    "materials": 5,
    "textures": 12,
    "animations": 3,
    "bones": 68
  },
  "capabilities": {
    "has_geometry": true,
    "has_materials": true,
    "has_textures": true,
    "has_rigging": true,
    "has_animations": true
  },
  "formats": {
    "source": {
      "primary_format": ".glb",
      "merged_from": [".glb", ".fbx", ".obj", ".blend"]
    }
  }
}
```

---

## Processing Your 603 Files

**Recommended approach:**

### Step 1: Run batch ingestion

```bash
cd C:\Users\Administrator\Desktop\Projects\LPG
python -m vaultmind_forge.forge_intake.batch_ingest_v2
```

Expected duration: 5-15 minutes depending on file sizes

### Step 2: Check results

```bash
# Count processed assets
dir /s assets\catalog | find /c ".vaf.catalog.json"

# View summary
type assets\metadata\ingestion_summary.json
```

### Step 3: Start daemon for future drops

```bash
mkdir C:\FutureAssets
python -m vaultmind_forge.forge_intake.forge_daemon start ^
    "C:\FutureAssets" ^
    "C:\ProcessedAssets"
```

Now you can drop new assets into `C:\FutureAssets` anytime and they'll auto-process!

---

## Troubleshooting

### "watchdog not found"
```bash
pip install watchdog
```

### "rarfile not found"
```bash
pip install rarfile
```

### Daemon won't start
```bash
# Check for existing instance
python -m vaultmind_forge.forge_intake.forge_daemon status

# Force stop if needed
python -m vaultmind_forge.forge_intake.forge_daemon stop

# Try again
python -m vaultmind_forge.forge_intake.forge_daemon start ...
```

### Files not processing
- Check file formats are supported (see `VAULTMIND_FORGE_PIPELINE.md`)
- Verify file stability timeout (default 2 seconds)
- Check daemon logs: `type forge_daemon.log`

---

## What's Next?

From AssetConverterPro, we can integrate:

1. **Web scraper** (ethical asset acquisition from public sources)
2. **Texture optimizer** (power-of-two conversion, compression)
3. **Duplicate detector** (hash-based deduplication)
4. **EXIF extractor** (image metadata)
5. **Game engine detection** (auto-detect Unity/Unreal projects)
6. **Docker containerization** (scalable processing)

---

## The Web Scraper (Worth Publishing!)

The AssetConverterPro web scraper is **production-ready** with:
- ✅ **Ethical boundaries** (90-day grace period for commercial content)
- ✅ **Docker containerized** (easy deployment)
- ✅ **Rate limiting** (0.5-0.8 req/sec - polite scraping)
- ✅ **Scalable** (`docker-compose up --scale scraper=5`)
- ✅ **Auto-cleanup** (session data removal)

**Location:** `D:\AssetConverterProVERSIONS\AssetConverterPro_AD_v1.0.0\docker\`

This could be published as a standalone open-source tool!

---

## Summary

You now have a complete asset pipeline that:

1. **Automatically watches** folders for new assets
2. **Intelligently merges** multiple format versions
3. **Converts** 40+ formats to unified VAF standard
4. **Runs persistently** as a background daemon
5. **Tracks lineage** for complete provenance
6. **Handles locking** for safe concurrent access
7. **Ready to scale** with existing Docker infrastructure

**Just run it and drop your files!**
