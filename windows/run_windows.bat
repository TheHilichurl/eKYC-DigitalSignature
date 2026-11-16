@echo off
title eKYC & Digital Signature System - Windows Desktop
color 0B
echo ========================================================
echo    eKYC Digital Signature System (Windows Desktop Pro)
echo    Theme: Cobalt Blue (#1D4ED8) & Orange (#EA580C)
echo ========================================================
echo.
echo [*] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b 1
)

echo [*] Launching Desktop App...
cd /d "%~dp0"
python main_desktop.py

if %errorlevel% neq 0 (
    echo.
    echo [!] Desktop app exited with error code %errorlevel%.
    pause
)

