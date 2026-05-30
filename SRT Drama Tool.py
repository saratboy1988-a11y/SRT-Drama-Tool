# -*- coding: utf-8 -*-
"""
SRT Drama Tool v1.0.10
PART 1 - Core UI + Light Accent Theme
Author: NOU SARAT
"""

import sys
import os
import urllib.request
import urllib.error
import zipfile
import shutil
import platform
original_stderr = sys.stderr

os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "windowsmediafoundation"
# Suppress Logs (Must be set before importing heavy libraries)
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false;qt.text.font.warning=false;qt.font.warning=false;qt.drawing.warning=false"
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "3"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import json
import subprocess
import traceback
import asyncio # type: ignore
import threading
import time
import random
import re
import winreg
import gc
import glob
import hashlib
import hmac
import base64
import datetime
import tempfile
import ctypes
import edge_tts # type: ignore
from typing import cast, Union, Optional, Any, Callable
from pydub import AudioSegment
import pygame  # NEW: For audio playback (replaces QMediaPlayer for audio preview)

try:
    from test_gpu import detect_gpu
except ImportError:
    detect_gpu = None
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QTimer, QTime, QThread, QEvent
from PyQt5.QtGui import QFont, QColor, QDesktopServices, QPixmap, QCloseEvent, QFontDatabase
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt5 import sip  # For checking if QObject is deleted
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGridLayout, QLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QProgressBar, QSlider, QGroupBox,
    QTabWidget, QScrollArea, QFileDialog, QMessageBox, QHeaderView, QTableWidget,
    QTableWidgetItem, QSplitter, QTimeEdit, QMenuBar, QMenu, QAction, QStatusBar,
    QStyle, QDialog, QFrame, QGraphicsView, QGraphicsScene, QSizePolicy, QStackedWidget, QSplashScreen
)

# Constants for Pylance/Qt Enum compatibility
QT_HORIZONTAL = 1
QT_VERTICAL = 2
QT_USER_ROLE = 256
QT_IGNORE_ASPECT_RATIO = 0
QSTYLE_SP_MEDIA_PLAY = 62
QSTYLE_SP_MEDIA_PAUSE = 63
MEDIA_PLAYER_PLAYING = 1
MEDIA_PLAYER_STOPPED = 0
QT_ITEM_IS_EDITABLE = 2

# =============================
# Application Constants
# =============================

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS # type: ignore
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    path = os.path.join(base_path, relative_path)
    if not os.path.exists(path) and getattr(sys, 'frozen', False):
        # Fallback to executable directory if not found in _MEIPASS
        path = os.path.join(os.path.dirname(sys.executable), relative_path)
    return path

# Dynamic Version Management
# Priority: version.txt > Git tag > Hardcoded fallback
def get_app_version():
    """Get app version dynamically from version.txt or Git tag"""
    # Try to read from version.txt first
    version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.txt")
    if os.path.exists(version_file):
        try:
            with open(version_file, "r") as f:
                version = f.read().strip()
                if version:
                    return version
        except:
            pass
    
    # Try to get from Git tag
    try:
        git_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".git")
        if os.path.exists(git_dir):
            import subprocess as _subprocess
            result = _subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True, text=True, timeout=5,
                creationflags=_subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            if result.returncode == 0:
                return result.stdout.strip().lstrip("v")
    except:
        pass
    
    # Fallback to hardcoded version
    return "1.0.10"

APP_VERSION = get_app_version()
APP_NAME = "SRT Drama Tool"
DEFAULT_UPDATE_URL = "https://github.com/saratboy1988-a11y/SRT-Drama-Tool/releases/latest"
DEFAULT_UPDATE_API_URL = "https://api.github.com/repos/saratboy1988-a11y/SRT-Drama-Tool/releases/latest"
APP_MUTEX_NAME = "Global\\SRTDramaToolSingleInstance"
ONLINE_LICENSE_CONFIG_FILE = "license_server_config.json"
ONLINE_LICENSE_STORE_FILE = "online_license.json"
ONLINE_LICENSE_GRACE_DAYS = 3
DEFAULT_KHMER_FONT = "Noto Sans Khmer"
KHMER_FONT_CHOICES = [
    "Noto Sans Khmer",
    "Khmer OS",
    "Khmer OS System",
    "Khmer OS Siemreap",
    "Khmer OS Battambang",
    "Khmer OS Bokor",
    "Khmer OS Content",
    "Hanuman",
    "Kantumruy Pro",
    "Moul",
    "Moulpali",
    "Battambang",
    "Bayon",
    "Content",
    "Dangrek",
    "Koulen",
    "Metal",
    "Odor Mean Chey",
    "Preahvihear",
    "Siemreap",
    "Suwannaphum",
]


def _version_parts(version_text):
    """Return comparable numeric version parts from values like v1.2.3-beta."""
    numbers = re.findall(r"\d+", str(version_text or ""))
    return [int(part) for part in numbers] if numbers else [0]


def is_newer_version(latest_version, current_version):
    latest_parts = _version_parts(latest_version)
    current_parts = _version_parts(current_version)
    length = max(len(latest_parts), len(current_parts))
    latest_parts += [0] * (length - len(latest_parts))
    current_parts += [0] * (length - len(current_parts))
    return latest_parts > current_parts


def acquire_single_instance_lock() -> bool:
    """Prevent multiple app windows/processes from being opened at the same time."""
    if sys.platform != "win32":
        return True

    try:
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, APP_MUTEX_NAME)
        if not mutex:
            return True
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            return False
        globals()["_app_single_instance_mutex"] = mutex
        return True
    except Exception:
        return True

# =============================
# Application Paths
# =============================

def get_app_data_dir():
    """Get proper app data directory for cross-platform compatibility"""
    if sys.platform == 'win32':
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        app_dir = os.path.join(app_data, 'SRTDramaTool')
    else:
        app_data = os.path.expanduser('~')
        app_dir = os.path.join(app_data, '.srt_drama_tool')
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def get_config_path(filename):
    """Get proper config file path"""
    return os.path.join(get_app_data_dir(), filename)


