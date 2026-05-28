# 📦 មគ្គុទ្ទេសក៍ Build & Package - DramaTool RVC PRO

## ចាប់ផ្តើមរហ័ស

### ជម្រើសទី 1: Build ទាំងអស់ (ណែនាំ) ⭐
គ្រាន់តែ run:
```
build_complete_package.bat
```
វានឹង:
- ✅ Build កម្មវិធីធំ (Main Application EXE)
- ✅ Build License Generator (ជាជម្រើស)
- ✅ បង្កើត Windows Installer (.exe)

### ជម្រើសទី 2: Build ម្តងមួយៗ
- `build_exe.bat` - Build តែកម្មវិធីធំ
- `build_license_gen.bat` - Build តែ license generator

---

## 📋 តម្រូវការមុន

### កម្មវិធីចាំបាច់
1. **Python 3.8+** (64-bit ណែនាំ)
   - ទាញយក: https://www.python.org/downloads/
   - ✅ ជ្រើស "Add to PATH" ពេល install

2. **Inno Setup** (សម្រាប់បង្កើត installer)
   - ទាញយក: http://www.jrsoftware.org/isdl.php
   - Install ទៅទីតាំងដើម (default)

### Python Packages (build scripts install ដោយស្វ័យបរវត្តិ)
- pyinstaller
- PyQt5
- edge-tts
- pydub
- aiohttp
- gradio_client

---

## 🔨 Build Scripts ពន្យល់

### 1. `build_complete_package.bat` ⭐ **ណែនាំបំផុត**
**គោលបំណង**: Build ទាំងអស់ក្នុងមួយ

**អ្វីដែលវាធ្វើ**:
1. ✅ ពិនិត្យ Python installation
2. ✅ Install requirements ទាំងអស់
3. ✅ Build កម្មវិីធំ (DramaTool RVC PRO.exe)
4. ✅ ជាជម្រើស build License Generator
5. ✅ បង្កើត Inno Setup installer
6. ✅ បើក output folders
7. ✅ បង្ហាញ distribution checklist

**Output**:
- `dist\DramaTool RVC PRO.exe` (~100-150 MB)
- `installer_output\DramaTool_RVC_PRO_v15.6_Setup.exe` (~50-100 MB)

### 2. `build_exe.bat`
**គោលបំណង**: Build តែកម្មវិធីធំ

**អ្វីដែលវាធ្វើ**:
1. ពិនិត្យ Python
2. Install requirements
3. សម្អាត builds ចាស់
4. Build EXE ជាមួយ PyInstaller
5. ផ្ទៀងផ្ទាត់ build

**Output**: `dist\DramaTool RVC PRO.exe`

### 3. `build_license_gen.bat`
**គោលបំណង**: Build តែ license generator

**Output**: `dist_gen\LicenseGenerator.exe`

---

## 📦 Inno Setup Installer

### ឯកសារ: `DramaTool_RVC_PRO_Installer.iss`

**មុខងារ**:
- ✅ Installer UI វិជ្ជាជីវៈ
- ✅ រក version ចាស់ដោយស្វ័យបរវត្តិ ហើយ uninstall
- ✅ បង្កើត Desktop shortcut
- ✅ បង្កើត Start menu shortcuts
- ✅ FFmpeg រួមបញ្ចូល
- ✅ Configuration files ត្រូវបានរក្សាទុកពេល update
- ✅ User អាចជ្រើសរក្សា/លុប settings ពេល uninstall
- ✅ 64-bit Windows តែប៉ុណ្ណោះ (Win 7+)
- ✅ Compression សម្រាប់ installer តូច

### Installer Customization

Edit `DramaTool_RVC_PRO_Installer.iss` ដើម្បីកែ:

```pascal
; ព័ត៌មានកម្មវិធី
#define MyAppName "DramaTool RVC PRO"
#define MyAppVersion "15.6"
#define MyAppPublisher "Nou Sarat"
#define MyAppURL "https://www.youtube.com/@TechFree2026"

; Installer Output
OutputBaseFilename=DramaTool_RVC_PRO_v{#MyAppVersion}_Setup

; ទីតាំង Install
DefaultDirName={autopf}\{#MyAppName}

; បញ្ចូល/លុក Files
; Add or remove files in the [Files] section
```

---

## 🎯 ដំណើរការ Build មួយជំហានម្តង

### ដំណើរការ Build ដោយដៃ

#### ជំហានទី 1: Install Dependencies
```bash
pip install pyinstaller edge-tts pydub PyQt5 aiohttp gradio_client
```

#### ជំហានទី 2: Build ជាមួយ PyInstaller
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

#### ជំហានទី 3: Test EXE
```bash
cd dist
"DramaTool RVC PRO.exe"
```

