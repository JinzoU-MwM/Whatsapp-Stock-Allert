@echo off
title Installing Dependencies...
cd /d "%~dp0"

echo ===========================================
echo   Checking & Installing Dependencies
echo ===========================================

:: 1. SETUP VIRTUAL ENVIRONMENT
if not exist "venv" (
    echo [SETUP] Creating Python Virtual Environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
)

:: 2. ACTIVATE VENV
call venv\Scripts\activate.bat

:: 3. UPGRADE PIP
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

:: 4. INSTALL REQUIREMENTS
echo [SETUP] Installing libraries from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

:: 5. NODE JS DEPS
if exist "whatsapp-service" (
    if not exist "whatsapp-service\node_modules" (
        echo [SETUP] Installing WhatsApp Service dependencies...
        cd whatsapp-service
        call npm install
        cd ..
    )
)

:: 6. CREATE FLAG FILE
echo [SUCCESS] Dependencies installed. > .installed
echo Setup Complete!
timeout /t 2 >nul
