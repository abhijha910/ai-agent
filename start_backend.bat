@echo off
echo ========================================
echo Starting AI Agent Backend Server
echo ========================================
echo.

REM Kill any existing processes on port 8000
echo Killing any processes using port 8000...
call kill_port_8000.bat >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo   Force killing process %%a...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 3 /nobreak >nul

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo ========================================
echo Starting server on http://localhost:8000
echo WebSocket: ws://localhost:8000/ws
echo API Docs: http://localhost:8000/docs
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the server
echo Starting server...
echo.
echo ========================================
echo   Server will start on:
echo   http://localhost:8000
echo   ws://localhost:8000/ws
echo ========================================
echo.
echo Waiting for: "Server ready!" message
echo.
echo ========================================
echo.

python test_server.py

echo.
echo ========================================
echo Server stopped. Press any key to exit...
echo ========================================
pause >nul
