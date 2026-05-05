@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║       Instagram Creator PRO — Starting...           ║
echo ╚══════════════════════════════════════════════════════╝
echo.
echo   Dashboard : http://localhost:5173
echo   API       : http://localhost:8000
echo.
echo   Press Ctrl+C to stop
echo.

set DEV_MODE=true
python run.py
pause
