@echo off
echo ===============================================================
echo VaultMind Forge - Clean Restart
echo ===============================================================
echo.

REM Kill all existing instances
echo Stopping existing servers...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq VaultMind*" 2>nul
taskkill /F /IM node.exe /FI "WINDOWTITLE eq VaultMind*" 2>nul

REM Also kill any process on port 8000 and 3000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul

echo Waiting for ports to free up...
timeout /t 3 /nobreak > nul

REM Start backend with new startup script
echo Starting backend...
start "VaultMind Forge - Backend" cmd /k "cd /d %~dp0backend && python start_backend.py"
timeout /t 3 /nobreak > nul

REM Start frontend
echo Starting frontend...
start "VaultMind Forge - Frontend" cmd /k "cd /d %~dp0web_ui && npm run dev"

echo.
echo ===============================================================
echo VaultMind Forge Started!
echo ===============================================================
echo.
echo Backend API: http://localhost:8000
echo Web UI:      http://localhost:3000
echo.
echo Press any key to close this window...
pause > nul
