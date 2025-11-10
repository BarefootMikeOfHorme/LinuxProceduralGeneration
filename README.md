# 🧬 VaultMind Forge

**AI-Powered Asset Generation Framework with Complete Lineage Tracking**

VaultMind Forge is a production-ready framework for generating game assets, characters, storyboards, and visual content using SDXL diffusion models. Built on a philosophy of **precision, reproducibility, and complete lineage tracking** over raw speed.

> **📖 Documentation:** [Quick Navigation](./docs/guides/QUICK_NAV.md) | [Complete Index](./DOCUMENTATION.md) | [Quick Start](./QUICK_START.md) | [API Docs](./docs/api/NODE_API_README.md)

---

## 🎯 Core Philosophy

**Lineage Fidelity**: Every asset has a complete genealogy with parent-child relationships, checksums, and validation history.

**Precision Over Speed**: Multi-pass generation with quality scoring ensures only the best assets are selected.

**Modular Architecture**: Python backend for generation, C++/Rust for validation, Node.js API layer for integration.

**Ceremonial Clarity**: Documentation as sacred scrolls, code as ritual, lineage as scripture.

---

## ✨ Features

### 🎨 Multi-Pass Diffusion Generation
- Generate 1-10 variations per job
- Auto-select winner based on quality scores
- Track rejections with AI-generated improvement suggestions
- Multiple backends: Python SDXL, Placeholder mode, Cloud APIs (planned)

### 🧬 Complete Lineage Tracking
- Parent-child genealogy with branch/merge support
- SHA-256 checksums for asset integrity
- Execution metrics and system information
- Query system for filtering records by job, branch, or status

### 📦 Asset Packaging
- ZIP archives with metadata.json
- Configurable compression levels
- Checksum verification for integrity
- Manifest generation

### ✅ Quality Validation
- Multiple backends: Python validators, Node.js basic validation
- Extensible custom metrics system
- Batch validation support
- Quality scoring: sharpness, anatomy, prompt alignment, consistency, color fidelity

### 📥 Asset Intake & Processing (NEW!)
- **Multi-Version Asset Detection**: Automatically groups different format versions (e.g., robot.fbx + robot.obj + robot.glb)
- **40+ Format Support**: glTF, FBX, OBJ, USD, COLLADA, Blender, textures, archives
- **Intelligent Merging**: Combines best data from each variant (geometry, materials, rigging, animations)
- **Drop Folder Monitoring**: Real-time file watching with auto-processing
- **Daemon Service**: Persistent background processing that survives reboots
- **VAF (VaultMind Asset Format)**: Unified multi-tier format system with 6 specialized variants

### 🖼️ LineageViewer React Component
- **3 View Modes**: Grid, List, Timeline
- **Advanced Filtering**: Job ID, Branch, Status, Search
- **Statistics Dashboard**: 6 real-time metrics
- **Rejection Analysis**: Failed metrics with improvement suggestions
- **Responsive Design**: Mobile-friendly UI

### 🔌 REST API Layer
- 11 comprehensive endpoints
- Express.js server with CORS and Helmet security
- JSON Schema validation with AJV
- Structured error handling and logging

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  React Frontend                      │
│              (LineageViewer UI)                      │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              Node.js API Layer                       │
│  ┌──────────┬──────────┬──────────┬──────────────┐ │
│  │ Diffusion│Validator │ Packager │ PythonBridge │ │
│  │   Module │  Module  │  Module  │     Module   │ │
│  └──────────┴──────────┴──────────┴──────────────┘ │
│  ┌──────────────────────────────────────────────┐  │
│  │     Utils (60+ helper functions)             │  │
│  │  - Lineage tagging (9 functions)             │  │
│  │  - Config validation (6 functions)           │  │
│  │  - Python execution (6 functions)            │  │
│  │  - Response formatting, logging, errors      │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              Python Backend                          │
│  ┌────────────┬──────────────┬──────────────────┐  │
│  │forge_      │forge_        │forge_            │  │
│  │diffusion   │validator     │lineage           │  │
│  │(SDXL)      │(Quality)     │(Tracking)        │  │
│  └────────────┴──────────────┴──────────────────┘  │
└──────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│        C++/Rust Validation Modules                   │
│  (Color fidelity, sharpness, anatomy checks)         │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18.0.0 or higher
- **Python** 3.10+ (optional, for SDXL generation)
- **CMake** (optional, for C++ validators)
- **Rust** (optional, for Rust validators)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/vaultmind-forge.git
cd vaultmind-forge

