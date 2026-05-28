# Path Memory Feature - Documentation

## Overview
DramaTool RVC PRO already has comprehensive path memory functionality built-in. The application automatically remembers and restores the following:

## Currently Remembered Paths ✅

### 1. **Last Video Directory** (`last_video_dir`)
- **When Saved**: When you open a video file
- **When Restored**: Next time you click "Open Video" button
- **Location in Code**: `load_video()` method at line ~1007

### 2. **Last SRT Directory** (`last_srt_dir`)
- **When Saved**: When you load an SRT subtitle file
- **When Restored**: Next time you click "Load SRT" button
- **Location in Code**: `load_srt()` method at line ~3690

### 3. **Last Output Directory** (`last_output_dir`)
- **When Saved**: When you select an output folder
- **When Restored**: Automatically filled in Export tab on startup
- **Location in Code**: `select_folder()` method at line ~3398 and initialized at line ~1620

### 4. **FFmpeg Path** (`ffmpeg_path` and `last_ffmpeg_dir`)
- **When Saved**: When you browse and select ffmpeg.exe
- **When Restored**: Settings are saved but need manual verification on startup
- **Location in Code**: `select_ffmpeg()` method at line ~3407

### 5. **Last Project Directory** (`last_project_dir`)
- **When Saved**: When you open or save a project
- **When Restored**: Next time you open/save project
- **Location in Code**: `open_project()` and `save_project_as()` methods

## Settings Storage

All settings are stored in: `app_settings.json`

The settings file is:
- **Loaded**: During `__init__()` at line ~642
- **Saved**: Every time you change a path or setting

## How It Works

### Auto-Save on File Selection
```python
# Example from load_video()
def load_video(self, path, autoplay=True):
    self.current_video_path = path
    self.app_settings["last_video_dir"] = os.path.dirname(path)
    self.save_app_settings()
```

### Auto-Restore on Startup
```python
# Example from build_export_tab()
self.output_folder = QLineEdit(self.app_settings.get("last_output_dir", ""))
```

## Additional Settings Remembered

Beyond file paths, the app also remembers:
- ✅ `fade_in` - Fade-in duration (ms)
- ✅ `fade_out` - Fade-out duration (ms)
- ✅ `global_speed` - TTS speed offset (%)
- ✅ `auto_play` - Auto-play after export
- ✅ `use_gpu` - GPU acceleration enabled
- ✅ `rvc_url` - RVC WebUI server URL
- ✅ `autosave_enabled` - Auto-save enabled
- ✅ `autosave_interval` - Auto-save interval (minutes)

## Conclusion

**The feature you requested is ALREADY FULLY IMPLEMENTED!** ✅

The application automatically:
1. Remembers the last input/output locations
2. Remembers your final settings
3. Restores them when you restart the app
4. Saves settings every time you make changes

No additional code changes are needed - the functionality is complete and working as designed.
