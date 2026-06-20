@echo off
chcp 65001 >nul
title Build Complete Package - SRT Drama Tool
cd /d "%~dp0"
set "APP_DIST_DIR=dist\SRT Drama Tool"
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
echo     COMPLETE BUILD PACKAGE FOR SRT DRAMA TOOL
echo     Developer: Nou Sarat
echo     This script will:
echo       1. Build the main application EXE
echo       2. Build the License Generator EXE (optional)
echo       3. Create Inno Setup Installer (optional)
echo ====================================================================
echo.

:: ============================================================================
:: Step 1: Build Main Application
:: ============================================================================
echo ====================================================================
echo     STEP 1: Building Main Application
echo ====================================================================
echo.

echo Checking PyInstaller...
%PYTHON_CMD% -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [WARNING] PyInstaller not found. Attempting to install...
    %PYTHON_CMD% -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller automatically.
        pause
        exit /b 1
    )
)

if exist "requirements.txt" (
    echo Installing requirements from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements.txt.
        echo Please fix the package installation errors above before building.
        pause
        exit /b 1
    )
)

echo Building main application...
echo This may take 10-30 minutes because Demucs AI/PyTorch packages are bundled...
echo.

%PYTHON_CMD% -m PyInstaller --clean "SRT Drama Tool.spec"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to build main application!
    echo Please check the errors above and try again.
    pause
    exit /b 1
)

