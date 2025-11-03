# VaultMind Forge - Compact Project Context

## Project Overview
**VaultMind Forge (LPG)** - AI-powered asset generation framework with Python backend and Node.js API layer.

**Stack:** Python 3.10+ (SDXL/diffusers), C++17 (validation), Rust (PyO3), Node.js 18+ (API)

**Core Philosophy:** Precision, reproducibility, complete lineage tracking over speed.

---

## Directory Structure (Key Files Only)

```
LPG/
├── vaultmind_forge/              # Python backend
│   ├── forge_diffusion/          # SDXL generation
│   ├── forge_validator/          # Quality validation
│   ├── forge_lineage/            # Lineage storage
│   ├── forge_packaging/          # Asset packaging
│   └── forge_cli.py              # CLI entry point
├── src/                          # Node.js API layer
│   ├── utils.js                  # 60+ utility functions (1,187 lines)
│   ├── pythonBridge.js           # Python CLI integration
│   ├── handlers.js               # REST API routes
│   ├── server.js                 # Express server
│   └── forge/                    # Node.js forge modules
│       ├── diffusion.js          # Generation with multi-pass
│       ├── validator.js          # Asset validation
│       └── packager.js           # ZIP packaging
├── src/frontend/components/      # React components
│   ├── LineageViewer.jsx         # Lineage visualization
│   └── LineageViewer.css         # Component styles
└── examples/                     # Usage examples
```

---

## Module 1: Lineage Tracking (src/utils.js)

### Core Functions

**Create & Tag:**
- `createLineageMetadata({ jobId, branch, parent, metadata })` → Lineage metadata
- `createAssetLineageTag({ assetPath, lineageId, jobId, status, metrics })` → Asset tag
- `computeFileChecksum(filePath)` → SHA-256 hash
- `createRejectionMetadata({ assetPath, reason, validationResult, failedMetrics })` → Rejection data

**Storage:**
- `createLineageRecord({ lineageMetadata, jobConfig, assets, validations, executionMetrics })` → Complete record
- `saveLineageRecord(lineageRecord, outputDir?)` → Saves to `lineage/run_{id}_{timestamp}.json`
- `loadLineageRecord(filePath)` → Loads record
- `queryLineageRecords({ jobId?, branch?, status?, lineageDir? })` → Query records

### Lineage Record Structure

```javascript
{
  version: "1.0",
  run_id: "uuid",
  timestamp: "ISO8601",
  lineage: { lineage_id, job_id, branch, parent, created_at, metadata },
  job: { /* full job config */ },
  assets: [{ asset_path, checksum, validated, metrics }],
  validations: [{ file, score, status, passed }],
  rejections: [{ asset_path, reason, failed_metrics, suggestions }],
  execution: { start_time, end_time, duration_ms, status },
  system: { platform, arch, node_version, memory_used_mb }
}
```

---

## Module 2: Diffusion Generation (src/forge/diffusion.js)

### Classes

**GenerationJob**
```javascript
new GenerationJob({ name, style, target: [w, h], refs: [], meta: {} })
```

**DiffusionGenerator**
```javascript
const generator = new DiffusionGenerator({ mode: 'python-bridge' | 'placeholder' });

// Basic generation
const assets = await generator.generate(job, outputDir, { count: 3 });

// Multi-pass with validation
const result = await generator.generateMultiPass(job, outputDir, {
  passes: 5,
  minScore: 0.7,
  validator: async (path) => validator.validate(path)
});
// Returns: { winner, allVariations, rejectedVariations, summary }

// Complete workflow with lineage
const result = await generator.generateWithLineage(jobConfig, outputDir, {
  multiPass: true,
  passes: 3,
  packageAssets: true
});
// Returns: { jobId, lineageId, winner, summary, lineagePath, packagePath }
```

### Multi-Pass Logic
1. Generate N variations (1-10)
2. Validate each with custom validator
3. Score & filter by minScore threshold
4. Auto-select winner (highest score)
5. Track rejections with improvement suggestions

---

## Module 3: Validation (src/forge/validator.js)

### AssetValidator

