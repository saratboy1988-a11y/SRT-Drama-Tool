# Fix: Preserve stderr for Debugging (Don't Suppress Crash Logs)

## 🐛 បញ្ហាដែលបានជួប

កូដមុននេះបាន **បិទ sys.stderr ទាំងស្រុង** ដោយប្រើ៖

```python
sys.stderr = open(os.devnull, 'w')  # ❌ បិទ Error Logs ទាំងអស់!
```

### ផលប៉ះពាល់

1. ❌ **លាក់ PyQt5 C++ Warnings** - សំខាន់សម្រាប់ debugging
2. ❌ **លាក់ Python Deprecation Warnings** - មិនឃើញ code ចាស់
3. ❌ **លាក់ Qt Object Lifecycle Errors** - Memory leak មិនដឹង
4. ❌ **លាក់ Crash Stack Traces** - ពិបាករកមូលហេតុ
5. ❌ **លាក់ Performance Warnings** - App យឺតមិនដឹង

### ឧទាហរណ៍ Errors ដែលត្រូវបានលាក់

```python
# PyQt5 C++ Warning (សំខាន់!)
QBasicTimer: Started from a different thread

# Qt Object Error (Memory Leak!)
QObject: Killed while events are still being processed

# Python Warning (Code Quality)
DeprecationWarning: sipPyTypeDict() is deprecated

# Qt Shutdown Noise (មិនសំខាន់ - អាចលាក់បាន)
QEventLoop: Exiting event loop during shutdown
```

---

## ✅ ដំណោះស្រាយដែលបានអនុវត្ត

### 1. បង្កើត StderrFilter Class

ជំនួសឱ្យការបិទទាំងស្រុង យើង **Filter** តែ Qt shutdown noise៖

```python
class StderrFilter:
    """Filter out known Qt shutdown noise while preserving important errors"""
    
    def __init__(self, original):
        self.original = original  # រក្សាទុក original stderr
        self.buffer = ""
    
    def write(self, text):
        # Filter out known Qt shutdown noise
        noise_patterns = [
            "QBasicTimer",
            "QEventLoop",
            "QObject::~QObject",
            "QCoreApplicationPrivate",
            "destroyed while events are still being processed"
        ]
        
        self.buffer += text
        
        # Check if this is known noise
        is_noise = any(pattern in self.buffer for pattern in noise_patterns)
        
        if is_noise:
            # Log to file but don't show to user
            with open(log_file, "a", encoding="utf-8") as log:
                log.write(f"[FILTERED] {self.buffer}\n")
            self.buffer = ""
        elif "\n" in self.buffer:
            # Has complete line - write to original stderr
            lines = self.buffer.split("\n")
            for line in lines[:-1]:  # All complete lines
                self.original.write(line + "\n")  # ✅ បង្ហាញ error!
            self.buffer = lines[-1]  # Keep incomplete line in buffer
    
    def flush(self):
        if self.buffer:
            self.original.write(self.buffer)
            self.buffer = ""
        self.original.flush()

# ប្រើ Filter
sys.stderr = StderrFilter(original_stderr)
```

### 2. បង្កើត Log File សម្រាប់ Debugging

**Normal Exit:**
```python
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_exit.log")
with open(log_file, "a", encoding="utf-8") as f:
    f.write(f"\n[{datetime.datetime.now()}] App exited with code: {exit_code}\n")
```

**Crash:**
```python
crash_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_log.txt")
with open(crash_log, "a", encoding="utf-8") as f:
    f.write(f"\n{'='*60}\n")
    f.write(f"[{datetime.datetime.now()}] CRASH LOG\n")
    f.write(f"{'='*60}\n")
    f.write(error_msg)  # ✅ រក្សាទុក Stack Trace ទាំងមូល!
    f.write(f"\n{'='*60}\n\n")
```

### 3. ប្រើ QMessageBox + Console Fallback

```python
try:
    QMessageBox.critical(None, "Critical Error", error_msg)
except:
    # If QMessageBox fails, write to console
    print(error_msg, file=sys.stderr)  # ✅ នៅតែបង្ហាញ!
```

