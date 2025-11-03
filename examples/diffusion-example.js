/**
 * VaultMind Forge Diffusion Module Examples
 *
 * Demonstrates how to use the forge_diffusion.js module for:
 * - Basic asset generation
 * - Multi-pass generation with validation
 * - Complete workflow with lineage tracking
 * - Asset packaging
 */

import path from 'path';
import { fileURLToPath } from 'url';
import {
  DiffusionGenerator,
  GenerationJob
} from '../src/forge/diffusion.js';
import { AssetValidator } from '../src/forge/validator.js';
import { AssetPackager } from '../src/forge/packager.js';
import {
  createJobConfig,
  generateJobId,
  logger
} from '../src/utils.js';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

/**
 * Example 1: Basic Generation
 */
async function basicGenerationExample() {
  console.log('\n📦 Example 1: Basic Generation\n');
  console.log('━'.repeat(50));

  const generator = new DiffusionGenerator({
    mode: 'placeholder' // Use placeholder for testing
  });

  const job = new GenerationJob({
    name: 'hero-character',
    style: 'cel-shaded',
    target: [512, 512],
    meta: {
      project: 'Game Alpha',
      artist: 'Example'
    }
  });

  const outputDir = path.join(projectRoot, 'output', 'example1');

  logger.info('Starting basic generation');

  const assets = await generator.generate(job, outputDir, {
    count: 3 // Generate 3 variations
  });

  console.log(`✅ Generated ${assets.length} assets:`);
  assets.forEach((asset, i) => {
    console.log(`   ${i + 1}. ${asset}`);
  });

  return assets;
}

/**
 * Example 2: Multi-Pass Generation with Validation
 */
async function multiPassGenerationExample() {
  console.log('\n🔄 Example 2: Multi-Pass Generation\n');
  console.log('━'.repeat(50));

  const generator = new DiffusionGenerator({
    mode: 'placeholder'
  });

  const validator = new AssetValidator({
    mode: 'basic' // Use basic validation (no Python required)
  });

  const job = new GenerationJob({
    name: 'environment-forest',
    style: 'photoreal',
    target: [1024, 768]
  });

  const outputDir = path.join(projectRoot, 'output', 'example2');

  logger.info('Starting multi-pass generation');

  const result = await generator.generateMultiPass(job, outputDir, {
    passes: 5,
    minScore: 0.7,
    validator: async (assetPath) => {
      return validator.validate(assetPath);
    }
  });

  console.log('\n📊 Multi-Pass Results:');
  console.log('━'.repeat(50));
  console.log(`Total Passes: ${result.summary.totalPasses}`);
  console.log(`Passed: ${result.summary.passedCount}`);
  console.log(`Failed: ${result.summary.failedCount}`);
  console.log(`Success Rate: ${result.summary.successRate}`);
  console.log(`Best Score: ${result.summary.bestScore.toFixed(3)}`);

  if (result.winner) {
    console.log(`\n🏆 Winner: ${path.basename(result.winner.path)}`);
    console.log(`   Score: ${result.winner.score.toFixed(3)}`);
  }

  console.log('\n✅ All Variations:');
  result.allVariations.forEach((v, i) => {
    console.log(`   ${i + 1}. ${path.basename(v.path)} - Score: ${v.score.toFixed(3)}`);
  });

  if (result.rejectedVariations.length > 0) {
    console.log('\n❌ Rejected Variations:');
    result.rejectedVariations.forEach((v, i) => {
      console.log(`   ${i + 1}. ${path.basename(v.path)} - Score: ${v.score.toFixed(3)}`);
    });
  }

  return result;
}

/**
 * Example 3: Complete Workflow with Lineage Tracking
 */
