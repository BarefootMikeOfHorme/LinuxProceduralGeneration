# VaultMind Forge - System Architecture Map

**Generated**: $(date +%Y-%m-%d)
**Lineage Status**: Endgame Ritual - Production Hardening Phase

## 🏛️ System Overview

VaultMind Forge is a multi-tier AI orchestration system for procedural asset generation with the following layers:

### Layer 1: CLI Orchestration System
- **Entry Point**: `vaultmind_cli.py`
- **Purpose**: Command-line interface for orchestrating workflows
- **Components**:
  - Agent Manager (5 AI specialists)
  - Workflow Engine (DAG-based)
  - Distributed Executor (worker pools)
  - Task Decomposer (intelligent planning)
  - Process Orchestrator (multi-language coordination)

### Layer 2: Core Generation Engines
- **Diffusion**: SDXL, PixelWave, Waifu models
- **Procedural**: Noise-based terrain/texture generation
- **3D**: Mesh generation and manipulation
- **Video**: Video synthesis
- **SR**: Super-resolution upscaling

### Layer 3: Integration & Processing
- **Converter**: Format conversion (FBX, USD, MaterialX, DDS)
- **Validator**: Multi-backend quality assessment (Python, Rust, C++)
- **Packager**: Asset packaging and distribution
- **Lineage**: Complete provenance tracking

### Layer 4: AI Backend Integration
- **Tiered AI Manager**: Multi-provider orchestration
- **Backends**: Claude, GPT, Ollama, LM Studio, HuggingFace
- **Agents**: Quality Guardian, Prompt Refiner, Material Suggester, etc.

## 📁 Directory Structure

