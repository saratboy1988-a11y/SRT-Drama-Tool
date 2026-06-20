@echo off
chcp 65001 >nul
title Build License Generator - Dev: Nou Sarat
cd /d "%~dp0"

echo ======================================================
echo    BUILD LICENSE GENERATOR
echo    Developer: Nou Sarat
echo ======================================================
echo.

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
    echo [ERROR] Python 3 is not installed or not in PATH!
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
%PYTHON_CMD% --version
echo.

echo [2/4] Installing requirements...
%PYTHON_CMD% -m pip install pyinstaller PyQt5
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements!
    pause
    exit /b 1
)
echo [OK] Requirements installed!
echo.

echo [3/4] Cleaning old builds...
if exist "build_gen" rmdir /s /q "build_gen"
if exist "dist_gen" rmdir /s /q "dist_gen"
echo [OK] Cleaned!
echo.

echo [4/4] Building LicenseGenerator EXE...
echo Please wait...
echo.

%PYTHON_CMD% -m PyInstaller --noconfirm --onefile --windowed --clean ^
 --name "LicenseGenerator" ^
 --workpath "build_gen" ^
 --distpath "dist_gen" ^
 "LicenseGen.py"

if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
if exist "dist_gen\LicenseGenerator.exe" (
    echo ======================================================
    echo    BUILD SUCCESSFUL!
    echo ======================================================
    echo.
    echo File: LicenseGenerator.exe
    echo Location: dist_gen\
    echo.
    echo Opening folder...
    explorer "dist_gen"
) else (
    echo [ERROR] Build failed - EXE not created!
)

echo.
pause
