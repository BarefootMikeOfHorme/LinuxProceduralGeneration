# 🧬 VaultMind Forge

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/rust-1.70%2B-orange)](https://www.rust-lang.org/)
[![C++](https://img.shields.io/badge/c%2B%2B-17%2B-00599C)](https://isocpp.org/)
[![License](https://img.shields.io/badge/license-proprietary-red)](./LICENSE.md)

**Multi-Language Procedural Content Generation Engine**

VaultMind Forge is a high-performance procedural content generation engine combining Python's orchestration capabilities with Rust's execution speed and C++'s specialized libraries. Features tab-based multi-modal editors for terrain, characters, audio, video, and workflows with AI-powered generation.

---

## 🚀 Features

### 🗺️ Multi-Modal Editors
- **Quick Gen**: Rapid procedural asset generation with presets
- **Terrain Editor**: Heightmap-based terrain with erosion, rivers, biomes
- **Character Editor**: Parametric character generation with rigging
- **Audio Editor**: Procedural sound synthesis and music generation
- **Video Editor**: Sequence composition with procedural effects
- **Workflow Manager**: Template-based generation pipelines

### ⚡ Performance Architecture
- **Python Orchestrator**: GUI, scripting, AI integration, workflow management
- **Rust Executor**: Performance-critical algorithms, parallel processing, geometry engine
- **C++ Specialized**: Game engine integration, physics, GPU compute

### 🔷 Geometry Engine
- **CSG Operations**: Union, difference, intersection with optimized mesh processing
- **Procedural Operations**: Extrude, revolve, loft, sweep, subdivision surfaces
- **Mesh Optimization**: LOD generation, compression, silhouette extraction
- **Multi-Engine Export**: Target-specific geometry for Unity, Godot, Unreal, custom engines

### 🤖 AI-Powered Generation
- **Stable Diffusion XL**: High-fidelity image generation
- **Prompt Engineering**: Built-in templates and refinement
- **Batch Processing**: Generate multiple variations efficiently
- **Neural Synthesis**: Audio and video generation with deep learning

### 🧩 Expandable Features
- **Context-Specific Nodes**: Modular components that expand for setup, collapse when complete
- **Workflow Templates**: Swappable presets for different scenarios
- **Scripting Integration**: Python API with Rust/C++ acceleration
- **Visual + Code Modes**: Hybrid interface supporting both paradigms

---

## 🏗️ Architecture

VaultMind Forge uses a polyglot architecture optimized for both developer experience and runtime performance. The architecture draws inspiration from multiple game engines and procedural generation tools:

- **Map_Generator** - Python orchestrator pattern with parameter-driven workflows
- **Lumix Engine** - Editor node → runtime compilation, expandable UI pattern
- **Ice Engine (Meshmerizer)** - CSG operations, mesh optimization, spatial structures
- **Godot Engine** - Multi-language performance model (GDScript + C++)
- **OpenSCAD** - Code-as-interface for procedural geometry

---

## 🛠️ Technology Stack

### Python Layer
- **PyQt6/CustomTkinter** - Native GUI framework
- **FastAPI** - API server
- **PyTorch + Transformers + Diffusers** - AI generation
- **PyO3** - Rust FFI bindings
- **NumPy/SciPy** - Scientific computing

### Rust Layer  
- **nalgebra** - Linear algebra
- **parry3d** - CSG operations
- **mesh-kit** - Mesh optimization
- **rayon** - Parallel processing
- **pyo3** - Python bindings

### C++ Layer
- **Eigen** - Matrix operations
- **Bullet/PhysX** - Physics
- **OpenCL/CUDA** - GPU compute

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- Rust 1.70+ (for building components)
- C++17 compiler
- 16GB RAM minimum
- GPU with 8GB+ VRAM (for AI)

### Quick Start

```bash
# Clone repository
git clone https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration.git
cd LinuxProceduralGeneration

# Create virtual environment
python -m venv .venv312
source .venv312/bin/activate  # Windows: .venv312\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env

# Launch
python -m vaultmind_forge
```

---

## 🎮 Usage

### Tab-Based Interface

#### Quick Gen
Rapid asset generation with one-click presets

#### Terrain
Advanced heightmap-based terrain with erosion simulation

#### Character  
Parametric character creation with rigging

#### Audio
Procedural sound synthesis

#### Video
Sequence composition with AI

#### Workflow
Template-based pipeline management

### Python API

```python
from vaultmind_forge import terrain, geometry

# Generate terrain (Rust accelerated)
heightmap = terrain.generate(
    algorithm="perlin",
    size=(1024, 1024),
    octaves=6
)

# CSG operations (Rust engine)
base = geometry.box(size=(10, 10, 10))
cutout = geometry.sphere(radius=6)
result = geometry.difference(base, cutout)
result.export("chamber.fbx", engine="unity")
```

---

## 🎯 Roadmap

### Phase 1: Foundation (Current)
- [x] Python backend with FastAPI
- [x] AI generation pipeline
- [x] Analytics and monitoring
- [ ] PyQt6 GUI

### Phase 2: Rust Integration
- [ ] Geometry engine with PyO3
- [ ] CSG operations
- [ ] Parallel terrain generation

### Phase 3: Editors
- [ ] Quick Gen, Terrain, Character editors

### Phase 4: C++ Specialization
- [ ] Physics, GPU compute, audio/video

---

## 📜 License

VaultMind Forge is licensed under the **Michael Sovereign License v1.0**.

**TL;DR**: Proprietary software - view and test freely, commercial use requires permission.

See [LICENSE.md](LICENSE.md) for full terms.

Contact: barefoot.mike.of.horme@gmail.com

---

## 🙏 Credits

**Created by**: Michael Shortland ([@BarefootMikeOfHorme](https://github.com/BarefootMikeOfHorme))

**Architectural Inspiration**:
- Map_Generator - Parameter-driven generation
- Lumix Engine - Node editor patterns
- Ice Engine - Meshmerizer geometry operations
- Godot Engine - Multi-language architecture
- OpenSCAD - Declarative geometry

**Development Assistance**:
- Claude (Anthropic)
- Open source community

---

**VaultMind Forge** — *Multi-language procedural content generation*

[![Star this repo](https://img.shields.io/github/stars/BarefootMikeOfHorme/LinuxProceduralGeneration?style=social)](https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration)
