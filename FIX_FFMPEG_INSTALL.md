# Fix: FFmpeg Auto-Install Permission & Antivirus Handling

## 🐛 បញ្ហាដែលបានជួប

ការ Auto-Download & Install FFmpeg អាចជួបបញ្ហា៖

### 1. ❌ Antivirus Blocking
- **Windows Defender** ឬ **Third-party AV** block Python download/extraction
- **Error**: "Permission denied" ឬ "Access denied"
- **សញ្ញាណ**: Download មិនបាន ឬ Extract fail

### 2. ❌ No Admin Rights
- User មិនមានសិទ្ធិ Admin លើ PC
- **Error**: "PermissionError: [WinError 5] Access is denied"
- **កន្លែង**: ព្យាយាម install ទៅ `C:\Program Files` ឬ `C:\Windows`

### 3. ❌ Corporate Network Restrictions
- **Firewall** block Python internet access
- **Proxy** settings មិនត្រឹមត្រូវ
- **Error**: "URLError" ឬ "Connection timeout"

### 4. ❌ No Fallback Option
- បើ Auto-install fail → គ្មានជម្រើសផ្សេង
- User មិនដឹងថាត្រូវធ្វើដូចម្តេចបន្ត

---

## ✅ ដំណោះស្រាយដែលបានអនុវត្ត

### 1. បន្ថែម Permission Error Handling

**មុននេះ (មិនមាន Error Handling):**
```python
os.makedirs(install_path, exist_ok=True)  # ❌ Fail បើគ្មាន permission
urllib.request.urlretrieve(url, zip_path, download_progress)  # ❌ Block ដោយ AV
```

**ឥឡូវនេះ (មាន Error Handling):**
```python
try:
    os.makedirs(install_path, exist_ok=True)
    report_progress(f"✓ Installation directory: {install_path}")
except PermissionError as e:
    report_progress(f"✗ Permission denied: {install_path}")
    report_progress(f"💡 Try running as Administrator or choose a different location")
    return False

# Try download with timeout
try:
    urllib.request.urlretrieve(url, zip_path, download_progress)
    report_progress("✓ Download complete")
except PermissionError as e:
    report_progress(f"✗ Download blocked by Antivirus/Permissions: {e}")
    report_progress(f"💡 Try: 1) Disable Antivirus temporarily, or 2) Manual install")
    continue
except urllib.error.URLError as e:
    report_progress(f"✗ Network error: {e}")
    report_progress(f"💡 Check internet connection or try manual install")
    continue
```

### 2. បន្ថែម Extraction Error Handling

**មុននេះ:**
```python
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)  # ❌ Fail បើ AV block
```

**ឥឡូវនេះ:**
```python
try:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    report_progress("✓ Extraction complete")
except PermissionError as e:
    report_progress(f"✗ Extraction failed - Antivirus may be blocking: {e}")
    report_progress(f"💡 Solution: Disable Antivirus temporarily, then retry")
    continue
except zipfile.BadZipFile as e:
    report_progress(f"✗ Corrupted download: {e}")
    report_progress(f"💡 Try again or use manual install")
    continue
```

### 3. បន្ថែម Installation Error Handling

**មុននេះ:**
```python
shutil.copy2(ffmpeg_exe, os.path.join(bin_dir, "ffmpeg.exe"))  # ❌ Fail
```

**ឥឡូវនេះ:**
```python
try:
    bin_dir = os.path.join(install_path, "bin")
    os.makedirs(bin_dir, exist_ok=True)

    shutil.copy2(ffmpeg_exe, os.path.join(bin_dir, "ffmpeg.exe"))
    report_progress("✓ Installed ffmpeg.exe")

    if ffprobe_exe:
        shutil.copy2(ffprobe_exe, os.path.join(bin_dir, "ffprobe.exe"))
        report_progress("✓ Installed ffprobe.exe")

    # Copy DLLs if any
    for root, dirs, files in os.walk(extract_path):
        for file in files:
            if file.lower().endswith('.dll'):
                src = os.path.join(root, file)
                dst = os.path.join(bin_dir, file)
                try:
                    shutil.copy2(src, dst)
                except PermissionError:
                    report_progress(f"⚠️ Could not copy {file} (may not be needed)")

    report_progress("\n✓ FFmpeg installed successfully!")
    report_progress(f"📍 Location: {bin_dir}")
    return True

except PermissionError as e:
    report_progress(f"✗ Installation failed - Permission denied: {e}")
    report_progress(f"💡 Try: 1) Run as Administrator, or 2) Choose different drive")
    continue
```

### 4. បង្កើត Manual Installation Guide

**Function ថ្មី: `print_manual_install_guide()`**

បង្ហាញការណែនាំលម្អិតពេល Auto-install fail៖

