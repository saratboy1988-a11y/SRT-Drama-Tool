@echo off
chcp 65001 >nul
title Build License Generator - Dev: Nou Sarat
cd /d "%~dp0"

echo ======================================================
echo    BUILD LICENSE GENERATOR
echo    Developer: Nou Sarat
echo ======================================================
echo.

:: Check Python installation
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
python --version
echo.

echo [2/4] Installing requirements...
pip install pyinstaller PyQt5
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

pyinstaller --noconfirm --onefile --windowed --clean ^
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