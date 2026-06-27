@echo off
chcp 65001 >nul
title Build Full Offline Package - SRT Drama Tool
cd /d "%~dp0"

set "APP_DIST_DIR=dist\SRT Drama Tool Full"
set "APP_EXE=%APP_DIST_DIR%\SRT Drama Tool.exe"
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
    echo [ERROR] Python 3 was not found. Install Python 3.10+ or create .venv first.
    pause
    exit /b 1
)

echo ====================================================================
echo     BUILDING SRT DRAMA TOOL FULL OFFLINE PACKAGE
echo ====================================================================
echo Full bundles PyTorch, TorchAudio, TorchVision, Demucs, and AI deps.
echo This build is large, but works offline after installation.
echo.

%PYTHON_CMD% -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [WARNING] PyInstaller not found. Installing...
    %PYTHON_CMD% -m pip install pyinstaller
    if errorlevel 1 exit /b 1
)

echo Installing full requirements...
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

echo Building Full app...
%PYTHON_CMD% -m PyInstaller --clean "SRT Drama Tool Full.spec"
if errorlevel 1 (
    echo [ERROR] Full build failed.
    pause
    exit /b 1
)

if not exist "%APP_EXE%" (
    echo [ERROR] Full EXE not found: %APP_EXE%
    pause
    exit /b 1
)

if exist "ffmpeg.exe" (
    copy /Y "ffmpeg.exe" "%APP_DIST_DIR%\" >nul 2>&1
    echo + ffmpeg.exe
)
if exist "ffprobe.exe" (
    copy /Y "ffprobe.exe" "%APP_DIST_DIR%\" >nul 2>&1
    echo + ffprobe.exe
)

set "INNO_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%INNO_PATH%" set "INNO_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%INNO_PATH%" (
    if not exist "installer_output" mkdir "installer_output"
    echo Building Full installer...
    "%INNO_PATH%" "SRT_Drama_Tool_Full_Installer.iss"
) else (
    echo [WARNING] Inno Setup not found. Full dist folder is ready.
)

echo.
echo Full package ready:
echo   %APP_EXE%
if exist "installer_output\*Full*.exe" echo   installer_output\*Full*.exe
pause
