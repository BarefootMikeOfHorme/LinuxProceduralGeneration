/**
 * VaultMind Forge - API Route Handlers
 *
 * All 11 REST API endpoint handlers
 */

import { v4 as uuidv4 } from 'uuid';
import path from 'path';
import { fileURLToPath } from 'url';
import multer from 'multer';
import {
  logger,
  validateJobConfig,
  validateGenerationOptions,
  createJobConfig,
  generateJobId,
  queryLineageRecords,
  readLineageRecord,
  executePythonScript,
  formatErrorResponse,
  formatSuccessResponse
} from './utils.js';
import { DiffusionGenerator } from './forge/diffusion.js';
import { AssetValidator } from './forge/validator.js';
import { AssetPackager } from './forge/packager.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============================================================================
// FILE UPLOAD CONFIGURATION
// ============================================================================

const upload = multer({
  dest: 'uploads/',
  limits: { fileSize: 100 * 1024 * 1024 }, // 100MB limit
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|gif|bmp|tiff|webp/;
    const mimetype = allowedTypes.test(file.mimetype);
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());

    if (mimetype && extname) {
      return cb(null, true);
    }
    cb(new Error('Invalid file type. Only images are allowed.'));
  }
});

// ============================================================================
// HEALTH & SYSTEM HANDLERS
// ============================================================================

/**
 * GET /api/health
 * Health check endpoint
 */
export async function handleHealth(req, res) {
  try {
    // Check Python backend availability
    const pythonAvailable = await checkPythonBackend();

    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        api: 'running',
        python: pythonAvailable ? 'available' : 'unavailable'
      },
      uptime: process.uptime(),
      memory: {
        used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
        total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
        unit: 'MB'
      }
    });
  } catch (error) {
    logger.error('Health check failed:', error);
    res.status(503).json(formatErrorResponse('Service Unavailable', error.message));
  }
}

/**
 * GET /api/version
 * Get API version
 */
export function handleVersion(req, res) {
  res.json({
    name: 'VaultMind Forge API',
    version: '0.4.1',
    apiVersion: 'v1',
    pythonBackend: '0.1.0',
    nodeVersion: process.version
  });
}

/**
 * GET /api/status
 * Get system status with detailed metrics
 */
export async function handleStatus(req, res) {
  try {
    const pythonAvailable = await checkPythonBackend();

    res.json({
      status: 'running',
      timestamp: new Date().toISOString(),
      services: {
        api: {
          status: 'running',
          version: '0.4.1',
          uptime: process.uptime()
        },
        python: {
          status: pythonAvailable ? 'available' : 'unavailable',
          backend: 'vaultmind_forge'
        }
      },
      system: {
        platform: process.platform,
        arch: process.arch,
        nodeVersion: process.version,
        memory: process.memoryUsage(),
        cpuUsage: process.cpuUsage()
      }
    });
  } catch (error) {
    logger.error('Status check failed:', error);
    res.status(500).json(formatErrorResponse('Status Check Failed', error.message));
  }
}

// ============================================================================
// DIFFUSION GENERATION HANDLERS
// ============================================================================

/**
 * POST /api/diffusion/generate
 * Simple or multi-pass generation
 */
export async function handleGenerateDiffusion(req, res) {
  try {
    const { jobConfig, multiPass = false, passes = 1, backend = 'placeholder' } = req.body;

    // Validate inputs
    if (!jobConfig) {
      return res.status(400).json(formatErrorResponse('Validation Error', 'jobConfig is required'));
    }

    const validation = validateJobConfig(jobConfig);
    if (!validation.valid) {
      return res.status(400).json(formatErrorResponse('Validation Error', validation.errors.join(', ')));
    }

    // Initialize generator
    const generator = new DiffusionGenerator({ mode: backend });

    // Execute generation
    logger.info(`Starting generation: ${jobConfig.id || 'anonymous'}`);
    const result = await generator.generate(jobConfig, {
      multiPass,
      passes,
      outputDir: path.join(__dirname, '..', 'output', jobConfig.id || generateJobId())
    });

    res.json(formatSuccessResponse('Generation completed', result));
  } catch (error) {
    logger.error('Generation failed:', error);
    res.status(500).json(formatErrorResponse('Generation Failed', error.message));
  }
}

/**
 * POST /api/diffusion/generate-with-lineage
 * Full workflow with lineage tracking
 */