# Install Node.js dependencies
npm install

# Start API server
npm start
```

Server starts at `http://localhost:3000`

### Generate Your First Asset

```bash
curl -X POST http://localhost:3000/api/diffusion/generate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hero-character",
    "style": "cel-shaded",
    "target": [512, 512],
    "multiPass": true,
    "passes": 3,
    "packageAssets": true
  }'
```

### View Lineage Records

Open `examples/lineage-viewer-demo.html` in your browser to visualize generated assets, quality scores, and lineage history.

---

## 📚 Documentation Scrolls

Comprehensive documentation organized as sacred scrolls:

### Core Scrolls
- **[PROJECT_CONTEXT_COMPACT.md](PROJECT_CONTEXT_COMPACT.md)** - Quick reference for all modules (~400 lines)
- **[SCROLL_INDEX.md](SCROLL_INDEX.md)** - Master catalog of all documentation

### API Layer Scrolls
- **[NODE_API_README.md](NODE_API_README.md)** - Complete API documentation
- **[UTILS_GUIDE.md](UTILS_GUIDE.md)** - 60+ utility functions reference

### Module Scrolls
- **[FORGE_DIFFUSION_SUMMARY.md](FORGE_DIFFUSION_SUMMARY.md)** - Diffusion generation module
- **[LINEAGE_VIEWER_DOCS.md](LINEAGE_VIEWER_DOCS.md)** - React component documentation

### Planning Scrolls
- **[NEXT.md](NEXT.md)** - Upcoming features and scrolls

---

## 💻 Usage Examples

### Multi-Pass Generation with Lineage

```javascript
import { DiffusionGenerator } from './src/forge/diffusion.js';
import { AssetValidator } from './src/forge/validator.js';
import { createJobConfig } from './src/utils.js';

// Create job configuration
const jobConfig = createJobConfig({
  outputType: 'character',
  styleTags: ['anime', 'cel-shaded'],
  passes: 5,
  consistencyThreshold: 0.85
});

// Initialize generator and validator
const generator = new DiffusionGenerator({ mode: 'placeholder' });
const validator = new AssetValidator({ mode: 'basic' });

// Generate with complete lineage tracking
const result = await generator.generateWithLineage(
  jobConfig,
  './output',
  {
    multiPass: true,
    passes: 5,
    validator: async (path) => validator.validate(path),
    packageAssets: true
  }
);

console.log('Winner:', result.winner);
console.log('Lineage ID:', result.lineageId);
console.log('Lineage saved:', result.lineagePath);
console.log('Package:', result.packagePath);
```

### Query Lineage Records

```javascript
import { queryLineageRecords } from './src/utils.js';

// Query by job ID and branch
const records = await queryLineageRecords({
  jobId: 'job-123',
  branch: 'main',
  status: 'completed'
});

console.log(`Found ${records.length} lineage records`);
```

### React LineageViewer

```jsx
import LineageViewer from './src/frontend/components/LineageViewer';
import './src/frontend/components/LineageViewer.css';

function App() {
  return <LineageViewer apiBaseUrl="http://localhost:3000/api" />;
}
```

### Asset Intake & Processing (NEW!)

```python
from vaultmind_forge.forge_intake.batch_ingest_v2 import AssetIngestorV2

# Batch process existing downloads
ingestor = AssetIngestorV2(
    downloads_dir="C:/Users/Me/Downloads",
    project_root="C:/Projects/GameAssets"
)
summary = ingestor.batch_process()

print(f"Processed {summary['processed']} assets")
print(f"Multi-version merges: {summary['multi_version_merges']}")
```

