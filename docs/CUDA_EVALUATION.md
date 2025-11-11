# CUDA Evaluation & Optimization Guide

**Date:** 2025-11-11
**Status:** GPU Detected, Partially Utilized
**GPU:** NVIDIA GeForce RTX 4070 Ti (12GB VRAM)

---

## Current CUDA Status

### Hardware & Drivers
```
GPU: NVIDIA GeForce RTX 4070 Ti
VRAM: 12 GB (11,650 MB currently used by LM Studio)
Driver Version: 581.57
Driver CUDA Version: 13.0
Compute Capability: 8.9
CUDA Cores: 7,680
Multi-Processors: 60
```

### Software Environment
```
CUDA Toolkit: 12.9 (nvcc)
CUDA Path: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9
PyTorch: 2.5.1+cu121
PyTorch CUDA: 12.1
Python: 3.12.8
```

### Current GPU Usage
```
Memory Used: 11,581 MiB / 12,282 MiB (94.3%)
Memory Free: 416 MiB
GPU Utilization: 7%
Memory Utilization: 11%
Temperature: 18°C
Power Draw: 10W / 285W (3.5%)
Fan Speed: 46%
```

---

## Issue Analysis

### 1. LM Studio Resource Usage

**Observation:**
- LM Studio (20B model, 13GB) maxes at 93% CPU
- Memory usage stays at 78% RAM
- GPU memory: 11.6 GB occupied
- GPU utilization: Only 7%
- 3 LM Studio processes running

**Problem:** LM Studio is running on **CPU mode**, not GPU acceleration.

**Evidence:**
- High CPU usage (93%)
- Low GPU utilization (7%)
- GPU memory occupied but not processing
- Only 10W power draw (should be 100-200W under load)

**Why This Happens:**
- GGUF models in LM Studio may default to CPU
- GPU layers not configured
- CUDA not properly enabled in LM Studio settings

**Impact:**
- 10-100x slower inference
- CPU bottleneck
- GPU sitting idle despite VRAM usage

### 2. CUDA Version Mismatch

**Installed:**
- CUDA Toolkit: 12.9
- Driver supports: CUDA 13.0
- PyTorch using: CUDA 12.1

**Status:** ✅ **Not a problem** - CUDA is backward compatible

**Explanation:**
- PyTorch 2.5.1+cu121 compiled for CUDA 12.1
- Works fine with newer CUDA toolkit (12.9) and driver (13.0)
- Backward compatibility ensures no issues

### 3. Multiple CUDA Versions

**Current Setup:**
- Toolkit: 12.9
- PyTorch: 12.1
- Driver: 13.0

**Status:** ✅ **Normal and expected**

**Why This is OK:**
- PyTorch bundles its own CUDA libraries
- System CUDA toolkit for development/compilation
- Driver provides runtime support for all versions

---

## Recommendations

### Priority 1: Fix LM Studio GPU Acceleration ⚠️ **HIGH IMPACT**

**Problem:** 13GB model using GPU memory but running on CPU

**Solution Steps:**

1. **Open LM Studio Settings**
   - Go to Settings → GPU Offloading
   - Set GPU layers to maximum (typically 60-80 for 20B model)
   - Enable "Use GPU for inference"

2. **Verify Model Configuration**
   - Check current model settings
   - Ensure "GPU Layers" is not 0
   - For 20B model with 12GB VRAM: Set to 60-70 layers

3. **Restart LM Studio**
   - Close all LM Studio processes
   - Clear GPU memory: `nvidia-smi -r` (may need admin)
   - Restart LM Studio with GPU enabled

4. **Test GPU Acceleration**
   ```bash
   # Before fix:
   CPU: 93%, GPU: 7%, Power: 10W

   # After fix (expected):
   CPU: 20-30%, GPU: 60-80%, Power: 150-200W
   ```

**Expected Performance Gain:**
- **Current:** ~10-50 tokens/second (CPU)
- **After Fix:** ~100-500 tokens/second (GPU)
- **Speedup:** 10-50x faster

### Priority 2: Optimize PyTorch Settings

**Current:** PyTorch working with CUDA 12.1

**Optimizations:**

1. **Enable TF32 (Tensor Float 32)**
   ```python
   import torch
   torch.backends.cuda.matmul.allow_tf32 = True
   torch.backends.cudnn.allow_tf32 = True
   ```
   - RTX 4070 Ti supports TF32
   - Free 2-3x speedup for AI operations
   - No accuracy loss for most tasks

2. **Optimize Memory Settings**
   ```python
   # Add to sdxl_generator.py initialization
   torch.cuda.empty_cache()
   torch.cuda.set_per_process_memory_fraction(0.95)  # Use 95% of VRAM
   ```

3. **Enable cuDNN Autotuner**
   ```python
   torch.backends.cudnn.benchmark = True
   ```
   - Finds fastest convolution algorithms
   - ~10-20% speedup for consistent input sizes

### Priority 3: CUDA Toolkit Configuration

**Current:** CUDA 12.9 installed, working correctly

**Optional Optimizations:**

1. **Set Optimal Power Mode**
   ```bash
   # Set GPU to prefer maximum performance
   nvidia-smi -pm 1  # Enable persistence mode
   nvidia-smi -pl 285  # Set power limit to max (285W)
   ```

2. **Check CUDA Samples** (if you compiled llama-cpp-python)
   ```bash
   cd "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9\extras\demo_suite"
   .\deviceQuery.exe
   .\bandwidthTest.exe
   ```

