# Python CLI Status Report

**Date**: 2025-12-04
**Purpose**: Document Python CLI status and restoration needs

---

## Current Status: ⚠️ NEEDS RESTORATION

The Python CLI exists but has installation issues that need to be resolved.

---

## What Exists ✅

### CLI Entry Point
**File**: `vaultmind_forge/forge_cli.py`
**Package**: `vaultmind-forge` (installed in .venv312)
**Command**: `forge` (configured in pyproject.toml)

### Available Commands (from source code)

```python
# vaultmind_forge/forge_cli.py implements:

1. forge version           # Show version
2. forge logo              # Display ASCII art
3. forge monitor           # Live system dashboard
4. forge generate          # SDXL image generation
```

### Package Configuration

**pyproject.toml**:
```toml
[project.scripts]
forge = "vaultmind_forge.forge_cli:app"
```

---

## Current Issues ❌

### Issue 1: Module Import Error

**Error**:
```
ModuleNotFoundError: No module named 'vaultmind_forge'
```

**Cause**:
- The editable install didn't create proper package structure
- The `pyproject.toml` has incorrect `[tool.setuptools.packages.find]` configuration
- Currently: `where = ["vaultmind_forge"]`
- Should be: `where = ["."]`

### Issue 2: Cached Executable

**Problem**:
- Old `forge.exe` cached in `.venv312/Scripts/`
- Still references old import paths
- Needs regeneration after fix

---

## Proposed Fixes

### Fix 1: Update pyproject.toml

**Change**:
```toml
# BEFORE (incorrect)
[tool.setuptools.packages.find]
where = ["vaultmind_forge"]
include = ["*"]

# AFTER (correct)
[tool.setuptools.packages.find]
where = ["."]
include = ["vaultmind_forge*"]
```

### Fix 2: Reinstall Package

```bash
# In project root
cd C:\Users\Administrator\Desktop\Projects\LPG

# Uninstall
.venv312/Scripts/pip uninstall vaultmind-forge -y

# Reinstall in editable mode
.venv312/Scripts/pip install -e .

# Verify
.venv312/Scripts/forge --help
```

### Fix 3: Alternative - Direct Python Execution

If package install fails, use direct execution:

```bash
# Set PYTHONPATH
export PYTHONPATH=C:\Users\Administrator\Desktop\Projects\LPG

# Run CLI directly
.venv312/Scripts/python -m vaultmind_forge.forge_cli --help
```

---

## CLI Features (Once Working)

### 1. Image Generation

```bash
forge generate "fantasy warrior" \
    --output warrior.png \
    --steps 30 \
    --width 1024 \
    --height 1024 \
    --cfg-scale 7.5
```

**Features**:
- SDXL generation
- Terminal FUI interface (fancy UI)
- Progress tracking
- Configurable parameters

### 2. System Monitoring

```bash
forge monitor --refresh 1.0
```

**Features**:
- Real-time CPU/GPU/Memory stats
- Live dashboard in terminal
- Resource utilization tracking

### 3. Logo Display

```bash
forge logo --style full
```

**Styles**: compact, simple, full

---

## Python API (Working Alternative)

While CLI is being fixed, use direct Python imports:

### Direct Import Method

```python
# Add to PYTHONPATH or run from project root
import sys
sys.path.insert(0, 'C:/Users/Administrator/Desktop/Projects/LPG')

from vaultmind_forge.forge_diffusion import SDXLGenerator
from vaultmind_forge.forge_diffusion.generator import GenerationConfig

# Initialize
generator = SDXLGenerator()
generator.initialize()

# Generate
config = GenerationConfig(
    prompt="fantasy warrior",
    width=1024,
    height=1024,
    steps=30,
    guidance_scale=7.5
)

result = generator.generate(config)
result.images[0].save("output.png")
```

**Advantages**:
- No installation issues
- Full control
- Faster (no CLI overhead)
- Works immediately

---

## Testing Plan

### Step 1: Verify Python Import

```python
import sys
sys.path.insert(0, 'C:/Users/Administrator/Desktop/Projects/LPG')

try:
    import vaultmind_forge
    print(f"✅ Package found: {vaultmind_forge.__version__}")
except ImportError as e:
    print(f"❌ Import failed: {e}")
```

### Step 2: Test forge_cli Module

```python
from vaultmind_forge import forge_cli
print(f"✅ forge_cli module loaded: {forge_cli.__file__}")
```

### Step 3: Test CLI Commands

```bash
# After fixing pyproject.toml
forge version
forge logo
forge monitor --refresh 2.0
```

