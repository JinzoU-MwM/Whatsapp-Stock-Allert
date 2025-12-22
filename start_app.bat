@echo off
title StockSignal Launcher
cd /d "%~dp0"

echo ========================================================
echo      StockSignal AI (Launch Mode)
echo ========================================================

:: 1. Verify Installation
if not exist "venv" (
    echo [ERROR] Virtual Environment not found!
    echo.
    echo Please run 'install_dependencies.bat' FIRST to set up the application.
    echo.
    pause
    exit
)

:: 2. Activate & Launch
echo [READY] Launching Dashboard...
:: Start pythonw (no console) for the GUI
start /B "" "venv\Scripts\pythonw.exe" desktop_app.py

:: Exit launcher
exit
