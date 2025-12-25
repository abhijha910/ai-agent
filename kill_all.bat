@echo off
echo ========================================
echo Killing all backend and frontend processes
echo ========================================

REM Kill all Python processes (backend)
taskkill /f /im python.exe /t 2>nul

REM Kill all Node processes (frontend)
taskkill /f /im node.exe /t 2>nul

REM Kill specific ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /f /pid %%a 2>nul

echo ========================================
echo DONE! All processes killed.
echo ========================================
pause
