# 🧬 VaultMind Forge

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node.js-18%2B-green)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-proprietary-red)](./LICENSE.md)

**Production-Ready AI Content Generation with Visual Node-Based Workflows**

VaultMind Forge is an enterprise-grade platform for AI-powered procedural content generation, featuring a visual node-based workflow editor, comprehensive API, and multiple deployment options.

![VaultMind Forge Screenshot](docs/screenshot.png)

---

## 🚀 Features

### 🎨 Visual Workflow Editor
- **Node-Based Interface**: Drag-and-drop workflow creation with ReactFlow
- **Real-Time Preview**: See your workflow execute with live progress indicators
- **Modular Design**: Extensible node system for custom operations
- **Undo/Redo**: Full workflow history with keyboard shortcuts

### 🤖 AI-Powered Generation
- **Stable Diffusion XL**: High-fidelity image generation
- **Text-to-Image**: Create visual assets from natural language descriptions
- **Prompt Engineering**: Built-in prompt templates and refinement
- **Batch Processing**: Generate multiple variations efficiently

### 🔒 Enterprise Security
- **API Key Authentication**: Secure access control with X-API-Key headers
- **Rate Limiting**: Protect against DoS attacks with configurable limits
- **Path Traversal Protection**: Dual-validation filesystem security
- **Audit Logging**: Complete request/response logging with rotation

### ⚡ Production Ready
- **Docker Deployment**: Multi-stage builds with health checks
- **Systemd Integration**: Native Linux service management
- **Windows Installer**: One-click installation with Inno Setup
- **Comprehensive Monitoring**: Health endpoints, structured logging, error tracking

### 🎯 Developer Experience
- **FastAPI Backend**: Modern async Python web framework
- **React Frontend**: TypeScript-based UI with Vite build tooling
- **REST API**: Comprehensive API with OpenAPI/Swagger documentation
- **CLI Interface**: Rich terminal UI with Typer and textual

---

## 📦 Installation

### Quick Start with Docker (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration.git
cd LinuxProceduralGeneration

# 2. Configure environment
cp .env.example .env

# 3. Generate API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 4. Edit .env and set VAULTMIND_API_KEY

# 5. Start with Docker Compose
docker-compose up -d

# 6. Access the application
# Web UI: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Arch Linux (AUR)

```bash
# Install from AUR
yay -S vaultmind-forge

# Or build manually
git clone https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration.git
cd LinuxProceduralGeneration
makepkg -si

# Start service
sudo systemctl enable --now vaultmind-forge
```

### Windows Installer

1. Download `VaultMindForge-Setup.exe` from [Releases](https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration/releases)
2. Run the installer (will install Python 3.12 and Node.js if needed)
3. Follow the setup wizard
4. Configure your API key in the `.env` file
5. Service starts automatically

### Manual Installation

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed manual installation instructions.

---

## 🎮 Usage

### Web UI

The visual node editor is the primary interface:

1. **Open your browser** to `http://localhost:8000`
2. **Drag nodes** from the palette onto the canvas
3. **Connect nodes** by dragging from output to input handles
4. **Configure properties** in the right panel
5. **Execute workflow** with the Execute button (or F5)
6. **Monitor progress** in the execution panel

**Keyboard Shortcuts:**
- `F5` - Execute workflow
- `Ctrl/Cmd + S` - Save workflow
- `Ctrl/Cmd + Z` - Undo
- `Ctrl/Cmd + Y` - Redo
- `Delete` - Delete selected nodes
- `F1` - Show help

### API

```python
import requests

headers = {"X-API-Key": "your-api-key-here"}

# Execute a workflow
response = requests.post(
    "http://localhost:8000/api/execute",
    headers=headers,
    json={
        "nodes": [...],
        "edges": [...]
    }
)

# Check health
health = requests.get("http://localhost:8000/api/health").json()
print(health)
```

### CLI

```bash
# Start the TUI interface
vaultmind-forge tui

# Run a workflow from file
vaultmind-forge run workflow.json

# Validate configuration
vaultmind-forge validate
```

---

## 🏗️ Architecture

VaultMind Forge uses a modern web architecture:

