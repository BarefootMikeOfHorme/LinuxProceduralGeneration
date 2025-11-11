# Setup Python 3.12 with CUDA Support
# Run this script to switch from Python 3.14 to 3.12

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Python 3.12 + CUDA Setup Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot

# Check if Python 3.12 is installed
Write-Host "[1/5] Checking for Python 3.12..." -ForegroundColor Yellow

$python312Paths = @(
    "C:\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
)

$python312 = $null
foreach ($path in $python312Paths) {
    if (Test-Path $path) {
        $python312 = $path
        Write-Host "  Found Python 3.12 at: $path" -ForegroundColor Green
        break
    }
}

if (-not $python312) {
    Write-Host "  [ERROR] Python 3.12 not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please install Python 3.12.8 from:" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Installation options:" -ForegroundColor Yellow
    Write-Host "  - Add Python 3.12 to PATH" -ForegroundColor White
    Write-Host "  - Install pip" -ForegroundColor White
    Write-Host "  - Suggested location: C:\Python312\" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Verify version
$version = & $python312 --version
Write-Host "  Version: $version" -ForegroundColor Green
Write-Host ""

# Create virtual environment
Write-Host "[2/5] Creating Python 3.12 virtual environment..." -ForegroundColor Yellow

$venvPath = Join-Path $PROJECT_ROOT ".venv312"

if (Test-Path $venvPath) {
    Write-Host "  Virtual environment already exists" -ForegroundColor Yellow
    $recreate = Read-Host "  Recreate it? (y/n)"
    if ($recreate -eq "y") {
        Remove-Item -Recurse -Force $venvPath
        & $python312 -m venv $venvPath
        Write-Host "  [OK] Virtual environment recreated" -ForegroundColor Green
    }
} else {
    & $python312 -m venv $venvPath
    Write-Host "  [OK] Virtual environment created at: $venvPath" -ForegroundColor Green
}

Write-Host ""

# Activate virtual environment
Write-Host "[3/5] Activating virtual environment..." -ForegroundColor Yellow

$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
. $activateScript

Write-Host "  [OK] Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Install PyTorch with CUDA
Write-Host "[4/5] Installing PyTorch with CUDA 12.1..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray
Write-Host ""

# Uninstall any existing torch
pip uninstall torch torchvision torchaudio -y 2>&1 | Out-Null

# Install with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

Write-Host ""
Write-Host "  [OK] PyTorch with CUDA installed" -ForegroundColor Green
Write-Host ""

# Verify CUDA
Write-Host "[5/5] Verifying CUDA support..." -ForegroundColor Yellow

python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

Write-Host ""

# Install other dependencies
Write-Host "Installing other dependencies..." -ForegroundColor Yellow
pip install diffusers transformers accelerate pillow numpy requests --quiet

Write-Host "[OK] Dependencies installed" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. To use this environment, run:" -ForegroundColor White
Write-Host "     .venv312\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Test SDXL with CUDA:" -ForegroundColor White
Write-Host "     python examples/test_sdxl.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Your RTX 4070 Ti is now being used!" -ForegroundColor Green
Write-Host ""
