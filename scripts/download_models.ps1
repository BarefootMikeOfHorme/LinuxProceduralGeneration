# VaultMind Forge - Model Download & Setup Script
# Downloads required models and links existing LM Studio models

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "VaultMind Forge - Model Download & Setup Script" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$MODELS_DIR = Join-Path $PROJECT_ROOT "models"
$LM_STUDIO_DIR = "C:\Users\Administrator\.lmstudio\models"

# Create models directory
if (-not (Test-Path $MODELS_DIR)) {
    New-Item -ItemType Directory -Path $MODELS_DIR | Out-Null
    Write-Host "[OK] Created models directory: $MODELS_DIR" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "PART 1: Link Existing LM Studio Models" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

# Check LM Studio directory
if (Test-Path $LM_STUDIO_DIR) {
    Write-Host "[OK] Found LM Studio models: $LM_STUDIO_DIR" -ForegroundColor Green
    Write-Host ""

    # 1. TeichAI 20B GPT-Claude (Main AI Agent)
    Write-Host "[1/3] TeichAI 20B GPT-Claude (Main AI)..." -ForegroundColor Yellow
    $teichai_search = Get-ChildItem -Path $LM_STUDIO_DIR -Recurse -Filter "*gpt-oss-20b-claude*.gguf" -ErrorAction SilentlyContinue | Select-Object -First 1

    if ($teichai_search) {
        $TEICHAI_PATH = $teichai_search.FullName
        $TEICHAI_LINK = Join-Path $MODELS_DIR "teichai-unified.gguf"

        if (-not (Test-Path $TEICHAI_LINK)) {
            # Create symlink
            New-Item -ItemType SymbolicLink -Path $TEICHAI_LINK -Target $TEICHAI_PATH -Force | Out-Null
            Write-Host "  [OK] Linked: $TEICHAI_LINK" -ForegroundColor Green
            Write-Host "       From: $TEICHAI_PATH" -ForegroundColor Gray
        } else {
            Write-Host "  [OK] Already linked: $TEICHAI_LINK" -ForegroundColor Green
        }
    } else {
        Write-Host "  [WARN] TeichAI model not found in LM Studio" -ForegroundColor Yellow
        Write-Host "         Expected: *gpt-oss-20b-claude*.gguf" -ForegroundColor Gray
    }

    # 2. PixelWave FLUX (Image Generation)
    Write-Host ""
    Write-Host "[2/3] PixelWave FLUX (Image Generation)..." -ForegroundColor Yellow
    $pixelwave_path = "C:\Users\Administrator\.lmstudio\models\mikeyandfriends\PixelWave_FLUX.1-dev_03\pixelwave_flux1_dev_Q8_0_03.gguf"

    if (Test-Path $pixelwave_path) {
        $PIXELWAVE_LINK = Join-Path $MODELS_DIR "pixelwave-flux.gguf"

        if (-not (Test-Path $PIXELWAVE_LINK)) {
            New-Item -ItemType SymbolicLink -Path $PIXELWAVE_LINK -Target $pixelwave_path -Force | Out-Null
            Write-Host "  [OK] Linked: $PIXELWAVE_LINK" -ForegroundColor Green
            Write-Host "       From: $pixelwave_path" -ForegroundColor Gray
        } else {
            Write-Host "  [OK] Already linked: $PIXELWAVE_LINK" -ForegroundColor Green
        }
    } else {
        Write-Host "  [WARN] PixelWave not found at expected path" -ForegroundColor Yellow
    }

    # 3. Waifu (Character Generation?)
    Write-Host ""
    Write-Host "[3/3] Waifu model..." -ForegroundColor Yellow
    $waifu_search = Get-ChildItem -Path $LM_STUDIO_DIR -Recurse -Filter "*waifu*.gguf" -ErrorAction SilentlyContinue | Select-Object -First 1

    if ($waifu_search) {
        $WAIFU_PATH = $waifu_search.FullName
        $WAIFU_LINK = Join-Path $MODELS_DIR "waifu.gguf"

        if (-not (Test-Path $WAIFU_LINK)) {
            New-Item -ItemType SymbolicLink -Path $WAIFU_LINK -Target $WAIFU_PATH -Force | Out-Null
            Write-Host "  [OK] Linked: $WAIFU_LINK" -ForegroundColor Green
            Write-Host "       From: $WAIFU_PATH" -ForegroundColor Gray
        } else {
            Write-Host "  [OK] Already linked: $WAIFU_LINK" -ForegroundColor Green
        }
    } else {
        Write-Host "  [WARN] Waifu model not found in LM Studio" -ForegroundColor Yellow
    }

} else {
    Write-Host "[WARN] LM Studio directory not found: $LM_STUDIO_DIR" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "PART 2: Download New Models" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python and pip
Write-Host "[1/4] Checking dependencies..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python not found. Please install Python 3.10+." -ForegroundColor Red
    exit 1
}

# Install huggingface-cli if needed
Write-Host ""
Write-Host "[2/4] Installing HuggingFace CLI..." -ForegroundColor Yellow
try {
    pip install -q huggingface_hub
    Write-Host "  [OK] HuggingFace CLI ready" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Failed to install huggingface_hub" -ForegroundColor Red
}

# Download mesh-xl-1.3b
Write-Host ""
Write-Host "[3/4] Downloading mesh-xl-1.3b..." -ForegroundColor Yellow
Write-Host "  Model: CH3COOK/mesh-xl-1.3b" -ForegroundColor Cyan
Write-Host "  Size: ~5GB" -ForegroundColor Cyan
Write-Host "  Purpose: 3D mesh generation (2D images → 3D models)" -ForegroundColor Cyan
Write-Host ""

$MESH_XL_DIR = Join-Path $MODELS_DIR "mesh-xl-1.3b"

if (Test-Path $MESH_XL_DIR) {
    Write-Host "  [OK] mesh-xl-1.3b already downloaded: $MESH_XL_DIR" -ForegroundColor Green
} else {
    $downloadMesh = Read-Host "  Download mesh-xl-1.3b? (y/n)"
    if ($downloadMesh -eq "y") {
        try {
            Write-Host "  Downloading... (this may take a while)" -ForegroundColor Yellow
            python -m huggingface_hub download CH3COOK/mesh-xl-1.3b --local-dir $MESH_XL_DIR
            Write-Host "  [OK] mesh-xl-1.3b downloaded to: $MESH_XL_DIR" -ForegroundColor Green
        } catch {
            Write-Host "  [ERROR] Failed to download mesh-xl-1.3b" -ForegroundColor Red
        }
    } else {
        Write-Host "  [SKIP] mesh-xl-1.3b download skipped" -ForegroundColor Yellow
    }
}

# Download StdGEN (3D generation pipeline)
Write-Host ""
Write-Host "[4/4] Downloading StdGEN (3D pipeline)..." -ForegroundColor Yellow
Write-Host "  Repo: hyz317/StdGEN" -ForegroundColor Cyan
Write-Host "  Purpose: 3D mesh generation pipeline" -ForegroundColor Cyan
Write-Host "  Stages: A-pose → Multi-view → Reconstruction → Refinement" -ForegroundColor Cyan
Write-Host ""

$EXTERNAL_DIR = Join-Path $PROJECT_ROOT "external"
$STDGEN_DIR = Join-Path $EXTERNAL_DIR "StdGEN"

if (Test-Path $STDGEN_DIR) {
    Write-Host "  [OK] StdGEN already cloned: $STDGEN_DIR" -ForegroundColor Green
} else {
    $downloadStdgen = Read-Host "  Clone StdGEN repo? (y/n)"
    if ($downloadStdgen -eq "y") {
        try {
            Write-Host "  Cloning..." -ForegroundColor Yellow

            # Create external directory
            if (-not (Test-Path $EXTERNAL_DIR)) {
                New-Item -ItemType Directory -Path $EXTERNAL_DIR | Out-Null
            }

            # Clone repo
            Set-Location $EXTERNAL_DIR
            git clone https://github.com/hyz317/StdGEN.git

            Write-Host "  [OK] StdGEN cloned to: $STDGEN_DIR" -ForegroundColor Green

            # Install requirements
            Write-Host "  Installing StdGEN requirements..." -ForegroundColor Yellow
            Set-Location $STDGEN_DIR
            pip install -q -r requirements.txt

            Write-Host "  [OK] StdGEN requirements installed" -ForegroundColor Green

        } catch {
            Write-Host "  [ERROR] Failed to clone/install StdGEN: $_" -ForegroundColor Red
        } finally {
            Set-Location $PROJECT_ROOT
        }
    } else {
        Write-Host "  [SKIP] StdGEN download skipped" -ForegroundColor Yellow
    }
}

# Create model config file
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "PART 3: Creating Model Configuration" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

$CONFIG_FILE = Join-Path $PROJECT_ROOT "config\model_paths.yaml"
$CONFIG_DIR = Split-Path $CONFIG_FILE

if (-not (Test-Path $CONFIG_DIR)) {
    New-Item -ItemType Directory -Path $CONFIG_DIR | Out-Null
}

$configContent = @"
# VaultMind Forge - Model Paths Configuration
# Auto-generated by download_models.ps1

# Main AI Agent
teichai_unified:
  path: "$($MODELS_DIR -replace '\\', '/')/teichai-unified.gguf"
  type: "gguf"
  purpose: "main_ai"
  capabilities: ["executive", "planning", "reasoning", "tool_use"]
  vram_gb: 16

# Image Generation
pixelwave_flux:
  path: "$($MODELS_DIR -replace '\\', '/')/pixelwave-flux.gguf"
  type: "gguf"
  purpose: "image_generation"
  capabilities: ["2d_generation", "pixel_art", "stylized"]
  vram_gb: 8

# Character/Waifu Model
waifu:
  path: "$($MODELS_DIR -replace '\\', '/')/waifu.gguf"
  type: "gguf"
  purpose: "character_generation"
  capabilities: ["character_design", "anime_style"]
  vram_gb: 4

# 3D Mesh Generation
mesh_xl:
  path: "$($MESH_XL_DIR -replace '\\', '/')"
  type: "directory"
  purpose: "3d_generation"
  capabilities: ["2d_to_3d", "semantic_decomposition"]
  vram_gb: 8

# 3D Pipeline
stdgen:
  path: "$($STDGEN_DIR -replace '\\', '/')"
  type: "directory"
  purpose: "3d_pipeline"
  capabilities: ["apose_conversion", "multiview", "reconstruction", "refinement"]
"@

$configContent | Out-File -FilePath $CONFIG_FILE -Encoding UTF8
Write-Host "[OK] Model configuration saved: $CONFIG_FILE" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "Setup Summary" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "LM Studio Models (Linked):" -ForegroundColor Yellow
if (Test-Path (Join-Path $MODELS_DIR "teichai-unified.gguf")) {
    Write-Host "  [OK] TeichAI 20B GPT-Claude (Main AI)" -ForegroundColor Green
} else {
    Write-Host "  [--] TeichAI 20B GPT-Claude (Not found)" -ForegroundColor Red
}

if (Test-Path (Join-Path $MODELS_DIR "pixelwave-flux.gguf")) {
    Write-Host "  [OK] PixelWave FLUX (Image Gen)" -ForegroundColor Green
} else {
    Write-Host "  [--] PixelWave FLUX (Not found)" -ForegroundColor Red
}

if (Test-Path (Join-Path $MODELS_DIR "waifu.gguf")) {
    Write-Host "  [OK] Waifu (Character Gen)" -ForegroundColor Green
} else {
    Write-Host "  [--] Waifu (Not found)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Downloaded Models:" -ForegroundColor Yellow
if (Test-Path $MESH_XL_DIR) {
    Write-Host "  [OK] mesh-xl-1.3b (3D Gen): $MESH_XL_DIR" -ForegroundColor Green
} else {
    Write-Host "  [--] mesh-xl-1.3b (Not downloaded)" -ForegroundColor Red
}

if (Test-Path $STDGEN_DIR) {
    Write-Host "  [OK] StdGEN (3D Pipeline): $STDGEN_DIR" -ForegroundColor Green
} else {
    Write-Host "  [--] StdGEN (Not downloaded)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Install additional dependencies:" -ForegroundColor White
Write-Host "     pip install llama-cpp-python transformers accelerate" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Test the models:" -ForegroundColor White
Write-Host "     python examples/test_models.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. Start using VaultMind Forge:" -ForegroundColor White
Write-Host "     python examples/complete_2d_to_3d_pipeline.py" -ForegroundColor Yellow
Write-Host ""

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan
