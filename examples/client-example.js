/**
 * VaultMind Forge API Client Example
 *
 * This example demonstrates how to use the VaultMind Forge Node.js API
 * to create generation jobs, check status, and validate assets.
 */

const API_BASE = process.env.API_URL || 'http://localhost:3000/api';

/**
 * Helper function to make API requests
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error?.message || 'API request failed');
    }

    return data;
  } catch (error) {
    console.error(`API request failed: ${endpoint}`, error.message);
    throw error;
  }
}

/**
 * Get API health status
 */
async function checkHealth() {
  console.log('🏥 Checking API health...');
  const result = await apiRequest('/health');
  console.log('✅ API is healthy:', result.data);
  return result.data;
}

/**
 * Get VaultMind Forge version
 */
async function getVersion() {
  console.log('📦 Getting version...');
  const result = await apiRequest('/version');
  console.log(`✅ Version: ${result.data.version}`);
  return result.data.version;
}

/**
 * Get system status
 */
async function getStatus() {
  console.log('📊 Getting system status...');
  const result = await apiRequest('/status');
  console.log(`✅ Modules found: ${result.data.modules.length}`);
  console.log(`   Available modules: ${result.data.modules.join(', ')}`);
  return result.data;
}

/**
 * Create a generation job
 */
async function createJob(config) {
  console.log('🎨 Creating generation job...');

  const jobConfig = {
    outputType: config.outputType || 'character',
    styleTags: config.styleTags || ['photoreal'],
    passes: config.passes || 3,
    consistencyThreshold: config.consistencyThreshold || 0.8,
    async: true,
    ...config
  };

  const result = await apiRequest('/jobs', {
    method: 'POST',
    body: JSON.stringify(jobConfig)
  });

  console.log(`✅ Job created: ${result.data.jobId}`);
  console.log(`   Status: ${result.data.status}`);
  console.log(`   Status URL: ${result.data.statusUrl}`);

  return result.data.jobId;
}

/**
 * Create a simple job
 */
async function createSimpleJob(name, style = 'photoreal', dimensions = [512, 512]) {
  console.log(`🎨 Creating simple job: ${name}`);

  const result = await apiRequest('/jobs/simple', {
    method: 'POST',
    body: JSON.stringify({
      name,
      style,
      target: dimensions,
      meta: {
        createdBy: 'client-example',
        timestamp: new Date().toISOString()
      }
    })
  });

  console.log(`✅ Simple job created:`, result.data);
  return result.data;
}

/**
 * Get job status
 */
async function getJobStatus(jobId) {
  const result = await apiRequest(`/jobs/${jobId}/status`);
  return result.data;
}

/**
 * Wait for job to complete
 */
async function waitForJobCompletion(jobId, pollInterval = 5000, maxWaitTime = 600000) {
  console.log(`⏳ Waiting for job ${jobId} to complete...`);

  const startTime = Date.now();

  while (true) {
    const status = await getJobStatus(jobId);

    console.log(`   Status: ${status.status} (${status.progress}%)`);

    if (status.status === 'completed') {
      console.log('✅ Job completed successfully!');
      return status;
    }

    if (status.status === 'failed') {
      console.error('❌ Job failed:', status.error);
      throw new Error(`Job failed: ${status.error}`);
    }

    // Check timeout
    if (Date.now() - startTime > maxWaitTime) {
      throw new Error(`Job timeout: exceeded ${maxWaitTime}ms`);
    }

    // Wait before next poll
    await new Promise(resolve => setTimeout(resolve, pollInterval));
  }
}

/**
 * Get job outputs
 */
async function getJobOutputs(jobId) {
  console.log(`📂 Getting outputs for job ${jobId}...`);

  const result = await apiRequest(`/jobs/${jobId}/outputs`);

  console.log(`✅ Found ${result.data.count} output files:`);
  result.data.files.forEach((file, index) => {
    console.log(`   ${index + 1}. ${file.filename}`);
  });

  return result.data.files;
}

/**
 * Validate asset files by path
 */
async function validateAssets(paths) {
  console.log(`🔍 Validating ${paths.length} assets...`);

  const result = await apiRequest('/validate/paths', {
    method: 'POST',
    body: JSON.stringify({ paths })
  });

  const { summary, validations } = result.data;

  console.log(`✅ Validation complete:`);
  console.log(`   Total: ${summary.total}`);
  console.log(`   Passed: ${summary.passed}`);
  console.log(`   Failed: ${summary.failed}`);

  validations.forEach((validation, index) => {
    const icon = validation.passed ? '✅' : '❌';
    console.log(`   ${icon} ${validation.file}: ${validation.status} (score: ${validation.score})`);
  });

  return result.data;
}