#### ជំហានទី 4: បង្កើត Installer (បើមាន Inno Setup)
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" DramaTool_RVC_PRO_Installer.iss
```

#### ជំហានទី 5: Test Installer
- Run installer លើ system ស្អាត
- ផ្ទៀងផ្ទាត់ installation location
- Test មុខងារទាំងអស់
- Test uninstallation

---

## 📁 រចនាសម្ព័ន្ធ Output

```
e:\Software maker\RVC Tool - Copy\
├── dist\
│   └── DramaTool RVC PRO.exe           ← កម្មវិីធំ
├── dist_gen\
│   └── LicenseGenerator.exe            ← License generator (ជាជម្រើស)
├── installer_output\
│   └── DramaTool_RVC_PRO_v15.6_Setup.exe ← Windows installer
├── build\                               ← Temporary (លុបបន្ទាប់ពី build)
├── build_gen\                           ← Temporary (លុបបន្ទាប់ពី build)
└── *.spec                               ← PyInstaller config (លុបបន្ទាប់ពី build)
```

---

## 🐛 ដោះស្រាយបញ្ហា

### Build Fail ជាមួយ "Module not found"
**ដំណោះស្រាយ**: Run `pip install -r requirements.txt`

### PyInstaller បង្កើត EXE ខូច
**ដំណោះស្រាយ**: 
1. លុប folders `build` និង `dist`
2. លុប files `*.spec`
3. Run build script ម្តងទៀតជាមួយ `--clean` flag

### Inno Setup រកមិនឃើញ
**ដំណោះស្រាយ**: 
- Install Inno Setup ទៅទីតាំងដើម
- ឬកែ path ដោយដៃក្នុង `build_complete_package.bat`

### EXE file ធំពេក (>200MB)
**ដំណោះស្រាយ**:
- ប្រើ UPX compression: `--upx-dir=C:\path\to\upx`
- លុក modules ដែលមិនប្រើ
- ប្រើ `--exclude-module=matplotlib` (បើមិនប្រើ)

### Installer fail ពេល compile
**ដំណោះស្រាយ**:
- ពិនិត្យ .iss file syntax
- ប្រាកដថា files ទាំងអស់ក្នុង [Files] section មាន
- ពិនិត្យ Inno Setup version (ត្រូវការ 5.5+)

### Antivirus flag EXE
**ដំណោះស្រាយ**:
- នេះធមមតាជាមួយ PyInstaller (false positive)
- បន្ថែម exception ក្នុង antivirus
- ប្រើ code signing certificate (សម្រាប់ production)

---

## 📊 Distribution Checklist

### មុនពេលចែកចាយ
- [ ] Build កម្មវិធី EXE
- [ ] Test EXE លើ development machine
- [ ] Test EXE លើ Windows 10/11 VM ស្អាត
- [ ] បង្កើត Inno Setup installer
- [ ] Test installer លើ system ស្អាត
- [ ] ផ្ទៀងផ្ទាត់ themes ដំណើរការ
- [ ] Test មុខងារធំៗ:
  - [ ] Video loading
  - [ ] SRT loading
  - [ ] TTS generation
  - [ ] RVC voice conversion
  - [ ] Export functionality
  - [ ] Settings persistence
  - [ ] Theme switching
- [ ] Test uninstallation
- [ ] ពិនិត្យ license system
- [ ] ពិនិត្យ file sizes
- [ ] បង្កើត release notes

---

## 🔐 Code Signing (ជាជម្រើស ប៉ុន្តែណែនាំ)

សម្រាប់ production releases, sign EXE របស់អ្នក:

### ទិញ Code Signing Certificate
- ពី: Comodo, DigiCert, GlobalSign, ជាដើម
- ឬប្រើ: Let's Encrypt (free ប៉ុន្តែកំណត់)

### Sign EXE
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com "DramaTool RVC PRO.exe"
```

### Sign Installer
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com "DramaTool_RVC_PRO_v15.6_Setup.exe"
```

---

## 📝 គ្រប់គ្រង Version History

Update version numbers ក្នុង:
1. `DramaTool_RVC_PRO_Installer.iss` - `#define MyAppVersion`
2. `RVC Tool.py` - Window title
3. `build_complete_package.bat` - Echo messages
4. Release notes/documentation

---

## 🎓 Tips សម្រាប់ Builds ល្អជាង

### កាត់បន្ថយ EXE Size
1. លុក unused imports ពី code
2. ប្រើ `--exclude-module` សម្រាប់ packages មិនចាំបាច់
3. Enable UPX compression
4. លុក debug files

### បង្កើន Build Speed
1. រក្សា pip cache enabled
2. ប្រើ virtual environment
3. Install តែ packages ចាំបាច់
4. ប្រើ SSD សម្រាប់ build directory

---

## 📞 ជំនួយ

**Developer**: Nou Sarat  
**Telegram**: 096 22 11 947  
**YouTube**: https://www.youtube.com/@TechFree2026  

---

## ✅ ឯកសារយោងរហ័ស

### Build ទាំងអស់
```
build_complete_package.bat
```

### Build តែ App
```
build_exe.bat
```

### Build តែ License Generator
```
build_license_gen.bat
```

### Manual Inno Setup Compile
```
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" DramaTool_RVC_PRO_Installer.iss
```

---

**ស្ថានភាព**: ✅ **Build scripts ទាំងអស់ត្រូវបាន test ហើយដំណើរការ**  
**បច្ចុបបន្នភាពចុងក្រោយ**: 2026-04-13  
**Version**: 15.6
