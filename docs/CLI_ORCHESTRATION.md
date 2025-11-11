# VaultMind Forge CLI - Multi-Language Orchestration System

**Version:** 0.1.0
**Status:** Development - Stage 1 Complete
**Date:** 2025-11-11

---

## Overview

VaultMind Forge CLI is a production-grade orchestration platform that conducts a symphony of languages:

- 🐍 **Python** - AI/ML operations (SDXL, agents, validation)
- ⚡ **Rust** - Performance-critical tasks (terrain, mesh, physics)
- ⚙️ **C++** - Optimized modules
- 🟢 **Node.js** - Async orchestration and web interfaces

All working together through an intelligent, beautiful command-line interface.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         VaultMind CLI (Python)                      │
│  - Terminal UI (Rich library)                       │
│  - Command processing                               │
│  - Workflow orchestration                           │
└─────────────┬───────────────────────────────────────┘
              │
    ┌─────────┴─────────┬──────────────┬─────────────┐
    │                   │              │             │
    ▼                   ▼              ▼             ▼
┌─────────┐      ┌──────────┐   ┌─────────┐   ┌──────────┐
│ Workflow│      │  Agent   │   │ Process │   │  Stats   │
│ Engine  │      │ Network  │   │Orchest. │   │ Monitor  │
└─────────┘      └──────────┘   └─────────┘   └──────────┘
    │                   │              │             │
    │         ┌─────────┴──────┬───────┴─────┬───────┘
    │         │                │             │
    ▼         ▼                ▼             ▼
┌─────────────────────────────────────────────────────┐
│              Execution Layer                        │
│                                                     │
│  Python Scripts  │  Rust Binaries  │  C++ Modules │
│  - SDXL Gen      │  - Terrain      │  - Physics   │
│  - Agents        │  - Mesh Ops     │  - Compute   │
│  - Validation    │  - Performance  │  - Legacy    │
└─────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Workflow Engine (`workflow_engine.py`)

**Features:**
- ✅ DAG (Directed Acyclic Graph) execution
- ✅ Parallel task processing with dependency resolution
- ✅ Resource management (GPU locks, agent allocation)
- ✅ Checkpoint/recovery system
- ✅ Real-time progress tracking
- ✅ Automatic retry on failure

**Example Usage:**
```python
from vaultmind_forge.cli.workflow_engine import WorkflowEngine, TaskType

# Create workflow
workflow = engine.create_workflow(
    name="Image Generation Pipeline",
    max_parallel=4
)

# Add tasks with dependencies
task1 = engine.add_task_to_workflow(
    workflow.id,
    name="Enhance Prompt",
    task_type=TaskType.ENHANCEMENT,
    executor="prompt_refiner"
)

task2 = engine.add_task_to_workflow(
    workflow.id,
    name="Generate Image",
    task_type=TaskType.GENERATION,
    depends_on=[task1.id],
    requires_gpu=True
)

# Execute
await engine.execute_workflow(workflow.id)
```

### 2. Agent Collaboration Network (`agent_network.py`)

**Features:**
- ✅ Agent-to-agent messaging
- ✅ Collaborative task solving
- ✅ Proposal and voting system
- ✅ Dynamic team formation
- ✅ Knowledge sharing

**Example Usage:**
```python
from vaultmind_forge.cli.agent_network import AgentNetwork

# Create collaborative task
task_id = await network.create_collaborative_task(
    name="Complex Generation",
    description="Multi-agent image generation with validation",
    required_agents=[
        AgentType.PROMPT,
        AgentType.PARAMETER,
        AgentType.QUALITY
    ]
)

# Execute with agent collaboration
results = await network.execute_collaborative_task(task_id)
```

### 3. Process Orchestrator (`process_orchestrator.py`)

**Features:**
- ✅ Multi-language process spawning
- ✅ Output capture and streaming
- ✅ Timeout handling
- ✅ JSON-based inter-process communication
- ✅ Process lifecycle management

**Example Usage:**
```python
# Execute Python script
result = orchestrator.execute_python(
    script_path=Path("scripts/generate.py"),
    args=["--prompt", "sunset"],
    venv_path=Path(".venv312"),
    timeout=300
)

# Execute Rust binary
result = orchestrator.execute_rust(
    binary_path=Path("target/release/terrain_gen"),
    args=["input.json", "output.json"]
)
```

### 4. Stats Monitor (`stats_monitor.py`)

