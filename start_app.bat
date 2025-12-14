@echo off
title StockSignal Launcher
cd /d "%~dp0"

echo ========================================================
echo      StockSignal AI (Auto-Setup & Launch)
echo ========================================================

:: --- 1. CHECK PYTHON ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation.
    pause
    exit
)

:: --- 2. SETUP VIRTUAL ENVIRONMENT ---
if not exist "venv" (
    echo [SETUP] Creating Python Virtual Environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create venv.
        pause
        exit
    )
)

:: --- 3. INSTALL PYTHON REQUIREMENTS ---
echo [SETUP] Checking Python dependencies...
call venv\Scripts\activate.bat

:: Upgrade pip first to avoid issues
python -m pip install --upgrade pip >nul 2>&1

:: Install requirements (will skip if already satisfied)
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.txt
    pause
    exit
)

:: --- 4. CHECK NODE.JS ---
call npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js (LTS) from https://nodejs.org/
    echo This is required for the WhatsApp connection.
    pause
    exit
)

:: --- 5. SETUP WHATSAPP SERVICE ---
if not exist "whatsapp-service\node_modules" (
    echo [SETUP] Installing WhatsApp Service dependencies...
    cd whatsapp-service
    call npm install
    cd ..
)

:: --- 6. LAUNCH APPLICATION ---
echo [READY] All systems go! Launching Dashboard...
:: Start pythonw (no console) for the GUI
start /B "" "venv\Scripts\pythonw.exe" desktop_app.py

:: Exit launcher
exit
