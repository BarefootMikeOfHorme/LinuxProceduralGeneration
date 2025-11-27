/**
 * VaultMind Forge - Diffusion Generation Module (Node.js)
 *
 * Wrapper around Python backend for image generation
 */

import path from 'path';
import fs from 'fs';
import {
  logger,
  validateJobConfig,
  createJobConfig,
  createLineageRecord,
  saveLineageRecord,
  generateRunId,
  ensureDirectory,
  calculateChecksum
} from '../utils.js';
import { callDiffusionGenerator } from '../pythonBridge.js';

/**
 * Generation Job Class
 */
export class GenerationJob {
  constructor(config) {
    this.config = config;
    this.id = config.id || config.name;
    this.name = config.name;
    this.style = config.style;
    this.target = config.target || [1024, 1024];
    this.meta = config.meta || {};
  }

  toJobConfig() {
    return createJobConfig({
      id: this.id,
      outputType: 'image',
      styleTags: [this.style],
      target: this.target,
      metadata: this.meta
    });
  }
}

/**
 * Diffusion Generator Class
 */
export class DiffusionGenerator {
  constructor(options = {}) {
    // FIXED: Use real Python backend by default, NOT placeholder
    // Environment variable takes precedence, then options, then default to 'python'
    this.mode = process.env.BACKEND_MODE || options.mode || 'python';
    this.backend = options.backend || 'sdxl_base';
    this.logger = options.logger || logger;

    // Log warning if placeholder mode is explicitly requested
    if (this.mode === 'placeholder') {
      this.logger.warn('⚠️  WARNING: Running in PLACEHOLDER mode - will generate fake images!');
      this.logger.warn('⚠️  Set BACKEND_MODE=python in .env to use real SDXL generation');
    } else {
      this.logger.info(`✅ Using real backend mode: ${this.mode}`);
    }
  }

  /**
   * Generate single or multi-pass
   */
  async generate(jobConfig, options = {}) {
    const validation = validateJobConfig(jobConfig);
    if (!validation.valid) {
      throw new Error(`Invalid job config: ${validation.errors.join(', ')}`);
    }

    this.logger.info(`Starting generation (mode: ${this.mode})`);

    const outputDir = options.outputDir || path.join(process.cwd(), 'output', jobConfig.id);
    await ensureDirectory(outputDir);

    if (this.mode === 'placeholder') {
      return this._generatePlaceholder(jobConfig, outputDir, options);
    } else {
      return this._generateWithPython(jobConfig, outputDir, options);
    }
  }

  /**
   * Generate with full lineage tracking
   */
  async generateWithLineage(jobConfig, outputDir, options = {}) {
    this.logger.info(`Starting generation with lineage tracking`);

    await ensureDirectory(outputDir);

    // Create lineage record
    const lineageRecord = createLineageRecord(jobConfig);

    try {
      // Generate assets
      const result = await this.generate(jobConfig, {
        ...options,
        outputDir
      });

      // Update lineage with results
      lineageRecord.assets = result.assets || [];
      lineageRecord.execution.end_time = new Date().toISOString();
      lineageRecord.execution.duration_ms = Date.now() - new Date(lineageRecord.execution.start_time).getTime();
      lineageRecord.execution.status = 'completed';

      // Add validations if validator provided
      if (options.validator && result.winner) {
        const validation = await options.validator(result.winner);
        lineageRecord.validations.push({
          file: result.winner,
          ...validation
        });
      }

      // Add rejections
      if (result.rejections) {
        lineageRecord.rejections = result.rejections;
      }

      // Save lineage
      const lineagePath = await saveLineageRecord(lineageRecord);
      this.logger.info(`Lineage saved: ${lineagePath}`);

      return {
        ...result,
        lineageId: lineageRecord.lineage.lineage_id,
        lineagePath,
        lineageRecord
      };
    } catch (error) {
      lineageRecord.execution.status = 'failed';
      lineageRecord.execution.end_time = new Date().toISOString();
      lineageRecord.execution.duration_ms = Date.now() - new Date(lineageRecord.execution.start_time).getTime();

      await saveLineageRecord(lineageRecord);
      throw error;
    }
  }

  /**
   * Generate placeholder images (for testing)
   */
  async _generatePlaceholder(jobConfig, outputDir, options) {
    this.logger.info('Generating placeholder assets');

    const passes = options.multiPass ? (options.passes || 3) : 1;
    const assets = [];
    const candidates = [];

    for (let i = 0; i < passes; i++) {
      const filename = `${jobConfig.id}_pass${i + 1}.png`;
      const assetPath = path.join(outputDir, filename);

      // Create placeholder image (1x1 pixel PNG)
      const placeholder = Buffer.from([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, // PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52, // IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, // 1x1 image
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
        0x89, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x44, 0x41,
        0x54, 0x78, 0x9C, 0x62, 0x00, 0x01, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
        0x42, 0x60, 0x82
      ]);

      fs.writeFileSync(assetPath, placeholder);

      const asset = {
        asset_path: assetPath,
        checksum: null,
        validated: false,
        metrics: { score: 0.7 + Math.random() * 0.3 } // Random score 0.7-1.0
      };

      assets.push(asset);
      candidates.push(asset);
    }

    // Select winner (highest score)
    const winner = candidates.reduce((best, current) =>
      current.metrics.score > best.metrics.score ? current : best
    );

    // Calculate checksums
    for (const asset of assets) {
      asset.checksum = await calculateChecksum(asset.asset_path);
    }

    this.logger.info(`Generated ${assets.length} placeholder assets, winner: ${path.basename(winner.asset_path)}`);

    return {
      jobId: jobConfig.id,
      assets,
      candidates,
      winner: winner.asset_path,
      winnerScore: winner.metrics.score,
      rejections: candidates.filter(c => c !== winner).map(c => ({
        asset_path: c.asset_path,
        reason: 'Lower quality score',
        score: c.metrics.score
      }))
    };
  }

  /**
   * Generate using Python backend
   */
  async _generateWithPython(jobConfig, outputDir, options) {
    this.logger.info('Generating with Python SDXL backend');

    try {
      const result = await callDiffusionGenerator(jobConfig, {
        outputDir,
        backend: this.backend,
        multiPass: options.multiPass,
        passes: options.passes,
        timeout: options.timeout
      });

      return result;
    } catch (error) {
      this.logger.error('Python generation failed:', error);
      throw new Error(`Python generation failed: ${error.message}`);
    }
  }
}

export default DiffusionGenerator;