/**
 * Run demo pipeline
 */
async function runDemo(outputDir = `demo_${Date.now()}`) {
  console.log(`🎬 Running demo pipeline...`);
  console.log(`   Output directory: ${outputDir}`);

  const result = await apiRequest('/demo', {
    method: 'POST',
    body: JSON.stringify({ outputDir })
  });

  console.log('✅ Demo completed successfully!');
  console.log(`   Output: ${result.data.outputDir}`);

  return result.data;
}

/**
 * List all jobs
 */
async function listJobs() {
  console.log('📋 Listing all jobs...');

  const result = await apiRequest('/jobs');

  console.log(`✅ Found ${result.data.count} jobs:`);
  result.data.jobs.forEach((job, index) => {
    console.log(`   ${index + 1}. ${job.jobId} - ${job.status} (${job.progress}%)`);
  });

  return result.data.jobs;
}

/**
 * Example: Complete workflow
 */
async function exampleWorkflow() {
  console.log('\n🚀 VaultMind Forge API Client Example\n');
  console.log('━'.repeat(50));

  try {
    // 1. Health check
    await checkHealth();
    console.log('');

    // 2. Get version
    await getVersion();
    console.log('');

    // 3. Get status
    await getStatus();
    console.log('');

    // 4. Create a simple job
    await createSimpleJob('hero-character', 'cel-shaded', [1024, 1024]);
    console.log('');

    // 5. Create a full generation job
    const jobId = await createJob({
      outputType: 'character',
      styleTags: ['anime', 'cel-shaded', 'vibrant'],
      passes: 3,
      consistencyThreshold: 0.85
    });
    console.log('');

    // 6. Wait for job completion
    const completedJob = await waitForJobCompletion(jobId);
    console.log('');

    // 7. Get job outputs
    const outputs = await getJobOutputs(jobId);
    console.log('');

    // 8. Validate outputs (if any exist)
    if (outputs.length > 0) {
      const outputPaths = outputs.map(f => f.path);
      await validateAssets(outputPaths);
      console.log('');
    }

    // 9. List all jobs
    await listJobs();
    console.log('');

    console.log('━'.repeat(50));
    console.log('✅ Workflow completed successfully!\n');

  } catch (error) {
    console.error('\n❌ Error in workflow:', error.message);
    process.exit(1);
  }
}

/**
 * Example: Run demo only
 */
async function exampleDemo() {
  console.log('\n🎬 Running Demo Pipeline Example\n');
  console.log('━'.repeat(50));

  try {
    await checkHealth();
    console.log('');

    await runDemo();
    console.log('');

    console.log('━'.repeat(50));
    console.log('✅ Demo completed!\n');

  } catch (error) {
    console.error('\n❌ Demo failed:', error.message);
    process.exit(1);
  }
}

/**
 * Example: Validate existing files
 */
async function exampleValidation() {
  console.log('\n🔍 Asset Validation Example\n');
  console.log('━'.repeat(50));

  try {
    await checkHealth();
    console.log('');

    // Replace with actual file paths
    const filesToValidate = [
      'C:\\path\\to\\image1.png',
      'C:\\path\\to\\image2.png'
    ];

    await validateAssets(filesToValidate);
    console.log('');

    console.log('━'.repeat(50));
    console.log('✅ Validation completed!\n');

  } catch (error) {
    console.error('\n❌ Validation failed:', error.message);
    process.exit(1);
  }
}

/**
 * Main entry point
 */
async function main() {
  const command = process.argv[2] || 'workflow';

  switch (command) {
    case 'workflow':
      await exampleWorkflow();
      break;
    case 'demo':
      await exampleDemo();
      break;
    case 'validate':
      await exampleValidation();
      break;
    case 'health':
      await checkHealth();
      break;
    case 'version':
      await getVersion();
      break;
    case 'status':
      await getStatus();
      break;
    case 'jobs':
      await listJobs();
      break;
    default:
      console.log('Usage: node client-example.js [command]');
      console.log('Commands:');
      console.log('  workflow   - Run complete workflow (default)');
      console.log('  demo       - Run demo pipeline');
      console.log('  validate   - Validate example files');
      console.log('  health     - Check API health');
      console.log('  version    - Get API version');
      console.log('  status     - Get system status');
      console.log('  jobs       - List all jobs');
      process.exit(1);
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

// Export functions for use as a module
export {
  checkHealth,
  getVersion,
  getStatus,
  createJob,
  createSimpleJob,
  getJobStatus,
  waitForJobCompletion,
  getJobOutputs,
  validateAssets,
  runDemo,
  listJobs
};
