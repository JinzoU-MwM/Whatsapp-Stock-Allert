@echo off
title StockSignal Installer
cd /d "%~dp0"

echo ========================================================
echo      StockSignal AI - Dependency Installer
echo ========================================================

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org.
    pause
    exit
)

:: 2. Create Virtual Environment
if not exist "venv" (
    echo [INFO] Creating virtual environment (venv)...
    python -m venv venv
) else (
    echo [INFO] Virtual environment found.
)

:: 3. Install Requirements
echo [INFO] Installing requirements...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

:: 4. Node.js Deps (WhatsApp Service)
if exist "whatsapp-service" (
    if not exist "whatsapp-service\node_modules" (
        echo [INFO] Installing WhatsApp Service dependencies...
        cd whatsapp-service
        call npm install
        cd ..
    )
)

:: 5. Finalize
if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Installation complete!
    echo You can now run 'start_app.bat' to launch the application.
    echo. > .installed
) else (
    echo.
    echo [ERROR] Failed to install dependencies. Check your internet connection.
)

pause
exit
