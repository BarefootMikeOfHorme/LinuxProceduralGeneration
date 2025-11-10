# Root Directory Cleanup Plan

**Current State:** 51 files in root (WAY TOO MANY!)
**Target State:** ~10-15 essential files in root
**Files to Relocate:** 36+ files

---

## Proposed Structure

```
LPG/
├── README.md                          ← Keep (essential)
├── LICENSE.md                         ← Keep (essential)
├── CONTRIBUTING.md                    ← Keep (essential)
├── CHANGELOG.md                       ← Keep (essential)
├── QUICK_START.md                     ← Keep (primary getting started)
├── package.json                       ← Keep (if Node.js project)
├── pyproject.toml                     ← Create/keep (Python packaging)
├── requirements.txt                   ← Create/keep (Python deps)
├── .gitignore                         ← Keep
├── docs/
│   ├── api/                          ← NEW: API documentation
│   │   ├── NODE_API_README.md
│   │   ├── NODE_API_SUMMARY.md
│   │   └── QUICKSTART_NODE_API.md
│   ├── guides/                       ← NEW: User guides
│   │   ├── BUILD_NATIVE.md
│   │   ├── QUICK_NAV.md             (renamed from DOCS_QUICK_NAV.md)
│   │   ├── UTILS_GUIDE.md
│   │   ├── INTERACTIVE_TUTORIAL.md
│   │   └── FORGE_CONVERTER_INTEGRATION_GUIDE.md
│   ├── architecture/                 ← NEW: Design docs
│   │   ├── VAULTMIND_FORGE_PIPELINE.md
│   │   ├── PROCEDURAL_GENERATION_OVERVIEW.md
│   │   ├── PROCEDURAL_ASSET_PIPELINE.md
│   │   ├── FORGE_CONVERTER_DESIGN.md
│   │   ├── AI_CONTROL_FRAMEWORK.md
│   │   ├── PROJECT_CONTEXT_COMPACT.md
│   │   └── ASSET_REFERENCE_CATALOG.md
│   ├── components/                   ← NEW: Component docs
│   │   ├── LINEAGE_VIEWER_DOCS.md
│   │   └── LINEAGE_VIEWER_SUMMARY.md
│   ├── development/                  ← NEW: Dev documentation
│   │   ├── INDUSTRY_STANDARDS_ANALYSIS.md
│   │   ├── INTEGRATION_AUDIT.md
│   │   ├── NATIVE_HANDLER_EVALUATION.md
│   │   ├── PROCEDURAL_LIBRARY_ANALYSIS.md
│   │   ├── VALIDATOR_ENHANCEMENTS.md
│   │   ├── UTILS_AMENDMENTS.md
│   │   └── VAULTMIND_FORGE_CURSOR_PROMPT.md
│   ├── reports/                      ← NEW: Status reports
│   │   ├── STATE_OF_PROGRAM_REPORT.md
│   │   ├── DOCS_STATUS.md
│   │   ├── SESSION_SUMMARY.md
│   │   ├── FORGE_DIFFUSION_SUMMARY.md
│   │   └── ASSET_CONVERTER_SUMMARY.md
│   ├── consolidation/                ← NEW: Consolidation docs
│   │   ├── MERGE_REPORT.md
│   │   ├── CONSOLIDATION_COMPLETE.md
│   │   ├── ARCHIVE_MANIFEST.json
│   │   ├── REPO_INVENTORY.json
│   │   ├── SIMILARITY_MAP.json
│   │   ├── nested_package_manifest.json
│   │   ├── executor_deprecation_manifest.json
│   │   └── milestone_reports_manifest.json
│   ├── archives/                     ← Already exists
│   │   ├── README.md
│   │   ├── code_snapshots/
│   │   └── milestones/
│   └── DOCUMENTATION.md              ← Master index (keep here or move to root?)
├── scripts/                          ← NEW: Utility scripts
│   ├── consolidation_script.py
│   ├── BACKEND.py
│   └── tests/                        ← Move test scripts here
│       ├── test_async_dag.py
│       ├── test_forge_converter.py
│       ├── test_optimization_math.py
│       └── test_pipeline_paths.py
├── vaultmind_forge/                  ← Existing code
├── examples/                         ← Existing examples
└── assets/                           ← Existing assets
```