:: Check if EXE was created
if not exist "%APP_EXE%" (
    echo.
    echo [ERROR] Main application EXE not found: %APP_EXE%
    echo Build may have failed due to recursion errors or missing dependencies.
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo     STEP 1 COMPLETE!
echo ====================================================================
echo Main application built successfully!
echo Output: %APP_EXE%
echo.

:: ============================================================================
:: Step 2: Copy Required Files to dist Folder
:: ============================================================================
echo ====================================================================
echo     STEP 2: Preparing Distribution Package
echo ====================================================================
echo.

echo Copying required files to dist folder...

:: Copy install_ffmpeg.py (not compiled, runs as Python script)
if exist "install_ffmpeg.py" (
    copy /Y "install_ffmpeg.py" "%APP_DIST_DIR%\" >nul 2>&1
    echo   + install_ffmpeg.py
)

:: Copy splash_logo.png (Required for startup)
if exist "splash_logo.png" (
    copy /Y "splash_logo.png" "%APP_DIST_DIR%\" >nul 2>&1
    echo   + splash_logo.png
)

:: Copy app_settings.json (if exists, don't overwrite if already there)
if exist "app_settings.json" (
    if not exist "%APP_DIST_DIR%\app_settings.json" (
        copy /Y "app_settings.json" "%APP_DIST_DIR%\" >nul 2>&1
        echo   + app_settings.json
    )
)

:: Copy version.txt
if exist "version.txt" (
    copy /Y "version.txt" "%APP_DIST_DIR%\" >nul 2>&1
    echo   + version.txt
)

:: Copy requirements.txt
if exist "requirements.txt" (
    copy /Y "requirements.txt" "%APP_DIST_DIR%\" >nul 2>&1
    echo   + requirements.txt
)

:: Copy ffmpeg.exe and ffprobe.exe (if they exist in current folder)
if exist "ffmpeg.exe" (
    copy /Y "ffmpeg.exe" "%APP_DIST_DIR%\" >nul 2>&1
    echo   + ffmpeg.exe
)
if exist "ffprobe.exe" (
    copy /Y "ffprobe.exe" "%APP_DIST_DIR%\" >nul 2>&1
    echo   + ffprobe.exe
)

:: Copy FFmpeg DLLs (if any)
for %%f in (*.dll) do (
    if exist "%%f" (
        copy /Y "%%f" "%APP_DIST_DIR%\" >nul 2>&1
        echo   + %%f
    )
)

echo.
echo Distribution package prepared!
echo.

:: ============================================================================
:: Step 3: Build License Generator (Optional)
:: ============================================================================
echo ====================================================================
echo     STEP 3: Build License Generator (Optional)
echo ====================================================================
echo.

set /p build_license="Do you want to build License Generator? (Y/N): "
if /i "%build_license%"=="Y" (
    echo.
    if not exist "LicenseGen.py" (
        echo [WARNING] LicenseGen.py not found!
        echo Skipping License Generator build.
    ) else (
        echo Building License Generator...
        
        if exist "build_license_gen.bat" (
            call build_license_gen.bat
        ) else (
            %PYTHON_CMD% -m PyInstaller --clean --distpath=dist_gen --workpath=build_gen --specpath=build_gen LicenseGenerator.spec 2>nul
            if errorlevel 1 (
                echo [ERROR] Failed to build License Generator!
            ) else (
                echo License Generator built successfully!
                if exist "dist_gen\LicenseGenerator.exe" (
                    copy /Y "dist_gen\LicenseGenerator.exe" "%APP_DIST_DIR%\" >nul 2>&1
                    echo   + Copied to %APP_DIST_DIR%\LicenseGenerator.exe
                )
            )
        )
    )
) else (
    echo Skipping License Generator build.
)

echo.
echo ====================================================================
echo     STEP 3 COMPLETE!
echo ====================================================================
echo.

:: ============================================================================
:: Step 4: Build Inno Setup Installer (Optional)
:: ============================================================================
echo ====================================================================
echo     STEP 4: Building Inno Setup Installer (Optional)
echo ====================================================================
echo.

set /p build_installer="Do you want to create Windows Installer? (Y/N): "
if /i not "%build_installer%"=="Y" (
    echo Skipping Inno Setup installer creation.
    goto :skip_installer
)

:: Check if Inno Setup is installed
set INNO_PATH=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set "INNO_PATH=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 5\ISCC.exe" (
    set "INNO_PATH=C:\Program Files\Inno Setup 5\ISCC.exe"
)

if "%INNO_PATH%"=="" (
    echo [WARNING] Inno Setup is not installed or not found!
    echo.
    echo To create an installer, please:
    echo   1. Download Inno Setup from: http://www.jrsoftware.org/isdl.php
    echo   2. Install it to default location
    echo   3. Run this script again
    echo.
    echo OR you can manually compile the .iss file later when Inno Setup is installed.
    echo.
    set /p skip_inno="Continue anyway? (Y/N): "
    if /i "%skip_inno%"=="N" (
        pause
        exit /b 1
    )
    goto :skip_installer
)

echo Found Inno Setup at: %INNO_PATH%
echo.

if not exist "%APP_DIST_DIR%\*" (
    echo [ERROR] Distribution folder is missing: %APP_DIST_DIR%
    echo Please finish Step 1 successfully before compiling the installer.
    goto :skip_installer
)

:: Check if .iss file exists
if not exist "SRT_Drama_Tool_Installer.iss" (
    echo [ERROR] Inno Setup script not found: SRT_Drama_Tool_Installer.iss
    echo Please ensure the .iss file exists before creating installer.
    goto :skip_installer
)

echo Creating installer output directory...
if not exist "installer_output" mkdir "installer_output"

echo.
echo Compiling Inno Setup Installer...
echo This may take a minute...
echo.

"%INNO_PATH%" "SRT_Drama_Tool_Installer.iss"

if %errorlevel% equ 0 (
    echo.
    echo ====================================================================
    echo     INSTALLER CREATED SUCCESSFULLY!
    echo ====================================================================
    echo.
    echo Installer Location: installer_output\
    echo.
    dir /b "installer_output\*.exe" 2>nul
    echo.
    echo Opening installer folder...
    explorer "installer_output"
) else (
    echo.
    echo [ERROR] Failed to create installer!
    echo Please check the Inno Setup script for errors.
    echo.
    set /p manual_inno="Open .iss file for editing? (Y/N): "
    if /i "%manual_inno%"=="Y" (
        notepad "SRT_Drama_Tool_Installer.iss"
    )
)

:skip_installer
echo.
echo ====================================================================
echo     BUILD PROCESS COMPLETE!
echo ====================================================================
echo.
echo Files created:
echo   [MAIN] %APP_EXE%
if exist "%APP_DIST_DIR%\install_ffmpeg.py" echo   [REQ]  %APP_DIST_DIR%\install_ffmpeg.py
if exist "%APP_DIST_DIR%\LicenseGenerator.exe" echo   [OPT]  %APP_DIST_DIR%\LicenseGenerator.exe
if exist "installer_output\*.exe" echo   [SETUP] installer_output\*.exe
echo.
echo ====================================================================
echo     DISTRIBUTION CHECKLIST:
echo ====================================================================
echo.
echo [ ] Test the application EXE
echo [ ] Test the installer on a clean system
echo [ ] Verify all features work correctly
echo [ ] Check themes load properly
echo [ ] Test video loading and playback
echo [ ] Test SRT loading
echo [ ] Test TTS generation
echo [ ] Test export functionality
echo [ ] Verify settings persistence
echo [ ] Check license system
echo.
echo ====================================================================

:: Ask to open dist folder
set /p open_dist="Open dist folder now? (Y/N): "
if /i "%open_dist%"=="Y" (
    explorer "%APP_DIST_DIR%"
)

pause
