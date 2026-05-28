# 📦 Build & Package Guide - DramaTool RVC PRO

## Quick Start

### Option 1: Build Everything (Recommended)
Simply run:
```
build_complete_package.bat
```
This will:
- ✅ Build main application EXE
- ✅ Build License Generator (optional)
- ✅ Create Windows Installer (.exe)

### Option 2: Build Individually
- `build_exe.bat` - Build only the main application
- `build_license_gen.bat` - Build only the license generator

---

## 📋 Prerequisites

### Required Software
1. **Python 3.8+** (64-bit recommended)
   - Download: https://www.python.org/downloads/
   - ✅ Add to PATH during installation

2. **Inno Setup** (for creating installer)
   - Download: http://www.jrsoftware.org/isdl.php
   - Install to default location

### Python Packages (auto-installed by build scripts)
- pyinstaller
- PyQt5
- edge-tts
- pydub
- aiohttp
- gradio_client

---

## 🔨 Build Scripts Explained

### 1. `build_complete_package.bat` ⭐ **RECOMMENDED**
**Purpose**: Build everything in one go

**What it does**:
1. ✅ Checks Python installation
2. ✅ Installs all requirements
3. ✅ Builds main application (DramaTool RVC PRO.exe)
4. ✅ Optionally builds License Generator
5. ✅ Creates Inno Setup installer
6. ✅ Opens output folders
7. ✅ Shows distribution checklist

**Output**:
- `dist\DramaTool RVC PRO.exe` (~100-150 MB)
- `installer_output\DramaTool_RVC_PRO_v15.6_Setup.exe` (~50-100 MB)

### 2. `build_exe.bat`
**Purpose**: Build only the main application

**What it does**:
1. Checks Python
2. Installs requirements
3. Cleans old builds
4. Builds EXE with PyInstaller
5. Verifies build

**Output**: `dist\DramaTool RVC PRO.exe`

### 3. `build_license_gen.bat`
**Purpose**: Build only the license generator

**What it does**:
1. Checks Python
2. Installs PyQt5
3. Builds LicenseGenerator.exe

**Output**: `dist_gen\LicenseGenerator.exe`

---

## 📦 Inno Setup Installer

### Inno Setup Script: `DramaTool_RVC_PRO_Installer.iss`

**Features**:
- ✅ Professional installer UI
- ✅ Automatic old version detection and removal
- ✅ Desktop shortcut creation
- ✅ Start menu shortcuts
- ✅ FFmpeg included
- ✅ Configuration files preserved on update
- ✅ User can choose to keep/delete settings on uninstall
- ✅ 64-bit Windows only (Win 7+)
- ✅ Compression for smaller installer size
- ✅ Version information embedded

### Installer Customization

Edit `DramaTool_RVC_PRO_Installer.iss` to customize:

```pascal
; App Information
#define MyAppName "DramaTool RVC PRO"
#define MyAppVersion "15.6"
#define MyAppPublisher "Nou Sarat"
#define MyAppURL "https://www.youtube.com/@TechFree2026"

; Installer Output
OutputBaseFilename=DramaTool_RVC_PRO_v{#MyAppVersion}_Setup

; Installation Location
DefaultDirName={autopf}\{#MyAppName}

; Include/Exclude Files
; Add or remove files in the [Files] section
```

### Installer Sections Explained

#### [Setup]
Basic installer configuration (app name, version, paths)

#### [Files]
Files to include in installer:
- Main EXE
- FFmpeg files
- Configuration files
- Helper scripts
- Documentation

#### [Icons]
Shortcuts to create:
- Start menu
- Desktop (optional)
- Quick launch (optional)

#### [Run]
Post-installation actions:
- Launch application (optional)

#### [Code]
Advanced features:
- Version detection
- Old version removal
- Settings preservation prompt
- Permission handling

---

## 🎯 Build Process Step-by-Step

### Manual Build Process

#### Step 1: Install Dependencies
```bash
pip install pyinstaller edge-tts pydub PyQt5 aiohttp gradio_client
```

#### Step 2: Build with PyInstaller
```bash
pyinstaller --noconfirm --onefile --windowed --clean ^
 --name "DramaTool RVC PRO" ^
 --hidden-import=edge_tts ^
 --hidden-import=pydub ^
 --hidden-import=aiohttp ^
 --hidden-import=gradio_client ^
 --collect-all edge_tts ^
 "RVC Tool.py"
```

#### Step 3: Test the EXE
```bash
cd dist
"DramaTool RVC PRO.exe"
```

