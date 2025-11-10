# VaultMind Forge Utils.js - Complete Usage Guide

Comprehensive guide for all utility functions in `src/utils.js` including the new lineage tagging, Python script execution, and enhanced config validation features.

## Table of Contents

1. [Response Formatting](#response-formatting)
2. [Error Handling](#error-handling)
3. [Lineage Tagging](#lineage-tagging) ⭐ NEW
4. [Config Validation](#config-validation) ⭐ ENHANCED
5. [Python Script Execution](#python-script-execution) ⭐ NEW
6. [File Operations](#file-operations)
7. [Job Creation](#job-creation)
8. [Logging](#logging)

---

## Response Formatting

### Standard Success Response

```javascript
import { successResponse } from './utils.js';

// Basic success
res.json(successResponse({ id: 123, name: 'Asset' }));

// With custom message
res.json(successResponse(
  { jobId: 'abc-123' },
  'Job created successfully'
));
```

**Output:**
```json
{
  "success": true,
  "message": "Job created successfully",
  "data": { "jobId": "abc-123" },
  "timestamp": "2025-10-30T12:00:00.000Z"
}
```

### Standard Error Response

```javascript
import { errorResponse } from './utils.js';

// Basic error
res.status(404).json(errorResponse('Resource not found', 404));

// With details
res.status(400).json(errorResponse(
  'Validation failed',
  400,
  { fields: ['email', 'password'] }
));
```

---

## Error Handling

### Custom ForgeAPIError

```javascript
import { ForgeAPIError, asyncHandler } from './utils.js';

// Throw custom error
throw new ForgeAPIError('Job not found', 404, { jobId });

// Use in route handlers
router.get('/jobs/:id', asyncHandler(async (req, res) => {
  const job = await findJob(req.params.id);
  if (!job) {
    throw new ForgeAPIError('Job not found', 404);
  }
  res.json(successResponse(job));
}));
```

---

## Lineage Tagging

### Create Lineage Metadata

```javascript
import {
  createLineageMetadata,
  generateLineageId
} from './utils.js';

const lineage = createLineageMetadata({
  jobId: 'job-123',
  branch: 'main',
  parent: 'parent-lineage-id',
  metadata: {
    artist: 'John Doe',
    project: 'Game Alpha'
  }
});
```

**Output:**
```json
{
  "lineage_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_id": "job-123",
  "branch": "main",
  "parent": "parent-lineage-id",
  "created_at": "2025-10-30T12:00:00.000Z",
  "version": "1.0",
  "metadata": {
    "artist": "John Doe",
    "project": "Game Alpha",
    "nodeType": "generation_run",
    "platform": "win32",
    "nodeVersion": "v18.0.0"
  }
}
```

### Tag Assets with Lineage

```javascript
import { createAssetLineageTag, computeFileChecksum } from './utils.js';

// Create asset tag
const assetTag = createAssetLineageTag({
  assetPath: 'output/character_001.png',
  lineageId: lineage.lineage_id,
  jobId: 'job-123',
  status: 'generated',
  metrics: {
    sharpness: 0.85,
    color_fidelity: 0.90
  }
});

// Compute checksum
const checksum = await computeFileChecksum('output/character_001.png');
assetTag.checksum = checksum;
```

### Create Complete Lineage Record

```javascript
import {
  createLineageRecord,
  saveLineageRecord
} from './utils.js';

const lineageRecord = createLineageRecord({
  lineageMetadata: lineage,
  jobConfig: jobConfig,
  assets: [assetTag1, assetTag2],
  validations: validationResults,
  packagePath: 'output/package.zip',
  executionMetrics: {
    startTime: '2025-10-30T12:00:00.000Z',
    endTime: '2025-10-30T12:05:00.000Z',
    durationMs: 300000,
    status: 'completed'
  }
});

// Save to file
const savedPath = await saveLineageRecord(lineageRecord);
console.log('Lineage saved to:', savedPath);
// Output: lineage/run_550e8400-e29b-41d4-a716-446655440000_1730289600000.json
```

### Query Lineage Records

```javascript
import { queryLineageRecords } from './utils.js';

// Find all records for a specific job
const records = await queryLineageRecords({
  jobId: 'job-123'
});

// Find by branch
const mainRecords = await queryLineageRecords({
  branch: 'main'
});

// Find completed jobs
const completed = await queryLineageRecords({
  status: 'completed'
});

// Find with custom directory
const customRecords = await queryLineageRecords({
  lineageDir: 'C:/custom/lineage/path'
});
```

### Load Lineage Record

```javascript
import { loadLineageRecord } from './utils.js';

const record = await loadLineageRecord('lineage/run_abc123.json');

console.log('Run ID:', record.run_id);
console.log('Assets:', record.assets.length);
console.log('Status:', record.execution.status);
```

### Track Rejections

```javascript
import { createRejectionMetadata } from './utils.js';

const rejection = createRejectionMetadata({
  assetPath: 'output/failed_001.png',
  reason: 'Low quality score',
  validationResult: {
    score: 0.45,
    status: 'FAIL'
  },
  failedMetrics: ['sharpness', 'anatomy']
});

console.log(rejection);
```

**Output:**
```json
{
  "asset_path": "output/failed_001.png",
  "rejected_at": "2025-10-30T12:00:00.000Z",
  "reason": "Low quality score",
  "failed_metrics": ["sharpness", "anatomy"],
  "validation_score": 0.45,
  "validation_status": "FAIL",
  "can_retry": true,
  "suggestions": [
    "Increase resolution or adjust denoising steps",
    "Use reference images or anatomy ControlNet"
  ]
}
```

### Complete Lineage Workflow Example

```javascript
import {
  createLineageMetadata,
  createAssetLineageTag,
  createLineageRecord,
  saveLineageRecord,
  computeFileChecksum
} from './utils.js';

async function trackGenerationRun(jobConfig, generatedAssets, validations) {
  // 1. Create lineage metadata
  const lineage = createLineageMetadata({
    jobId: jobConfig.id,
    branch: jobConfig.lineage?.branch || 'main',
    parent: jobConfig.lineage?.parent || null,
    metadata: {
      outputType: jobConfig.output_type,
      passes: jobConfig.passes
    }
  });

  // 2. Tag each asset
  const assetTags = await Promise.all(
    generatedAssets.map(async (assetPath) => {
      const tag = createAssetLineageTag({
        assetPath,
        lineageId: lineage.lineage_id,
        jobId: jobConfig.id,
        status: 'generated'
      });

      // Compute checksum
      tag.checksum = await computeFileChecksum(assetPath);

      return tag;
    })
  );

  // 3. Create complete record
  const record = createLineageRecord({
    lineageMetadata: lineage,
    jobConfig,
    assets: assetTags,
    validations,
    executionMetrics: {
      startTime: lineage.created_at,
      endTime: new Date().toISOString(),
      durationMs: Date.now() - new Date(lineage.created_at).getTime(),
      status: 'completed'
    }
  });

  // 4. Save to disk
  const savedPath = await saveLineageRecord(record);

  logger.info('Lineage tracking complete', {
    runId: lineage.lineage_id,
    assetsCount: assetTags.length,
    savedPath
  });

  return record;
}
```

---

## Config Validation

### Enhanced Job Config Validation

```javascript
import { validateJobConfig } from './utils.js';

const config = {
  id: 'job-123',
  output_type: 'character',
  passes: 8, // Will trigger warning
  consistency_threshold: 0.98, // Will trigger warning
  references: {
    palettes: ['palette.png'],
    embeddings: ['style.pt']
  }
};

const result = await validateJobConfig(config);

if (!result.valid) {
  console.error('Validation errors:', result.errors);
}

if (result.warnings.length > 0) {
  console.warn('Warnings:', result.warnings);
}
```

**Output:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    {
      "field": "passes",
      "message": "High number of passes may significantly increase generation time",
      "value": 8
    },
    {
      "field": "consistency_threshold",
      "message": "Very high consistency threshold may be difficult to achieve",
      "value": 0.98
    }
  ]
}
```

### Batch Config Validation

```javascript
import { validateConfigBatch } from './utils.js';

const configs = [
  { id: 'job-1', output_type: 'character', passes: 3 },
  { id: 'job-2', output_type: 'invalid', passes: 3 }, // Invalid
  { id: 'job-3', output_type: 'environment', passes: 5 }
];

const results = await validateConfigBatch(configs, 'job.schema.json');

results.forEach(result => {
  if (!result.valid) {
    console.error(`Config ${result.index} failed:`, result.errors);
  }
});
```

### Sanitize Config

```javascript
import { sanitizeConfig } from './utils.js';

const unsafeConfig = {
  id: 'job-123',
  output_type: 'character',
  passes: 3,
  __proto__: 'malicious', // Will be removed
  _internal: 'secret' // Will be removed
};

const allowedFields = ['id', 'output_type', 'passes', 'style_tags'];
const safe = sanitizeConfig(unsafeConfig, allowedFields);

console.log(safe);
// { id: 'job-123', output_type: 'character', passes: 3 }
```

### Merge Configs

```javascript
import { mergeConfigs } from './utils.js';

const baseConfig = {
  output_type: 'character',
  passes: 3,
  consistency_threshold: 0.8,
  references: {
    palettes: ['base.png']
  }
};

const overrideConfig = {
  passes: 5,
  consistency_threshold: 0.9,
  references: {
    embeddings: ['style.pt']
  }
};

const merged = mergeConfigs(baseConfig, overrideConfig, ['output_type']);

console.log(merged);
```

**Output:**
```json
{
  "output_type": "character",
  "passes": 5,
  "consistency_threshold": 0.9,
  "references": {
    "palettes": ["base.png"],
    "embeddings": ["style.pt"]
  }
}
```

---

## Python Script Execution

### Execute Python Script

```javascript
import { executePythonScript } from './utils.js';

const result = await executePythonScript(
  'scripts/generate.py',
  ['--output', 'output/', '--style', 'anime'],
  {
    timeout: 600000, // 10 minutes
    cwd: '/path/to/project'
  }
);

if (result.exitCode === 0) {
  console.log('Success:', result.stdout);
} else {
  console.error('Failed:', result.stderr);
}
```

### Build Python Command

```javascript
import { buildPythonCommand } from './utils.js';

const cmd = buildPythonCommand(
  'vaultmind_forge/forge_cli.py',
  ['run-demo', '--output-dir', 'demo'],
  {
    env: { PYTHONPATH: '/custom/path' },
    timeout: 300000
  }
);

console.log('Command:', cmd.command);
console.log('Args:', cmd.args);
console.log('Options:', cmd.options);
```

### Parse JSON from Python Output

```javascript
import { parsePythonJSON } from './utils.js';

const pythonOutput = `
Starting generation...
{"status": "completed", "assets": ["img1.png", "img2.png"]}
Process finished.
`;

const data = parsePythonJSON(pythonOutput);
console.log(data.status); // "completed"
console.log(data.assets); // ["img1.png", "img2.png"]

// Strict mode (throws if no JSON found)
try {
  const strictData = parsePythonJSON('No JSON here', true);
} catch (error) {
  console.error('No JSON found:', error.message);
}
```

### Parse Key-Value Pairs

```javascript
import { parsePythonKeyValue } from './utils.js';

const output = `
Version: 0.1.0
Status: Running
Assets: 5
Duration: 120s
`;

const data = parsePythonKeyValue(output);
console.log(data);
```

**Output:**
```json
{
  "Version": "0.1.0",
  "Status": "Running",
  "Assets": "5",
  "Duration": "120s"
}
```

### Validate Python Output

```javascript
import { validatePythonOutput } from './utils.js';

const output = '{"status": "completed", "result": "success"}';

const validation = validatePythonOutput(output, {
  requireJSON: true,
  requiredKeys: ['status', 'result'],
  minLength: 10
});

if (!validation.valid) {
  console.error('Output validation failed:', validation.errors);
}
```

### Complete Python Integration Example

```javascript
import {
  executePythonScript,
  parsePythonJSON,
  validatePythonOutput
} from './utils.js';

async function runGenerationScript(config) {
  // 1. Execute script
  const result = await executePythonScript(
    'scripts/generate.py',
    ['--config', JSON.stringify(config)],
    { timeout: 600000 }
  );

  if (result.exitCode !== 0) {
    throw new Error(`Script failed: ${result.stderr}`);
  }

  // 2. Validate output
  const validation = validatePythonOutput(result.stdout, {
    requireJSON: true,
    requiredKeys: ['assets', 'status']
  });

  if (!validation.valid) {
    throw new Error(`Invalid output: ${validation.errors.join(', ')}`);
  }

  // 3. Parse JSON result
  const data = parsePythonJSON(result.stdout, true);

  logger.info('Generation complete', {
    assetsCount: data.assets.length,
    status: data.status
  });

  return data;
}
```

---

## File Operations

### Read/Write JSON

```javascript
import { readJSON, writeJSON } from './utils.js';

// Read
const config = await readJSON('config/settings.json');

// Write
await writeJSON('output/result.json', {
  status: 'completed',
  timestamp: new Date().toISOString()
});
```

### File Operations

```javascript
import {
  fileExists,
  getFileSize,
  listFiles,
  ensureJobOutputDir
} from './utils.js';

// Check existence
if (await fileExists('config.json')) {
  console.log('Config exists');
}

// Get size
const size = await getFileSize('large_file.zip');
console.log('Size:', formatBytes(size));

// List files with filter
const pngFiles = await listFiles('./output', /\.png$/);
console.log('PNG files:', pngFiles);

// Create job directory
const outputDir = await ensureJobOutputDir('job-123');
console.log('Output directory:', outputDir);
```

---

## Job Creation

### Create Full Job Config

```javascript
import { createJobConfig, OUTPUT_TYPES } from './utils.js';

const job = createJobConfig({
  outputType: 'character',
  styleTags: ['anime', 'cel-shaded'],
  passes: 3,
  consistencyThreshold: 0.85,
  references: {
    palettes: ['palette.png'],
    styleGuides: ['guide.pdf']
  },
  lineage: {
    branch: 'experimental',
    parent: 'parent-job-id'
  }
});

console.log('Job ID:', job.id);
console.log('Valid types:', OUTPUT_TYPES);
```

### Create Simple Job

```javascript
import { createSimpleJob } from './utils.js';

const simple = createSimpleJob({
  name: 'hero-character',
  style: 'photoreal',
  target: [1024, 1024],
  meta: {
    project: 'Game Alpha',
    artist: 'John Doe'
  }
});
```

---

## Logging

### Structured Logging

```javascript
import { logger } from './utils.js';

// Info
logger.info('Job started', { jobId: '123', outputType: 'character' });

// Warning
logger.warn('High memory usage', { memoryMB: 2048 });

// Error
logger.error('Validation failed', {
  jobId: '123',
  error: 'Score too low',
  score: 0.45
});

// Debug
logger.debug('Processing asset', { path: 'output/img.png' });
```

**Output:**
```json
{
  "level": "INFO",
  "message": "Job started",
  "timestamp": "2025-10-30T12:00:00.000Z",
  "jobId": "123",
  "outputType": "character"
}
```

---

## Complete Integration Example

Here's a complete example combining all utilities:

```javascript
import {
  // Job creation
  createJobConfig,
  validateJobConfig,

  // Lineage tracking
  createLineageMetadata,
  createAssetLineageTag,
  createLineageRecord,
  saveLineageRecord,
  computeFileChecksum,

  // Python execution
  executePythonScript,
  parsePythonJSON,

  // File operations
  ensureJobOutputDir,
  listFiles,

  // Response & logging
  successResponse,
  errorResponse,
  ForgeAPIError,
  logger
} from './utils.js';

async function completeGenerationWorkflow(requestConfig) {
  try {
    // 1. Create and validate job config
    const jobConfig = createJobConfig(requestConfig);
    const validation = await validateJobConfig(jobConfig);

    if (!validation.valid) {
      throw new ForgeAPIError('Invalid config', 400, {
        errors: validation.errors
      });
    }

    if (validation.warnings.length > 0) {
      logger.warn('Config warnings', { warnings: validation.warnings });
    }

    // 2. Create lineage metadata
    const lineage = createLineageMetadata({
      jobId: jobConfig.id,
      branch: jobConfig.lineage.branch,
      parent: jobConfig.lineage.parent,
      metadata: { outputType: jobConfig.output_type }
    });

    // 3. Create output directory
    const outputDir = await ensureJobOutputDir(jobConfig.id);

    // 4. Execute Python generation script
    logger.info('Starting generation', { jobId: jobConfig.id });
    const startTime = Date.now();

    const result = await executePythonScript(
      'scripts/generate.py',
      ['--config', JSON.stringify(jobConfig), '--output', outputDir]
    );

    const generationData = parsePythonJSON(result.stdout, true);

    // 5. List generated assets
    const assets = await listFiles(outputDir, /\.(png|jpg)$/);

    // 6. Create asset tags with checksums
    const assetTags = await Promise.all(
      assets.map(async (assetPath) => {
        const tag = createAssetLineageTag({
          assetPath,
          lineageId: lineage.lineage_id,
          jobId: jobConfig.id,
          status: 'generated'
        });
        tag.checksum = await computeFileChecksum(assetPath);
        return tag;
      })
    );

    // 7. Create and save lineage record
    const lineageRecord = createLineageRecord({
      lineageMetadata: lineage,
      jobConfig,
      assets: assetTags,
      executionMetrics: {
        startTime: new Date(startTime).toISOString(),
        endTime: new Date().toISOString(),
        durationMs: Date.now() - startTime,
        status: 'completed'
      }
    });

    const lineagePath = await saveLineageRecord(lineageRecord);

    logger.info('Workflow completed', {
      jobId: jobConfig.id,
      assetsCount: assets.length,
      duration: Date.now() - startTime
    });

    // 8. Return success response
    return successResponse({
      jobId: jobConfig.id,
      lineageId: lineage.lineage_id,
      assets: assetTags,
      lineagePath,
      executionTime: Date.now() - startTime
    }, 'Generation completed successfully');

  } catch (error) {
    logger.error('Workflow failed', {
      error: error.message,
      stack: error.stack
    });

    if (error instanceof ForgeAPIError) {
      throw error;
    }

    throw new ForgeAPIError(
      'Workflow execution failed',
      500,
      { originalError: error.message }
    );
  }
}

// Usage
const response = await completeGenerationWorkflow({
  outputType: 'character',
  styleTags: ['anime', 'cel-shaded'],
  passes: 3,
  consistencyThreshold: 0.85
});

console.log(response);
```

---

## Quick Reference

### Most Commonly Used Functions

```javascript
// Response formatting
successResponse(data, message)
errorResponse(message, code, details)

// Error handling
throw new ForgeAPIError(message, statusCode, details)

// Lineage tracking
createLineageMetadata({ jobId, branch, parent, metadata })
createAssetLineageTag({ assetPath, lineageId, jobId, status, metrics })
saveLineageRecord(lineageRecord, outputDir)
queryLineageRecords({ jobId, branch, status })

// Config validation
validateJobConfig(config) // Returns { valid, errors, warnings }
sanitizeConfig(config, allowedFields)
mergeConfigs(baseConfig, overrideConfig, immutableFields)

// Python execution
executePythonScript(scriptPath, args, options)
parsePythonJSON(output, strict)
validatePythonOutput(output, expectations)

// File operations
readJSON(filePath)
writeJSON(filePath, data)
ensureJobOutputDir(jobId)
computeFileChecksum(filePath)

// Logging
logger.info(message, metadata)
logger.error(message, metadata)
```

---

## Summary

The enhanced `utils.js` now includes **60+ utility functions** organized into:

- ✅ **Response Formatting** - Standardized API responses
- ✅ **Error Handling** - Custom errors and async wrappers
- ✅ **Lineage Tagging** - Complete asset tracking system ⭐ NEW
- ✅ **Config Validation** - Enhanced validation with warnings ⭐ ENHANCED
- ✅ **Python Integration** - Script execution and parsing ⭐ NEW
- ✅ **File Operations** - JSON, checksums, file management
- ✅ **Job Creation** - Validated job configurations
- ✅ **Logging** - Structured JSON logging

All functions are fully documented with JSDoc and include type information for better IDE support.
