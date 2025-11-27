/**
 * VaultMind Forge - Express API Server
 *
 * Production-ready REST API for asset generation, validation, and lineage tracking
 * Multi-language orchestration: Node.js API → Python backend → C++/Rust validators
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import path from 'path';
import { fileURLToPath } from 'url';
import { existsSync, mkdirSync } from 'fs';
import { createServer } from 'net';

import { logger, validatePort } from './utils.js';
import {
  handleGenerateDiffusion,
  handleGenerateWithLineage,
  handleValidate,
  handleValidatePaths,
  handleQueryLineage,
  handleGetLineageRecord,
  handleCreateJob,
  handleJobStatus,
  handleJobOutputs,
  handleHealth,
  handleVersion,
  handleStatus,
  handleDemo
} from './handlers.js';

// ES module __dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const HOST = process.env.HOST || 'localhost';
const NODE_ENV = process.env.NODE_ENV || 'development';

/**
 * Find available port in range 1000-8000
 * Avoids conflicts with LM Studio (3000), common services
 */
async function findAvailablePort(minPort = 1000, maxPort = 8000) {
  const checkPort = (port) => {
    return new Promise((resolve) => {
      const server = createServer();

      server.once('error', (err) => {
        if (err.code === 'EADDRINUSE') {
          resolve(false); // Port in use
        } else {
          resolve(false); // Other error, treat as unavailable
        }
      });

      server.once('listening', () => {
        server.close();
        resolve(true); // Port available
      });

      server.listen(port, HOST);
    });
  };

  // Try random ports in range
  const maxAttempts = 20;
  for (let i = 0; i < maxAttempts; i++) {
    const port = Math.floor(Math.random() * (maxPort - minPort + 1)) + minPort;
    if (await checkPort(port)) {
      return port;
    }
  }

  // Fallback: sequential search
  for (let port = minPort; port <= maxPort; port++) {
    if (await checkPort(port)) {
      return port;
    }
  }

  throw new Error(`No available ports found in range ${minPort}-${maxPort}`);
}

const PORT = process.env.PORT ? parseInt(process.env.PORT) : await findAvailablePort();

// Initialize Express app
const app = express();

// ============================================================================
// MIDDLEWARE
// ============================================================================

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "blob:"],
    }
  }
}));

// CORS middleware
app.use(cors({
  origin: NODE_ENV === 'production'
    ? process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000']
    : '*',
  credentials: true
}));

// Body parsing middleware
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Request logging middleware
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info(`${req.method} ${req.path} ${res.statusCode} - ${duration}ms`);
  });
  next();
});

// ============================================================================
// STATIC FILE SERVING
// ============================================================================

// Serve frontend components
app.use('/static', express.static(path.join(__dirname, 'frontend')));

// Serve web UI
const webDir = path.join(__dirname, '..', 'web');
app.use('/web', express.static(webDir));

// Serve generated assets
const outputDir = path.join(__dirname, '..', 'output');
if (!existsSync(outputDir)) {
  mkdirSync(outputDir, { recursive: true });
}
app.use('/output', express.static(outputDir));

// ============================================================================
// ROUTES
// ============================================================================

// Health & System Routes
app.get('/api/health', handleHealth);
app.get('/api/version', handleVersion);
app.get('/api/status', handleStatus);

// Diffusion Generation Routes
app.post('/api/diffusion/generate', handleGenerateDiffusion);
app.post('/api/diffusion/generate-with-lineage', handleGenerateWithLineage);

// Validation Routes
app.post('/api/validate', handleValidate);
app.post('/api/validate/paths', handleValidatePaths);

// Lineage Routes
app.get('/api/lineage', handleQueryLineage);
app.get('/api/lineage/:runId', handleGetLineageRecord);

// Job Management Routes
app.post('/api/jobs', handleCreateJob);
app.get('/api/jobs/:id/status', handleJobStatus);
app.get('/api/jobs/:id/outputs', handleJobOutputs);

// Demo Route
app.post('/api/demo', handleDemo);

// ============================================================================
// FRONTEND ROUTES
// ============================================================================

// LineageViewer demo page
app.get('/lineage-viewer', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'examples', 'lineage-viewer-demo.html'));
});

// Root route
app.get('/', (req, res) => {
  res.json({
    name: 'VaultMind Forge API',
    version: '0.4.1',
    status: 'running',
    endpoints: {
      health: 'GET /api/health',
      version: 'GET /api/version',
      status: 'GET /api/status',
      generate: 'POST /api/diffusion/generate',
      generateWithLineage: 'POST /api/diffusion/generate-with-lineage',
      validate: 'POST /api/validate',
      validatePaths: 'POST /api/validate/paths',
      lineage: 'GET /api/lineage',
      lineageRecord: 'GET /api/lineage/:runId',
      createJob: 'POST /api/jobs',
      jobStatus: 'GET /api/jobs/:id/status',
      jobOutputs: 'GET /api/jobs/:id/outputs',
      demo: 'POST /api/demo'
    },
    documentation: 'See /docs/api/NODE_API_README.md'
  });
});

// ============================================================================
// ERROR HANDLING
// ============================================================================

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.method} ${req.path} not found`,
    availableRoutes: '/api/*'
  });
});

// Global error handler
app.use((err, req, res, next) => {
  logger.error(`Server error: ${err.message}`, { stack: err.stack });

  res.status(err.status || 500).json({
    error: err.name || 'Internal Server Error',
    message: err.message || 'An unexpected error occurred',
    ...(NODE_ENV === 'development' && { stack: err.stack })
  });
});

// ============================================================================
// SERVER STARTUP
// ============================================================================

const server = app.listen(PORT, HOST, () => {
  logger.info('='.repeat(60));
  logger.info('🧬 VaultMind Forge API Server Started');
  logger.info('='.repeat(60));
  logger.info(`Environment: ${NODE_ENV}`);
  logger.info(`Server:      http://${HOST}:${PORT}`);
  logger.info(`Health:      http://${HOST}:${PORT}/api/health`);
  logger.info(`Docs:        http://${HOST}:${PORT}/`);
  logger.info(`LineageView: http://${HOST}:${PORT}/lineage-viewer`);
  logger.info('='.repeat(60));
  logger.info('Press Ctrl+C to stop server');
  logger.info('');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('\nSIGINT received, shutting down gracefully...');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

// Unhandled rejection handler
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

export default app;
