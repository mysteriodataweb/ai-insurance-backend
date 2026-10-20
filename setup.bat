@echo off
echo ========================================
echo  AI Insurance Operations Platform - Backend
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

echo [1/3] Installing backend dependencies...
pip install -r requirements-dev.txt
if %errorlevel% neq 0 (
    echo Failed to install backend dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Copying .env if not exists...
if not exist .env (
    copy .env.example .env
    echo .env created from .env.example - configure DATABASE_URL, GROQ_API_KEY and SECRET_KEY
)

echo.
echo [3/3] Setup complete!
echo.
echo ========================================
echo  Next steps:
echo.
echo  1. Configure .env (DATABASE_URL, GROQ_API_KEY, SECRET_KEY)
echo  2. Seed the database (empty database only):  python seed.py
echo  3. Start the API:                            uvicorn app.main:app --reload
echo  4. Run the tests:                            pytest
echo.
echo  Frontend: see the ai-insurance-frontend repository.
echo ========================================
pause
