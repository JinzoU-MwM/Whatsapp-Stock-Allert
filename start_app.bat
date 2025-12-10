@echo off
title StockSignal Launcher
cd /d "%~dp0"

echo ========================================================
echo      StockSignal AI (Gemini 2.0 Flash Exp)
echo ========================================================

:: Activate Environment
call venv\Scripts\activate.bat

:: Launch the Desktop App (GUI)
:: Using start /B pythonw to hide console window in production
echo [1/1] Starting Dashboard (Hidden Console)...
start /B "" "venv\Scripts\pythonw.exe" desktop_app.py

:: Exit launcher immediately
exit
