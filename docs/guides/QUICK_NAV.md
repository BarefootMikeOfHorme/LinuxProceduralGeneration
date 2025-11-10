# VaultMind Forge - Documentation Quick Navigation

**Get to the right document fast.**

---

## 🚀 I Want To...

### Get Started
- **Install and run my first asset** → [QUICK_START.md](./QUICK_START.md)
- **Understand what this project does** → [README.md](./README.md)
- **Process my existing downloads** → [QUICK_START.md](./QUICK_START.md) (Section: Batch Processing)
- **Set up a drop folder** → [QUICK_START.md](./QUICK_START.md) (Section: Drop Folder)

### Use the API
- **API quick start (5 min)** → [QUICKSTART_NODE_API.md](./QUICKSTART_NODE_API.md)
- **Complete API reference** → [NODE_API_README.md](./NODE_API_README.md)
- **All 11 endpoints** → [NODE_API_README.md](./NODE_API_README.md#endpoints)

### Understand the System
- **Complete pipeline** → [VAULTMIND_FORGE_PIPELINE.md](./VAULTMIND_FORGE_PIPELINE.md)
- **Architecture overview** → [README.md](./README.md#architecture)
- **VAF format specification** → [vaultmind_forge/config/schemas/VAF_SYSTEM_DESIGN.md](./vaultmind_forge/config/schemas/VAF_SYSTEM_DESIGN.md)
- **Quick reference (all modules)** → [PROJECT_CONTEXT_COMPACT.md](./PROJECT_CONTEXT_COMPACT.md)

### Work with Specific Features
- **Asset intake & processing** → [vaultmind_forge/forge_intake/README.md](./vaultmind_forge/forge_intake/README.md)
- **AI image generation** → [vaultmind_forge/forge_diffusion/README.md](./vaultmind_forge/forge_diffusion/README.md)
- **Lineage tracking** → [LINEAGE_VIEWER_DOCS.md](./LINEAGE_VIEWER_DOCS.md)
- **60+ utility functions** → [UTILS_GUIDE.md](./UTILS_GUIDE.md)

### Contribute or Extend
- **How to contribute** → [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Build native components** → [BUILD_NATIVE.md](./BUILD_NATIVE.md)
- **Project status & roadmap** → [STATE_OF_PROGRAM_REPORT.md](./STATE_OF_PROGRAM_REPORT.md)
- **Version history** → [CHANGELOG.md](./CHANGELOG.md)

### Reference
- **Complete documentation index** → [DOCUMENTATION.md](./DOCUMENTATION.md)
- **License info** → [LICENSE.md](./LICENSE.md)
- **Supported formats** → [vaultmind_forge/forge_intake/format_registry.py](./vaultmind_forge/forge_intake/format_registry.py)

---

## 📚 Documentation by Type

### For Users
1. [README.md](./README.md) - What is this?
2. [QUICK_START.md](./QUICK_START.md) - How do I use it?
3. [VAULTMIND_FORGE_PIPELINE.md](./VAULTMIND_FORGE_PIPELINE.md) - How does it work?

### For Developers
1. [CONTRIBUTING.md](./CONTRIBUTING.md) - How to contribute
2. [PROJECT_CONTEXT_COMPACT.md](./PROJECT_CONTEXT_COMPACT.md) - System overview
3. [BUILD_NATIVE.md](./BUILD_NATIVE.md) - Building C++/Rust components

### For API Integrators
1. [QUICKSTART_NODE_API.md](./QUICKSTART_NODE_API.md) - Quick API setup
2. [NODE_API_README.md](./NODE_API_README.md) - Complete API docs
3. [UTILS_GUIDE.md](./UTILS_GUIDE.md) - Helper functions

### For AI Assistants
1. [VAULTMIND_FORGE_CURSOR_PROMPT.md](./VAULTMIND_FORGE_CURSOR_PROMPT.md) - AI instructions
2. [PROJECT_CONTEXT_COMPACT.md](./PROJECT_CONTEXT_COMPACT.md) - Quick reference
3. [CHANGELOG.md](./CHANGELOG.md) - What's new

---

## 🎯 Documentation Hierarchy

```
README.md (START HERE!)
    ├─→ QUICK_START.md (Get running)
    ├─→ VAULTMIND_FORGE_PIPELINE.md (Understand the system)
    └─→ DOCUMENTATION.md (Find everything else)

CONTRIBUTING.md (Want to help?)
    ├─→ BUILD_NATIVE.md (Build components)
    ├─→ PROJECT_CONTEXT_COMPACT.md (Code overview)
    └─→ CHANGELOG.md (Recent changes)

Module-Specific (Deep dives)
    ├─→ vaultmind_forge/forge_intake/README.md
    ├─→ vaultmind_forge/forge_diffusion/README.md
    └─→ (Other modules - see DOCUMENTATION.md)
```

---

## ⚠️ Common Confusions (Clarified)

### "Which getting started guide?"
- **README.md** → 2-minute overview
- **QUICK_START.md** → 5-10 minute hands-on tutorial
- **QUICKSTART_NODE_API.md** → API-specific (for integrators only)

**Pick one based on your needs.**

### "Which pipeline doc?"
- **VAULTMIND_FORGE_PIPELINE.md** → **CANONICAL** - Complete asset intake pipeline ⭐
- **PROCEDURAL_GENERATION_OVERVIEW.md** → Historical overview (for context only)
- **PROCEDURAL_ASSET_PIPELINE.md** → Converter-specific (subset of main pipeline)

**Use VAULTMIND_FORGE_PIPELINE.md unless you specifically need converter docs.**

### "What's the difference between summaries and full docs?"
- **\*\_SUMMARY.md** → Quick reference (5-10 min read)
- **Full docs** → Comprehensive guide (30+ min read)

**Summaries** = Executive overview
**Full docs** = Complete manual

### "Where's the module documentation?"
All module READMEs are in:
```
vaultmind_forge/
    ├── forge_intake/README.md      ← ⭐ Complete
    ├── forge_diffusion/README.md   ← ⭐ Complete
    └── forge_*/README.md           ← (Others: stubs, being written)
```

**Note:** Ignore `vaultmind_forge/vaultmind_forge/` - it's a duplicate being removed.

---

## 🔧 Development/Historical Docs (Archival)

These docs capture development history but aren't needed for daily use:

- `SESSION_SUMMARY.md` - Development session notes
- `INTEGRATION_AUDIT.md` - Integration analysis
- `TASK_VERIFICATION_REPORT.md` - Task completion audit
- `PHASE_1_AND_4_COMPLETE.md` - Milestone reports
- `BOT_FRAMEWORK_COMPLETE.md` - Bot system completion
- `BEAST_MODE_ACTION_PLAN.md` - Development roadmap

**When to read these:** If you're curious about project evolution or need historical context.

---

## 📖 Full Documentation Index

For a complete alphabetical list of ALL 72+ documentation files, see:
**[DOCUMENTATION.md](./DOCUMENTATION.md)**

---

---

## 📦 Archives

Historical code and milestone documentation have been archived:

- **Code Archives:** `docs/archives/code_snapshots/`
  - Nested package snapshot (historical)
  - Deprecated executor prototype
- **Milestone Archives:** `docs/archives/milestones/`
  - Development completion reports (6 files)

**Full Details:** [MERGE_REPORT.md](./MERGE_REPORT.md) - Complete consolidation documentation

---

**Last Updated:** November 9, 2025
**For:** VaultMind Forge v0.4.0
