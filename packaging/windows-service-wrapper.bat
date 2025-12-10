@echo off
REM VaultMind Forge - Service Wrapper
REM This wrapper ensures proper environment setup before starting the service

set INSTALL_DIR=%~dp0
set VENV_PYTHON=%INSTALL_DIR%.venv312\Scripts\python.exe

REM Load environment variables from .env file
if exist "%INSTALL_DIR%.env" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%INSTALL_DIR%.env") do (
        if not "%%a"=="" if not "%%b"=="" (
            set %%a=%%b
        )
    )
)

REM Start the API server
cd /d "%INSTALL_DIR%"
"%VENV_PYTHON%" -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
