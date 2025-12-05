/**
 * VaultMind Forge - API Client
 * Handles communication with Node.js API (which bridges to Python orchestrator)
 * Supports multiple backends: Local SDXL, Hugging Face, NVIDIA NIM, Replicate
 */

class VaultMindAPI {
    constructor(baseUrl = 'http://localhost:5084') {
        this.baseUrl = baseUrl;
        this.connected = false;
        this.backend = 'local'; // local, huggingface, nvidia, replicate
    }

    /**
     * Test API connection
     */
    async testConnection() {
        try {
            const response = await fetch(`${this.baseUrl}/api/health`);
            const data = await response.json();

            this.connected = data.status === 'ok';
            return { success: true, data };
        } catch (error) {
            this.connected = false;
            return { success: false, error: error.message };
        }
    }

    /**
     * Get API version and capabilities
     */
    async getVersion() {
        try {
            const response = await fetch(`${this.baseUrl}/api/version`);
            return await response.json();
        } catch (error) {
            throw new Error(`Failed to get version: ${error.message}`);
        }
    }

    /**
     * Get system status
     */
    async getStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/api/status`);
            return await response.json();
        } catch (error) {
            throw new Error(`Failed to get status: ${error.message}`);
        }
    }

    /**
     * Generate asset with diffusion model
     * Supports multiple backends via backend parameter
     *
     * @param {Object} config - Generation configuration
     * @param {string} config.prompt - Generation prompt
     * @param {number} config.width - Image width
     * @param {number} config.height - Image height
     * @param {number} config.num_inference_steps - Number of steps
     * @param {string} config.output_type - Asset type (character, environment, etc.)
     * @param {string} config.id - Job ID
     * @param {string} config.backend - Backend to use (local, huggingface, nvidia, replicate)
     */
    async generate(config) {
        try {
            const payload = {
                jobConfig: {
                    id: config.id || `gen_${Date.now()}`,
                    output_type: config.output_type || 'character',
                    prompt: config.prompt,
                    width: config.width || 1024,
                    height: config.height || 1024,
                    num_inference_steps: config.num_inference_steps || 30,
                    batch_size: config.batch_size || 1,
                    backend: config.backend || this.backend
                }
            };

            // Add backend-specific parameters
            if (config.backend === 'huggingface' && config.hf_token) {
                payload.jobConfig.hf_token = config.hf_token;
                payload.jobConfig.hf_model = config.hf_model || 'stabilityai/stable-diffusion-xl-base-1.0';
            } else if (config.backend === 'nvidia' && config.nvidia_api_key) {
                payload.jobConfig.nvidia_api_key = config.nvidia_api_key;
                payload.jobConfig.nvidia_model = config.nvidia_model || 'stable-diffusion-xl';
            } else if (config.backend === 'replicate' && config.replicate_token) {
                payload.jobConfig.replicate_token = config.replicate_token;
                payload.jobConfig.replicate_model = config.replicate_model || 'stability-ai/sdxl';
            }

            const response = await fetch(`${this.baseUrl}/api/diffusion/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Generation failed');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Generation failed: ${error.message}`);
        }
    }

    /**
     * Generate with full lineage tracking
     */
    async generateWithLineage(config) {
        try {
            const payload = {
                jobConfig: {
                    id: config.id || `gen_${Date.now()}`,
                    output_type: config.output_type || 'character',
                    prompt: config.prompt,
                    width: config.width || 1024,
                    height: config.height || 1024,
                    num_inference_steps: config.num_inference_steps || 30,
                    backend: config.backend || this.backend
                }
            };

            const response = await fetch(`${this.baseUrl}/api/diffusion/generate-with-lineage`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Generation failed');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Generation with lineage failed: ${error.message}`);
        }
    }

    /**
     * Validate generated assets
     */
    async validate(files) {
        try {
            const formData = new FormData();

            files.forEach((file, index) => {
                formData.append('files', file);
            });

            const response = await fetch(`${this.baseUrl}/api/validate`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Validation failed');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Validation failed: ${error.message}`);
        }
    }

    /**
     * Validate assets by file paths
     */
    async validatePaths(paths) {
        try {
            const response = await fetch(`${this.baseUrl}/api/validate/paths`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ paths })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Validation failed');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Path validation failed: ${error.message}`);
        }
    }

    /**
     * Query lineage records
     */
    async queryLineage(filters = {}) {
        try {
            const params = new URLSearchParams();

            if (filters.jobId) params.append('jobId', filters.jobId);
            if (filters.branch) params.append('branch', filters.branch);
            if (filters.status) params.append('status', filters.status);
            if (filters.limit) params.append('limit', filters.limit);

            const response = await fetch(`${this.baseUrl}/api/lineage?${params.toString()}`);

            if (!response.ok) {
                throw new Error('Failed to query lineage');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Lineage query failed: ${error.message}`);
        }
    }

    /**
     * Get specific lineage record
     */
    async getLineageRecord(runId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/lineage/${runId}`);

            if (!response.ok) {
                throw new Error('Lineage record not found');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Failed to get lineage record: ${error.message}`);
        }
    }

    /**
     * Create async job
     */
    async createJob(jobConfig) {
        try {
            const response = await fetch(`${this.baseUrl}/api/jobs`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ jobConfig })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Job creation failed');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Job creation failed: ${error.message}`);
        }
    }

    /**
     * Get job status
     */
    async getJobStatus(jobId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/jobs/${jobId}/status`);

            if (!response.ok) {
                throw new Error('Job not found');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Failed to get job status: ${error.message}`);
        }
    }

    /**
     * Get job outputs
     */
    async getJobOutputs(jobId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/jobs/${jobId}/outputs`);

            if (!response.ok) {
                throw new Error('Job outputs not found');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Failed to get job outputs: ${error.message}`);
        }
    }

    /**
     * Run demo pipeline
     */
    async runDemo() {
        try {
            const response = await fetch(`${this.baseUrl}/api/demo`, {
                method: 'POST'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Demo failed');
            }

            return await response.json();
        } catch (error) {
            throw new Error(`Demo failed: ${error.message}`);
        }
    }

    /**
     * Poll job until completion
     */
    async pollJob(jobId, onProgress = null, pollInterval = 1000) {
        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const status = await this.getJobStatus(jobId);

                    if (onProgress) {
                        onProgress(status);
                    }

                    if (status.status === 'completed') {
                        const outputs = await this.getJobOutputs(jobId);
                        resolve({ status, outputs });
                    } else if (status.status === 'failed') {
                        reject(new Error(status.error || 'Job failed'));
                    } else {
                        setTimeout(poll, pollInterval);
                    }
                } catch (error) {
                    reject(error);
                }
            };

            poll();
        });
    }

    /**
     * Set backend (local, huggingface, nvidia, replicate)
     */
    setBackend(backend) {
        this.backend = backend;
    }

    /**
     * Get current backend
     */
    getBackend() {
        return this.backend;
    }
}

// Create global API instance
const api = new VaultMindAPI();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VaultMindAPI, api };
}