**Features:**
- ✅ System resource monitoring (CPU, RAM, Disk)
- ✅ GPU/CUDA statistics (VRAM, utilization, temperature)
- ✅ Agent performance metrics
- ✅ Process execution statistics
- ✅ Real-time dashboard

**Metrics Tracked:**
- CPU utilization and core count
- Memory usage and availability
- GPU VRAM and utilization
- CUDA version and compute capability
- Agent task success rates
- Process execution duration

### 5. Terminal UI (`terminal_ui.py`)

**Features:**
- ✅ Rich-based beautiful terminal interface
- ✅ Progress bars and spinners
- ✅ Tables and panels
- ✅ Color-coded status indicators
- ✅ Interactive prompts
- ✅ Command history

---

## CLI Commands

### Agent Management

```bash
# List all agents
vaultmind agents

# Filter by status
vaultmind agents --status running

# Manage specific agent
vaultmind agent quality_guardian
```

### Process Orchestration

```bash
# View process dashboard
vaultmind processes

# Execute script/binary
vaultmind run python scripts/test.py --arg value
vaultmind run rust ./target/release/binary input.json
vaultmind run nodejs scripts/orchestrate.js
```

### Statistics & Monitoring

```bash
# View stats dashboard
vaultmind stats

# Real-time monitoring (watch mode)
vaultmind monitor --watch
```

### Image Generation

```bash
# Generate with SDXL
vaultmind generate "a futuristic cityscape" --width 1024 --height 1024 --steps 30

# Quick generation
vaultmind generate "sunset over mountains" --batch 4
```

### Interactive Mode

```bash
# Start interactive shell
vaultmind interactive

# Commands in interactive mode:
> agents          # List agents
> processes       # View processes
> stats           # Show statistics
> generate <prompt>  # Generate image
> help            # Show help
> exit            # Exit shell
```

---

## Specialist Agents

### Quality Guardian
- **Type:** Validation
- **Autonomy:** 75%
- **Capabilities:**
  - Artifact detection
  - Composition checking
  - Technical validation

### Prompt Refiner
- **Type:** Enhancement
- **Autonomy:** 85%
- **Capabilities:**
  - Clarity enhancement
  - Specificity boost
  - Negative prompt generation

### Parameter Optimizer
- **Type:** Optimization
- **Autonomy:** 70%
- **Capabilities:**
  - Step optimization
  - CFG tuning
  - Seed management

### Material Specialist
- **Type:** Analysis
- **Autonomy:** 75%
- **Capabilities:**
  - Material detection
  - Style analysis
  - Texture enhancement

### Resolution Expert
- **Type:** Optimization
- **Autonomy:** 80%
- **Capabilities:**
  - Resolution selection
  - Aspect ratio optimization

---

## Workflow Patterns

### Pattern 1: Simple Generation
```
Prompt → Generate → Save
```

### Pattern 2: Enhanced Generation
```
Prompt → Refine Prompt → Optimize Parameters → Generate → Validate → Save
```

### Pattern 3: Collaborative Generation
```
User Input → [Prompt Refiner + Parameter Optimizer] → Generate → Quality Guardian → Material Specialist → Resolution Expert → Final Output
```

### Pattern 4: Multi-Modal Pipeline
```
Text Prompt → [Image Generation + Audio Generation] → [Validation + Enhancement] → Combined Output
```

---

## CUDA Integration

### GPU Resource Management

The workflow engine automatically manages GPU resources:

```python
task = Task(
    name="SDXL Generation",
    type=TaskType.GENERATION,
    requires_gpu=True,  # Acquires GPU lock
    estimated_duration=30.0
)
```

### CUDA Statistics

Real-time CUDA monitoring:
- VRAM allocation and usage
- GPU utilization percentage
- Temperature monitoring
- Power draw
- Compute capability

### Optimizations Applied

- ✅ TF32 enabled for RTX 30xx/40xx GPUs
- ✅ cuDNN benchmark autotuner
- ✅ Memory-efficient attention
- ✅ VAE slicing for large images

---

## Communication Protocols

### Agent-to-Agent Messages

```python
# Request assistance
await network.send_message(
    sender_id="prompt_refiner",
    recipient_id="quality_guardian",
    message_type=MessageType.REQUEST,
    content={"request": "validate_prompt", "prompt": "..."}
)

# Broadcast information
await network.send_message(
    sender_id="parameter_optimizer",
    recipient_id="broadcast",
    message_type=MessageType.INFORM,
    content={"optimal_steps": 30, "cfg": 7.5}
)
```

