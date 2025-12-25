@echo off
echo ========================================
echo FORCE RESTART - Killing all processes
echo ========================================

REM Kill all Python processes
taskkill /f /im python.exe /t 2>nul

REM Kill all Node processes
taskkill /f /im node.exe /t 2>nul

REM Kill specific ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /f /pid %%a 2>nul

REM Delete old databases
del ai_agent*.db /f /q 2>nul

echo ========================================
echo Starting fresh backend...
echo ========================================
start cmd /k "python run_backend.py"

timeout /t 3 /nobreak >nul

echo ========================================
echo Starting fresh frontend...
echo ========================================
start cmd /k "cd frontend && set PORT=3000 && npm run dev"

echo ========================================
echo DONE! Check the new terminals.
echo Frontend: http://localhost:3000
echo ========================================
pause
