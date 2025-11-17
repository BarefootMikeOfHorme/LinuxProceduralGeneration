/**
 * VaultMind Forge - Utility Functions
 *
 * 60+ helper functions for the Node.js API layer
 * Categories: Path manipulation, validation, logging, data processing, file operations
 */

import { createHash, randomBytes } from 'crypto';
import { promisify } from 'util';
import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';

const execAsync = promisify(exec);
const readFileAsync = promisify(fs.readFile);
const writeFileAsync = promisify(fs.writeFile);
const readdirAsync = promisify(fs.readdir);
const statAsync = promisify(fs.stat);

// ============================================================================
// LOGGING UTILITIES
// ============================================================================

/**
 * Simple logger with levels
 */
export const logger = {
  info: (...args) => console.log('[INFO]', new Date().toISOString(), ...args),
  warn: (...args) => console.warn('[WARN]', new Date().toISOString(), ...args),
  error: (...args) => console.error('[ERROR]', new Date().toISOString(), ...args),
  debug: (...args) => {
    if (process.env.DEBUG) console.log('[DEBUG]', new Date().toISOString(), ...args);
  }
};

/**
 * Format log message with context
 */
export function formatLogMessage(level, message, context = {}) {
  return JSON.stringify({
    timestamp: new Date().toISOString(),
    level,
    message,
    ...context
  });
}

// ============================================================================
// VALIDATION UTILITIES
// ============================================================================

/**
 * Validate job configuration
 */
