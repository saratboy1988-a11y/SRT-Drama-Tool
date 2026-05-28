# ✅ K-Lite Codec Pack Integration - SRT Drama Tool v15.6

## 📋 Feature Added

**K-Lite Codec Pack** is now available as an alternative installation option in the **Settings → Required Software** tab.

---

## 🎯 What Does K-Lite Codec Pack Do?

**K-Lite Codec Pack** installs system-wide video codecs that enable:
- ✅ **All video formats** (MKV, AVI, MOV, FLV, WebM, etc.)
- ✅ **Works with QMediaPlayer** (PyQt5) - fixes video playback errors
- ✅ **Works with Windows Media Player**
- ✅ **Works with Windows Explorer** (video thumbnails)
- ✅ **Permanent solution** - once installed, all apps benefit

---

## 📊 Where to Find It

**Path:** Settings Tab → Required Software → **K-Lite Codec Pack (System-Wide Video Codecs)**

```
Settings Tab
├── System Status
├── Quick Actions
├── Required Software
│   ├── FFmpeg (Audio/Video Processing)
│   ├── K-Lite Codec Pack (System-Wide Video Codecs) ← NEW!
│   └── VC++ Redistributable (Runtime Library)
├── Auto-Save
├── Configuration
├── Logs
└── About
```

---

## ️ UI Elements

### **K-Lite Codec Pack Section:**

```
┌─ K-Lite Codec Pack (System-Wide Video Codecs) ─────────┐
│                                                          │
│  Installs system codecs to enable playback of all       │
│  video formats (MKV, AVI, MOV, etc.) in this app and    │
│  Windows Media Player.                                  │
│                                                          │
│  Status: ⚠ Not Installed  (or ✓ Detected)              │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ⬇️ Download & Install K-Lite Codec Pack (Basic) │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  [████████████████░░░░░░░░░░░░] 60% (Progress Bar)      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🔄 How It Works

### **1. User Clicks "Download & Install K-Lite Codec Pack"**

```
>> ⬇️ Starting K-Lite Codec Pack download...
→ K-Lite Codec Pack download started...
💡 File size: ~45 MB - Please wait for download to complete...
```

### **2. Download Progress**

- Progress bar updates: 0% → 10% → 20% → ... → 100%
- File downloads to: `klite_codec_basic.exe` (~45 MB)
- Download URL: `https://files3.codecguide.com/K-Lite_Codec_Pack_1875_Basic.exe`

### **3. Download Complete**

```
✓ Download complete: klite_codec_basic.exe
🚀 Launching K-Lite Codec Pack installer...
```

**Dialog appears:**
```
K-Lite Installation

✅ Download complete!

The K-Lite installer will now start.

Installation steps:
1. Click 'Next' through the installer
2. Choose 'Basic' or 'Standard' installation
3. Click 'Install' and wait for completion
4. Restart your computer (recommended)

After installation, all video formats (MKV, AVI, MOV) will work!

(កម្មវិធីដំឡើងនឹងចាប់ផ្តើមឡូវនេះ...)

[OK]
```

### **4. User Completes Installation**

After installation:
- K-Lite status updates to: **"✓ K-Lite Codec Pack Detected"**
- All video formats now work in the app!
- No more "Video format not supported" errors!

---

## 🎨 Status Detection

The app automatically detects if K-Lite is installed by checking:

### **Method 1: Windows Registry**
```
✓ SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\K-Lite Codec Pack_is1
✓ SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\K-Lite Codec Pack_is1
✓ SOFTWARE\WOW6432Node\KLCodecPack
✓ SOFTWARE\KLCodecPack
```

### **Method 2: System Files**
```
✓ C:\Windows\System32\lavvideo.ax
✓ C:\Windows\System32\lavsplitter.ax
✓ C:\Windows\System32\lavaudio.ax
```

If any of these are found → Status shows **"✓ K-Lite Codec Pack Detected"** (Green)
If none found → Status shows **"⚠ Not Installed"** (Yellow)

---

## 🆚 FFmpeg vs K-Lite Codec Pack