export async function handleGenerateWithLineage(req, res) {
  try {
    const {
      jobConfig,
      multiPass = true,
      passes = 3,
      backend = 'placeholder',
      packageAssets = true,
      validateAssets = true
    } = req.body;

    // Validate inputs
    if (!jobConfig) {
      return res.status(400).json(formatErrorResponse('Validation Error', 'jobConfig is required'));
    }

    const validation = validateJobConfig(jobConfig);
    if (!validation.valid) {
      return res.status(400).json(formatErrorResponse('Validation Error', validation.errors.join(', ')));
    }

    // Initialize components
    const generator = new DiffusionGenerator({ mode: backend });
    const validator = validateAssets ? new AssetValidator({ mode: 'basic' }) : null;
    const packager = packageAssets ? new AssetPackager() : null;

    // Execute full workflow
    logger.info(`Starting workflow with lineage: ${jobConfig.id}`);

    const result = await generator.generateWithLineage(
      jobConfig,
      path.join(__dirname, '..', 'output', jobConfig.id),
      {
        multiPass,
        passes,
        validator: validator ? async (assetPath) => validator.validate(assetPath) : null,
        packageAssets: !!packager
      }
    );

    // Package if requested
    if (packager && result.winner) {
      const packageResult = await packager.package([result.winner], {
        outputDir: path.join(__dirname, '..', 'output', jobConfig.id),
        includeMeta: true
      });
      result.package = packageResult;
    }

    res.json(formatSuccessResponse('Workflow completed with lineage', result));
  } catch (error) {
    logger.error('Workflow failed:', error);
    res.status(500).json(formatErrorResponse('Workflow Failed', error.message));
  }
}

// ============================================================================
// VALIDATION HANDLERS
// ============================================================================

/**
 * POST /api/validate
 * Validate uploaded files (multipart)
 */
export const handleValidate = [
  upload.array('files', 10),
  async (req, res) => {
    try {
      if (!req.files || req.files.length === 0) {
        return res.status(400).json(formatErrorResponse('Validation Error', 'No files uploaded'));
      }

      const validator = new AssetValidator({ mode: 'basic' });
      const results = [];

      for (const file of req.files) {
        const result = await validator.validate(file.path);
        results.push({
          filename: file.originalname,
          ...result
        });
      }

      res.json(formatSuccessResponse('Validation completed', { results }));
    } catch (error) {
      logger.error('Validation failed:', error);
      res.status(500).json(formatErrorResponse('Validation Failed', error.message));
    }
  }
];

/**
 * POST /api/validate/paths
 * Validate files by path
 */
export async function handleValidatePaths(req, res) {
  try {
    const { paths, backend = 'basic' } = req.body;

    if (!paths || !Array.isArray(paths)) {
      return res.status(400).json(formatErrorResponse('Validation Error', 'paths array is required'));
    }

    const validator = new AssetValidator({ mode: backend });
    const results = [];

    for (const filePath of paths) {
      const result = await validator.validate(filePath);
      results.push({
        path: filePath,
        ...result
      });
    }

    res.json(formatSuccessResponse('Validation completed', { results }));
  } catch (error) {
    logger.error('Path validation failed:', error);
    res.status(500).json(formatErrorResponse('Path Validation Failed', error.message));
  }
}

// ============================================================================
// LINEAGE HANDLERS
// ============================================================================

/**
 * GET /api/lineage?jobId=&branch=&status=
 * Query lineage records
 */
export async function handleQueryLineage(req, res) {
  try {
    const { jobId, branch, status } = req.query;

    const records = await queryLineageRecords({
      jobId,
      branch,
      status
    });

    res.json(formatSuccessResponse('Lineage query completed', {
      count: records.length,
      records
    }));
  } catch (error) {
    logger.error('Lineage query failed:', error);
    res.status(500).json(formatErrorResponse('Lineage Query Failed', error.message));
  }
}

/**
 * GET /api/lineage/:runId
 * Get single lineage record
 */
export async function handleGetLineageRecord(req, res) {
  try {
    const { runId } = req.params;

    if (!runId) {
      return res.status(400).json(formatErrorResponse('Validation Error', 'runId is required'));
    }

    const record = await readLineageRecord(runId);

    if (!record) {
      return res.status(404).json(formatErrorResponse('Not Found', `Lineage record ${runId} not found`));
    }

    res.json(formatSuccessResponse('Lineage record retrieved', record));
  } catch (error) {
    logger.error('Lineage retrieval failed:', error);
    res.status(500).json(formatErrorResponse('Lineage Retrieval Failed', error.message));
  }
}

// ============================================================================
// JOB MANAGEMENT HANDLERS
// ============================================================================

// In-memory job store (replace with database in production)
const jobs = new Map();

/**
 * POST /api/jobs
 * Create async job
 */