```python
# Real-time drop folder monitoring
from vaultmind_forge.forge_intake.drop_folder_monitor import DropFolderMonitor

monitor = DropFolderMonitor(
    drop_folder="C:/AssetDropFolder",
    output_folder="C:/ProcessedAssets",
    batch_size=10,
    batch_timeout=30.0
)
monitor.run_interactive()  # Press Ctrl+C to stop
```

```bash
# Background daemon service
python -m vaultmind_forge.forge_intake.forge_daemon start \
    "C:/AssetDropFolder" \
    "C:/ProcessedAssets"

# Check status
python -m vaultmind_forge.forge_intake.forge_daemon status
```

**See Also:**
- [Complete Pipeline Documentation](./VAULTMIND_FORGE_PIPELINE.md)
- [Quick Start Guide](./QUICK_START.md)
- [VAF Format Specification](./vaultmind_forge/config/schemas/VAF_SYSTEM_DESIGN.md)

---

## 🔌 REST API Endpoints

### Diffusion Generation

- **`POST /api/diffusion/generate`** - Simple or multi-pass generation
- **`POST /api/diffusion/generate-with-lineage`** - Full workflow with lineage tracking

### Lineage Tracking

- **`GET /api/lineage?jobId=&branch=&status=`** - Query lineage records
- **`GET /api/lineage/:runId`** - Get single lineage record

### Validation

- **`POST /api/validate`** - Validate uploaded files (multipart)
- **`POST /api/validate/paths`** - Validate by file paths

### Jobs

- **`POST /api/jobs`** - Create async job
- **`GET /api/jobs/:id/status`** - Get job status
- **`GET /api/jobs/:id/outputs`** - Get output files

### System

- **`GET /api/health`** - Health check
- **`GET /api/version`** - Get Forge version
- **`GET /api/status`** - Get system status
- **`POST /api/demo`** - Run demo pipeline

---

## 📊 Lineage Record Structure

Every generation produces a complete lineage record:

```json
{
  "version": "1.0",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-30T12:00:00.000Z",
  "lineage": {
    "lineage_id": "lineage-abc123",
    "job_id": "job-123",
    "branch": "main",
    "parent": null,
    "metadata": {}
  },
  "job": {
    "id": "job-123",
    "output_type": "character",
    "style_tags": ["anime", "cel-shaded"],
    "passes": 3
  },
  "assets": [
    {
      "asset_path": "output/hero.png",
      "checksum": "sha256...",
      "validated": true,
      "metrics": { "score": 0.89 }
    }
  ],
  "validations": [
    {
      "file": "output/hero.png",
      "score": 0.89,
      "status": "PASS",
      "passed": true
    }
  ],
  "rejections": [
    {
      "asset_path": "output/failed.png",
      "reason": "Score below threshold",
      "failed_metrics": ["sharpness", "anatomy"],
      "suggestions": [
        "Increase resolution or adjust denoising steps",
        "Use reference images or anatomy ControlNet"
      ]
    }
  ],
  "execution": {
    "start_time": "2025-10-30T12:00:00.000Z",
    "end_time": "2025-10-30T12:05:00.000Z",
    "duration_ms": 300000,
    "status": "completed"
  },
  "system": {
    "platform": "win32",
    "arch": "x64",
    "node_version": "v18.0.0",
    "memory_used_mb": 125.4
  }
}
```

---

## 🎨 LineageViewer Features

The React LineageViewer component provides comprehensive visualization:

### View Modes
- **Grid View**: Card-based layout with hover effects
- **List View**: Sortable table with all metrics
- **Timeline View**: Chronological visualization with connection lines

### Filters
- **Search**: Free text search in Run ID and Job ID
- **Job ID**: Filter by specific job
- **Branch**: Filter by lineage branch
- **Status**: Filter by execution status (completed, failed, running)

### Statistics Dashboard
- Total Runs
- Completed Count
- Failed Count
- Total Assets Generated
- Average Quality Score
- Average Execution Duration

### Rejection Analysis
- View failed assets with validation scores
- See specific failed metrics
- Get AI-generated improvement suggestions
- Understand why assets were rejected

---

## 🛠️ Development

### Project Structure

