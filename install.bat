@echo off
chcp 65001 >nul
echo.
echo  ====================================
echo   Dexscreener CLI - Quick Install
echo  ====================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
)

:: Create venv if missing
if not exist ".venv" (
    echo  Creating virtual environment...
    python -m venv .venv
)

:: Activate and install
echo  Installing dependencies...
call .venv\Scripts\activate.bat
pip install -e . --quiet

echo.
echo  ====================================
echo   Install complete!
echo  ====================================
echo.
echo  Activate the environment first:
echo    .venv\Scripts\activate
echo.
echo  Then run:
echo    ds setup          - Calibrate your scanner
echo    ds hot            - Scan hot tokens
echo    ds watch          - Live dashboard
echo    ds search pepe    - Search tokens
echo    ds --help         - All commands
echo.
echo  Or run without activating:
echo    .\.venv\Scripts\ds.exe hot --chains=solana --limit=10
echo.
pause
