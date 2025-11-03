# VaultMind Forge - Node.js API Layer

Node.js REST API wrapper for the VaultMind Forge Python backend, providing a modern HTTP interface for AI-powered asset generation and validation.

## Overview

This Node.js layer provides:
- **RESTful API** for VaultMind Forge operations
- **Async job execution** with status tracking
- **File upload handling** for asset validation
- **JSON Schema validation** for job configurations
- **Comprehensive utility functions** for integration

## Architecture

```
┌─────────────────────────────────────────┐
│         Node.js API Layer               │
│  ┌────────────┐      ┌───────────────┐ │
│  │  Express   │◄─────┤   Handlers    │ │
│  │   Server   │      │  (REST API)   │ │
│  └────────────┘      └───────────────┘ │
│         ▲                    │          │
│         │                    ▼          │
│         │            ┌───────────────┐  │
│         │            │ Python Bridge │  │
│         │            │  (CLI Exec)   │  │
│         │            └───────────────┘  │
└─────────┼──────────────────┼────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────┐
│      VaultMind Forge Python Backend     │
│   (forge_cli.py, diffusion, validator)  │
└─────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Node.js 18+
- Python 3.10+ with VaultMind Forge installed
- VaultMind Forge Python backend configured

### Setup

```bash
# Install Node.js dependencies
npm install

# Run in development mode
npm run dev

# Run in production mode
npm start
```

## API Endpoints

### Health & Info

#### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "success": true,
  "message": "API is running",
  "data": { "status": "healthy" },
  "timestamp": "2025-10-30T12:00:00.000Z"
}
```

#### `GET /api/version`
Get VaultMind Forge version.

**Response:**
```json
{
  "success": true,
  "data": { "version": "0.1.0" }
}
```

#### `GET /api/status`
Get system status and available modules.

**Response:**
```json
{
  "success": true,
  "data": {
    "root": "C:\\Projects\\LPG",
    "modules": ["forge_agent", "forge_diffusion", "forge_validator", ...]
  }
}
```

### Job Management

#### `POST /api/jobs`
Create and execute a generation job asynchronously.

**Request Body:**
```json
{
  "outputType": "character",
  "styleTags": ["cel-shaded", "anime"],
  "passes": 3,
  "consistencyThreshold": 0.8,
  "async": true,
  "references": {
    "palettes": ["palette1.png"],
    "embeddings": ["style_embedding.pt"],
    "styleGuides": ["guide.pdf"]
  },
  "lineage": {
    "branch": "main",
    "parent": "uuid-of-parent-job"
  }
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Job queued for execution",
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "queued",
    "statusUrl": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/status"
  }
}
```

**Valid Output Types:**
- `storyboard`, `game_asset`, `environment`, `character`, `video`
- `advert`, `film`, `ui`, `product`, `archviz`, `cad`, `education`, `print`

#### `POST /api/jobs/simple`
Create a simple generation job configuration (for Planner).

**Request Body:**
```json
{
  "name": "hero-character",
  "style": "cel-shaded",
  "target": [1024, 1024],
  "refs": [],
  "meta": {
    "artist": "John Doe",
    "project": "Game Alpha"
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "name": "hero-character",
    "style": "cel-shaded",
    "target": [1024, 1024],
    "refs": [],
    "meta": {
      "artist": "John Doe",
      "project": "Game Alpha",
      "createdAt": "2025-10-30T12:00:00.000Z",
      "jobId": "..."
    }
  }
}
```

#### `GET /api/jobs/:jobId/status`
Get job execution status.

**Response:**
```json
{
  "success": true,
  "data": {
    "jobId": "550e8400-...",
    "status": "running",
    "progress": 45,
    "outputDir": "output/550e8400-.../",
    "startedAt": "2025-10-30T12:00:00.000Z",
    "updatedAt": "2025-10-30T12:01:30.000Z"
  }
}
```

**Job Statuses:**
- `queued` - Job is queued for execution
- `running` - Job is currently executing
- `completed` - Job finished successfully
- `failed` - Job failed with errors

#### `GET /api/jobs`
List all jobs.