| Feature | FFmpeg | K-Lite Codec Pack |
|---------|--------|-------------------|
| **Purpose** | Convert videos to MP4 | Install system codecs |
| **Video Playback** | ✅ Works (after conversion) | ✅ Works (direct playback) |
| **File Size** | ~100 MB | ~45 MB |
| **Installation** | Automatic | Manual (user clicks Next) |
| **System Impact** | None (app-only) | System-wide |
| **Restart Required** | No | Recommended |
| **Best For** | Users who want automatic fix | Users who want permanent system fix |

---

## 💡 When to Recommend Each

### **Recommend FFmpeg When:**
- ✅ User wants automatic solution (no manual steps)
- ✅ User doesn't want to install system-wide codecs
- ✅ User only needs occasional video conversion
- ✅ User prefers app-specific solution

### **Recommend K-Lite When:**
- ✅ User wants to play ALL video formats directly (no conversion)
- ✅ User wants Windows Media Player to work with all formats
- ✅ User wants video thumbnails in Windows Explorer
- ✅ User is comfortable with manual installation steps
- ✅ User wants a permanent system-wide solution

---

## 🔧 Code Changes

### **New Methods Added:**

| Method | Purpose |
|--------|---------|
| `_update_klite_status_label()` | Update status label color and text |
| `_check_klite_installed()` | Detect K-Lite via registry/system files |
| `install_klite_codec()` | Main entry point - checks if already installed |
| `_download_klite()` | Start download in background thread |
| `on_klite_download_finished()` | Launch installer after download completes |

### **New UI Elements:**

| Element | Type | Purpose |
|---------|------|---------|
| `klite_group` | QGroupBox | Container for K-Lite section |
| `klite_desc` | QLabel | Description text |
| `lbl_klite_status` | QLabel | Status indicator |
| `btn_klite` | QPushButton | Download & Install button |
| `klite_progress` | QProgressBar | Download progress bar |
| `klite_thread` | DownloadThread | Background download thread |

---

## 📦 Files Modified

| File | Changes |
|------|---------|
| `SRT Drama Tool.py` | ✅ Added K-Lite UI section |
| `SRT Drama Tool.py` | ✅ Added 5 new methods for K-Lite |
| `SRT_Drama_Tool_Installer.iss` | ✅ Rebuilt installer |

---

## 🧪 Testing Instructions

### **Test on PC WITHOUT K-Lite:**

1. Install SRT Drama Tool on clean PC
2. Open app → Settings → Required Software
3. **Expected:** K-Lite status shows "⚠ Not Installed" (yellow)
4. Click **"Download & Install K-Lite Codec Pack"**
5. **Expected:** Download starts, progress bar updates
6. After download completes (~45 MB):
   - Installer launches automatically
   - Follow installer steps (Next → Next → Install)
7. After installation completes:
   - Status updates to "✓ K-Lite Codec Pack Detected" (green)
8. Load an MKV/AVI/MOV video
9. **Expected:** Video plays directly (no conversion needed!)

### **Test on PC WITH K-Lite Already Installed:**

1. Open app → Settings → Required Software
2. **Expected:** K-Lite status shows "✓ K-Lite Codec Pack Detected" (green)
3. Click **"Download & Install K-Lite Codec Pack"**
4. **Expected:** Dialog appears: "K-Lite Already Installed"
5. User can click OK or Ignore (to reinstall)

---

## ⚠️ Important Notes

### **For Users:**
- K-Lite Codec Pack Basic is **FREE** and safe
- Official download from: `https://codecguide.com/download_kl.htm`
- During installation, choose **"Basic"** or **"Standard"** (not "Full" or "Mega" unless needed)
- **Restart your computer** after installation for best results
- Once installed, it benefits ALL video apps, not just SRT Drama Tool

### **For Developers:**
- Download thread reuses existing `DownloadThread` class (code reuse!)
- Status detection checks both registry AND system files (fallback)
- Progress bar uses same pattern as FFmpeg installer
- Dialog includes both English and Khmer instructions

---

## ✅ Summary

**Before:** Users had only FFmpeg (convert videos) or manual K-Lite installation

**After:** Users can choose:
1. ✅ **FFmpeg** - Automatic video conversion (app-specific)
2. ✅ **K-Lite** - System-wide codec installation (permanent fix)
3. ✅ **Both** - Maximum compatibility!

**Result:** Better user experience, more options, solves video playback issues for all users! 🎉

---

Developer: Nou Sarat | SRT Drama Tool v15.6 PRO
Date: 2026-04-14