### Step 4: Test Generation

```bash
forge generate "test prompt" --output test.png --steps 5
```

---

## Comparison: CLI vs Direct Python

| Feature | CLI (`forge`) | Python API |
|---------|---------------|------------|
| **Status** | ⚠️ Needs fix | ✅ Working |
| **Ease of Use** | Easy | Medium |
| **Speed** | Fast | Fastest |
| **Flexibility** | Limited | Full |
| **Dependencies** | Requires install | Requires PYTHONPATH |
| **Automation** | Bash scripts | Python scripts |
| **Best For** | Quick tasks | Complex workflows |

---

## Recommended Workflow

### For Now (CLI Broken)

**Use Python API**:
```python
# Create quick_generate.py
import sys
sys.path.insert(0, 'C:/Users/Administrator/Desktop/Projects/LPG')

from vaultmind_forge.forge_diffusion import SDXLGenerator
from vaultmind_forge.forge_diffusion.generator import GenerationConfig

def generate(prompt, output="output.png"):
    generator = SDXLGenerator()
    generator.initialize()

    config = GenerationConfig(
        prompt=prompt,
        width=1024,
        height=1024,
        steps=30
    )

    result = generator.generate(config)
    result.images[0].save(output)
    print(f"✅ Generated: {output}")

if __name__ == "__main__":
    import sys
    generate(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "output.png")
```

**Usage**:
```bash
.venv312/Scripts/python quick_generate.py "fantasy warrior" warrior.png
```

### After CLI Fix

**Use both**:
- CLI for quick one-off tasks
- Python API for complex workflows and integration

---

## Action Items

### Immediate (High Priority)

- [ ] Fix `pyproject.toml` package discovery
- [ ] Reinstall package in editable mode
- [ ] Test `forge --help`
- [ ] Test `forge version`
- [ ] Test `forge generate`

### Short Term

- [ ] Create wrapper scripts for common CLI operations
- [ ] Add more CLI commands (validate, convert, etc.)
- [ ] Document all CLI commands
- [ ] Add CLI integration tests

### Long Term

- [ ] Add progress bars for all operations
- [ ] Add config file support (~/.forge/config.yaml)
- [ ] Add tab completion
- [ ] Add interactive mode
- [ ] Add workflow orchestration commands

---

## CLI Architecture

### Current Design

```
forge (executable)
  ↓
forge_cli.py (typer app)
  ↓
vaultmind_forge modules
  ↓
Rust/C++ validators (if needed)
```

### Expected Commands (Full Scope)

```bash
# Generation
forge generate <prompt>           # SDXL generation
forge generate-video <frames>     # Video creation
forge upscale <image>              # Super resolution

# Validation
forge validate <asset>             # Quality check
forge validate-batch <dir>         # Batch validation

# Conversion
forge convert <input> <output>     # Format conversion
forge convert-engine <asset> <engine>  # Engine-specific

# Monitoring
forge monitor                      # Live dashboard
forge stats                        # System stats

# Lineage
forge lineage <asset>              # Show lineage
forge lineage-export <id>          # Export lineage

# Workflow
forge workflow run <file>          # Execute workflow
forge workflow validate <file>     # Validate workflow

# System
forge version                      # Show version
forge logo                         # ASCII art
forge config                       # Show/edit config
forge doctor                       # System check
```

---

## Comparison with Web UI

### CLI Advantages ✅

- **Speed**: No HTTP overhead
- **Automation**: Scriptable
- **Headless**: Works on servers
- **Efficiency**: Lower resource usage
- **CI/CD**: Pipeline integration

### Web UI Advantages ✅

- **Visualization**: Real-time preview
- **Ease**: Beginner-friendly
- **Discovery**: Browse capabilities
- **Remote**: Browser access
- **Collaborative**: Multi-user

### Both Are Important

- CLI for power users and automation
- Web UI for visualization and exploration
- Python API for integration and custom tools

**All three should be equally maintained.**

---

## Next Steps

1. **Fix CLI Installation**
   - Update pyproject.toml
   - Reinstall package
   - Test all commands

2. **Document CLI Usage**
   - Create CLI_GUIDE.md
   - Add examples
   - Add troubleshooting

3. **Expand CLI Features**
   - Add missing commands
   - Improve UX
   - Add tests

4. **Ensure Parity**
   - Everything in Web UI → CLI
   - Everything in CLI → Python API
   - All three interfaces equal

---

**Status**: CLI exists but needs fixes
**Priority**: High (restore Python-first philosophy)
**Timeline**: 1-2 hours to fix, test, document
