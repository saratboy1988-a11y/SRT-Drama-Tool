# Fix: Real-Time FFmpeg Progress Tracking

## 🐛 បញ្ហាដែលបានជួប

មុនពេលកែប្រែ FFmpeg Export ប្រើ `subprocess.communicate()` ដែល៖
- ❌ **រង់ចាំរហូតដល់ចប់** (blocking call)
- ❌ **UI ហាក់ដូចជា "គាំង"** ពេល Export វីដេអូធំ
- ❌ **មិនមាន Progress** ជាក់ស្តែង (តែ 0% → 100% ភ្លាមៗ)
- ❌ **អ្នកប្រើមិនដឹង** ថាតើកំពុងដំណើរការឬអត់

```python
# ❌ មុននេះ (គ្មាន Progress)
process = subprocess.Popen(cmd, ...)
_, stderr = process.communicate()  # BLOCKS រហូតដល់ចប់!
self.progress.setValue(100)  # លោតពី 0 → 100 ភ្លាមៗ
```

---

## ✅ ដំណោះស្រាយដែលបានអនុវត្ត

### 1️⃣ បង្កើត Signal ថ្មីសម្រាប់ Progress Text

```python
class MainWindow(QMainWindow):
    progress_text_signal = pyqtSignal(str)  # NEW: សម្រាប់បង្ហាញអត្ថបទ
```

### 2️⃣ អាន FFmpeg stderr ជា Real-Time

ជំនួសឱ្យ `communicate()` ដែល block យើងប្រើ `readline()` ជា loop៖

```python
# ✅ ឥឡូវនេះ (Real-Time Progress)
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, ...)

# អាន stderr ម្តង់ៗជា real-time
while True:
    line = process.stderr.readline()
    if not line:
        break
    
    # Parse FFmpeg progress (time=HH:MM:SS.XX)
    if "time=" in line:
        time_match = re.search(r'time=(\d{2,}):(\d{2}):(\d{2})\.(\d{2})', line)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = int(time_match.group(3))
            current_time = hours * 3600 + minutes * 60 + seconds
            
            # គណនាភាគរយ
            progress_percent = int((current_time / total_duration) * 100)
            
            # Update UI ភ្លាមៗ
            self.progress_signal.emit(progress_percent)
            self.progress_text_signal.emit(f"Encoding: {progress_percent}%")

process.wait()  # រង់ចាំចប់
```

### 3️⃣ បង្កើត Method `get_video_duration_ms()`

ប្រើ ffprobe ដើម្បីទទួលបាន duration វីដេអូ៖

```python
def get_video_duration_ms(self, video_path):
    """Get video duration in milliseconds using ffprobe"""
    ffprobe_path = self._find_ffprobe()
    cmd = [
        ffprobe_path, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ]
    
    output = subprocess.check_output(cmd, ...).strip()
    duration_sec = float(output)
    return int(duration_sec * 1000)  # Return milliseconds
```

### 4️⃣ Update Progress Bar Text

```python
def update_progress_text(self, text):
    """Update progress bar text display (e.g., 'Encoding: 45%')"""
    if hasattr(self, 'export_progress'):
        self.export_progress.setFormat(text)
```

---

## 📍 ទីតាំងដែលបានកែប្រែ

### 1. Signal Declaration (Line ~630)
```python
progress_text_signal = pyqtSignal(str)  # NEW
```

### 2. Signal Connection (Line ~702)
```python
self.progress_text_signal.connect(self.update_progress_text)
```

### 3. Helper Method (Line ~4193)
```python
def get_video_duration_ms(self, video_path):
    """Get video duration for progress calculation"""
```

### 4. Progress Text Method (Line ~4422)
```python
def update_progress_text(self, text):
    """Update progress bar display"""
```

### 5. Export MP4 Thread (Line ~5707)
```python
# Changed from communicate() to readline() loop
# Added real-time progress updates
```

### 6. Proxy Conversion Thread (Line ~1905)
```python
# Added real-time progress for video conversion
```

### 7. Progress Bar Init (Line ~2894)
```python
self.export_progress.setFormat("Ready")  # Initial text
```

---

## 🎯 អត្ថប្រយោជន៍

| មុនពេលកែ | ក្រោយពេលកែ |
|-----------|------------|
| ❌ UI "គាំង" ពេល Export | ✅ UI រលូង មាន Progress ជាក់ស្តែង |
| ❌ 0% → 100% ភ្លាមៗ | ✅ 0% → 10% → 20% → ... → 100% |
| ❌ មិនដឹងថាកំពុង run | ✅ ឃើញភាគរយ + Speed (x) |
| ❌ Blocking call | ✅ Non-blocking, responsive |
| ❌ គ្មាន feedback | ✅ "Encoding: 45%", "⚡ 2.5x" |

---

## 📊 ឧទាហរណ៍ការបង្ហាញ

**កំឡុងពេល Export៖**
```
Progress Bar: [████████░░░░░░] Encoding: 45%
Log: ⚡ Encoding speed: 2.5x
```

**ពេលចប់៖**
```
Progress Bar: [██████████████] 100%
Log: ✅ Video Exported Successfully: Final_Video.mp4
```

**ពេលមាន Error៖**
```
Progress Bar: [██░░░░░░░░░░░░] Failed
Log: ❌ FFmpeg Export Error (code 1)...
```

---

## 🔧 របៀបធ្វើការ

1. **ចាប់ផ្តើម Export** → Progress = "Ready"
2. **រក Duration** → ffprobe អានវីដេអូ
3. **ចាប់ផ្តើម FFmpeg** → Popen (មិន block)
4. **អាន stderr ជា real-time** → readline() loop
5. **Parse "time=XX:XX:XX"** → គណនាភាគរយ
6. **Update UI** → Signal emit → Progress bar ផ្លាស់ប្តូរ
7. **Log speed** → "⚡ 2.5x" (បើមាន)
8. **ចប់** → 100% → Clear text → Auto-play (បើ enable)

---

## 🧪 ការធ្វើតេស្ត

សូមសាកល្បង៖

1. ✅ Load វីដេអូ (យ៉ាងហោចណាស់ 1-2 នាទី)
2. ✅ ចុច "Export MP4 Dub"
3. ✅ មើល Progress bar ថាតើវាផ្លាស់ប្តូរជា real-time ឬទេ?
4. ✅ ពិនិត្យ Log មាន "⚡ Encoding speed: Xx" ឬទេ?
5. ✅ ធានាថា UI មិនគាំង (អាច scroll log បាន)

---

## 📝 កំណត់ចំណាំ

### FFmpeg Output Format
FFmpeg output មានទម្រង់៖
```
frame= 1234 fps= 56 q=28.0 size=    5678kB time=00:01:23.45 bitrate= 567.8kbits/s speed= 2.5x
```

យើង parse៖
- `time=HH:MM:SS.XX` → ភាគរយ
- `speed=X.Xx` → ល្បឿន

### ហេតុអ្វីប្រើ stderr?
- FFmpeg សរសេរ progress ទៅ **stderr** (មិនមែន stdout)
- stdout ទុកសម្រាប់ output video data (pipe)
- stderr ទុកសម្រាប់ log + progress info

---

## 🔗 ឯកសារយោង

- [FFmpeg Documentation](https://ffmpeg.org/ffmpeg.html)
- [Python subprocess](https://docs.python.org/3/library/subprocess.html)
- [PyQt5 Signals](https://doc.qt.io/qtforpython/overviews/signalsandslots.html)