```javascript
const validator = new AssetValidator({
  mode: 'python-bridge' | 'basic',
  thresholds: { sharpness: 0.7, consistency: 0.8, color_fidelity: 0.75 }
});

// Single validation
const result = await validator.validate(assetPath);
// Returns: { file, status, score, passed, metrics, timestamp }

// Batch validation
const { results, summary } = await validator.validateBatch([...paths]);

// Custom metrics
const result = await validator.validateWithMetrics(assetPath, {
  minDimensions: async (path) => QualityMetrics.minDimensions(path, { minWidth: 512, minHeight: 512 }),
  aspectRatio: async (path) => QualityMetrics.aspectRatio(path, 1.0, 0.1)
});
```

### Quality Metrics
- **sharpness** - Variance-based image sharpness (0-1)
- **anatomy** - Anatomical correctness (Python only)
- **prompt_alignment** - Text-image alignment (Python only)
- **consistency** - Multi-image consistency (Python only)
- **color_fidelity** - Color histogram matching (C++/Python)

---

## Module 4: Asset Packaging (src/forge/packager.js)

### AssetPackager

```javascript
const packager = new AssetPackager({ compressionLevel: 9, includeMetadata: true });

// Basic packaging
const path = await packager.packageAssets(assets, 'output.zip', { jobId, metadata });

// With checksums
const info = await packager.packageWithChecksums(assets, 'output.zip', metadata);
// Returns: { packagePath, packageChecksum, packageSize, assets: [{checksum, ...}] }

// Create manifest
await packager.createManifest(assets, 'manifest.json', metadata);
```

---

## REST API Endpoints

**Diffusion:**
- `POST /api/diffusion/generate` - Generate assets (simple or multi-pass)
- `POST /api/diffusion/generate-with-lineage` - Full workflow with lineage

**Lineage:**
- `GET /api/lineage?jobId=&branch=&status=` - Query lineage records
- `GET /api/lineage/:runId` - Get single record

**Validation:**
- `POST /api/validate` - Validate uploaded files (multipart)
- `POST /api/validate/paths` - Validate by file paths

**Jobs:**
- `POST /api/jobs` - Create async job
- `GET /api/jobs/:id/status` - Get job status
- `GET /api/jobs/:id/outputs` - Get output files

**System:**
- `GET /api/health` - Health check
- `GET /api/version` - Get Forge version
- `GET /api/status` - Get system status
- `POST /api/demo` - Run demo pipeline

---

## Python Bridge (src/pythonBridge.js)

### Key Functions

```javascript
import { executePythonScript, getVersion, getStatus, runDemo, validateAssets } from './pythonBridge.js';

// Execute Python CLI
const { stdout, stderr, exitCode } = await executePythonScript(scriptPath, args, { timeout: 300000 });

// Forge CLI commands
await getVersion();                    // Get forge version
await getStatus();                     // Get installed modules
await runDemo(outputDir);              // Run demo pipeline
await validateAssets([...paths]);      // Validate assets

// Job execution
const jobId = await executeJobAsync(jobConfig, outputDir);
const status = getJobStatus(jobId);    // { status, progress, outputDir, result }
```

---

## Utils.js Quick Reference (60+ functions)

**Path & Files:**
`getProjectRoot()`, `ensureJobOutputDir(jobId)`, `readJSON(path)`, `writeJSON(path, data)`, `fileExists(path)`, `listFiles(dir, filter?)`, `getFileSize(path)`

**Job Creation:**
`createJobConfig({ outputType, styleTags, passes, consistencyThreshold })`, `createSimpleJob({ name, style, target })`, `OUTPUT_TYPES[]`

**Validation:**
`validateJobConfig(config)`, `validateAgainstSchema(data, schemaName)`, `validateConfigBatch(configs, schema)`, `sanitizeConfig(config, allowedFields)`, `mergeConfigs(base, override, immutableFields)`

**Python Execution:**
`getPythonCommand()`, `executePythonScript(path, args, opts)`, `parsePythonJSON(output, strict?)`, `parsePythonKeyValue(output)`, `validatePythonOutput(output, expectations)`

**Responses:**
`successResponse(data, message)`, `errorResponse(message, code, details)`, `formatValidationErrors(errors)`

**Error Handling:**
`ForgeAPIError(message, statusCode, details)`, `asyncHandler(fn)`