---

## Files to Keep in Root (10 files)

**Essential Documentation:**
1. `README.md` - Project overview
2. `LICENSE.md` - Legal
3. `CONTRIBUTING.md` - Contribution guidelines
4. `CHANGELOG.md` - Version history
5. `QUICK_START.md` - Fast onboarding

**Optional (consider moving):**
6. `DOCUMENTATION.md` - Master index (or move to docs/)

**Configuration:**
7. `package.json` - Node.js config (if applicable)
8. `pyproject.toml` - Python packaging
9. `requirements.txt` - Python deps
10. `.gitignore` - Git config

---

## Files to Relocate (41 files)

### → docs/api/ (3 files)
- NODE_API_README.md
- NODE_API_SUMMARY.md
- QUICKSTART_NODE_API.md

### → docs/guides/ (5 files)
- BUILD_NATIVE.md
- DOCS_QUICK_NAV.md → QUICK_NAV.md (rename)
- UTILS_GUIDE.md
- INTERACTIVE_TUTORIAL.md
- FORGE_CONVERTER_INTEGRATION_GUIDE.md

### → docs/architecture/ (7 files)
- VAULTMIND_FORGE_PIPELINE.md
- PROCEDURAL_GENERATION_OVERVIEW.md
- PROCEDURAL_ASSET_PIPELINE.md
- FORGE_CONVERTER_DESIGN.md
- AI_CONTROL_FRAMEWORK.md
- PROJECT_CONTEXT_COMPACT.md
- ASSET_REFERENCE_CATALOG.md

### → docs/components/ (2 files)
- LINEAGE_VIEWER_DOCS.md
- LINEAGE_VIEWER_SUMMARY.md

### → docs/development/ (7 files)
- INDUSTRY_STANDARDS_ANALYSIS.md
- INTEGRATION_AUDIT.md
- NATIVE_HANDLER_EVALUATION.md
- PROCEDURAL_LIBRARY_ANALYSIS.md
- VALIDATOR_ENHANCEMENTS.md
- UTILS_AMENDMENTS.md
- VAULTMIND_FORGE_CURSOR_PROMPT.md

### → docs/reports/ (5 files)
- STATE_OF_PROGRAM_REPORT.md
- DOCS_STATUS.md
- SESSION_SUMMARY.md
- FORGE_DIFFUSION_SUMMARY.md
- ASSET_CONVERTER_SUMMARY.md

### → docs/consolidation/ (9 files)
- MERGE_REPORT.md
- CONSOLIDATION_COMPLETE.md
- ARCHIVE_MANIFEST.json
- REPO_INVENTORY.json
- SIMILARITY_MAP.json
- nested_package_manifest.json
- executor_deprecation_manifest.json
- milestone_reports_manifest.json
- ROOT_CLEANUP_PLAN.md (this file, after execution)

### → scripts/ (5 files)
- consolidation_script.py
- BACKEND.py
- CMakeSettings.json

### → scripts/tests/ (4 files)
- test_async_dag.py
- test_forge_converter.py
- test_optimization_math.py
- test_pipeline_paths.py

---

## Migration Impact

### Documentation Updates Required

After migration, update these files with new paths:

1. **README.md** - Update all doc links
2. **DOCUMENTATION.md** - Update all file paths
3. **QUICK_NAV.md** (renamed) - Update all links
4. **CONTRIBUTING.md** - Update references to development docs

### Import Path Changes

**Python Scripts:**
- No import changes needed (moving scripts, not modules)
- Test scripts already standalone

**Configuration:**
- CMakeSettings.json - May need path updates if referenced

---

## Benefits

**Before (Current):**
- 51 files in root
- Confusing, hard to navigate
- No clear organization
- Professional projects don't look like this

**After (Proposed):**
- ~10 essential files in root
- Clear categorization by purpose
- Easy to find documentation
- Professional appearance
- Standard open-source structure

---

## Execution Plan

### Phase 1: Create Directory Structure
```bash
mkdir -p docs/api
mkdir -p docs/guides
mkdir -p docs/architecture
mkdir -p docs/components
mkdir -p docs/development
mkdir -p docs/reports
mkdir -p docs/consolidation
mkdir -p scripts/tests
```

