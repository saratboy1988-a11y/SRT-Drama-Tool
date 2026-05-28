# 🚀 ចាប់ផ្តើមរហ័ស - Build & Package

## 📥 អ្វីដែលត្រូវការ

### 1. Install Python
```
ទាញយក: https://www.python.org/downloads/
✅ ជ្រើស "Add to PATH" ពេល install
```

### 2. Install Inno Setup (សម្រាប់បង្កើត installer)
```
ទាញយក: http://www.jrsoftware.org/isdl.php
Install ទៅ default location
```

---

## ⚡ វិធីងាយបំផុត - Build ទាំងអស់!

### 1️⃣ Run Script តែមួយ

```
build_complete_package.bat
```

**វានឹងធ្វើអ្វីខ្លះ?**
- ✅ Install dependencies ទាំងអស់
- ✅ Build កម្មវិធី EXE
- ✅ បង្កើត Windows Installer
- ✅ បើក folder output

### 2️⃣ រង់ចាំ 3-5 នាទី
- Script នឹង install packages
- Build application
- បង្កើត installer

### 3️⃣ ទទួលបាន Files
```
dist\DramaTool RVC PRO.exe              ← កម្មវិីធំ
installer_output\DramaTool_RVC_PRO_v15.6_Setup.exe  ← Installer
```

**ចប់! រួចរាល់សម្រាប់ចែកចាយ!** 🎉

---

## 📦 ឯកសារទាំងអស់

### Build Scripts
| File | គោលបំណង |
|------|-----------|
| `build_complete_package.bat` ⭐ | Build ទាំងអស់ (ណែនាំ) |
| `build_exe.bat` | Build តែកម្មវិធីធំ |
| `build_license_gen.bat` | Build License Generator |

### Inno Setup
| File | គោលបំណង |
|------|-----------|
| `DramaTool_RVC_PRO_Installer.iss` | Script សម្រាប់បង្កើត installer |
| `build_complete_package.bat` | Auto-compile installer |

### Documentation
| File | ភាសា |
|------|-------|
| `BUILD_GUIDE.md` | អង់គ្លេស (លម្អិត) |
| `BUILD_GUIDE_KHMER.md` | ខ្មែរ (លម្អិត) |
| `QUICKSTART.md` | ខ្មែរ (សង្ខេប) |

---

## ❓ សំណួរញឹកញាប់

### Q: តើខ្ញុំត្រូវការអ្វីខ្លះ?
**A**: Python + Inno Setup (មើលខាងលើ)

### Q: Build យូរប៉ុន្មាន?
**A**: 3-5 នាទី (អាស្រ័យលើ internet speed)

### Q: EXE នៅឯណា?
**A**: `dist\DramaTool RVC PRO.exe`

### Q: Installer នៅឯណា?
**A**: `installer_output\DramaTool_RVC_PRO_v15.6_Setup.exe`

### Q: Build ហើយ EXE ធំពេក?
**A**: ធមមតា (~100-150 MB)។ ប្រើ UPX compression ដើម្បីកាត់បន្ថយ

### Q: Antivirus flag EXE?
**A**: False positive ធមមតា។ Add exception ឬ use code signing

---

## 🎯 ជំហានសាមញ្ញ

```
1. Install Python ✅
2. Install Inno Setup ✅
3. Double-click build_complete_package.bat ✅
4. រង់ចាំ 3-5 នាទី ⏱️
5. ទទួលបាន EXE + Installer 🎉
6. Test លើ clean system ✅
7. ចែកចាយ! 📦
```

---

## 🔧 បញ្ហា?

### Python រកមិនឃើញ
```
Install Python ហើយ add to PATH
Restart command prompt
```

### Inno Setup រកមិនឃើញ
```
Install Inno Setup
ឬ skip installer creation (យកតែ EXE)
```

### Build Fail
```
1. Delete build, dist folders
2. Delete *.spec files
3. Run build script ម្តងទៀត
```

---

## 📞 ជំនួយ

**Telegram**: 096 22 11 947  
**YouTube**: https://www.youtube.com/@TechFree2026  

---

## ✅ រួចរាល់!

គ្រាន់តែ run `build_complete_package.bat` ហើយរង់ចាំ!

**សាមញ្ញ ងាយស្រួល រហ័ស!** 🚀