### Proposal System

```python
# Create proposal
proposal_id = await network.create_proposal(
    proposer_id="quality_guardian",
    description="Regenerate with higher steps",
    action="regenerate",
    params={"steps": 50},
    required_votes=2
)

# Agents vote
await network.vote_on_proposal(proposal_id, "prompt_refiner", approve=True)
await network.vote_on_proposal(proposal_id, "parameter_optimizer", approve=True)
```

---

## JSON Communication (Language Interop)

### Python ↔ Rust

```python
# Execute Rust with JSON I/O
result = orchestrator.execute_with_json_io(
    process_type=ProcessType.RUST,
    executable=Path("target/release/terrain_gen"),
    input_data={
        "seed": 12345,
        "size": [1024, 1024],
        "octaves": 6
    }
)
# Returns: {"heightmap": [...], "metadata": {...}}
```

### Python ↔ Node.js

```python
# Execute Node.js orchestration
result = orchestrator.execute_with_json_io(
    process_type=ProcessType.NODEJS,
    executable=Path("scripts/orchestrate.js"),
    input_data={
        "workflow": "complex_generation",
        "agents": ["python_ai", "rust_terrain"]
    }
)
```

---

## Installation

### Requirements

```bash
# Python 3.12+ (for CUDA support)
# See docs/PYTHON_CUDA_SETUP.md

# Install CLI dependencies
pip install rich click psutil

# Optional: For full functionality
pip install torch torchvision diffusers transformers
```

### Setup

```bash
# Clone repository
cd VaultMind_Forge

# Create Python 3.12 venv (for CUDA)
python3.12 -m venv .venv312
.venv312/Scripts/activate  # Windows
source .venv312/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x vaultmind_cli.py  # Linux/Mac
```

---

## Current Status

### ✅ Stage 1 Complete

- [x] Terminal UI with Rich library
- [x] Agent management system
- [x] Process orchestration (Python/Rust/C++/Node.js)
- [x] Stats monitoring with GPU/CUDA
- [x] Workflow engine with DAG execution
- [x] Agent collaboration network
- [x] Command history
- [x] Interactive shell

### 🚧 Stage 2 (In Progress)

- [ ] Intelligent task decomposition with AI
- [ ] Multi-modal generation pipelines
- [ ] Distributed execution with worker pools
- [ ] Advanced checkpoint/recovery
- [ ] Rich TUI with live dashboards
- [ ] Plugin system for extensions

### 📋 Stage 3 (Planned)

- [ ] Web dashboard (Node.js/React)
- [ ] REST API for remote control
- [ ] Workflow templates library
- [ ] Agent learning and adaptation
- [ ] Performance profiling tools
- [ ] Distributed multi-machine execution

---

## Performance

### Workflow Execution

- **Parallel Tasks:** Up to 4 simultaneous (configurable)
- **Dependency Resolution:** O(V + E) topological sort
- **GPU Lock:** Zero-contention with asyncio
- **Checkpoint Interval:** 30 seconds (configurable)

### Agent Network

- **Message Latency:** <1ms (in-process)
- **Proposal Consensus:** 2-vote threshold (configurable)
- **Team Formation:** <100ms for 5 agents
- **Knowledge Sharing:** Lock-free read, synchronized write

---

## Troubleshooting

### CUDA Not Available

```bash
# Check Python version
python --version  # Should be 3.12.x

# Verify PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"

# See docs/CUDA_EVALUATION.md for detailed troubleshooting
```

### Agent Not Responding

```bash
# Check agent status
vaultmind agents

# View agent details
vaultmind agent <agent_id>

# Restart agent
vaultmind agent <agent_id>  # Then select "Restart"
```

### Process Execution Failed

```bash
# View process logs
vaultmind processes

# Check exit codes and stderr
```

---

## Contributing

VaultMind Forge CLI is designed for extensibility:

1. **Add New Agents:** Extend `AgentManager`
2. **Add Task Types:** Extend `TaskType` enum
3. **Add Language Support:** Extend `ProcessOrchestrator`
4. **Add Commands:** Add click commands to `vaultmind_cli.py`

---

## License

See LICENSE file in project root.

---

## Next Steps

1. Test CLI with `vaultmind --help`
2. Try interactive mode: `vaultmind interactive`
3. Generate your first image: `vaultmind generate "your prompt"`
4. Monitor GPU usage: `vaultmind monitor --watch`

**Let's orchestrate some AI! 🎭🤖**
