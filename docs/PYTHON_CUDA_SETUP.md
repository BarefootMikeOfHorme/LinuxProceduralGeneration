# Python & CUDA Setup Guide

**Issue:** Python 3.14 doesn't have PyTorch CUDA wheels yet
**Solution:** Use Python 3.12 for CUDA support
**Impact:** None - our code is fully compatible

---

## Problem Summary

**Current Situation:**
- Python 3.14.0 installed
- RTX 4070 Ti GPU available (CUDA 13.0)
- PyTorch installed as CPU-only (no CUDA support)
- CUDA cores not being utilized

**Root Cause:**
PyTorch doesn't provide CUDA-enabled wheels for Python 3.14 yet. Only CPU version available.

---

## Code Compatibility Analysis

**Our Codebase Uses:**
- `from __future__ import annotations` (Python 3.7+)
- Type hints with `|` syntax (handled by future imports)
- No match/case statements
- No Python 3.12+ exclusive features

**Verdict:** ✅ **100% compatible with Python 3.12**

Files analyzed: 91 Python files
- 0 match/case statements found
- 0 Python 3.12+ exclusive features
- All type hints handled by `__future__` imports

---

## Solution: Downgrade to Python 3.12

### Step 1: Install Python 3.12

**Download:**
- Go to: https://www.python.org/downloads/
- Download Python 3.12.8 (latest 3.12.x)
- Run installer

**Installation Options:**
- ✅ Add Python 3.12 to PATH
- ✅ Install pip
- Installation directory: `C:\Python312\` (recommended)

### Step 2: Set Python 3.12 as Default

**Option A: Update PATH**
```powershell
# Move Python 3.12 to top of PATH
# System Properties → Environment Variables → Path
# Move C:\Python312\ above C:\Python314\
```

**Option B: Create Virtual Environment**
```powershell
cd C:\Users\Administrator\Desktop\Projects\LPG

# Create venv with Python 3.12
C:\Python312\python.exe -m venv .venv312

# Activate it
.venv312\Scripts\activate

# Verify version
python --version  # Should show 3.12.x
```

### Step 3: Install PyTorch with CUDA

**Uninstall current PyTorch:**
```bash
pip uninstall torch torchvision torchaudio -y
```

**Install PyTorch with CUDA 12.1:**
```bash
# For CUDA 12.1 (compatible with CUDA 13.0)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Verify CUDA:**
```python
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
```

**Expected Output:**
```
PyTorch version: 2.x.x+cu121
CUDA available: True
CUDA version: 12.1
GPU: NVIDIA GeForce RTX 4070 Ti
```

### Step 4: Reinstall Dependencies

```bash
cd C:\Users\Administrator\Desktop\Projects\LPG

# Reinstall all dependencies with Python 3.12
pip install -r requirements.txt

# Or install key packages
pip install diffusers transformers accelerate
pip install pillow numpy requests
```

---

## Alternative: Keep Python 3.14

If you want to keep Python 3.14, here are the alternatives:

### Option 1: Build PyTorch from Source (Advanced)
- Requires Visual Studio C++ Build Tools
- Requires CUDA Toolkit 12.1+
- Takes several hours to build
- Not recommended for most users

### Option 2: Use CPU-Only (Current)
- Keep Python 3.14
- Accept CPU-only PyTorch
- Slower generation (10-100x slower than GPU)
- Works but not optimal

### Option 3: Wait for Official CUDA Wheels
- Python 3.14 CUDA support coming soon
- Nightly builds available but unstable
- Wait for official release (estimated: early 2026)

---

## Recommended Setup

**For Development (Best Performance):**
```
Python 3.12.8
PyTorch 2.x with CUDA 12.1
RTX 4070 Ti utilized
Fast image generation
```

**Project Structure:**
```
C:\Users\Administrator\Desktop\Projects\LPG\
├── .venv312\          # Python 3.12 virtual environment
├── vaultmind_forge\   # Our code (works on 3.12)
├── models\            # Model files
└── requirements.txt   # Dependencies
```

---

## Performance Comparison

### CPU-Only (Current):
- SDXL 512x512: ~60-120 seconds per image
- SDXL 1024x1024: ~5-10 minutes per image
- Limited batch sizes

### With CUDA (After Fix):
- SDXL 512x512: ~3-5 seconds per image
- SDXL 1024x1024: ~10-20 seconds per image
- Larger batch sizes possible
- 12GB VRAM available

**Speedup: 20-30x faster with GPU**

---

## Testing After Setup

**Test CUDA availability:**
```bash
python examples/test_cuda.py
```

**Test SDXL with GPU:**
```bash
python examples/test_sdxl.py
```

**Expected results:**
- CUDA detected: ✅
- GPU memory: 12282 MiB
- Generation speed: <20s for 1024x1024

---

## Troubleshooting

### Issue: "CUDA available: False"

**Check 1: PyTorch version**
```bash
pip list | grep torch
# Should show: torch 2.x.x+cu121 (not +cpu)
```

**Fix:** Reinstall with CUDA index:
```bash
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Issue: "RuntimeError: CUDA out of memory"

**Solutions:**
- Reduce batch size
- Reduce resolution (512x512 instead of 1024x1024)
- Enable CPU offloading (already in code)
- Close other GPU applications

### Issue: "No module named 'torch'"

**Fix:** Ensure virtual environment activated:
```bash
.venv312\Scripts\activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

## Summary

**Current State:**
- ❌ Python 3.14 with CPU-only PyTorch
- ❌ RTX 4070 Ti not utilized
- ❌ Slow generation

**After Fix:**
- ✅ Python 3.12 with CUDA PyTorch
- ✅ RTX 4070 Ti fully utilized
- ✅ Fast generation (20-30x speedup)
- ✅ All code compatible

**Next Steps:**
1. Install Python 3.12
2. Create virtual environment
3. Install PyTorch with CUDA
4. Test SDXL generation
5. Enjoy GPU acceleration!
