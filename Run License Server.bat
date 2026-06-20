@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON_CMD="
if exist ".venv\Scripts\python.exe" set "PYTHON_CMD=.venv\Scripts\python.exe"
if not defined PYTHON_CMD (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)
if not defined PYTHON_CMD (
    python --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo [ERROR] Python was not found.
    echo Please install Python 3.10+ or run this from the development folder with .venv.
    pause
    exit /b 1
)

%PYTHON_CMD% "License Server Launcher.py"
if errorlevel 1 (
    echo.
    echo [ERROR] License server launcher failed.
)
pause
