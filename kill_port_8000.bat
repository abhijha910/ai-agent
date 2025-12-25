@echo off
echo Killing all processes on port 8000...
echo.

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing process %%a...
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo   Failed to kill process %%a
    ) else (
        echo   Successfully killed process %%a
    )
)

echo.
echo Waiting 3 seconds for port to be released...
timeout /t 3 /nobreak >nul

echo.
echo Checking if port 8000 is free...
netstat -ano | findstr :8000 | findstr LISTENING
if errorlevel 1 (
    echo   Port 8000 is now free!
) else (
    echo   WARNING: Port 8000 is still in use!
    echo   You may need to restart your computer or manually kill the processes.
)

echo.
pause