async function completeWorkflowExample() {
  console.log('\n🎨 Example 3: Complete Workflow with Lineage\n');
  console.log('━'.repeat(50));

  const generator = new DiffusionGenerator({
    mode: 'placeholder'
  });

  const validator = new AssetValidator({
    mode: 'basic'
  });

  // Create a full job configuration
  const jobConfig = createJobConfig({
    outputType: 'character',
    styleTags: ['anime', 'cel-shaded', 'vibrant'],
    passes: 3,
    consistencyThreshold: 0.85,
    references: {
      palettes: [],
      embeddings: [],
      styleGuides: []
    },
    lineage: {
      branch: 'main',
      parent: null
    }
  });

  const outputDir = path.join(projectRoot, 'output', jobConfig.id);

  logger.info('Starting complete workflow', { jobId: jobConfig.id });

  const result = await generator.generateWithLineage(
    jobConfig,
    outputDir,
    {
      multiPass: true,
      passes: 3,
      validator: async (assetPath) => {
        return validator.validate(assetPath);
      },
      packageAssets: true
    }
  );

  console.log('\n📦 Workflow Complete:');
  console.log('━'.repeat(50));
  console.log(`Job ID: ${result.jobId}`);
  console.log(`Lineage ID: ${result.lineageId}`);
  console.log(`Assets Generated: ${result.allVariations.length}`);
  console.log(`Winner Score: ${result.winner?.score.toFixed(3) || 'N/A'}`);
  console.log(`Lineage Saved: ${result.lineagePath}`);
  console.log(`Package Created: ${result.packagePath || 'Not packaged'}`);
  console.log(`Execution Time: ${result.executionTime}ms`);

  console.log('\n✅ Summary:', JSON.stringify(result.summary, null, 2));

  return result;
}

/**
 * Example 4: Batch Validation
 */
async function batchValidationExample() {
  console.log('\n✅ Example 4: Batch Validation\n');
  console.log('━'.repeat(50));

  // First generate some assets
  const generator = new DiffusionGenerator({ mode: 'placeholder' });
  const job = new GenerationJob({
    name: 'batch-test',
    style: 'photoreal',
    target: [512, 512]
  });

  const outputDir = path.join(projectRoot, 'output', 'example4');
  const assets = await generator.generate(job, outputDir, { count: 5 });

  // Now validate them all
  const validator = new AssetValidator({ mode: 'basic' });
  const results = await validator.validateBatch(assets);

  console.log('\n📊 Batch Validation Results:');
  console.log('━'.repeat(50));
  console.log(`Total Assets: ${results.summary.total}`);
  console.log(`Passed: ${results.summary.passed}`);
  console.log(`Failed: ${results.summary.failed}`);
  console.log(`Average Score: ${results.summary.averageScore}`);

  console.log('\n📋 Individual Results:');
  results.results.forEach((r, i) => {
    const icon = r.passed ? '✅' : '❌';
    console.log(`   ${icon} ${path.basename(r.file)}: ${r.score.toFixed(3)}`);
  });

  return results;
}

/**
 * Example 5: Asset Packaging
 */
async function assetPackagingExample() {
  console.log('\n📦 Example 5: Asset Packaging\n');
  console.log('━'.repeat(50));

  // Generate assets
  const generator = new DiffusionGenerator({ mode: 'placeholder' });
  const job = new GenerationJob({
    name: 'packaging-test',
    style: 'anime',
    target: [1024, 1024]
  });

  const outputDir = path.join(projectRoot, 'output', 'example5');
  const assets = await generator.generate(job, outputDir, { count: 3 });

  console.log(`Generated ${assets.length} assets`);

  // Package them
  const packager = new AssetPackager({
    compressionLevel: 9, // Maximum compression
    includeMetadata: true
  });

  const packagePath = path.join(outputDir, 'assets-package.zip');

  console.log('\n📦 Creating package...');

  const packageInfo = await packager.packageWithChecksums(
    assets,
    packagePath,
    {
      jobId: generateJobId(),
      projectName: 'VaultMind Forge',
      generatedBy: 'diffusion-example',
      timestamp: new Date().toISOString()
    }
  );

  console.log('\n✅ Package Created:');
  console.log('━'.repeat(50));
  console.log(`Path: ${packageInfo.packagePath}`);
  console.log(`Size: ${(packageInfo.packageSize / 1024).toFixed(2)} KB`);
  console.log(`Assets: ${packageInfo.assetsCount}`);
  console.log(`Checksum: ${packageInfo.packageChecksum.substring(0, 16)}...`);

  console.log('\n📋 Asset Checksums:');
  packageInfo.assets.forEach((asset, i) => {
    console.log(`   ${i + 1}. ${asset.filename}`);
    console.log(`      Checksum: ${asset.checksum.substring(0, 16)}...`);
    console.log(`      Size: ${(asset.size / 1024).toFixed(2)} KB`);
  });

  return packageInfo;
}

