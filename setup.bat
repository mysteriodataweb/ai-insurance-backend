@echo off
echo ========================================
echo  AI Insurance Operations Platform
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)

echo [1/4] Installing backend dependencies...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install backend dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Copying .env if not exists...
if not exist .env (
    copy .env.example .env
    echo .env created from .env.example - Please configure DATABASE_URL and OPENAI_API_KEY
)

echo.
echo [3/4] Installing frontend dependencies...
cd ..\frontend
call npm install
if %errorlevel% neq 0 (
    echo Failed to install frontend dependencies
    pause
    exit /b 1
)

echo.
echo [4/4] Setup complete!
echo.
echo ========================================
echo  To run the platform:
echo.
echo  1. Start PostgreSQL and create database:
echo     CREATE DATABASE ai_insurance;
echo.
echo  2. Configure backend/.env with your DATABASE_URL
echo.
echo  3. Seed the database:
echo     cd backend ^& python seed.py
echo.
echo  4. Start backend (Terminal 1):
echo     cd backend ^& uvicorn app.main:app --reload
echo.
echo  5. Start frontend (Terminal 2):
echo     cd frontend ^& npm run dev
echo.
echo  6. Open http://localhost:3000
echo ========================================
pause
