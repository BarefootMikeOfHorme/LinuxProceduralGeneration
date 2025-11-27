# Real SDXL Generation Guide

**Date:** 2025-11-16
**Status:** ✅ Fully Implemented & Ready to Use

---

## 🎉 Good News: SDXL Backend is Complete!

The real SDXL backend is fully implemented in `forge_diffusion/generator.py`. All dependencies are already installed!

**Installed Libraries:**
- ✅ torch 2.9.0
- ✅ diffusers 0.35.2
- ✅ transformers 4.57.1
- ✅ accelerate 1.11.0
- ✅ safetensors 0.6.2

**You're Ready to Generate!**

---

## 🚀 How to Generate with Real SDXL

### Option 1: SDXL Turbo (Fastest - 4 steps)

```bash
cd C:\Users\Administrator\Desktop\Projects\LPG

python examples/generate_sdxl.py \
  --prompt "california girl at the beach tanning in her shades sipping a mai tai in her bikini, highly detailed, photorealistic" \
  --backend sdxl_turbo \
  --width 512 \
  --height 512 \
  --steps 4 \
  --output ./beach_girl_real
```

**SDXL Turbo Specs:**
- Speed: ~4 seconds per image (on GPU)
- Steps: 4 (optimized for speed)
- Quality: Very good
- Model Size: ~6.9 GB (downloads on first run)

### Option 2: SDXL Base (Highest Quality)

```bash
python examples/generate_sdxl.py \
  --prompt "california girl at the beach tanning in her shades sipping a mai tai in her bikini, highly detailed, photorealistic" \
  --backend sdxl_base \
  --width 1024 \
  --height 1024 \
  --steps 30 \
  --use-refiner \
  --output ./beach_girl_hq
```

**SDXL Base Specs:**
- Speed: ~30 seconds per image (on GPU)
- Steps: 20-50 (higher = better quality)
- Quality: Excellent
- Model Size: ~6.9 GB base + ~6.2 GB refiner (optional)

---

## 📝 CLI Usage

### Basic Generation

```bash
# Generate with default settings
python examples/generate_sdxl.py \
  --prompt "your prompt here" \
  --backend sdxl_turbo

# High resolution with more steps
python examples/generate_sdxl.py \
  --prompt "your prompt here" \
  --backend sdxl_base \
  --width 1024 \
  --height 1024 \
  --steps 50

# Generate multiple images
python examples/generate_sdxl.py \
  --prompt "your prompt here" \
  --backend sdxl_turbo \
  --batch 4
```

### Using the Main CLI

```bash
# Generate via vaultmind_cli.py
python vaultmind_cli.py generate \
  "your prompt here" \
  --width 1024 \
  --height 1024 \
  --output ./my_output
```

---

## 🎨 Generation Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `--prompt` | Required | - | Main generation prompt |
| `--negative-prompt` | "low quality..." | - | Things to avoid |
| `--width` | 1024 | 512-2048 | Image width (multiple of 64) |
| `--height` | 1024 | 512-2048 | Image height (multiple of 64) |
| `--steps` | 30 | 4-100 | Diffusion steps (higher = better) |
| `--guidance-scale` | 7.5 | 1.0-20.0 | Prompt adherence (7.5 recommended) |
| `--batch` | 1 | 1-10 | Number of images |
| `--seed` | Random | 0-∞ | For reproducibility |
| `--backend` | placeholder | sdxl_turbo, sdxl_base | Generation backend |
| `--use-refiner` | False | - | Use SDXL refiner (sdxl_base only) |

---

## 💻 Python API Usage

```python
from vaultmind_forge.forge_diffusion.generator import (
    DiffusionGenerator,
    GenerationConfig,
    GenerationBackend
)

# Initialize generator
generator = DiffusionGenerator(
    backend=GenerationBackend.SDXL_TURBO
)

# Load models
generator.load_models(
    enable_xformers=True,
    enable_attention_slicing=True
)

# Configure generation
config = GenerationConfig(
    prompt="california girl at the beach, photorealistic",
    width=512,
    height=512,
    steps=4,
    batch_size=1
)

# Generate
result = generator.generate(config)

# Save
result.images[0].save("output.png")

print(f"Generated in {result.generation_time:.2f}s")
print(f"Seed: {result.seed}")
```