```python
def print_manual_install_guide(install_path):
    """Print manual installation instructions when auto-install fails"""
    print("\n" + "="*60)
    print("⚠️  MANUAL INSTALLATION REQUIRED")
    print("="*60)
    print("\n🔍 Possible causes for auto-install failure:")
    print("  1. Antivirus software is blocking download/extraction")
    print("  2. No internet connection or firewall blocking")
    print("  3. Permission denied (try running as Administrator)")
    print("  4. Corporate network restrictions")
    print("\n" + "-"*60)
    print("📖 MANUAL INSTALLATION STEPS:")
    print("-"*60)
    print(f"\n1️⃣  Download FFmpeg from one of these sources:")
    print("   • https://www.gyan.dev/ffmpeg/builds/ (Recommended)")
    print("   • https://github.com/BtbN/FFmpeg-Builds/releases")
    print("   • https://github.com/GyanD/codexffmpeg/releases")
    print("\n2️⃣  Choose: 'ffmpeg-*-full' or 'ffmpeg-*-latest' (Windows 64-bit)")
    print("   • Download the ZIP file (not .7z)")
    print("\n3️⃣  Extract the downloaded archive")
    print("   • Right-click → Extract All")
    print("   • Note the extraction folder")
    print("\n4️⃣  Copy files to this location:")
    print(f"   📍 {install_path}\\bin\\")
    print("\n   You need these files in the bin folder:")
    print("   • ffmpeg.exe (required)")
    print("   • ffprobe.exe (recommended)")
    print("   • Any .dll files from the extracted folder")
    print("\n5️⃣  Restart SRT Drama Tool")
    print("   • The app will detect FFmpeg automatically")
    print("\n" + "-"*60)
    print("💡 QUICK FIXES FOR ANTIVIRUS:")
    print("-"*60)
    print("  • Windows Defender: Settings → Virus & threat protection")
    print("    → Add exclusion for: Python.exe and app folder")
    print("  • Other AV: Temporarily disable during installation")
    print("  • Corporate PC: Ask IT department to whitelist Python")
    print("\n" + "-"*60)
    print("🛡️  PORTABLE FFMPEG OPTION:")
    print("-"*60)
    print("  If you can't install to system folders:")
    print("  1. Extract FFmpeg to any folder you have access to")
    print("  2. In SRT Drama Tool → Settings tab")
    print("  3. Set FFmpeg path to your extracted ffmpeg.exe")
    print("="*60 + "\n")
```

### 5. បន្ថែម User-Friendly Messages in Main App

**មុននេះ:**
```python
subprocess.Popen([sys.executable, script_path])
self.log("✓ FFmpeg installer started")
```

**ឥឡូវនេះ:**
```python
# Run with CREATE_NO_WINDOW to avoid console flash
subprocess.Popen(
    [sys.executable, script_path],
    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
)
self.log("✓ FFmpeg installer started in background")
self.log("→ Please wait for installer to complete...")
self.log("💡 If auto-install fails, manual instructions will be shown")

# Permission error handling
except PermissionError as e:
    self.log("✗ Permission denied - Try running as Administrator")
    self.log("💡 Or manually install FFmpeg (see Settings tab for instructions)")
```

---

## 📍 ទីតាំងដែលបានកែប្រែ

### 1. `install_ffmpeg.py` - Line ~78

**Function: `download_ffmpeg()`**
- ✅ Added PermissionError handling for directory creation
- ✅ Added URLError handling for network issues
- ✅ Added Antivirus blocking detection
- ✅ Added user-friendly error messages with solutions

### 2. `install_ffmpeg.py` - Line ~142

**ZIP Extraction**
- ✅ Added BadZipFile handling
- ✅ Added PermissionError handling for extraction
- ✅ Continued to next source on failure

### 3. `install_ffmpeg.py` - Line ~175

**Installation**
- ✅ Added PermissionError handling for file copy
- ✅ Added DLL copy error tolerance
- ✅ Added success message with location

### 4. `install_ffmpeg.py` - Line ~510

**New Function: `print_manual_install_guide()`**
- ✅ Comprehensive manual installation guide
- ✅ Multiple download sources listed
- ✅ Antivirus workaround instructions
- ✅ Portable FFmpeg option

### 5. `RVC Tool.py` - Line ~4132

**Function: `install_ffmpeg_auto()`**
- ✅ Added CREATE_NO_WINDOW flag
- ✅ Added PermissionError handling
- ✅ Added user-friendly messages
- ✅ Added manual install fallback suggestion

---

## 🎯 អត្ថប្រយោជន៍

### មុនពេលកែ
```
❌ Antivirus block → App crash
❌ No admin rights → Silent fail
❌ Network error → No feedback
❌ User confused → No solution
```

### ក្រោយពេលកែ
```
✅ Antivirus block → Clear message + Manual guide
✅ No admin rights → Suggest different location
✅ Network error → Suggest manual install
✅ User guided → Step-by-step instructions
```

