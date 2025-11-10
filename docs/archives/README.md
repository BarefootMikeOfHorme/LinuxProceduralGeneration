# VaultMind Forge Archives

This directory contains archived historical code and documentation from the VaultMind Forge repository.

**Archive Date:** November 9, 2025
**Consolidation Report:** [MERGE_REPORT.md](../../MERGE_REPORT.md)
**Complete Details:** [CONSOLIDATION_COMPLETE.md](../../CONSOLIDATION_COMPLETE.md)

---

## Directory Structure

```
archives/
├── code_snapshots/           # Historical code implementations
│   ├── nested_package_snapshot_20251109.zip
│   ├── nested_package_snapshot_20251109_manifest.json
│   ├── deprecated_executor_prototype.zip
│   └── deprecated_executor_prototype_manifest.json
└── milestones/               # Development milestone reports
    ├── milestone_reports_20251109.zip
    └── milestone_reports_20251109_manifest.json
```

---

## Archive Contents

### Code Snapshots

#### nested_package_snapshot_20251109.zip
- **Size:** 3,032 bytes (0 files - empty after first archive, re-archived second run)
- **Original Path:** `vaultmind_forge/vaultmind_forge/`
- **Description:** Historical snapshot of vaultmind_forge package from before major development (Oct 28 - Nov 3, 2024)
- **Why Archived:**
  - Obsolete code snapshot missing 5 critical modules:
    - `forge_bots` (bot framework)
    - `forge_intake` (asset intake system)
    - `forge_procedural` (procedural generation)
    - `forge_converter` (format conversion)
    - `forge_batch` (batch processing)
  - Contains outdated implementations of remaining modules
  - Native libraries outdated (37KB vs current 2MB)
- **Manifest:** `nested_package_snapshot_20251109_manifest.json`

#### deprecated_executor_prototype.zip
- **Size:** 2,413 bytes (1 file)
- **Original Path:** `vaultmind_forge/executor.py`
- **Description:** Original DAG executor prototype (simple async implementation, 162 lines)
- **Why Archived:**
  - Superseded by `forge_executor` package
  - Zero active imports in codebase
  - Simpler implementation vs enhanced package version
- **Canonical Replacement:** `vaultmind_forge/forge_executor/executor.py`
- **Manifest:** `deprecated_executor_prototype_manifest.json`

### Milestone Documentation

#### milestone_reports_20251109.zip
- **Size:** 33,616 bytes (6 files)
- **Original Paths:**
  - `vaultmind_forge/BOT_FRAMEWORK_COMPLETE.md`
  - `vaultmind_forge/PHASE_1_AND_4_COMPLETE.md`
  - `vaultmind_forge/QUICK_WIN_TRIO_COMPLETE.md`
  - `vaultmind_forge/TASK_VERIFICATION_REPORT.md`
  - `vaultmind_forge/BEAST_MODE_ACTION_PLAN.md`
  - `vaultmind_forge/PLACEHOLDER_AUDIT.md`
- **Description:** Development milestone completion reports
- **Why Archived:**
  - Historical development documentation
  - Milestone-specific completion reports
  - Cleaner root directory structure
- **Manifest:** `milestone_reports_20251109_manifest.json`

---

## Archive Format

All archives follow this structure:

```
archive_name.zip
├── MANIFEST.json              # Embedded manifest (inside ZIP)
├── [original/path/file1]      # Original relative paths preserved
├── [original/path/file2]
└── ...

archive_name_manifest.json     # External manifest (alongside ZIP)
```

### Manifest Structure

Each manifest includes:
- **archive_name** - ZIP filename
- **created** - ISO8601 timestamp
- **description** - Human-readable description
- **reason** - Why archived
- **total_files** - File count
- **total_size** - Total bytes
- **files** - Array of:
  - `path` - Original relative path
  - `size` - File size in bytes
  - `hash` - SHA256 hash (first 16 chars)
  - `modified` - Last modified timestamp

---

## Accessing Archives

### Extract Entire Archive

```bash
cd C:\Users\Administrator\Desktop\Projects\LPG
unzip docs/archives/code_snapshots/nested_package_snapshot_20251109.zip -d ./
```

### List Contents

```bash
unzip -l docs/archives/code_snapshots/deprecated_executor_prototype.zip
```

### View Manifest

```bash
# External manifest
cat docs/archives/code_snapshots/deprecated_executor_prototype_manifest.json

# Or extract embedded manifest
unzip -p docs/archives/code_snapshots/deprecated_executor_prototype.zip MANIFEST.json
```

### Verify Hash

```bash
# Extract file and compare hash
unzip docs/archives/code_snapshots/deprecated_executor_prototype.zip
sha256sum vaultmind_forge/executor.py
# Compare against hash in manifest
```

---

## Rollback Procedure

To restore archived files to their original locations:

```bash
cd C:\Users\Administrator\Desktop\Projects\LPG

# Extract code snapshots
cd docs/archives/code_snapshots
unzip nested_package_snapshot_20251109.zip -d ../../../
unzip deprecated_executor_prototype.zip -d ../../../

# Extract milestone reports
cd ../milestones
unzip milestone_reports_20251109.zip -d ../../../

# Verify restoration
cd ../../../
ls -la vaultmind_forge/vaultmind_forge/    # Should exist
ls -la vaultmind_forge/executor.py         # Should exist
ls -la vaultmind_forge/*.md                 # Should include milestone reports
```

**Note:** No import changes were made during consolidation, so rollback requires no import path fixes.

---

## Archive Maintenance

### Adding New Archives

When archiving additional files:

1. Create ZIP with embedded MANIFEST.json
2. Create external manifest JSON alongside ZIP
3. Update this README with new archive details
4. Update [MERGE_REPORT.md](../../MERGE_REPORT.md) if significant
5. Follow naming convention: `descriptive_name_YYYYMMDD.zip`

### Archive Retention

- **Policy:** Indefinite retention for all code archives
- **Reason:** Historical reference, rollback capability, compliance
- **Review:** Annual review recommended (document in CHANGELOG.md)

---

## Compliance

### Licensing
- All archived code under MIT License
- See [LICENSE.md](../../LICENSE.md) for details
- No licensing conflicts

### Privacy
- No personal data in archives
- Source code and documentation only

### Security
- All files checksummed (SHA256)
- Manifests preserve verification hashes
- Archive integrity verifiable

---

## Questions?

- **Consolidation Details:** See [MERGE_REPORT.md](../../MERGE_REPORT.md)
- **Complete Summary:** See [CONSOLIDATION_COMPLETE.md](../../CONSOLIDATION_COMPLETE.md)
- **Repository Status:** See [DOCS_STATUS.md](../../DOCS_STATUS.md)
- **Navigation:** See [DOCS_QUICK_NAV.md](../../DOCS_QUICK_NAV.md)

---

**Last Updated:** 2025-11-09
**Archive Count:** 3 archives (2 code, 1 documentation)
**Total Archived Size:** ~39 KB compressed (~385 KB original)
