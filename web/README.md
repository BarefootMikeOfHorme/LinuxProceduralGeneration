# VaultMind Forge - Web UI

**Browser-based interface for VaultMind Forge asset generation pipeline**

---

## Overview

The web UI provides a modern, browser-based interface for interacting with VaultMind Forge's AI asset generation system. It connects to the Node.js API server which orchestrates Python backend operations and Rust validators.

### Architecture

```
Web UI (Browser)
    ↓ HTTP
Node.js API Server (port 5084)
    ↓ Python Bridge
Python Orchestrator (vaultmind_cli.py)
    ↓ PyO3 Bindings
Rust Validators (native performance)
```

---

## Features

- **🎨 Asset Generation** - Web-based prompt editor with real-time generation
- **🤖 Agent Dashboard** - Monitor 5 specialist AI agents with autonomy levels
- **📊 Lineage Viewer** - Track asset genealogy and validation history
- **⚡ Workflow Builder** - Visual DAG workflow creation (coming soon)
- **🖥️ Multi-Backend Support** - Local SDXL, Hugging Face, NVIDIA NIM, Replicate
- **📈 Real-time Stats** - Generation metrics and quality scores
- **🌐 Cloud Integration** - Easy configuration for cloud AI providers

---

## Quick Start

### 1. Start the API Server

```bash
cd C:\Users\Administrator\Desktop\Projects\LPG
npm start
```

Server will start on `http://localhost:5084`

### 2. Open Web UI

Navigate to: `http://localhost:5084/web/index.html`

Or use the Python CLI fallback:

```bash
python vaultmind_cli.py --help
```

---

## Backend Configuration

### Local (Default)

Uses local Python SDXL installation (placeholder mode if models not installed).

```javascript
// In browser console or via Settings panel
settings.backend = 'local';
```

### Hugging Face

Requires Hugging Face API token.

1. Get token from: https://huggingface.co/settings/tokens
2. Open Settings panel
3. Set backend to "huggingface"
4. Enter your HF token
5. Save settings

```javascript
settings.backend = 'huggingface';
settings.hf_token = 'hf_...';
settings.hf_model = 'stabilityai/stable-diffusion-xl-base-1.0'; // optional
```

### NVIDIA NIM

Requires NVIDIA API key.

1. Get API key from: https://build.nvidia.com
2. Configure in Settings
3. Select NVIDIA backend

```javascript
settings.backend = 'nvidia';
settings.nvidia_api_key = 'nvapi-...';
```

### Replicate

Requires Replicate API token.

1. Get token from: https://replicate.com/account/api-tokens
2. Configure in Settings

```javascript
settings.backend = 'replicate';
settings.replicate_token = 'r8_...';
```

---

## File Structure

```
web/
├── index.html              # Main HTML structure
├── css/
│   └── styles.css          # VaultMind Forge styling
├── js/
│   ├── api.js              # API client (multi-backend)
│   ├── app.js              # Main application logic
│   ├── agents.js           # Agent management (TODO)
│   ├── terminal.js         # Terminal emulator (TODO)
│   └── generation.js       # Generation helpers (TODO)
└── components/
    └── (React components)  # LineageViewer, etc.
```

---

## API Client Usage

The `VaultMindAPI` class provides a complete interface to the backend:

```javascript
// Initialize
const api = new VaultMindAPI('http://localhost:5084');

// Test connection
const result = await api.testConnection();

// Generate asset
const generation = await api.generate({
    prompt: 'a photorealistic cyberpunk samurai',
    width: 1024,
    height: 1024,
    num_inference_steps: 30,
    output_type: 'character',
    backend: 'local' // or 'huggingface', 'nvidia', 'replicate'
});

// With lineage tracking
const withLineage = await api.generateWithLineage(config);

// Query lineage
const lineage = await api.queryLineage({
    jobId: 'gen_12345',
    limit: 100
});

// Validate assets
const validation = await api.validatePaths([
    './output/asset1.png',
    './output/asset2.png'
]);
```

---

## Agent System

The web UI displays 5 specialist agents that autonomously handle different aspects of generation:

| Agent | Autonomy | Role |
|-------|----------|------|
| **Quality Guardian** | 75% | Validates output quality, rejects low-quality assets |
| **Prompt Refiner** | 85% | Enhances prompts for better results |
| **Parameter Optimizer** | 70% | Optimizes generation parameters |
| **Material Specialist** | 75% | Handles material/texture generation |
| **Resolution Expert** | 80% | Manages resolution scaling |

Agents communicate through the Python orchestrator via the Node.js bridge.

