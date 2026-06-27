@echo off
chcp 65001 >nul
title Build Package - SRT Drama Tool
cd /d "%~dp0"

echo ====================================================================
echo     SRT DRAMA TOOL PACKAGE BUILDER
echo ====================================================================
echo.
echo   1. Lite Installer  - small download, AI deps install online
echo   2. Full Offline    - large installer split into .exe + .bin files
echo.
set /p choice="Choose build type (1 or 2): "

if "%choice%"=="1" (
    call "%~dp0build_lite_package.bat"
    exit /b %errorlevel%
)

if "%choice%"=="2" (
    call "%~dp0build_full_package.bat"
    exit /b %errorlevel%
)

echo.
echo Invalid choice.
pause
exit /b 1