```
vaultmind-forge/
├── src/
│   ├── server.js                    # Express server
│   ├── handlers.js                  # API route handlers
│   ├── utils.js                     # 60+ utility functions
│   ├── pythonBridge.js              # Python CLI integration
│   ├── forge/
│   │   ├── diffusion.js             # Generation module
│   │   ├── validator.js             # Validation module
│   │   └── packager.js              # Packaging module
│   └── frontend/
│       └── components/
│           ├── LineageViewer.jsx    # React component
│           └── LineageViewer.css    # Component styles
├── vaultmind_forge/                 # Python backend
│   ├── forge_diffusion/             # SDXL generation
│   ├── forge_validator/             # Quality validation
│   ├── forge_lineage/               # Lineage tracking
│   └── forge_cli.py                 # CLI entry point
├── examples/
│   ├── diffusion-example.js         # Node.js examples
│   └── lineage-viewer-demo.html     # Standalone demo
├── output/                          # Generated assets
│   ├── {jobId}/                     # Job-specific outputs
│   └── lineage/                     # Lineage records
└── package.json                     # Node.js dependencies
```

### Run Examples

```bash
# All diffusion examples
node examples/diffusion-example.js all

# Specific examples
node examples/diffusion-example.js multipass
node examples/diffusion-example.js workflow
node examples/diffusion-example.js validation
```

### Development Mode

```bash
# Watch mode with auto-reload
npm run dev
```

---

## 🧪 Testing

### Generate Test Data

```bash
# Generate with lineage tracking
curl -X POST http://localhost:3000/api/diffusion/generate-with-lineage \
  -H "Content-Type: application/json" \
  -d '{
    "jobConfig": {
      "id": "test-job",
      "output_type": "character",
      "lineage": { "branch": "main" }
    },
    "multiPass": true,
    "passes": 3
  }'
```

### View in LineageViewer

```bash
# Open standalone demo
start examples/lineage-viewer-demo.html
```

---

## 📦 Dependencies

### Node.js
- `express` - Web framework
- `ajv` - JSON Schema validation
- `multer` - File upload handling
- `archiver` - ZIP packaging
- `sharp` - Image processing
- `uuid` - Unique ID generation
- `cors` - CORS middleware
- `helmet` - Security headers

### React (Dev Dependencies)
- `react` ^18.2.0
- `react-dom` ^18.2.0
- `vite` ^5.0.8

### Python (Optional)
- `diffusers` - SDXL models
- `torch` - PyTorch backend
- `PIL` - Image processing
- `pydantic` - Data validation

---

## 🔮 Upcoming Features

See [NEXT.md](NEXT.md) for the complete roadmap:

### Planned Scrolls
- **semanticTagger.js** - AI-powered semantic tagging for assets
- **lineageWatcher.js** - Real-time lineage monitoring and WebSocket updates
- **comparisonView.jsx** - Side-by-side asset comparison
- **exportButton.jsx** - Export lineage to JSON/CSV/PDF
- **glyphSystem.js** - Sacred glyph system for ceremonial asset marking

### Planned Features
- **Lineage Merge Support** - Merge multiple lineage branches
- **Asset Relationships** - Define dependencies between assets
- **Version Control Integration** - Git-like operations for asset history
- **Distributed Generation** - Multi-node generation cluster
- **Advanced Analytics** - ML-powered quality prediction

---

## 🤝 Contributing

VaultMind Forge follows the philosophy of ceremonial clarity:

1. **Documentation First**: Update scrolls before code
2. **Lineage Fidelity**: All changes tracked with complete history
3. **Modular Structure**: Each module is self-contained
4. **Test Coverage**: All features must have examples

---

## 📜 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built on the shoulders of giants:
- Stability AI (SDXL models)
- Hugging Face (diffusers library)
- Express.js community
- React community

---

## 📞 Support

- **Documentation**: See scrolls in project root
- **Issues**: [GitHub Issues](https://github.com/yourusername/vaultmind-forge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/vaultmind-forge/discussions)

---

**VaultMind Forge** - *Where AI generation meets ceremonial precision* 🧬✨

*Built with lineage fidelity, documented with sacred scrolls, crafted with precision.*
