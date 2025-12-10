@echo off
REM VaultMind Forge - Uninstall Windows Service

echo Uninstalling VaultMind Forge Windows Service...

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script must be run as Administrator
    pause
    exit /b 1
)

REM Check if NSSM is installed
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo NSSM not found. Service may not be installed.
    pause
    exit /b 1
)

REM Stop the service if running
echo Stopping VaultMind Forge service...
nssm stop VaultMindForge

REM Remove the service
echo Removing VaultMind Forge service...
nssm remove VaultMindForge confirm

echo.
echo VaultMind Forge service has been removed.
echo.
pause
