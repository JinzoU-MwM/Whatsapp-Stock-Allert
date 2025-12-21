@echo off
title StockSignal Launcher
cd /d "%~dp0"

echo ========================================================
echo      StockSignal AI (Auto-Setup ^& Launch)
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

:: --- 2. CHECK & SETUP DEPENDENCIES ---
if not exist ".installed" (
    echo [FIRST RUN] Installing dependencies...
    call install_dependencies.bat
) else (
    echo [READY] Dependencies already installed. Skipping check.
)

:: Activate venv for launch
call venv\Scripts\activate.bat

:: --- 6. LAUNCH APPLICATION ---
echo [READY] All systems go! Launching Dashboard...
:: Start pythonw (no console) for the GUI
start /B "" "venv\Scripts\pythonw.exe" desktop_app.py

:: Exit launcher
exit