```
┌─────────────────────────────────────────────────┐
│           Frontend (React + Vite)               │
│  ┌──────────────────────────────────────────┐   │
│  │ ReactFlow Canvas │ Node Palette │ Props │   │
│  │ Execution Panel  │ Toast Notifications  │   │
│  └──────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────────────┐
│          Backend (FastAPI + Uvicorn)            │
│  ┌──────────────────────────────────────────┐   │
│  │ API Endpoints │ Rate Limiter │ Auth      │   │
│  │ Error Handler │ Logging │ Validators    │   │
│  └──────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│       Processing Layer (Python + PyTorch)       │
│  ┌──────────────────────────────────────────┐   │
│  │ Workflow Executor │ Node Processors      │   │
│  │ SDXL Pipeline │ File Operations          │   │
│  └──────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│         Data Layer (SQLite + Filesystem)        │
│  ┌──────────────────────────────────────────┐   │
│  │ Workflows │ Assets │ Logs │ Checkpoints  │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **SQLAlchemy** - Database ORM
- **slowapi** - Rate limiting
- **PyTorch** - Deep learning framework
- **Transformers** - Hugging Face model library
- **Diffusers** - Stable Diffusion pipeline

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tooling
- **ReactFlow** - Visual node editor
- **Zustand** - State management
- **Framer Motion** - Animations
- **react-hot-toast** - Notifications
- **Tailwind CSS** - Styling

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Systemd** - Linux service management
- **NSSM** - Windows service wrapper
- **Nginx** - Reverse proxy (optional)
- **Redis** - Distributed rate limiting (optional)

---

## 📚 Documentation

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Installation, configuration, production setup
- **[API Reference](http://localhost:8000/docs)** - Interactive OpenAPI documentation
- **[Package Building](packaging/README.md)** - Creating Arch/Windows installers

---

## 🔧 Configuration

VaultMind Forge is configured via environment variables (`.env` file):

### Required
```env
VAULTMIND_API_KEY=your-generated-api-key-here
```

### Security
```env
VAULTMIND_AUTH_ENABLED=true  # Enable API authentication (default: true)
```

### Logging
```env
VAULTMIND_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Paths
```env
VAULTMIND_MODELS_DIR=./models
VAULTMIND_OUTPUT_DIR=./output
VAULTMIND_CHECKPOINTS_DIR=./checkpoints
```

### Rate Limiting
```env
RATE_LIMIT_STORAGE=memory://  # or redis://localhost:6379
```

See `.env.example` for all available options.

---

## 🚦 Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- 8GB RAM minimum (16GB recommended for AI models)

### Setup

```bash
# 1. Clone repository
git clone https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration.git
cd LinuxProceduralGeneration

# 2. Create Python virtual environment
python -m venv .venv312
source .venv312/bin/activate  # Windows: .venv312\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set up frontend
cd web_ui
npm install
npm run dev  # Runs on http://localhost:5173

# 5. In another terminal, start backend
cd backend
uvicorn api:app --reload --port 8000
```

### Running Tests

```bash
# Python tests
pytest

# Frontend tests
cd web_ui
npm test

# E2E tests
npm run test:e2e
```

---

## 🎯 Roadmap

- [ ] **Plugin System**: Third-party node development
- [ ] **Cloud Deployment**: AWS/GCP/Azure templates
- [ ] **Multi-Model Support**: DALL-E 3, Midjourney integration
- [ ] **Collaboration**: Real-time multi-user workflows
- [ ] **Version Control**: Git-like workflow versioning
- [ ] **Mobile App**: iOS/Android remote monitoring

---

## 📜 License

VaultMind Forge is licensed under the **Michael Sovereign License v1.0**.

**TL;DR**: This is proprietary software. You may:
- ✅ View, evaluate, and test the software
- ✅ Use for personal, non-commercial purposes during beta
- ❌ Redistribute, modify, or use commercially without permission

See [LICENSE.md](LICENSE.md) for full terms.

For commercial licensing inquiries, contact: barefoot.mike.of.horme@gmail.com

---

## 🙏 Credits

**Created by**: Michael Shortland ([@BarefootMikeOfHorme](https://github.com/BarefootMikeOfHorme))

**Development Assistance**:
- Claude (Anthropic) - Architecture design, security implementation, deployment infrastructure
- Open source community - Libraries and frameworks that made this possible

**Special Thanks**:
- Hugging Face for Transformers and Diffusers
- FastAPI team for the excellent web framework
- ReactFlow team for the visual editor foundation
- The entire Python and JavaScript ecosystems

---

## 🤝 Contributing

While VaultMind Forge is proprietary software, we welcome:
- **Bug Reports**: [Open an issue](https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration/issues)
- **Feature Requests**: Suggest improvements
- **Documentation**: Help improve docs and examples

For commercial partnerships or contributions, please contact the author.

---

## 📞 Support

- **Documentation**: [/docs](./docs/)
- **Issues**: [GitHub Issues](https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration/issues)
- **Email**: barefoot.mike.of.horme@gmail.com

---

## 🏆 Acknowledgments

This project builds on the shoulders of giants:
- **PyTorch** - Deep learning infrastructure
- **Stability AI** - Stable Diffusion models
- **Anthropic** - Claude AI assistance
- **Vercel** - Vite build system
- **Meta** - React framework

---

**VaultMind Forge** — *Forging the future of AI content creation.*

[![Star this repo](https://img.shields.io/github/stars/BarefootMikeOfHorme/LinuxProceduralGeneration?style=social)](https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration)
