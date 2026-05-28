# ✅ Video Playback Error Fix - SRT Drama Tool v15.6

## 📋 Problem Description

**Error Message:**
```
Video format not supported or Codec missing.
Do you want to convert it to a compatible format (MP4)?
(វីដេអូមិនដំណើរការ តើអ្នកចង់បម្លែងវាទៅជា MP4 ដែរឬទេ?)
```

**When it occurs:**
- On clean PCs without video codecs installed
- When loading video formats like MKV, AVI, MOV, etc.
- QMediaPlayer in PyQt5 requires system codecs (K-Lite, LAV Filters, etc.)

---

## 🔧 What Was Fixed

### **Old Behavior:**
```
User loads video → Error dialog appears
→ User clicks "Yes" to convert
→ "FFmpeg not found" error (because FFmpeg not installed)
→ User stuck, doesn't know what to do
```

### **New Behavior:**
```
User loads video → Error dialog appears
→ App checks if FFmpeg is installed
→ If NO: Offers to install FFmpeg automatically
   → Redirects to Settings tab
   → Starts FFmpeg installer
   → After install, user can retry loading video
→ If YES: Offers to convert video to MP4
   → Converts using FFmpeg
   → Plays converted video automatically
```

---

## 💡 How It Works Now

### **Scenario 1: FFmpeg NOT Installed**

**Dialog shown:**
```
Playback Error - FFmpeg Required

Video format not supported or Codec missing.

To fix this, you need FFmpeg installed.
Would you like to install FFmpeg automatically?

(វីដេអូមិនដំណើរការ ត្រូវការ FFmpeg ដើម្បីបម្លែង។
តើអ្នកចង់ដំឡើង FFmpeg ដោយស្វ័យបរវត្តិ?)

[Yes] [No]
```

**If user clicks "Yes":**
1. ✅ Automatically switches to **Settings tab** → **Required Software** page
2. ✅ Starts **FFmpeg auto-installer** in background
3. ✅ Shows progress in logs (10%, 20%, 30%... 100%)
4. ✅ After installation completes, user can retry loading the video

**If user clicks "No":**
```
Codec Missing

Video cannot be played without codecs.

Options:
1. Install FFmpeg (Settings → Required Software)
2. Install K-Lite Codec Pack from:
   https://codecguide.com/download_kl.htm

(វីដេអូមិនដំណើរការ ជម្រើស:
 ១. ដំឡើង FFmpeg នៅ Settings tab
 ២. ដំឡើង K-Lite Codec Pack)

[OK]
```

---

### **Scenario 2: FFmpeg IS Installed**

**Dialog shown:**
```
Playback Error

Video format not supported or Codec missing.
Do you want to convert it to a compatible format (MP4)?
(វីដេអូមិនដំណើរការ តើអ្នកចង់បម្លែងវាទៅជា MP4 ដែរឬទេ?)

[Yes] [No]
```

**If user clicks "Yes":**
1. ✅ Converts video to MP4 using FFmpeg (H.264 + AAC)
2. ✅ Shows conversion progress (0% → 100%)
3. ✅ Automatically loads and plays the converted video
4. ✅ Saves as `video_name_fixed.mp4`

**If user clicks "No":**
```
Codec Missing

Video cannot be played.

Try installing K-Lite Codec Pack:
https://codecguide.com/download_kl.htm

(វីដេអូមិនដំណើរការ សូមដំឡើង K-Lite Codec Pack)

[OK]
```

---

## 🎯 Code Changes

### **Modified Function: `handle_errors()`**

**Old code:**
```python
def handle_errors(self):
    # ... error detection ...
    reply = QMessageBox.question(self, "Playback Error",
                                 "Video format not supported...")
    if reply == QMessageBox.Yes:
        self.convert_and_play_video()  # Fails if FFmpeg not installed!
```

**New code:**
```python
def handle_errors(self):
    # ... error detection ...
    
    # Check if FFmpeg is available first
    ffmpeg_path = self.get_ffmpeg()
    has_ffmpeg = os.path.exists(ffmpeg_path) if ffmpeg_path != "ffmpeg" else False

    if not has_ffmpeg:
        # FFmpeg not installed - offer to install it first
        reply = QMessageBox.question(
            self, "Playback Error - FFmpeg Required",
            "Video format not supported...\n"
            "Would you like to install FFmpeg automatically?..."
        )
        
        if reply == QMessageBox.Yes:
            # Switch to Settings tab and trigger FFmpeg install
            self.tabs.setCurrentIndex(2)  # Settings tab
            self._show_settings_page("software")  # Required Software page
            QTimer.singleShot(500, lambda: self.install_ffmpeg_auto())
    else:
        # FFmpeg is available - offer to convert
        reply = QMessageBox.question(...)
        if reply == QMessageBox.Yes:
            self.convert_and_play_video()
```

---

## 📦 Files Updated

| File | Changes |
|------|---------|
| `SRT Drama Tool.py` | ✅ Improved `handle_errors()` function |
| `SRT Drama Tool.py` | ✅ Added FFmpeg availability check |
| `SRT Drama Tool.py` | ✅ Auto-redirect to Settings for FFmpeg install |
| `SRT_Drama_Tool_Installer.iss` | ✅ Rebuilt installer |

---

## 🧪 Testing Instructions

### **Test on Clean PC (No FFmpeg, No Codecs):**

1. Install SRT Drama Tool on a fresh PC
2. Open the application
3. Click **"Open Video"** and select an MKV/AVI/MOV file
4. **Expected:** Error dialog appears with **"Install FFmpeg automatically?"** option
5. Click **"Yes"**
6. **Expected:** App switches to Settings tab, FFmpeg installer starts
7. Wait for installation (1-5 minutes)
8. After installation completes, reload the video
9. **Expected:** App offers to convert video → Click "Yes" → Video plays

### **Test on PC with FFmpeg Installed:**

1. Install FFmpeg first (Settings → Required Software → Install FFmpeg)
2. Load a video that doesn't play (MKV, AVI, etc.)
3. **Expected:** Error dialog appears with **"Convert to MP4?"** option
4. Click **"Yes"**
5. **Expected:** Video converts and plays automatically

---

## 💡 Additional Notes

### **Why This Happens:**
- **QMediaPlayer** in PyQt5 uses Windows Media Foundation
- Windows Media Foundation requires codecs for many video formats
- Clean Windows installations only support basic formats (MP4/H.264, WMV)
- Formats like MKV, AVI, MOV require additional codecs

### **Solutions for Users:**
1. **Install FFmpeg** (Recommended) - App can do this automatically
2. **Install K-Lite Codec Pack** - https://codecguide.com/download_kl.htm
3. **Use MP4 videos** - Most compatible format

### **FFmpeg Installation Location:**
- Auto-installs to: `D:\RVC_Tools\FFmpeg\bin\` (or drive with most space)
- Alternative: `C:\Program Files\SRT Drama Tool\ffmpeg\bin\`

---

## ✅ Summary

**Before:** User gets error → Clicks "Yes" → "FFmpeg not found" → Stuck

**After:** User gets error → App checks FFmpeg → If missing, offers to install → After install, offers to convert → Video plays

**Result:** Much better user experience, no confusion, automatic guidance! 🎉

---

Developer: Nou Sarat | SRT Drama Tool v15.6 PRO
Date: 2026-04-14
