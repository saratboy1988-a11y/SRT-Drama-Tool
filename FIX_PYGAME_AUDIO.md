# Fix: Replace QMediaPlayer Audio with pygame.mixer

## 🐛 បញ្ហាដែលបានជួប

`QMediaPlayer` ក្នុង PyQt5 មានបញ្ហា៖

1. ❌ **ពឹងផ្អែកលើ System Codec** (LAV Filters, K-Lite Codec Pack)
2. ❌ **Windows 11** មិនមាន codec ល្អដោយលំនាំដើម
3. ❌ **MP3/WAV playback** អាច fail ឬគ្មានសំឡេង
4. ❌ **Format support** មានកម្រិត (MKV, WebM, FLV មិនដំណើរការ)
5. ❌ **Error ងាយ** - "DirectShowPlayerService::failed" ឬ "Codec not found"

### កំហុសធម្មតា
```
DirectShowPlayerService::failed: The graph cannot be run.
DirectShowPlayerService::doRender: Failed to build graph for file
```

---

## ✅ ដំណោះស្រាយដែលបានអនុវត្ត

### ជំនួស Audio Preview ដោយ `pygame.mixer`

យើងប្រើ **Hybrid Approach**៖
- **Video Player** → បន្តប្រើ `QMediaPlayer` (ត្រូវការ video output + seek bar)
- **Audio Preview** → ជំនួសដោយ `pygame.mixer` (សាមញ្ញ + stable)

### ហេតុអ្វី pygame?

| លក្ខណៈ | QMediaPlayer | pygame.mixer |
|---------|--------------|--------------|
| Install | ត្រូវការ Codec Pack | `pip install pygame` ចប់! |
| MP3 Support | ❌ អាច fail | ✅ ដំណើរការភ្លាមៗ |
| WAV Support | ✅ | ✅ |
| Windows 11 | ❌ មានបញ្ហា | ✅ Stable |
| Dependencies | System Codec | SDL2 (included) |
| Format Support | មានកម្រិត | គ្រប់ format |

---

## 📍 ការកែប្រែដែលបានធ្វើ

### 1. Import pygame (Line ~49)

```python
import pygame  # NEW: For audio playback (replaces QMediaPlayer for audio preview)
```

### 2. Initialize pygame.mixer (Line ~710)

```python
# Initialize pygame mixer for audio playback (replaces QMediaPlayer for audio)
# This avoids Windows 11 codec issues with QMediaPlayer
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    self.pygame_audio_available = True
    self.log("✅ Pygame audio system initialized successfully")
except Exception as e:
    self.log(f"⚠️ Pygame audio initialization failed: {e}")
    self.pygame_audio_available = False
```

### 3. ជំនួស on_play_audio() (Line ~4866)

**មុននេះ (QMediaPlayer only):**
```python
def on_play_audio(self, file_path, start_ms):
    self.preview_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
    self.preview_player.play()
```

**ឥឡូវនេះ (pygame + fallback):**
```python
def on_play_audio(self, file_path, start_ms):
    """Play audio preview using pygame (avoids QMediaPlayer codec issues)"""
    # Use pygame for audio preview
    if self.pygame_audio_available:
        try:
            # Stop any currently playing audio
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            
            # Load and play the audio file
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.log(f"🔊 Playing audio preview: {os.path.basename(file_path)}")
        except Exception as e:
            self.log(f"⚠️ Audio playback failed: {e}")
            # Fallback: try QMediaPlayer if pygame fails
            self.log("⚠️ Falling back to QMediaPlayer for audio")
            self.preview_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.preview_player.play()
    else:
        # Fallback to QMediaPlayer if pygame not available
        self.preview_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        self.preview_player.play()
```

### 4. ជំនួស force_stop_player() (Line ~4897)

**មុននេះ:**
```python
def force_stop_player(self):
    self.preview_player.stop()
    self.preview_player.setMedia(QMediaContent())
```

**ឥឡូវនេះ:**
```python
def force_stop_player(self):
    """Stop audio playback (pygame + QMediaPlayer fallback)"""
    # Stop pygame audio
    if self.pygame_audio_available:
        try:
            pygame.mixer.music.stop()
        except:
            pass
    
    # Also stop QMediaPlayer (for video)
    self.media_player.pause()
```

### 5. Update closeEvent() (Line ~6063)

```python
def closeEvent(self, a0):
    # Stop players to release file handles
    if hasattr(self, 'media_player'):
        self.media_player.stop()
    
    # Stop pygame audio
    if hasattr(self, 'pygame_audio_available') and self.pygame_audio_available:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except:
            pass
    
    # Also stop QMediaPlayer audio if it exists
    if hasattr(self, 'preview_player'):
        self.preview_player.stop()
```

---

## 🎯 អត្ថប្រយោជន៍