---

## 📊 Error Scenarios & Solutions

### Scenario 1: Antivirus Blocking

**Error:**
```
PermissionError: [WinError 5] Access is denied
```

**Auto Message:**
```
✗ Download blocked by Antivirus/Permissions
💡 Try: 1) Disable Antivirus temporarily, or 2) Manual install
```

**Manual Guide:**
```
💡 QUICK FIXES FOR ANTIVIRUS:
  • Windows Defender: Settings → Virus & threat protection
    → Add exclusion for: Python.exe and app folder
  • Other AV: Temporarily disable during installation
```

### Scenario 2: No Admin Rights

**Error:**
```
PermissionError: [WinError 5] Access is denied
✗ Installation failed - Permission denied
```

**Auto Message:**
```
💡 Try: 1) Run as Administrator, or 2) Choose different drive
```

**Manual Guide:**
```
🛡️  PORTABLE FFMPEG OPTION:
  If you can't install to system folders:
  1. Extract FFmpeg to any folder you have access to
  2. In SRT Drama Tool → Settings tab
  3. Set FFmpeg path to your extracted ffmpeg.exe
```

### Scenario 3: Network/Firewall Block

**Error:**
```
URLError: <urlopen error [Errno 11001] getaddrinfo failed>
```

**Auto Message:**
```
✗ Network error
💡 Check internet connection or try manual install
```

**Manual Guide:**
```
1️⃣  Download FFmpeg from one of these sources:
   • https://www.gyan.dev/ffmpeg/builds/ (Recommended)
   • https://github.com/BtbN/FFmpeg-Builds/releases
   • https://github.com/GyanD/codexffmpeg/releases
```

---

## 🧪 ការធ្វើតេស្ត

សូមសាកល្បងសេណារីយ៉ូទាំងនេះ៖

### Test 1: Normal Installation
1. ✅ Run `python install_ffmpeg.py`
2. ✅ មើល Download progress
3. ✅ មើល Extraction
4. ✅ មើល Success message

### Test 2: Permission Denied (Simulated)
1. ✅ ព្យាយាម install ទៅ `C:\Program Files`
2. ✅ មើល Permission error message
3. ✅ មើល Manual installation guide

### Test 3: Network Error (Disconnect Internet)
1. ✅ បិទ Internet
2. ✅ Run installer
3. ✅ មើល Network error message
4. ✅ មើល Manual guide printed

### Test 4: App Integration
1. ✅ Open SRT Drama Tool
2. ✅ ចុច "Install FFmpeg" button
3. ✅ មើល Log messages
4. ✅ មើល Background process (no console flash)

---

## 📋 Checklist for Users

### Before Auto-Install:
- [ ] Internet connection is stable
- [ ] Antivirus temporarily disabled (if needed)
- [ ] Running as Administrator (if possible)

### If Auto-Install Fails:
- [ ] Read error message carefully
- [ ] Check "Possible causes" section
- [ ] Follow "Manual Installation Steps"
- [ ] Copy files to correct location
- [ ] Restart app

### After Manual Install:
- [ ] ffmpeg.exe is in `{path}\bin\`
- [ ] ffprobe.exe is in `{path}\bin\`
- [ ] App detects FFmpeg automatically
- [ ] Test Export works

---

## 🔧 Troubleshooting

### Q: Antivirus keeps blocking installation

**A:** Add exclusion for:
1. Python executable: `C:\Python310\python.exe`
2. App folder: `E:\Software maker\SRT Drama Tool\`
3. FFmpeg install path: `C:\RVC_Tools\FFmpeg\`

### Q: No admin rights on PC

**A:** Use Portable FFmpeg:
1. Download FFmpeg ZIP
2. Extract to any folder you can access (e.g., Desktop)
3. In app → Settings → Set FFmpeg path to `ffmpeg.exe`

### Q: Corporate firewall blocks download

**A:** Manual install:
1. Download FFmpeg on different PC (home)
2. Copy ZIP via USB
3. Extract on work PC
4. Copy to app folder

### Q: Extraction fails with "Access denied"

**A:** 
1. Right-click ZIP file → Properties
2. Check "Unblock" checkbox (if present)
3. Try extracting to Desktop first
4. Then copy extracted files manually

---

## 🔗 ឯកសារយោង

- [FFmpeg Downloads](https://www.gyan.dev/ffmpeg/builds/)
- [Windows Defender Exclusions](https://support.microsoft.com/en-us/windows/add-an-exclusion-to-windows-security-811816c0-4dfd-af4a-47e4-c301afe13726)
- [Python subprocess](https://docs.python.org/3/library/subprocess.html)
- [urllib.request](https://docs.python.org/3/library/urllib.request.html)