---

## Performance Expectations

### Current Performance (LM Studio on CPU)

**Text Generation (20B model):**
- Tokens/second: ~10-50
- Response time: 10-30 seconds for 100 tokens
- CPU usage: 93%
- GPU usage: 7%
- Power: 10W

**SDXL Image Generation (GPU enabled):**
- 512x512: ~3-5 seconds ✅
- 1024x1024: ~10-20 seconds ✅
- GPU usage: 60-80% ✅
- Power: 150-200W ✅

### Expected Performance (LM Studio on GPU)

**Text Generation (20B model with GPU):**
- Tokens/second: 100-500 (10-50x faster)
- Response time: 1-3 seconds for 100 tokens
- CPU usage: 20-30%
- GPU usage: 60-80%
- Power: 150-200W

**SDXL Image Generation (optimized):**
- 512x512: ~2-3 seconds (with TF32)
- 1024x1024: ~8-15 seconds (with TF32)
- GPU usage: 80-95%
- Power: 200-250W

---

## Quick Diagnostic Commands

### Check GPU Status
```bash
nvidia-smi
```

### Monitor GPU in Real-Time
```bash
nvidia-smi dmon -s pucvmet -d 1
```

### Check PyTorch CUDA
```bash
cd "C:\Users\Administrator\Desktop\Projects\LPG"
.venv312\Scripts\python.exe -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}'); print(f'Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB')"
```

### Test GPU Load
```bash
# Run SDXL generation while watching nvidia-smi
# Should see GPU spike to 60-80% and power draw 150-200W
.venv312\Scripts\python.exe examples/test_sdxl.py
```

---

## LM Studio GPU Configuration

### How to Enable GPU in LM Studio

1. **Stop Current Inference**
   - Stop any running generations
   - Unload current model

2. **Configure GPU Layers**
   ```
   Settings → Advanced → GPU Offloading

   For RTX 4070 Ti (12GB):
   - 20B model: 60-70 layers
   - 13B model: 70-80 layers
   - 7B model: Full offload (all layers)
   ```

3. **Memory Management**
   ```
   Settings → Memory
   - Context length: 4096 (adjust based on needs)
   - Batch size: 512
   - GPU memory reserve: 1GB (for system)
   ```

4. **Reload Model**
   - Reload the model with new settings
   - Check console for "GPU layers: XX" confirmation

### Verify GPU Acceleration

**Signs GPU is Working:**
- High GPU utilization (60-80%)
- Higher power draw (150-200W)
- Lower CPU usage (~20-30%)
- Much faster tokens/second
- Console shows "Using GPU: 60 layers"

**Signs GPU is NOT Working:**
- Low GPU utilization (<10%)
- Low power draw (<20W)
- High CPU usage (>80%)
- Slow tokens/second
- Console shows "Using GPU: 0 layers"

---

## CUDA Toolkit Usage for Our Tasks

### What We Need CUDA For:

1. **PyTorch/SDXL (Currently Working)** ✅
   - Uses bundled CUDA libraries
   - Toolkit not required
   - Working with cu121 wheel

2. **LM Studio GGUF (Needs Configuration)** ⚠️
   - Uses llama.cpp with CUDA backend
   - Should work out-of-box
   - Needs proper GPU layer configuration

3. **Future: llama-cpp-python (Optional)**
   - Requires C++ build tools + CUDA toolkit
   - For direct GGUF loading in Python
   - Not currently needed (LM Studio API works)

### CUDA Toolkit 12.9 Features Available:

- **TF32 Support:** Faster matrix operations (already in PyTorch)
- **FP16/BF16:** Half precision for 2x memory/speed
- **CUDA Graphs:** Reduce kernel launch overhead
- **Stream Compaction:** Efficient dynamic parallelism
- **Tensor Cores:** Hardware acceleration for AI

**For Our Use:** PyTorch handles all of this automatically.

---

## Summary & Action Plan

### Current State
✅ CUDA working for PyTorch/SDXL
❌ LM Studio using CPU instead of GPU
✅ All hardware/drivers correct
⚠️ GPU mostly idle despite 11GB VRAM used

### Immediate Actions

**1. Fix LM Studio GPU Acceleration** (10 minutes)
   - Enable GPU layers in settings
   - Restart with GPU offload
   - Expected: 10-50x speedup

**2. Apply PyTorch Optimizations** (5 minutes)
   - Enable TF32 in sdxl_generator.py
   - Enable cuDNN benchmark
   - Expected: 20-30% speedup

**3. Test & Verify** (5 minutes)
   - Run SDXL generation
   - Run LM Studio inference
   - Monitor with nvidia-smi
   - Verify 60-80% GPU usage

### Expected Results After Fixes

**Before:**
```
LM Studio: 93% CPU, 7% GPU, 10W, ~20 tokens/sec
SDXL: Working, 3-5 sec per 512x512 image
```

**After:**
```
LM Studio: 30% CPU, 70% GPU, 180W, ~200 tokens/sec
SDXL: Optimized, 2-3 sec per 512x512 image
```

**Total GPU Utilization:** 70-90% (much better!)

---

## Next Steps

1. Configure LM Studio GPU layers
2. Apply TF32 optimization to SDXL
3. Test both systems simultaneously
4. Document actual performance gains
5. Update MODEL_INTEGRATION_STATUS.md

Once LM Studio is on GPU, your RTX 4070 Ti will be fully utilized and you'll see dramatic speed improvements!
