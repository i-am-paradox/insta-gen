@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║       Instagram Creator PRO — Setup (Windows)       ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found

:: Install Python dependencies
echo.
echo [1/3] Installing Python dependencies...
pip install -r requirements_pro.txt
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)
echo [OK] Python packages installed

:: Download Camoufox browser
echo.
echo [2/3] Downloading Camoufox stealth browser...
python -m camoufox fetch
if %errorlevel% neq 0 (
    echo [ERROR] Camoufox fetch failed
    pause
    exit /b 1
)
echo [OK] Camoufox ready

:: Install frontend dependencies
echo.
echo [3/3] Installing frontend dependencies...
cd frontend
npm install
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed
    pause
    exit /b 1
)
cd ..
echo [OK] Frontend packages installed

:: Copy .env if not exists
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [OK] .env created from template
) else (
    echo [OK] .env already exists
)

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║   Setup Complete! Now run:                          ║
echo ║                                                      ║
echo ║       start.bat                                      ║
echo ║                                                      ║
echo ║   Then open: http://localhost:5173                  ║
echo ╚══════════════════════════════════════════════════════╝
echo.
pause