export async function handleCreateJob(req, res) {
  try {
    const { type, config } = req.body;

    if (!type || !config) {
      return res.status(400).json(formatErrorResponse('Validation Error', 'type and config are required'));
    }

    const jobId = generateJobId();
    const job = {
      id: jobId,
      type,
      config,
      status: 'pending',
      createdAt: new Date().toISOString(),
      outputs: []
    };

    jobs.set(jobId, job);

    // Start async processing
    processJobAsync(jobId, type, config);

    res.status(202).json(formatSuccessResponse('Job created', {
      jobId,
      status: 'pending',
      statusUrl: `/api/jobs/${jobId}/status`
    }));
  } catch (error) {
    logger.error('Job creation failed:', error);
    res.status(500).json(formatErrorResponse('Job Creation Failed', error.message));
  }
}

/**
 * GET /api/jobs/:id/status
 * Get job status
 */
export function handleJobStatus(req, res) {
  try {
    const { id } = req.params;
    const job = jobs.get(id);

    if (!job) {
      return res.status(404).json(formatErrorResponse('Not Found', `Job ${id} not found`));
    }

    res.json(formatSuccessResponse('Job status retrieved', {
      id: job.id,
      type: job.type,
      status: job.status,
      createdAt: job.createdAt,
      completedAt: job.completedAt,
      error: job.error
    }));
  } catch (error) {
    logger.error('Job status retrieval failed:', error);
    res.status(500).json(formatErrorResponse('Job Status Retrieval Failed', error.message));
  }
}

/**
 * GET /api/jobs/:id/outputs
 * Get job outputs
 */
export function handleJobOutputs(req, res) {
  try {
    const { id } = req.params;
    const job = jobs.get(id);

    if (!job) {
      return res.status(404).json(formatErrorResponse('Not Found', `Job ${id} not found`));
    }

    if (job.status !== 'completed') {
      return res.status(400).json(formatErrorResponse('Invalid State', 'Job is not completed yet'));
    }

    res.json(formatSuccessResponse('Job outputs retrieved', {
      id: job.id,
      outputs: job.outputs
    }));
  } catch (error) {
    logger.error('Job outputs retrieval failed:', error);
    res.status(500).json(formatErrorResponse('Job Outputs Retrieval Failed', error.message));
  }
}

// ============================================================================
// DEMO HANDLER
// ============================================================================

/**
 * POST /api/demo
 * Run demo pipeline
 */
export async function handleDemo(req, res) {
  try {
    logger.info('Running demo pipeline...');

    const demoJobConfig = createJobConfig({
      outputType: 'character',
      styleTags: ['anime', 'demo'],
      passes: 2
    });

    const generator = new DiffusionGenerator({ mode: 'placeholder' });
    const validator = new AssetValidator({ mode: 'basic' });

    const result = await generator.generateWithLineage(
      demoJobConfig,
      path.join(__dirname, '..', 'output', 'demo'),
      {
        multiPass: true,
        passes: 2,
        validator: async (assetPath) => validator.validate(assetPath),
        packageAssets: true
      }
    );

    res.json(formatSuccessResponse('Demo completed', {
      message: 'Demo pipeline executed successfully',
      jobId: demoJobConfig.id,
      result
    }));
  } catch (error) {
    logger.error('Demo failed:', error);
    res.status(500).json(formatErrorResponse('Demo Failed', error.message));
  }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Check if Python backend is available
 */
async function checkPythonBackend() {
  try {
    const result = await executePythonScript('forge_cli.py', ['--version'], {
      timeout: 5000
    });
    return result.success;
  } catch (error) {
    logger.warn('Python backend check failed:', error.message);
    return false;
  }
}

/**
 * Process job asynchronously
 */
async function processJobAsync(jobId, type, config) {
  const job = jobs.get(jobId);
  if (!job) return;

  try {
    job.status = 'running';
    logger.info(`Processing job ${jobId} (${type})`);

    // Simulate processing based on type
    let result;
    switch (type) {
      case 'generation':
        const generator = new DiffusionGenerator({ mode: config.backend || 'placeholder' });
        result = await generator.generate(config);
        break;
      case 'validation':
        const validator = new AssetValidator({ mode: config.backend || 'basic' });
        result = await validator.validate(config.path);
        break;
      default:
        throw new Error(`Unknown job type: ${type}`);
    }

    job.status = 'completed';
    job.completedAt = new Date().toISOString();
    job.outputs = Array.isArray(result) ? result : [result];
    logger.info(`Job ${jobId} completed successfully`);
  } catch (error) {
    job.status = 'failed';
    job.error = error.message;
    job.completedAt = new Date().toISOString();
    logger.error(`Job ${jobId} failed:`, error);
  }
}