#### Step 4: Create Installer (if Inno Setup installed)
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" DramaTool_RVC_PRO_Installer.iss
```

#### Step 5: Test the Installer
- Run installer on clean system
- Verify installation location
- Test all features
- Test uninstallation

---

## 📁 Output Structure

```
e:\Software maker\RVC Tool - Copy\
├── dist\
│   └── DramaTool RVC PRO.exe           ← Main application
├── dist_gen\
│   └── LicenseGenerator.exe            ← License generator (optional)
├── installer_output\
│   └── DramaTool_RVC_PRO_v15.6_Setup.exe ← Windows installer
├── build\                               ← Temporary (deleted after build)
├── build_gen\                           ← Temporary (deleted after build)
└── *.spec                               ← PyInstaller config (deleted after build)
```

---

## 🐛 Troubleshooting

### Build Fails with "Module not found"
**Solution**: Run `pip install -r requirements.txt`

### PyInstaller creates broken EXE
**Solution**: 
1. Delete `build` and `dist` folders
2. Delete `*.spec` files
3. Run build script again with `--clean` flag

### Inno Setup not found
**Solution**: 
- Install Inno Setup to default location
- Or manually edit the path in `build_complete_package.bat`

### EXE file too large (>200MB)
**Solutions**:
- Use UPX compression: `--upx-dir=C:\path\to\upx`
- Exclude unnecessary modules
- Use `--exclude-module=matplotlib` (if not needed)

### Installer fails to compile
**Solutions**:
- Check .iss file syntax
- Ensure all files in [Files] section exist
- Check Inno Setup version (need 5.5+)

### Antivirus flags the EXE
**Solutions**:
- This is common with PyInstaller (false positive)
- Add exception in antivirus
- Use code signing certificate (for production)
- Submit to antivirus vendors for whitelisting

---

## 📊 Distribution Checklist

### Before Distribution
- [ ] Build application EXE
- [ ] Test EXE on development machine
- [ ] Test EXE on clean Windows 10/11 VM
- [ ] Create Inno Setup installer
- [ ] Test installer on clean system
- [ ] Verify all themes work
- [ ] Test all major features:
  - [ ] Video loading
  - [ ] SRT loading
  - [ ] TTS generation
  - [ ] RVC voice conversion
  - [ ] Export functionality
  - [ ] Settings persistence
  - [ ] Theme switching
- [ ] Test uninstallation
- [ ] Verify license system
- [ ] Check file sizes
- [ ] Create release notes

### Distribution Package
Include in release:
- [ ] Installer EXE
- [ ] README file
- [ ] Version information
- [ ] Change log
- [ ] License information
- [ ] Contact information

---

## 🔐 Code Signing (Optional but Recommended)

For production releases, sign your EXE:

### Get a Code Signing Certificate
- Purchase from: Comodo, DigiCert, GlobalSign, etc.
- Or use: Let's Encrypt (free but limited)

### Sign the EXE
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com "DramaTool RVC PRO.exe"
```

### Sign the Installer
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com "DramaTool_RVC_PRO_v15.6_Setup.exe"
```

---

## 📝 Version History Management

Update version numbers in:
1. `DramaTool_RVC_PRO_Installer.iss` - `#define MyAppVersion`
2. `RVC Tool.py` - Window title
3. `build_complete_package.bat` - Echo messages
4. Release notes/documentation

---

## 🎓 Tips for Better Builds

### Reduce EXE Size
1. Remove unused imports from code
2. Use `--exclude-module` for unnecessary packages
3. Enable UPX compression
4. Remove debug files

### Improve Build Speed
1. Keep pip cache enabled
2. Use virtual environment
3. Only install necessary packages
4. Use SSD for build directory

### Better Error Handling
1. Read error messages carefully
2. Check PyInstaller logs
3. Test on multiple Windows versions
4. Use compatibility mode if needed

---

## 📞 Support

**Developer**: Nou Sarat  
**Telegram**: 096 22 11 947  
**YouTube**: https://www.youtube.com/@TechFree2026  

---

## ✅ Quick Reference

### Build Everything
```
build_complete_package.bat
```

### Build Only App
```
build_exe.bat
```

### Build Only License Generator
```
build_license_gen.bat
```

### Manual Inno Setup Compile
```
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" DramaTool_RVC_PRO_Installer.iss
```

---

**Status**: ✅ **All build scripts tested and working**  
**Last Updated**: 2026-04-13  
**Version**: 15.6
