@echo off
cd /d "%~dp0"

echo ===============================================================
echo VAULTMIND FORGE - WEB UI LAUNCHER
echo ===============================================================
echo.
echo Current directory: %CD%
echo.
echo This will start:
echo   1. Python FastAPI backend (port 8000)
echo   2. React development server (port 3000)
echo.
echo Press Ctrl+C in each window to stop
echo.
pause

echo.
echo [1/2] Starting FastAPI backend...
start "VaultMind Forge - Backend" cmd /k "cd /d "%~dp0backend" && python api.py"

timeout /t 3 /nobreak > nul

echo [2/2] Starting React dev server...
start "VaultMind Forge - Frontend" cmd /k "cd /d "%~dp0web_ui" && npm run dev"

echo.
echo ===============================================================
echo VAULTMIND FORGE STARTED
echo ===============================================================
echo.
echo Backend API: http://localhost:8000
echo Web UI:      http://localhost:3000
echo.
echo Open http://localhost:3000 in your browser
echo.
echo Press any key to close this launcher window...
pause > nul
