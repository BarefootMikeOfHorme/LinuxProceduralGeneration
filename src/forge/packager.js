/**
 * VaultMind Forge - Asset Packager Module (Node.js)
 *
 * ZIP packaging with metadata and checksums
 */

import fs from 'fs';
import path from 'path';
import archiver from 'archiver';
import {
  logger,
  ensureDirectory,
  calculateChecksum,
  writeJSONFile,
  getFileSizeMB
} from '../utils.js';

/**
 * Asset Packager Class
 */
export class AssetPackager {
  constructor(options = {}) {
    this.compression = options.compression || 'deflate';
    this.level = options.level || 9;
    this.logger = options.logger || logger;
  }

  /**
   * Package assets into ZIP
   */
  async package(assetPaths, options = {}) {
    if (!Array.isArray(assetPaths) || assetPaths.length === 0) {
      throw new Error('No assets provided for packaging');
    }

    const outputDir = options.outputDir || './output';
    await ensureDirectory(outputDir);

    const packageName = options.packageName || `package_${Date.now()}`;
    const zipPath = path.join(outputDir, `${packageName}.zip`);

    this.logger.info(`Packaging ${assetPaths.length} assets into: ${zipPath}`);

    // Create manifest
    const manifest = await this._createManifest(assetPaths, options);

    // Create ZIP archive
    await this._createZip(assetPaths, zipPath, manifest, options);

    const zipSize = await getFileSizeMB(zipPath);
    this.logger.info(`Package created: ${zipPath} (${zipSize.toFixed(2)} MB)`);

    return {
      packagePath: zipPath,
      packageSize: zipSize,
      manifest,
      assetCount: assetPaths.length
    };
  }

  /**
   * Create manifest with checksums
   */
  async _createManifest(assetPaths, options) {
    const assets = [];

    for (const assetPath of assetPaths) {
      const stats = fs.statSync(assetPath);
      const checksum = await calculateChecksum(assetPath);

      assets.push({
        filename: path.basename(assetPath),
        path: assetPath,
        size: stats.size,
        size_mb: (stats.size / 1024 / 1024).toFixed(2),
        checksum,
        modified: stats.mtime.toISOString()
      });
    }

    return {
      version: '1.0',
      created: new Date().toISOString(),
      asset_count: assets.length,
      total_size_mb: assets.reduce((sum, a) => sum + parseFloat(a.size_mb), 0).toFixed(2),
      compression: this.compression,
      assets,
      metadata: options.metadata || {}
    };
  }

  /**
   * Create ZIP archive
   */
  async _createZip(assetPaths, zipPath, manifest, options) {
    return new Promise((resolve, reject) => {
      const output = fs.createWriteStream(zipPath);
      const archive = archiver('zip', {
        zlib: { level: this.level }
      });

      output.on('close', () => {
        this.logger.debug(`ZIP created: ${archive.pointer()} total bytes`);
        resolve(zipPath);
      });

      archive.on('error', (err) => {
        reject(err);
      });

      archive.pipe(output);

      // Add assets
      for (const assetPath of assetPaths) {
        const filename = path.basename(assetPath);
        archive.file(assetPath, { name: `assets/${filename}` });
      }

      // Add manifest
      if (options.includeMeta !== false) {
        archive.append(JSON.stringify(manifest, null, 2), { name: 'manifest.json' });
      }

      // Add metadata if provided
      if (options.metadata) {
        archive.append(JSON.stringify(options.metadata, null, 2), { name: 'metadata.json' });
      }

      archive.finalize();
    });
  }

  /**
   * Unpack ZIP archive
   */
  async unpack(zipPath, outputDir) {
    // TODO: Implement ZIP extraction
    throw new Error('Unpack not yet implemented');
  }

  /**
   * Verify package integrity
   */
  async verify(zipPath) {
    // TODO: Implement package verification
    throw new Error('Verify not yet implemented');
  }
}

export default AssetPackager;
