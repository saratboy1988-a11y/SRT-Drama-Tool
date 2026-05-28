# ការជួសជុល FFmpeg Auto-Install សម្រាប់ EXE

## ✅ អ្វីដែលបានជួសជុល:

### បញ្ហាចាស់:
```python
# កូដចាស់ - មិនដំណើរការក្នុង EXE!
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_ffmpeg.py")
```

**ហេតុអ្វីមិនដំណើរការ:**
- ពេល build ជា EXE, `__file__` ចង្អុលទៅ `_MEIPASS` folder (temporary)
- `install_ffmpeg.py` ត្រូវបាន copy ទៅ `dist/` ប៉ុន្តែកូដស្វែងរកខុសកន្លែង

### កូដថ្មី:
```python
# រក install_ffmpeg.py - ដំណើរការទាំង .py និង .exe
if getattr(sys, 'frozen', False):
    # កំពុងដំណើរការជា EXE
    base_dir = sys._MEIPASS
else:
    # កំពុងដំណើរការជា Python script
    base_dir = os.path.dirname(os.path.abspath(__file__))

script_path = os.path.join(base_dir, "install_ffmpeg.py")

# បើមិនមានក្នុង _MEIPASS ស្វែងរកក្នុង dist folder
if not os.path.exists(script_path):
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_ffmpeg.py")
```

**អ្វីដែលប្រសើរឡើង:**
1. ✅ ស្វែងរក `install_ffmpeg.py` បានត្រឹមត្រូវ (ទាំងក្នុង Python និង EXE)
2. ✅ ពិនិត្យ status រាល់ 10s, 30s, 60s (ជំនួសឱ្យ 5s តែម្តង)
3. ✅ បង្ហាញ path ដែលរំពឹងទុក បើរកមិនឃើញ

---

## 📦 របៀប Build EXE ថ្មី:

### ជំហានទី 1: Run Build
```bash
cd "e:\Software maker\SRT Drama Tool"
pyinstaller --clean "SRT Drama Tool.spec"
```

### ជំហានទី 2: Copy Files
```bash
copy /Y "install_ffmpeg.py" "dist\"
copy /Y "app_settings.json" "dist\"
copy /Y "version.txt" "dist\"
```

### ជំហានទី 3: Test
1. ចម្លង `dist\` folder ទៅកុំព្យូទ័រផ្សេង
2. ដំណើរការ `SRT Drama Tool.exe`
3. ចូលទៅ **Settings Tab** → **Required Software**
4. ចុច **"⬇️ Install FFmpeg Automatically"**
5. រង់ចាំ 30 វិនាទី - 5 នាទី
6. ពិនិត្យមើល log បើមាន "✓ FFmpeg installed"

---

## 🎯 អ្វីដែលត្រូវមានក្នុង `dist/` folder:

```
dist/
├── SRT Drama Tool.exe        ← Main application
├── install_ffmpeg.py         ← FFmpeg installer (ចាំបាច់!)
├── app_settings.json         ← Settings file
├── version.txt               ← Version info
└── [other files...]
```

---

## ⚠️ ចំណាំសំខាន់:

1. **install_ffmpeg.py** ត្រូវតែមានក្នុង `dist/` folder
2. អ្នកប្រើត្រូវមាន **Internet Connection** ដើម្បី download FFmpeg
3. បើមាន Antivirus អាចត្រូវ **disable temporarily** ពេល install
4. FFmpeg នឹងត្រូវ install ទៅ drive ដែលមាន space ច្រើនជាងគេ

---

## 🔍 របៀប Test លើកុំព្យូទ័រស្អាត:

1. ចម្លង `dist/` folder ទៅ USB drive
2. យកទៅដំណើរការលើកុំព្យូទ័រដែលមិនទាន់មាន FFmpeg
3. បើកកម្មវិធី → Settings → Install FFmpeg
4. ពិនិត្យមើល Log តើមានសារអ្វី

### Log ដែលរំពឹងទុក:
```
⬇️ Starting FFmpeg auto-installation...
✓ FFmpeg installer started in background
→ Please wait for installer to complete...
💡 If auto-install fails, manual instructions will be shown
```

បន្ទាប់មក 10-60 វិនាទី:
```
✓ FFmpeg status update: ✓ Found (Auto)
```

---

Developer: Nou Sarat | SRT Drama Tool