export function validateJobConfig(config) {
  const errors = [];

  if (!config.id) errors.push('id is required');
  if (!config.output_type) errors.push('output_type is required');

  if (config.target) {
    if (!Array.isArray(config.target) || config.target.length !== 2) {
      errors.push('target must be [width, height] array');
    }
    if (config.target[0] % 64 !== 0 || config.target[1] % 64 !== 0) {
      errors.push('target dimensions must be multiples of 64');
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Validate generation options
 */
export function validateGenerationOptions(options) {
  const errors = [];

  if (options.passes && (options.passes < 1 || options.passes > 10)) {
    errors.push('passes must be between 1 and 10');
  }

  if (options.consistencyThreshold && (options.consistencyThreshold < 0 || options.consistencyThreshold > 1)) {
    errors.push('consistencyThreshold must be between 0 and 1');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Validate port number
 */
export function validatePort(port) {
  const p = parseInt(port, 10);
  return !isNaN(p) && p >= 1024 && p <= 65535;
}

/**
 * Validate file path
 */
export function validateFilePath(filePath) {
  try {
    return fs.existsSync(filePath);
  } catch (error) {
    return false;
  }
}

/**
 * Validate image format
 */
export function validateImageFormat(filename) {
  const allowedFormats = /\.(jpg|jpeg|png|gif|bmp|tiff|webp)$/i;
  return allowedFormats.test(filename);
}

/**
 * Validate JSON schema
 */
export function validateSchema(data, schema) {
  // Simple schema validation (use ajv for production)
  const errors = [];

  for (const [key, type] of Object.entries(schema)) {
    if (!(key in data)) {
      errors.push(`Missing required field: ${key}`);
    } else if (typeof data[key] !== type) {
      errors.push(`Field ${key} should be ${type}, got ${typeof data[key]}`);
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

// ============================================================================
// ID & HASH GENERATION
// ============================================================================

/**
 * Generate unique job ID
 */
export function generateJobId(prefix = 'job') {
  const timestamp = Date.now().toString(36);
  const random = randomBytes(4).toString('hex');
  return `${prefix}-${timestamp}-${random}`;
}

/**
 * Generate UUID
 */
export function generateUUID() {
  return uuidv4();
}

/**
 * Generate run ID
 */
export function generateRunId() {
  return `run-${uuidv4()}`;
}

/**
 * Generate lineage ID
 */
export function generateLineageId(jobId) {
  const hash = createHash('md5').update(jobId + Date.now()).digest('hex').substring(0, 8);
  return `lineage-${hash}`;
}

/**
 * Calculate file checksum (SHA-256)
 */
export async function calculateChecksum(filePath) {
  const hash = createHash('sha256');
  const data = await readFileAsync(filePath);
  hash.update(data);
  return hash.digest('hex');
}

/**
 * Calculate string hash
 */
export function hashString(str, algorithm = 'md5') {
  return createHash(algorithm).update(str).digest('hex');
}

// ============================================================================
// PATH UTILITIES
// ============================================================================

/**
 * Normalize path for cross-platform compatibility
 */
export function normalizePath(filePath) {
  return path.normalize(filePath).replace(/\\/g, '/');
}

/**
 * Resolve absolute path
 */
export function resolveAbsolutePath(filePath, basePath = process.cwd()) {
  return path.isAbsolute(filePath) ? filePath : path.resolve(basePath, filePath);
}

/**
 * Get file extension
 */
export function getFileExtension(filename) {
  return path.extname(filename).toLowerCase();
}

/**
 * Get filename without extension
 */
export function getBasename(filePath) {
  return path.basename(filePath, path.extname(filePath));
}

/**
 * Ensure directory exists
 */
export async function ensureDirectory(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
  return dirPath;
}

/**
 * Get relative path
 */
export function getRelativePath(from, to) {
  return path.relative(from, to);
}

/**
 * Join paths safely
 */
export function joinPaths(...paths) {
  return path.join(...paths);
}

/**
 * Get parent directory
 */
export function getParentDir(filePath) {
  return path.dirname(filePath);
}

/**
 * Sanitize filename
 */
export function sanitizeFilename(filename) {
  return filename.replace(/[^a-zA-Z0-9._-]/g, '_');
}

/**
 * Get unique filename
 */
export function getUniqueFilename(basePath, filename) {
  let counter = 1;
  let newFilename = filename;
  const ext = path.extname(filename);
  const base = path.basename(filename, ext);

  while (fs.existsSync(path.join(basePath, newFilename))) {
    newFilename = `${base}_${counter}${ext}`;
    counter++;
  }

  return newFilename;
}

// ============================================================================
// FILE OPERATIONS
// ============================================================================

/**
 * Read JSON file
 */
export async function readJSONFile(filePath) {
  const data = await readFileAsync(filePath, 'utf8');
  return JSON.parse(data);
}

/**
 * Write JSON file
 */
export async function writeJSONFile(filePath, data, pretty = true) {
  const json = pretty ? JSON.stringify(data, null, 2) : JSON.stringify(data);
  await writeFileAsync(filePath, json, 'utf8');
  return filePath;
}

/**
 * Copy file
 */
export async function copyFile(src, dest) {
  await fs.promises.copyFile(src, dest);
  return dest;
}

/**
 * Move file
 */
export async function moveFile(src, dest) {
  await fs.promises.rename(src, dest);
  return dest;
}

/**
 * Delete file
 */
export async function deleteFile(filePath) {
  if (fs.existsSync(filePath)) {
    await fs.promises.unlink(filePath);
    return true;
  }
  return false;
}

/**
 * List files in directory
 */
export async function listFiles(dirPath, filter = null) {
  const files = await readdirAsync(dirPath);
  return filter ? files.filter(filter) : files;
}

/**
 * Get file stats
 */
export async function getFileStats(filePath) {
  return await statAsync(filePath);
}

/**
 * Get file size in MB
 */
export async function getFileSizeMB(filePath) {
  const stats = await statAsync(filePath);
  return stats.size / (1024 * 1024);
}

/**
 * Check if path is directory
 */
export async function isDirectory(dirPath) {
  try {
    const stats = await statAsync(dirPath);
    return stats.isDirectory();
  } catch (error) {
    return false;
  }
}

/**
 * Check if path is file
 */
export async function isFile(filePath) {
  try {
    const stats = await statAsync(filePath);
    return stats.isFile();
  } catch (error) {
    return false;
  }
}

// ============================================================================
// JOB CONFIGURATION
// ============================================================================

/**
 * Create job configuration
 */
export function createJobConfig(options = {}) {
  return {
    id: options.id || generateJobId(),
    output_type: options.outputType || 'image',
    style_tags: options.styleTags || [],
    target: options.target || [1024, 1024],
    passes: options.passes || 1,
    consistencyThreshold: options.consistencyThreshold || 0.85,
    lineage: {
      branch: options.branch || 'main',
      parent: options.parent || null,
      metadata: options.metadata || {}
    },
    timestamp: new Date().toISOString(),
    ...options
  };
}

/**
 * Create generation options
 */
export function createGenerationOptions(options = {}) {
  return {
    multiPass: options.multiPass !== false,
    passes: options.passes || 3,
    outputDir: options.outputDir || './output',
    packageAssets: options.packageAssets !== false,
    validator: options.validator || null,
    backend: options.backend || 'placeholder'
  };
}

// ============================================================================
// LINEAGE UTILITIES
// ============================================================================

/**
 * Tag asset with lineage
 */
export function tagAssetWithLineage(assetPath, lineageId, jobId) {
  return {
    assetPath,
    lineageId,
    jobId,
    checksum: null, // Calculate on demand
    timestamp: new Date().toISOString()
  };
}

/**
 * Create lineage record
 */
export function createLineageRecord(jobConfig, assets = []) {
  return {
    version: '1.0',
    run_id: generateRunId(),
    timestamp: new Date().toISOString(),
    lineage: {
      lineage_id: generateLineageId(jobConfig.id),
      job_id: jobConfig.id,
      branch: jobConfig.lineage?.branch || 'main',
      parent: jobConfig.lineage?.parent || null,
      metadata: jobConfig.lineage?.metadata || {}
    },
    job: jobConfig,
    assets: assets,
    validations: [],
    rejections: [],
    execution: {
      start_time: new Date().toISOString(),
      end_time: null,
      duration_ms: null,
      status: 'running'
    },
    system: {
      platform: process.platform,
      arch: process.arch,
      node_version: process.version,
      memory_used_mb: Math.round(process.memoryUsage().heapUsed / 1024 / 1024)
    }
  };
}

/**
 * Query lineage records
 */
export async function queryLineageRecords(query = {}) {
  const lineageDir = path.join(process.cwd(), 'output', 'lineage');

  if (!fs.existsSync(lineageDir)) {
    return [];
  }

  const files = await readdirAsync(lineageDir);
  const records = [];

  for (const file of files) {
    if (file.endsWith('.json')) {
      try {
        const record = await readJSONFile(path.join(lineageDir, file));

        // Apply filters
        if (query.jobId && record.lineage?.job_id !== query.jobId) continue;
        if (query.branch && record.lineage?.branch !== query.branch) continue;
        if (query.status && record.execution?.status !== query.status) continue;

        records.push(record);
      } catch (error) {
        logger.warn(`Failed to read lineage file ${file}:`, error.message);
      }
    }
  }

  return records;
}

/**
 * Read lineage record by run ID
 */
export async function readLineageRecord(runId) {
  const lineageDir = path.join(process.cwd(), 'output', 'lineage');
  const filePath = path.join(lineageDir, `${runId}.json`);

  if (!fs.existsSync(filePath)) {
    return null;
  }

  return await readJSONFile(filePath);
}

/**
 * Save lineage record
 */
export async function saveLineageRecord(record) {
  const lineageDir = path.join(process.cwd(), 'output', 'lineage');
  await ensureDirectory(lineageDir);

  const filePath = path.join(lineageDir, `${record.run_id}.json`);
  await writeJSONFile(filePath, record);

  return filePath;
}

// ============================================================================
// PYTHON BRIDGE UTILITIES
// ============================================================================

/**
 * Execute Python script
 */
export async function executePythonScript(scriptPath, args = [], options = {}) {
  const python = options.python || 'python';
  const timeout = options.timeout || 60000;
  const cwd = options.cwd || process.cwd();

  const command = `${python} ${scriptPath} ${args.join(' ')}`;

  try {
    const { stdout, stderr } = await execAsync(command, {
      cwd,
      timeout,
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });

    return {
      success: true,
      stdout: stdout.trim(),
      stderr: stderr.trim()
    };
  } catch (error) {
    return {
      success: false,
      stdout: error.stdout?.trim() || '',
      stderr: error.stderr?.trim() || error.message,
      error: error.message
    };
  }
}

/**
 * Call Python module
 */
export async function callPythonModule(modulePath, functionName, args = {}) {
  // Create temporary Python script to call module function
  const tempScript = `
import json
import sys
from ${modulePath} import ${functionName}

args = json.loads(sys.argv[1])
result = ${functionName}(**args)
print(json.dumps(result))
  `.trim();

  const scriptPath = path.join(process.cwd(), '.temp_py_call.py');
  await writeFileAsync(scriptPath, tempScript);

  try {
    const result = await executePythonScript(scriptPath, [JSON.stringify(args)]);

    if (result.success) {
      return JSON.parse(result.stdout);
    } else {
      throw new Error(result.stderr || 'Python call failed');
    }
  } finally {
    await deleteFile(scriptPath);
  }
}

// ============================================================================
// RESPONSE FORMATTING
// ============================================================================

/**
 * Format success response
 */
export function formatSuccessResponse(message, data = {}) {
  return {
    success: true,
    message,
    data,
    timestamp: new Date().toISOString()
  };
}

/**
 * Format error response
 */
export function formatErrorResponse(error, message) {
  return {
    success: false,
    error,
    message,
    timestamp: new Date().toISOString()
  };
}

/**
 * Format validation error
 */
export function formatValidationError(errors) {
  return {
    success: false,
    error: 'Validation Error',
    errors: Array.isArray(errors) ? errors : [errors],
    timestamp: new Date().toISOString()
  };
}

// ============================================================================
// DATA PROCESSING
// ============================================================================

/**
 * Deep clone object
 */
export function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Merge objects
 */
export function mergeObjects(...objects) {
  return Object.assign({}, ...objects);
}

/**
 * Pick keys from object
 */
export function pickKeys(obj, keys) {
  return keys.reduce((acc, key) => {
    if (key in obj) acc[key] = obj[key];
    return acc;
  }, {});
}

/**
 * Omit keys from object
 */
export function omitKeys(obj, keys) {
  const result = { ...obj };
  keys.forEach(key => delete result[key]);
  return result;
}

/**
 * Group array by key
 */
export function groupBy(array, key) {
  return array.reduce((acc, item) => {
    const group = item[key];
    if (!acc[group]) acc[group] = [];
    acc[group].push(item);
    return acc;
  }, {});
}

/**
 * Flatten array
 */
export function flatten(array) {
  return array.reduce((acc, val) => acc.concat(val), []);
}

/**
 * Unique array values
 */
export function unique(array) {
  return [...new Set(array)];
}

/**
 * Chunk array
 */
export function chunk(array, size) {
  const chunks = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}

// ============================================================================
// TIME UTILITIES
// ============================================================================

/**
 * Format duration
 */
export function formatDuration(ms) {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(2)}m`;
  return `${(ms / 3600000).toFixed(2)}h`;
}

/**
 * Sleep/delay
 */
export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry with exponential backoff
 */
export async function retry(fn, maxAttempts = 3, baseDelay = 1000) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxAttempts) throw error;
      const delay = baseDelay * Math.pow(2, attempt - 1);
      logger.warn(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
      await sleep(delay);
    }
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  // Logging
  logger,
  formatLogMessage,

  // Validation
  validateJobConfig,
  validateGenerationOptions,
  validatePort,
  validateFilePath,
  validateImageFormat,
  validateSchema,

  // ID & Hash Generation
  generateJobId,
  generateUUID,
  generateRunId,
  generateLineageId,
  calculateChecksum,
  hashString,

  // Path Utilities
  normalizePath,
  resolveAbsolutePath,
  getFileExtension,
  getBasename,
  ensureDirectory,
  getRelativePath,
  joinPaths,
  getParentDir,
  sanitizeFilename,
  getUniqueFilename,

  // File Operations
  readJSONFile,
  writeJSONFile,
  copyFile,
  moveFile,
  deleteFile,
  listFiles,
  getFileStats,
  getFileSizeMB,
  isDirectory,
  isFile,

  // Job Configuration
  createJobConfig,
  createGenerationOptions,

  // Lineage
  tagAssetWithLineage,
  createLineageRecord,
  queryLineageRecords,
  readLineageRecord,
  saveLineageRecord,

  // Python Bridge
  executePythonScript,
  callPythonModule,

  // Response Formatting
  formatSuccessResponse,
  formatErrorResponse,
  formatValidationError,

  // Data Processing
  deepClone,
  mergeObjects,
  pickKeys,
  omitKeys,
  groupBy,
  flatten,
  unique,
  chunk,

  // Time Utilities
  formatDuration,
  sleep,
  retry
};
