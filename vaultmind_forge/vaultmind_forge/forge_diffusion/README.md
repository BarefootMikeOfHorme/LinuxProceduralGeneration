# forge_diffusion

Production-grade SDXL diffusion generator with advanced features for VaultMind Forge.

## Features

- **Multiple Backends**: SDXL Base, SDXL Turbo, SD 1.5, Kandinsky, Placeholder
- **SDXL Refiner Support**: Optional refinement pass for enhanced quality
- **Multi-Pass Generation**: Generate multiple variations and select best
- **Memory Optimization**: xFormers, attention slicing, CPU offload
- **ControlNet Integration**: Depth, Canny, Pose, Segmentation, etc.
- **IP-Adapter Support**: Style transfer and reference image guidance
- **Helper Pass System**: Structured control passes for precision
- **Validation Integration**: Built-in support for quality validation
- **Comprehensive Error Handling**: Detailed exceptions and logging

## Quick Start

### Basic Generation

```python
from vaultmind_forge.forge_diffusion import (
    DiffusionGenerator,
    GenerationConfig,
    GenerationBackend
)

# Initialize generator
generator = DiffusionGenerator(backend=GenerationBackend.SDXL_BASE)
generator.load_models(device="cuda")

# Configure generation
config = GenerationConfig(
    prompt="a serene forest landscape, highly detailed",
    width=1024,
    height=1024,
    steps=30,
    guidance_scale=7.5
)

# Generate
result = generator.generate(config)
result.images[0].save("output.png")

print(f"Generated in {result.generation_time:.2f}s with seed {result.seed}")
```

### Multi-Pass with Validation

```python
def my_validator(image):
    """Custom validation function"""
    # Return (passed: bool, score: float)
    return True, 0.85

# Generate multiple variations
best, all_results = generator.generate_multi_pass(
    config,
    num_passes=5,
    validator=my_validator,
    min_score=0.7
)

best.images[0].save("best_output.png")
print(f"Best score: {best.metadata['validation_score']}")
```

### Placeholder Mode (No GPU)

```python
# Great for testing without GPU
generator = DiffusionGenerator(backend=GenerationBackend.PLACEHOLDER)
generator.load_models()  # No models loaded

config = GenerationConfig(
    prompt="test image",
    width=512,
    height=512
)

result = generator.generate(config)
# Generates colored placeholder with text label
```

## Configuration

### GenerationConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | str | *required* | Main generation prompt |
| `negative_prompt` | str | "low quality..." | Negative guidance prompt |
| `width` | int | 1024 | Output width (multiple of 64) |
| `height` | int | 1024 | Output height (multiple of 64) |
| `steps` | int | 30 | Diffusion steps (20-100) |
| `guidance_scale` | float | 7.5 | CFG scale (1.0-20.0) |
| `seed` | int\|None | None | Random seed (None = random) |
| `batch_size` | int | 1 | Images per generation |
| `use_refiner` | bool | False | Use SDXL refiner |
| `refiner_start` | float | 0.85 | Refiner start ratio |
| `helper_passes` | List | [] | Helper passes to apply |

### Generation Backends

- `SDXL_BASE`: Stable Diffusion XL 1.0 base model
- `SDXL_TURBO`: SDXL Turbo (faster, fewer steps)
- `SD_1_5`: Stable Diffusion 1.5 (legacy)
- `KANDINSKY`: Kandinsky 2.2
- `PLACEHOLDER`: Testing mode (no GPU required)

### Helper Pass Types

- `DEPTH_MAP`: Depth-based conditioning
- `CANNY_EDGE`: Edge detection control
- `POSE_SKELETON`: Human pose control
- `SEGMENTATION`: Semantic segmentation
- `NORMAL_MAP`: Surface normal control
- `LINE_ART`: Line art conditioning
- `SCRIBBLE`: Scribble-based control
- `COLOR_PALETTE`: Color palette enforcement
- `IP_ADAPTER`: Image prompt adaptation

## Advanced Usage

### With Refiner

```python
config = GenerationConfig(
    prompt="a majestic castle on a hill",
    width=1024,
    height=1024,
    steps=40,
    use_refiner=True,
    refiner_start=0.85  # Start refiner at 85% through generation
)

result = generator.generate(config)
```

### Memory Optimization

```python
# For low VRAM (8GB or less)
generator.load_models(
    device="cuda",
    enable_xformers=True,
    enable_attention_slicing=True,
    enable_cpu_offload=True  # Sequential offload for very low VRAM
)
```

### Progress Callback

```python
def progress_callback(step, total_steps):
    print(f"Step {step}/{total_steps}")

result = generator.generate(config, callback=progress_callback)
```

### Model Unloading

```python
# Free memory when done
generator.unload_models()
```

## Integration with VaultMind Forge

### With Lineage Tracking

```python
from vaultmind_forge.forge_lineage import LineageLogger
from vaultmind_forge.forge_validator import Validator

logger = LineageLogger(root=Path("./output"))
validator = Validator(threshold=0.7)

# Generate
result = generator.generate(config)

# Validate
validation = validator.validate_asset(result.images[0])

# Log to lineage
logger.write_report(
    job_id="job-123",
    pass_name="generation",
    decision="accept" if validation.status == "pass" else "reject",
    report={
        "seed": result.seed,
        "score": validation.score,
        "generation_time": result.generation_time
    }
)
```

### With Executor DAG

```python
from vaultmind_forge.forge_executor import DAG, Task, Executor

async def gen_task():
    config = GenerationConfig(prompt="test")
    result = generator.generate(config)
    return result

dag = DAG()
dag.add(Task(name="generate", func=gen_task, deps=set()))

executor = Executor(dag)
await executor.run()
```

## Error Handling

```python
from vaultmind_forge.forge_diffusion import (
    ModelNotLoadedError,
    GenerationFailedError,
    InvalidConfigurationError
)

try:
    result = generator.generate(config)
except ModelNotLoadedError:
    print("Models not loaded. Call load_models() first")
except GenerationFailedError as e:
    print(f"Generation failed: {e}")
except InvalidConfigurationError as e:
    print(f"Invalid config: {e}")
```

## Requirements

```bash
pip install torch diffusers transformers accelerate safetensors
pip install pillow numpy
```

Optional:
```bash
pip install xformers  # For memory efficiency
```

## Performance Tips

1. **Use Turbo for Speed**: `backend=GenerationBackend.SDXL_TURBO` with `steps=4-8`
2. **Enable xFormers**: 30-50% memory reduction
3. **Attention Slicing**: Another 20% memory reduction
4. **CPU Offload**: For very low VRAM (< 8GB)
5. **Lower Resolution**: Use 768x768 or 512x512 for faster generation
6. **Batch Size**: Keep at 1 for most use cases
7. **FP16**: Use `dtype=torch.float16` (default)

## License

Part of VaultMind Forge - See main LICENSE file.
