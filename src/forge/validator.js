/**
 * VaultMind Forge - Asset Validator Module (Node.js)
 *
 * Wrapper around Python/C++/Rust validators
 */

import fs from 'fs';
import path from 'path';
import { logger, validateFilePath, getFileExtension } from '../utils.js';
import { callValidator } from '../pythonBridge.js';

/**
 * Asset Validator Class
 */
export class AssetValidator {
  constructor(options = {}) {
    this.mode = options.mode || 'basic';
    this.threshold = options.threshold || 0.7;
    this.logger = options.logger || logger;
  }

  /**
   * Validate single asset
   */
  async validate(assetPath, options = {}) {
    if (!validateFilePath(assetPath)) {
      throw new Error(`Asset not found: ${assetPath}`);
    }

    this.logger.info(`Validating: ${path.basename(assetPath)} (mode: ${this.mode})`);

    if (this.mode === 'basic') {
      return this._validateBasic(assetPath);
    } else if (this.mode === 'python') {
      return this._validateWithPython(assetPath, options);
    } else {
      throw new Error(`Unknown validation mode: ${this.mode}`);
    }
  }

  /**
   * Validate multiple assets
   */
  async validateBatch(assetPaths, options = {}) {
    const results = [];

    for (const assetPath of assetPaths) {
      try {
        const result = await this.validate(assetPath, options);
        results.push({
          path: assetPath,
          ...result
        });
      } catch (error) {
        results.push({
          path: assetPath,
          error: error.message,
          passed: false
        });
      }
    }

    return results;
  }

  /**
   * Basic validation (file exists, size, format)
   */
  async _validateBasic(assetPath) {
    const stats = fs.statSync(assetPath);
    const ext = getFileExtension(assetPath);
    const validFormats = ['.png', '.jpg', '.jpeg', '.webp', '.bmp'];

    const isValidFormat = validFormats.includes(ext);
    const isValidSize = stats.size > 100 && stats.size < 100 * 1024 * 1024; // 100B - 100MB
    const score = (isValidFormat ? 0.5 : 0) + (isValidSize ? 0.5 : 0);

    const passed = score >= this.threshold;

    return {
      score,
      status: passed ? 'PASS' : 'FAIL',
      passed,
      metrics: {
        format: ext,
        size_mb: (stats.size / 1024 / 1024).toFixed(2),
        valid_format: isValidFormat,
        valid_size: isValidSize
      },
      details: {
        file: path.basename(assetPath),
        size: stats.size,
        created: stats.birthtime.toISOString()
      }
    };
  }

  /**
   * Advanced validation using Python backend
   */
  async _validateWithPython(assetPath, options) {
    try {
      const result = await callValidator(assetPath, options.backend || 'advanced');
      return {
        ...result,
        passed: result.score >= this.threshold
      };
    } catch (error) {
      this.logger.error('Python validation failed:', error);
      // Fallback to basic validation
      return this._validateBasic(assetPath);
    }
  }

  /**
   * Get validation report
   */
  async getReport(validationResults) {
    const total = validationResults.length;
    const passed = validationResults.filter(r => r.passed).length;
    const failed = total - passed;
    const avgScore = validationResults.reduce((sum, r) => sum + (r.score || 0), 0) / total;

    return {
      summary: {
        total,
        passed,
        failed,
        pass_rate: ((passed / total) * 100).toFixed(2) + '%',
        avg_score: avgScore.toFixed(3)
      },
      results: validationResults
    };
  }
}

export default AssetValidator;