**Logging:**
`logger.info(msg, meta)`, `logger.warn(msg, meta)`, `logger.error(msg, meta)`, `logger.debug(msg, meta)`

**Helpers:**
`sleep(ms)`, `formatBytes(bytes)`, `generateJobId()`, `parseDuration(str)`

---

## React Component: LineageViewer

**Location:** `src/frontend/components/LineageViewer.jsx`

**Props:**
```jsx
<LineageViewer apiBaseUrl="http://localhost:3000/api" />
```

**Features:**
- 3 view modes: Grid, List, Timeline
- Filters: jobId, branch, status, search
- Statistics dashboard (6 metrics)
- Detail modal with rejection analysis
- Responsive design

**API Requirements:**
- `GET /api/lineage?jobId=&branch=&status=` → `{ success, data: { records, count } }`

---

## Complete Workflow Example

```javascript
import { DiffusionGenerator } from './forge/diffusion.js';
import { AssetValidator } from './forge/validator.js';
import { createJobConfig } from './utils.js';

// 1. Create job config
const jobConfig = createJobConfig({
  outputType: 'character',
  styleTags: ['anime', 'cel-shaded'],
  passes: 3,
  consistencyThreshold: 0.85
});

// 2. Initialize generator & validator
const generator = new DiffusionGenerator({ mode: 'placeholder' });
const validator = new AssetValidator({ mode: 'basic' });

// 3. Generate with full lineage tracking
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

// 4. Result includes:
// - jobId, lineageId
// - winner (best scoring asset)
// - summary (stats)
// - lineagePath (saved JSON)
// - packagePath (ZIP archive)
```

---

## Configuration Files

**Job Schema:** `vaultmind_forge/config/schemas/job.schema.json`
```json
{
  "required": ["id", "output_type", "passes"],
  "properties": {
    "id": "string",
    "output_type": "enum[storyboard|game_asset|character|...]",
    "style_tags": "string[]",
    "passes": { "min": 1, "max": 10, "default": 3 },
    "consistency_threshold": { "min": 0, "max": 1, "default": 0.8 },
    "references": { "palettes": [], "embeddings": [], "style_guides": [] },
    "lineage": { "branch": "string", "parent": "string|null" }
  }
}
```

---

## Dependencies

**Node.js:**
- express, ajv, multer, uuid, cors, helmet
- archiver (ZIP), sharp (image processing)
- react, react-dom (dev)

**Python:**
- diffusers, torch (SDXL)
- PIL, numpy (images)
- pydantic (validation)

**Build:**
- CMake (C++), maturin (Rust), npm (Node.js)

---

## Key Commands

```bash
# Start API server
npm start

# Run diffusion examples
node examples/diffusion-example.js all

# View lineage viewer
start examples/lineage-viewer-demo.html

# Generate with lineage
curl -X POST http://localhost:3000/api/diffusion/generate-with-lineage \
  -H "Content-Type: application/json" \
  -d '{"jobConfig": {"id": "test", "output_type": "character"}, "multiPass": true}'

# Query lineage
curl http://localhost:3000/api/lineage?branch=main&status=completed
```

---

## Current State Summary

**Implemented:**
✅ Complete lineage tracking system (9 functions)
✅ Multi-pass diffusion generation (3 modes)
✅ Asset validation (Python bridge + basic Node.js)
✅ Asset packaging with checksums
✅ REST API (11 endpoints)
✅ React LineageViewer component (3 views)
✅ Python CLI integration
✅ 60+ utility functions
✅ Comprehensive documentation

**Total Code:**
- Python backend: ~500 lines
- Node.js API: ~3,500 lines
- React frontend: ~1,200 lines
- Documentation: ~5,000 lines

**Status:** Production ready 🚀

---

## Quick Reference URLs

- Full API docs: `NODE_API_README.md`
- Utils guide: `UTILS_GUIDE.md`
- Diffusion module: `FORGE_DIFFUSION_SUMMARY.md`
- LineageViewer: `LINEAGE_VIEWER_DOCS.md`
- Python protocol: `vaultmind_forge/PROTOCOL.md`

---

**End of Compact Context** - All modules summarized for space efficiency.