\`\`\`
LPG/
├── vaultmind_cli.py              # Main CLI entry point
├── vaultmind_forge/              # Core package
│   ├── cli/                      # CLI orchestration modules
│   │   ├── agent_manager.py      # 5 AI specialist agents
│   │   ├── workflow_engine.py    # DAG workflow execution
│   │   ├── distributed_executor.py # Worker pool management
│   │   ├── task_decomposer.py    # Intelligent task planning
│   │   └── process_orchestrator.py # Multi-language coordination
│   ├── forge_diffusion/          # Image generation
│   ├── forge_procedural/         # Noise-based generation
│   ├── forge_3d/                 # 3D mesh operations
│   ├── forge_converter/          # Format conversion
│   ├── forge_validator/          # Quality assessment
│   ├── forge_ai/                 # AI backend integrations
│   ├── forge_agents/             # Specialist AI agents
│   ├── forge_batch/              # Job queue & resource management
│   ├── forge_bots/               # Autonomous monitoring bots
│   └── forge_lineage/            # Provenance tracking
├── src/                          # Node.js API layer
│   ├── server.js                 # Express API server
│   ├── pythonBridge.js           # Python integration
│   └── forge/                    # Node.js modules
├── examples/                     # Integration examples
├── scripts/                      # Utility scripts
└── assets/                       # Asset storage hierarchy

## 🔌 Entry Points

### Primary Executables
1. **vaultmind_cli.py** - Main CLI orchestrator
2. **src/server.js** - Node.js API server
3. **vaultmind_forge/forge_cli.py** - Legacy CLI (forge-cli command)

### Integration Scripts
- examples/generate_sdxl.py - SDXL generation wrapper
- examples/complete_pipeline_demo.py - Full pipeline demonstration
- examples/three_tier_ai_system.py - AI tier demonstration

## 🔄 Data Flow

\`\`\`
User Command → CLI → Task Decomposer → Workflow Engine → Distributed Executor
                                           ↓
                              Agent Manager (5 specialists)
                                           ↓
                              Process Orchestrator
                                           ↓
                        ┌──────────────────┼──────────────────┐
                        ↓                  ↓                   ↓
                  Diffusion Gen      Procedural Gen       Converter
                        ↓                  ↓                   ↓
                  Validator (Rust/C++/Python multi-backend)
                        ↓                  ↓                   ↓
                   Lineage Tracking → Packager → Output
\`\`\`

## 🎯 Critical Integration Points

### Missing/Incomplete Integrations (Pre-Audit Findings)
1. ❌ examples/generate_sdxl.py - Called by CLI but incomplete
2. ⚠️  Agent Manager → AI Backend connection (data structures only)
3. ⚠️  Workflow executors using placeholder sleeps
4. ⚠️  CLI ↔ Node.js bridge incomplete
5. ⚠️  Distributed executor simulates workers

### Existing Integrations (Verified)
1. ✅ Lineage tracking system (SHA256-based provenance)
2. ✅ Multi-format converter (FBX, USD, MaterialX, DDS)
3. ✅ Tri-language validator (Python, Rust, C++)
4. ✅ Checkpoint/recovery system
5. ✅ GPU/system monitoring

## 🛡️ Security Considerations

### File I/O Paths
- Assets: \`assets/\` (input, output, validated, packages)
- Temp: \`assets/temp/\` (cache, intermediate, processing)
- Lineage: \`assets/lineage/\` (SHA256-named JSON files)
- Checkpoints: \`checkpoints/\`

### Permissions Model
- Read: All asset directories
- Write: output/, temp/, validated/, packages/, lineage/, checkpoints/
- Execute: Native validators (Rust/C++ binaries)

### Process Isolation
- Multi-language executors (Python, Rust, C++, Node.js)
- Worker pool isolation (distributed_executor.py)
- Async/await concurrency model

## 📊 Component Status Matrix

| Component | Language | Status | Integration | Tests |
|-----------|----------|--------|-------------|-------|
| CLI Orchestrator | Python | ✅ Complete | ⚠️ Partial | ✅ Yes |
| Workflow Engine | Python | ✅ Complete | ⚠️ Partial | ✅ Yes |
| Agent Manager | Python | ✅ Complete | ❌ No Backend | ✅ Yes |
| Distributed Executor | Python | ✅ Complete | ⚠️ Simulated | ✅ Yes |
| SDXL Generator | Python | ✅ Complete | ❌ No Wrapper | ⚠️ Partial |
| Procedural Gen | Python | ✅ Complete | ✅ Full | ✅ Yes |
| Format Converter | Python | ✅ Complete | ✅ Full | ✅ Yes |
| Validator (Python) | Python | ✅ Complete | ✅ Full | ✅ Yes |
| Validator (Rust) | Rust | ✅ Complete | ✅ Full | ⚠️ Partial |
| Validator (C++) | C++ | ✅ Complete | ✅ Full | ❌ No |
| Lineage Tracker | Python | ✅ Complete | ✅ Full | ✅ Yes |
| Node.js API | Node.js | ✅ Complete | ❌ No CLI Bridge | ❌ No |
| AI Backends | Python | ✅ Complete | ⚠️ Partial | ⚠️ Partial |

## 🔧 Build & Deployment

### Python Environment
- Package: \`vaultmind_forge\` (setuptools)
- Virtual env: \`.venv312/\`
- Dependencies: requirements.txt (inferred from imports)

### Node.js Environment
- Package: \`package.json\`
- Dependencies: \`node_modules/\`

### Native Components
- Rust validator: \`vaultmind_forge/native/rust/validator/\`
- C++ validator: \`vaultmind_forge/native/cpp/validator/\`

### Build System
- ❌ No Makefile
- ❌ No build.sh
- ❌ No Dockerfile
- ⚠️ CMake for C++ (partial)
- ✅ Cargo for Rust

## 🧪 Testing Infrastructure

### Existing Tests
- CLI component tests (\`vaultmind_forge/tests/test_cli_*.py\`)
- Integration tests (\`vaultmind_forge/tests/test_integrated_pipeline.py\`)
- Format handler tests
- Procedural generation tests
- Quality guardian tests

### Test Execution
- Framework: pytest (anyio backend for async)
- Coverage: ~60% estimated
- Missing: End-to-end workflow tests

---

**Status**: Architecture mapped. Proceeding to code audit.
