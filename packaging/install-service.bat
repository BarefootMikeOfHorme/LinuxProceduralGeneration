@echo off
REM VaultMind Forge - Install Windows Service

echo Installing VaultMind Forge Windows Service...

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script must be run as Administrator
    pause
    exit /b 1
)

REM Install NSSM if not already installed
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo NSSM not found. Please install NSSM first:
    echo https://nssm.cc/download
    pause
    exit /b 1
)

REM Set installation directory
set INSTALL_DIR=%~dp0
set VENV_PYTHON=%INSTALL_DIR%.venv312\Scripts\python.exe
set UVICORN=%INSTALL_DIR%.venv312\Scripts\uvicorn.exe

REM Check if virtual environment exists
if not exist "%VENV_PYTHON%" (
    echo Error: Python virtual environment not found at %VENV_PYTHON%
    pause
    exit /b 1
)

REM Install service using NSSM
nssm install VaultMindForge "%UVICORN%" backend.api:app --host 0.0.0.0 --port 8000
nssm set VaultMindForge AppDirectory "%INSTALL_DIR%"
nssm set VaultMindForge AppEnvironmentExtra "VAULTMIND_LOG_LEVEL=INFO"
nssm set VaultMindForge DisplayName "VaultMind Forge API Server"
nssm set VaultMindForge Description "AI-powered procedural content generation API"
nssm set VaultMindForge Start SERVICE_AUTO_START
nssm set VaultMindForge AppStdout "%INSTALL_DIR%logs\service.log"
nssm set VaultMindForge AppStderr "%INSTALL_DIR%logs\service-error.log"

REM Start the service
echo Starting VaultMind Forge service...
nssm start VaultMindForge

echo.
echo VaultMind Forge service installed and started successfully!
echo.
echo Service Name: VaultMindForge
echo API Endpoint: http://localhost:8000
echo Logs: %INSTALL_DIR%logs\
echo.
echo To check service status: nssm status VaultMindForge
echo To stop service: nssm stop VaultMindForge
echo To remove service: run uninstall-service.bat
echo.
pause