**Response:**
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "jobId": "...",
        "status": "completed",
        "progress": 100,
        "outputDir": "output/...",
        "startedAt": "...",
        "completedAt": "..."
      }
    ],
    "count": 1
  }
}
```

#### `GET /api/jobs/:jobId/outputs`
Get output files from a completed job.

**Response:**
```json
{
  "success": true,
  "data": {
    "jobId": "550e8400-...",
    "outputDir": "output/550e8400-.../",
    "files": [
      {
        "path": "output/.../image_001.png",
        "filename": "image_001.png"
      }
    ],
    "count": 1
  }
}
```

### Asset Validation

#### `POST /api/validate`
Validate uploaded image files.

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `files` - One or more image files (max 10 files, 50MB each)

**Response:**
```json
{
  "success": true,
  "data": {
    "validations": [
      {
        "file": "uploads/temp/image-123456789.png",
        "status": "PASS",
        "score": 0.85,
        "passed": true,
        "metrics": {},
        "timestamp": "2025-10-30T12:00:00.000Z"
      }
    ],
    "summary": {
      "total": 1,
      "passed": 1,
      "failed": 0
    }
  }
}
```

#### `POST /api/validate/paths`
Validate assets by file path.

**Request Body:**
```json
{
  "paths": [
    "C:\\path\\to\\image1.png",
    "C:\\path\\to\\image2.png"
  ]
}
```

**Response:** Same format as `/api/validate`

### Demo Pipeline

#### `POST /api/demo`
Run the demo pipeline (plan → generate → validate → package → archive).

**Request Body:**
```json
{
  "outputDir": "demo_output_custom"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Demo completed",
  "data": {
    "outputDir": "demo_output_custom",
    "message": "Demo pipeline completed successfully"
  }
}
```

## Utility Functions (`src/utils.js`)

### Path & File Operations

```javascript
import {
  getProjectRoot,
  ensureJobOutputDir,
  fileExists,
  readJSON,
  writeJSON,
  listFiles
} from './utils.js';

// Get project root
const root = getProjectRoot();

// Create job output directory
const outputDir = await ensureJobOutputDir('job-id-123');

// Check if file exists
const exists = await fileExists('/path/to/file.json');

// Read/write JSON
const data = await readJSON('/path/to/file.json');
await writeJSON('/path/to/output.json', { foo: 'bar' });

// List files with filter
const pngFiles = await listFiles('./output', /\.png$/);
```

### JSON Schema Validation

```javascript
import { validateAgainstSchema } from './utils.js';

const jobData = {
  id: 'uuid',
  output_type: 'character',
  passes: 3
};

const { valid, errors } = await validateAgainstSchema(jobData, 'job.schema.json');

if (!valid) {
  console.error('Validation errors:', errors);
}
```

### Job Creation

```javascript
import { createJobConfig, createSimpleJob, OUTPUT_TYPES } from './utils.js';

// Create full job config
const job = createJobConfig({
  outputType: 'character',
  styleTags: ['anime', 'cel-shaded'],
  passes: 5,
  consistencyThreshold: 0.9
});

// Create simple job
const simpleJob = createSimpleJob({
  name: 'my-character',
  style: 'photoreal',
  target: [1024, 1024]
});

// List valid output types
console.log(OUTPUT_TYPES);
```

### Response Formatting

```javascript
import { successResponse, errorResponse, ForgeAPIError } from './utils.js';

// Success response
res.json(successResponse({ id: 123 }, 'Resource created'));

// Error response
res.status(400).json(errorResponse('Invalid input', 400, { field: 'email' }));

// Throw custom error
throw new ForgeAPIError('Job not found', 404);
```

### Error Handling

```javascript
import { asyncHandler } from './utils.js';

// Wrap async route handlers
router.get('/resource', asyncHandler(async (req, res) => {
  const data = await fetchData();
  res.json(successResponse(data));
}));
```

### Logging

```javascript
import { logger } from './utils.js';

logger.info('Operation completed', { userId: 123 });
logger.warn('Low disk space', { available: '10GB' });
logger.error('Database connection failed', { error: err.message });
logger.debug('Debug info', { data: debugData });
```

### Helpers

```javascript
import { formatBytes, sleep, generateJobId } from './utils.js';