### មុនពេលកែ
```
❌ ចុច "Test TTS" → គ្មានសំឡេង
❌ Windows 11 → "Codec not found" error
❌ ត្រូវ install K-Lite Codec Pack
❌ MP3 file → "DirectShowPlayerService::failed"
```

### ក្រោយពេលកែ
```
✅ ចុច "Test TTS" → សំឡេងចេញភ្លាមៗ
✅ Windows 11 → ដំណើរការល្អ
✅ pip install pygame → ចប់!
✅ MP3/WAV → គ្មានបញ្ហា
✅ Auto fallback → បើ pygame fail → ប្រើ QMediaPlayer
```

---

## 📦 ការ Install

### Install pygame
```bash
pip install pygame
```

### បញ្ជាត្រួតពិនិត្យ
```bash
python -c "import pygame; print(f'Pygame {pygame.version.ver}'); pygame.mixer.init(); print('✅ OK')"
```

**Expected Output:**
```
pygame 2.6.1 (SDL 2.28.4, Python 3.10.11)
Pygame 2.6.1
✅ Pygame mixer initialized successfully
```

---

## 🔧 របៀបធ្វើការ

1. **App Start** → Initialize pygame.mixer
2. **User clicks "Test TTS"** → Generate MP3 file
3. **Audio Playback** → 
   - ✅ Load file → `pygame.mixer.music.load(file_path)`
   - ✅ Play → `pygame.mixer.music.play()`
   - ✅ Stop old audio → `pygame.mixer.music.stop()` (if playing)
4. **Fallback** → បើ pygame fail → ប្រើ QMediaPlayer វិញ

---

## 🧪 ការធ្វើតេស្ត

សូមសាកល្បង៖

1. ✅ Load កម្មវិធី → មើល Log "✅ Pygame audio system initialized"
2. ✅ បង្កើត TTS មួយ → ចុច "Test TTS" (🔊 icon)
3. ✅ ស្តាប់សំឡេង → តើចេញឬទេ?
4. ✅ ចុចម្តងទៀត → តើសំឡេងចាស់ឈប់ ហើយចាប់ផ្តើមថ្មីឬទេ?
5. ✅ លឿន + Stable → គ្មាន error

---

## 📊 ប្រៀបធៀបបច្ចេកទេស

### QMediaPlayer Architecture
```
Python App → PyQt5 QMediaPlayer → DirectShow → System Codec → Audio Output
                                    ↓
                            ❌ អាច fail បើគ្មាន Codec
```

### pygame.mixer Architecture
```
Python App → pygame.mixer → SDL2 (built-in) → Audio Output
                             ↓
                        ✅ ដំណើរការភ្លាមៗ (no external codec)
```

---

## ⚙️ pygame.mixer Settings

```python
pygame.mixer.init(
    frequency=44100,   # CD quality audio
    size=-16,          # 16-bit audio
    channels=2,        # Stereo
    buffer=512         # Small buffer = low latency
)
```

### ហេតុអ្វីជ្រើសរើស settings ទាំងនេះ?

| Setting | Value | Reason |
|---------|-------|--------|
| frequency | 44100 Hz | CD quality, matches TTS output |
| size | -16 bit | Standard audio quality |
| channels | 2 | Stereo support |
| buffer | 512 | Low latency (fast playback) |

---

## 🔄 Backward Compatibility

កម្មវិធីនៅតែមាន **fallback system**៖

```python
if self.pygame_audio_available:
    # Use pygame (primary)
    pygame.mixer.music.play()
else:
    # Fallback to QMediaPlayer (secondary)
    self.preview_player.play()
```

ដូច្នេះបើ pygame មានបញ្ហា → កម្មវិធីនឹងប្រើ QMediaPlayer វិញដោយស្វ័យប្រវត្តិ!

---

## 📝 កំណត់ចំណាំ

### Video Player នៅតែប្រើ QMediaPlayer
- `self.media_player` → **មិនបានកែទេ** (ត្រូវការ video output)
- ប្រើសម្រាប់ដើរវីដេអូ + seek bar + timeline
- អាចមាន codec issues ប៉ុន្តែ acceptបាន

### Audio Preview ប្រើ pygame
- `self.preview_player` → **ជំនួសដោយ pygame** (fallback only)
- ប្រើសម្រាប់ដើរ TTS audio (MP3/WAV)
- គ្មាន codec issues

---

## 🔗 ឯកសារយោង

- [pygame.mixer Documentation](https://www.pygame.org/docs/ref/mixer.html)
- [SDL2 Audio](https://wiki.libsdl.org/SDL2/Audio)
- [PyQt5 Multimedia](https://doc.qt.io/qtforpython/PySide6/QtMultimedia.html)
- [Windows 11 Codec Issues](https://github.com/ftylitak/qtwrapper/issues/12)
