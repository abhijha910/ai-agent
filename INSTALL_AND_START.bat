@echo off
echo ========================================
echo   AI Agent - Installation & Start
echo ========================================
echo.

echo Step 1: Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

echo.
echo Step 2: Activating virtual environment...
call venv\Scripts\activate

echo.
echo Step 3: Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Installation failed!
    pause
    exit /b 1
)
echo ✅ Dependencies installed

echo.
echo Step 4: Initializing database...
python -c "from app.database import init_db; init_db(); print('✅ Database initialized')"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Database initialization failed!
    pause
    exit /b 1
)

echo.
echo Step 5: Testing API keys...
python test_api_keys.py

echo.
echo ========================================
echo   ✅ Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Keep this window open
echo 2. Open a NEW terminal window
echo 3. Run: cd frontend ^&^& npm install ^&^& npm run dev
echo 4. Then start backend: python -m uvicorn app.main:app --reload
echo.
echo Or see START_SERVERS.md for detailed instructions
echo.
pause