/**
 * Example 6: Custom Validation Metrics
 */
async function customMetricsExample() {
  console.log('\n📏 Example 6: Custom Validation Metrics\n');
  console.log('━'.repeat(50));

  // Generate assets
  const generator = new DiffusionGenerator({ mode: 'placeholder' });
  const job = new GenerationJob({
    name: 'custom-metrics',
    style: 'photoreal',
    target: [800, 600]
  });

  const outputDir = path.join(projectRoot, 'output', 'example6');
  const assets = await generator.generate(job, outputDir, { count: 1 });

  // Validate with custom metrics
  const validator = new AssetValidator({ mode: 'basic' });

  const customMetrics = {
    minDimensions: async (assetPath) => {
      const { QualityMetrics } = await import('../src/forge/validator.js');
      return QualityMetrics.minDimensions(assetPath, {
        minWidth: 512,
        minHeight: 512
      });
    },
    aspectRatio: async (assetPath) => {
      const { QualityMetrics } = await import('../src/forge/validator.js');
      return QualityMetrics.aspectRatio(assetPath, 4 / 3, 0.1);
    },
    fileSize: async (assetPath) => {
      const { QualityMetrics } = await import('../src/forge/validator.js');
      return QualityMetrics.fileSize(assetPath, {
        minSize: 1024,
        maxSize: 5 * 1024 * 1024
      });
    }
  };

  const result = await validator.validateWithMetrics(assets[0], customMetrics);

  console.log('\n✅ Validation with Custom Metrics:');
  console.log('━'.repeat(50));
  console.log(`File: ${path.basename(result.file)}`);
  console.log(`Status: ${result.status}`);
  console.log(`Score: ${result.score.toFixed(3)}`);

  console.log('\n📏 Custom Metrics:');
  Object.entries(result.customMetrics).forEach(([name, metric]) => {
    const icon = metric.passed ? '✅' : '❌';
    console.log(`   ${icon} ${name}: ${metric.score.toFixed(3)}`);
    console.log(`      ${JSON.stringify(metric, null, 6)}`);
  });

  return result;
}

/**
 * Main runner - Execute all examples
 */
async function runAllExamples() {
  console.log('\n🚀 VaultMind Forge Diffusion Examples\n');
  console.log('═'.repeat(50));

  try {
    // Run examples sequentially
    await basicGenerationExample();
    await new Promise(resolve => setTimeout(resolve, 1000)); // Pause

    await multiPassGenerationExample();
    await new Promise(resolve => setTimeout(resolve, 1000));

    await completeWorkflowExample();
    await new Promise(resolve => setTimeout(resolve, 1000));

    await batchValidationExample();
    await new Promise(resolve => setTimeout(resolve, 1000));

    await assetPackagingExample();
    await new Promise(resolve => setTimeout(resolve, 1000));

    await customMetricsExample();

    console.log('\n═'.repeat(50));
    console.log('✅ All examples completed successfully!\n');

  } catch (error) {
    console.error('\n❌ Example failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

/**
 * CLI interface
 */
async function main() {
  const command = process.argv[2] || 'all';

  const examples = {
    basic: basicGenerationExample,
    multipass: multiPassGenerationExample,
    workflow: completeWorkflowExample,
    validation: batchValidationExample,
    packaging: assetPackagingExample,
    metrics: customMetricsExample,
    all: runAllExamples
  };

  if (!examples[command]) {
    console.log('Usage: node diffusion-example.js [command]');
    console.log('Commands:');
    console.log('  basic      - Basic asset generation');
    console.log('  multipass  - Multi-pass generation with validation');
    console.log('  workflow   - Complete workflow with lineage');
    console.log('  validation - Batch validation');
    console.log('  packaging  - Asset packaging');
    console.log('  metrics    - Custom validation metrics');
    console.log('  all        - Run all examples (default)');
    process.exit(1);
  }

  await examples[command]();
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export {
  basicGenerationExample,
  multiPassGenerationExample,
  completeWorkflowExample,
  batchValidationExample,
  assetPackagingExample,
  customMetricsExample
};