### Phase 2: Move Files (with git mv for tracking)
```bash
# API docs
git mv NODE_API_README.md docs/api/
git mv NODE_API_SUMMARY.md docs/api/
git mv QUICKSTART_NODE_API.md docs/api/

# Guides
git mv BUILD_NATIVE.md docs/guides/
git mv DOCS_QUICK_NAV.md docs/guides/QUICK_NAV.md
git mv UTILS_GUIDE.md docs/guides/
git mv INTERACTIVE_TUTORIAL.md docs/guides/
git mv FORGE_CONVERTER_INTEGRATION_GUIDE.md docs/guides/

# Architecture
git mv VAULTMIND_FORGE_PIPELINE.md docs/architecture/
git mv PROCEDURAL_GENERATION_OVERVIEW.md docs/architecture/
git mv PROCEDURAL_ASSET_PIPELINE.md docs/architecture/
git mv FORGE_CONVERTER_DESIGN.md docs/architecture/
git mv AI_CONTROL_FRAMEWORK.md docs/architecture/
git mv PROJECT_CONTEXT_COMPACT.md docs/architecture/
git mv ASSET_REFERENCE_CATALOG.md docs/architecture/

# Components
git mv LINEAGE_VIEWER_DOCS.md docs/components/
git mv LINEAGE_VIEWER_SUMMARY.md docs/components/

# Development
git mv INDUSTRY_STANDARDS_ANALYSIS.md docs/development/
git mv INTEGRATION_AUDIT.md docs/development/
git mv NATIVE_HANDLER_EVALUATION.md docs/development/
git mv PROCEDURAL_LIBRARY_ANALYSIS.md docs/development/
git mv VALIDATOR_ENHANCEMENTS.md docs/development/
git mv UTILS_AMENDMENTS.md docs/development/
git mv VAULTMIND_FORGE_CURSOR_PROMPT.md docs/development/

# Reports
git mv STATE_OF_PROGRAM_REPORT.md docs/reports/
git mv DOCS_STATUS.md docs/reports/
git mv SESSION_SUMMARY.md docs/reports/
git mv FORGE_DIFFUSION_SUMMARY.md docs/reports/
git mv ASSET_CONVERTER_SUMMARY.md docs/reports/

# Consolidation
git mv MERGE_REPORT.md docs/consolidation/
git mv CONSOLIDATION_COMPLETE.md docs/consolidation/
git mv ARCHIVE_MANIFEST.json docs/consolidation/
git mv REPO_INVENTORY.json docs/consolidation/
git mv SIMILARITY_MAP.json docs/consolidation/
git mv nested_package_manifest.json docs/consolidation/
git mv executor_deprecation_manifest.json docs/consolidation/
git mv milestone_reports_manifest.json docs/consolidation/

# Scripts
git mv consolidation_script.py scripts/
git mv BACKEND.py scripts/
git mv CMakeSettings.json scripts/

# Test scripts
git mv test_async_dag.py scripts/tests/
git mv test_forge_converter.py scripts/tests/
git mv test_optimization_math.py scripts/tests/
git mv test_pipeline_paths.py scripts/tests/
```

### Phase 3: Update Documentation Links
- Run automated link updater script
- Manually verify critical files (README.md, DOCUMENTATION.md)

### Phase 4: Verification
- Check all links work
- Verify no broken references
- Test example/test imports still work

---

## Decision Point

**Option A: Full Cleanup (Recommended)**
- Move all 41 files as outlined above
- Professional structure
- ~10 files in root
- Update all documentation links

**Option B: Partial Cleanup**
- Move only consolidation artifacts (9 files) and scripts (9 files)
- Keep documentation in root for now
- ~33 files in root (still too many but better)

**Option C: Minimal Cleanup**
- Move only manifests/inventory (9 files)
- ~42 files in root (marginal improvement)

**Recommendation: Option A** - Do it right, get professional structure

---

## User Approval Required

Please confirm:
1. Which option (A, B, or C)?
2. Should DOCUMENTATION.md stay in root or move to docs/?
3. Any files that MUST stay in root?
4. Proceed with automated migration?