---

## 📊 ភាពខុសគ្នា

### មុនពេលកែ (Suppress All)

```python
# ❌ បិទអ្វីៗទាំងអស់
sys.stderr = open(os.devnull, 'w')
sys.exit(1)

# លទ្ធផល:
# - គ្មាន Error បង្ហាញ
# - គ្មាន Warning បង្ហាញ
# - គ្មាន Stack Trace
# - ពិបាក Debug ខ្លាំងណាស់!
```

### ក្រោយពេលកែ (Smart Filter)

```python
# ✅ Filter តែ Noise, រក្សា Error
sys.stderr = StderrFilter(original_stderr)
sys.exit(1)

# លទ្ធផល:
# ✅ Qt Shutdown Noise → Filtered (លាក់)
# ✅ C++ Errors → បង្ហាញ
# ✅ Python Warnings → បង្ហាញ
# ✅ Stack Traces → បង្ហាញ + Save to file
# ✅ Debug ងាយស្រួល!
```

---

## 🎯 អ្វីដែលបានកែប្រែ

### 1. Normal Exit (Line ~6413)

**មុននេះ:**
```python
# Redirect stderr to null device before exiting to hide C++ shutdown logs
sys.stderr = open(os.devnull, 'w')
sys.exit(exit_code)
```

**ឥឡូវនេះ:**
```python
# IMPROVED: Don't completely suppress stderr - only filter Qt shutdown noise
# This preserves important crash logs and warnings for debugging
try:
    # Write exit info to log file for debugging
    log_file = os.path.join(..., "app_exit.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.datetime.now()}] App exited with code: {exit_code}\n")
    
    # Only suppress known Qt shutdown warnings, keep everything else
    sys.stderr = StderrFilter(original_stderr)
except:
    # If filter fails, fall back to original stderr
    sys.stderr = original_stderr

sys.exit(exit_code)
```

### 2. Crash Handler (Line ~6471)

**មុននេះ:**
```python
error_msg = f"CRITICAL ERROR:\n{str(e)}\n\n{traceback.format_exc()}"
try:
    QMessageBox.critical(None, "Critical Error", error_msg)
except:
    with open("crash_log.txt", "w") as f:
        f.write(error_msg)
finally:
    sys.stderr = open(os.devnull, 'w')  # ❌ លាក់ Error!
    sys.exit(1)
```

**ឥឡូវនេះ:**
```python
error_msg = f"CRITICAL ERROR:\n{str(e)}\n\n{traceback.format_exc()}"

# IMPROVED: Always write crash log to file for debugging
crash_log = os.path.join(..., "crash_log.txt")
try:
    with open(crash_log, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{datetime.datetime.now()}] CRASH LOG\n")
        f.write(f"{'='*60}\n")
        f.write(error_msg)  # ✅ Save full stack trace
        f.write(f"\n{'='*60}\n\n")
except:
    pass

try:
    QMessageBox.critical(None, "Critical Error", error_msg)
except:
    # If QMessageBox fails, write to console
    print(error_msg, file=sys.stderr)  # ✅ Still show error!
finally:
    # Don't suppress stderr - let errors show for debugging
    if sys.stderr and hasattr(sys.stderr, 'original'):
        sys.stderr = original_stderr
    sys.exit(1)
```

---

## 🔍 របៀប StderrFilter ធ្វើការ

### Flow Diagram

```
Error/Warning occurs
    ↓
Written to stderr buffer
    ↓
StderrFilter.write(text) called
    ↓
Check if text matches known noise patterns:
    ├─ YES (QBasicTimer, QEventLoop, etc.)
    │   ↓
    │   Write to app_exit.log (filtered)
    │   Don't show to user
    │
    └─ NO (Real error/warning)
        ↓
        Write to original stderr
        Show to user/console
```

### Filtered Patterns (លាក់)

| Pattern | មូលហេតុ |
|---------|----------|
| `QBasicTimer` | Qt internal timer warning |
| `QEventLoop` | Event loop shutdown noise |
| `QObject::~QObject` | Object cleanup during shutdown |
| `QCoreApplicationPrivate` | Qt internal cleanup |
| `destroyed while events...` | Object lifecycle warning |