// Format bytes
console.log(formatBytes(1536)); // "1.5 KB"

// Delay execution
await sleep(1000); // Sleep for 1 second

// Generate UUID
const jobId = generateJobId(); // "550e8400-e29b-41d4-a716-446655440000"
```

## Python Bridge (`src/pythonBridge.js`)

Execute VaultMind Forge Python commands from Node.js:

```javascript
import {
  getVersion,
  getStatus,
  runDemo,
  validateAssets,
  executeJobAsync,
  getJobStatus
} from './pythonBridge.js';

// Get version
const { version } = await getVersion();

// Run demo
const result = await runDemo('my_demo_output');

// Validate assets
const validations = await validateAssets([
  'path/to/image1.png',
  'path/to/image2.png'
]);

// Execute job asynchronously
const jobId = await executeJobAsync(jobConfig, outputDir);

// Check job status
const status = getJobStatus(jobId);
console.log(status.status); // 'queued' | 'running' | 'completed' | 'failed'
```

## Environment Variables

Create a `.env` file (optional):

```env
PORT=3000
HOST=0.0.0.0
NODE_ENV=development
CORS_ORIGIN=*
```

## Example Usage

### cURL Examples

```bash
# Health check
curl http://localhost:3000/api/health

# Get version
curl http://localhost:3000/api/version

# Create job
curl -X POST http://localhost:3000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "outputType": "character",
    "styleTags": ["anime"],
    "passes": 3,
    "async": true
  }'

# Check job status
curl http://localhost:3000/api/jobs/{jobId}/status

# Validate files
curl -X POST http://localhost:3000/api/validate/paths \
  -H "Content-Type: application/json" \
  -d '{"paths": ["output/image.png"]}'
```

### JavaScript Client Example

```javascript
const API_BASE = 'http://localhost:3000/api';

// Create a job
async function createGenerationJob() {
  const response = await fetch(`${API_BASE}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      outputType: 'character',
      styleTags: ['cel-shaded', 'anime'],
      passes: 3,
      async: true
    })
  });

  const result = await response.json();
  return result.data.jobId;
}

// Poll job status
async function waitForJob(jobId) {
  while (true) {
    const response = await fetch(`${API_BASE}/jobs/${jobId}/status`);
    const result = await response.json();
    const status = result.data.status;

    if (status === 'completed') {
      return result.data;
    } else if (status === 'failed') {
      throw new Error('Job failed');
    }

    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5s
  }
}

// Full workflow
const jobId = await createGenerationJob();
console.log('Job created:', jobId);

const completedJob = await waitForJob(jobId);
console.log('Job completed:', completedJob);
```

## Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "message": "Error description",
    "code": 400,
    "timestamp": "2025-10-30T12:00:00.000Z",
    "details": {
      "field": "additionalInfo"
    }
  }
}
```

**Common Error Codes:**
- `400` - Bad Request (validation errors, missing fields)
- `404` - Not Found (job/resource not found)
- `413` - Payload Too Large (file size exceeded)
- `408` - Request Timeout (job execution timeout)
- `500` - Internal Server Error
- `501` - Not Implemented

## File Structure

```
LPG/
├── src/
│   ├── server.js           # Express server & startup
│   ├── handlers.js         # API route handlers
│   ├── pythonBridge.js     # Python CLI integration
│   └── utils.js            # Utility functions (YOU ARE HERE)
├── package.json            # Node.js dependencies
├── NODE_API_README.md      # This file
└── vaultmind_forge/        # Python backend
    ├── forge_cli.py
    ├── config/schemas/
    └── ...
```

## Development

```bash
# Install dependencies
npm install

# Run development server (auto-restart on changes)
npm run dev

# Run production server
npm start

# Run tests (when implemented)
npm test
```

## Production Deployment

1. Ensure Python backend is installed and configured
2. Set environment variables for production
3. Use a process manager (PM2, systemd)
4. Set up reverse proxy (nginx, Apache)
5. Enable HTTPS with SSL certificates

```bash
# Example with PM2
npm install -g pm2
pm2 start src/server.js --name vaultmind-api
pm2 startup
pm2 save
```

## License

Same as VaultMind Forge parent project.

## Contributing

See main project documentation.