---

## 🖼️ Recommended Settings

### For Speed (Testing)
```bash
--backend sdxl_turbo --width 512 --height 512 --steps 4
```
Generation time: ~4 seconds

### For Quality (Production)
```bash
--backend sdxl_base --width 1024 --height 1024 --steps 30 --use-refiner
```
Generation time: ~30 seconds

### For High Resolution
```bash
--backend sdxl_base --width 1536 --height 1536 --steps 40
```
Generation time: ~60 seconds

---

## 📥 First Run - Model Download

On the first run with `--backend sdxl_turbo` or `sdxl_base`, the models will download from Hugging Face:

```
Step 1: Initializing SDXL Turbo...
Step 2: Loading models (this may take a few minutes on first run)...
         Downloading from Hugging Face if needed...
Downloading: 100%|██████████| 6.94GB/6.94GB [05:23<00:00, 21.4MB/s]
Step 3: Configuring generation...
Step 4: Generating image...
SUCCESS! Image saved to: output_real_sdxl.png
```

**Download Size:**
- SDXL Turbo: ~6.9 GB
- SDXL Base: ~6.9 GB
- SDXL Refiner: ~6.2 GB (optional)

**Cache Location:**
`C:\Users\Administrator\.cache\vaultmind_forge\`

---

## 🎯 Example: Generate Your Beach Girl

```bash
python examples/generate_sdxl.py \
  --prompt "california girl at the beach tanning in her shades sipping a mai tai in her bikini, highly detailed, photorealistic, professional photography, golden hour lighting, 4k" \
  --backend sdxl_turbo \
  --width 512 \
  --height 512 \
  --steps 4 \
  --output ./beach_girl_sdxl_turbo

# Result: Photorealistic beach scene in ~4 seconds!
```

For higher quality:
```bash
python examples/generate_sdxl.py \
  --prompt "california girl at the beach tanning in her shades sipping a mai tai in her bikini, highly detailed, photorealistic, professional photography, golden hour lighting, 4k" \
  --backend sdxl_base \
  --width 1024 \
  --height 1024 \
  --steps 30 \
  --use-refiner \
  --output ./beach_girl_sdxl_base

# Result: Studio-quality image in ~30 seconds!
```

---

## 🔧 Memory Requirements

**Minimum (SDXL Turbo, 512x512):**
- VRAM: 6 GB
- RAM: 16 GB

**Recommended (SDXL Base, 1024x1024):**
- VRAM: 10 GB
- RAM: 32 GB

**For 4K+ resolutions:**
- VRAM: 24 GB
- RAM: 64 GB

**Memory Optimizations Available:**
- `enable_xformers` - Memory efficient attention (automatically enabled)
- `enable_attention_slicing` - Reduce VRAM usage (automatically enabled)
- `enable_cpu_offload` - For very low VRAM (optional)

---

## 🐛 Troubleshooting

### "CUDA out of memory"
**Solution:** Reduce resolution or enable CPU offload:
```python
generator.load_models(enable_cpu_offload=True)
```

### "Model not found"
**Solution:** Check internet connection. Models download from Hugging Face on first run.

### "Generation too slow"
**Solution:** Use SDXL Turbo instead of Base:
```bash
--backend sdxl_turbo --steps 4
```

---

## ✅ Verification

Test the real backend with this simple command:
```bash
python test_real_sdxl.py
```

This will:
1. Load SDXL Turbo
2. Generate a test image
3. Save to `output_real_sdxl.png`

---

## 🎉 You're All Set!

The real SDXL backend is production-ready. Just change `--backend placeholder` to `--backend sdxl_turbo` or `--backend sdxl_base` and you'll get real photorealistic AI-generated images!

**Next Steps:**
1. Run your first real generation with `--backend sdxl_turbo`
2. Experiment with prompts and settings
3. Use `--use-refiner` for maximum quality
4. Integrate with your workflows via Python API

Happy generating! 🎨
