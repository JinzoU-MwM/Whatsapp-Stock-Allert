@echo off
title StockSignal Launcher
cd /d "%~dp0"

echo ========================================================
echo      StockSignal AI (Gemini 2.0 Flash Exp)
echo ========================================================

:: Check for Virtual Environment
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment 'venv' not found!
    echo.
    echo Please run the following commands manually first:
    echo 1. python -m venv venv
    echo 2. venv\Scripts\activate
    echo 3. pip install -r requirements.txt
    echo.
    echo See README.md for full details.
    pause
    exit
)

:: Check for Node Modules
if not exist "whatsapp-service\node_modules" (
    echo [ERROR] Node modules not found!
    echo.
    echo Please run 'npm install' inside the 'whatsapp-service' folder.
    echo.
    pause
    exit
)

:: Activate Environment
call venv\Scripts\activate.bat

:: Launch the Desktop App (GUI)
:: Using start /B pythonw to hide console window in production
echo [1/1] Starting Dashboard (Hidden Console)...
start /B "" "venv\Scripts\pythonw.exe" desktop_app.py

:: Exit launcher immediately
exit