---

## Settings

Access via the ⚙️ Settings button in the top bar.

### API Connection

- **API Base URL**: Node.js server address (default: `http://localhost:5084`)
- **Test Connection**: Verify API is reachable

### Agent Configuration

- **Enable Agent Autonomy**: Allow agents to make autonomous decisions
- **Autonomy Threshold**: Minimum confidence level for autonomous actions (0-100%)

### Output Preferences

- **Output Directory**: Where generated assets are saved
- **Auto-validate**: Automatically validate generated assets

---

## Cloud Provider Setup

### Hugging Face Inference API

**Pros:**
- Free tier available
- Access to many SDXL models
- Good for experimentation

**Setup:**
1. Create account: https://huggingface.co/join
2. Generate token: Settings → Access Tokens → New Token
3. Enter token in web UI settings
4. Select model (or use default: `stabilityai/stable-diffusion-xl-base-1.0`)

**Example:**
```javascript
{
    prompt: "epic dragon",
    backend: "huggingface",
    hf_token: "hf_yourtoken",
    hf_model: "stabilityai/stable-diffusion-xl-base-1.0"
}
```

### NVIDIA NIM (NGC)

**Pros:**
- Enterprise-grade
- Optimized for NVIDIA GPUs
- Production-ready

**Setup:**
1. Register: https://build.nvidia.com
2. Get API key from dashboard
3. Configure in web UI

**Example:**
```javascript
{
    prompt: "futuristic city",
    backend: "nvidia",
    nvidia_api_key: "nvapi-yourkey",
    nvidia_model: "stable-diffusion-xl"
}
```

### Replicate

**Pros:**
- Pay-per-use
- Many model options
- Simple API

**Setup:**
1. Sign up: https://replicate.com/signup
2. Get token: Account → API Tokens
3. Enter in web UI

**Example:**
```javascript
{
    prompt: "magical forest",
    backend: "replicate",
    replicate_token: "r8_yourtoken",
    replicate_model: "stability-ai/sdxl"
}
```

---

## Python CLI Fallback

If Node.js is not available or you prefer terminal:

```bash
# Start Python Rich CLI
python vaultmind_cli.py

# Generate with CLI
python vaultmind_cli.py generate \
    "a photorealistic cyberpunk samurai" \
    --width 1024 \
    --height 1024 \
    --steps 30 \
    --output ./output/samurai.png

# Check agent status
python vaultmind_cli.py agents status

# View lineage
python vaultmind_cli.py lineage query --limit 10
```

The Python CLI uses Rich library for beautiful terminal output and is the **primary interface** for Linux servers and terminal-only environments.

---

## Development

### Running Locally

```bash
# Terminal 1: Start API server
npm start

# Terminal 2: Open browser
# Navigate to http://localhost:5084/web/index.html
```

### Adding New Features

1. **Add API endpoint** in `src/handlers.js`
2. **Add API client method** in `web/js/api.js`
3. **Add UI component** in `web/index.html`
4. **Wire up logic** in `web/js/app.js`

### Debugging

Open browser console (F12) to see:
- API connection status
- Generation progress
- Error messages
- Agent activity

---

## Troubleshooting

### Web UI won't load

```bash
# Check if server is running
curl http://localhost:5084/api/health

# Check server logs
npm start
```

### Connection failed

- Verify API server is running on correct port
- Check firewall settings
- Confirm `settings.apiUrl` matches server address

### Generation fails

- Check Python backend is installed: `python vaultmind_cli.py --version`
- Verify SDXL models are installed (or use placeholder mode)
- Check API logs for detailed error

### Cloud backend issues

- Verify API keys are correct
- Check rate limits for your provider
- Ensure network connectivity

---

## Next Steps

1. **Install SDXL models** for local generation
2. **Configure cloud provider** for enhanced capabilities
3. **Explore agent autonomy** settings
4. **Build workflows** for automation (coming soon)
5. **Review lineage** to track asset genealogy

---

## Integration with Rust

Rust validators run via Python PyO3 bindings and are called automatically:

- **Sharpness analysis** - Rust `rs_sharpness_score()`
- **Color fidelity** - Rust color analysis (in development)
- **Fast image processing** - Rust parallel pixel operations

The Python orchestrator handles the coordination while Rust provides native performance for compute-intensive validation.

---

## License

MIT License - See LICENSE.md

**Co-Authored-By:** Claude <noreply@anthropic.com>

---

**Built with L1-ACP Protocol Governance**
**Python orchestrates. Rust accelerates. Web UI facilitates.**