def load_startup_app_settings() -> dict[str, Any]:
    """Load settings before MainWindow exists, for splash and startup dialogs."""
    try:
        settings_path = get_config_path("app_settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                if isinstance(settings, dict):
                    return settings
    except Exception:
        pass
    return {}


def get_startup_khmer_font() -> str:
    font_name = load_startup_app_settings().get("khmer_font", DEFAULT_KHMER_FONT)
    if not isinstance(font_name, str) or not font_name.strip():
        return DEFAULT_KHMER_FONT
    return font_name.strip()


def normalize_windows_drive_path(path: str) -> str:
    """Convert D:folder\file.exe to D:\folder\file.exe when possible."""
    if sys.platform == "win32" and re.match(r"^[A-Za-z]:[^\\/]", path):
        return f"{path[:2]}\\{path[2:]}"
    return path


def get_video_codec():
    """Return best available video codec, preferring NVIDIA NVENC if available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True
        )
        if "h264_nvenc" in result.stdout:
            return "h264_nvenc"
    except Exception:
        pass

    return "libx264"


def normalize_role_name(raw_role):
    """Normalize role text to extract specific character name and traits."""
    if not raw_role:
        return "Unknown"

    # Support format: Name (Gender, Age) inside brackets
    match = re.match(r'^(.*?)\s*\((.*?)\)', raw_role.strip())
    if match:
        name = match.group(1).strip()
        traits = match.group(2).lower()
    else:
        name = raw_role.strip()
        traits = name.lower()

    gender = "Male"
    if any(tok in traits for tok in ["female", "ស្រី", "girl", "woman"]):
        gender = "Female"

    age = "Adult"
    if any(tok in traits for tok in ["child", "kid", "baby", "ក្មេង"]):
        age = "Child"
    elif "young adult" in traits or "young" in traits:
        age = "Adult"
    elif any(tok in traits for tok in ["teen", "young", "យុវ", "youth"]):
        age = "Teen"
    elif any(tok in traits for tok in ["elder", "old", "grand", "ចាស់"]):
        age = "Elder"

    # If the name is just a generic gender term, return only the category
    if name.lower() in ["male", "female", "man", "woman", "boy", "girl", "ស្រី", "ប្រុស", "lead", "supporting"]:
        return f"{gender}, {age}"

    return f"{name} ({gender}, {age})"


def get_default_role_configs():
    return {
        "Male, Child": {
            "voice": "km-KH-PisethNeural",
            "age": "Child",
            "emotion": "Normal",
            "rate": 0,
            "tts_pitch": 20,
            "fade_in": 50,
            "fade_out": 50
        },
        "Female, Child": {
            "voice": "km-KH-SreymomNeural",
            "age": "Child",
            "emotion": "Normal",
            "rate": 0,
            "tts_pitch": 20,
            "fade_in": 50,
            "fade_out": 50
        },
        "Male, Teen": {
            "voice": "km-KH-PisethNeural",
            "age": "Teen",
            "emotion": "Normal",
            "rate": 5,
            "tts_pitch": 10,
            "fade_in": 50,
            "fade_out": 50
        },
        "Female, Teen": {
            "voice": "km-KH-SreymomNeural",
            "age": "Teen",
            "emotion": "Normal",
            "rate": 5,
            "tts_pitch": 10,
            "fade_in": 50,
            "fade_out": 50
        },
        "Male, Adult": {
            "voice": "km-KH-PisethNeural",
            "age": "Adult",
            "emotion": "Normal",
            "rate": 0,
            "tts_pitch": 0,
            "fade_in": 50,
            "fade_out": 50
        },
        "Female, Adult": {
            "voice": "km-KH-SreymomNeural",
            "age": "Adult",
            "emotion": "Normal",
            "rate": 0,
            "tts_pitch": 0,
            "fade_in": 50,
            "fade_out": 50
        },
        "Male, Elder": {
            "voice": "km-KH-PisethNeural",
            "age": "Elder",
            "emotion": "Normal",
            "rate": -10,
            "tts_pitch": -15,
            "fade_in": 50,
            "fade_out": 50
        },
        "Female, Elder": {
            "voice": "km-KH-SreymomNeural",
            "age": "Elder",
            "emotion": "Normal",
            "rate": -10,
            "tts_pitch": -15,
            "fade_in": 50,
            "fade_out": 50
        },
        "Unknown": {
            "voice": "km-KH-PisethNeural",
            "age": "Adult",
            "emotion": "Normal",
            "rate": 0,
            "tts_pitch": 0,
            "fade_in": 50,
            "fade_out": 50
        }
    }

# =============================
# License System
# =============================

# Fix Bug #5: License secret is now hashed to prevent exposure in source code
# The hash must match the one generated by LicenseGen.py
_LICENSE_SECRET_PLAIN = "DRAMA_TOOL_RVC_SECRET_KEY_2024"
LICENSE_SECRET = hashlib.sha256(_LICENSE_SECRET_PLAIN.encode()).hexdigest()

def get_machine_id():
    components = []
    # Fix Bug #15: Use PowerShell Get-CimInstance instead of deprecated wmic
    # 1. UUID (from Motherboard) - Try modern method first
    try:
        if sys.platform == 'win32':
            # Try PowerShell CIM method first (Windows 10/11)
            ps_cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_ComputerSystemProduct).UUID"'
            output = subprocess.check_output(ps_cmd, shell=True, creationflags=0x08000000).decode().strip()
            if output and len(output) > 10:
                components.append(output)
            else:
                raise ValueError("Empty UUID")
    except:
        # Fallback to old wmic method (Windows 7/8)
        try:
            if sys.platform == 'win32':
                cmd = 'wmic csproduct get uuid'
                output = subprocess.check_output(cmd, shell=True, creationflags=0x08000000).decode().split('\n')[1].strip()
                if output and len(output) > 10:
                    components.append(output)
        except:
            pass

    # 2. Disk Serial Number (C: Drive) - Helps if UUID is generic
    try:
        if sys.platform == 'win32':
            cmd = 'vol c:'
            output = subprocess.check_output(cmd, shell=True, creationflags=0x08000000).decode()
            serial = output.strip().split()[-1] # Gets format XXXX-XXXX
            components.append(serial)
    except:
        pass

    # 3. MAC Address (Network Card) - Fallback (always available)
    import uuid
    components.append(str(uuid.getnode()))

    # Combine all to create a unique hash
    raw_id = "|".join(components)
    return hashlib.md5(raw_id.encode()).hexdigest().upper()

def verify_license_key(key, machine_id):
    try:
        decoded = base64.b64decode(key).decode()
        if "::" not in decoded: return False, "Invalid Format"
        
        payload, sig = decoded.split("::")
        expected_sig = hmac.new(LICENSE_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        
        if sig != expected_sig: return False, "Invalid Signature (កូដមិនត្រឹមត្រូវ)"
        
        email, mid, exp = payload.split("|")
        
        if mid != machine_id: return False, "Machine ID Mismatch (ខុសម៉ាស៊ីន)"
        
        if exp != "LIFETIME":
            if datetime.datetime.now().timestamp() > float(exp):
                return False, "License Expired (កូដផុតកំណត់)"
        
        return True, "Valid"
    except Exception as e:
        return False, f"Error: {e}"


def load_online_license_config():
    """Load online license API settings from app data first, then bundled config."""
    default_config = {
        "enabled": False,
        "api_base_url": "",
        "app_token": "",
        "timeout_seconds": 15,
    }
    config_paths = [
        get_config_path(ONLINE_LICENSE_CONFIG_FILE),
        resource_path(ONLINE_LICENSE_CONFIG_FILE),
    ]

    for path in config_paths:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    merged = default_config.copy()
                    merged.update(data)
                    merged["api_base_url"] = str(merged.get("api_base_url", "")).rstrip("/")
                    return merged
        except Exception:
            continue

    return default_config


def online_license_is_enabled(config=None):
    config = config or load_online_license_config()
    return bool(config.get("enabled") and config.get("api_base_url"))


def _license_api_post(path, payload, config=None):
    config = config or load_online_license_config()
    base_url = str(config.get("api_base_url", "")).rstrip("/")
    if not base_url:
        return False, {"message": "License server is not configured."}

    url = f"{base_url}{path}"
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"{APP_NAME}/{APP_VERSION}",
    }
    app_token = str(config.get("app_token", "")).strip()
    if app_token:
        headers["Authorization"] = f"Bearer {app_token}"

    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    timeout = int(config.get("timeout_seconds") or 15)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
            return True, json.loads(response_body) if response_body else {}
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
            data = json.loads(error_body) if error_body else {"message": str(e)}
            if isinstance(data, dict) and isinstance(data.get("detail"), dict):
                return False, data["detail"]
            return False, data
        except Exception:
            return False, {"message": str(e)}
    except Exception as e:
        return False, {"message": str(e), "network_error": True}


def save_online_license(data):
    payload = dict(data)
    payload["last_valid_at"] = datetime.datetime.now().isoformat()
    with open(get_config_path(ONLINE_LICENSE_STORE_FILE), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_saved_online_license():
    path = get_config_path(ONLINE_LICENSE_STORE_FILE)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def activate_online_license(email, license_key, machine_id):
    config = load_online_license_config()
    if not online_license_is_enabled(config):
        return False, "Online license server is not configured.", {}

    ok, response = _license_api_post(
        "/api/v1/licenses/activate",
        {
            "email": email,
            "license_key": license_key,
            "machine_id": machine_id,
            "app_version": APP_VERSION,
        },
        config,
    )
    if ok and response.get("ok"):
        save_online_license(response)
        return True, response.get("message", "Activated"), response

    return False, response.get("message", "Online activation failed."), response


def validate_saved_online_license(machine_id):
    config = load_online_license_config()
    if not online_license_is_enabled(config):
        return False, "Online license is disabled."

    saved = load_saved_online_license()
    token = str(saved.get("token", "")).strip()
    if not token:
        return False, "No online license token found."

    ok, response = _license_api_post(
        "/api/v1/licenses/check",
        {
            "token": token,
            "machine_id": machine_id,
            "app_version": APP_VERSION,
        },
        config,
    )
    if ok and response.get("ok"):
        merged = saved.copy()
        merged.update(response)
        save_online_license(merged)
        return True, response.get("message", "Online license valid.")

    if response.get("network_error"):
        try:
            last_valid_at = saved.get("last_valid_at")
            if last_valid_at:
                last_dt = datetime.datetime.fromisoformat(last_valid_at)
                days = (datetime.datetime.now() - last_dt).days
                if days <= ONLINE_LICENSE_GRACE_DAYS:
                    return True, f"Offline grace period active ({days}/{ONLINE_LICENSE_GRACE_DAYS} days)."
        except Exception:
            pass

    return False, response.get("message", "Online license invalid.")

class LicenseDialog(QDialog):
    def __init__(self, machine_id):
        super().__init__()
        self.setWindowTitle("Register License (ចុះឈ្មោះប្រើប្រាស់)")
        self.resize(460, 430)
        self.machine_id = machine_id
        self.online_config = load_online_license_config()
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.txt_mid = QLineEdit(machine_id)
        self.txt_mid.setReadOnly(True)
        
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Enter your email...")
        
        self.txt_key = QLineEdit()
        self.txt_key.setPlaceholderText("Paste License Key here...")
        
        form.addRow("Machine ID (លេខកូដម៉ាស៊ីន):", self.txt_mid)
        form.addRow("Email (អ៊ីមែល):", self.txt_email)
        form.addRow("License Key (លេខកូដ):", self.txt_key)
        
        layout.addLayout(form)

        if online_license_is_enabled(self.online_config):
            status_text = "Online activation enabled (អាច Activate តាម Online)"
            status_color = "#198754"
        else:
            status_text = "Online activation not configured; offline key still works."
            status_color = "#b26a00"

        self.lbl_online_status = QLabel(status_text)
        self.lbl_online_status.setWordWrap(True)
        self.lbl_online_status.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        layout.addWidget(self.lbl_online_status)
        
        # --- Add Developer Info ---
        dev_group = QGroupBox("Contact for License (ទំនាក់ទំនងដើម្បីទិញ License)")
        dev_layout = QFormLayout()
        
        lbl_name = QLabel("នូរ សារ៉ាត់ (Nou Sarat)")
        lbl_name.setStyleSheet("font-weight: bold; color: #2b6cb0;")
        dev_layout.addRow("Name:", lbl_name)

        lbl_tele = QLabel('<a href="https://t.me/nousarat" style="color: #0088cc; text-decoration: none;">@nousarat</a>')
        lbl_tele.setOpenExternalLinks(True)
        dev_layout.addRow("Telegram:", lbl_tele)
        
        lbl_yt = QLabel('<a href="https://www.youtube.com/@TechFree2026">@TechFree2026</a>')
        lbl_yt.setOpenExternalLinks(True)
        dev_layout.addRow("YouTube:", lbl_yt)
        
        dev_group.setLayout(dev_layout)
        layout.addWidget(dev_group)
        
        btn_reg = QPushButton("Register (ចុះឈ្មោះ)")
        btn_reg.clicked.connect(self.register)
        btn_reg.setStyleSheet("background-color: #2b6cb0; color: white; font-weight: bold; padding: 8px;")
        layout.addWidget(btn_reg)
        
    def register(self):
        key = self.txt_key.text().strip()
        email = self.txt_email.text().strip()

        if online_license_is_enabled(self.online_config):
            if not email:
                QMessageBox.warning(self, "Missing Email", "Please enter your email before online activation.")
                return

            valid, msg, _ = activate_online_license(email, key, self.machine_id)
            if valid:
                QMessageBox.information(self, "Success", "Online activation successful!\n(Activate Online ជោគជ័យ)")
                self.accept()
                return

            fallback_valid, fallback_msg = verify_license_key(key, self.machine_id)
            if not fallback_valid:
                QMessageBox.warning(self, "Failed", f"Online activation failed:\n{msg}")
                return

            valid, msg = fallback_valid, fallback_msg
        else:
            valid, msg = verify_license_key(key, self.machine_id)
        
        if valid:
            try:
                with open(get_config_path("license.key"), "w") as f:
                    f.write(key)
                QMessageBox.information(self, "Success", "Registration Successful!\n(ចុះឈ្មោះជោគជ័យ)")
                self.accept()
            except:
                QMessageBox.warning(self, "Error", "Could not save license file.")
        else:
            QMessageBox.warning(self, "Failed", f"Registration Failed:\n{msg}")

class OverlapFixDialog(QDialog):
    def __init__(self, parent, subs):
        super().__init__(parent)
        self.main = parent
        self.subs = subs
        self.setWindowTitle("Fix Overlaps (កែសម្រួលការជាន់គ្នា)")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("The following segments overlap. Please adjust the times.\n(បន្ទាត់ខាងក្រោមមានម៉ោងជាន់គ្នា សូមកែសម្រួល)")
        lbl_info.setStyleSheet("color: #e53e3e; font-weight: bold;")
        layout.addWidget(lbl_info)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.container = QWidget()
        self.form_layout = QVBoxLayout(self.container)
        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)
        
        btn_layout = QHBoxLayout()
        
        self.btn_auto = QPushButton("⚡ Auto Fix All (ជួសជុលទាំងអស់)")
        self.btn_auto.clicked.connect(self.auto_fix_all)
        self.btn_auto.setStyleSheet("background-color: #805ad5; color: white; font-weight: bold; padding: 10px;")
        btn_layout.addWidget(self.btn_auto)

        self.btn_apply = QPushButton("✅ Re-Check & Apply")
        self.btn_apply.clicked.connect(self.apply_changes)
        self.btn_apply.setStyleSheet("background-color: #2b6cb0; color: white; font-weight: bold; padding: 10px;")
        
        self.btn_cancel = QPushButton("Close (បិទ)")
        self.btn_cancel.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
        self.inputs = []
        self.refresh_list()

    def delete_row(self, index):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Delete Row {index+1}?\n(លុបបន្ទាត់ទី {index+1}?)", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.subs.pop(index)
            self.refresh_list()

    def merge_rows(self, index1, index2):
        if index1 >= 0 and index2 < len(self.subs):
            s1 = self.subs[index1]
            s2 = self.subs[index2]

            reply = QMessageBox.question(self, "Confirm Merge",
                                         f"Are you sure you want to merge these two rows?\n(តើអ្នកពិតជាចង់បញ្ចូលបន្ទាត់ទាំងពីរនេះមែនទេ?)\n\n"
                                         f"<b>New Text:</b><br>{s1['text']} {s2['text']}",
                                         QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                # Merge text, update end time, and remove the second segment
                s1['text'] = f"{s1['text']} {s2['text']}"
                s1['end'] = s2['end']
                self.subs.pop(index2)
                self.refresh_list()

    def create_time_edit(self, ms):
        te = QLineEdit()
        te.setText(self.main.ms_to_time(ms))
        te.setPlaceholderText("HH:MM:SS,mmm")
        return te

    def refresh_list(self):
        # Clear layout
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child:
                widget = child.widget()
                if widget:
                    widget.deleteLater()
        
        self.inputs = []
        overlaps_found = False
        
        for i in range(len(self.subs) - 1):
            s1 = self.subs[i]
            s2 = self.subs[i+1]
            
            # Check for actual overlap OR too close (less than 10ms gap)
            # Fix: Only flag strict overlaps (start < previous end). Ignore touching segments.
            if s2['start'] < s1['end']:
                overlaps_found = True
                
                frame = QFrame()
                frame.setFrameShape(QFrame.StyledPanel)
                frame.setStyleSheet("background-color: #fff5f5; border: 1px solid #feb2b2; border-radius: 5px;")
                fl = QVBoxLayout(frame)
                
                fl.addWidget(QLabel(f"🔻 Conflict: Row {i+1} & {i+2}"))
                
                # Grid for inputs
                gl = QGridLayout()
                
                # Row 1
                gl.addWidget(QLabel(f"Row {i+1}:"), 0, 0)
                t1_start = self.create_time_edit(s1['start'])
                t1_start.setStyleSheet("border: 1px solid #4299e1;") # Blue (Editable)
                t1_start.setToolTip("Edit Start Time (អាចកែបាន)")
                t1_end = self.create_time_edit(s1['end'])
                t1_end.setStyleSheet("border: 2px solid red;")
                
                gl.addWidget(t1_start, 0, 1)
                gl.addWidget(QLabel("-->"), 0, 2)
                gl.addWidget(t1_end, 0, 3)
                gl.addWidget(QLabel(s1['text'][:30]+"..."), 0, 4)
                
                btn_del1 = QPushButton("🗑️")
                btn_del1.setFixedSize(24, 24)
                btn_del1.setToolTip("Delete Row (លុបបន្ទាត់)")
                btn_del1.setStyleSheet("background-color: #e53e3e; color: white; border: none; border-radius: 3px;")
                btn_del1.clicked.connect(lambda _, idx=i: self.delete_row(idx))
                gl.addWidget(btn_del1, 0, 5)

                # Row 2
                gl.addWidget(QLabel(f"Row {i+2}:"), 1, 0)
                t2_start = self.create_time_edit(s2['start'])
                t2_start.setStyleSheet("border: 2px solid red;")
                t2_end = self.create_time_edit(s2['end'])
                t2_end.setStyleSheet("border: 1px solid #4299e1;") # Blue (Editable)
                t2_end.setToolTip("Edit End Time (អាចកែបាន)")
                
                gl.addWidget(t2_start, 1, 1)
                gl.addWidget(QLabel("-->"), 1, 2)
                gl.addWidget(t2_end, 1, 3)
                gl.addWidget(QLabel(s2['text'][:30]+"..."), 1, 4)
                
                btn_del2 = QPushButton("🗑️")
                btn_del2.setFixedSize(24, 24)
                btn_del2.setToolTip("Delete Row (លុបបន្ទាត់)")
                btn_del2.setStyleSheet("background-color: #e53e3e; color: white; border: none; border-radius: 3px;")
                btn_del2.clicked.connect(lambda _, idx=i+1: self.delete_row(idx))
                gl.addWidget(btn_del2, 1, 5)

                # Add Merge Button
                btn_merge = QPushButton("🔗\nMerge")
                btn_merge.setToolTip("Merge these two rows into one (បញ្ចូលគ្នា)")
                btn_merge.setStyleSheet("background-color: #38a169; color: white; font-weight: bold;")
                btn_merge.clicked.connect(lambda _, idx1=i, idx2=i+1: self.merge_rows(idx1, idx2))
                gl.addWidget(btn_merge, 0, 6, 2, 1) # Span 2 rows

                # Row 3 (Context - Next Line) - បង្ហាញបន្ទាត់បន្ទាប់ដើម្បីមើលកុំអោយជាន់គ្នា
                if i + 2 < len(self.subs):
                    s3 = self.subs[i+2]
                    gl.addWidget(QLabel(f"Row {i+3} (Next):"), 2, 0)
                    
                    t3_start = self.create_time_edit(s3['start'])
                    t3_start.setReadOnly(True)
                    t3_start.setStyleSheet("background-color: #f0f0f0; color: #555;") # Gray color
                    
                    t3_end = self.create_time_edit(s3['end'])
                    t3_end.setReadOnly(True)
                    t3_end.setStyleSheet("background-color: #f0f0f0; color: #555;")
                    
                    gl.addWidget(t3_start, 2, 1)
                    gl.addWidget(QLabel("-->"), 2, 2)
                    gl.addWidget(t3_end, 2, 3)
                    gl.addWidget(QLabel(s3['text'][:30]+"..."), 2, 4)
                
                fl.addLayout(gl)
                self.form_layout.addWidget(frame)
                
                self.inputs.append({
                    'idx': i,
                    't1_start': t1_start, 't1_end': t1_end,
                    't2_start': t2_start, 't2_end': t2_end,
                    'orig_s1_start': s1['start'], 'orig_s1_end': s1['end'],
                    'orig_s2_start': s2['start'], 'orig_s2_end': s2['end']
                })
        
        if not overlaps_found:
            QMessageBox.information(self, "Success", "All overlaps resolved! (ការជាន់គ្នាត្រូវបានដោះស្រាយ)")
            self.accept()

    def auto_fix_all(self):
        total_fixes = 0
        # Limit loops to prevent infinite cycles (ការពារកុំអោយវិលមិនឈប់)
        for _ in range(20): 
            fixes_in_pass = 0
            for i in range(len(self.subs) - 1):
                s1 = self.subs[i]
                s2 = self.subs[i+1]
                
                # Skip if no strict overlap (Allow touching segments)
                # (រំលងប្រសិនបើវាមិនជាន់គ្នាពិតប្រាកដ - អនុញ្ញាតអោយក្បាលនិងកន្ទុយប៉ះគ្នាបាន)
                if s2['start'] >= s1['end']:
                    continue
                
                # Heuristic: If overlap is huge (> 2000ms), assume S1 end is wrong (typo), 
                # rather than shifting S2 (which would desync the video).
                # Trim S1 instead. (ប្រសិនបើជាន់គ្នាលើសពី ២ វិនាទី កាត់កន្ទុយឃ្លាមុនវិញ)
                overlap_amount = s1['end'] - s2['start']
                if overlap_amount > 2000:
                    allowed_end = s2['start'] - 50
                    # Ensure S1 keeps at least 500ms duration
                    if allowed_end > s1['start'] + 500:
                        s1['end'] = allowed_end
                        fixes_in_pass += 1
                        continue
                
                # Desired Start for Next = Current End + 50ms buffer
                required_start = s1['end'] + 50
                
                if s2['start'] < required_start:
                    # Method 1: Try moving Next Start forward
                    if required_start < s2['end']:
                        s2['start'] = required_start
                        fixes_in_pass += 1
                    # Method 2: If Next becomes invalid (Start >= End), try trimming Current End
                    else:
                        # Desired End for Current = Next Start - 50ms
                        allowed_end = s2['start'] - 50
                        
                        if allowed_end > s1['start']:
                            s1['end'] = allowed_end
                            fixes_in_pass += 1
                        # Method 3: Both are huge overlaps? Force Next Start & Push Next End
                        else:
                            s2['start'] = required_start
                            # Ensure minimum duration 500ms
                            if s2['end'] <= s2['start']:
                                s2['end'] = s2['start'] + 500
                            fixes_in_pass += 1
            
            total_fixes += fixes_in_pass
            if fixes_in_pass == 0:
                break
        
        self.refresh_list()
        QMessageBox.information(self, "Success", f"Auto-fix completed! Adjusted {total_fixes} times.\n(ជួសជុលបានជោគជ័យ ចំនួន {total_fixes} កន្លែង)")

    def apply_changes(self):
        try:
            for item in self.inputs:
                idx = item['idx']
                
                def get_ms(widget):
                    return self.main.time_to_ms(widget.text().strip())

                s1_start = get_ms(item['t1_start'])
                s1_end = get_ms(item['t1_end'])
                s2_start = get_ms(item['t2_start'])
                s2_end = get_ms(item['t2_end'])
                
                if s1_start >= s1_end: raise ValueError(f"Row {idx+1}: Start >= End")
                if s2_start >= s2_end: raise ValueError(f"Row {idx+2}: Start >= End")
                
                if s1_start != item['orig_s1_start']: self.subs[idx]['start'] = s1_start
                if s1_end != item['orig_s1_end']: self.subs[idx]['end'] = s1_end
                if s2_start != item['orig_s2_start']: self.subs[idx+1]['start'] = s2_start
                if s2_end != item['orig_s2_end']: self.subs[idx+1]['end'] = s2_end
            
            self.refresh_list()
        except Exception as e:
            QMessageBox.warning(self, "Input Error", f"Invalid time format or logic:\n{e}")

# =============================
# Main Window
# =============================

class CharacterConfigDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.edited_roles = set()
        self.setWindowTitle("TTS Configuration (ការកំណត់តួអង្គ)")
        self.resize(600, 500)
        self.v_layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Role (តួអង្គ)", "Rate (%)", "TTS Pitch (Hz)", "Status"])
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.roles = parent.roles.copy()
        self.table.setRowCount(len(self.roles))
        
        for i, role in enumerate(self.roles):
            item = QTableWidgetItem(role)
            item.setFlags(cast(Qt.ItemFlags, item.flags() & ~QT_ITEM_IS_EDITABLE)) # Make Role Name Read-only (ហាមកែឈ្មោះ)
            self.table.setItem(i, 0, item)
            
            # Rate
            sb_rate = QSpinBox()
            sb_rate.setRange(-100, 100)
            sb_rate.setSuffix("%")
            val_rate = parent.role_configs.get(role, {}).get("rate", 0)
            sb_rate.setValue(val_rate)
            self.table.setCellWidget(i, 1, sb_rate)
            sb_rate.valueChanged.connect(lambda _value, row=i, role=role: self.mark_role_edited(row, role))
            
            # Pitch
            sb_pitch = QSpinBox()
            sb_pitch.setRange(-100, 100)
            sb_pitch.setSuffix("Hz")
            val_pitch = parent.role_configs.get(role, {}).get("tts_pitch", 0)
            sb_pitch.setValue(val_pitch)
            self.table.setCellWidget(i, 2, sb_pitch)

            sb_pitch.valueChanged.connect(lambda _value, row=i, role=role: self.mark_role_edited(row, role))

            status_item = QTableWidgetItem()
            status_item.setFlags(cast(Qt.ItemFlags, status_item.flags() & ~QT_ITEM_IS_EDITABLE))
            self.table.setItem(i, 3, status_item)
            self.apply_role_highlight(i, role)
            
        self.v_layout.addWidget(self.table)
        
        btn_save = QPushButton("💾 Save All")
        btn_save.clicked.connect(self.save_config)
        self.v_layout.addWidget(btn_save)

    def apply_role_highlight(self, row: int, role: str) -> None:
        is_new = self.main_window.role_configs.get(role, {}).get("is_new", False)
        status_item = self.table.item(row, 3)
        if status_item:
            status_item.setText("NEW" if is_new else "")
            status_item.setToolTip("New character - edit Rate or Pitch to mark as configured." if is_new else "")

        bg = QColor("#fff3cd") if is_new else QColor("#ffffff")
        fg = QColor("#856404") if is_new else QColor("#1f2937")
        for col in (0, 3):
            item = self.table.item(row, col)
            if item:
                item.setBackground(bg)
                item.setForeground(fg)
                font = item.font()
                font.setBold(is_new)
                item.setFont(font)

        widget_style = (
            "background-color: #fff3cd; border: 2px solid #ffc107; font-weight: bold; color: #856404;"
            if is_new else
            ""
        )
        for col in (1, 2):
            widget = self.table.cellWidget(row, col)
            if widget:
                widget.setStyleSheet(widget_style)

    def mark_role_edited(self, row: int, role: str) -> None:
        self.edited_roles.add(role)
        if role in self.main_window.role_configs:
            self.main_window.role_configs[role]["is_new"] = False
        self.apply_role_highlight(row, role)
        
    def save_config(self):
        for i, role in enumerate(self.roles):
            w_rate = self.table.cellWidget(i, 1)
            w_pitch = self.table.cellWidget(i, 2)
            
            rate = w_rate.value() if w_rate else 0
            pitch = w_pitch.value() if w_pitch else 0
            
            if role not in self.main_window.role_configs:
                self.main_window.role_configs[role] = {}
            
            if role in self.edited_roles:
                self.main_window.role_configs[role]["is_new"] = False # Mark as configured
            self.main_window.role_configs[role]["rate"] = rate
            self.main_window.role_configs[role]["tts_pitch"] = pitch
            
        # Update the main window's list with the (potentially new) roles and save the project
        self.main_window.roles = list(self.main_window.role_configs.keys()) # Refresh roles list from updated configs
        self.main_window.save_project() # Save the project to persist role configs
        self.main_window.refresh_role_config_table()
        self.accept()

class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, url, filename, timeout=30):
        super().__init__()
        self.url = url
        self.filename = filename
        self.timeout = timeout  # Fix Bug #13: Add timeout to prevent hanging

    def run(self):
        try:
            # Fix Bug #13: Use urllib with timeout instead of urlretrieve
            import socket
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self.timeout)
            try:
                urllib.request.urlretrieve(self.url, self.filename, self.reporthook)
                self.finished_signal.emit(self.filename)
            finally:
                socket.setdefaulttimeout(old_timeout)
        except Exception as e:
            self.error_signal.emit(str(e))

    def reporthook(self, blocknum, blocksize, totalsize):
        if totalsize > 0:
            percent = int(blocknum * blocksize * 100 / totalsize)
            self.progress_signal.emit(percent)


class UpdateCheckThread(QThread):
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, api_url, current_version, timeout=20):
        super().__init__()
        self.api_url = api_url
        self.current_version = current_version
        self.timeout = timeout

    def run(self):
        try:
            request = urllib.request.Request(
                self.api_url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "SRT-Drama-Tool-Updater"
                }
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))

            latest_version = str(payload.get("tag_name") or payload.get("name") or "").strip()
            latest_version = latest_version.lstrip("vV")
            if not latest_version:
                raise ValueError("Release version was not found.")

            assets = payload.get("assets") or []
            installer_asset = None
            for asset in assets:
                name = str(asset.get("name") or "")
                url = str(asset.get("browser_download_url") or "")
                lowered = name.lower()
                if url and lowered.endswith(".exe") and any(token in lowered for token in ["setup", "installer", "install"]):
                    installer_asset = asset
                    break
            if installer_asset is None:
                for asset in assets:
                    name = str(asset.get("name") or "")
                    url = str(asset.get("browser_download_url") or "")
                    if url and name.lower().endswith(".exe"):
                        installer_asset = asset
                        break

            self.finished_signal.emit({
                "latest_version": latest_version,
                "has_update": is_newer_version(latest_version, self.current_version),
                "installer_name": str(installer_asset.get("name") or "") if installer_asset else "",
                "installer_url": str(installer_asset.get("browser_download_url") or "") if installer_asset else "",
                "release_url": str(payload.get("html_url") or DEFAULT_UPDATE_URL),
            })
        except Exception as e:
            self.error_signal.emit(str(e))


class FFmpegInstallThread(QThread):
    """Thread for running FFmpeg installer in background without blocking UI"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)  # For progress bar updates
    finished_signal = pyqtSignal(bool)  # True = success, False = failed

    def __init__(self, script_path, python_cmd):
        super().__init__()
        self.script_path = script_path
        self.python_cmd = python_cmd

    def run(self):
        import re  # For parsing percentage numbers
        last_progress = 0

        try:
            self.log_signal.emit(f"📍 Installer: {self.script_path}")
            self.log_signal.emit("✓ FFmpeg installer started")
            self.log_signal.emit("→ Reading installer output...")

            # Start installer process
            installer_process: subprocess.Popen = subprocess.Popen(
                [*self.python_cmd, self.script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            # Read installer output line by line (non-blocking for UI)
            if installer_process.stdout:
                for line in installer_process.stdout:
                    line = line.strip()
                    if line:
                        # Log each line from installer
                        self.log_signal.emit(f"   {line}")

                        # Check for final success/failure keywords. A plain checkmark can
                        # appear in intermediate steps such as creating the install folder.
                        line_lower = line.lower()
                        percentage_match = re.search(r'(\d+)%', line)
                        if percentage_match:
                            raw_percent = max(0, min(100, int(percentage_match.group(1))))
                            if "downloading:" in line_lower:
                                percent = int(raw_percent * 0.70)
                            elif "extracting:" in line_lower:
                                percent = 70 + int(raw_percent * 0.20)
                            else:
                                percent = raw_percent
                            last_progress = max(last_progress, percent)
                            self.progress_signal.emit(last_progress)

                        if "ffmpeg installed successfully" in line_lower or "installer completed successfully" in line_lower:
                            self.log_signal.emit("✅ FFmpeg installation progress: SUCCESS")
                            self.progress_signal.emit(100)
                        elif "installing ffmpeg" in line_lower:
                            last_progress = max(last_progress, 95)
                            self.progress_signal.emit(last_progress)
                        elif "failed" in line_lower or "✗" in line_lower or "error" in line_lower:
                            self.log_signal.emit(f"⚠️ FFmpeg installation issue: {line}")

            # Wait for process to complete
            installer_process.wait()

            if installer_process.returncode == 0:
                self.log_signal.emit("✅ FFmpeg installer completed successfully!")
                self.progress_signal.emit(100)
                self.finished_signal.emit(True)
            else:
                self.log_signal.emit(f"⚠️ FFmpeg installer exited with code: {installer_process.returncode}")
                self.log_signal.emit("💡 Check the log above for error details")
                self.log_signal.emit("💡 You may need to: 1) Run as Administrator, or 2) Manual install")
                self.finished_signal.emit(False)

        except PermissionError as e:
            self.log_signal.emit("✗ Permission denied - Try running as Administrator")
            self.log_signal.emit("💡 Or manually install FFmpeg (see Settings tab for instructions)")
            self.finished_signal.emit(False)
        except Exception as e:
            self.log_signal.emit(f"✗ Error: {e}")
            self.log_signal.emit("💡 Try manual installation from Settings tab")
            self.finished_signal.emit(False)

class PyTorchInstallThread(QThread):
    """Thread for running PyTorch installer in background without blocking UI"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)

    def __init__(self, script_path, python_cmd):
        super().__init__()
        self.script_path = script_path
        self.python_cmd = python_cmd

    def run(self):
        import re
        last_progress = 0

        try:
            self.log_signal.emit(f"📍 Installer: {self.script_path}")
            self.log_signal.emit("✓ PyTorch installer started")
            self.log_signal.emit("→ Reading installer output...")

            installer_process: subprocess.Popen = subprocess.Popen(
                [*self.python_cmd, self.script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            if installer_process.stdout:
                for line in installer_process.stdout:
                    line = line.strip()
                    if line:
                        self.log_signal.emit(f"   {line}")

                        percentage_match = re.search(r'(\d+)%', line)
                        if percentage_match:
                            raw_percent = max(0, min(100, int(percentage_match.group(1))))
                            percent = 5 + int(raw_percent * 0.80)
                            last_progress = max(last_progress, percent)
                            self.progress_signal.emit(last_progress)

                        line_lower = line.lower()
                        if "pytorch installation completed successfully" in line_lower:
                            self.log_signal.emit("✅ PyTorch installation progress: SUCCESS")
                            self.progress_signal.emit(100)
                        elif "verifying installation" in line_lower:
                            last_progress = max(last_progress, 95)
                            self.progress_signal.emit(last_progress)
                        elif "failed" in line_lower or "error" in line_lower:
                            self.log_signal.emit(f"⚠️ PyTorch installation issue: {line}")

            installer_process.wait()

            if installer_process.returncode == 0:
                self.log_signal.emit("✅ PyTorch installer completed successfully!")
                self.progress_signal.emit(100)
                self.finished_signal.emit(True)
            else:
                self.log_signal.emit(f"⚠️ PyTorch installer exited with code: {installer_process.returncode}")
                self.log_signal.emit("💡 Check the log above for error details")
                self.finished_signal.emit(False)

        except PermissionError as e:
            self.log_signal.emit("✗ Permission denied - Try running as Administrator")
            self.finished_signal.emit(False)
        except Exception as e:
            self.log_signal.emit(f"✗ Error: {e}")
            self.finished_signal.emit(False)

class MainWindow(QMainWindow):
    log_signal = pyqtSignal(str)
    play_audio_signal = pyqtSignal(str, int)
    progress_signal = pyqtSignal(int)
    progress_text_signal = pyqtSignal(str)  # NEW: For progress percentage text
    tts_finished_signal = pyqtSignal()
    srt_finished_signal = pyqtSignal()
    export_finished_signal = pyqtSignal()
    stop_player_signal = pyqtSignal()
    video_converted_signal = pyqtSignal(str)
    merge_finished_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} | Dev: នូរ សារ៉ាត់")
        self.resize(1100, 650)

        self.setFont(QFont(DEFAULT_KHMER_FONT, 10))
        self.setAcceptDrops(True)

        # Fix: Always initialize app_settings FIRST to prevent AttributeError
        self.app_settings = {}

        # Load App Settings (must be before apply_theme)
        self.load_app_settings()
        self.apply_app_font()

        # Initialize current_theme attribute
        self.current_theme = None

        # Apply Theme (after settings are loaded)
        self.apply_theme() # type: ignore

        # Set Window Icon (logo.ico) # type: ignore
        try:
            from PyQt5 import QtGui
            icon_path = resource_path("logo.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QtGui.QIcon(icon_path))
        except:
            pass  # Fallback: no icon if file not found

        self.current_project_path = None
        self.current_srt_path = None
        self.ffmpeg_path = None  # QLineEdit for ffmpeg path (created in settings tab)
        self.output_folder = None  # QLineEdit for output folder (created in export tab)
        # Crop spinboxes (created in export tab)
        self.sb_crop_top = None
        self.sb_crop_bottom = None # type: ignore
        self.sb_crop_left = None # type: ignore
        self.sb_crop_right = None # type: ignore
        # Initialize Role Configs
        self.role_configs = {}
        self.load_configs_from_file()
        self.ensure_default_role_configs()

        # Auto-Save Timer (Must be initialized before Settings Tab)
        self.autosave_timer = QTimer(self)
        # Fix: Ensure autosave_timer is connected only once
        try:
            self.autosave_timer.timeout.disconnect(self.auto_save_project)
        except TypeError: # If not connected, this will raise TypeError
            pass
        self.autosave_timer.timeout.connect(self.auto_save_project)

        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Use Splitter for resizable layout
        splitter = QSplitter(QT_HORIZONTAL) # type: ignore
        main_layout.addWidget(splitter)

        # Left: Video Player
        self.video_container = self.build_video_player()
        splitter.addWidget(self.video_container)

        # Right: Tabs
        self.tabs = QTabWidget() # type: ignore
        splitter.addWidget(self.tabs)

        # type: ignore
        self.tabs.addTab(self.build_home_tab(), "🏠 ទំព័រដើម (Home)")
        self.tabs.addTab(self.build_export_tab(), "📤 នាំចេញ (Export)")
        self.tabs.addTab(self.build_settings_tab(), "⚙ ការកំណត់ (Settings)")

        # Create menu bar
        self.create_menu_bar()
        # Connect log signal
        self.log_signal.connect(self.append_log)
        self.play_audio_signal.connect(self.on_play_audio)
        self.progress_signal.connect(self.progress.setValue)
        self.progress_text_signal.connect(self.update_progress_text)  # NEW: Real-time progress text
        self.tts_finished_signal.connect(self.on_tts_finished)
        self.srt_finished_signal.connect(self.on_srt_finished)
        self.export_finished_signal.connect(self.on_export_finished) # type: ignore
        self.stop_player_signal.connect(self.force_stop_player)
        self.video_converted_signal.connect(self.on_video_converted)
        self.merge_finished_signal.connect(self.on_merge_projects_finished)
        self.stop_event = threading.Event()
        self.last_generated_audio = None # ចងចាំ File អូឌីយ៉ូចុងក្រោយ

        # Initialize pygame mixer for audio playback (replaces QMediaPlayer for audio)
        # This avoids Windows 11 codec issues with QMediaPlayer
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.pygame_audio_available = True
            self.log("✅ Pygame audio system initialized successfully")
        except Exception as e:
            self.log(f"⚠️ Pygame audio initialization failed: {e}")
            self.pygame_audio_available = False
            # Fix Bug #28: Fallback to QMediaPlayer immediately if pygame fails
            self.log("🔄 Falling back to QMediaPlayer for audio preview")

        # Initialize QMediaPlayer for audio fallback (Fix: was never initialized)
        self.preview_player = QMediaPlayer()
        self.preview_player.stateChanged.connect(self.on_preview_state_changed)

        # Fix Bug #18: Track all worker threads for graceful shutdown
        self.worker_threads = []
        self.worker_threads_lock = threading.Lock()  # Thread-safe access

        self.segment_end_time = -1  # Track when to stop video playback for segment preview
        self.current_video_path = None
        
        # Initialize SRT character detection storage
        self.srt_characters = []  # List of detected characters
        self.character_info = {}  # Character -> color mapping

    def safe_emit_signal(self, signal, *args):
        """Safely emit signal only if window is not deleted (Fix: race condition)"""
        try:
            if not sip.isdeleted(self):
                signal.emit(*args) if args else signal.emit()
        except:
            pass  # Window already deleted, silently ignore

    def safe_log(self, message):
        """Safely log message from threads without crashing"""
        self.safe_emit_signal(self.log_signal, message)

    def _initialize_new_role_config(self, role_name):
        """Initialize a new unique character config based on its name/traits."""
        if role_name in self.role_configs:
            return # type: ignore

        # Extract traits from name if in "Name (Gender, Age)" format
        gender = "Male"
        age = "Adult"
        
        if "(" in role_name and ")" in role_name:
            try:
                traits = role_name.split("(")[1].split(")")[0].lower()
                if "female" in traits: gender = "Female"
                if "child" in traits: age = "Child"
                elif "teen" in traits: age = "Teen"
                elif "elder" in traits: age = "Elder"
            except:
                pass

        # Find best matching default template
        base_role = f"{gender}, {age}"
        defaults = get_default_role_configs()
        template = defaults.get(base_role, defaults["Unknown"]).copy()
        
        # Add slight variation to pitch for unique identity
        template["tts_pitch"] += random.randint(-3, 3)
        
        template["is_new"] = True # Mark as new for highlighting
        self.role_configs[role_name] = template
        self.save_configs_to_file()

    def get_app_data_dir(self):
        """Fix Bug #27: Get proper app data directory to avoid hardcoded paths"""
        return get_app_data_dir()

    def get_config_path(self, filename):
        """Get proper config file path"""
        return get_config_path(filename)

    def start_worker_thread(self, target, args=(), daemon=True):
        """Fix Bug #18: Start and track worker threads for graceful shutdown"""
        t = threading.Thread(target=target, args=args, daemon=daemon)
        with self.worker_threads_lock:
            self.worker_threads.append(t)
        t.start()
        return t

    def cleanup_finished_threads(self):
        """Remove references to finished threads"""
        with self.worker_threads_lock:
            self.worker_threads = [t for t in self.worker_threads if t.is_alive()]

    def wait_for_workers(self, timeout=5.0):
        """Wait for all worker threads to finish (used during close)"""
        with self.worker_threads_lock:
            threads = list(self.worker_threads)

        for t in threads:
            if t.is_alive():
                t.join(timeout=timeout / max(len(threads), 1))

        self.cleanup_finished_threads()

    def open_file_or_folder(self, path):
        """Cross-platform file/folder opener with existence check (Fix: bugs #3 & #4)""" # type: ignore
        if not path or not os.path.exists(path):
            self.safe_log(f"⚠️ Cannot open: path does not exist: {path}")
            return False

        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', path])
            else:  # Linux
                subprocess.Popen(['xdg-open', path])
            return True
        except Exception as e:
            self.safe_log(f"⚠️ Failed to open {path}: {e}")
            return False

    # =============================
    # Theme System
    # =============================

    THEMES = {
        "Default": {
            "name": "Default (Light)",
            "icon": "\u2600\ufe0f",
            "colors": {
                "text": "#2d3748", "window_bg": "#f0f2f5", "pane_bg": "white",
                "border": "#d9d9d9", "tab_bg": "#fafafa", "tab_text": "#595959",
                "primary": "#1890ff", "primary_hover": "#40a9ff", "primary_pressed": "#096dd9",
                "button_text": "white", "disabled_bg": "#f5f5f5", "disabled_text": "#d9d9d9",
                "input_bg": "#ffffff", "input_focus_bg": "#ffffff", "selection_bg": "#1890ff",
                "selection_text": "white", "progress_bg": "#f5f5f5", "progress_chunk": "#52c41a",
                "group_bg": "white", "group_title": "#2d3748", "table_border": "#f0f0f0",
                "table_grid": "#f0f0f0", "table_selection_bg": "#e6f7ff", "table_alt": "#fafafa",
                "header_bg": "#fafafa", "header_text": "#595959", "slider_bg": "#f5f5f5",
                "scroll_handle": "#bfbfbf", "scroll_hover": "#8c8c8c",
            },
        },
        "Black": {
            "name": "Black (Dark)",
            "icon": "\U0001f311",
            "colors": {
                "text": "#e0e0e0", "window_bg": "#1a1a1a", "pane_bg": "#2d2d2d",
                "border": "#444444", "tab_bg": "#2d2d2d", "tab_text": "#aaaaaa",
                "primary": "#4fc3f7", "primary_hover": "#29b6f6", "primary_pressed": "#039be5",
                "button_text": "#1a1a1a", "disabled_bg": "#333333", "disabled_text": "#666666",
                "input_bg": "#2d2d2d", "input_focus_bg": "#333333", "selection_bg": "#4fc3f7",
                "selection_text": "#1a1a1a", "progress_bg": "#333333", "progress_chunk": "#66bb6a",
                "group_bg": "#2d2d2d", "group_title": "#e0e0e0", "table_border": "#444444",
                "table_grid": "#333333", "table_selection_bg": "#00bcd4", "table_alt": "#252525",
                "header_bg": "#333333", "header_text": "#e0e0e0", "slider_bg": "#333333",
                "scroll_handle": "#666666", "scroll_hover": "#999999",
            },
        },
        "Purple": {
            "name": "Purple Theme",
            "icon": "\U0001f49c",
            "colors": {
                "text": "#2d3748", "window_bg": "#f3e5f5", "pane_bg": "white",
                "border": "#ce93d8", "tab_bg": "#f3e5f5", "tab_text": "#6a1b9a",
                "primary": "#8e24aa", "primary_hover": "#ab47bc", "primary_pressed": "#6a1b9a",
                "button_text": "white", "disabled_bg": "#f5f5f5", "disabled_text": "#d9d9d9",
                "input_bg": "#ffffff", "input_focus_bg": "#ffffff", "selection_bg": "#8e24aa",
                "selection_text": "white", "progress_bg": "#f3e5f5", "progress_chunk": "#ab47bc",
                "group_bg": "white", "group_title": "#6a1b9a", "table_border": "#e1bee7",
                "table_grid": "#e1bee7", "table_selection_bg": "#f3e5f5", "table_alt": "#fafafa",
                "header_bg": "#f3e5f5", "header_text": "#6a1b9a", "slider_bg": "#f3e5f5",
                "scroll_handle": "#ce93d8", "scroll_hover": "#ab47bc",
            },
        },
        "Blue": {
            "name": "Blue Ocean",
            "icon": "\U0001f499",
            "colors": {
                "text": "#1a3a52", "window_bg": "#e3f2fd", "pane_bg": "white",
                "border": "#64b5f6", "tab_bg": "#e3f2fd", "tab_text": "#1565c0",
                "primary": "#1976d2", "primary_hover": "#1e88e5", "primary_pressed": "#1565c0",
                "button_text": "white", "disabled_bg": "#f5f5f5", "disabled_text": "#d9d9d9",
                "input_bg": "#ffffff", "input_focus_bg": "#ffffff", "selection_bg": "#1976d2",
                "selection_text": "white", "progress_bg": "#e3f2fd", "progress_chunk": "#1e88e5",
                "group_bg": "white", "group_title": "#1565c0", "table_border": "#bbdefb",
                "table_grid": "#bbdefb", "table_selection_bg": "#e3f2fd", "table_alt": "#fafafa",
                "header_bg": "#e3f2fd", "header_text": "#1565c0", "slider_bg": "#e3f2fd",
                "scroll_handle": "#64b5f6", "scroll_hover": "#1e88e5",
            },
        },
        "Green": {
            "name": "Green Forest",
            "icon": "\U0001f49a",
            "colors": {
                "text": "#1b4332", "window_bg": "#e8f5e9", "pane_bg": "white",
                "border": "#81c784", "tab_bg": "#e8f5e9", "tab_text": "#2e7d32",
                "primary": "#388e3c", "primary_hover": "#43a047", "primary_pressed": "#2e7d32",
                "button_text": "white", "disabled_bg": "#f5f5f5", "disabled_text": "#d9d9d9",
                "input_bg": "#ffffff", "input_focus_bg": "#ffffff", "selection_bg": "#388e3c",
                "selection_text": "white", "progress_bg": "#e8f5e9", "progress_chunk": "#43a047",
                "group_bg": "white", "group_title": "#2e7d32", "table_border": "#c8e6c9",
                "table_grid": "#c8e6c9", "table_selection_bg": "#e8f5e9", "table_alt": "#fafafa",
                "header_bg": "#e8f5e9", "header_text": "#2e7d32", "slider_bg": "#e8f5e9",
                "scroll_handle": "#81c784", "scroll_hover": "#43a047",
            },
        },
    }

    def get_selected_khmer_font(self) -> str:
        font_name = getattr(self, 'app_settings', {}).get("khmer_font", DEFAULT_KHMER_FONT)
        if not isinstance(font_name, str) or not font_name.strip():
            return DEFAULT_KHMER_FONT
        return font_name.strip()

    def apply_app_font(self) -> None:
        font_name = self.get_selected_khmer_font()
        app = QApplication.instance()
        font = QFont(font_name, 10)
        if app and isinstance(app, QApplication):
            app.setFont(font)
        self.setFont(font)
        if hasattr(self, 'log_box') and self.log_box:
            self.apply_log_font_style()

    def apply_log_font_style(self) -> None:
        font_name = self.get_selected_khmer_font()
        self.log_box.setFont(QFont(font_name, 12)) # type: ignore
        self.log_box.setStyleSheet(f"""
            QTextEdit {{
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                font-family: {self._font_stack(font_name)};
                font-size: 12pt;
            }}
        """)

    @staticmethod
    def _font_stack(primary_font: str) -> str:
        safe_font = primary_font.replace("\\", "\\\\").replace('"', '\\"')
        fallback_fonts = [
            DEFAULT_KHMER_FONT,
            "Khmer OS",
            "Khmer OS System",
            "Segoe UI",
            "sans-serif",
        ]
        fonts = [safe_font]
        for font in fallback_fonts:
            if font != primary_font:
                fonts.append(font)
        return ", ".join(f'"{font}"' if font != "sans-serif" else font for font in fonts)

    def get_available_khmer_fonts(self) -> list[str]:
        try:
            installed = set(QFontDatabase().families())
        except Exception:
            installed = set()

        fonts: list[str] = []
        for font in KHMER_FONT_CHOICES:
            if font in installed and font not in fonts:
                fonts.append(font)

        for font in sorted(installed):
            name = font.lower()
            if any(token in name for token in ("khmer", "hanuman", "battambang", "siemreap", "moul", "bayon", "koulen", "dangrek", "suwannaphum", "preahvihear")):
                if font not in fonts:
                    fonts.append(font)

        current_font = self.get_selected_khmer_font()
        if current_font not in fonts:
            fonts.insert(0, current_font)
        if DEFAULT_KHMER_FONT not in fonts:
            fonts.append(DEFAULT_KHMER_FONT)
        return fonts

    @staticmethod
    def _build_theme_stylesheet(colors: dict[str, str], font_family: str = DEFAULT_KHMER_FONT) -> str:
        c = colors
        font_stack = MainWindow._font_stack(font_family)
        return f"""
        /* Global Font & Colors */
        QWidget {{
            font-family: {font_stack};
            font-size: 10pt;
            color: {c['text']};
        }}

        QMainWindow, QDialog {{
            background-color: {c['window_bg']};
        }}

        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {c['border']};
            background: {c['pane_bg']};
            border-radius: 8px;
            top: -1px;
        }}

        QTabBar::tab {{
            background: {c['tab_bg']};
            border: 1px solid {c['border']};
            padding: 10px 24px;
            margin-right: 4px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            color: {c['tab_text']};
            font-weight: 600;
        }}

        QTabBar::tab:selected {{
            background: {c['pane_bg']};
            border-bottom-color: {c['pane_bg']};
            color: {c['primary']};
        }}

        QTabBar::tab:hover {{
            background: {c['slider_bg']};
            color: {c['primary_hover']};
        }}

        /* Buttons */
        QPushButton {{
            background-color: {c['primary']};
            color: {c['button_text']};
            padding: 8px 20px;
            border-radius: 6px;
            border: none;
            font-weight: bold;
            font-size: 10pt;
        }}

        QPushButton:hover {{
            background-color: {c['primary_hover']};
        }}

        QPushButton:pressed {{
            background-color: {c['primary_pressed']};
        }}

        QPushButton:disabled {{
            background-color: {c['disabled_bg']};
            color: {c['disabled_text']};
            border: 1px solid {c['border']};
        }}

        /* Input Fields */
        QTextEdit, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {c['input_bg']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            padding: 8px;
            color: {c['text']};
            selection-background-color: {c['selection_bg']};
            selection-color: {c['selection_text']};
        }}

        QTextEdit:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
            border: 1px solid {c['primary_hover']};
            background-color: {c['input_focus_bg']};
        }}

        /* Combo Box */
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 30px;
            border-left-width: 0px;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
        }}

        /* Progress Bar */
        QProgressBar {{
            border: none;
            border-radius: 6px;
            text-align: center;
            background-color: {c['progress_bg']};
            color: {c['text']};
            font-weight: bold;
            height: 12px;
        }}

        QProgressBar::chunk {{
            background-color: {c['progress_chunk']};
            border-radius: 5px;
        }}

        /* Group Box */
        QGroupBox {{
            border: 1px solid {c['border']};
            border-radius: 8px;
            margin-top: 1.5em;
            background-color: {c['group_bg']};
            padding: 20px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: {c['group_title']};
            font-weight: bold;
            font-size: 11pt;
            background-color: transparent;
        }}

        /* Table Widget */
        QTableWidget {{
            border: 1px solid {c['table_border']};
            border-radius: 6px;
            gridline-color: {c['table_grid']};
            background-color: {c['group_bg']};
            selection-background-color: {c['table_selection_bg']};
            selection-color: {c['text']};
            alternate-background-color: {c['table_alt']};
        }}

        QHeaderView::section {{
            background-color: {c['header_bg']};
            padding: 10px;
            border: none;
            border-bottom: 1px solid {c['border']};
            font-weight: bold;
            color: {c['header_text']};
        }}

        /* Sliders */
        QSlider::groove:horizontal {{
            border: 1px solid {c['border']};
            height: 6px;
            background: {c['slider_bg']};
            margin: 2px 0;
            border-radius: 4px;
        }}

        QSlider::handle:horizontal {{
            background: {c['primary']};
            border: 1px solid {c['primary']};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}

        /* Scrollbars */
        QScrollBar:vertical {{
            border: none;
            background: {c['slider_bg']};
            width: 8px;
            margin: 0px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {c['scroll_handle']};
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c['scroll_hover']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        """

    def apply_theme(self, theme_name=None):
        """Apply theme to the entire application"""
        if theme_name is None:
            theme_name = getattr(self, 'app_settings', {}).get("selected_theme", "Default")

        if theme_name not in self.THEMES:
            theme_name = "Default"

        self.apply_app_font()
        font_name = self.get_selected_khmer_font()
        app = QApplication.instance()
        if app and isinstance(app, QApplication):
            app.setStyleSheet(self._build_theme_stylesheet(self.THEMES[theme_name]["colors"], font_name))

        self.current_theme = theme_name

    def apply_selected_khmer_font(self) -> None:
        """Save and apply the selected Khmer UI font."""
        if not hasattr(self, 'khmer_font_selector'):
            return

        font_name = self.khmer_font_selector.currentText().strip()
        if not font_name:
            font_name = DEFAULT_KHMER_FONT

        self.app_settings["khmer_font"] = font_name
        self.save_app_settings()
        self.apply_theme(getattr(self, 'current_theme', None))
        self.log(f"🔤 Khmer font changed to: {font_name}")

    def apply_selected_theme(self):
        """Apply the theme selected in the theme selector combo box"""
        if hasattr(self, 'theme_selector'):
            theme_key = self.theme_selector.currentData()
            if theme_key:
                self.apply_theme(theme_key)
                # Save to settings
                self.app_settings["selected_theme"] = theme_key
                self.save_app_settings()
                
                # Show confirmation
                theme_name = self.THEMES[theme_key]["name"]
                self.log(f"🎨 Theme changed to: {theme_name}")
                
                QMessageBox.information(
                    self,
                    "Theme Applied",
                    f"✅ Theme changed to: {theme_name}\n\n"
                    f"The new theme has been applied to the entire application.\n"
                    f"Your preference has been saved for next time.",
                    QMessageBox.Ok
                )

    # =============================
    # Video Player
    # =============================

    def build_video_player(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Video Widget
        self.video_scene = QGraphicsScene()
        self.video_view = QGraphicsView(self.video_scene)
        self.video_view.setMinimumSize(280, 500) # ទំហំសមាមាត្រ 9:16 (Portrait)
        self.video_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # បន្ថែមស៊ុមជុំវិញ និងធ្វើឱ្យជ្រុងមូល (Mobile Phone Look)
        self.video_view.setStyleSheet("""
            QGraphicsView {
                border: 12px solid #1a202c;
                border-radius: 25px;
                background-color: black;
            }
        """)

        self.video_item = QGraphicsVideoItem()
        self.video_scene.addItem(self.video_item)
        
        self.media_player = QMediaPlayer(None)
        self.media_player.setVideoOutput(self.video_item)
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.error.connect(self.handle_errors)
        
        # Handle Video Sizing
        self.video_item.nativeSizeChanged.connect(self.video_native_size_changed)
        
        layout.addWidget(self.video_view)
        
        # Controls
        controls = QHBoxLayout()
        controls.setContentsMargins(10, 0, 10, 0)
        
        self.play_btn = QPushButton()
        self.play_btn.setEnabled(False)
        style = self.style()
        if style:
            self.play_btn.setIcon(style.standardIcon(QSTYLE_SP_MEDIA_PLAY)) # type: ignore
        self.play_btn.clicked.connect(self.play_video)
        controls.addWidget(self.play_btn)
        
        self.position_slider = QSlider(QT_HORIZONTAL) # type: ignore
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        controls.addWidget(self.position_slider)
        
        self.lbl_duration = QLabel("00:00 / 00:00")
        controls.addWidget(self.lbl_duration)
        
        layout.addLayout(controls)
        
        # Offset Control (សម្រាប់កំណត់ម៉ោងចាប់ផ្តើមវីដេអូ)
        offset_layout = QHBoxLayout()
        offset_layout.setContentsMargins(10, 0, 10, 0)
        offset_layout.addWidget(QLabel("Video Offset (ម៉ោងចាប់ផ្តើមវីដេអូ):"))
        
        self.time_offset_edit = QLineEdit("00:00:00,000")
        self.time_offset_edit.setInputMask("99:99:99,999")
        self.time_offset_edit.setToolTip("កំណត់ម៉ោងចាប់ផ្តើមនៃវីដេអូនេះធៀបនឹងអត្ថបទដើម\n(Example: If this is Ep2 starting at 10min, enter 00:10:00,000)")
        offset_layout.addWidget(self.time_offset_edit)
        layout.addLayout(offset_layout)
        
        # Load Button
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(10, 0, 10, 10)
        btn_load = QPushButton("📂 Open Video (បើកវីដេអូ)")
        btn_load.clicked.connect(self.open_video_file)
        btn_layout.addWidget(btn_load)
        
        # Fix Playback Button
        btn_fix = QPushButton("🛠️ Fix Playback")
        btn_fix.setToolTip("Convert video to MP4 if it doesn't play.\n(បម្លែងវីដេអូប្រសិនបើវាលេងមិនកើត)")
        btn_fix.clicked.connect(self.convert_and_play_video)
        btn_layout.addWidget(btn_fix)
        
        layout.addLayout(btn_layout)
        
        return widget

    def video_native_size_changed(self, size):
        self.video_item.setSize(size)
        self.video_view.fitInView(self.video_item, Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, a0):
        self.video_view.fitInView(self.video_item, Qt.AspectRatioMode.KeepAspectRatio)
        super().resizeEvent(a0)

    def open_video_file(self):
        last_dir = getattr(self, 'app_settings', {}).get("last_video_dir", "")
        path, _ = QFileDialog.getOpenFileName(self, "Select Video", last_dir, "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.3gp *.ts *.mts *.m2ts *.vob)")
        if path:
            self.load_video(path)

    def load_video(self, path, autoplay=True):
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Error", f"Video file not found:\n{path}")
            return

        self.current_video_path = path
        if hasattr(self, "video_item"):
            self.video_item.setVisible(True)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        self.play_btn.setEnabled(True)
        if hasattr(self, 'app_settings'):
            self.app_settings["last_video_dir"] = os.path.dirname(path)
        self.save_app_settings()
        if autoplay:
            self.media_player.play()
        else:
            self.media_player.pause()

    def play_video(self):
        if self.media_player.state() == MEDIA_PLAYER_PLAYING:
            self.media_player.pause()
        else:
            self.media_player.play()
            self.segment_end_time = -1

    def media_state_changed(self, state):
        style = self.style()
        if not style:
            return
        if self.media_player.state() == MEDIA_PLAYER_PLAYING:
            self.play_btn.setIcon(style.standardIcon(QSTYLE_SP_MEDIA_PAUSE)) # type: ignore
        else:
            self.play_btn.setIcon(style.standardIcon(QSTYLE_SP_MEDIA_PLAY)) # type: ignore

    def position_changed(self, position):
        self.position_slider.setValue(position)
        self.update_duration_label(position)
        
        if self.segment_end_time != -1:
            if position >= self.segment_end_time:
                self.media_player.pause()
                self.segment_end_time = -1

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)

    def set_position(self, position):
        self.media_player.setPosition(position)

    def update_duration_label(self, current_ms):
        duration_ms = self.media_player.duration()
        def fmt(ms):
            seconds = (ms // 1000) % 60
            minutes = (ms // (1000 * 60)) % 60
            hours = (ms // (1000 * 60 * 60))
            if hours > 0: return f"{hours:02}:{minutes:02}:{seconds:02}"
            return f"{minutes:02}:{seconds:02}"
        self.lbl_duration.setText(f"{fmt(current_ms)} / {fmt(duration_ms)}")

    def handle_errors(self):
        self.play_btn.setEnabled(False)
        err_msg = self.media_player.errorString()
        if not err_msg or "0x80040266" in err_msg:
            err_msg = "DirectShow Error 0x80040266: Codec connection failed."
        self.log(f"Video Error: {err_msg}")

        # Auto-suggest conversion if codec error
        if "ServiceMissing" in err_msg or "ResourceError" in err_msg or "FormatError" in err_msg or "0x80040266" in err_msg:
            # Check if FFmpeg is available first
            ffmpeg_path = self.get_ffmpeg()
            has_ffmpeg = os.path.exists(ffmpeg_path) if ffmpeg_path != "ffmpeg" else False

            if not has_ffmpeg:
                # FFmpeg not installed - offer to install it first
                reply = QMessageBox.question(
                    self, "Playback Error - FFmpeg Required",
                    "Video format not supported or Codec missing.\n\n"
                    "To fix this, you need FFmpeg installed.\n"
                    "Would you like to install FFmpeg automatically?\n\n"
                    "(វីដេអូមិនដំណើរការ ត្រូវការ FFmpeg ដើម្បីបម្លែង។\n"
                    "តើអ្នកចង់ដំឡើង FFmpeg ដោយស្វ័យបរវត្តិ?)",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    # Switch to Settings tab and trigger FFmpeg install
                    self.tabs.setCurrentIndex(2)  # Settings tab
                    self._show_settings_page("software")  # Required Software page
                    QTimer.singleShot(500, lambda: self.install_ffmpeg_auto())
                    QMessageBox.information(
                        self, "Installing FFmpeg",
                        "FFmpeg installer will start in Settings tab.\n"
                        "Please wait for installation to complete, then try loading the video again.\n\n"
                        "(FFmpeg កំពុងដំឡើង... សូមរង់ចាំរួចសាកល្បងម្តងទៀត)",
                        QMessageBox.Ok
                    )
                else:
                    QMessageBox.warning(
                        self, "Codec Missing",
                        "Video cannot be played without codecs.\n\n"
                        "Options:\n"
                        "1. Install FFmpeg (Settings → Required Software)\n"
                        "2. Install K-Lite Codec Pack from:\n"
                        "   https://codecguide.com/download_kl.htm\n\n"
                        "(វីដេអូមិនដំណើរការ ជម្រើស:\n"
                        " ១. ដំឡើង FFmpeg នៅ Settings tab\n"
                        " ២. ដំឡើង K-Lite Codec Pack)",
                        QMessageBox.Ok
                    )
            else:
                # Check if K-Lite is already installed
                has_klite = self._check_klite_installed()
                
                extra_tip = ""
                if has_klite:
                    extra_tip = (
                        "\n\n💡 Note: K-Lite Codec Pack is detected, but the system player (Media Foundation) "
                        "is still unable to play this file. Converting to MP4 is the safest fix.\n"
                        "(រកឃើញ K-Lite ហើយ តែប្រព័ន្ធនៅតែមិនអាចលេងបាន សូមបម្លែងវាទៅ MP4)"
                    )

                # FFmpeg is available - offer to convert
                reply = QMessageBox.question(
                    self, "Playback Error",
                    f"Video format not supported or Codec missing.{extra_tip}\n\n"
                    "Do you want to convert it to a compatible format (MP4)?\n"
                    "(វីដេអូមិនដំណើរការ តើអ្នកចង់បម្លែងវាទៅជា MP4 ដែរឬទេ?)",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    self.convert_and_play_video()
                else:
                    QMessageBox.warning(
                        self, "Codec Missing",
                        "Video cannot be played.\n\n"
                        "Try installing K-Lite Codec Pack:\n"
                        "https://codecguide.com/download_kl.htm\n\n"
                        "(វីដេអូមិនដំណើរការ សូមដំឡើង K-Lite Codec Pack)",
                        QMessageBox.Ok
                    )

    def convert_and_play_video(self):
        path = self.current_video_path
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Error", "No video loaded to convert.")
            return

        ffmpeg_bin = self.get_ffmpeg()
        if not os.path.exists(ffmpeg_bin) and ffmpeg_bin != "ffmpeg":
             QMessageBox.warning(self, "Error", "FFmpeg not found. Please install it in Settings tab.")
             return
             
        self.log("⏳ Converting video... Please wait.")
        self.log("💡 Tip: Using 'baseline' profile for maximum system compatibility.")
        self.progress.setValue(10)
        
        # Output file: video_name_fixed.mp4
        output_file = os.path.splitext(path)[0] + "_fixed.mp4"
        
        self.start_worker_thread(target=self.run_proxy_conversion, args=(path, output_file, ffmpeg_bin))

    def run_proxy_conversion(self, input_path, output_path, ffmpeg_bin):
        try:
            # Using standard baseline profile and yuv420p for best compatibility with built-in Windows decoders
            cmd = [
                ffmpeg_bin, "-y", "-i", input_path,
                "-c:v", "libx264", "-preset", "ultrafast", "-profile:v", "baseline", "-level", "3.0", "-pix_fmt", "yuv420p", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-movflags", "faststart",
                output_path
            ]

            self.log("⏳ Converting video... 0%")
            self.progress_signal.emit(10)
            
            # Get total duration
            total_duration = self.get_video_duration_ms(input_path) / 1000.0
            if total_duration <= 0:
                total_duration = 1
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                       creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)

            # Real-time progress
            while True:
                line = process.stderr.readline()  # type: ignore[union-attr]
                if not line:
                    break

                line = line.strip()
                if "time=" in line:
                    time_match = re.search(r'time=(\d{2,}):(\d{2}):(\d{2})\.(\d{2})', line)
                    if time_match:
                        hours = int(time_match.group(1))
                        minutes = int(time_match.group(2))
                        seconds = int(time_match.group(3))
                        current_time = hours * 3600 + minutes * 60 + seconds + int(time_match.group(4)) / 100.0
                        progress_percent = min(95, int((current_time / total_duration) * 100))
                        if progress_percent > 0:
                            self.progress_signal.emit(10 + int(progress_percent * 0.9))  # Scale to 10-100%
                            self.progress_text_signal.emit(f"Converting: {progress_percent}%")

            process.wait()
            stderr_output = process.stderr.read()  # type: ignore[union-attr]

            if process.returncode == 0:
                self.progress_text_signal.emit("")  # Clear progress text
                self.video_converted_signal.emit(output_path)
            else:
                self.log(f"❌ Conversion Failed: {stderr_output}")
                self.progress_text_signal.emit("Failed")

        except Exception as e:
            self.log(f"❌ Error: {e}")
            self.progress_text_signal.emit("Error")

    def on_video_converted(self, new_path):
        self.log(f"✅ Video Converted: {new_path}")
        self.progress.setValue(100)
        self.load_video(new_path, autoplay=True)
        QMessageBox.information(self, "Success", "Video converted and loaded successfully!\n(បម្លែងជោគជ័យ)")

    def dragEnterEvent(self, a0):
        if a0:
            mime = a0.mimeData()
            if mime and mime.hasUrls():
                a0.accept()
            else:
                a0.ignore()

    def dropEvent(self, a0):
        if not a0: return # type: ignore
        mime = a0.mimeData()
        if not mime: return
        files = [u.toLocalFile() for u in mime.urls()]
        for f in files:
            if f.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts', '.mts', '.m2ts', '.vob')):
                self.load_video(f)
                break
            elif f.lower().endswith(('.srt', '.vtt')):
                self.open_project(f)
                break
            elif f.lower().endswith('.srt'):
                self.load_srt(f)
                break

    # =============================
    # Home Tab
    # =============================

    def build_home_tab(self):
        # Main Wrapper with Splitter
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(QT_VERTICAL) # type: ignore
        main_layout.addWidget(splitter)

        # --- Top Controls Area ---
        controls_widget = QWidget()
        layout = QVBoxLayout(controls_widget)
        layout.setContentsMargins(10, 10, 10, 5)
        layout.setSpacing(5)

        # 1. Text Input & TTS Gen (Compact)
        input_row = QHBoxLayout()
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("បញ្ចូលអត្ថបទនៅទីនេះ... (Text Input)")
        self.text_input.setMaximumHeight(45)
        input_row.addWidget(self.text_input)

        self.btn_generate = QPushButton("🔊 TTS") # type: ignore
        self.btn_generate.clicked.connect(self.generate_tts)
        self.btn_generate.setFixedWidth(80)
        self.btn_generate.setFixedHeight(45)
        input_row.addWidget(self.btn_generate)
        layout.addLayout(input_row) # type: ignore

        # 2. Settings Group (Grid Layout for compactness)
        settings_group = QGroupBox("Settings (ការកំណត់)")
        settings_layout = QGridLayout()
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(8)

        self.roles = [
            "Male, Child", "Female, Child",
            "Male, Adult", "Female, Adult",
            "Male, Elder", "Female, Elder",
            "Unknown"
            "Male, Child", "Female, Child", # type: ignore
            "Male, Adult", "Female, Adult", # type: ignore
            "Male, Elder", "Female, Elder", # type: ignore
            "Unknown" # type: ignore
        ]

        # type: ignore
        # Row 0: Role, Age, Emotion
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(self.roles)
        self.voice_combo.currentIndexChanged.connect(self.on_combo_role_changed)
        
        self.btn_tts_config = QPushButton("⚙")
        self.btn_tts_config.setFixedWidth(30)
        self.btn_tts_config.setToolTip("TTS Config")
        self.btn_tts_config.clicked.connect(self.open_tts_config)

        self.age_combo = QComboBox() # type: ignore
        self.age_combo.addItems(["Normal", "Child", "Teen", "Elder"])
        
        self.emotion_combo = QComboBox() # type: ignore
        self.emotion_combo.addItems(["Normal", "Happy", "Sad", "Angry", "Excited"])

        settings_layout.addWidget(QLabel("Role:"), 0, 0) # type: ignore
        role_box = QHBoxLayout()
        role_box.setContentsMargins(0,0,0,0)
        role_box.addWidget(self.voice_combo)
        role_box.addWidget(self.btn_tts_config)
        settings_layout.addLayout(role_box, 0, 1)
        
        # type: ignore
        settings_layout.addWidget(QLabel("Age:"), 0, 2)
        settings_layout.addWidget(self.age_combo, 0, 3)
        
        settings_layout.addWidget(QLabel("Emotion:"), 0, 4)
        settings_layout.addWidget(self.emotion_combo, 0, 5)

        # Row 1: Speed, Fade, Save
        self.speed_spin = QSpinBox() # type: ignore
        self.speed_spin.setRange(-90, 200); self.speed_spin.setSuffix("%")
        self.speed_spin.setValue(self.app_settings.get("global_speed", 0))
        
        self.fade_in = QSpinBox() # type: ignore
        self.fade_in.setRange(0, 2000); self.fade_in.setSuffix("ms")
        self.fade_in.setValue(self.app_settings.get("fade_in", 50))
        
        self.fade_out = QSpinBox() # type: ignore
        self.fade_out.setRange(0, 2000); self.fade_out.setSuffix("ms")
        self.fade_out.setValue(self.app_settings.get("fade_out", 50))
        
        btn_save_role = QPushButton("💾 Save") # type: ignore
        btn_save_role.clicked.connect(self.save_current_role_config)

        settings_layout.addWidget(QLabel("Speed:"), 1, 0) # type: ignore
        settings_layout.addWidget(self.speed_spin, 1, 1)
        
        settings_layout.addWidget(QLabel("Fade In:"), 1, 2)
        settings_layout.addWidget(self.fade_in, 1, 3)
        settings_layout.addWidget(QLabel("Fade In:"), 1, 2) # type: ignore
        settings_layout.addWidget(self.fade_in, 1, 3) # type: ignore
        
        settings_layout.addWidget(QLabel("Fade Out:"), 1, 4)
        settings_layout.addWidget(self.fade_out, 1, 5)
        
        settings_layout.addWidget(btn_save_role, 1, 6)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # 4. Operations & Manual Entry (Horizontal Layout)
        ops_layout = QHBoxLayout()
        
        # SRT Controls
        self.btn_srt = QPushButton("📂 SRT") # type: ignore
        self.btn_srt.clicked.connect(self.load_srt)
        
        self.btn_sync_srt = QPushButton("🔗 Sync SRT") # type: ignore
        self.btn_sync_srt.setToolTip("បញ្ចូល SRT ពីរ (មួយយកនាទីដើម មួយយកអត្ថបទបកប្រែ)")
        self.btn_sync_srt.clicked.connect(self.load_dual_srt)
        
        self.btn_run_srt = QPushButton("▶ Run") # type: ignore
        self.btn_run_srt.clicked.connect(self.run_srt_conversion)
        self.btn_run_srt.setEnabled(False)
        
        self.btn_stop_srt = QPushButton("⏹ Stop") # type: ignore
        self.btn_stop_srt.clicked.connect(self.stop_processing)
        self.btn_stop_srt.setEnabled(False)
        self.btn_stop_srt.setStyleSheet("background-color: #e53e3e; color: white; font-weight: bold;")
        
        self.chk_auto_fit = QCheckBox("Auto-Fit") # type: ignore
        self.chk_auto_fit.setToolTip("Adjust audio speed to fit segment duration")
        self.chk_auto_fit.setChecked(True)

        ops_layout.addWidget(self.btn_srt)
        ops_layout.addWidget(self.btn_sync_srt)
        ops_layout.addWidget(self.btn_run_srt)
        ops_layout.addWidget(self.btn_stop_srt)
        ops_layout.addWidget(self.chk_auto_fit)
        
        btn_goto_export = QPushButton("📤 Go to Export")
        # type: ignore
        btn_goto_export = QPushButton("📤 Go to Export") # type: ignore
        btn_goto_export.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        ops_layout.addWidget(btn_goto_export)
        
        # Spacer
        ops_layout.addStretch()
        
        # type: ignore
        # Manual Entry (Compact)
        self.manual_start = QLineEdit("00:00:00,000"); self.manual_start.setInputMask("99:99:99,999"); self.manual_start.setFixedWidth(85)
        self.manual_end = QLineEdit("00:00:00,000"); self.manual_end.setInputMask("99:99:99,999"); self.manual_end.setFixedWidth(85)
        self.manual_text = QLineEdit(); self.manual_text.setPlaceholderText("Text...")
        btn_add_seg = QPushButton("➕")
        btn_add_seg.clicked.connect(self.add_manual_segment)
        btn_add_seg.setFixedWidth(40)

        ops_layout.addWidget(self.manual_start)
        ops_layout.addWidget(self.manual_end)
        ops_layout.addWidget(self.manual_text)
        ops_layout.addWidget(btn_add_seg)

        # type: ignore
        layout.addLayout(ops_layout)

        # Progress Bar (Made larger for better visibility)
        self.progress = QProgressBar()
        self.progress.setFixedHeight(25)  # Increased from 8 to 25 pixels
        self.progress.setMinimumHeight(25)  # Ensure minimum height
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #a0aec0;
                border-radius: 6px;
                text-align: center;
                background-color: #edf2f7;
                font-size: 11pt;
                font-weight: bold;
                color: #2d3748;
            }
            QProgressBar::chunk {
                background-color: #4299e1;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress)
        
        # type: ignore
        # Credit Label
        lbl_credit = QLabel("Dev: នូរ សារ៉ាត់ | Tel: 096 22 11 947 | YT: @TechFree2026")
        lbl_credit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_credit.setStyleSheet("color: #718096; font-size: 9pt; margin-top: 5px;")
        layout.addWidget(lbl_credit)

        # Add Controls to Splitter (via ScrollArea for safety)
        scroll_area = QScrollArea() # type: ignore
        scroll_area.setWidget(controls_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame) # No border
        scroll_area.setMaximumHeight(380) # Limit height
        splitter.addWidget(scroll_area)

        # --- Bottom Table Area ---
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(10, 0, 10, 10) # type: ignore

        # Segment List Table
        self.segment_table = QTableWidget()
        self.segment_table.setColumnCount(6)
        self.segment_table.setHorizontalHeaderLabels(["Start", "End", "Duration", "Role", "Text", "Actions"])
        header = self.segment_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(4, QHeaderView.Stretch)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.segment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.segment_table.setAlternatingRowColors(True) # type: ignore
        table_layout.addWidget(self.segment_table)
        
        splitter.addWidget(table_container)
        splitter.setStretchFactor(0, 0) # Controls minimize
        splitter.setStretchFactor(1, 1) # Table maximizes

        return main_widget

    # =============================
    # Export Tab (Professional Sidebar Design)
    # =============================

    def _create_sidebar_button(self, icon: str, label: str) -> QPushButton:
        btn = QPushButton(f"{icon}  {label}")
        btn.setFixedHeight(40)
        btn.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ecf0f1;
                text-align: left;
                padding-left: 15px;
                border-radius: 6px;
                font-size: 10pt;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(52, 152, 219, 0.3);
            }
            QPushButton:checked {
                background-color: #3498db;
                font-weight: bold;
            }
        """)
        btn.setCheckable(True)
        return btn

    def _build_sidebar_tab(
        self,
        title: str,
        menu_items: list[tuple[str, str, str]],
        stack_attr: str,
        buttons_attr: str,
        show_handler: Callable[[str], None],
        pages: list[QWidget],
        default_key: str,
    ) -> QWidget:
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                border-right: 2px solid #1a252f;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(8)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16pt;
                font-weight: bold;
                padding: 10px;
                border-bottom: 2px solid #3498db;
                margin-bottom: 10px;
            }
        """)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(lbl_title)

        menu_buttons = {}
        for icon, key, label in menu_items:
            btn = self._create_sidebar_button(icon, label)
            btn.clicked.connect(lambda checked, k=key: show_handler(k))
            sidebar_layout.addWidget(btn)
            menu_buttons[key] = btn
        setattr(self, buttons_attr, menu_buttons)

        sidebar_layout.addStretch()

        lbl_version_bottom = QLabel(f"v{APP_VERSION}")
        lbl_version_bottom.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 9pt;
                padding: 10px;
                border-top: 1px solid #34495e;
            }
        """)
        lbl_version_bottom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(lbl_version_bottom)
        main_layout.addWidget(sidebar)

        content_area = QWidget()
        content_area.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
        """)
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)

        stack = QStackedWidget()
        stack.setStyleSheet("""
            QStackedWidget {
                background-color: white;
                border: none;
            }
        """)
        for page in pages:
            stack.addWidget(page)
        setattr(self, stack_attr, stack)

        content_layout.addWidget(stack)
        main_layout.addWidget(content_area, 1)
        show_handler(default_key)
        return main_widget

    def _show_sidebar_page(self, page_key: str, buttons: dict[str, QPushButton], stack: QStackedWidget, page_map: dict[str, int]) -> None:
        for key, btn in buttons.items():
            btn.setChecked(key == page_key)
        stack.setCurrentIndex(page_map.get(page_key, 0))

    def build_export_tab(self):
        """Build professional Export tab with sidebar menu"""
        menu_items = [
            ("📁", "output", "Output Settings"),
            ("🎬", "video", "Video Processing"),
            ("🎵", "audio", "Audio Export"),
            ("📄", "subtitles", "Subtitles"),
            ("⚡", "process", "Process & Export")
        ]
        pages = [
            self._create_output_settings_page(),
            self._create_video_processing_page(),
            self._create_audio_export_page(),
            self._create_subtitles_page(),
            self._create_process_export_page(),
        ]
        return self._build_sidebar_tab(
            "📤 EXPORT", menu_items, "export_stack", "export_menu_buttons",
            self._show_export_page, pages, "output"
        )

    def _show_export_page(self, page_key):
        """Show selected export page"""
        page_map = {
            "output": 0,
            "video": 1,
            "audio": 2,
            "subtitles": 3,
            "process": 4
        }
        self._show_sidebar_page(page_key, self.export_menu_buttons, self.export_stack, page_map)

    def _create_styled_export_group(self, title: str, layout: Union[QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout]) -> QGroupBox:
        """Create professional styled group box for export""" # type: ignore
        group = QGroupBox(title)
        group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        group.setLayout(layout)
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #2c3e50;
            }
        """)
        return group

    def _create_styled_button(self, text: str, bg_start: str, bg_end: str, hover_start: str, hover_end: str,
                              text_color: str = "white", font_size: str = "12pt", height: int = 60,
                              radius: int = 8, padding: str = "") -> QPushButton:
        """Create a styled button with gradient background and hover effect.
        
        Args:
            text: Button text
            bg_start: Background gradient start color
            bg_end: Background gradient end color
            hover_start: Hover gradient start color
            hover_end: Hover gradient end color
            text_color: Text color
            font_size: Font size
            height: Fixed button height
        """
        btn = QPushButton(text)
        btn.setFixedHeight(height)
        btn.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {bg_start}, stop:1 {bg_end});
                color: {text_color};
                font-size: {font_size};
                font-weight: bold;
                border-radius: {radius}px;
                {f"padding: {padding};" if padding else ""}
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {hover_start}, stop:1 {hover_end});
            }}
        """)
        return btn

    def _create_page_container(self, title: str, icon: str = "") -> QScrollArea:
        """Create a standard page container with scroll area, header, and layout.

        Args:
            title: Page title text
            icon: Optional icon prefix

        Returns:
            QScrollArea with widget, layout, and header already set up.
            Access layout via scroll.widget().layout()
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setObjectName("page_layout")  # Keep reference alive
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        full_title = f"{icon} {title}" if icon else title
        header = QLabel(full_title)
        header.setStyleSheet("""
            QLabel {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
                border-bottom: 3px solid #3498db;
            }
        """)
        layout.addWidget(header)

        # IMPORTANT: Set widget on scroll area
        scroll.setWidget(widget)

        # Store widget reference on scroll to prevent GC
        scroll._page_widget = widget
        scroll._page_layout = layout

        return scroll

    def _create_output_settings_page(self):
        """Create Output Settings page""" # type: ignore
        scroll = self._create_page_container("Output Settings (ការកំណត់)", "📁")
        layout = scroll._page_layout

        # Output folder
        folder_layout = QVBoxLayout() # type: ignore
        folder_group = self._create_styled_export_group("Output Folder", folder_layout)
        folder_row = QHBoxLayout()

        self.output_folder = QLineEdit(getattr(self, 'app_settings', {}).get("last_output_dir", ""))
        self.output_folder.setPlaceholderText("Select Output Folder...")
        self.output_folder.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 11pt;
                border: 2px solid #3498db;
                border-radius: 6px;
            }
        """)
        folder_row.addWidget(self.output_folder)

        btn_browse = self._create_styled_button(
            "📂 Browse", "#007bff", "#0056b3", "#0056b3", "#004085",
            font_size="11pt", height=45, radius=6, padding="0 20px"
        )
        btn_browse.clicked.connect(self.select_folder)
        folder_row.addWidget(btn_browse)

        btn_open = self._create_styled_button(
            "📂 Open Folder", "#28a745", "#1e7e34", "#1e7e34", "#155d27",
            font_size="11pt", height=45, radius=6, padding="0 20px"
        )
        btn_open.clicked.connect(self.open_output_folder)
        folder_row.addWidget(btn_open) # This line was correctly indented
        folder_layout.addLayout(folder_row)
        layout.addWidget(folder_group)

        # Quality & Options
        quality_group_layout = QVBoxLayout()
        quality_group = self._create_styled_export_group("Quality & Options", quality_group_layout)

        quality_row = QHBoxLayout()
        quality_row.addWidget(QLabel("Audio Quality:"))

        self.combo_quality = QComboBox()
        self.combo_quality.addItems(["WAV (Lossless)", "MP3 320kbps (High)", "MP3 192kbps (Medium)", "MP3 128kbps (Low)"])
        self.combo_quality.setCurrentIndex(0)
        self.combo_quality.setStyleSheet("""
                QComboBox {
                    padding: 10px;
                    font-size: 11pt;
                    border: 2px solid #3498db;
                    border-radius: 6px;
                }
            """)
        quality_row.addWidget(self.combo_quality)
        quality_row.addStretch()
        quality_group_layout.addLayout(quality_row) 

            # Options row
        opts_row = QHBoxLayout()

        self.chk_autoplay = QCheckBox("Auto-play after export")
        self.chk_autoplay.setChecked(getattr(self, 'app_settings', {}).get("auto_play", True))
        self.chk_autoplay.setFont(QFont("Segoe UI", 10))
        opts_row.addWidget(self.chk_autoplay)
        opts_row.addStretch()
        quality_group_layout.addLayout(opts_row) 

        layout.addWidget(quality_group)
        layout.addStretch()

        return scroll

    def _create_video_processing_page(self):
        """Create Video Processing page""" # type: ignore
        scroll = self._create_page_container("Video Processing (កែសម្រួលវីដេអូ)", "🎬")
        layout = scroll._page_layout

        # General settings
        gen_settings_layout = QFormLayout() # type: ignore
        general_group = self._create_styled_export_group("General Settings", gen_settings_layout)

        self.cb_codec = QComboBox()
        self.cb_codec.addItems(["H.264 (AVC) - Standard"])
        self.cb_codec.setEnabled(False)
        gen_settings_layout.addRow("Video Codec:", self.cb_codec)

        self.cb_resolution = QComboBox()
        self.cb_resolution.addItems(["Original (រក្សាដើម)", "1920x1080 (1080p)", "1280x720 (720p)", "720x480 (480p)", "3840x2160 (4K)"]) # type: ignore
        self.cb_resolution.setCurrentIndex(getattr(self, 'app_settings', {}).get("resolution_idx", 0))
        self.cb_resolution.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
        gen_settings_layout.addRow("Resolution:", self.cb_resolution)

        self.cb_preset = QComboBox()
        self.cb_preset.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower"]) # type: ignore
        self.cb_preset.setCurrentIndex(getattr(self, 'app_settings', {}).get("preset_idx", 5))
        self.cb_preset.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
        gen_settings_layout.addRow("Encoder Speed:", self.cb_preset)

        # type: ignore
        self.chk_gpu = QCheckBox("Use NVIDIA GPU (H.264 NVENC)")
        self.chk_gpu.setChecked(getattr(self, 'app_settings', {}).get("use_gpu", True))
        self.chk_gpu.setFont(QFont("Segoe UI", 10))
        gen_settings_layout.addRow("Hardware Accel:", self.chk_gpu)

        self.btn_auto_detect_gpu = QPushButton("Auto Detect GPU / CPU")
        self.btn_auto_detect_gpu.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        self.btn_auto_detect_gpu.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #2ecc71;
                        color: white;
                        padding: 8px;
                        font-size: 10pt;
                        border: 2px solid #27ae60;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #229954;
                    }
                    """
                )
        self.btn_auto_detect_gpu.clicked.connect(self._auto_detect_gpu_vs_cpu)
        gen_settings_layout.addRow("Auto Detect:", self.btn_auto_detect_gpu)  # type: ignore[union-attr]

        self.sb_crf = QSpinBox()
        self.sb_crf.setRange(0, 51)
        self.sb_crf.setValue(self.app_settings.get("crf_value", 23))
        self.sb_crf.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
        gen_settings_layout.addRow("Quality (CRF 0-51):", self.sb_crf)  # type: ignore[union-attr]

        layout.addWidget(general_group)

        # Color & Crop # type: ignore
        color_layout = QFormLayout()
        color_group = self._create_styled_export_group("Color & Crop", color_layout)

        self.cb_crop_preset = QComboBox()
        self.cb_crop_preset.addItems(["Custom", "16:9 (YouTube Landscape)", "9:16 (TikTok/Reels)", "1:1 (Square)", "4:5 (Facebook)"])
        self.cb_crop_preset.setCurrentIndex(self.app_settings.get("crop_preset_idx", 0))
        self.cb_crop_preset.currentIndexChanged.connect(self.on_crop_preset_changed)
        self.cb_crop_preset.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
        color_layout.addRow("Crop Preset:", self.cb_crop_preset)  # type: ignore[union-attr]

        self.sb_brightness = QDoubleSpinBox()
        self.sb_brightness.setRange(-1.0, 1.0)
        self.sb_brightness.setSingleStep(0.1)
        self.sb_brightness.setValue(self.app_settings.get("brightness", 0.0))
        self.sb_brightness.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
        color_layout.addRow("Brightness:", self.sb_brightness)  # type: ignore[union-attr]

        self.sb_contrast = QDoubleSpinBox()
        self.sb_contrast.setRange(-2.0, 2.0)
        self.sb_contrast.setSingleStep(0.1)
        self.sb_contrast.setValue(self.app_settings.get("contrast", 1.0))
        self.sb_contrast.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
        color_layout.addRow("Contrast:", self.sb_contrast)  # type: ignore[union-attr]

        self.sb_saturation = QDoubleSpinBox()
        self.sb_saturation.setRange(0.0, 3.0)
        self.sb_saturation.setSingleStep(0.1)
        self.sb_saturation.setValue(self.app_settings.get("saturation", 1.0))
        self.sb_saturation.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
        color_layout.addRow("Saturation:", self.sb_saturation)  # type: ignore[union-attr]

        # Crop values (will be initialized after creation in the code)
        self.sb_crop_top = None
        self.sb_crop_bottom = None
        self.sb_crop_left = None
        self.sb_crop_right = None

        layout.addWidget(color_group)
        layout.addStretch()

        return scroll

    def _create_audio_export_page(self):
        """Create Audio Export page"""
        scroll = self._create_page_container("Audio Export (នាំចេញអូឌីយ៉ូ)", "🎵") # type: ignore
        widget_layout = scroll._page_layout  # Safe reference

        # Audio options
        audio_opts_layout = QVBoxLayout()
        audio_group = self._create_styled_export_group("Audio Options", audio_opts_layout)

        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel("Original Audio Volume:"))

        # type: ignore
        self.slider_orig_vol = QSlider(QT_HORIZONTAL)  # type: ignore
        self.slider_orig_vol.setRange(0, 100)
        self.slider_orig_vol.setValue(self.app_settings.get("orig_vol", 100))
        self.slider_orig_vol.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 2px solid #2980b9;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        volume_row.addWidget(self.slider_orig_vol) # type: ignore

        self.lbl_orig_vol_value = QLabel(f"{self.slider_orig_vol.value()}%")
        self.lbl_orig_vol_value.setFixedWidth(45)
        self.lbl_orig_vol_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        volume_row.addWidget(self.lbl_orig_vol_value)

        def _on_orig_vol_change(value: int) -> None:
            self.lbl_orig_vol_value.setText(f"{value}%")
            self.app_settings["orig_vol"] = value
            self.save_app_settings()

        self.slider_orig_vol.valueChanged.connect(_on_orig_vol_change)

        audio_opts_layout.addLayout(volume_row) # type: ignore

        self.chk_remove_vocals = QCheckBox("Reduce vocals from original audio (approximate)")
        self.chk_remove_vocals.setChecked(getattr(self, 'app_settings', {}).get("remove_vocals", False))
        self.chk_remove_vocals.setFont(QFont("Segoe UI", 10))
        self.chk_remove_vocals.setToolTip("Use center-channel cancellation to reduce vocals in the original audio while preserving background effects when possible.")
        audio_opts_layout.addWidget(self.chk_remove_vocals)

        # Export buttons # type: ignore
        export_layout = QHBoxLayout()

        self.btn_export_wav = self._create_styled_button(
            "🎵 Export WAV", "#28a745", "#1e7e34", "#1e7e34", "#155d27"
        )
        self.btn_export_wav.clicked.connect(self.export_wav)
        export_layout.addWidget(self.btn_export_wav)

        audio_opts_layout.addLayout(export_layout) # type: ignore

        widget_layout.addWidget(audio_group)
        widget_layout.addStretch()

        return scroll

    def _create_subtitles_page(self):
        """Create Subtitles page""" # type: ignore
        scroll = self._create_page_container("Subtitles & Transcript (អត្ថបទ/ចំណងជើង)", "📄")
        layout = scroll._page_layout

        # Options
        sub_opts_layout = QVBoxLayout() # type: ignore
        opts_group = self._create_styled_export_group("Subtitle Options", sub_opts_layout)

        opts_layout = QHBoxLayout()
        self.chk_empty_line = QCheckBox("Empty line between cues")
        self.chk_empty_line.setChecked(True)
        self.chk_include_time = QCheckBox("Include cue timings")
        self.chk_include_time.setChecked(True)
        self.chk_include_filename = QCheckBox("Include file name")

        opts_layout.addWidget(self.chk_empty_line)
        opts_layout.addWidget(self.chk_include_time)
        opts_layout.addWidget(self.chk_include_filename)
        opts_layout.addStretch()

        # type: ignore
        sub_opts_layout.addLayout(opts_layout)
        layout.addWidget(opts_group)

        # Export buttons # type: ignore
        sub_export_layout = QHBoxLayout()
        export_group = self._create_styled_export_group("Export Subtitles", sub_export_layout)

        btn_srt = QPushButton("📄 Export SRT")
        btn_srt.setFixedHeight(60)
        btn_srt.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_srt.clicked.connect(self.export_srt_file)
        btn_srt.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
            }
        """)
        sub_export_layout.addWidget(btn_srt)

        btn_txt = QPushButton("📄 Export Plain Text")
        btn_txt.setFixedHeight(60)
        btn_txt.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_txt.clicked.connect(self.export_plain_text_file)
        btn_txt.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #545b62);
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #545b62, stop:1 #3d4246);
            }
        """)
        sub_export_layout.addWidget(btn_txt)

        layout.addWidget(export_group)
        layout.addStretch()

        return scroll

    def _create_process_export_page(self):
        """Create Process & Export page""" # type: ignore
        scroll = self._create_page_container("Process & Export (ដំណើរការ)", "⚡")
        layout = scroll._page_layout

        # Time range
        time_range_layout = QVBoxLayout() # type: ignore
        time_group = self._create_styled_export_group("Time Range (កាត់យកតាមម៉ោង)", time_range_layout)

        cut_layout = QHBoxLayout()
        self.chk_cut = QCheckBox("Enable Time Range:")
        self.chk_cut.toggled.connect(self.toggle_cut_inputs)
        cut_layout.addWidget(self.chk_cut)

        cut_layout.addWidget(QLabel("Start:"))
        self.txt_start = QLineEdit("00:00:00")
        self.txt_start.setInputMask("99:99:99")
        self.txt_start.setEnabled(False)
        self.txt_start.setStyleSheet("padding: 8px; font-size: 11pt; border: 2px solid #3498db; border-radius: 5px;")
        cut_layout.addWidget(self.txt_start)

        cut_layout.addWidget(QLabel("End:"))
        self.txt_end = QLineEdit("00:00:00")
        self.txt_end.setInputMask("99:99:99")
        self.txt_end.setEnabled(False)
        self.txt_end.setStyleSheet("padding: 8px; font-size: 11pt; border: 2px solid #3498db; border-radius: 5px;")
        cut_layout.addWidget(self.txt_end)

        cut_layout.addStretch()
        time_range_layout.addLayout(cut_layout) # type: ignore
        layout.addWidget(time_group)

        # Export buttons
        export_actions_layout = QVBoxLayout()
        export_group = self._create_styled_export_group("Export Actions", export_actions_layout)

        btn_layout = QHBoxLayout()

        btn_preview = QPushButton("👁 Preview (5s)")
        btn_preview.setFixedHeight(60)
        btn_preview.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_preview.clicked.connect(self.preview_video_effects)
        btn_preview.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffc107, stop:1 #e0a800);
                color: #333;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e0a800, stop:1 #c69500);
            }
        """)
        btn_layout.addWidget(btn_preview)

        self.btn_export_mp4 = QPushButton("🎬 Export MP4 Dub")
        self.btn_export_mp4.setFixedHeight(60)
        self.btn_export_mp4.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        self.btn_export_mp4.clicked.connect(self.export_mp4)
        self.btn_export_mp4.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc3545, stop:1 #c82333);
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c82333, stop:1 #bd2130);
            }
        """)
        btn_layout.addWidget(self.btn_export_mp4)

        export_actions_layout.addLayout(btn_layout) # type: ignore

        # Progress bar
        self.export_progress = QProgressBar()
        self.export_progress.setValue(0)
        self.export_progress.setFixedHeight(30)
        self.export_progress.setFormat("Ready")  # Initial text
        self.export_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                background-color: #f8f9fa;
                font-size: 11pt;
            }
            QProgressBar::chunk {
                background-color: #dc3545;
                border-radius: 3px;
            }
        """)
        export_actions_layout.addWidget(self.export_progress)

        layout.addWidget(export_group) # type: ignore
        layout.addStretch()

        return scroll

    # =============================
    # Settings Tab (Professional Menu Design)
    # =============================

    def build_settings_tab(self): # type: ignore
        """Build professional Settings tab with sidebar menu"""
        menu_items = [
            ("📊", "status", "System Status"),
            ("⚡", "quick", "Quick Actions"),
            ("📦", "software", "Required Software"),
            ("💾", "autosave", "Auto-Save"),
            ("⚙", "config", "Configuration"),
            ("🔐", "license", "License"),
            ("⬆", "update", "Update"),
            ("📝", "logs", "Logs"),
            ("👨‍💻", "about", "About")
        ]
        pages = [
            self._create_status_page(),
            self._create_quick_actions_page(),
            self._create_software_page(),
            self._create_autosave_page(),
            self._create_config_page(),
            self._create_license_page(),
            self._create_update_page(),
            self._create_logs_page(),
            self._create_about_page(),
        ]
        return self._build_sidebar_tab(
            "⚙ SETTINGS", menu_items, "settings_stack", "menu_buttons",
            self._show_settings_page, pages, "status"
        )

    def _show_settings_page(self, page_key):
        """Show selected settings page"""
        page_map = {
            "status": 0,
            "quick": 1,
            "software": 2,
            "autosave": 3,
            "config": 4,
            "license": 5,
            "update": 6,
            "logs": 7,
            "about": 8
        }
        self._show_sidebar_page(page_key, self.menu_buttons, self.settings_stack, page_map)

    def _create_status_page(self):
        """Create System Status page""" # type: ignore
        scroll = self._create_page_container("System Status (ស្ថានភាពប្រព័ន្ធ)", "📊")
        layout = scroll._page_layout

        # Status cards
        cards_layout = QGridLayout() # type: ignore
        cards_layout.setSpacing(15)

        # Python card
        card_python = self._create_status_card(
            "Python",
            f"✓ {platform.python_version()}",
            "#28a745",
            "🐍"
        )
        cards_layout.addWidget(card_python, 0, 0) # type: ignore

        # GPU card
        gpu_info = self._get_gpu_status()
        card_gpu = self._create_status_card(
            "GPU",
            gpu_info["text"],
            gpu_info["color"],
            "🎮"
        )
        cards_layout.addWidget(card_gpu, 0, 1) # type: ignore

        # FFmpeg card
        ffmpeg_info = self._get_ffmpeg_status()
        card_ffmpeg = self._create_status_card(
            "FFmpeg",
            ffmpeg_info["text"],
            ffmpeg_info["color"],
            "🎬"
        )
        cards_layout.addWidget(card_ffmpeg, 1, 0) # type: ignore

        # Disk card
        try:
            usage = shutil.disk_usage(".")
            free_gb = usage.free / (1024**3)
            card_disk = self._create_status_card(
                "Disk Space",
                f"✓ {free_gb:.1f} GB Free",
                "#28a745",
                "💾"
            )
        except:
            card_disk = self._create_status_card(
                "Disk Space",
                "⚠ Unknown",
                "#ffc107",
                "💾"
            )
        cards_layout.addWidget(card_disk, 1, 1) # type: ignore

        layout.addLayout(cards_layout)
        layout.addStretch()
        layout.addLayout(cards_layout) # type: ignore
        layout.addStretch() # type: ignore

        return scroll

    def _create_status_card(self, title, status, color, icon):
        """Create a status card widget"""
        card = QFrame()
        card.setMinimumHeight(120)  # Changed from setFixedHeight to allow expansion
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 white, stop:1 #f8f9fa);
                border: 2px solid {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        # Icon and title
        title_layout = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 24pt; font-weight: bold;")
        lbl_icon.setFixedWidth(40)
        title_layout.addWidget(lbl_icon)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("""
            QLabel {
                font-size: 12pt;
                color: #2c3e50;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Status
        lbl_status = QLabel(status)
        lbl_status.setStyleSheet(f"""
            QLabel {{
                font-size: 11pt;
                color: {color};
                font-weight: bold;
                padding: 8px;
                background: white;
                border-radius: 5px;
            }}
        """)
        lbl_status.setWordWrap(True)
        lbl_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl_status.setToolTip(status)
        lbl_status.setAlignment(cast(Qt.Alignment, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))
        layout.addWidget(lbl_status)

        return card

    def _create_quick_actions_page(self):
        """Create Quick Actions page""" # type: ignore
        scroll = self._create_page_container("Quick Actions (សកម្មភាពរហ័ស)", "⚡")
        layout = scroll._page_layout

        # Action buttons grid
        actions_layout = QGridLayout() # type: ignore
        actions_layout.setSpacing(15)

        # Verify Installation
        btn_verify = QPushButton("🔍 Verify Installation")
        btn_verify.setFixedHeight(60)
        btn_verify.clicked.connect(self._run_verification)
        btn_verify.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_verify.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
            }
        """)
        actions_layout.addWidget(btn_verify, 0, 0) # type: ignore

        # Test GPU
        btn_gpu = QPushButton("🎮 Test GPU")
        btn_gpu.setFixedHeight(60)
        btn_gpu.clicked.connect(self._test_gpu)
        btn_gpu.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_gpu.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #1e7e34);
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e7e34, stop:1 #155d27);
            }
        """)
        actions_layout.addWidget(btn_gpu, 0, 1) # type: ignore

        # Clear Cache
        btn_clear = QPushButton("🧹 Clear Cache & RAM")
        btn_clear.setFixedHeight(60)
        btn_clear.clicked.connect(self.clear_cache_manual)
        btn_clear.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_clear.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffc107, stop:1 #e0a800);
                color: #333;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e0a800, stop:1 #c69500);
            }
        """)
        actions_layout.addWidget(btn_clear, 1, 0) # type: ignore

        actions_layout.setColumnStretch(0, 1)
        actions_layout.setColumnStretch(1, 1)
        actions_layout.setColumnStretch(0, 1) # type: ignore
        actions_layout.setColumnStretch(1, 1) # type: ignore

        layout.addLayout(actions_layout)

        # Description
        desc = QLabel("💡 Click any button above to perform quick actions for system maintenance and testing.")
        desc.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
            }
        """)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()

        return scroll

    def _create_software_page(self):
        """Create Required Software page"""
        scroll = self._create_page_container("Required Software (កម្មវិធីចាំបាច់)", "📦")
        layout = scroll._page_layout

        # FFmpeg Section
        ffmpeg_group = QGroupBox("FFmpeg (Audio/Video Processing)") # type: ignore
        ffmpeg_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        ffmpeg_layout = QVBoxLayout()

        # Status
        self.lbl_ffmpeg_status = QLabel()
        self._update_ffmpeg_status_label()
        self.lbl_ffmpeg_status.setFont(QFont("Segoe UI", 10))
        self.lbl_ffmpeg_status.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 6px;")
        ffmpeg_layout.addWidget(self.lbl_ffmpeg_status)

        # type: ignore
        # Manual Path Input Section
        path_label = QLabel("📁 FFmpeg Path (Manual Configuration):")
        path_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        ffmpeg_layout.addWidget(path_label)

        # Path input layout
        path_input_layout = QHBoxLayout()
        self.ffmpeg_path = QLineEdit()
        self.ffmpeg_path.setPlaceholderText("e.g., E:\\ffmpeg_bin\\ffmpeg.exe or just 'ffmpeg' to use system PATH")
        self.ffmpeg_path.setText(getattr(self, 'app_settings', {}).get("ffmpeg_path", ""))
        self.ffmpeg_path.setFont(QFont("Segoe UI", 10))
        path_input_layout.addWidget(self.ffmpeg_path)

        # type: ignore
        # Browse button
        btn_browse = QPushButton("🔍 Browse")
        btn_browse.setFixedWidth(100)
        btn_browse.clicked.connect(self.select_ffmpeg)
        btn_browse.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        path_input_layout.addWidget(btn_browse)

        # Save button # type: ignore
        btn_save_path = QPushButton("💾 Save")
        btn_save_path.setFixedWidth(80)
        btn_save_path.clicked.connect(self.save_ffmpeg_path)
        btn_save_path.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_save_path.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        path_input_layout.addWidget(btn_save_path)

        ffmpeg_layout.addLayout(path_input_layout) # type: ignore

        # Install button
        btn_ffmpeg = QPushButton("⬇️ Install FFmpeg Automatically")
        btn_ffmpeg.setFixedHeight(50)
        btn_ffmpeg.clicked.connect(self.install_ffmpeg_auto)
        btn_ffmpeg.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_ffmpeg.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #17a2b8, stop:1 #138496);
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #138496, stop:1 #0f6674);
            }
        """)
        ffmpeg_layout.addWidget(btn_ffmpeg)

        # type: ignore
        # Progress
        self.dl_progress = QProgressBar()
        self.dl_progress.setVisible(False)
        self.dl_progress.setRange(0, 100)
        self.dl_progress.setFormat("%p%")
        self.dl_progress.setFixedHeight(25)
        self.dl_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background-color: #17a2b8;
                border-radius: 3px;
            }
        """)
        ffmpeg_layout.addWidget(self.dl_progress)

        ffmpeg_group.setLayout(ffmpeg_layout) # type: ignore
        layout.addWidget(ffmpeg_group)

        # PyTorch Section
        pytorch_group = QGroupBox("PyTorch (GPU Acceleration for RVC Voice Conversion)")
        pytorch_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        pytorch_layout = QVBoxLayout()

        # Description
        pytorch_desc = QLabel("Optional: Install PyTorch with GPU support for faster voice conversion using RVC. Auto-detects NVIDIA GPU.")
        pytorch_desc.setWordWrap(True)
        pytorch_desc.setStyleSheet("color: #6c757d; font-size: 9pt; padding: 5px;")
        pytorch_layout.addWidget(pytorch_desc)

        # type: ignore
        # Status
        self.lbl_pytorch_status = QLabel()
        self._update_pytorch_status_label()
        self.lbl_pytorch_status.setFont(QFont("Segoe UI", 10))
        self.lbl_pytorch_status.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 6px;")
        pytorch_layout.addWidget(self.lbl_pytorch_status)

        # Install button # type: ignore
        btn_pytorch = QPushButton("⬇️ Install PyTorch (with GPU Support)")
        btn_pytorch.setFixedHeight(50)
        btn_pytorch.clicked.connect(self.install_pytorch_auto)
        btn_pytorch.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_pytorch.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ee5a2f, stop:1 #c73d1d);
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c73d1d, stop:1 #a02d0f);
            }
        """)
        pytorch_layout.addWidget(btn_pytorch)

        # Progress # type: ignore
        self.pytorch_progress = QProgressBar()
        self.pytorch_progress.setVisible(False)
        self.pytorch_progress.setRange(0, 100)
        self.pytorch_progress.setFormat("%p%")
        self.pytorch_progress.setFixedHeight(25)
        self.pytorch_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background-color: #ee5a2f;
                border-radius: 3px;
            }
        """)
        pytorch_layout.addWidget(self.pytorch_progress)

        pytorch_group.setLayout(pytorch_layout) # type: ignore
        layout.addWidget(pytorch_group)

        # K-Lite Codec Pack Section
        klite_group = QGroupBox("K-Lite Codec Pack (System-Wide Video Codecs)")
        klite_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        klite_layout = QVBoxLayout()

        # Description
        klite_desc = QLabel("Installs system codecs to enable playback of all video formats (MKV, AVI, MOV, etc.) in this app and Windows Media Player.")
        klite_desc.setWordWrap(True)
        klite_desc.setStyleSheet("color: #6c757d; font-size: 9pt; padding: 5px;")
        klite_layout.addWidget(klite_desc)

        # type: ignore
        # Status label
        self.lbl_klite_status = QLabel("Status: Not checked")
        self._update_klite_status_label()
        self.lbl_klite_status.setFont(QFont("Segoe UI", 10))
        self.lbl_klite_status.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 6px;")
        klite_layout.addWidget(self.lbl_klite_status)

        # Install button # type: ignore
        btn_klite = QPushButton("⬇️ Download & Install K-Lite Codec Pack (Basic)")
        btn_klite.setFixedHeight(50)
        btn_klite.clicked.connect(self.install_klite_codec)
        btn_klite.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_klite.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #1e7e34);
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e7e34, stop:1 #155d27);
            }
        """)
        klite_layout.addWidget(btn_klite)

        # Progress # type: ignore
        self.klite_progress = QProgressBar()
        self.klite_progress.setVisible(False)
        self.klite_progress.setFixedHeight(25)
        self.klite_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        klite_layout.addWidget(self.klite_progress)

        klite_group.setLayout(klite_layout) # type: ignore
        layout.addWidget(klite_group)

        # VC++ Section
        vc_group = QGroupBox("VC++ Redistributable (Runtime Library)")
        vc_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        vc_layout = QVBoxLayout()

        btn_vc = QPushButton("⬇️ Install VC++ Redistributable")
        btn_vc.setFixedHeight(50)
        btn_vc.clicked.connect(self.download_vc)
        btn_vc.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_vc.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #545b62);
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #545b62, stop:1 #3d4246);
            }
        """)
        vc_layout.addWidget(btn_vc)

        vc_group.setLayout(vc_layout) # type: ignore
        layout.addWidget(vc_group)

        layout.addStretch()

        return scroll

    def _create_autosave_page(self):
        """Create Auto-Save page"""
        scroll = self._create_page_container("Auto-Save Settings (ការរក្សាទុកស្វ័យប្រវត្តិ)", "💾")
        layout = scroll._page_layout

        # Auto-Save group
        autosave_group = QGroupBox("Auto-Save Configuration") # type: ignore
        autosave_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        autosave_layout = QVBoxLayout()

        # Enable checkbox
        self.chk_autosave = QCheckBox("Enable Auto-Save")
        self.chk_autosave.setChecked(getattr(self, 'app_settings', {}).get("autosave_enabled", False))
        self.chk_autosave.stateChanged.connect(self.update_autosave_timer)
        self.chk_autosave.setFont(QFont("Segoe UI", 11))
        autosave_layout.addWidget(self.chk_autosave)

        # Interval # type: ignore
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Save Interval:"))
        
        self.sb_autosave_interval = QSpinBox()
        self.sb_autosave_interval.setRange(1, 60)
        self.sb_autosave_interval.setSuffix(" min")
        self.sb_autosave_interval.setValue(getattr(self, 'app_settings', {}).get("autosave_interval", 5))
        self.sb_autosave_interval.valueChanged.connect(self.update_autosave_timer)
        self.sb_autosave_interval.setFixedWidth(150)
        self.sb_autosave_interval.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                font-size: 11pt;
                border: 2px solid #3498db;
                border-radius: 5px;
            }
        """)
        interval_layout.addWidget(self.sb_autosave_interval)
        interval_layout.addStretch()
        autosave_layout.addLayout(interval_layout) # type: ignore

        # Description
        desc = QLabel("💡 Auto-save will automatically save your work at the specified interval to prevent data loss.")
        desc.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                padding: 15px;
                background-color: #e7f3ff;
                border-left: 4px solid #3498db;
                border-radius: 6px;
            }
        """)
        desc.setWordWrap(True)
        autosave_layout.addWidget(desc)

        autosave_group.setLayout(autosave_layout)
        # type: ignore
        autosave_group.setLayout(autosave_layout) # type: ignore
        layout.addWidget(autosave_group)

        # Start timer if enabled
        self.update_autosave_timer() # type: ignore

        layout.addStretch()

        return scroll

    def _create_config_page(self):
        """Create Configuration page"""
        scroll = self._create_page_container("Configuration Management (ការកំណត់)", "⚙️")
        layout = scroll._page_layout

        # Theme Selector Section
        theme_group = QGroupBox("🎨 Theme Selection (ជ្រើសរើស Theme)") # type: ignore
        theme_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        theme_layout = QFormLayout()

        # Theme description
        theme_desc = QLabel("Choose your preferred visual theme for the application")
        theme_desc.setWordWrap(True)
        theme_desc.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 6px;
                margin-bottom: 10px;
            }
        """)
        theme_layout.addRow(theme_desc)

        # type: ignore
        # Theme selector combo
        self.theme_selector = QComboBox()
        for theme_key in self.THEMES:
            theme_data = self.THEMES[theme_key]
            self.theme_selector.addItem(f"{theme_data['icon']}  {theme_data['name']}", theme_key)
        
        # Set current theme
        current_theme = getattr(self, 'app_settings', {}).get("selected_theme", "Default")
        for i in range(self.theme_selector.count()):
            if self.theme_selector.itemData(i) == current_theme:
                self.theme_selector.setCurrentIndex(i)
                break
        
        self.theme_selector.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 11pt;
                border: 2px solid #3498db;
                border-radius: 6px;
                font-weight: bold;
            }
            QComboBox:hover {
                border: 2px solid #2980b9;
            }
        """)
        theme_layout.addRow("Current Theme:", self.theme_selector)

        # Apply button # type: ignore
        btn_apply_theme = QPushButton("✨ Apply Theme")
        btn_apply_theme.setFixedHeight(45)
        btn_apply_theme.clicked.connect(self.apply_selected_theme)
        btn_apply_theme.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_apply_theme.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8e44ad, stop:1 #7d3c98);
            }
        """)
        theme_layout.addRow(btn_apply_theme)

        theme_group.setLayout(theme_layout) # type: ignore
        layout.addWidget(theme_group)

        # Khmer font selector
        font_group = QGroupBox("🔤 Khmer Font (ពុម្ពអក្សរខ្មែរ)") # type: ignore
        font_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        font_layout = QFormLayout()

        font_desc = QLabel("Choose the Khmer font used across the application UI")
        font_desc.setWordWrap(True)
        font_desc.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 6px;
                margin-bottom: 10px;
            }
        """)
        font_layout.addRow(font_desc)

        self.khmer_font_selector = QComboBox()
        self.khmer_font_selector.setEditable(True)
        for font_name in self.get_available_khmer_fonts():
            self.khmer_font_selector.addItem(font_name)

        current_font = self.get_selected_khmer_font()
        font_index = self.khmer_font_selector.findText(current_font)
        if font_index >= 0:
            self.khmer_font_selector.setCurrentIndex(font_index)
        else:
            self.khmer_font_selector.setEditText(current_font)

        self.khmer_font_selector.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 11pt;
                border: 2px solid #3498db;
                border-radius: 6px;
                font-weight: bold;
            }
            QComboBox:hover {
                border: 2px solid #2980b9;
            }
        """)
        font_layout.addRow("Current Font:", self.khmer_font_selector)

        font_preview = QLabel("សួស្តី! នេះជាគំរូពុម្ពអក្សរខ្មែរ")
        font_preview.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                padding: 12px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        font_layout.addRow("Preview:", font_preview)

        def _update_font_preview(font_name: str) -> None:
            font_preview.setFont(QFont(font_name.strip() or DEFAULT_KHMER_FONT, 14))

        self.khmer_font_selector.currentTextChanged.connect(_update_font_preview)
        _update_font_preview(current_font)

        btn_apply_font = QPushButton("Apply Khmer Font")
        btn_apply_font.setFixedHeight(45)
        btn_apply_font.clicked.connect(self.apply_selected_khmer_font)
        btn_apply_font.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_apply_font.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f6f9f);
            }
        """)
        font_layout.addRow(btn_apply_font)

        font_group.setLayout(font_layout) # type: ignore
        layout.addWidget(font_group)

        # Config buttons # type: ignore
        config_layout = QGridLayout()
        config_layout.setSpacing(15)

        # Export
        btn_export = QPushButton("📤 Export Configuration")
        btn_export.setFixedHeight(60)
        btn_export.clicked.connect(self._export_config)
        btn_export.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_export.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #1e7e34);
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e7e34, stop:1 #155d27);
            }
        """)
        config_layout.addWidget(btn_export, 0, 0) # type: ignore

        # Import
        btn_import = QPushButton("📥 Import Configuration")
        btn_import.setFixedHeight(60)
        btn_import.clicked.connect(self._import_config)
        btn_import.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_import.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
            }
        """)
        config_layout.addWidget(btn_import, 0, 1) # type: ignore

        # Reset
        btn_reset = QPushButton("🔄 Reset to Defaults")
        btn_reset.setFixedHeight(60)
        btn_reset.clicked.connect(self._reset_settings)
        btn_reset.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_reset.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc3545, stop:1 #c82333);
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c82333, stop:1 #bd2130);
            }
        """)
        config_layout.addWidget(btn_reset, 1, 0, 1, 2) # type: ignore

        config_layout.setColumnStretch(0, 1)
        config_layout.setColumnStretch(1, 1)
        config_layout.setColumnStretch(0, 1) # type: ignore
        config_layout.setColumnStretch(1, 1) # type: ignore

        layout.addLayout(config_layout)

        # Description
        desc = QLabel("💡 Export your settings to share with others or import settings from another installation.")
        desc.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
            }
        """)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # type: ignore
        layout.addStretch()

        return scroll

    def _create_logs_page(self):
        """Create Logs page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        header = QLabel("📝 Logs (កំណត់ហេតុ)")
        header.setStyleSheet("""
            QLabel {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
                border-bottom: 3px solid #3498db;
            }
        """)
        layout.addWidget(header)

        # Log controls
        controls_layout = QHBoxLayout() # type: ignore

        btn_clear = QPushButton("🗑️ Clear Logs")
        btn_clear.setFixedHeight(45)
        btn_clear.clicked.connect(lambda: self.log_box.clear())
        btn_clear.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #333;
                font-weight: bold;
                font-size: 10pt;
                border-radius: 6px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        controls_layout.addWidget(btn_clear) # type: ignore

        btn_save = QPushButton("💾 Save Logs")
        btn_save.setFixedHeight(45)
        btn_save.clicked.connect(self._save_logs)
        btn_save.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-weight: bold;
                font-size: 10pt;
                border-radius: 6px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        controls_layout.addWidget(btn_save) # type: ignore

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Log box
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Logs will appear here...")
        self.apply_log_font_style()
        layout.addWidget(self.log_box)

        return widget # type: ignore

    def _create_license_page(self):
        """Create license registration page."""
        scroll = self._create_page_container("License & Register (ចុះឈ្មោះ License)", "🔐")
        layout = scroll._page_layout

        license_group = QGroupBox("Register License")
        form = QFormLayout(license_group)
        form.setSpacing(14)

        machine_id = get_machine_id()
        self.license_machine_id = QLineEdit(machine_id)
        self.license_machine_id.setReadOnly(True)
        self.license_machine_id.setStyleSheet("padding: 8px; font-family: Consolas;")
        form.addRow("Machine ID:", self.license_machine_id)

        self.license_status_label = QLabel()
        self.license_status_label.setWordWrap(True)
        form.addRow("Status:", self.license_status_label)

        config = load_online_license_config()
        online_text = "Enabled" if online_license_is_enabled(config) else "Not configured"
        self.license_server_label = QLabel(f"{online_text} - {config.get('api_base_url') or 'No server URL'}")
        self.license_server_label.setWordWrap(True)
        self.license_server_label.setStyleSheet("color: #6c757d;")
        form.addRow("Online Server:", self.license_server_label)

        buttons = QHBoxLayout()
        btn_register = QPushButton("🔐 Register License")
        btn_register.setFixedHeight(45)
        btn_register.clicked.connect(self.open_license_registration)
        btn_register.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_register.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; border-radius: 6px;")
        buttons.addWidget(btn_register)

        btn_check = QPushButton("🔍 Check License")
        btn_check.setFixedHeight(45)
        btn_check.clicked.connect(self.check_license_status_clicked)
        btn_check.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_check.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; border-radius: 6px;")
        buttons.addWidget(btn_check)

        btn_copy = QPushButton("📋 Copy Machine ID")
        btn_copy.setFixedHeight(45)
        btn_copy.clicked.connect(self.copy_machine_id)
        btn_copy.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_copy.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; border-radius: 6px;")
        buttons.addWidget(btn_copy)

        btn_remove = QPushButton("🗑 Remove Saved License")
        btn_remove.setFixedHeight(45)
        btn_remove.clicked.connect(self.remove_saved_license)
        btn_remove.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn_remove.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; border-radius: 6px;")
        buttons.addWidget(btn_remove)
        form.addRow(buttons)

        layout.addWidget(license_group)

        note = QLabel(
            "Online Register ប្រើ email និង license key ពី admin panel។ "
            "បើ server មិនទាន់ configure កម្មវិធីនៅតែអាចប្រើ offline license key ចាស់បាន។"
        )
        note.setWordWrap(True)
        note.setStyleSheet("font-size: 10pt; color: #495057; padding: 15px; background-color: #e7f3ff; border-radius: 6px;")
        layout.addWidget(note)
        layout.addStretch()

        self.refresh_license_page_status()
        return scroll

    def get_license_status_text(self):
        machine_id = get_machine_id()
        online_valid, online_msg = validate_saved_online_license(machine_id)
        if online_valid:
            saved = load_saved_online_license()
            license_key = saved.get("license_key", "")
            expires_at = saved.get("expires_at") or "Lifetime"
            return True, f"Online license valid. Key: {license_key} | Expires: {expires_at}\n{online_msg}"

        license_file = get_config_path("license.key")
        if os.path.exists(license_file):
            try:
                with open(license_file, "r", encoding="utf-8") as f:
                    saved_key = f.read().strip()
                valid, msg = verify_license_key(saved_key, machine_id)
                if valid:
                    return True, "Offline license valid."
                return False, f"Saved offline license invalid: {msg}"
            except Exception as e:
                return False, f"Could not read saved offline license: {e}"

        return False, "No registered license found. Trial mode may still be active."

    def refresh_license_page_status(self):
        if not hasattr(self, "license_status_label"):
            return
        valid, text = self.get_license_status_text()
        self.license_status_label.setText(text)
        color = "#e7f6ed" if valid else "#fff4df"
        border = "#28a745" if valid else "#ffc107"
        self.license_status_label.setStyleSheet(
            f"padding: 10px; background-color: {color}; border: 1px solid {border}; "
            "border-radius: 6px; font-weight: bold;"
        )

    def open_license_registration(self):
        dlg = LicenseDialog(get_machine_id())
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_license_page_status()
            self.log("✓ License registered")

    def check_license_status_clicked(self):
        self.refresh_license_page_status()
        valid, text = self.get_license_status_text()
        if valid:
            QMessageBox.information(self, "License", text)
        else:
            QMessageBox.warning(self, "License", text)

    def copy_machine_id(self):
        QApplication.clipboard().setText(get_machine_id())
        QMessageBox.information(self, "License", "Machine ID copied.")

    def remove_saved_license(self):
        reply = QMessageBox.question(
            self,
            "Remove License",
            "Remove saved license from this computer?\n\nលុប License ដែលបានរក្សាទុកចេញពីម៉ាស៊ីននេះ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        removed = False
        for filename in ("license.key", ONLINE_LICENSE_STORE_FILE):
            path = get_config_path(filename)
            try:
                if os.path.exists(path):
                    os.remove(path)
                    removed = True
            except Exception as e:
                QMessageBox.warning(self, "License", f"Could not remove {filename}:\n{e}")
                return

        self.refresh_license_page_status()
        if removed:
            self.log("✓ Saved license removed")
            QMessageBox.information(self, "License", "Saved license removed.")
        else:
            QMessageBox.information(self, "License", "No saved license was found.")

    def _create_update_page(self):
        """Create Update page"""
        scroll = self._create_page_container("Update (ធ្វើបច្ចុប្បន្នភាព)", "⬆")
        layout = scroll._page_layout

        update_group = QGroupBox("កម្មវិធី Update")
        update_layout = QFormLayout(update_group)
        update_layout.setSpacing(12)

        lbl_current = QLabel(f"v{APP_VERSION}")
        lbl_current.setStyleSheet("font-size: 12pt; font-weight: bold; color: #28a745;")
        update_layout.addRow("Current Version:", lbl_current)

        self.update_status_label = QLabel("ចុច Check Update ដើម្បីពិនិត្យកំណែថ្មី។")
        self.update_status_label.setWordWrap(True)
        self.update_status_label.setStyleSheet("""
            QLabel {
                color: #495057;
                padding: 10px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        update_layout.addRow("Status:", self.update_status_label)

        self.update_progress = QProgressBar()
        self.update_progress.setVisible(False)
        self.update_progress.setRange(0, 100)
        self.update_progress.setFormat("%p%")
        self.update_progress.setFixedHeight(24)
        update_layout.addRow("Download:", self.update_progress)

        btn_row = QHBoxLayout()

        self.btn_check_update = QPushButton("🔍 Check Update")
        self.btn_check_update.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        self.btn_check_update.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                padding: 10px 18px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0b5ed7; }
        """)
        self.btn_check_update.clicked.connect(self.check_for_updates)
        btn_row.addWidget(self.btn_check_update)

        self.btn_install_update = QPushButton("⬇ Update")
        self.btn_install_update.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        self.btn_install_update.setEnabled(False)
        self.btn_install_update.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 18px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:disabled { background-color: #adb5bd; }
        """)
        self.btn_install_update.clicked.connect(self.download_and_install_update)
        btn_row.addWidget(self.btn_install_update)
        btn_row.addStretch()
        update_layout.addRow("Actions:", btn_row)

        layout.addWidget(update_group)

        desc = QLabel(
            "ប៊ូតុង Check Update នឹងពិនិត្យ GitHub Release ថ្មី។ "
            "បើមាន version ថ្មី ប៊ូតុង Update នឹងអាចចុចបាន ហើយកម្មវិធីនឹងទាញយក installer មកបើកដំឡើង។"
        )
        desc.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                padding: 15px;
                background-color: #e7f3ff;
                border-left: 4px solid #3498db;
                border-radius: 6px;
            }
        """)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addStretch()

        return scroll

    def _create_about_page(self):
        """Create About page"""
        scroll = self._create_page_container("About Developer (ព័ត៌មានអ្នកបង្កើត)", "👨‍💻")
        layout = scroll._page_layout

        # Developer info card
        dev_card = QFrame() # type: ignore
        dev_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 2px solid #3498db;
                border-radius: 12px;
                padding: 25px;
            }
        """)
        
        # type: ignore
        dev_layout = QFormLayout()
        dev_layout.setSpacing(15)

        lbl_name = QLabel("នូរ សារ៉ាត់ (Nou Sarat)")
        lbl_name.setStyleSheet("font-size: 13pt; font-weight: bold; color: #2b6cb0;")
        dev_layout.addRow("Name:", lbl_name)

        lbl_tele = QLabel('<a href="https://t.me/nousarat" style="color: #0088cc; text-decoration: none;">@nousarat</a>')
        lbl_tele.setOpenExternalLinks(True)
        lbl_tele.setStyleSheet("font-size: 11pt;")
        dev_layout.addRow("Telegram:", lbl_tele)

        lbl_yt = QLabel('<a href="https://www.youtube.com/@TechFree2026" style="color: #dc3545; text-decoration: none; font-weight: bold;">▶ www.youtube.com/@TechFree2026</a>')
        lbl_yt.setOpenExternalLinks(True)
        lbl_yt.setStyleSheet("font-size: 10pt;")
        dev_layout.addRow("YouTube:", lbl_yt)

        lbl_version = QLabel(f"v{APP_VERSION}")
        lbl_version.setStyleSheet("font-size: 11pt; font-weight: bold; color: #28a745;")
        dev_layout.addRow("Version:", lbl_version)

        dev_card.setLayout(dev_layout) # type: ignore
        layout.addWidget(dev_card)

        # Description
        desc = QLabel("💡 DramaTool RVC PRO - Professional voice conversion and text-to-speech tool with AI-powered features.")
        desc.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #6c757d;
                padding: 15px;
                background-color: #e7f3ff;
                border-left: 4px solid #3498db;
                border-radius: 6px;
            }
        """)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()

        # type: ignore
        return scroll

    def save_update_url(self) -> None:
        """Save the update URL used by the Update button."""
        try:
            url = self.update_url_input.text().strip() if hasattr(self, 'update_url_input') else ""
            self.app_settings["update_url"] = url
            self.save_app_settings()
            self.log("✓ Update URL saved")
            QMessageBox.information(self, "Update", "Update URL saved successfully.")
        except Exception as e:
            self.log(f"✗ Could not save update URL: {e}")
            QMessageBox.critical(self, "Update Error", f"Could not save update URL:\n{e}")

    def check_for_updates(self) -> None:
        """Check GitHub Releases for a newer installer."""
        if hasattr(self, 'update_check_thread') and self.update_check_thread.isRunning():  # type: ignore
            QMessageBox.information(self, "Update", "កំពុងពិនិត្យ update រួចហើយ...")
            return

        self.available_update = None
        if hasattr(self, 'btn_install_update'):
            self.btn_install_update.setEnabled(False)
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(False)
        if hasattr(self, 'update_status_label'):
            self.update_status_label.setText("កំពុងពិនិត្យ update...")

        self.log("🔍 Checking for updates...")
        self.update_check_thread = UpdateCheckThread(DEFAULT_UPDATE_API_URL, APP_VERSION)  # type: ignore
        self.update_check_thread.finished_signal.connect(self.on_update_check_finished)
        self.update_check_thread.error_signal.connect(self.on_update_check_error)
        self.update_check_thread.start()

    def on_update_check_finished(self, info) -> None:
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(True)

        latest_version = info.get("latest_version", "")
        if not info.get("has_update"):
            message = f"កម្មវិធីនេះជាកំណែចុងក្រោយហើយ។ Current: v{APP_VERSION}"
            if latest_version:
                message += f" | Latest: v{latest_version}"
            if hasattr(self, 'update_status_label'):
                self.update_status_label.setText(message)
            self.log(f"✓ No update available. Current v{APP_VERSION}, latest v{latest_version or APP_VERSION}")
            QMessageBox.information(self, "Update", message)
            return

        if not info.get("installer_url"):
            message = (
                f"មាន version ថ្មី v{latest_version} ប៉ុន្តែមិនឃើញ installer .exe ក្នុង GitHub Release ទេ។"
            )
            if hasattr(self, 'update_status_label'):
                self.update_status_label.setText(message)
            self.log(f"⚠️ Update v{latest_version} found, but no installer asset was found.")
            QMessageBox.warning(self, "Update", message)
            return

        self.available_update = info
        message = (
            f"មាន version ថ្មី v{latest_version}។ "
            f"ចុច Update ដើម្បីទាញយក {info.get('installer_name', 'installer')} ហើយបើកដំឡើង។"
        )
        if hasattr(self, 'update_status_label'):
            self.update_status_label.setText(message)
        if hasattr(self, 'btn_install_update'):
            self.btn_install_update.setEnabled(True)
        self.log(f"⬆ Update available: v{latest_version} ({info.get('installer_name')})")
        QMessageBox.information(self, "Update Available", message)

    def on_update_check_error(self, error) -> None:
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(True)
        if hasattr(self, 'update_status_label'):
            self.update_status_label.setText("ពិនិត្យ update មិនបាន។ សូមពិនិត្យ Internet ឬ GitHub Release។")
        self.log(f"✗ Update check failed: {error}")
        QMessageBox.warning(self, "Update Error", f"Could not check for updates:\n{error}")

    def download_and_install_update(self) -> None:
        """Download the latest installer and launch it."""
        info = getattr(self, 'available_update', None)
        if not info or not info.get("installer_url"):
            QMessageBox.information(self, "Update", "សូមចុច Check Update មុនសិន។")
            return

        if hasattr(self, 'update_download_thread') and self.update_download_thread.isRunning():  # type: ignore
            QMessageBox.information(self, "Update", "កំពុងទាញយក update រួចហើយ...")
            return

        download_dir = os.path.join(get_app_data_dir(), "updates")
        try:
            os.makedirs(download_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "Update Error", f"Could not create update folder:\n{download_dir}\n\n{e}")
            return

        filename = os.path.basename(str(info.get("installer_name") or "SRT_Drama_Tool_Setup.exe"))
        stem, ext = os.path.splitext(filename)
        if not ext:
            ext = ".exe"
        installer_path = os.path.join(download_dir, filename)
        if os.path.exists(installer_path):
            installer_path = os.path.join(download_dir, f"{stem}_{int(time.time())}{ext}")

        if hasattr(self, 'update_progress'):
            self.update_progress.setVisible(True)
            self.update_progress.setValue(0)
        if hasattr(self, 'btn_install_update'):
            self.btn_install_update.setEnabled(False)
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(False)
        if hasattr(self, 'update_status_label'):
            self.update_status_label.setText(f"កំពុងទាញយក v{info.get('latest_version')}...")

        self.update_download_thread = DownloadThread(info.get("installer_url"), installer_path, timeout=60)  # type: ignore
        self.update_download_thread.progress_signal.connect(self.update_progress.setValue)
        self.update_download_thread.finished_signal.connect(self.on_update_download_finished)
        self.update_download_thread.error_signal.connect(self.on_update_download_error)
        self.update_download_thread.start()
        self.log(f"⬇️ Downloading update installer: {os.path.basename(installer_path)}")

    def on_update_download_finished(self, filename) -> None:
        if hasattr(self, 'update_progress'):
            self.update_progress.setValue(100)
            self.update_progress.setVisible(False)
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(True)

        self.log(f"✅ Update installer downloaded: {filename}")
        if hasattr(self, 'update_status_label'):
            self.update_status_label.setText("Download រួចរាល់។ កំពុងបើក installer...")

        QMessageBox.information(
            self,
            "Update",
            "✅ Download រួចរាល់!\n\nInstaller នឹងបើកឥឡូវនេះ។ "
            "សូមបិទកម្មវិធីនេះ បើ installer ស្នើឲ្យបិទ។"
        )
        if not self.open_file_or_folder(filename):
            QMessageBox.warning(self, "Update Error", f"Could not open installer:\n{filename}")

    def on_update_download_error(self, error) -> None:
        if hasattr(self, 'update_progress'):
            self.update_progress.setVisible(False)
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(True)
        if getattr(self, 'available_update', None) and hasattr(self, 'btn_install_update'):
            self.btn_install_update.setEnabled(True)
        if hasattr(self, 'update_status_label'):
            self.update_status_label.setText("Download update មិនបាន។ សូមព្យាយាមម្ដងទៀត។")
        self.log(f"✗ Update download failed: {error}")
        QMessageBox.critical(self, "Update Error", f"Failed to download update:\n{error}")

    def open_update_page(self) -> None:
        """Open the configured update/download page in the default browser."""
        url = ""
        if hasattr(self, 'update_url_input'):
            url = self.update_url_input.text().strip()
        if not url:
            url = str(self.app_settings.get("update_url", DEFAULT_UPDATE_URL)).strip()

        if not url:
            QMessageBox.information(
                self,
                "Update",
                "No update URL is configured yet.\n\n"
                "Please paste your GitHub Releases URL, save it, then click update again."
            )
            return

        if not re.match(r"^https?://", url, re.IGNORECASE):
            url = "https://" + url

        opened = QDesktopServices.openUrl(QUrl(url))
        if opened:
            self.app_settings["update_url"] = url
            self.save_app_settings()
            self.log(f"⬆ Opened update page: {url}")
        else:
            QMessageBox.warning(self, "Update Error", f"Could not open update URL:\n{url}")

    def download_ffmpeg(self):
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        self.start_download(url, "ffmpeg_setup.zip", "ffmpeg")

    def _check_vc_installed(self):
        """Check if VC++ Redistributable is already installed"""
        try:
            # Check Windows Registry for VC++ 2015-2022
            import winreg
            
            # Check multiple possible registry paths
            paths_to_check = [
                r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
                r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
            ]
            
            for path in paths_to_check:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                    version, _ = winreg.QueryValueEx(key, "Version")
                    if version:
                        self.log(f"✅ VC++ Redistributable found: {version}")
                        winreg.CloseKey(key)
                        return True
                except WindowsError:
                    continue # type: ignore
            
            # Alternative check: Look for installed programs
            uninstall_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        if "Visual C++" in display_name and "2015-2022" in display_name:
                            self.log(f"✅ VC++ found: {display_name}")
                            winreg.CloseKey(subkey)
                            winreg.CloseKey(key)
                            return True
                        winreg.CloseKey(subkey)
                    except WindowsError:
                        continue # type: ignore
                winreg.CloseKey(key)
            except WindowsError:
                pass
            
            return False
        except Exception as e:
            self.log(f"⚠️ Could not check VC++ status: {e}")
            return False
    
    def download_vc(self): # type: ignore
        # Check if VC++ is already installed before downloading
        if self._check_vc_installed():
            reply = QMessageBox.information(
                self,
                "VC++ Already Installed",
                "✅ Microsoft Visual C++ Redistributable is already installed on your system!\n\n"
                "You don't need to install it again.\n\n"
                "If you're experiencing issues, you can:\n"
                "• Repair the installation via Control Panel\n"
                "• Continue using the application normally\n\n"
                "សូមអរគុណ! កម្មវិធី VC++ ត្រូវបានដំឡើងរួចហើយ។",
                QMessageBox.Ok | QMessageBox.Ignore
            )
            if reply == QMessageBox.Ignore:
                # Still allow manual installation if user wants
                url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
                self.start_download(url, "vc_redist.exe", "vc")
        else:
            url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
            self.start_download(url, "vc_redist.exe", "vc")

    def start_download(self, url, filename, task_type):
        if hasattr(self, 'dl_thread') and self.dl_thread.isRunning(): # type: ignore
            QMessageBox.warning(self, "Busy", "Download in progress...")
            return
        
        self.dl_progress.setVisible(True)
        self.dl_progress.setValue(0)
        self.current_dl_task = task_type
        
        self.dl_thread = DownloadThread(url, filename) # type: ignore
        self.dl_thread.progress_signal.connect(self.dl_progress.setValue)
        self.dl_thread.finished_signal.connect(self.on_download_finished)
        self.dl_thread.error_signal.connect(self.on_download_error)
        self.dl_thread.start()
        self.log(f"⬇️ Starting download: {filename}...")

    def on_download_finished(self, filename):
        self.dl_progress.setVisible(False)
        self.log(f"✅ Download finished: {filename}") # type: ignore
        
        if self.current_dl_task == "ffmpeg":
            try:
                self.log("📦 Extracting FFmpeg...")
                with zipfile.ZipFile(filename, 'r') as zip_ref:
                    zip_ref.extractall("ffmpeg_temp")
                
                # Find ffmpeg.exe and ffprobe.exe in extracted folder
                ffmpeg_exe = None
                ffprobe_exe = None
                for root, dirs, files in os.walk("ffmpeg_temp"):
                    if "ffmpeg.exe" in files:
                        ffmpeg_exe = os.path.join(root, "ffmpeg.exe")
                    if "ffprobe.exe" in files:
                        ffprobe_exe = os.path.join(root, "ffprobe.exe")
                
                if ffmpeg_exe:
                    # Move to a permanent location
                    dest_dir = "ffmpeg_bin"
                    if not os.path.exists(dest_dir): os.makedirs(dest_dir)
                    final_path = os.path.join(dest_dir, "ffmpeg.exe")
                    
                    # Copy/Move
                    shutil.copy2(ffmpeg_exe, final_path)
                    
                    # Copy ffprobe if found (Important for Pydub)
                    if ffprobe_exe:
                        final_ffprobe_path = os.path.join(dest_dir, "ffprobe.exe")
                        shutil.copy2(ffprobe_exe, final_ffprobe_path)
                    else:
                        final_ffprobe_path = ""
                    
                    # Update Settings
                    if self.ffmpeg_path is not None:
                        self.ffmpeg_path.setText(os.path.abspath(final_path))
                    self.app_settings["ffmpeg_path"] = os.path.abspath(final_path) # type: ignore
                    if final_ffprobe_path:
                        self.app_settings["ffprobe_path"] = os.path.abspath(final_ffprobe_path) # type: ignore
                    else:
                        self.log("⚠️ ffprobe.exe was not found in the downloaded archive.")
                    self.save_app_settings()
                    
                    QMessageBox.information(self, "Success", "FFmpeg installed successfully!\n(ដំឡើងជោគជ័យ)")
                    # Cleanup
                    shutil.rmtree("ffmpeg_temp", ignore_errors=True)
                    os.remove(filename)
                else:
                    QMessageBox.warning(self, "Error", "Could not find ffmpeg.exe in zip.")
            except Exception as e: # type: ignore
                QMessageBox.warning(self, "Error", f"Failed to install FFmpeg: {e}")

        elif self.current_dl_task == "vc":
            self.log("🚀 Launching VC++ Installer...")

            # Check if VC++ is already installed
            is_installed = self._check_vc_installed()
            if is_installed:
                reply = QMessageBox.information(
                    self,
                    "VC++ Already Installed",
                    "✅ Microsoft Visual C++ Redistributable is already installed on your system!\n\n" \
                    "You don't need to install it again.\n\n" \
                    "If you're experiencing issues, you can:\n" \
                    "• Repair the installation via Control Panel\n" \
                    "• Continue using the application normally\n\n" \
                    "សូមអរគុណ! កម្មវិធី VC++ ត្រូវបានដំឡើងរួចហើយ។",
                    QMessageBox.Ok | QMessageBox.Ignore
                )
                if reply == QMessageBox.Ignore:
                    self.open_file_or_folder(filename) # type: ignore
            else:
                self.open_file_or_folder(filename)

    def on_download_error(self, err):
        self.dl_progress.setVisible(False) # type: ignore
        QMessageBox.critical(self, "Download Error", f"Failed to download:\n{err}")

    def on_klite_download_error(self, err):
        self.klite_progress.setVisible(False) # type: ignore
        QMessageBox.critical(self, "Download Error", f"Failed to download K-Lite Codec Pack:\n{err}")

    # =============================
    # K-Lite Codec Pack Installation
    # =============================

    def _update_klite_status_label(self) -> None:
        """Update K-Lite Codec Pack status label"""
        if hasattr(self, 'lbl_klite_status'):
            is_installed = self._check_klite_installed()
            if is_installed:
                self.lbl_klite_status.setText("✓ K-Lite Codec Pack Detected")
                self.lbl_klite_status.setStyleSheet("color: #28a745; font-weight: bold; padding: 10px; background-color: #f8f9fa; border-radius: 6px;")
            else:
                self.lbl_klite_status.setText("⚠ Not Installed")
                self.lbl_klite_status.setStyleSheet("color: #ffc107; font-weight: bold; padding: 10px; background-color: #f8f9fa; border-radius: 6px;")

    def refresh_all_statuses(self) -> None:
        """Refresh all software and hardware status labels"""
        self._update_ffmpeg_status_label()
        self._update_pytorch_status_label()
        self._update_klite_status_label()
        self.log("🔄 System statuses refreshed.")

    def _check_klite_installed(self):
        """Check if K-Lite Codec Pack is installed (Improved Detection)"""
        try:
            import winreg

            # Check registry for K-Lite Codec Pack in both HKLM and HKCU
            keys_to_check = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\K-Lite Codec Pack_is1"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\K-Lite Codec Pack_is1"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\K-Lite Codec Pack_is1"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\KLCodecPack"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\KLCodecPack"),
            ]

            for hkey, path in keys_to_check:
                try:
                    key = winreg.OpenKey(hkey, path)
                    winreg.CloseKey(key)
                    return True # Key exists, meaning it's installed
                except WindowsError: # type: ignore
                    continue

            # Alternative: Check if core LAV filters exist in system directories
            sys_roots = [
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32"),
                os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "SysWOW64")
            ]
            klite_files = ["lavvideo.ax", "lavsplitter.ax", "lavaudio.ax"]

            for root in sys_roots:
                if os.path.exists(root):
                    for file in klite_files:
                        if os.path.exists(os.path.join(root, file)):
                            return True

            return False
        except Exception:
            return False
    
    def install_klite_codec(self):
        """Download and install K-Lite Codec Pack Basic"""
        # Check if already installed
        if self._check_klite_installed():
            reply = QMessageBox.information(
                self,
                "K-Lite Already Installed",
                "✅ K-Lite Codec Pack is already detected on your system!\n\n" \
                "You don't need to install it again.\n\n" \
                "If you're still experiencing video issues, you can:\n" \
                "• Repair the installation via Control Panel\n" \
                "• Try reinstalling to latest version\n\n" \
                "សូមអរគុណ! K-Lite Codec Pack ត្រូវបានដំឡើងរួចហើយ។",
                QMessageBox.Ok | QMessageBox.Ignore
            )
            if reply == QMessageBox.Ignore:
                # Still allow manual reinstall if user wants
                self._download_klite()
        else:
            self._download_klite()

    def _download_klite(self):
        """Download K-Lite Codec Pack Basic"""
        self.log("⬇️ Starting K-Lite Codec Pack download...")
        self.klite_progress.setVisible(True)
        self.klite_progress.setValue(0)

        try:
            # K-Lite Codec Pack Basic download URL
            url = "https://files3.codecguide.com/K-Lite_Codec_Pack_1970_Basic.exe"
            filename = "klite_codec_basic.exe"

            # Check if already downloading
            if hasattr(self, 'klite_thread') and self.klite_thread.isRunning(): # type: ignore
                self.log("⚠️ K-Lite download is already in progress...")
                return

            # Start download in background thread
            self.klite_thread = DownloadThread(url, filename)
            self.klite_thread.progress_signal.connect(self.klite_progress.setValue)
            self.klite_thread.finished_signal.connect(self.on_klite_download_finished)
            self.klite_thread.error_signal.connect(self.on_klite_download_error)
            self.klite_thread.start()

            self.log("→ K-Lite Codec Pack download started...")
            self.log("💡 File size: ~21 MB - Please wait for download to complete...")

        except Exception as e: # type: ignore
            self.log(f"✗ Error: {e}")
            self.klite_progress.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to start download:\n{e}")

    def on_klite_download_finished(self, filename):
        """Called when K-Lite download completes"""
        self.log(f"✓ Download complete: {filename}")
        self.klite_progress.setValue(100) # type: ignore

        try:
            self.log("🚀 Launching K-Lite Codec Pack installer...")
            self.klite_progress.setVisible(False)

            # Show installation instructions
            QMessageBox.information(
                self,
                "K-Lite Installation",
                "✅ Download complete!\n\n" \
                "The K-Lite installer will now start.\n\n" \
                "Installation steps:\n" \
                "1. Click 'Next' through the installer\n" \
                "2. Choose 'Basic' or 'Standard' installation\n" \
                "3. Click 'Install' and wait for completion\n" \
                "4. Restart your computer (recommended)\n\n" \
                "After installation, all video formats (MKV, AVI, MOV) will work!\n\n" \
                "(កម្មវិធីដំឡើងនឹងចាប់ផ្តើមឥឡូវនេះ...)",
                QMessageBox.Ok
            )

            # Launch installer
            if os.path.exists(filename):
                self.open_file_or_folder(filename)
            else:
                self.log(f"✗ Installer file not found: {filename}")

        except Exception as e: # type: ignore
            self.log(f"✗ Error launching installer: {e}")
            self.klite_progress.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to launch installer:\n{e}")

    # =============================
    # Professional Settings Helpers
    # =============================

    def _get_gpu_status(self) -> dict[str, str]:
        """Get GPU status for display"""
        if detect_gpu is not None:
            try:
                info = detect_gpu()
                if info.get("gpu_detected"):
                    gpu_name = info.get("gpu_name", "Unknown GPU")
                    gpu_type = info.get("gpu_type", "GPU")
                    return {
                        "text": f"✓ {gpu_name} ({gpu_type})",
                        "color": "#28a745"
                    }
            except Exception:
                pass
        
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                stderr=subprocess.STDOUT,
                creationflags=self._subprocess_creation_flags()
            ).decode("utf-8", errors="ignore").strip()

            if output:
                gpu_name = output.split("\n")[0].strip()
                return {
                    "text": f"✓ {gpu_name}",
                    "color": "#28a745"
                }
        except Exception: # type: ignore
            pass

        return {
            "text": "⚠ No GPU (CPU Mode)",
            "color": "#ffc107"
        }

    def _is_nvidia_gpu_available(self) -> bool:
        """Return True if NVIDIA GPU is available for NVENC encoding."""
        if detect_gpu is not None:
            try:
                info = detect_gpu()
                return bool(info.get("gpu_detected")) and info.get("gpu_type", "").upper().startswith("NVIDIA")
            except Exception:
                pass

        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                stderr=subprocess.STDOUT,
                creationflags=self._subprocess_creation_flags()
            ).decode("utf-8", errors="ignore").strip()
            return bool(output)
        except Exception:
            return False
    
    def _auto_detect_gpu_vs_cpu(self):
        """Auto-detect the best compute mode and update the GPU setting."""
        available = self._is_nvidia_gpu_available()
        self.chk_gpu.setChecked(available)

        # type: ignore
        if available:
            self.safe_log("✅ Auto Detect: NVIDIA GPU found, using GPU encoding.")
            QMessageBox.information(self, "Auto Detect GPU", 
                "✅ GPU Detection Successful\n\n"
                "NVIDIA GPU found. Video will be encoded using GPU (H.264 NVENC).\n"
                "This will be faster than CPU encoding.", QMessageBox.Ok)
        else:
            if detect_gpu is not None:
                try:
                    info = detect_gpu()
                    if info.get("gpu_detected"):
                        gpu_name = info.get("gpu_name", "Unknown GPU")
                        self._warn_cpu_encoding("GPU Not Compatible", f"{gpu_name} detected, but NVIDIA NVENC is not available.")
                    else:
                        self._warn_cpu_encoding("No GPU Available", "No compatible NVIDIA GPU detected.")
                except Exception:
                    self._warn_cpu_encoding("GPU Detection Failed", "Unable to detect GPU status.")
            else:
                self._warn_cpu_encoding("No GPU Available", "No compatible NVIDIA GPU detected.")

        return None

    def _warn_cpu_encoding(self, title: str, detail: str) -> None:
        self.safe_log(f"⚠ Auto Detect: {detail} Using CPU encoding.")
        QMessageBox.warning(
            self,
            "Auto Detect GPU",
            f"⚠️ {title}\n\n{detail}\nVideo will be encoded using CPU.",
            QMessageBox.Ok,
        )

    def _get_ffmpeg_status(self) -> dict[str, str]:
        """Get FFmpeg status for display"""
        ffmpeg_path = self.app_settings.get("ffmpeg_path", "")

        ffmpeg_cmd = None
        if ffmpeg_path:
            ffmpeg_cmd = ffmpeg_path if os.path.exists(ffmpeg_path) else shutil.which(ffmpeg_path)

        if ffmpeg_cmd:
            try:
                output = subprocess.check_output(
                    [ffmpeg_cmd, "-version"],
                    stderr=subprocess.STDOUT,
                    creationflags=self._subprocess_creation_flags()
                ).decode("utf-8", errors="ignore")

                version = output.split("\n")[0].strip()[:60]
                return {
                    "text": f"✓ {version}",
                    "color": "#28a745"
                }
            except Exception:
                return { # type: ignore
                    "text": "⚠ Found (Error)",
                    "color": "#ffc107"
                }

        # Try to find ffmpeg
        search_paths = [
            os.path.join(".", "ffmpeg_bin", "ffmpeg.exe"),
            os.path.join(".", "ffmpeg.exe"),
        ]

        for path in search_paths:
            if os.path.exists(path):
                return {
                    "text": "✓ Found (Auto)",
                    "color": "#28a745"
                }

        return {
            "text": "✗ Not Found",
            "color": "#dc3545"
        }

    def _update_ffmpeg_status_label(self) -> None:
        """Update FFmpeg status label""" # type: ignore
        if hasattr(self, 'lbl_ffmpeg_status'):
            status = self._get_ffmpeg_status()
            self.lbl_ffmpeg_status.setText(status["text"])
            self.lbl_ffmpeg_status.setStyleSheet(f"color: {status['color']}; font-weight: bold;")

    def _get_pytorch_status(self):
        """Get PyTorch status for display"""
        status_code = """
import json
try:
    import torch
    data = {
        "installed": True,
        "version": getattr(torch, "__version__", "unknown"),
        "cuda": bool(torch.cuda.is_available()),
    }
    data["gpu_name"] = torch.cuda.get_device_name(0) if data["cuda"] else None
    print(json.dumps(data))
except Exception:
    print(json.dumps({"installed": False}))
"""
        try:
            python_cmd = self._python_command()
            if not python_cmd:
                return {
                    "text": "✗ Python not found",
                    "color": "#dc3545"
                }

            result = subprocess.run(
                [*python_cmd, "-c", status_code],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode != 0 or not result.stdout.strip():
                raise ImportError("PyTorch status check failed")

            status = json.loads(result.stdout.strip().splitlines()[-1])
            if not status.get("installed"):
                raise ImportError("PyTorch is not installed")

            status_text = f"✓ PyTorch {status.get('version', 'unknown')}"
            if status.get("cuda"):
                gpu_name = status.get("gpu_name")
                status_text += f" (GPU: {gpu_name})" if gpu_name else " (GPU enabled)"
            else:
                status_text += " (CPU mode)"
            return {
                "text": status_text,
                "color": "#28a745"
            }
        except (ImportError, AttributeError): # AttributeError for torch.cuda.is_available if torch is not fully installed # type: ignore
            return {
                "text": "✗ Not Installed",
                "color": "#dc3545"
            }
        except Exception:
            return {
                "text": "⚠ Check installation",
                "color": "#ffc107"
            }

    def _update_pytorch_status_label(self) -> None:
        """Update PyTorch status label""" # type: ignore
        if hasattr(self, 'lbl_pytorch_status'):
            status = self._get_pytorch_status()
            self.lbl_pytorch_status.setText(status["text"])
            self.lbl_pytorch_status.setStyleSheet(f"color: {status['color']}; font-weight: bold;")

    def install_pytorch_auto(self):
        """Install PyTorch using background thread"""
        self.log("⬇️ Starting PyTorch auto-installation...")
        
        self.pytorch_progress.setVisible(True) # type: ignore
        self.pytorch_progress.setRange(0, 100)
        self.pytorch_progress.setFormat("%p%")
        self.pytorch_progress.setValue(0)

        try:
            script_path = self._bundled_script_path("install_pytorch.py")
            if os.path.exists(script_path):
                if hasattr(self, 'pytorch_install_thread') and self.pytorch_install_thread.isRunning():
                    self.log("⚠️ PyTorch installation is already in progress...")
                    return # type: ignore

                python_cmd = self._python_command()
                if not python_cmd:
                    self.log("✗ Python 3.10+ is required to run the PyTorch installer.")
                    self.pytorch_progress.setVisible(False)
                    QMessageBox.warning(self, "Python Required", "Please install Python 3.10+ before running the PyTorch installer.")
                    return

                self.pytorch_install_thread = PyTorchInstallThread(script_path, python_cmd)
                self.pytorch_install_thread.log_signal.connect(self.log)
                self.pytorch_install_thread.progress_signal.connect(self.pytorch_progress.setValue)
                self.pytorch_install_thread.progress_signal.connect(lambda value: self.pytorch_progress.setFormat(f"{value}%"))
                self.pytorch_install_thread.finished_signal.connect(self.on_pytorch_install_finished)
                self.pytorch_install_thread.start()

                self.log("→ Installer running in background (UI remains responsive)")
                self.log("💡 This may take 5-10 minutes depending on your internet speed...")

            else:
                self.log("✗ install_pytorch.py not found")
                self.log(f"💡 Expected path: {script_path}") # type: ignore
                self.pytorch_progress.setVisible(False)

        except PermissionError as e: # type: ignore
            self.log("✗ Permission denied - Try running as Administrator") # type: ignore
            self.pytorch_progress.setVisible(False)
        except Exception as e:
            self.log(f"✗ Error: {e}")
            self.pytorch_progress.setVisible(False)

    def on_pytorch_install_finished(self, success):
        """Called when PyTorch installation completes"""
        self.pytorch_progress.setRange(0, 100)
        
        # type: ignore
        if success:
            self.pytorch_progress.setValue(100)
            self.log("✅ PyTorch installation completed!")
            self._update_pytorch_status_label()
            QTimer.singleShot(2000, lambda: self.pytorch_progress.setVisible(False))
        else:
            self.pytorch_progress.setValue(0)
            self.log("⚠️ PyTorch installation failed or incomplete")
            QTimer.singleShot(3000, lambda: self.pytorch_progress.setVisible(False))

    def _run_verification(self):
        """Run verification script"""
        self.log("🔍 Running installation verification...")
        self._launch_python_script(
            "verify_installation.py",
            "✓ Verification script started",
            "✗ verify_installation.py not found",
        )

    def _test_gpu(self) -> None:
        """Test GPU"""
        self.log("🎮 Testing GPU...")
        self._launch_python_script(
            "test_gpu.py",
            "✓ GPU test started",
            "✗ test_gpu.py not found",
        )

    def install_ffmpeg_auto(self) -> None:
        """Install FFmpeg using background thread (doesn't block UI)"""
        self.log("⬇️ Starting FFmpeg auto-installation...")
        
        self.dl_progress.setVisible(True)
        self.dl_progress.setRange(0, 100)
        self.dl_progress.setFormat("%p%")
        self.dl_progress.setValue(0)

        try:
            script_path = self._bundled_script_path("install_ffmpeg.py")
            if os.path.exists(script_path):
                # Check if already running
                if hasattr(self, 'ffmpeg_install_thread') and self.ffmpeg_install_thread.isRunning():
                    self.log("⚠️ FFmpeg installation is already in progress...") # type: ignore
                    return

                # Start installer in background thread
                python_cmd = self._python_command()
                if not python_cmd:
                    self.log("✗ Python 3.10+ is required to run the FFmpeg installer.")
                    self.dl_progress.setVisible(False)
                    QMessageBox.warning(self, "Python Required", "Please install Python 3.10+ before running the FFmpeg installer.")
                    return

                self.ffmpeg_install_thread = FFmpegInstallThread(script_path, python_cmd)
                self.ffmpeg_install_thread.log_signal.connect(self.log)
                self.ffmpeg_install_thread.progress_signal.connect(self.dl_progress.setValue)
                self.ffmpeg_install_thread.progress_signal.connect(lambda value: self.dl_progress.setFormat(f"{value}%"))
                self.ffmpeg_install_thread.finished_signal.connect(self.on_ffmpeg_install_finished)
                self.ffmpeg_install_thread.start()

                self.log("→ Installer running in background (UI remains responsive)")
                self.log("💡 Watch the logs above for progress...")

            else:
                self.log("✗ install_ffmpeg.py not found")
                self.log("💡 Please download from: https://www.gyan.dev/ffmpeg/builds/") # type: ignore
                self.log(f"💡 Expected path: {script_path}")
                self.dl_progress.setVisible(False)

        except PermissionError as e:
            self.log("✗ Permission denied - Try running as Administrator")
            self.log("💡 Or manually install FFmpeg (see Settings tab for instructions)")
            self.dl_progress.setVisible(False)
        except Exception as e:
            self.log(f"✗ Error: {e}")
            self.log("💡 Try manual installation from Settings tab")
            self.dl_progress.setVisible(False)

    def on_ffmpeg_install_finished(self, success: bool) -> None:
        """Called when FFmpeg installation completes"""
        # Switch back to determinate mode # type: ignore
        self.dl_progress.setRange(0, 100)
        
        if success:
            self.dl_progress.setValue(100)
            self.load_app_settings()
            self.log("✅ FFmpeg installation completed!")
            # Update status immediately
            self._update_ffmpeg_status_label()
            # Hide progress bar after 2 seconds
            QTimer.singleShot(2000, lambda: self.dl_progress.setVisible(False))
        else:
            self.dl_progress.setValue(0)
            self.log("⚠️ FFmpeg installation failed or incomplete")
            # Hide progress bar after 3 seconds
            QTimer.singleShot(3000, lambda: self.dl_progress.setVisible(False)) # type: ignore
    
    def _export_config(self) -> None:
        """Export configuration to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Config", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.app_settings, f, indent=2, ensure_ascii=False) # type: ignore
                self.log(f"✓ Config exported to: {file_path}")
            except Exception as e:
                self.log(f"✗ Export failed: {e}")
    
    def _import_config(self) -> None:
        """Import configuration from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Config", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # type: ignore
                self.app_settings.update(config)
                self.save_app_settings()
                self.log(f"✓ Config imported from: {file_path}")
                QMessageBox.information(self, "Success", "Configuration imported successfully!")
            except Exception as e:
                self.log(f"✗ Import failed: {e}")
                QMessageBox.critical(self, "Error", f"Failed to import config:\n{e}")
    def _reset_settings(self) -> None:
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\n(តើអ្នកប្រាកដថាចង់កំណត់ឡើងវិញមែនទេ?)",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.app_settings = {
                "autosave_enabled": False, # type: ignore
                "autosave_interval": 5,
                "ffmpeg_path": "",
                "update_url": DEFAULT_UPDATE_URL,
                "khmer_font": DEFAULT_KHMER_FONT,
            }
            self.save_app_settings()
            self.chk_autosave.setChecked(False)
            self.sb_autosave_interval.setValue(5)
            if hasattr(self, 'khmer_font_selector'):
                font_index = self.khmer_font_selector.findText(DEFAULT_KHMER_FONT)
                if font_index >= 0:
                    self.khmer_font_selector.setCurrentIndex(font_index)
                else:
                    self.khmer_font_selector.setEditText(DEFAULT_KHMER_FONT)
            self.apply_theme("Default")
            self.log("✓ Settings reset to defaults")

    def _save_logs(self) -> None:
        """Save logs to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Logs",
            f"srt_drama_tool_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_box.toPlainText())
                self.log(f"✓ Logs saved to: {file_path}")
            except Exception as e:
                self.log(f"✗ Failed to save logs: {e}")

    # =============================
    # Helpers (These methods were correctly indented)
    # =============================
    def refresh_role_config_table(self) -> None:
        """Refresh the role column styles in the main table."""
        self.refresh_role_column_styles()

    def apply_role_combo_highlight(self, combo: QComboBox, role: str) -> None:
        if self.role_configs.get(role, {}).get("is_new", False):
            combo.setStyleSheet("background-color: #fff3cd; border: 2px solid #ffc107; font-weight: bold; color: #856404;")
            combo.setToolTip("New character - configure this role to remove the highlight.")
        else:
            combo.setStyleSheet("")
            combo.setToolTip("")

    def refresh_role_column_styles(self) -> None:
        if not hasattr(self, "segment_table"):
            return

        for row in range(self.segment_table.rowCount()):
            combo = self.segment_table.cellWidget(row, 3)
            if isinstance(combo, QComboBox):
                self.apply_role_combo_highlight(combo, combo.currentText())

    def _app_base_dir(self) -> str:
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS  # type: ignore[attr-defined]
        return os.path.dirname(os.path.abspath(__file__))

    def _bundled_script_path(self, script_name: str) -> str:
        script_path = os.path.join(self._app_base_dir(), script_name)
        if not os.path.exists(script_path):
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
        return script_path

    def _python_command(self) -> Optional[list[str]]:
        """Return a real Python interpreter command, avoiding the packaged app EXE."""
        if not getattr(sys, 'frozen', False):
            return [sys.executable]

        for exe_name in ("python.exe", "python3.exe", "python"):
            exe_path = shutil.which(exe_name)
            if exe_path:
                return [exe_path]

        py_launcher = shutil.which("py.exe") or shutil.which("py")
        if py_launcher:
            return [py_launcher, "-3"]

        return None

    def _launch_python_script(self, script_name: str, success_message: str, missing_message: str) -> None:
        try:
            script_path = self._bundled_script_path(script_name)
            if os.path.exists(script_path):
                python_cmd = self._python_command()
                if not python_cmd:
                    message = "Python is required to run this helper script. Please install Python 3.10+ and try again."
                    self.log(f"✗ {message}")
                    QMessageBox.warning(self, "Python Required", message)
                    return

                subprocess.Popen([*python_cmd, script_path]) # type: ignore
                self.log(success_message)
            else:
                self.log(missing_message)
                QMessageBox.warning(self, "Error", missing_message)
        except Exception as e:
            self.log(f"✗ Failed to launch {script_name}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to launch {script_name}:\n{e}")

    def _subprocess_creation_flags(self) -> int:
        return subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    def _configure_audio_converter(self, ffmpeg_bin: str) -> None:
        if ffmpeg_bin and os.path.exists(ffmpeg_bin):
            AudioSegment.converter = ffmpeg_bin

    def _clear_table_cell_widgets(self, row: int) -> None:
        for col in range(self.segment_table.columnCount()):
            cell_widget = self.segment_table.cellWidget(row, col)
            if cell_widget:
                for child in cell_widget.findChildren(QWidget):
                    child.deleteLater()
                cell_widget.deleteLater()

    def _refresh_voice_combo(self, current_voice: str) -> None:
        self.voice_combo.clear()
        self.voice_combo.addItems(self.roles)
        if current_voice in self.roles:
            self.voice_combo.setCurrentText(current_voice)

    def get_ffmpeg(self):
        # 1. ពិនិត្យក្នុង Settings ជាមុន # type: ignore
        path = normalize_windows_drive_path(self.app_settings.get("ffmpeg_path", ""))
        if path and os.path.exists(path):
            return path

        # 2. ពិនិត្យក្នុង Folder ដែល Install ស្វ័យប្រវត្តិ
        auto_install_path = os.path.join(os.path.expanduser("~"), "RVC_Tools", "FFmpeg", "bin", "ffmpeg.exe")
        if os.path.exists(auto_install_path):
            return auto_install_path

        # 3. Check bundled app folders
        app_dir = os.path.dirname(os.path.abspath(__file__))
        for candidate in (
            os.path.join(app_dir, "ffmpeg_bin", "ffmpeg.exe"),
            os.path.join(app_dir, "ffmpeg.exe"),
        ):
            if os.path.exists(candidate):
                return candidate

        # 4. បើរកមិនឃើញទាំងអស់ ប្រើពាក្យបញ្ជា System
        return "ffmpeg"
    
    def get_ffprobe(self): # type: ignore
        """Find ffprobe path relative to ffmpeg or in system PATH."""
        saved_ffprobe = normalize_windows_drive_path(self.app_settings.get("ffprobe_path", ""))
        if saved_ffprobe and os.path.exists(saved_ffprobe):
            return saved_ffprobe

        ffmpeg_path = self.get_ffmpeg()
        ext = ".exe" if sys.platform == "win32" else ""
        
        # 1. If absolute path to ffmpeg is provided, check same dir for ffprobe
        if os.path.exists(ffmpeg_path):
            dir_name = os.path.dirname(ffmpeg_path)
            candidate = os.path.join(dir_name, "ffprobe" + ext)
            if os.path.exists(candidate):
                return candidate
                
        # 2. Check application's local bin folder
        local_bin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg_bin")
        local_ffprobe = os.path.join(local_bin, "ffprobe" + ext)
        if os.path.exists(local_ffprobe):
            return local_ffprobe
            
        # 3. Check installation directory created by install_ffmpeg.py
        user_ffmpeg_bin = os.path.join(os.path.expanduser("~"), "RVC_Tools", "FFmpeg", "bin")
        path_ffprobe = os.path.join(user_ffmpeg_bin, "ffprobe" + ext)
        if os.path.exists(path_ffprobe):
            return path_ffprobe
            
        # 4. Fallback to system PATH
        return "ffprobe"
    
    def get_video_duration_ms(self, video_path):
        """Get video duration in milliseconds using ffprobe (Fix Bug #19: async to avoid UI freeze)""" # type: ignore
        # Use a list to capture result from the thread
        result_container = [0]

        def _duration_from_ffmpeg(path: str) -> int:
            ffmpeg_path = self.get_ffmpeg()
            cmd = [ffmpeg_path, "-i", path]
            try:
                creation_flags = self._subprocess_creation_flags()
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=10,
                    creationflags=creation_flags,
                )
                output = f"{result.stdout}\n{result.stderr}"
                match = re.search(r"Duration:\s*(\d{2,}):(\d{2}):(\d{2}(?:\.\d+)?)", output)
                if not match:
                    return 0
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = float(match.group(3))
                return int(((hours * 3600) + (minutes * 60) + seconds) * 1000)
            except Exception:
                return 0

        def _probe(instance_self, path, container):
            ffprobe_path = self.get_ffprobe()
            cmd = [
                ffprobe_path, "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", path
            ]

            try:
                creation_flags = self._subprocess_creation_flags()
                # Fix Bug #19: Add timeout to prevent hanging
                output = subprocess.check_output(cmd, creationflags=creation_flags, text=True, timeout=10).strip()
                duration_sec = float(output)
                container[0] = int(duration_sec * 1000)  # Convert to milliseconds
            except FileNotFoundError:
                fallback_duration = _duration_from_ffmpeg(path)
                if fallback_duration > 0:
                    container[0] = fallback_duration
                else:
                    instance_self.safe_log("⚠️ Could not get video duration: ffprobe.exe not found and ffmpeg fallback failed")
            except subprocess.TimeoutExpired:
                instance_self.safe_log("⚠️ ffprobe timed out after 10 seconds")
            except Exception as e:
                fallback_duration = _duration_from_ffmpeg(path)
                if fallback_duration > 0:
                    container[0] = fallback_duration
                else:
                    instance_self.safe_log(f"⚠️ Could not get video duration: {e}")

        # Run in a separate thread and wait for completion
        t = threading.Thread(target=_probe, args=(self, video_path, result_container), daemon=True)
        t.start()
        t.join(timeout=12)  # 10s timeout + 2s buffer

        return result_container[0]
    
    def has_audio_stream(self, video_path): # type: ignore
        ffprobe_path = self.get_ffprobe()

        cmd = [
            ffprobe_path, "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=codec_type", "-of", "csv=p=0", video_path
        ]
        
        try:
            # Hide window on Windows
            creation_flags = self._subprocess_creation_flags()
            output = subprocess.check_output(cmd, creationflags=creation_flags, text=True).strip()
            return len(output) > 0 # Returns True if 'audio' is found
        except Exception:
            try:
                ffmpeg_path = self.get_ffmpeg()
                result = subprocess.run(
                    [ffmpeg_path, "-i", video_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=10,
                    creationflags=self._subprocess_creation_flags(),
                )
                output = f"{result.stdout}\n{result.stderr}"
                return bool(re.search(r"Stream #\d+:\d+.*Audio:", output))
            except Exception:
                pass
            # If all probes fail, assume False to be safe (prevent FFmpeg crash)
            return False # type: ignore
    def has_stereo_audio_stream(self, video_path): # type: ignore
        ffprobe_path = self.get_ffprobe()
        if not ffprobe_path:
            return False

        cmd = [
            ffprobe_path, "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=channels",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ]

        try:
            creation_flags = self._subprocess_creation_flags()
            output = subprocess.check_output(cmd, creationflags=creation_flags, text=True).strip()
            return int(output) >= 2
        except Exception:
            return False
    
    def get_output_dir(self): # type: ignore
        path = ""
        if self.output_folder is not None:
            path = self.output_folder.text() if hasattr(self.output_folder, 'text') else str(self.output_folder)
        path = path.strip() or "Output"  # Fix Bug #9: Strip whitespace

        # Fix Bug #9: Validate path to prevent invalid characters or unreachable locations
        try:
            # Check for invalid characters in path (Windows)
            if sys.platform == 'win32':
                invalid_chars = set('<>:"|?*')
                drive, tail = os.path.splitdrive(path)
                check_path = tail if drive else path
                if any(c in invalid_chars for c in check_path):
                    self.safe_log("⚠️ Invalid characters in output path, using default 'Output'")
                    path = "Output"

            # Create directory only if it doesn't exist
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)

            # Verify the path is accessible
            if not os.path.isdir(path):
                self.safe_log("⚠️ Output path is not a directory, using default 'Output'")
                path = "Output"
                os.makedirs(path, exist_ok=True)

        except PermissionError:
            self.safe_log("⚠️ Permission denied for output path, using default 'Output'")
            path = "Output"
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            self.safe_log(f"⚠️ Error creating output directory: {e}, using default 'Output'")
            path = "Output"
            os.makedirs(path, exist_ok=True)

        return path
    
    # type: ignore
    def get_latest_audio_source(self):
        # Priority 1: ប្រើ File ដែលទើបបង្កើតថ្មីៗបំផុត (ទោះដូរឈ្មោះក៏ដោយ)
        if self.last_generated_audio and os.path.exists(self.last_generated_audio):
            return self.last_generated_audio

        # Priority 2: ស្វែងរកតាមឈ្មោះចាស់ (Fallback)
        output_dir = self.get_output_dir()
        candidates = [
            os.path.join(output_dir, "Full_TTS_Export.wav"),
            os.path.join(output_dir, "Full_TTS_Export.mp3"),
            os.path.join(output_dir, "srt_output.wav")
        ]
        tts_audio = ""
        latest_time = 0
        for f in candidates:
            if os.path.exists(f):
                mtime = os.path.getmtime(f)
                if mtime > latest_time:
                    latest_time = mtime
                    tts_audio = f
        return tts_audio
    
    # type: ignore
    def set_table_row(self, row, start_ms, end_ms, role, text):
        # Helper to set table items (កាត់បន្ថយកូដស្ទួន)
        item_start = QTableWidgetItem(self.ms_to_time(start_ms)); item_start.setData(QT_USER_ROLE, start_ms)
        self.segment_table.setItem(row, 0, item_start)
        item_end = QTableWidgetItem(self.ms_to_time(end_ms)); item_end.setData(QT_USER_ROLE, end_ms)
        self.segment_table.setItem(row, 1, item_end)

        # Fix Bug #8: Clear old cell widgets to prevent memory leaks
        for col in [2, 3, 5]:  # Columns with dynamic widgets
            old_widget = self.segment_table.cellWidget(row, col)
            if old_widget:
                old_widget.deleteLater()

        # Duration SpinBox (សម្រាប់កំណត់ល្បឿន/រយៈពេល)
        dur_sec = max(0.1, (end_ms - start_ms) / 1000.0)
        sb_dur = QDoubleSpinBox()
        sb_dur.setRange(0.1, 9999.0)
        sb_dur.setSingleStep(0.001)
        sb_dur.setDecimals(3)
        sb_dur.setValue(dur_sec)
        sb_dur.setSuffix("s")
        sb_dur.setToolTip("Adjust duration with millisecond precision (កំណត់រយៈពេលត្រឹម 0.001s)")
        # Highlight long duration > 10s (បង្ហាញពណ៌លឿងបើលើសពី ១០ វិនាទី)
        if dur_sec > 10.0: # type: ignore
            sb_dur.setStyleSheet("background-color: #fefcbf; font-weight: bold; color: #b7791f;")
            sb_dur.setToolTip("⚠️ Warning: Duration > 10s! (វែងខុសប្រក្រតី)")
        else:
            sb_dur.setStyleSheet("background-color: #ebf8ff;")
        sb_dur.valueChanged.connect(self.on_duration_changed)
        self.segment_table.setCellWidget(row, 2, sb_dur)

        combo = QComboBox(); combo.addItems(self.roles); combo.setCurrentText(role) # type: ignore
        combo.currentTextChanged.connect(lambda selected_role, role_combo=combo: self.apply_role_combo_highlight(role_combo, selected_role))
        self.segment_table.setCellWidget(row, 3, combo)
        self.apply_role_combo_highlight(combo, role)
        self.segment_table.setItem(row, 4, QTableWidgetItem(text))
        self.segment_table.setCellWidget(row, 5, self.create_action_widget()) # type: ignore

    def on_duration_changed(self, value):
        sb = self.sender()
        if not sb: return
        sb = cast(QDoubleSpinBox, sb)
        
        # Find row dynamically
        row = -1
        for r in range(self.segment_table.rowCount()):
            if self.segment_table.cellWidget(r, 2) == sb:
                row = r
                break
        
        if row == -1: return
        
        # Update End Time
        item_start = self.segment_table.item(row, 0)
        if item_start:
            start_ms = item_start.data(QT_USER_ROLE)
            new_end_ms = start_ms + int(round(value * 1000))
            
            item_end = self.segment_table.item(row, 1)
            if item_end:
                item_end.setText(self.ms_to_time(new_end_ms))
                item_end.setData(QT_USER_ROLE, new_end_ms)
            
            # Check Overlap
            next_row = row + 1
            if next_row < self.segment_table.rowCount():
                item_next = self.segment_table.item(next_row, 0)
                if item_next:
                    next_start = item_next.data(QT_USER_ROLE)
                    if new_end_ms > next_start:
                        # Overlap -> Red
                        sb.setStyleSheet("background-color: #feb2b2; font-weight: bold; color: #c53030;")
                        sb.setToolTip(f"⚠️ Overlap! Next starts at {self.ms_to_time(next_start)}")
                    elif value > 10.0:
                        # Long Duration -> Yellow
                        sb.setStyleSheet("background-color: #fefcbf; font-weight: bold; color: #b7791f;") # type: ignore
                        sb.setToolTip("⚠️ Warning: Duration > 10s! (វែងខុសប្រក្រតី)")
                    else:
                        # Normal -> Blue
                        sb.setStyleSheet("background-color: #ebf8ff;")
                        sb.setToolTip("Adjust duration with millisecond precision (កំណត់រយៈពេលត្រឹម 0.001s)")
    def on_crop_preset_changed(self):
        if self.sb_crop_top is None or self.sb_crop_bottom is None:
            return
        is_custom = self.cb_crop_preset.currentText() == "Custom"
        self.sb_crop_top.setEnabled(is_custom)
        self.sb_crop_bottom.setEnabled(is_custom)
        if self.sb_crop_left is not None: self.sb_crop_left.setEnabled(is_custom)
        if self.sb_crop_right is not None: self.sb_crop_right.setEnabled(is_custom) # type: ignore

    def toggle_cut_inputs(self, checked):
        self.txt_start.setEnabled(checked)
        self.txt_end.setEnabled(checked)
        if checked:
            dur = self.media_player.duration()
            if dur > 0:
                # Format: HH:MM:SS
                self.txt_end.setText(self.ms_to_time(dur).split(',')[0]) # type: ignore

    def get_voice_from_role(self, role: str) -> str:
        if role in self.role_configs and "voice" in self.role_configs[role]:
            # type: ignore
            return self.role_configs[role]["voice"]
        if "Female" in role or "Girl" in role or "ស្រី" in role:
            return "km-KH-SreymomNeural"
        return "km-KH-PisethNeural"

    def get_tts_params(self, role, speed_offset=0): # type: ignore
        config = self.role_configs.get(role, {})
        voice = self.get_voice_from_role(role)
    
        # Base values from config + manual offset
        rate_val = config.get("rate", 0) + speed_offset
        pitch_val = config.get("tts_pitch", 0)
    
        # Age & Emotion Logic
        age = config.get("age", "")
        emotion = config.get("emotion", "")
    
        if "Child" in age: pitch_val += 25; rate_val += 10
        elif "Teen" in age: pitch_val += 10; rate_val += 5
        elif "Elder" in age: pitch_val -= 15; rate_val -= 10
        
        if "Happy" in emotion: pitch_val += 5; rate_val += 10
        elif "Sad" in emotion: pitch_val -= 5; rate_val -= 15
        elif "Angry" in emotion: rate_val += 5; pitch_val -= 5
        elif "Excited" in emotion: rate_val += 20; pitch_val += 5
    
        return voice, f"{rate_val:+d}%", f"{pitch_val:+d}Hz"

    def select_folder(self) -> None:
        last_dir = self.app_settings.get("last_output_dir", "") # type: ignore
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder", last_dir)
        if path:
            if self.output_folder is not None:
                self.output_folder.setText(path)
            self.app_settings["last_output_dir"] = path
            self.save_app_settings()

    def select_ffmpeg(self) -> None:
        last_dir = self.app_settings.get("last_ffmpeg_dir", "") # type: ignore
        path, _ = QFileDialog.getOpenFileName(self, "Select ffmpeg.exe", last_dir, "Executable (*.exe);;All Files (*)")
        if path:
            if self.ffmpeg_path is not None:
                self.ffmpeg_path.setText(path)
            self.app_settings["ffmpeg_path"] = path
            self.app_settings["last_ffmpeg_dir"] = os.path.dirname(path)
            self.save_app_settings()
    def save_ffmpeg_path(self) -> None:
        """Save manually entered FFmpeg path"""
        if self.ffmpeg_path is None: # type: ignore
            return
    
        path = self.ffmpeg_path.text().strip()
    
        if not path:
            QMessageBox.warning(self, "Error", "Please enter an FFmpeg path")
            return
    
        # Check if path exists and is valid (only for absolute paths)
        if path != "ffmpeg" and not os.path.exists(path):
            reply = QMessageBox.question(
                self, "Path Not Found",
                f"The specified path does not exist:\n{path}\n\nDo you want to save it anyway?\n"
                "(It might be in system PATH or you can correct it later)",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
    
        # Save to settings
        self.app_settings["ffmpeg_path"] = path # type: ignore
        self.save_app_settings()
    
        # Update status
        self._update_ffmpeg_status_label() # type: ignore
    
        QMessageBox.information(self, "Success", f"FFmpeg path saved successfully!\n{path}")

    def open_output_folder(self) -> None:
        output_dir = self.get_output_dir()
        self.open_file_or_folder(output_dir)

    # =============================
    # Logic / Actions
    # =============================

    def append_log(self, message: str) -> None:
        # Fix Bug #29: Check if log_box exists and is a valid widget
        if hasattr(self, 'log_box') and self.log_box: # type: ignore
            try:
                self.log_box.append(f">> {message}")
            except Exception:
                pass  # log_box may not be ready or deleted

    def log(self, message: str) -> None:
        self.log_signal.emit(message)
    def on_tts_finished(self) -> None:
        self.btn_generate.setEnabled(True) # type: ignore
        self.progress.setValue(100)
    def on_srt_finished(self): # This method was correctly indented
        self.btn_srt.setEnabled(True)
        self.btn_run_srt.setEnabled(True)
        self.btn_stop_srt.setEnabled(False)
        self.btn_export_wav.setEnabled(True)
        self.progress.setValue(100)
        if hasattr(self, 'export_progress'): # type: ignore
            self.export_progress.setValue(100)
    def on_export_finished(self) -> None:
        if getattr(self, "merge_in_progress", False):
            return
        self.btn_export_mp4.setEnabled(True) # type: ignore
        self.export_progress.setValue(100)
        # Also update Home tab progress bar (they share the same export process)
        if hasattr(self, 'progress'): # type: ignore
            self.progress.setValue(100)
        self.progress_text_signal.emit("")  # Clear progress text
    def update_progress_text(self, text: str) -> None:
        """Update progress bar text display (e.g., 'Encoding: 45%')"""
        if hasattr(self, 'export_progress'): # type: ignore
            self.export_progress.setFormat(text)
    def stop_processing(self) -> None:
        self.stop_event.set()
        self.log("🛑 Stopping process... Please wait for current tasks to finish.")
        self.btn_stop_srt.setEnabled(False)
    def generate_tts(self): # This method was correctly indented # type: ignore
        text = self.text_input.toPlainText()
        if not text:
            QMessageBox.warning(self, "Input Error", "សូមបញ្ចូលអត្ថបទជាមុនសិន! (Please enter text)")
            return
    
        self.log(f"Generating TTS... ({len(text)} chars)")
        self.progress.setValue(10)
        self.btn_generate.setEnabled(False) # type: ignore
        role_name = self.voice_combo.currentText()
        voice_short, rate_str, pitch_str = self.get_tts_params(role_name, self.speed_spin.value())

        # Get Fade values & FFmpeg path
        fade_in = self.fade_in.value()
        fade_out = self.fade_out.value()
        ffmpeg_bin = self.get_ffmpeg()
        output_dir = self.get_output_dir()
        output_file = os.path.join(output_dir, "tts_output.wav")
        output_file = os.path.abspath(output_file)
    
        # type: ignore
        auto_play = self.chk_autoplay.isChecked()
        # Run in a separate thread to keep UI responsive
        self.start_worker_thread(target=self.run_tts_thread, args=(text, voice_short, rate_str, pitch_str, fade_in, fade_out, ffmpeg_bin, output_file, auto_play))

    def get_row_for_sender(self) -> Optional[int]:
        """Finds the table row for the widget that sent the signal."""
        sender = self.sender()
        if not sender or not isinstance(sender, QWidget):
            return None

        # The sender button is inside the action_widget
        parent = sender.parentWidget()
        if not parent:
            return None

        # Find the row by matching the cell widget in the actions column
        for row in range(self.segment_table.rowCount()):
            if self.segment_table.cellWidget(row, 5) == parent:
                return row
        return None

    def handle_play_video_button(self) -> None:
        row = self.get_row_for_sender() # type: ignore
        if row is not None:
            self.play_video_segment(row)

    def handle_test_tts_button(self) -> None:
        row = self.get_row_for_sender()
        if row is not None:
            self.row_action(row, "test_tts")

    def handle_gen_tts_button(self) -> None:
        row = self.get_row_for_sender() # type: ignore
        if row is not None:
            self.row_action(row, "gen_tts")

    def handle_delete_button(self) -> None:
        row = self.get_row_for_sender()
        if row is not None:
            self.delete_segment(row)

    def create_action_widget(self) -> QWidget:
        action_widget = QWidget() # type: ignore
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(2, 2, 2, 2)
        action_layout.setSpacing(2)

        btn_play_orig = QPushButton("▶ Video")
        btn_play_orig.setStyleSheet("""
            QPushButton {
                background-color: #ed8936;
                color: white;
            }
        """) # type: ignore
        btn_play_orig.clicked.connect(self.handle_play_video_button) # type: ignore
    
        btn_test_tts = QPushButton("Test TTS")
        btn_test_tts.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2c5282;
            }
        """)
        btn_test_tts.clicked.connect(self.handle_test_tts_button)

        btn_gen_tts = QPushButton("Gen TTS")
        btn_gen_tts.setStyleSheet("""
            QPushButton {
                background-color: #38a169;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2f855a;
            }
        """)
    
        action_layout.addWidget(btn_play_orig)
        action_layout.addWidget(btn_test_tts) # type: ignore
        action_layout.addWidget(btn_gen_tts)
    
        # Add Delete Button
        btn_del = QPushButton("❌")
        btn_del.setFixedWidth(30)
        btn_del.setStyleSheet("background-color: #e53e3e; font-weight: bold;")
        btn_del.clicked.connect(self.handle_delete_button)
        action_layout.addWidget(btn_del) # type: ignore
    
        return action_widget

    def delete_segment(self, row: int) -> None:
        # This is now a very fast operation, as it no longer needs to # type: ignore
        # rebuild all the action widgets in the table.
    
        self._clear_table_cell_widgets(row)
    
        # Now remove the row (widgets already scheduled for deletion)
        self.segment_table.removeRow(row)

    def load_dual_srt(self) -> None:
        """
        Sync two SRT files: One for accurate Timing (Original), one for Text (Translated).
        (បញ្ចូល SRT ពីរផ្គុំគ្នា៖ មួយយកនាទី មួយយកអត្ថបទ)
        """
        last_dir = self.app_settings.get("last_srt_dir", "")

        # 1. Select Timing File (Original Chinese SRT)
        time_path, _ = QFileDialog.getOpenFileName(self, "ជ្រើសរើស SRT ដើម (ដើម្បីយកនាទីត្រឹមត្រូវ)", last_dir, "Subtitle Files (*.srt *.vtt)")
        if not time_path: return

        # Save the directory for future use
        self.app_settings["last_srt_dir"] = os.path.dirname(time_path)
        self.save_app_settings()

        # 2. Select Text File (AI Translated SRT)
        text_path, _ = QFileDialog.getOpenFileName(self, "ជ្រើសរើស SRT បកប្រែ (ដើម្បីយកអត្ថបទ)", os.path.dirname(time_path), "Subtitle Files (*.srt *.vtt)")
        if not text_path: return

        # Update last_srt_dir if different
        text_dir = os.path.dirname(text_path)
        if text_dir != self.app_settings.get("last_srt_dir", ""):
            self.app_settings["last_srt_dir"] = text_dir
            self.save_app_settings()

        self.log(f"🔄 កំពុងផ្គុំនាទីពី ({os.path.basename(time_path)}) ជាមួយអត្ថបទ ({os.path.basename(text_path)})...")

        try:
            time_subs = self.parse_srt(time_path) # type: ignore
            text_subs = self.parse_srt(text_path)
        
            if not time_subs:
                QMessageBox.warning(self, "Error", "File នាទីដើមមិនមានទិន្នន័យ!")
                return
            if not text_subs:
                QMessageBox.warning(self, "Error", "File បកប្រែមិនមានទិន្នន័យ!")
                return
            self.log("ℹ️ Sync mode: នាទីយកពី CapCut file ដើម។ Timestamp ក្នុង file AI បកប្រែត្រូវបានរំលង។")
            if len(time_subs) != len(text_subs):
                self.log(
                    f"⚠️ ចំនួនបន្ទាត់មិនស្មើគ្នា: នាទី={len(time_subs)}, បកប្រែ={len(text_subs)}. "
                    "កម្មវិធីនឹងយកនាទីពី CapCut ហើយចែកអត្ថបទបកប្រែតាមលំដាប់។"
                )
            else:
                self.log(f"✅ ចំនួនបន្ទាត់ស្មើគ្នា ({len(time_subs)}). កម្មវិធីនឹងយកអត្ថបទបកប្រែតាមលេខ/លំដាប់បន្ទាត់។")

            base_subs = time_subs
            text_by_number: dict[int, str] = {}
            for text_sub in text_subs:
                number = text_sub.get("number")
                text = text_sub.get("text", "")
                if isinstance(number, int):
                    text_by_number[number] = f"{text_by_number.get(number, '')} {text}".strip()

            text_list = [sub.get("text", "") for sub in text_subs]
            index_fallback_count = 0
            proportional_merge_count = 0

            def get_translated_text_for_row(index: int, timing_sub: dict[str, Any]) -> str:
                nonlocal index_fallback_count, proportional_merge_count
                number = timing_sub.get("number")
                if isinstance(number, int) and number in text_by_number:
                    return text_by_number[number]

                if len(text_subs) == len(time_subs) and index < len(text_list):
                    index_fallback_count += 1
                    return text_list[index]

                if text_list:
                    start_idx = (index * len(text_list)) // len(base_subs)
                    end_idx = ((index + 1) * len(text_list)) // len(base_subs)
                    if end_idx <= start_idx:
                        end_idx = start_idx + 1
                    proportional_merge_count += 1
                    return " ".join(t.strip() for t in text_list[start_idx:end_idx] if t.strip()).strip()

                return "[បាត់អត្ថបទបកប្រែ]"

            # --- ផ្នែករៀបចំពណ៌សម្រាប់តួអង្គ (Role Color Setup) --- # type: ignore
            import re
            from PyQt5.QtGui import QColor
            role_colors = {}
            color_palette = [ # type: ignore
                "#e6f7ff", "#f6ffed", "#fff7e6", "#fff1f0", 
                "#f9f0ff", "#fffbe6", "#e6fffb", "#f0f5ff",
                "#f5f5f5", "#e6e6fa", "#faf0e6", "#f0fff0"
            ]
            # --------------------------------------------------

            existing_roles_before_load = set(self.roles)

            # type: ignore
            # Merge logic: Use timing from time_subs, text from text_subs
            self.segment_table.setUpdatesEnabled(False)
            self.segment_table.setRowCount(len(base_subs))
        
            try:
                prev_end = 0
                for i, t_sub in enumerate(base_subs):
                    # Timing always comes from CapCut. AI-translated timestamps are ignored.
                    translated_text = get_translated_text_for_row(i, t_sub)
                
                    # ១. ចាប់យកតួអង្គដោយស្វ័យប្រវត្តិ (Automatic Speaker Detection)
                    detected_role: str = "Unknown" # type: ignore
                    clean_text = translated_text
                
                    # ស្វែងរក Pattern ដូចជា [ប្រុស, យុវវ័យ]
                    match = re.search(r'^\[(.*?)\]', translated_text)
                    if match:
                        detected_role = normalize_role_name(match.group(1).strip())
                        clean_text = translated_text.replace(match.group(0), "").strip()
                
                    # ២. កំណត់ពណ៌តាមតួអង្គ (Character Color Assignment) # type: ignore
                    if detected_role not in role_colors:
                        color_idx = len(role_colors) % len(color_palette) # type: ignore
                        role_colors[detected_role] = color_palette[color_idx]
                
                    current_bg_color = role_colors[detected_role]
                
                    # Fix: Add to global roles BEFORE setting table row to prevent default to "Male, Child"
                    if detected_role not in self.roles:
                        self.roles.append(detected_role)
                        self._initialize_new_role_config(detected_role)

                    self.set_table_row(i, t_sub['start'], t_sub['end'], detected_role, clean_text) # type: ignore

                    # ៤. អនុវត្តពណ៌លើជួរនីមួយៗ (Apply Row/Widget Coloring)
                    # Check if this role is marked as new and unconfigured
                    is_unconfigured_role = self.role_configs.get(detected_role, {}).get("is_new", False)

                    for col in range(self.segment_table.columnCount()):
                        # ពណ៌លើអត្ថបទធម្មតា
                        table_item = self.segment_table.item(i, col)
                        if table_item: # type: ignore
                            table_item.setBackground(QColor(current_bg_color)) # type: ignore
                    
                        # ពណ៌លើ Widget (ComboBox, SpinBox)
                        cell_widget = self.segment_table.cellWidget(i, col)
                        if cell_widget:
                            style = f"background-color: {current_bg_color}; border: none;"
                            # Apply highlight if it's the role column and the role is new
                            if col == 3 and is_unconfigured_role:
                                style = f"background-color: #fff3cd; border: 2px solid #ffc107; font-weight: bold; color: #856404;"
                            cell_widget.setStyleSheet(style)

                    # Timing validation for original file too
                    error_tip = ""
                    duration = t_sub['end'] - t_sub['start'] # type: ignore
                    if t_sub['start'] >= t_sub['end']: 
                        error_tip = "⚠️ នាទីបញ្ចប់ខុស"
                    elif t_sub['start'] < prev_end: 
                        error_tip = "⚠️ នាទីជាន់គ្នា"
                    elif duration > 30000: # Over 30 seconds is usually a mistake for a single line
                        error_tip = f"⚠️ រយៈពេលវែងខុសប្រក្រតី ({duration/1000:.1f}s)"

                    if error_tip:
                        # បើមានកំហុស ប្រើពណ៌ក្រហមឆ្អៅជំនួសវិញ
                        error_color = "#fed7d7"
                        for col in range(self.segment_table.columnCount()): # type: ignore
                            item = self.segment_table.item(i, col) # type: ignore
                            if item: item.setBackground(QColor(error_color))
                            widget = self.segment_table.cellWidget(i, col)
                            if widget: widget.setStyleSheet(f"background-color: {error_color};")

                    prev_end = t_sub['end']
            finally:
                # CRITICAL: Always re-enable updates even if exception occurs
                # This prevents table from freezing if an error happens mid-loop
                self.segment_table.setUpdatesEnabled(True)

            # Update main combo box with new roles
            current_voice = self.voice_combo.currentText()
            self.voice_combo.blockSignals(True)
            self._refresh_voice_combo(current_voice)
            self.voice_combo.blockSignals(False)

            self.btn_run_srt.setEnabled(True) # type: ignore
        
            # Store character information globally for lip-sync and other features
            self.srt_characters = list(role_colors.keys())
            self.character_info = role_colors.copy()
        
            new_roles_count = len(set(self.roles) - existing_roles_before_load)
            summary_msg = f"✅ ផ្គុំបានជោគជ័យ ចំនួន {len(base_subs)} បន្ទាត់! រកឃើញ {len(role_colors)} តួអង្គ។"
            if new_roles_count > 0:
                summary_msg += f" (រកឃើញតួអង្គថ្មីចំនួន {new_roles_count} ដែលត្រូវកំណត់សំឡេង)"
            self.log(summary_msg)
            if proportional_merge_count:
                self.log(
                    f"ℹ️ មាន {proportional_merge_count} បន្ទាត់បានចែក/បូកអត្ថបទបកប្រែតាមលំដាប់ ព្រោះចំនួនបន្ទាត់មិនស្មើ។"
                )
            if index_fallback_count:
                self.log(
                    f"ℹ️ មាន {index_fallback_count} បន្ទាត់បានយកអត្ថបទតាមលំដាប់បន្ទាត់។ នាទីនៅតែយកពី CapCut file ដើម។"
                )
            self.progress.setValue(100) # type: ignore

        except Exception as e:
            # No need to re-enable updates here - finally block already did it
            self.log(f"❌ Error during Sync: {e}")
            QMessageBox.critical(self, "Sync Error", f"មានបញ្ហាក្នុងការផ្គុំ File:\n{e}") # type: ignore

    def add_manual_segment(self) -> None:
        start_str = self.manual_start.text() # type: ignore
    
        # Support pasting "00:00:00,000 --> 00:00:00,000" into Start field
        if "-->" in start_str:
            parts = start_str.split("-->")
            if len(parts) == 2:
                start_str = parts[0].strip()
                self.manual_start.setText(start_str)
                self.manual_end.setText(parts[1].strip())

        end_str = self.manual_end.text() # type: ignore
        text = self.manual_text.text()
    
        if not text.strip():
            QMessageBox.warning(self, "Input Error", "Please enter text.")
            return

        try:
            start_ms = self.time_to_ms(start_str) # type: ignore
            end_ms = self.time_to_ms(end_str)
        except Exception as e:
            QMessageBox.warning(self, "Time Format Error", f"Invalid time format. Use HH:MM:SS,ms\n{e}")
            return
        
        if start_ms >= end_ms:
            QMessageBox.warning(self, "Time Error", "End time must be greater than Start time.")
            return
        
        # Check video duration limit (ត្រួតពិនិត្យរយៈពេលវីដេអូ)
        video_duration = self.media_player.duration()
        if video_duration > 0 and (start_ms > video_duration or end_ms > video_duration): # type: ignore
            QMessageBox.warning(self, "Time Warning (លើសម៉ោងវីដេអូ)", 
                               f"ពេលវេលាដែលបានបញ្ចូលលើសពីរយៈពេលរបស់វីដេអូ!\n(Time exceeds video duration)\n\n"
                               f"Video Duration: {self.ms_to_time(video_duration)}\n"
                               f"Your Input: {end_str}")
            return

        # Check for overlaps (ត្រួតពិនិត្យការជាន់គ្នា)
        for r in range(self.segment_table.rowCount()):
            item_s = self.segment_table.item(r, 0)
            item_e = self.segment_table.item(r, 1)
            if item_s and item_e: # type: ignore
                ex_start = item_s.data(QT_USER_ROLE)
                ex_end = item_e.data(QT_USER_ROLE)
            
                if start_ms < ex_end and end_ms > ex_start:
                    QMessageBox.warning(self, "Overlap Warning (ជាន់គ្នា)", f"Time overlaps with Row {r+1}!\nExisting: {self.ms_to_time(ex_start)} - {self.ms_to_time(ex_end)}")
                    msg = f"ជាន់គ្នាជាមួយបន្ទាត់ទី {r+1} (Overlaps with Row {r+1})!\n"
                    msg += f"Existing: {self.ms_to_time(ex_start)} --> {self.ms_to_time(ex_end)}\n\n"
                
                    if ex_start <= start_ms < ex_end:
                        msg += f"ជាន់នៅ Start: {start_str}\n"
                    if ex_start < end_ms <= ex_end:
                        msg += f"ជាន់នៅ End: {end_str}\n"
                    if start_ms <= ex_start and end_ms >= ex_end:
                        msg += "ជាន់គ្របដណ្តប់ (Covers existing segment)\n"

                    QMessageBox.warning(self, "Overlap Warning (ជាន់គ្នា)", msg)
                    return
        
        row = self.segment_table.rowCount() # type: ignore
        self.segment_table.insertRow(row)
    
        self.set_table_row(row, start_ms, end_ms, self.voice_combo.currentText(), text)
        # type: ignore
    
    
        self.manual_text.clear()
        self.manual_start.setText("00:00:00,000")
        self.manual_end.setText("00:00:00,000") # type: ignore
        self.btn_run_srt.setEnabled(True) # type: ignore
    def load_srt(self, srt_path: Optional[str] = None) -> None:
        if not srt_path:
            last_dir = self.app_settings.get("last_srt_dir", "")
            srt_path, _ = QFileDialog.getOpenFileName(self, "Select Subtitle File", last_dir, "Subtitle Files (*.srt *.vtt)")
    
        if not srt_path:
            return

        self.app_settings["last_srt_dir"] = os.path.dirname(srt_path)
        self.save_app_settings()
        self.current_srt_path = srt_path
        self.log(f"Loaded SRT: {srt_path}")
    
        try:
            subs = self.parse_srt(srt_path)
        
            # Optimization: Disable updates to prevent freezing
            self.segment_table.setUpdatesEnabled(False)
            self.segment_table.setRowCount(len(subs))

            # --- ផ្នែករៀបចំពណ៌សម្រាប់តួអង្គ (Role Color Setup) ---
            import re
            from PyQt5.QtGui import QColor # type: ignore
            role_colors = {}
            color_palette = [ # type: ignore
                "#e6f7ff", "#f6ffed", "#fff7e6", "#fff1f0", 
                "#f9f0ff", "#fffbe6", "#e6fffb", "#f0f5ff",
                "#f5f5f5", "#e6e6fa", "#faf0e6", "#f0fff0"
            ]
            # --------------------------------------------------

            existing_roles_before_load = set(self.roles)

            try:
                total_subs = len(subs) # type: ignore
                prev_end = 0

                for i, sub in enumerate(subs): # type: ignore
                    raw_text = sub['text']
                
                    # ១. ចាប់យកតួអង្គដោយស្វ័យប្រវត្តិ (Automatic Speaker Detection)
                    detected_role = "Unknown"
                    clean_text = raw_text
                
                    # ស្វែងរក Pattern ដូចជា [ប្រុស, យុវវ័យ]
                    match = re.search(r'^\[(.*?)\]', raw_text)
                    if match:
                        detected_role = normalize_role_name(match.group(1).strip())
                        clean_text = raw_text.replace(match.group(0), "").strip() # type: ignore
                
                    # ២. កំណត់ពណ៌តាមតួអង្គ (Character Color Assignment)
                    if detected_role not in role_colors:
                        color_idx = len(role_colors) % len(color_palette) # type: ignore
                        role_colors[detected_role] = color_palette[color_idx]

                    current_bg_color = role_colors[detected_role]

                    # Fix: Add to global roles BEFORE setting table row to prevent default to "Male, Child"
                    if detected_role not in self.roles:
                        self.roles.append(detected_role)
                        self._initialize_new_role_config(detected_role)

                    # ៣. បញ្ចូលជួរទិន្នន័យក្នុង Table # type: ignore
                    self.set_table_row(i, sub['start'], sub['end'], detected_role, clean_text)

                    # ៤. អនុវត្តពណ៌លើជួរនីមួយៗ (Apply Row/Widget Coloring)
                    # Check if this role is marked as new and unconfigured
                    is_unconfigured_role = self.role_configs.get(detected_role, {}).get("is_new", False)

                    for col in range(self.segment_table.columnCount()):
                        # ពណ៌លើអត្ថបទធម្មតា
                        table_item = self.segment_table.item(i, col) # type: ignore
                        if table_item: # type: ignore
                            table_item.setBackground(QColor(current_bg_color))
                    
                        # ពណ៌លើ Widget (ComboBox, SpinBox)
                        cell_widget = self.segment_table.cellWidget(i, col)
                        if cell_widget:
                            style = f"background-color: {current_bg_color}; border: none;"
                            # Apply highlight if it's the role column and the role is new
                            if col == 3 and is_unconfigured_role:
                                style = f"background-color: #fff3cd; border: 2px solid #ffc107; font-weight: bold; color: #856404;"
                            cell_widget.setStyleSheet(style)

                    # ៥. ពិនិត្យរកកំហុសពេលវេលា (Timing Error Check)
                    error_tip = ""
                    duration = sub['end'] - sub['start'] # type: ignore
                    if sub['start'] >= sub['end']:
                        error_tip = "⚠️ នាទីបញ្ចប់តូចជាងនាទីចាប់ផ្តើម"
                    elif sub['start'] < prev_end:
                        error_tip = f"⚠️ នាទីជាន់គ្នាជាមួយបន្ទាត់មុន"

                    if error_tip:
                        # បើមានកំហុស ប្រើពណ៌ក្រហមឆ្អៅជំនួសវិញ
                        error_color = "#fed7d7"
                        for col in range(self.segment_table.columnCount()): # type: ignore
                            item = self.segment_table.item(i, col) # type: ignore
                            if item: item.setBackground(QColor(error_color))
                            widget = self.segment_table.cellWidget(i, col)
                            if widget: widget.setStyleSheet(f"background-color: {error_color};")

                    prev_end = sub['end']

                    # ធ្វើឱ្យ UI រស់រវើក (Update Progress)
                    if i % 20 == 0: # type: ignore
                        self.progress.setValue(int((i / total_subs) * 100))
                        QApplication.processEvents()

            finally:
                self.segment_table.setUpdatesEnabled(True) # type: ignore

            # Update main combo box with new roles
            current_voice = self.voice_combo.currentText()
            self.voice_combo.blockSignals(True)
            self._refresh_voice_combo(current_voice)
            self.voice_combo.blockSignals(False)

            self.btn_run_srt.setEnabled(True) # type: ignore
            
            new_roles_count = len(set(self.roles) - existing_roles_before_load)
            summary_msg = f"✅ Table populated. Found {len(role_colors)} characters."
            if new_roles_count > 0:
                summary_msg += f" (Detected {new_roles_count} new characters to configure)"
            self.log(summary_msg)
        
            # Store character information globally for lip-sync and other features
            self.srt_characters = list(role_colors.keys())
            self.character_info = role_colors.copy()
        
            self.progress.setValue(100) # type: ignore

        except Exception as e:
            self.log(f"❌ Error reading SRT: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to parse SRT file.\n{str(e)}")

    def get_offset_ms(self):
        try:
            text = self.time_offset_edit.text()
            if text.strip() == ":  :  ,": return 0
            return self.time_to_ms(text)
        except:
            return 0

    def play_video_segment(self, row: int) -> None:
        try:
            item_start = self.segment_table.item(row, 0)
            item_end = self.segment_table.item(row, 1)
        
            if item_start and item_end:
                start_val = item_start.data(QT_USER_ROLE)
                end_val = item_end.data(QT_USER_ROLE)
            
                if start_val is not None and end_val is not None:
                    offset = self.get_offset_ms()
                
                    # Calculate relative position (ដក Offset ចេញដើម្បីរកម៉ោងក្នុងវីដេអូនេះ)
                    seek_pos = int(start_val) - offset
                    end_pos = int(end_val) - offset
                
                    if seek_pos < 0:
                        if end_pos > 0: # Overlaps start
                            seek_pos = 0
                        else:
                            self.log(f"⚠️ Segment starts before this video (Offset: {self.ms_to_time(offset)})")
                            return

                    self.segment_end_time = end_pos
                    self.media_player.setPosition(seek_pos)
                    self.media_player.play()
        except Exception as e:
            self.log(f"Error playing video segment: {e}") # type: ignore
    def row_action(self, row, action_type): # This method was correctly indented
        # Sync Video to Segment Start
        start_ms = 0
        end_ms = 0
        seek_pos = 0
        try:
            item_start = self.segment_table.item(row, 0)
            item_end = self.segment_table.item(row, 1)
            if item_start and item_end:
                val_start = item_start.data(QT_USER_ROLE)
                val_end = item_end.data(QT_USER_ROLE)
                if val_start is not None and val_end is not None:
                    start_ms = int(val_start)
                    end_ms = int(val_end)
                
                    # Apply Offset (Fix for Test Video/TTS sync)
                    offset = self.get_offset_ms()
                    seek_pos = max(0, start_ms - offset) # type: ignore
                    self.media_player.setPosition(seek_pos)
        except:
            pass # type: ignore
        role_combo = self.segment_table.cellWidget(row, 3)
        role = role_combo.currentText() if role_combo else ""
    
        item_text = self.segment_table.item(row, 4)
        text = item_text.text() if item_text else ""
    
        # Capture values from UI in Main Thread
        speed_val = self.speed_spin.value()
        ffmpeg_bin = self.get_ffmpeg()
    
        global_fade_in = self.fade_in.value()
        global_fade_out = self.fade_out.value()
        output_dir = self.get_output_dir()

        # type: ignore
        self.log(f"Processing Row {row+1} [{action_type}] - Role: {role}") # type: ignore
        self.start_worker_thread(target=self.process_row_action, args=(row, role, text, action_type, seek_pos, speed_val, ffmpeg_bin, global_fade_in, global_fade_out, output_dir, start_ms, end_ms))

    def on_play_audio(self, file_path, start_ms):
        """Play audio preview using pygame"""
        if start_ms >= 0 and self.media_player.state() != MEDIA_PLAYER_PLAYING:
            self.media_player.setPosition(start_ms)
            self.media_player.play() # type: ignore

        # Use pygame for audio preview
        if self.pygame_audio_available: # type: ignore
            try:
                # Stop any currently playing audio
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
            
                # Load and play the audio file
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play() # type: ignore
                self.log(f"🔊 Playing audio preview: {os.path.basename(file_path)}") # type: ignore
            except Exception as e:
                self.log(f"⚠️ Audio playback failed: {e}")
                # Fallback: try QMediaPlayer if pygame fails
                self.log("⚠️ Falling back to QMediaPlayer for audio")
                self.preview_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
                self.preview_player.play()
        else: # type: ignore
            # Fallback to QMediaPlayer if pygame not available
            self.preview_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.preview_player.play()

    def on_preview_state_changed(self, state): # type: ignore
        if state == MEDIA_PLAYER_STOPPED: # type: ignore
            self.media_player.pause() # type: ignore

    def force_stop_player(self) -> None:
        """Stop audio playback (pygame + QMediaPlayer fallback)"""
        # Stop pygame audio
        if self.pygame_audio_available:
            try:
                pygame.mixer.music.stop()
            except:
                pass
    
        # type: ignore
        # Also stop QMediaPlayer (for video)
        self.media_player.pause()

    def process_row_action(self, row: int, role: str, text: str, action_type: str, 
                           seek_pos: int, speed_val: int, ffmpeg_bin: str, 
                           global_fade_in: int, global_fade_out: int, 
                           output_dir: str, seg_start_ms: int, seg_end_ms: int) -> None:
        """Process TTS generation and audio manipulation for a single row in a worker thread."""
        try:
            # Determine temp filename based on action
            timestamp = int(time.time() * 1000)
            auto_fit_enabled = self.chk_auto_fit.isChecked()

            if action_type in ["test_tts"]:
                self.stop_player_signal.emit() # type: ignore
                time.sleep(0.1) # Wait for player to release file handle
                # Clean up old preview files to prevent accumulation # type: ignore
                for f in glob.glob("temp_preview_*"):
                    try:
                        os.remove(f)
                    except (OSError, PermissionError):
                        pass
                # Use unique name to avoid file lock issues
                temp_tts = f"temp_preview_{timestamp}.mp3"
            else:
                temp_tts = f"temp_gen_{row}_{timestamp}.mp3"
        
            working_file = temp_tts

            # type: ignore
            # 1. Get TTS Parameters
            config = self.role_configs.get(role, {})
            speed_offset = speed_val if not auto_fit_enabled else 0
            voice, rate_str, pitch_str = self.get_tts_params(role, speed_offset)

            # Strip literal parentheses (often used for thoughts/actions in drama scripts)
            tts_text = text.replace("(", "").replace(")", "")

            # 2. Generate TTS Temp (thread-safe async)
            self.run_async_in_thread(self.edge_tts_save(tts_text, voice, temp_tts, rate_str, pitch_str))
        
            if self.stop_event.is_set(): return

            # 3. Apply Auto-Fit if enabled
            if auto_fit_enabled and seg_end_ms > seg_start_ms:
                try:
                    segment_audio = self.safe_load_audio(working_file, ffmpeg_bin)
                    target_duration = max(100, (seg_end_ms - seg_start_ms) - 50)
                    current_duration = len(segment_audio)

                    if target_duration > 10 and abs(current_duration - target_duration) > 100: # type: ignore
                        tempo = current_duration / target_duration
                        if tempo < 0.8: tempo = 0.8
                        if tempo > 1.8: tempo = 1.8

                        filter_chain = f"atempo={tempo}"
                        if tempo > 2.0: # Handle higher tempos
                            filter_chain = ""
                            temp_t = tempo
                            while temp_t > 2.0:
                                filter_chain += "atempo=2.0,"
                                temp_t /= 2.0
                            filter_chain += f"atempo={temp_t}"

                        # type: ignore
                        fitted_file = os.path.splitext(working_file)[0] + ".fit.wav"
                        cmd = [ffmpeg_bin, "-y", "-i", working_file, "-filter:a", filter_chain, fitted_file]
                        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)

                        if res.returncode == 0 and os.path.exists(fitted_file):
                            os.remove(working_file) # remove the original mp3
                            working_file = fitted_file
                            self.log(f"   ⚡ Adjusted Row {row+1}: {current_duration}ms -> {len(AudioSegment.from_file(working_file))}ms (Tempo: {tempo:.2f}x)")
                        else:
                            self.log(f"⚠️ Speed adjustment failed for Row {row+1}. Using original. Error: {res.stderr}") # type: ignore
                except Exception as e:
                    self.log(f"⚠️ Auto-fit error for Row {row+1}: {e}")

            # 4. Load processed audio to memory for final touches (Fade/Padding)
            if not os.path.exists(working_file): # type: ignore
                self.log(f"❌ Audio file missing for row {row+1}")
                return
        
            final_segment = self.safe_load_audio(working_file, ffmpeg_bin) # type: ignore

            # Apply Fades (Per Character) in memory
            c_fade_in = config.get("fade_in", -1)
            final_fade_in = c_fade_in if c_fade_in != -1 else global_fade_in
            c_fade_out = config.get("fade_out", -1)
            final_fade_out = c_fade_out if c_fade_out != -1 else global_fade_out
        
            if final_fade_in > 0:
                final_segment = final_segment.fade_in(final_fade_in)
            if final_fade_out > 0:
                final_segment = final_segment.fade_out(final_fade_out)
        
        # type: ignore
            # Add padding to prevent abrupt starts/ends # type: ignore
            pad_ms = 50
            silence = AudioSegment.silent(duration=pad_ms, frame_rate=final_segment.frame_rate)
            final_segment = silence + final_segment + silence

            if action_type == "test_tts":
                final_segment.export(working_file, format="mp3")
                self.play_audio_signal.emit(os.path.abspath(working_file), seek_pos) # type: ignore
        
            elif action_type == "gen_tts":
                output_file_path = os.path.join(output_dir, f"row_{row+1}_tts.wav")
                final_segment.export(output_file_path, format="wav")
                self.log(f"✅ Saved: {output_file_path}")
                if os.path.exists(working_file):
                    os.remove(working_file)
            
        except Exception as e:
            self.log(f"❌ Error in Row Action: {e}")
            traceback.print_exc() # type: ignore

    def get_active_segments(self) -> list[dict[str, Union[str, int]]]:
        segments = self.get_segments_from_table()
        if not segments: return []

        offset = self.get_offset_ms()

        if offset > 0:
            adjusted_segments = []
            for seg in segments:
                # Skip segments that end before the video starts
                if seg['end'] <= offset: continue # type: ignore
                seg['start'] = max(0, seg['start'] - offset)
                seg['end'] = max(0, seg['end'] - offset)
                adjusted_segments.append(seg)
            return adjusted_segments
        return segments

    def get_segments_from_table(self) -> list[dict[str, Any]]:
        rows = self.segment_table.rowCount() # type: ignore
        segments = []
        global_speed = self.speed_spin.value()
        global_fade_in = self.fade_in.value()
        global_fade_out = self.fade_out.value()
    
        for r in range(rows):
            # Start/End
            item_start = self.segment_table.item(r, 0)
            start_val = item_start.data(QT_USER_ROLE) if item_start else None # type: ignore
            start_ms = int(start_val) if start_val is not None else 0
        
            item_end = self.segment_table.item(r, 1) # type: ignore
            end_val = item_end.data(QT_USER_ROLE) if item_end else None
            end_ms = int(end_val) if end_val is not None else 0
        
            # Role & Text # type: ignore
            combo = self.segment_table.cellWidget(r, 3)
            role = combo.currentText() if combo else ""
        
            item_text = self.segment_table.item(r, 4)
            text = item_text.text() if item_text else ""
        
            # Fix: If Auto-Fit is checked, ignore global speed to ensure accurate base duration
            # (ជួសជុល៖ បើប្រើ Auto-Fit ត្រូវបិទ Global Speed ដើម្បីអោយការគណនារយៈពេលត្រឹមត្រូវ)
            speed_offset = global_speed if not self.chk_auto_fit.isChecked() else 0
            voice, rate_str, pitch_str = self.get_tts_params(role, speed_offset)

            # Resolve Fade
            config = self.role_configs.get(role, {})
            c_fade_in = config.get("fade_in", -1)
            final_fade_in = c_fade_in if c_fade_in != -1 else global_fade_in
        
            c_fade_out = config.get("fade_out", -1) # type: ignore
            final_fade_out = c_fade_out if c_fade_out != -1 else global_fade_out

            segments.append({
                "text": text,
                "voice": voice,
                "rate": rate_str,
                "pitch": pitch_str,
                "start": start_ms,
                "end": end_ms,
                "fade_in": final_fade_in,
                "fade_out": final_fade_out
            })
        return segments

    async def batch_generate_tts(self, tasks: list[tuple[str, str, str, str, str]]) -> None:
        # Edge TTS has strict rate limits, especially for batch exports # type: ignore
        max_concurrent = min(3, max(1, len(tasks) // 10))  # Dynamic: 1-3 based on task count
        semaphore = asyncio.Semaphore(max_concurrent)

        self.log(f"🔧 Using {max_concurrent} concurrent TTS workers (rate-limited)")

        async def worker(task):
            if self.stop_event.is_set(): return
            text, voice, filename, rate, pitch = task
            # Add jitter to prevent thundering herd
            await asyncio.sleep(random.uniform(0.5, 2.0)) # type: ignore
            async with semaphore:
                retries = 5
                for attempt in range(retries):
                    try: # type: ignore
                        if self.stop_event.is_set(): return
                        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                        await communicate.save(filename)
                        # Fix Bug #14: Increase delay after success to respect rate limits
                        await asyncio.sleep(random.uniform(0.5, 1.5)) # type: ignore
                        return
                    except Exception as e:
                        if attempt < retries - 1:
                            # Exponential backoff + jitter
                            wait_time = (2 ** attempt) + random.uniform(2, 5)
                            self.log(f"⚠️ Retry {attempt+1}/{retries} for {filename} due to: {e}. Waiting {wait_time:.2f}s")
                            await asyncio.sleep(wait_time)
                        else:
                            self.log(f"❌ Error gen {filename}: {e}")

        await asyncio.gather(*(worker(t) for t in tasks))

    def safe_load_audio(self, filepath: str, ffmpeg_bin: str) -> AudioSegment: # type: ignore
        """
        Safely load audio by converting to WAV first using FFmpeg CLI.
        This prevents Pydub/Minimpal from cutting off the start of MP3s.
        (បម្លែងទៅ WAV ជាមុនសិន ដើម្បីការពារកុំឱ្យបាត់សំឡេងដើម)
        """
        try:
            # If it's MP3, convert to WAV first
            if filepath.lower().endswith(".mp3"):
                wav_path = filepath + ".temp.wav"
                cmd = [ffmpeg_bin, "-y", "-i", filepath, "-acodec", "pcm_s16le", "-ar", "44100", wav_path]
            
                # Run FFmpeg
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, 
                               creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            
                if os.path.exists(wav_path):
                    # Check if file is valid (not empty)
                    if os.path.getsize(wav_path) > 1024: # Increased check to 1KB to avoid headers-only wav
                        audio = AudioSegment.from_file(wav_path)
                        try: os.remove(wav_path)
                        except: pass
                        return audio
        
            # Fallback or if not MP3
            return AudioSegment.from_file(filepath)
        except Exception as e:
            self.log(f"⚠️ Error safe loading audio: {e}") # type: ignore
            return AudioSegment.from_file(filepath) # Last resort
            return AudioSegment.from_file(filepath)

    def clear_cache(self) -> None:
        """
        Clears temporary files and forces garbage collection to free up RAM.
        Frees temporary files and RAM.
        """
        # Fix Bug #17: Stop pygame audio before deleting files to prevent PermissionError # type: ignore
        try: # type: ignore
            if getattr(self, 'pygame_audio_available', False) and pygame.mixer.get_init():
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                    time.sleep(0.2)  # Wait for file handle to release
        except:
            pass
    
        # 1. Force Garbage Collection
        gc.collect() # type: ignore
        collected = gc.collect()

        # 2. Remove temp files (Fix Bug #17: Skip files in use)
        patterns = ["temp_*.mp3", "temp_*.wav", "*.temp.wav"]
        removed_count = 0
        failed_count = 0
        for pattern in patterns:
            for f in glob.glob(pattern):
                try:
                    # Fix Bug #17: Check if file is in use by trying to open it first # type: ignore
                    os.remove(f)
                    removed_count += 1
                except PermissionError:
                    # File is still in use (e.g., by pygame or OS), skip silently # type: ignore
                    failed_count += 1
                except:
                    pass
    
        # Log result (បង្ហាញលទ្ធផលសម្អាត)
        if collected > 0 or removed_count > 0: # type: ignore
            if failed_count > 0:
                self.log(f"🧹 System Cleaned: {removed_count} temp files removed, {failed_count} skipped (in use), RAM freed (GC: {collected})")
            else:
                self.log(f"🧹 System Cleaned: {removed_count} temp files removed, RAM freed (GC: {collected})")

    # type: ignore
    def clear_cache_manual(self) -> None:
        self.clear_cache()
        QMessageBox.information(self, "Success", "Cache and RAM cleared successfully!\n(សម្អាតរួចរាល់)")

    def run_srt_conversion(self) -> None:
        self.clear_cache() # Clean before starting
        segments = self.get_active_segments()
        if not segments:
            QMessageBox.warning(self, "Warning", "No segments to process! (Check Table or Offset)")
            return

        self.log(f"Processing {len(segments)} segments from table...")
        self.stop_event.clear()
        self.btn_run_srt.setEnabled(False) # type: ignore
        self.btn_srt.setEnabled(False)
        self.btn_stop_srt.setEnabled(True)
    
        ffmpeg_bin = self.get_ffmpeg()
        auto_fit = self.chk_auto_fit.isChecked()
    
        fade_in = self.fade_in.value()
        fade_out = self.fade_out.value()
    
        # Default to WAV/High for run button
        # Save to Output folder so Export MP4 can find it
        output_dir = self.get_output_dir()
        output_file = os.path.join(output_dir, "srt_output.wav")
    
        self.start_worker_thread(target=self.run_srt_thread, args=(segments, ffmpeg_bin, output_file, 0, auto_fit, fade_in, fade_out))

    def run_srt_thread(self, segments: list[dict[str, Any]], ffmpeg_bin: str, output_file: str = "srt_output.wav", quality_idx: int = 0, auto_fit: bool = True, fade_in: int = 0, fade_out: int = 0, auto_play: bool = True, emit_signal: bool = True) -> None:
        try:
            # Configure FFmpeg for Pydub
            self._configure_audio_converter(ffmpeg_bin)
        
            # 1. Prepare Tasks
            if not segments: return # type: ignore
        
        # type: ignore
            # Sort segments by time internally to ensure correct audio assembly order
            # (រៀបចំតាមលំដាប់ម៉ោងដោយស្វ័យប្រវត្តិនៅផ្ទៃខាងក្រោយ ដើម្បីកុំអោយបាត់សំឡេងពេលផ្គុំ)
            segments.sort(key=lambda x: x['start'])
        
            tasks = []
            temp_map = [] # (index, filename, start_ms)
            segments_map = {} # Store segment info for duration check
        
            for i, seg in enumerate(segments):
                text = seg['text']
                if not text or not text.strip(): continue
            
                temp_file = f"temp_{i}.mp3"
                tasks.append((text, seg['voice'], temp_file, seg['rate'], seg['pitch'])) # type: ignore
                temp_map.append((i, temp_file, seg['start']))
                segments_map[i] = seg

            if self.stop_event.is_set(): return

            # 2. Run Async Generation (Parallel) - លឿនជាងមុន
            self.log(f"🚀 Generating {len(tasks)} segments in parallel...") # type: ignore
            self.run_async_in_thread(self.batch_generate_tts(tasks))
        
            if self.stop_event.is_set():
                self.log("🛑 Process stopped by user.")
                return

            # 3. Assemble Audio
            self.log("🧩 Assembling audio tracks...") # type: ignore
            max_end = max(s['end'] for s in segments) # type: ignore
            total_duration = max_end + 3000 # +3s buffer
        
            # FIX: Detect frame rate to prevent low-quality downsampling (11kHz bug)
            # កំណត់ Frame Rate ឱ្យត្រូវនឹងសំឡេងដើម (44100Hz) ដើម្បីកុំឱ្យសំឡេងខូចគុណភាព
            target_rate = 44100
            for _, t_file, _ in temp_map:
                if os.path.exists(t_file): # type: ignore
                    try: # type: ignore
                        probe = self.safe_load_audio(t_file, ffmpeg_bin)
                        target_rate = probe.frame_rate
                        if probe.frame_rate > 16000: # Only accept high quality rates
                            target_rate = probe.frame_rate
                        break
                    except: pass
        
            final_audio = AudioSegment.silent(duration=total_duration, frame_rate=target_rate) # type: ignore
        
        # type: ignore
            for i, temp_file, start_ms in temp_map:
                if self.stop_event.is_set(): break

                if os.path.exists(temp_file): # type: ignore
                    try:
                        if os.path.getsize(temp_file) < 100:
                            self.log(f"⚠️ Segment {i+1} skipped: File too small/empty.")
                            continue
                        
                        # type: ignore
                        segment = self.safe_load_audio(temp_file, ffmpeg_bin)
                        
                        # --- Auto-Fit Duration Logic (កែសម្រួលល្បឿនតាមម៉ោង) --- # type: ignore
                        seg_info = segments_map.get(i)
                        if auto_fit and seg_info:
                            # Reduce target duration slightly to ensure audio doesn't bleed into next segment
                            # កាត់បន្ថយរយៈពេលគោលដៅ ៥០ms ដើម្បីទុកចន្លោះកុំអោយប៉ះគ្នាជាមួយឃ្លាបន្ទាប់
                            target_duration = max(100, (seg_info['end'] - seg_info['start']) - 50)
                            current_duration = len(segment)
                        
                            # ប្រសិនបើ Duration ខុសគ្នាខ្លាំង (> 100ms) ត្រូវកែសម្រួល (Prevent div by zero) # type: ignore
                            if target_duration > 10 and abs(current_duration - target_duration) > 100:
                                # Calculate Tempo (Speed Factor)
                                # tempo > 1.0 = លឿន (Speed Up)
                                # tempo < 1.0 = យឺត (Slow Down)
                                tempo = current_duration / target_duration
                            
                                # Clamp tempo to a reasonable range
                                if tempo < 0.8: tempo = 0.8 # type: ignore
                            
                                # Allow aggressive speedup to prevent overlaps (up to 5x)
                                # អនុញ្ញាតឱ្យលឿនខ្លាំងរហូតដល់ ៥ ដង ដើម្បីឱ្យចូលស៊ុមទោះបីអត្ថបទវែងក៏ដោយ
                                max_tempo = 1.8

                                # Only apply safety caps if the required speed is low
                                # ប្រសិនបើសំឡេងត្រូវការលឿនតិចតួច យើងអាចកំណត់កុំឱ្យលឿនពេកបាន
                                # ប៉ុន្តែបើវាវែងពេក យើងត្រូវបង្ខំឱ្យលឿន
                                if target_duration < 1000 and tempo < 1.5:
                                    max_tempo = 1.2
                                
                                # type: ignore
                                if tempo > max_tempo: tempo = max_tempo

                                # ប្រើ FFmpeg atempo filter ដើម្បីប្តូរល្បឿន
                                # atempo ទទួលតម្លៃពី 0.5 ដល់ 2.0។ បើលើសនេះត្រូវដាក់តគ្នា។
                                filter_chain = ""
                                temp_t = tempo
                                while temp_t > 2.0:
                                    filter_chain += "atempo=2.0,"
                                    temp_t /= 2.0
                                while temp_t < 0.5:
                                    filter_chain += "atempo=0.5,"
                                    temp_t /= 0.5
                                filter_chain += f"atempo={temp_t}" # type: ignore
                            
                                processed_file = f"temp_fit_{i}.wav"
                                cmd = [ffmpeg_bin, "-y", "-i", temp_file, "-filter:a", filter_chain, processed_file]
                                # Capture stderr to log if it fails
                                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
                            
                                if res.returncode == 0 and os.path.exists(processed_file): # type: ignore
                                    segment = AudioSegment.from_file(processed_file) # type: ignore
                                    os.remove(processed_file)
                                    self.log(f"   ⚡ Adjusted Seg {i+1}: {current_duration}ms -> {len(segment)}ms (Target: {target_duration}ms)")
                                else:
                                    self.log(f"⚠️ Speed adjustment failed for Seg {i+1}. Using original. Error: {res.stderr}")
                    
                        # Apply Fades
                        seg_fade_in = seg_info.get('fade_in', fade_in) if seg_info else fade_in # type: ignore
                        seg_fade_out = seg_info.get('fade_out', fade_out) if seg_info else fade_out # type: ignore
                    
                        # Apply Fades FIRST (Fade លើសំឡេងជាមុនសិន)
                        if seg_fade_in > 0:
                            segment = segment.fade_in(seg_fade_in)
                        if seg_fade_out > 0:
                            segment = segment.fade_out(seg_fade_out)

                        # THEN Add fixed silence padding (បន្ទាប់មកទើបបន្ថែម Silence ការពារដាច់)
                        pad_ms = 50
                        silence = AudioSegment.silent(duration=pad_ms, frame_rate=segment.frame_rate)
                        segment = silence + segment + silence
                    
                        # Adjust position to compensate for padding (កែសម្រួលម៉ោងវិញ)
                        adj_start = max(0, start_ms - pad_ms)
                        final_audio = final_audio.overlay(segment, position=adj_start)
                        os.remove(temp_file)
                    except Exception as e: # type: ignore
                        self.log(f"⚠️ Error overlaying segment {i}: {e}")
                else:
                    self.log(f"⚠️ Segment {i+1} missing: Audio generation failed.")
            
                progress = int((i + 1) / len(segments) * 100)
                self.progress_signal.emit(progress)

            if self.stop_event.is_set():
                self.log("🛑 Process stopped. Audio not saved.") # type: ignore
                return

            # 4. Export with Quality # type: ignore
            fmt = "wav"
            bitrate = None
        
            # Determine format based on filename extension or quality selection
            if output_file.lower().endswith(".mp3"):
                fmt = "mp3"
                if quality_idx == 1: bitrate = "320k"
                elif quality_idx == 2: bitrate = "192k"
                elif quality_idx == 3: bitrate = "128k"
                else: bitrate = "320k"
        
            self.log(f"💾 Saving to {output_file} (Format: {fmt}, Bitrate: {bitrate})...") # type: ignore
            final_audio.export(output_file, format=fmt, bitrate=bitrate) # type: ignore
        
            self.last_generated_audio = output_file # រក្សាទុកឈ្មោះ File សម្រាប់ Export Video
        
            self.log(f"✅ SRT Audio Generated: {output_file}")
            if auto_play and sys.platform == "win32":
                self.log("⏳ Opening player...")
                time.sleep(2.0) # Wait longer for slower disks
                self.open_file_or_folder(output_file)
        except Exception as e:
            self.log(f"❌ SRT Error: {str(e)}")
        finally: # type: ignore
            # type: ignore
            # Fix Bug #11: Only emit signal when not called from auto-export
            if emit_signal:
                self.srt_finished_signal.emit()
            self.clear_cache() # Clean after finishing

    def parse_srt(self, filepath: str) -> list[dict[str, Any]]:
        parsed = [] # type: ignore
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f: # type: ignore
                lines = [line.rstrip("\n\r") for line in f]

        except Exception:
            return []

        def get_arrow(line: str) -> Optional[str]:
            if "-->" in line:
                return "-->"
            if "->" in line:
                return "->"
            if "--&gt;" in line:
                return "--&gt;"
            return None

        def is_time_line(line: str) -> bool:
            arrow = get_arrow(line)
            return bool(arrow and any(c.isdigit() for c in line) and ":" in line)

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            if line.upper().startswith("WEBVTT") or line.startswith(("STYLE", "REGION")):
                i += 1
                continue

            # Skip WEBVTT comment blocks without deleting following subtitles.
            if line.upper().startswith("NOTE"): # type: ignore
                i += 1
                while i < len(lines) and lines[i].strip():
                    i += 1
                continue # type: ignore

            arrow = get_arrow(line)
            if is_time_line(line): # type: ignore
                try: # type: ignore
                    subtitle_number = None
                    if i > 0 and lines[i - 1].strip().isdigit():
                        subtitle_number = int(lines[i - 1].strip())
                    # Split and clean whitespace (Fix for loose formatting)
                    parts = line.split(arrow)
                    start_ms = self.time_to_ms(parts[0].strip())
                    end_ms = self.time_to_ms(parts[1].strip())
                except:
                    i += 1
                    continue
            
                # Parse Text (Consume lines until next block start) # type: ignore
                j = i + 1
                text_parts = []
                while j < len(lines):
                    next_line = lines[j].strip()

                    if not next_line:
                        j += 1
                        break

                    # Fix Bug #16: Skip WEBVTT comment markers in text
                    if next_line.upper().startswith("NOTE"):
                        j += 1 # type: ignore
                        while j < len(lines) and lines[j].strip(): # type: ignore
                            j += 1
                        continue

                    # Check if next_line is start of new block
                    # 1. Index + Time (Standard)
                    if next_line.isdigit() and (j + 1 < len(lines)):
                        nl_arrow = get_arrow(lines[j+1]) # type: ignore

                        if nl_arrow:
                            break

                    # 2. Just Time (Missing Index)
                    if is_time_line(next_line):
                         break

                    text_parts.append(next_line)
                    j += 1
            
                text = " ".join(text_parts) # type: ignore
                parsed.append({'number': subtitle_number, 'start': start_ms, 'end': end_ms, 'text': text})
                i = j
            else: # type: ignore
                # Skip index lines or garbage # type: ignore
                i += 1
            
        return parsed

    def ms_to_time(self, ms):
        # Fix Bug #31: Handle values exceeding 99 hours
        if ms < 0: # type: ignore
            ms = 0
        seconds = (ms // 1000) % 60
        minutes = (ms // (1000 * 60)) % 60
        hours = (ms // (1000 * 60 * 60))
        millis = ms % 1000
    
        # SRT format supports up to 99 hours, wrap if exceeded
        if hours > 99:
            self.safe_log(f"⚠️ Duration exceeds 99 hours ({hours}h), wrapping to {(hours % 100)}h")
            hours = hours % 100

        # type: ignore
        return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"
    def time_to_ms(self, time_str: str) -> int:
        try: # type: ignore
            # Fix Bug #12: Stricter validation to reject malformed times
            time_str = time_str.strip()
            if not time_str:
                return 0

            # Match SRT time format: HH:MM:SS,mmm or MM:SS,mmm
            # Accept BOTH comma (,) and period (.) as valid separators
            match = re.match(r'^(?:(\d{1,2}):)?(\d{2}):(\d{2})[,.](\d{1,3})$', time_str)
            if match: # type: ignore
                h_str, m_str, s_str, ms_str = match.groups()
                h = int(h_str) if h_str else 0
                m, s = int(m_str), int(s_str)
                ms = int(ms_str.ljust(3, '0')[:3])
            
                # Validate ranges
                if m > 59 or s > 59:
                    self.safe_log(f"⚠️ Invalid time format: {time_str} (minutes/seconds out of range)")
                    return 0

                return h * 3600000 + m * 60000 + s * 1000 + ms

            # Fallback to old regex for unusual formats
            match_old = re.search(r'(\d+:)*\d+:\d+([,.]\d+)?', time_str)
            if match_old:
                clean = match_old.group(0).replace('.', ',')
                ms = 0
                if ',' in clean:
                    t_part, ms_part = clean.split(',')
                    ms_str = ms_part.ljust(3, '0')[:3]
                    ms = int(ms_str)
                else:
                    t_part = clean

                parts = list(map(int, t_part.split(':')))
                if len(parts) == 3:  # HH:MM:SS
                    return parts[0] * 3600000 + parts[1] * 60000 + parts[2] * 1000 + ms
                elif len(parts) == 2:  # MM:SS
                    return parts[0] * 60000 + parts[1] * 1000 + ms

            return 0
        except Exception as e:
            self.safe_log(f"⚠️ Error parsing time '{time_str}': {e}")
            return 0

    def run_async_in_thread(self, coro: Any) -> Any:
        """
        Use this instead of asyncio.run() when calling async functions from threading.Thread.
        Each thread gets its own isolated event loop.
        """
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro) # type: ignore
        finally:
            loop.close()
            try:
                asyncio.set_event_loop(None)
            except:
                pass

    def run_tts_thread(self, text: str, voice: str, rate: str, pitch: str, fade_in: int, fade_out: int, ffmpeg_bin: str, output_file: str, auto_play: bool) -> None: # type: ignore
            # Use temp file for download (Edge TTS is MP3)
            temp_file = "temp_tts.mp3"
            try:
                # Run the async function safely in thread
                self.run_async_in_thread(self.edge_tts_save(text, voice, temp_file, rate, pitch))
        
                # Configure ffmpeg for pydub
                self._configure_audio_converter(ffmpeg_bin)

                # Load audio
                audio = self.safe_load_audio(temp_file, ffmpeg_bin)

                # Apply Fades FIRST
                if fade_in > 0:
                    audio = audio.fade_in(fade_in)
                if fade_out > 0:
                    audio = audio.fade_out(fade_out)
        
                # THEN Add fixed silence padding # type: ignore
                pad_ms = 50 # type: ignore
                silence = AudioSegment.silent(duration=pad_ms, frame_rate=audio.frame_rate)
                audio = silence + audio + silence
        
                # Export
                fmt = "wav" if output_file.lower().endswith(".wav") else "mp3"
                audio.export(output_file, format=fmt)
        
                # Cleanup
                if os.path.exists(temp_file):
                    os.remove(temp_file)

                self.log(f"✅ Success! Saved to: {output_file}")
                self.tts_finished_signal.emit()

                # Play the audio automatically (Windows only)
                if auto_play and sys.platform == "win32":
                    self.log("⏳ Opening player...")
                    time.sleep(2.0) # Wait longer for slower disks # type: ignore
                    self.open_file_or_folder(output_file)
        
            except Exception as e: # type: ignore
                self.log(f"❌ Error: {str(e)}")
                self.tts_finished_signal.emit()
            finally:
                pass # Handled by signal

    def process_audio_fades(self, filepath: str, fade_in: int, fade_out: int, ffmpeg_bin: str) -> None:
        try: # type: ignore
            # Configure ffmpeg for pydub if path is set
            self._configure_audio_converter(ffmpeg_bin)

            # ប្រើ safe_load_audio ដើម្បីការពារការដាច់ក្បាលសំឡេង # type: ignore
            audio = self.safe_load_audio(filepath, ffmpeg_bin)

            # Apply Fades FIRST
            if fade_in > 0:
                audio = audio.fade_in(fade_in)
            if fade_out > 0:
                audio = audio.fade_out(fade_out)

            # THEN Add fixed silence padding
            pad_ms = 50
            silence = AudioSegment.silent(duration=pad_ms, frame_rate=audio.frame_rate)
            audio = silence + audio + silence

            # Determine format
            fmt = "wav" if filepath.lower().endswith(".wav") else "mp3"

            # Fix Bug #7: Export to temp file first to avoid file lock issues on Windows # type: ignore
            temp_path = filepath + ".fade_temp"
            audio.export(temp_path, format=fmt)

            # Replace original file only after export completes
            if os.path.exists(filepath):
                os.remove(filepath)  # Remove original to prevent lock
            os.rename(temp_path, filepath) # type: ignore

            if fade_in > 0 or fade_out > 0:
                self.log(f"✨ Applied Fade In: {fade_in}ms, Fade Out: {fade_out}ms")
        except Exception as e: # type: ignore
            self.log(f"⚠️ Fade Error: {str(e)} (Check FFmpeg path)")

    async def edge_tts_save(self, text: str, voice: str, filename: str, rate: str, pitch: str) -> None:
        retries = 5
        for attempt in range(retries):
            try:
                communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                await communicate.save(filename)
                return
            except Exception as e: # type: ignore
                if attempt < retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(1, 3)
                    self.log(f"⚠️ Retry {attempt+1}/{retries} for single TTS due to: {e}. Waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    continue
                raise e
    def export_wav(self) -> None: # type: ignore
        segments = self.get_active_segments()
        if not segments:
            self.log("⚠️ Warning: All segments were filtered out! Check your Video Offset or Duration.")
            QMessageBox.warning(self, "Warning", "No segments to export! (Check Table or Offset)") # type: ignore
            return

        quality_idx = self.combo_quality.currentIndex()
        ext = ".wav" if quality_idx == 0 else ".mp3"
        file_filter = "WAV Files (*.wav)" if quality_idx == 0 else "MP3 Files (*.mp3)"

        out_path = ""
        if self.output_folder is not None:
            out_path = self.output_folder.text() if hasattr(self.output_folder, 'text') else str(self.output_folder)
        last_dir = out_path or self.app_settings.get("last_output_dir", "") # type: ignore
        output_file, _ = QFileDialog.getSaveFileName(self, "Export Audio", os.path.join(last_dir, f"Full_TTS_Export{ext}"), file_filter)

        if not output_file:
            return

        self.log(f"Exporting Full TTS to {output_file}...")
        self.btn_export_wav.setEnabled(False)

        ffmpeg_bin = self.get_ffmpeg()
        auto_fit = self.chk_auto_fit.isChecked()

        fade_in = self.fade_in.value()
        fade_out = self.fade_out.value()

        self.start_worker_thread(target=self.run_srt_thread, args=(segments, ffmpeg_bin, output_file, quality_idx, auto_fit, fade_in, fade_out))

    def run_auto_export_thread(self, video_path: str, output_video_file: str, segments: list[dict[str, Any]], ffmpeg_bin: str, video_settings: dict[str, Any], audio_settings: dict[str, Any]) -> None:
        # Temp audio path
        temp_audio = os.path.join(self.get_output_dir(), "temp_auto_export.wav")

        self.log("🔄 Step 1/2: Auto-generating Audio (SRT to WAV)...")

        # Fix Bug #11: Disable signal emission during auto-export to prevent premature UI re-enable
        self.run_srt_thread(segments, ffmpeg_bin, temp_audio, quality_idx=0,
                            auto_fit=audio_settings['auto_fit'],
                            fade_in=audio_settings['fade_in'],
                            fade_out=audio_settings['fade_out'],
                            auto_play=False, # type: ignore
                            emit_signal=False) # type: ignore
                    
        if not os.path.exists(temp_audio):
            self.log("❌ Auto-generation failed. Stopping export.")
            self.export_finished_signal.emit()
            return
    
        self.log(f"✅ Audio Ready: {os.path.basename(temp_audio)}")
        self.log("🔄 Step 2/2: Rendering Video...")

        self.run_export_mp4_thread(video_path, temp_audio, output_video_file, ffmpeg_bin, video_settings)

        try: os.remove(temp_audio)
        except: pass

        # Fix Bug #11: Emit signals only after entire auto-export completes
        self.srt_finished_signal.emit()
        self.export_finished_signal.emit()

    def preview_video_effects(self) -> None:
        self.export_mp4(preview=True)
    def apply_lip_sync(self, video_path: str, audio_path: str, output_path: str, character_info: Optional[dict[str, str]] = None) -> bool:
        """
        Apply lip-sync to video using SRT-detected character information.
        This is a placeholder for lip-sync functionality that can be extended with AI models.

        Args: # type: ignore
            video_path: Path to input video
            audio_path: Path to audio file
            output_path: Path to output video
            character_info: Dictionary of character -> color mapping from SRT detection
        """ # type: ignore
        if not character_info:
            character_info = self.character_info
    
        # type: ignore
        self.log("🎭 Starting Lip-Sync with SRT Character Detection...")
        self.log(f"📋 Detected Characters: {', '.join(character_info.keys()) if character_info else 'None'}")

        # Placeholder for lip-sync implementation
        # This could integrate with tools like Wav2Lip, Faceswap, or other AI lip-sync solutions
        # For now, just copy the video (no actual lip-sync processing)

        import shutil
        try:
            shutil.copy2(video_path, output_path)
            self.log(f"✅ Lip-Sync placeholder applied. Output: {output_path}")
            self.log("💡 To implement real lip-sync, integrate with AI models like Wav2Lip")
    
            # Log character information for potential use by lip-sync tools
            if character_info:
                self.log("🎭 Character Information for Lip-Sync:")
                for char, color in character_info.items():
                    self.log(f"   • {char}: {color}")
            
            # type: ignore
        except Exception as e:
            self.log(f"❌ Lip-Sync failed: {e}")
            return False

        return True
    def export_mp4(self, preview: bool = False) -> None: # type: ignore
        # 1. Check Prerequisites # type: ignore
        video_path = ""
        if self.media_player.media().canonicalUrl().isLocalFile(): # type: ignore
            video_path = self.media_player.media().canonicalUrl().toLocalFile()
    
        if not video_path or not os.path.exists(video_path):
            QMessageBox.warning(self, "Error", "No video loaded!")
            return
    
        if preview: # type: ignore
            tts_audio = self.get_latest_audio_source()
            if not tts_audio:
                QMessageBox.warning(self, "Warning", "TTS Audio not found!\nFor preview, please Generate Audio first.") # type: ignore
                return
            self.log(f"ℹ️ Using audio source: {os.path.basename(tts_audio)} (Latest generated)")
        else:
            tts_audio = None

        output_dir = self.get_output_dir()

        if preview:
            output_file = os.path.join(output_dir, "Preview_Video.mp4")
        else:
            last_dir = output_dir or self.app_settings.get("last_output_dir", "")
            output_file, _ = QFileDialog.getSaveFileName(self, "Export Video", os.path.join(last_dir, "Final_Video_Export.mp4"), "Video Files (*.mp4)")
    
            if not output_file:
                return

        ffmpeg_bin = self.get_ffmpeg()

        mode_str = "Preview" if preview else "Export"
        self.log(f"🎬 Starting Professional Video {mode_str}...")
        self.btn_export_mp4.setEnabled(False)

        # 2. Gather Settings
        crop_top = self.sb_crop_top.value() if self.sb_crop_top is not None else 0
        crop_bottom = self.sb_crop_bottom.value() if self.sb_crop_bottom is not None else 0
        crop_left = self.sb_crop_left.value() if self.sb_crop_left is not None else 0
        crop_right = self.sb_crop_right.value() if self.sb_crop_right is not None else 0

        settings = {
            "resolution": self.cb_resolution.currentText(),
            "preset": self.cb_preset.currentText(),
            "crf": self.sb_crf.value(), # type: ignore
            "crop_preset": self.cb_crop_preset.currentText(), # type: ignore
            "orig_vol": self.slider_orig_vol.value() / 100.0,
            "brightness": self.sb_brightness.value(),
            "contrast": self.sb_contrast.value(),
            "saturation": self.sb_saturation.value(),
            "crop": (crop_top, crop_bottom, crop_left, crop_right),
            "preview": preview,
            "auto_play": self.chk_autoplay.isChecked(), # បញ្ជូនតម្លៃ Auto Play ទៅ Thread
            "use_gpu": self.chk_gpu.isChecked(),
            "remove_vocals": self.chk_remove_vocals.isChecked(),
            "enable_lip_sync": self.chk_lip_sync.isChecked() if hasattr(self, 'chk_lip_sync') else False,
            "cut_enabled": self.chk_cut.isChecked(),
            "cut_start": self.txt_start.text(), # type: ignore
            "cut_end": self.txt_end.text()
        }

        self.app_settings["remove_vocals"] = self.chk_remove_vocals.isChecked() # type: ignore
        self.save_app_settings()

        if preview:
            self.start_worker_thread(target=self.run_export_mp4_thread, args=(video_path, tts_audio, output_file, ffmpeg_bin, settings)) # type: ignore
        else:
            segments = self.get_active_segments()
            if not segments:
                QMessageBox.warning(self, "Warning", "No segments found to export!")
                self.btn_export_mp4.setEnabled(True)
                return

            # Save the output directory for future use
            output_dir = os.path.dirname(output_file)
            if output_dir:
                self.app_settings["last_output_dir"] = output_dir
                self.save_app_settings()

            audio_settings = {
                "auto_fit": self.chk_auto_fit.isChecked(),
                "fade_in": self.fade_in.value(),
                "fade_out": self.fade_out.value()
            }
            self.start_worker_thread(target=self.run_auto_export_thread, # type: ignore
                                     args=(video_path, output_file, segments, ffmpeg_bin, settings, audio_settings)) # type: ignore

    def run_export_mp4_thread(self, video_path: str, tts_audio: str, output_file: str, ffmpeg_bin: str, s: dict[str, Any]) -> None: # type: ignore
        try: # type: ignore
            # Build Filter Complex
            # 1. Crop
            top, btm, left, right = s['crop'] # type: ignore
    
            # 3. Scale (Resolution)
            res_map = {"1920x1080": "1920:1080", "1280x720": "1280:720", "720x480": "720:480", "3840x2160": "3840:2160"}
            target_res = next((v for k, v in res_map.items() if k in s['resolution']), None)

            # Construct command list
            cmd = [ffmpeg_bin, "-y", "-i", video_path, "-i", tts_audio]
    
            # Filter Complex String
            fc = []
            # Video Stream Chain: [0:v] -> [v1] -> [v2] ...
            last_v = "0:v"
    
            # Crop
            if s['crop_preset'] == "Custom":
                if top > 0 or btm > 0 or left > 0 or right > 0:
                    fc.append(f"[{last_v}]crop=in_w-{left}-{right}:in_h-{top}-{btm}:{left}:{top}[v_crop]")
                    last_v = "v_crop"
            else:
                # Presets (Assuming Landscape Input)
                preset_map = {
                    "9:16 (TikTok/Reels)": "crop=h=ih:w=ih*9/16:x=(iw-ow)/2:y=0",
                    "1:1 (Square)": "crop=h=ih:w=ih:x=(iw-ow)/2:y=0",
                    "4:5 (Facebook)": "crop=h=ih:w=ih*4/5:x=(iw-ow)/2:y=0",
                } # type: ignore
                if s['crop_preset'] in preset_map: # type: ignore
                    fc.append(f"[{last_v}]{preset_map[s['crop_preset']]}[v_crop]")
                    last_v = "v_crop"
    
            # Color
            if s['brightness'] != 0 or s['contrast'] != 1 or s['saturation'] != 1:
                fc.append(f"[{last_v}]eq=brightness={s['brightness']}:contrast={s['contrast']}:saturation={s['saturation']}[v_color]")
                last_v = "v_color"
        
            # Scale
            if target_res:
                fc.append(f"[{last_v}]scale={target_res}[v_scale]")
                last_v = "v_scale"
        
            # Add setpts to reset video timestamp to 0, fixing sync issues with videos that don't start at 0.
            fc.append(f"[{last_v}]setpts=PTS-STARTPTS[v_final]") # type: ignore
    
            # Audio Mixing: [0:a] (vol adjusted) + [1:a] -> [a_out]
            vol = s['orig_vol']
    
            # Check for audio stream before trying to map [0:a]
            has_audio = self.has_audio_stream(video_path)
            if not has_audio and vol > 0:
                self.log(f"⚠️ Warning: Input video has no audio stream. Ignoring 'Original Audio Vol'.")

            if vol > 0 and has_audio:
                if s.get('remove_vocals', False):
                    if self.has_stereo_audio_stream(video_path):
                        # Center channel cancellation reduces RMS by about half,
                        # so compensate to keep sound effects loud enough.
                        fc.append(
                            f"[0:a]pan=stereo|c0=0.5*c0-0.5*c1|c1=-0.5*c0+0.5*c1,volume={vol * 2}[a0];"
                            f"[1:a]volume=1.0[a1];[a0][a1]amix=inputs=2:duration=longest[a_mix];"
                            f"[a_mix]asetpts=PTS-STARTPTS[a_out]"
                        ) # type: ignore
                    else:
                        self.log("⚠️ Vocal removal requires stereo source audio. Using original audio instead.")
                        fc.append(f"[0:a]volume={vol}[a0];[1:a]volume=1.0[a1];[a0][a1]amix=inputs=2:duration=longest[a_mix];[a_mix]asetpts=PTS-STARTPTS[a_out]")
                else: # type: ignore
                    fc.append(f"[0:a]volume={vol}[a0];[1:a]volume=1.0[a1];[a0][a1]amix=inputs=2:duration=longest[a_mix];[a_mix]asetpts=PTS-STARTPTS[a_out]")
            else:
                # Use only TTS audio if original volume is 0 OR video has no audio
                fc.append(f"[1:a]volume=1.0,asetpts=PTS-STARTPTS[a_out]")
    
            cmd.extend(["-filter_complex", ";".join(fc)])
    
            # Map outputs
            cmd.extend(["-map", "[v_final]"])
            cmd.extend(["-map", "[a_out]"])
    
            # Preview Duration
            if s['preview']:
                cmd.extend(["-t", "5"])
            elif s.get('cut_enabled', False):
                cmd.extend(["-ss", s['cut_start']])
                cmd.extend(["-to", s['cut_end']])
    
            # Encoding settings
            if s.get('use_gpu', False): # type: ignore
                # Map the existing speed selector to NVENC presets. Lower p-values are faster.
                nvenc_preset_map = {
                    "ultrafast": "p1",
                    "superfast": "p1",
                    "veryfast": "p2",
                    "faster": "p2",
                    "fast": "p3",
                    "medium": "p4",
                    "slow": "p5",
                    "slower": "p6",
                }
                selected_preset = str(s.get('preset', 'medium')).lower()
                nvenc_preset = nvenc_preset_map.get(selected_preset, "p4")
                fast_nvenc = selected_preset in {"ultrafast", "superfast", "veryfast", "faster", "fast"}
                nvenc_rc = "vbr" if fast_nvenc else "vbr_hq"
                nvenc_tune = "ll" if fast_nvenc else "hq"
                cmd.extend([
                    "-c:v", "h264_nvenc",
                    "-preset", nvenc_preset,
                    "-tune", nvenc_tune,
                    "-rc", nvenc_rc,
                    "-cq", str(s['crf']),
                    "-pix_fmt", "yuv420p",
                ])
            else:
                # CPU Encoding (x264)
                cmd.extend(["-c:v", "libx264", "-preset", s['preset'], "-crf", str(s['crf']), "-pix_fmt", "yuv420p"]) # type: ignore
            # FIX: Force Stereo (2 channels) and 48kHz sample rate to prevent audio glitches
            cmd.extend(["-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000"])
            cmd.append(output_file)

            # Debug
            print("FFmpeg Cmd:", " ".join(cmd))

            # Run with REAL-TIME progress monitoring
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           text=True, encoding='utf-8', errors='ignore', # type: ignore
                                           creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0) # type: ignore
                stderr_log = []
        
                # Get total duration from input video for progress calculation
                total_duration = self.get_video_duration_ms(video_path) / 1000.0  # Convert to seconds
                if total_duration <= 0:
                    total_duration = 1  # Prevent division by zero
        
                # Read stderr line by line for real-time progress
                while True:
                    line = process.stderr.readline()  # type: ignore[union-attr]
                    if not line:
                        break

                    stderr_log.append(line.strip())
                    line = line.strip()

                    # Parse FFmpeg progress (look for "time=XX:XX:XX.XX" pattern)
                    if "time=" in line:
                        time_match = re.search(r'time=(\d{2,}):(\d{2}):(\d{2})\.(\d{2})', line)
                        if time_match:
                            hours = int(time_match.group(1))
                            minutes = int(time_match.group(2))
                            seconds = int(time_match.group(3))
                            current_time = hours * 3600 + minutes * 60 + seconds + int(time_match.group(4)) / 100.0

                            # Calculate percentage
                            progress_percent = min(95, int((current_time / total_duration) * 100))
                            if progress_percent > 0:
                                self.progress_signal.emit(progress_percent)
                                self.progress_text_signal.emit(f"Encoding: {progress_percent}%")

                    # Log speed info
                    if "speed=" in line and "x" in line:
                        speed_match = re.search(r'speed=(\d+\.?\d*)x', line) # type: ignore
                        if speed_match:
                            self.log(f"⚡ Encoding speed: {speed_match.group(1)}x")

                # Wait for process to finish
                process.wait() # type: ignore

                if process.returncode != 0:
                    last_logs = "\n".join(stderr_log[-20:])
                    self.log(f"❌ FFmpeg Export Error (code {process.returncode}). See details below.")
                    self.log("--- FFmpeg Log ---")
                    self.log(last_logs)
                    self.log("--------------------")

                    # Check for common error: No audio stream in video (ករណីវីដេអូគ្មានសំឡេង)
                    if "Stream specifier ':a'" in last_logs and s['orig_vol'] > 0:
                        self.log("⚠️ Error: Video has no audio stream, but 'Original Audio Vol' > 0.") # type: ignore
                        self.log("💡 Fix: Please set 'Original Audio Vol' to 0 and try again. (សូមដាក់សំឡេងវីដេអូដើមមក 0)") # type: ignore

                    return
            except FileNotFoundError:
                self.log("❌ Error: FFmpeg executable not found. Please check the path in Settings.")
                return
    
            self.log(f"✅ Video Exported Successfully: {output_file}")
    
            # Apply Lip-Sync if enabled
            if s.get('enable_lip_sync', False) and self.srt_characters: # type: ignore
                self.log("🎭 Applying Lip-Sync with SRT character detection...")
                lip_sync_output = output_file.replace('.mp4', '_lipsync.mp4')
                if self.apply_lip_sync(output_file, tts_audio, lip_sync_output, self.character_info):
                    output_file = lip_sync_output  # Use lip-synced version
                    self.log(f"✅ Lip-Sync applied. Final output: {output_file}")
                else:
                    self.log("⚠️ Lip-Sync failed, using original video")
    
            # Check Auto Play setting
            if s.get('auto_play', True):
                if sys.platform == "win32":
                    self.log("⏳ Opening player...")
                    time.sleep(3.0) # Wait 3s to ensure file is fully written
                    self.open_file_or_folder(output_file)
            else:
                self.log("ℹ️ Auto-play disabled. Please open the folder to view.")

        except Exception as e:
            self.log(f"❌ Video export thread failed. Check logs for FFmpeg errors.")
        finally:
            self.export_finished_signal.emit()
            self.clear_cache() # Clean after finishing
    def export_srt_file(self) -> None:
        segments = self.get_segments_from_table()
        if not segments:
            QMessageBox.warning(self, "Warning", "No segments to export!")
            return

        last_dir = self.app_settings.get("last_output_dir", "")
        path, _ = QFileDialog.getSaveFileName(self, "Export SRT", last_dir, "Subtitle Files (*.srt)")
        if not path: return

        # type: ignore
        try:
            with open(path, "w", encoding="utf-8") as f:
                for i, seg in enumerate(segments):
                    start = self.ms_to_time(seg['start'])
                    end = self.ms_to_time(seg['end'])
                    text = seg['text']

                    f.write(f"{i+1}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n")

                    # Fix Bug #30: Check if checkbox exists before accessing # type: ignore
                    if hasattr(self, 'chk_empty_line') and self.chk_empty_line:
                        if self.chk_empty_line.isChecked():
                            f.write("\n")

            self.log(f"✅ Exported SRT: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not export SRT:\n{e}")

    def export_plain_text_file(self, segments: list[dict[str, Any]]) -> None:
        if not segments: # type: ignore
            QMessageBox.warning(self, "Warning", "No segments to export!")
            return
    
        last_dir = self.app_settings.get("last_output_dir", "")
        path, _ = QFileDialog.getSaveFileName(self, "Export Text", last_dir, "Text Files (*.txt)")
        if not path: return

        try:
            with open(path, "w", encoding="utf-8") as f:
                if self.chk_include_filename.isChecked():
                    video_name = "Unknown Video"
                    if self.media_player.media().canonicalUrl().isLocalFile():
                        video_name = os.path.basename(self.media_player.media().canonicalUrl().toLocalFile())
                    f.write(f"File: {video_name}\n\n")
        
                for seg in segments:
                    text = seg['text']
                    if self.chk_include_time.isChecked():
                        start = self.ms_to_time(seg['start'])
                        end = self.ms_to_time(seg['end'])
                        f.write(f"[{start} - {end}] {text}")
                    else:
                        f.write(f"{text}")
            
                    f.write("\n")
                    if self.chk_empty_line.isChecked():
                        f.write("\n")
                
            self.log(f"✅ Exported Text: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not export Text:\n{e}")

    def load_configs_from_file(self) -> None: # type: ignore
        try:
            with open(self.get_config_path("role_configs.json"), "r", encoding="utf-8") as f:
                self.role_configs = json.load(f)
        except Exception as e:
            self.log(f"Error loading configs: {e}")
            self.role_configs = {}
        """Load app_settings.json, not role_configs.json anymore."""
        # This method is now only for app_settings.json, role_configs are part of project file
        # The previous implementation of loading role_configs.json is removed.
        # role_configs will be loaded from project file or initialized to defaults.
        pass
    def save_configs_to_file(self) -> None: # type: ignore
        try:
            with open(self.get_config_path("role_configs.json"), "w", encoding="utf-8") as f:
                json.dump(self.role_configs, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save config: {e}")
        """Save app_settings.json, not role_configs.json anymore."""
        # This method is now only for app_settings.json, role_configs are part of project file
        # The previous implementation of saving role_configs.json is removed.
        # Project saving handles role_configs persistence.
        pass

    def ensure_default_role_configs(self):
        """Ensure default role configurations exist. Called on new project or if no roles loaded."""
        defaults = get_default_role_configs()
        updated = False
        for role, default_cfg in defaults.items():
            if role not in self.role_configs:
                self.role_configs[role] = default_cfg.copy()
                updated = True
                self.role_configs[role]["is_new"] = False
            else:
                for key, value in default_cfg.items():
                    if key not in self.role_configs[role]:
                        self.role_configs[role][key] = value
                        updated = True
                if self.role_configs[role].get("is_new", False):
                    self.role_configs[role]["is_new"] = False
                    updated = True
        if updated: # type: ignore
            self.save_configs_to_file()
    def save_current_role_config(self) -> None:
        role = self.voice_combo.currentText() # type: ignore

        # Preserve existing rate/pitch if any
        existing = self.role_configs.get(role, {})
        rate = existing.get("rate", 0)
        tts_pitch = existing.get("tts_pitch", 0)
        fade_in = self.fade_in.value()
        fade_out = self.fade_out.value()

        config = {
            "voice": self.get_voice_from_role(role),
            "age": self.age_combo.currentText(),
            "emotion": self.emotion_combo.currentText(),
            "rate": rate,
            "tts_pitch": tts_pitch,
            "fade_in": fade_in,
            "fade_out": fade_out,
            "is_new": False
        }
        self.role_configs[role] = config
        self.save_configs_to_file()
        self.save_project() # Save the entire project to persist role configs
        self.refresh_role_config_table()
        self.log(f"✅ Saved settings for {role}")

    def load_app_settings(self) -> None:
        try:
            if os.path.exists(self.get_config_path("app_settings.json")):
                with open(self.get_config_path("app_settings.json"), "r", encoding="utf-8") as f:
                    self.app_settings = json.load(f) # type: ignore
            if not isinstance(self.app_settings, dict):
                self.app_settings = {}
        except:
            self.app_settings = {}

        self.app_settings.setdefault("update_url", DEFAULT_UPDATE_URL)

        try:
            with open(self.get_config_path("app_settings.json"), "w", encoding="utf-8") as f:
                json.dump(self.app_settings, f, indent=4) # type: ignore
        except:
            pass

    def save_app_settings(self) -> None:
        try:
            if not isinstance(self.app_settings, dict):
                self.app_settings = {}
            with open(self.get_config_path("app_settings.json"), "w", encoding="utf-8") as f: # type: ignore
                json.dump(self.app_settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"⚠️ Could not save app settings: {e}")

    def update_autosave_timer(self) -> None:
        enabled = self.chk_autosave.isChecked()
        interval = self.sb_autosave_interval.value()

        self.app_settings["autosave_enabled"] = enabled
        self.app_settings["autosave_interval"] = interval
        self.save_app_settings()

        if enabled:
            ms = interval * 60 * 1000
            self.autosave_timer.start(ms)
        else:
            self.autosave_timer.stop()
    def auto_save_project(self) -> None:
        if self.current_project_path: # type: ignore
            # Silent save (avoid popup) # type: ignore
            try:
                data = self.get_project_data()
                # Fix Bug #10: Write to temp file first, then rename (atomic operation)
                temp_path = self.current_project_path + ".autosave_tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                # Replace original atomically after successful write.
                os.replace(temp_path, self.current_project_path)
                self.log(f"💾 Auto-Saved: {os.path.basename(self.current_project_path)}")
            except Exception as e:
                self.log(f"⚠️ Auto-Save Failed: {e}")
        else:
            # Fix Bug #10: Use unique backup filename per session to prevent overwriting
            try:
                import getpass
                session_id = hashlib.md5(f"{getpass.getuser()}_{os.getcwd()}".encode()).hexdigest()[:8]
                backup_path = os.path.abspath(f"autosave_backup_{session_id}.json")
                data = self.get_project_data()
                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                self.log(f"💾 Auto-Saved Backup: {os.path.basename(backup_path)}")
            except:
                pass # type: ignore

    def open_tts_config(self) -> None:
        dialog = CharacterConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            current = self.voice_combo.currentText() # type: ignore
            self._refresh_voice_combo(current)
            self.refresh_table_combos() # type: ignore
    def refresh_table_combos(self) -> None: # type: ignore
        rows = self.segment_table.rowCount() # type: ignore
        for r in range(rows):
            combo = self.segment_table.cellWidget(r, 3)
            if isinstance(combo, QComboBox):
                current = combo.currentText()
                combo.blockSignals(True) # type: ignore
                combo.clear()
                combo.addItems(self.roles)
                combo.setCurrentText(current)
                combo.blockSignals(False) # type: ignore
                self.apply_role_combo_highlight(combo, current)
    def closeEvent(self, a0: Optional[QCloseEvent]) -> None: # type: ignore
        # Set stop_event to signal all running threads to stop (Fix: race condition)
        if hasattr(self, 'stop_event'):
            self.stop_event.set()

        # Stop players to release file handles
        if hasattr(self, 'media_player'): # type: ignore
            try:
                self.media_player.stop()
                self.media_player.setVideoOutput(None)
                self.media_player.setMedia(QMediaContent())
            except:
                pass

        # Stop pygame audio
        if hasattr(self, 'pygame_audio_available') and self.pygame_audio_available:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except:
                pass

        # Also stop QMediaPlayer audio if it exists # type: ignore
        if hasattr(self, 'preview_player'):
            try:
                self.preview_player.stop() # type: ignore
                self.preview_player.setMedia(QMediaContent())
            except:
                pass  # Player may already be deleted

        if hasattr(self, 'autosave_timer'):
            self.autosave_timer.stop()

        # Fix Bug #18 & #22: Wait for worker threads to finish gracefully # type: ignore
        self.log("⏳ Shutting down worker threads...")
        self.wait_for_workers(timeout=5.0)

        # Wait for background threads to finish (prevent crashes)
        if hasattr(self, 'ffmpeg_install_thread') and self.ffmpeg_install_thread.isRunning():
            self.ffmpeg_install_thread.wait(2000)  # Wait up to 2 seconds
        if hasattr(self, 'dl_thread') and self.dl_thread.isRunning():
            self.dl_thread.wait(2000)
        if hasattr(self, 'klite_thread') and self.klite_thread.isRunning():
            self.klite_thread.wait(2000)

        # Save all UI settings to app_settings # type: ignore
        self.app_settings["fade_in"] = self.fade_in.value()
        self.app_settings["fade_out"] = self.fade_out.value()
        self.app_settings["global_speed"] = self.speed_spin.value()
        self.app_settings["auto_play"] = self.chk_autoplay.isChecked()
        self.app_settings["use_gpu"] = self.chk_gpu.isChecked()
        if hasattr(self, 'chk_lip_sync'):
            self.app_settings["enable_lip_sync"] = self.chk_lip_sync.isChecked()

        # Save current theme # type: ignore
        if hasattr(self, 'current_theme'):
            self.app_settings["selected_theme"] = self.current_theme
        if hasattr(self, 'khmer_font_selector'):
            font_name = self.khmer_font_selector.currentText().strip()
            self.app_settings["khmer_font"] = font_name or DEFAULT_KHMER_FONT

        # Save export tab settings
        if hasattr(self, 'cb_resolution'):
            self.app_settings["resolution_idx"] = self.cb_resolution.currentIndex()
        if hasattr(self, 'cb_preset'):
            self.app_settings["preset_idx"] = self.cb_preset.currentIndex()
        if hasattr(self, 'sb_crf'):
            self.app_settings["crf_value"] = self.sb_crf.value()
        if hasattr(self, 'cb_crop_preset'):
            self.app_settings["crop_preset_idx"] = self.cb_crop_preset.currentIndex()
        if hasattr(self, 'sb_brightness'):
            self.app_settings["brightness"] = self.sb_brightness.value()
        if hasattr(self, 'sb_contrast'):
            self.app_settings["contrast"] = self.sb_contrast.value()
        if hasattr(self, 'sb_saturation'):
            self.app_settings["saturation"] = self.sb_saturation.value()

        self.save_app_settings() # type: ignore
        try:
            QApplication.processEvents()
            time.sleep(0.2)
        except:
            pass
        if a0: # type: ignore
            a0.accept()

    def on_combo_role_changed(self) -> None:
        role = self.voice_combo.currentText()

        self.age_combo.blockSignals(True)
        self.emotion_combo.blockSignals(True)
        self.fade_in.blockSignals(True)
        self.fade_out.blockSignals(True) # type: ignore

        if role in self.role_configs: # type: ignore
            c = self.role_configs[role]
            self.age_combo.setCurrentText(c.get("age", ""))
            self.emotion_combo.setCurrentText(c.get("emotion", ""))
    
            # Load Fade settings if available (Load ការកំណត់ Fade របស់តួអង្គ)
            self.fade_in.setValue(c.get("fade_in", 50)) # type: ignore
            self.fade_out.setValue(c.get("fade_out", 50))
    
            self.log(f"Loaded config for {role}") # type: ignore
        else:
            # Reset other fields to default
            self.age_combo.setCurrentIndex(0)
            self.emotion_combo.setCurrentIndex(0)
            self.fade_in.setValue(50)
            self.fade_out.setValue(50)
    
        self.age_combo.blockSignals(False) # type: ignore
        self.emotion_combo.blockSignals(False) # type: ignore
        self.fade_in.blockSignals(False)
        self.fade_out.blockSignals(False) # type: ignore
    def create_menu_bar(self) -> None:
        menubar = self.menuBar()
        if menubar:
            file_menu = menubar.addMenu("File (ឯកសារ)")
            if file_menu:
                # New Project (with confirmation)
                new_action = QAction("📄 New Project (គម្រោងថ្មី)", self)
                new_action.setShortcut("Ctrl+N")
                new_action.triggered.connect(lambda _checked=False: self.new_project())
                file_menu.addAction(new_action)

                open_action = QAction("📂 Open Project (បើកគម្រោង)", self)
                open_action.setShortcut("Ctrl+O")
                open_action.triggered.connect(lambda _checked=False: self.open_project())
                file_menu.addAction(open_action)

                save_action = QAction("💾 Save Project (រក្សាទុក)", self)
                save_action.setShortcut("Ctrl+S")
                save_action.triggered.connect(lambda _checked=False: self.save_project())
                file_menu.addAction(save_action)

                save_as_action = QAction("💾 Save Project As... (រក្សាទុកជា...)", self)
                save_as_action.setShortcut("Ctrl+Shift+S")
                save_as_action.triggered.connect(lambda _checked=False: self.save_project_as())
                file_menu.addAction(save_as_action)

                # Separator
                file_menu.addSeparator()

                # Merge Projects
                merge_action = QAction("🔗 Merge Projects (ផ្សំគម្រោង)", self)
                merge_action.triggered.connect(lambda _checked=False: self.merge_projects())
                file_menu.addAction(merge_action)

                # Separator
                file_menu.addSeparator()

                # Clear Table (with confirmation)
                clear_action = QAction("🗑️ Clear All Segments (លុបទាំងអស់)", self)
                clear_action.setShortcut("Ctrl+Shift+Delete")
                clear_action.triggered.connect(lambda _checked=False: self.clear_all_segments())
                file_menu.addAction(clear_action)

            # Tools menu
            # (Tools menu removed because the Role Config Table feature is disabled) # type: ignore
    def open_project(self, path: Optional[str] = None) -> None:
        if not path: # type: ignore
            last_dir = self.app_settings.get("last_project_dir", "")
            path, _ = QFileDialog.getOpenFileName(self, "Open Project", last_dir, "RVC Project (*.json)")

        if path:
            self.current_project_path = path
            self.app_settings["last_project_dir"] = os.path.dirname(path)
            self.save_app_settings()
            try: # type: ignore
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f) # type: ignore
                self.load_project_data(data)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open project:\n{e}")

    def save_project(self) -> None:
        if not self.current_project_path:
            self.save_project_as()
        else:
            self.write_project_file(self.current_project_path) # type: ignore

    def save_project_as(self) -> None:
        last_dir = self.app_settings.get("last_project_dir", "") # type: ignore
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", last_dir, "RVC Project (*.json)")
        if path:
            self.current_project_path = path
            self.app_settings["last_project_dir"] = os.path.dirname(path)
            self.save_app_settings()
            self.write_project_file(path) # type: ignore

    def concat_project_videos(self, video_paths: list[str], output_path: str) -> tuple[bool, str]: # type: ignore
        """Concatenate multiple videos using FFmpeg concat demuxer, with a re-encode fallback."""
        error_message = ""
        list_file = os.path.join(tempfile.gettempdir(), f"concat_list_{int(time.time())}.txt")
        try:
            with open(list_file, "w", encoding="utf-8") as f:
                for path in video_paths:
                    normalized_path = path.replace('\\', '/')
                    f.write(f"file '{normalized_path}'\n")

            ffmpeg_bin = self.get_ffmpeg()
            cmd = [
                ffmpeg_bin, "-y", "-f", "concat", "-safe", "0", "-i", list_file, # type: ignore
                "-c", "copy", output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            if result.returncode == 0:
                return True, ""

            error_message = result.stderr.strip()
            self.safe_log(f"FFmpeg concat copy failed: {error_message}")
            self.safe_log("Retrying concat using re-encode fallback...")

            # Fallback to filter_complex concat with re-encoding for compatibility
            cmd = [ffmpeg_bin, "-y"]
            for path in video_paths: # type: ignore
                cmd.extend(["-i", path])
            input_streams = "".join([f"[{idx}:v:0][{idx}:a:0]" for idx in range(len(video_paths))])
            filter_complex = f"{input_streams}concat=n={len(video_paths)}:v=1:a=1[outv][outa]"
            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-map", "[outa]",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]) # type: ignore

            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            if result.returncode == 0:
                return True, ""

            error_message = result.stderr.strip()
            self.safe_log(f"FFmpeg concat fallback failed: {error_message}")
            return False, error_message
        except Exception as e:
            error_message = str(e)
            self.safe_log(f"FFmpeg concat failed: {error_message}")
            return False, error_message
        finally:
            try:
                os.remove(list_file)
            except:
                pass

    def merge_projects(self) -> None:
        """Merge multiple projects by exporting each to video first, then concatenating the videos.""" # type: ignore
        if getattr(self, "merge_in_progress", False):
            QMessageBox.information(self, "Merge Projects", "Merge is already running. Please wait.")
            return

        last_dir = self.app_settings.get("last_project_dir", "")
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Projects to Merge", last_dir, "RVC Project (*.json)")

        if not paths:
            return

        if len(paths) < 2:
            QMessageBox.warning(self, "Merge Projects", "Please select at least 2 projects to merge.")
            return

        # Collect video paths and validate
        project_data = []
        for project_path in paths: # type: ignore
            try:
                with open(project_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                video_path = data.get("video_path", "")
                if not video_path or not os.path.exists(video_path):
                    QMessageBox.warning(self, "Merge Projects", f"Project {os.path.basename(project_path)} has no valid video file.")
                    return
                project_data.append((data, video_path))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load project {project_path}:\n{e}")
                return

        self.merge_in_progress = True
        self.progress.setValue(0)
        self.progress_text_signal.emit("Merging projects...")
        self.log(f"🔗 Starting merge for {len(project_data)} projects...")
        self.start_worker_thread(
            target=self.merge_projects_worker,
            args=(project_data, self.chk_gpu.isChecked(), self.get_ffmpeg())
        )

    def build_project_tts_segments(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert saved project segments into the richer shape expected by run_srt_thread."""
        project_role_configs = data.get("role_configs", get_default_role_configs())
        project_settings = data.get("settings", {})
        global_fade_in = project_settings.get("fade_in", 50)
        global_fade_out = project_settings.get("fade_out", 50)

        def role_tts_params(role: str) -> tuple[str, str, str]:
            config = project_role_configs.get(role, {})
            voice = config.get("voice")
            if not voice:
                voice = "km-KH-SreymomNeural" if ("Female" in role or "Girl" in role or "ស្រី" in role) else "km-KH-PisethNeural"

            rate_val = int(config.get("rate", 0))
            pitch_val = int(config.get("tts_pitch", 0))
            age = str(config.get("age", ""))
            emotion = str(config.get("emotion", ""))

            if "Child" in age:
                pitch_val += 25
                rate_val += 10
            elif "Teen" in age:
                pitch_val += 10
                rate_val += 5
            elif "Elder" in age:
                pitch_val -= 15
                rate_val -= 10

            if "Happy" in emotion:
                pitch_val += 5
                rate_val += 10
            elif "Sad" in emotion:
                pitch_val -= 5
                rate_val -= 15
            elif "Angry" in emotion:
                rate_val += 5
                pitch_val -= 5
            elif "Excited" in emotion:
                rate_val += 20
                pitch_val += 5

            return str(voice), f"{rate_val:+d}%", f"{pitch_val:+d}Hz"

        tts_segments = []
        for seg in data.get("segments", []):
            role = seg.get("role", "")
            voice, rate_str, pitch_str = role_tts_params(role)
            config = project_role_configs.get(role, {})
            role_fade_in = config.get("fade_in", -1)
            role_fade_out = config.get("fade_out", -1)
            tts_segments.append({
                "text": seg.get("text", ""),
                "voice": voice,
                "rate": rate_str,
                "pitch": pitch_str,
                "start": int(seg.get("start", 0)),
                "end": int(seg.get("end", 0)),
                "fade_in": role_fade_in if role_fade_in != -1 else global_fade_in,
                "fade_out": role_fade_out if role_fade_out != -1 else global_fade_out,
            })
        return tts_segments

    def merge_projects_worker(self, project_data: list[tuple[dict[str, Any], str]], use_gpu: bool, ffmpeg_bin: str) -> None:
        """Export each project and concatenate the temporary videos in a background thread."""
        temp_videos = []
        temp_audios = []
        exported_projects = []
        error_msg = ""
        try:
            total_projects = max(1, len(project_data))

            for i, (data, video_path) in enumerate(project_data):
                self.safe_log(f"🔊 Merge {i + 1}/{total_projects}: generating audio...")
                self.progress_text_signal.emit(f"Merge {i + 1}/{total_projects}: audio")
                self.progress_signal.emit(int(i / total_projects * 80))

                segments = self.build_project_tts_segments(data)
                if not segments:
                    self.safe_log(f"⚠️ Project {i + 1} has no segments. Skipping.")
                    continue

                timestamp = int(time.time() * 1000)
                temp_audio = os.path.join(tempfile.gettempdir(), f"merge_audio_{i}_{timestamp}.wav")
                temp_audios.append(temp_audio)
                try:
                    self.run_srt_thread(
                        segments,
                        ffmpeg_bin,
                        temp_audio,
                        quality_idx=0,
                        auto_fit=True,
                        fade_in=50,
                        fade_out=50,
                        auto_play=False,
                        emit_signal=False
                    )
                except Exception as e:
                    self.safe_log(f"Failed to generate audio for project {i + 1}: {e}")
                    continue

                if not os.path.exists(temp_audio):
                    self.safe_log(f"Failed to generate audio for project {i + 1}: output file was not created")
                    continue

                self.safe_log(f"🎬 Merge {i + 1}/{total_projects}: exporting video...")
                self.progress_text_signal.emit(f"Merge {i + 1}/{total_projects}: video")
                temp_video = os.path.join(tempfile.gettempdir(), f"merge_video_{i}_{timestamp}.mp4")
                video_settings = {
                    'resolution': '1920x1080',
                    'crop_preset': 'Original',
                    'brightness': 0.0,
                    'contrast': 1.0,
                    'saturation': 1.0,
                    'crop': [0, 0, 0, 0],
                    'use_gpu': use_gpu,
                    'preset': 'veryfast',
                    'crf': 23,
                    'orig_vol': 0.5,
                    'remove_vocals': False,
                    'preview': False,
                    'cut_enabled': False
                }

                try:
                    self.run_export_mp4_thread(video_path, temp_audio, temp_video, ffmpeg_bin, video_settings)
                except Exception as e:
                    self.safe_log(f"Failed to export video for project {i + 1}: {e}")
                    continue

                if not os.path.exists(temp_video):
                    self.safe_log(f"Failed to export video for project {i + 1}: output file was not created")
                    continue

                temp_videos.append(temp_video)
                exported_projects.append((data, temp_video))

            if not temp_videos:
                self.merge_finished_signal.emit({
                    "success": False,
                    "message": "No videos were successfully exported.",
                    "cleanup": temp_videos + temp_audios,
                })
                return

            self.safe_log("🔗 Concatenating exported project videos...")
            self.progress_text_signal.emit("Concatenating merged video...")
            self.progress_signal.emit(90)

            merged_video_path = os.path.join(tempfile.gettempdir(), f"merged_projects_{int(time.time())}.mp4")
            success, error_msg = self.concat_project_videos(temp_videos, merged_video_path)
            if not success or not os.path.exists(merged_video_path):
                self.merge_finished_signal.emit({
                    "success": False,
                    "message": "Video concatenation failed.",
                    "error": error_msg,
                    "cleanup": temp_videos + temp_audios,
                })
                return

            merged_segments = []
            time_offset = 0
            for data, temp_video in exported_projects:
                segments = data.get("segments", [])
                if segments:
                    for seg in segments:
                        merged_segments.append({
                            "start": int(seg.get("start", 0)) + time_offset,
                            "end": int(seg.get("end", 0)) + time_offset,
                            "role": seg.get("role", ""),
                            "text": seg.get("text", "")
                        })
                    video_duration = self.get_video_duration_ms(temp_video)
                    if video_duration <= 0:
                        video_duration = max((int(seg.get("end", 0)) for seg in segments), default=0)
                    time_offset += video_duration

            merged_role_configs = {}
            for data, _ in exported_projects:
                for role, config in data.get("role_configs", {}).items():
                    if role not in merged_role_configs:
                        merged_role_configs[role] = config

            self.merge_finished_signal.emit({
                "success": True,
                "merged_video_path": merged_video_path,
                "merged_segments": merged_segments,
                "role_configs": merged_role_configs,
                "exported_count": len(exported_projects),
                "cleanup": temp_videos + temp_audios,
            })
        except Exception as e:
            self.merge_finished_signal.emit({
                "success": False,
                "message": "Merge failed.",
                "error": str(e),
                "cleanup": temp_videos + temp_audios,
            })

    def on_merge_projects_finished(self, result: dict[str, Any]) -> None:
        self.merge_in_progress = False
        self.progress_signal.emit(100 if result.get("success") else 0)
        self.progress_text_signal.emit("")

        for temp_file in result.get("cleanup", []):
            try:
                os.remove(temp_file)
            except:
                pass

        if not result.get("success"):
            details = f"\n\n{result.get('error')}" if result.get("error") else ""
            QMessageBox.warning(self, "Merge Projects", f"{result.get('message', 'Merge failed.')}{details}")
            return

        merged_video_path = result.get("merged_video_path", "")
        merged_segments = result.get("merged_segments", [])
        self.load_video(merged_video_path, autoplay=False)
        self.current_project_path = None
        self.current_srt_path = None
        self.log(f"✅ Merged {result.get('exported_count', 0)} projects into video: {merged_video_path}")

        self.segment_table.setRowCount(0)
        self.segment_table.setRowCount(len(merged_segments))

        for role, config in result.get("role_configs", {}).items():
            if role not in self.role_configs:
                self.role_configs[role] = config

        for seg in merged_segments:
            role = seg.get("role", "")
            if role and role not in self.roles:
                self.roles.append(role)

        current_voice = self.voice_combo.currentText() # type: ignore
        self._refresh_voice_combo(current_voice)

        for i, seg in enumerate(merged_segments):
            self.set_table_row(i, seg["start"], seg["end"], seg["role"], seg["text"])

        QMessageBox.information(
            self,
            "Merge Projects",
            f"Successfully merged {result.get('exported_count', 0)} projects.\n"
            f"Total segments: {len(merged_segments)}\n"
            f"Video: {merged_video_path}\n\n"
            "This merged result is unsaved. Use Save Project As to keep it."
        )

    def new_project(self, *_args) -> None:
        """Create a new project with confirmation dialog""" # type: ignore
        reply = QMessageBox.question(
            self,
            "New Project (គម្រោងថ្មី)",
            "Are you sure you want to create a new project?\nUnsaved changes will be lost.\n(តើអ្នកប្រាកដថាចង់បង្កើតគម្រោងថ្មីមែនទេ?)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Clear all data
                self.current_project_path = None
                self.current_video_path = None
                self.current_srt_path = None

                # Reset role configurations to defaults for the new project
                self.role_configs = get_default_role_configs()
                self.roles = list(self.role_configs.keys())
                self._refresh_voice_combo(self.roles[0] if self.roles else "")

                self.segment_table.setUpdatesEnabled(False)
                try:
                    for row in range(self.segment_table.rowCount()):
                        self._clear_table_cell_widgets(row)
                    self.segment_table.setRowCount(0)
                finally:
                    self.segment_table.setUpdatesEnabled(True)

                self.log_box.clear()
                self.progress.setValue(0)
                self.btn_run_srt.setEnabled(False)

                # Reset video controls without clearing QMediaPlayer media directly.
                # On some Windows multimedia backends, setting an empty QMediaContent
                # can terminate the process without a Python traceback.
                self.media_player.stop()
                self.media_player.setPosition(0)
                if hasattr(self, "video_item"):
                    self.video_item.setVisible(False)
                self.play_btn.setEnabled(False)
                self.lbl_duration.setText("00:00 / 00:00")
                self.position_slider.setRange(0, 0)
                self.position_slider.setValue(0)

                self.log("📄 New project created") # type: ignore
                QMessageBox.information(self, "New Project", "New project created successfully!\n(គម្រោងថ្មីត្រូវបានបង្កើត)")
            except Exception as e:
                self.safe_log(f"New project failed: {e}")
                QMessageBox.warning(self, "New Project", f"Could not create a new project:\n{e}")

    def clear_all_segments(self) -> None:
        row_count = self.segment_table.rowCount()
        if row_count == 0:
            QMessageBox.information(self, "Info", "No segments to clear.")
            return

        reply = QMessageBox.question(
            self,
            "Clear All Segments (លុបទាំងអស់)",
            f"Are you sure you want to delete all {row_count} segments?\n(តើអ្នកប្រាកដថាចង់លុប {row_count} បន្ទាត់មែនទេ?)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes: # type: ignore
            # Clean up all cell widgets before removing rows (memory leak prevention)
            for row in range(row_count):
                self._clear_table_cell_widgets(row)

            self.segment_table.setRowCount(0)
            self.log(f"🗑️ Cleared all {row_count} segments")
    def write_project_file(self, path: str) -> None:
        try:
            data = self.get_project_data() # type: ignore
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False) # type: ignore
            self.log(f"✅ Project saved: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save project:\n{e}")

    def get_project_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        # Video
        if self.current_video_path and os.path.exists(self.current_video_path): # type: ignore
            data["video_path"] = self.current_video_path

        # Settings
        data["settings"] = {
            "speed": self.speed_spin.value(),
            "fade_in": self.fade_in.value(),
            "fade_out": self.fade_out.value(),
            # --- Export Configs (រក្សាទុកការកំណត់ Export) ---
            "resolution_idx": self.cb_resolution.currentIndex(),
            "crop_preset_idx": self.cb_crop_preset.currentIndex(),
            "brightness": self.sb_brightness.value(),
            "contrast": self.sb_contrast.value(),
            "saturation": self.sb_saturation.value(),
            "crop": [ # type: ignore
                self.sb_crop_top.value() if self.sb_crop_top else 0,
                self.sb_crop_bottom.value() if self.sb_crop_bottom else 0,
                self.sb_crop_left.value() if self.sb_crop_left else 0,
                self.sb_crop_right.value() if self.sb_crop_right else 0
            ]
        }

        # Include role configurations in project data
        data["role_configs"] = self.role_configs

        # Segments
        segments = []
        rows = self.segment_table.rowCount()
        for r in range(rows):
            item_start = self.segment_table.item(r, 0) # type: ignore
            start_ms = item_start.data(QT_USER_ROLE) if item_start else 0
    
            item_end = self.segment_table.item(r, 1) # type: ignore
            end_ms = item_end.data(QT_USER_ROLE) if item_end else 0
    
            combo = self.segment_table.cellWidget(r, 3) # type: ignore
            role = combo.currentText() if combo else ""
    
            item_text = self.segment_table.item(r, 4) # type: ignore
            text = item_text.text() if item_text else ""
    
            segments.append({
                "start": start_ms,
                "end": end_ms,
                "role": role,
                "text": text
            })
        data["segments"] = segments
        return data
    def load_project_data(self, data: dict[str, Any]) -> None: # type: ignore
        # Load Video
        video_path = data.get("video_path", "") # type: ignore
        if video_path and os.path.exists(video_path):
            self.load_video(video_path, autoplay=False)

        # Load Settings
        settings = data.get("settings", {})
        self.speed_spin.setValue(settings.get("speed", 0))
        self.fade_in.setValue(settings.get("fade_in", 50))
        self.fade_out.setValue(settings.get("fade_out", 50)) # type: ignore

        # --- Load Export Configs (ទាញយកការកំណត់ Export) ---
        self.cb_resolution.setCurrentIndex(settings.get("resolution_idx", 0))
        self.cb_crop_preset.setCurrentIndex(settings.get("crop_preset_idx", 0))
        self.sb_brightness.setValue(settings.get("brightness", 0.0))
        self.sb_contrast.setValue(settings.get("contrast", 1.0))
        self.sb_saturation.setValue(settings.get("saturation", 1.0))
        crop = settings.get("crop", [0,0,0,0])
        if self.sb_crop_top is not None: self.sb_crop_top.setValue(crop[0])
        if self.sb_crop_bottom is not None: self.sb_crop_bottom.setValue(crop[1]) # type: ignore
        if self.sb_crop_left is not None: self.sb_crop_left.setValue(crop[2])
        if self.sb_crop_right is not None: self.sb_crop_right.setValue(crop[3]) # type: ignore

        # Load role configurations from project data
        self.role_configs = data.get("role_configs", get_default_role_configs())
        self.roles = list(self.role_configs.keys())

        # Load Segments
        segments = data.get("segments", [])
        self.segment_table.setRowCount(0)
        self.segment_table.setRowCount(len(segments))

        # 1. Collect all unique roles first (ប្រមូលតួអង្គទាំងអស់ជាមុន)
        for seg in segments:
            role = seg.get("role", "")
            if role and role not in self.roles:
                self.roles.append(role)
                self.log(f"➕ Added missing role from project: {role}")

        # This step is now redundant as self.roles is populated from self.role_configs
        # which is loaded from project data.
        # However, we need to ensure all roles in segments are also in self.role_configs
        for seg in segments: # type: ignore
            self._initialize_new_role_config(seg.get("role", "Unknown"))
            
        # 2. Update Main Combo
        current_voice = self.voice_combo.currentText() # type: ignore
        self._refresh_voice_combo(current_voice)

        # 3. Populate Table
        for i, seg in enumerate(segments):
            start_ms = seg.get("start", 0)
            end_ms = seg.get("end", 0)
            text = seg.get("text", "")
            role = seg.get("role", "")
    
            self.set_table_row(i, start_ms, end_ms, role, text)
    

        self.btn_run_srt.setEnabled(True)
        self.log(f"✅ Project loaded with {len(segments)} segments.")


    # =============================
    # Run App
    # =============================

if __name__ == "__main__":
    app = None
    window = None
    splash: Optional[QSplashScreen] = None
    original_stderr = sys.stderr
    try: # type: ignore
        if not acquire_single_instance_lock():
            app = QApplication(sys.argv)
            QMessageBox.information(
                None,
                "SRT Drama Tool",
                "SRT Drama Tool is already running.\n\nកម្មវិធីកំពុងបើករួចហើយ។"
            )
            sys.exit(0)

        app = QApplication(sys.argv)
        startup_font = get_startup_khmer_font()
        app.setFont(QFont(startup_font, 10))
        
        # --- License Check Start ---
        machine_id = get_machine_id()
        # Fix Bug #27: Use proper config path for license file
        license_file = get_config_path('license.key')
        is_registered = False

        online_valid, online_msg = validate_saved_online_license(machine_id)
        if online_valid:
            is_registered = True

        if not is_registered and os.path.exists(license_file):
            with open(license_file, "r") as f:
                saved_key = f.read().strip()
                valid, _ = verify_license_key(saved_key, machine_id)
                if valid: is_registered = True

        if not is_registered:
            # Check Trial Period (7 Days) # type: ignore
            # USE REGISTRY INSTEAD OF JSON FILE (More Secure)
            reg_path = r"SOFTWARE\SRT_Drama_Tool_v15"
            current_ts = datetime.datetime.now().timestamp()

            first_run_ts = 0.0
            last_run_ts = 0.0
            stored_hash = ""

            # SECURE TRIAL: Cross-validation hash to prevent registry manipulation
            def get_secure_trial_hash(machine_id, first_run_ts):
                """Create hash from MachineID + Timestamp + Secret Salt"""
                raw = f"{machine_id}|{first_run_ts}|DRAMA_TOOL_SALT_2026" # type: ignore
                return hashlib.sha256(raw.encode()).hexdigest()[:16]

            try:
                # Try to read from Registry
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ)
                fr, _ = winreg.QueryValueEx(key, "FirstRun")
                lr, _ = winreg.QueryValueEx(key, "LastRun")
                # Read stored hash for validation
                try:
                    stored_hash, _ = winreg.QueryValueEx(key, "TrialHash")
                except:
                    stored_hash = ""
                winreg.CloseKey(key)
                first_run_ts = float(fr) # type: ignore
                last_run_ts = float(lr)
            except FileNotFoundError:
                # Not found = First run ever
                pass
            except Exception:
                pass # type: ignore

            if first_run_ts == 0.0:
                # Initialize Trial in Registry
                try:
                    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
                    winreg.SetValueEx(key, "FirstRun", 0, winreg.REG_SZ, str(current_ts))
                    winreg.SetValueEx(key, "LastRun", 0, winreg.REG_SZ, str(current_ts))
                    # Store secure hash for cross-validation
                    trial_hash = get_secure_trial_hash(machine_id, current_ts)
                    winreg.SetValueEx(key, "TrialHash", 0, winreg.REG_SZ, trial_hash)
                    winreg.CloseKey(key) # type: ignore
                except Exception:
                    pass # If registry fails, might fallback or allow
                is_registered = True # Allow trial
            else:
                # SECURITY CHECK: Validate hash to detect registry manipulation
                expected_hash = get_secure_trial_hash(machine_id, first_run_ts)
                if stored_hash and stored_hash != expected_hash:
                    # Hash mismatch = Registry tampered or FirstRun timestamp modified
                    QMessageBox.critical(None, "Security Error", 
                        "Trial validation failed!\n"
                        "Registry tampering detected. (រកឃើញការកែប្រែ Registry)\n"
                        "Please purchase a license to continue.")
                    # Force license check
                    dlg = LicenseDialog(machine_id)
                    if dlg.exec_() == QDialog.Accepted:
                        is_registered = True
                    else: # type: ignore
                        sys.exit(0)
                else:
                    # Check for clock manipulation (Time moved backwards)
                    if current_ts < last_run_ts:
                        QMessageBox.critical(None, "Security Error", "System clock manipulation detected!\n(រកឃើញការកែម៉ោងថយក្រោយ)\nTrial mode disabled.")
                        # Force license check
                        dlg = LicenseDialog(machine_id)
                        if dlg.exec_() == QDialog.Accepted:
                            is_registered = True
                        else: # type: ignore
                            sys.exit(0)
                    else:
                        # Update last run
                        try:
                            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
                            winreg.SetValueEx(key, "LastRun", 0, winreg.REG_SZ, str(current_ts))
                            # Update hash in case it wasn't there (backward compatibility)
                            if not stored_hash:
                                trial_hash = get_secure_trial_hash(machine_id, first_run_ts)
                                winreg.SetValueEx(key, "TrialHash", 0, winreg.REG_SZ, trial_hash)
                            winreg.CloseKey(key) # type: ignore
                        except Exception:
                            pass

                        # Check duration
                        first_run_date = datetime.datetime.fromtimestamp(first_run_ts)
                        days_passed = (datetime.datetime.now() - first_run_date).days

                        if days_passed < 7:
                            is_registered = True # Trial active
                        else:
                            # Trial expired
                            dlg = LicenseDialog(machine_id)
                            if dlg.exec_() == QDialog.Accepted:
                                is_registered = True
                            else: # type: ignore
                                sys.exit(0)
        # --- License Check End ---
        
        if is_registered:
            # --- Splash Screen Implementation ---
            # ស្វែងរក Path រូបភាព (គាំទ្រទាំងពេល run កូដធម្មតា និងពេល build ជា EXE)
            splash_path = resource_path("splash_logo.png")

            if os.path.exists(splash_path): # type: ignore
                pixmap = QPixmap(splash_path)
                splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
                splash.setFont(QFont(startup_font, 15, QFont.Bold))
                splash.show()
                splash.showMessage("កំពុងដំណើរការកម្មវិធី... Please wait...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, QColor(Qt.GlobalColor.white))
                app.processEvents()
            # ------------------------------------

            window = MainWindow()
            window.show()
            
            if splash: # type: ignore
                splash.finish(window) # បិទ Splash Screen ពេល MainWindow បង្ហាញខ្លួន
                
            exit_code = app.exec_()

            # IMPROVED: Don't completely suppress stderr - only filter Qt shutdown noise
            # This preserves important crash logs and warnings for debugging
            try:
                # Write exit info to log file for debugging
                log_file = get_config_path("app_exit.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n[{datetime.datetime.now()}] App exited with code: {exit_code}\n")
                
                # Only suppress known Qt shutdown warnings, keep everything else
                import io
                class StderrFilter:
                    def __init__(self, original):
                        self.original = original
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
                                self.original.write(line + "\n")
                            self.buffer = lines[-1]  # Keep incomplete line in buffer
                    
                    def flush(self):
                        if self.buffer:
                            self.original.write(self.buffer)
                            self.buffer = ""
                        self.original.flush()
                
                sys.stderr = StderrFilter(original_stderr)
            except:
                # If filter fails, fall back to original stderr
                sys.stderr = original_stderr
            
            sys.exit(exit_code)
    except Exception as e:
        # Handle errors for Windowed mode (No Console)
        error_msg = f"CRITICAL ERROR:\n{str(e)}\n\n{traceback.format_exc()}"
        
        # IMPROVED: Always write crash log to file for debugging
        crash_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_log.txt")
        try:
            with open(crash_log, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"[{datetime.datetime.now()}] CRASH LOG\n")
                f.write(f"{'='*60}\n")
                f.write(error_msg)
                f.write(f"\n{'='*60}\n\n")
        except:
            pass # type: ignore
        
        try:
            if not app: app = QApplication(sys.argv)
            # បិទ Splash Screen ជាមុនសិន ប្រសិនបើវាមានវត្តមាន ដើម្បីកុំឱ្យវាបាំងផ្ទាំង Error
            if splash:
                splash.close()
            QMessageBox.critical(None, "Critical Error", error_msg)
        except:
            # If QMessageBox fails, write to console
            print(error_msg, file=sys.stderr)
        finally:
            # Don't suppress stderr - let errors show for debugging
            # Only restore original stderr if it was changed
            if sys.stderr and hasattr(sys.stderr, 'original'):
                sys.stderr = original_stderr # type: ignore
            sys.exit(1)