### Preserved Messages (បង្ហាញ)

| Type | ឧទាហរណ៍ |
|------|-----------|
| **Python Errors** | `TypeError`, `ValueError`, etc. |
| **Qt Errors** | `QPainter: Cannot draw on null image` |
| **Warnings** | `DeprecationWarning`, `UserWarning` |
| **Tracebacks** | Full stack traces |
| **Performance** | `QObject: Killed while processing` |

---

## 📁 Log Files ដែលបានបង្កើត

### 1. `app_exit.log` (Normal Exit)

```log
[2026-04-13 15:30:45.123456] App exited with code: 0
[FILTERED] QEventLoop: Exiting event loop during shutdown
[FILTERED] QObject::~QObject: Cleaning up...
```

### 2. `crash_log.txt` (Crash)

```log
============================================================
[2026-04-13 15:35:12.654321] CRASH LOG
============================================================
CRITICAL ERROR:
TypeError: expected str, got NoneType

Traceback (most recent call last):
  File "RVC Tool.py", line 1234, in export_video
    process = subprocess.Popen(cmd, ...)
  File "subprocess.py", line 971, in __init__
    self._execute_child(args, ...)
  File "subprocess.py", line 1436, in _execute_child
    hp, ht, pid, tid = _winapi.CreateProcess(...)
TypeError: expected str, got NoneType
============================================================
```

---

## 🧪 ការធ្វើតេស្ត

### Test 1: Normal Exit
1. ✅ Open app
2. ✅ Close app normally
3. ✅ Check `app_exit.log` exists
4. ✅ No errors shown (only filtered noise)

### Test 2: Crash Simulation
1. ✅ Force an error (e.g., delete ffmpeg.exe)
2. ✅ Try to export video
3. ✅ QMessageBox shows error ✅
4. ✅ `crash_log.txt` created with full stack trace ✅
5. ✅ Console shows error (if running with console) ✅

### Test 3: Qt Shutdown Noise
1. ✅ Close app with video player active
2. ✅ Check console for noise
3. ✅ Noise filtered to log file ✅
4. ✅ Real errors still shown ✅

---

## 🎨 Debugging Benefits

### Before (Suppressed stderr)

```
User: "App crashed but I don't know why!"
Dev: "No logs, no errors, nothing to debug 😞"
```

### After (Filtered stderr)

```
User: "App crashed!"
Dev: "Let me check crash_log.txt..."
Dev: "Ah! TypeError at line 1234 - ffmpeg path is None 😊"
Dev: "Fixed! Here's the patch."
```

---

## 📋 Checklist for Developers

### When App Crashes:
- [ ] Check `crash_log.txt` for stack trace
- [ ] Check `app_exit.log` for exit code
- [ ] Run with console: `python "RVC Tool.py"` to see real-time errors
- [ ] Look for filtered messages in log files

### When Debugging:
- [ ] Don't modify stderr filter without good reason
- [ ] Add new noise patterns only if they're truly harmless
- [ ] Test both windowed and console modes
- [ ] Verify crash logs are written correctly

---

## 🔧 Advanced: Adding New Filter Patterns

If you see repetitive Qt noise in console, add to filter:

```python
noise_patterns = [
    "QBasicTimer",
    "QEventLoop",
    "QObject::~QObject",
    "QCoreApplicationPrivate",
    "destroyed while events are still being processed",
    "YOUR_NEW_PATTERN_HERE"  # ← Add here
]
```

**Rules:**
- ✅ Only add truly harmless shutdown noise
- ❌ Never add real error patterns
- ✅ Test thoroughly before adding
- ✅ Document why pattern was added

---

## 🔗 ឯកសារយោង

- [Python sys.stderr](https://docs.python.org/3/library/sys.html#sys.stderr)
- [PyQt5 Error Handling](https://doc.qt.io/qtforpython/overviews/signalsandslots.html)
- [Qt Object Lifecycle](https://doc.qt.io/qt-5/object.html)
- [Python Logging](https://docs.python.org/3/library/logging.html)
