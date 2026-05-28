# -*- coding: utf-8 -*-
"""
Settings Tab - Professional Version
Improved and optimized for RVC Tool
NOTE: This is a reference file. The actual code is in RVC Tool.py
"""

import os
import json
import shutil
import subprocess
import datetime
import platform
from PyQt5.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
                              QFormLayout, QGroupBox, QLabel, QPushButton,
                              QLineEdit, QCheckBox, QSpinBox, QTextEdit,
                              QProgressBar, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# =============================
# Settings Tab (Professional Version)
# =============================

def build_settings_tab(self):
    """Build improved Settings tab with professional layout"""
    from PyQt5.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
                                  QFormLayout, QGroupBox, QLabel, QPushButton,
                                  QLineEdit, QCheckBox, QSpinBox, QTextEdit,
                                  QProgressBar, QMessageBox, QFileDialog, QSplitter)
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setStyleSheet("""
        QScrollArea {
            border: none;
            background-color: transparent;
        }
    """)

    widget = QWidget()
    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(20, 20, 20, 20)
    main_layout.setSpacing(18)

    # ===== ១. SYSTEM STATUS (ថែមថ្មី) =====
    status_group = QGroupBox("📊 System Status (ស្ថានភាពប្រព័ន្ធ)")
    status_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
    status_layout = QVBoxLayout()

    # System Info Grid
    info_grid = QFormLayout()
    info_grid.setSpacing(10)

    # Python Version
    import platform
    lbl_python = QLabel(f"✓ Python {platform.python_version()}")
    lbl_python.setStyleSheet("color: #28a745; font-weight: bold;")
    info_grid.addRow("Python:", lbl_python)

    # GPU Status
    gpu_status = self._get_gpu_status()
    lbl_gpu = QLabel(gpu_status["text"])
    lbl_gpu.setStyleSheet(f"color: {gpu_status['color']}; font-weight: bold;")
    info_grid.addRow("GPU:", lbl_gpu)

    # FFmpeg Status
    ffmpeg_status = self._get_ffmpeg_status()
    lbl_ffmpeg = QLabel(ffmpeg_status["text"])
    lbl_ffmpeg.setStyleSheet(f"color: {ffmpeg_status['color']}; font-weight: bold;")
    info_grid.addRow("FFmpeg:", lbl_ffmpeg)

    # Disk Space
    import shutil
    try:
        usage = shutil.disk_usage(".")
        free_gb = usage.free / (1024**3)
        lbl_disk = QLabel(f"✓ {free_gb:.1f} GB Free")
        lbl_disk.setStyleSheet("color: #28a745; font-weight: bold;")
    except:
        lbl_disk = QLabel("⚠ Unknown")
        lbl_disk.setStyleSheet("color: #ffc107;")
    info_grid.addRow("Disk:", lbl_disk)

    status_layout.addLayout(info_grid)
    status_group.setLayout(status_layout)
    main_layout.addWidget(status_group)

    # ===== ២. QUICK ACTIONS (ថែមថ្មី) =====
    quick_group = QGroupBox("⚡ Quick Actions (សកម្មភាពរហ័ស)")
    quick_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
    quick_layout = QHBoxLayout()

    # Verify Installation Button
    btn_verify = QPushButton("🔍 Verify Installation")
    btn_verify.clicked.connect(self._run_verification)
    btn_verify.setToolTip("ពិនិត្យមើលការដំឡើងទាំងអស់")
    btn_verify.setStyleSheet("""
        QPushButton {
            background-color: #007bff;
            color: white;
            font-weight: bold;
            padding: 8px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
    """)
    quick_layout.addWidget(btn_verify)

    # Test GPU Button
    btn_gpu_test = QPushButton("🎮 Test GPU")
    btn_gpu_test.clicked.connect(self._test_gpu)
    btn_gpu_test.setToolTip("តេស្តមើល GPU")
    btn_gpu_test.setStyleSheet("""
        QPushButton {
            background-color: #28a745;
            color: white;
            font-weight: bold;
            padding: 8px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #1e7e34;
        }
    """)
    quick_layout.addWidget(btn_gpu_test)

    # Clear Cache Button
    btn_clear = QPushButton("🧹 Clear Cache")
    btn_clear.clicked.connect(self.clear_cache_manual)
    btn_clear.setToolTip("សម្អាត Cache + RAM")
    btn_clear.setStyleSheet("""
        QPushButton {
            background-color: #ffc107;
            color: #333;
            font-weight: bold;
            padding: 8px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #e0a800;
        }
    """)
    quick_layout.addWidget(btn_clear)

    quick_group.setLayout(quick_layout)
    main_layout.addWidget(quick_group)

    # ===== ៣. REQUIRED SOFTWARE =====
    dep_group = QGroupBox("📦 Required Software (កម្មវិធីចាំបាច់)")
    dep_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
    dep_layout = QVBoxLayout()

    # FFmpeg Section
    ffmpeg_section = QHBoxLayout()
    lbl_ffmpeg_label = QLabel("FFmpeg:")
    lbl_ffmpeg_label.setStyleSheet("font-weight: bold; min-width: 80px;")
    ffmpeg_section.addWidget(lbl_ffmpeg_label)

    btn_ffmpeg_install = QPushButton("⬇️ Install FFmpeg (Auto)")
    btn_ffmpeg_install.clicked.connect(self.install_ffmpeg_auto)
    btn_ffmpeg_install.setToolTip("ទាញយក និងដំឡើង FFmpeg ដោយស្វ័យប្រវត្តិ")
    btn_ffmpeg_install.setStyleSheet("""
        QPushButton {
            background-color: #17a2b8;
            color: white;
            font-weight: bold;
            padding: 6px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #138496;
        }
    """)
    ffmpeg_section.addWidget(btn_ffmpeg_install)

    # Status indicator
    self.lbl_ffmpeg_status = QLabel()
    self._update_ffmpeg_status_label()
    self.lbl_ffmpeg_status.setStyleSheet("font-weight: bold;")
    ffmpeg_section.addWidget(self.lbl_ffmpeg_status)

    dep_layout.addLayout(ffmpeg_section)

    # VC++ Section
    vc_section = QHBoxLayout()
    lbl_vc_label = QLabel("VC++ Redist:")
    lbl_vc_label.setStyleSheet("font-weight: bold; min-width: 80px;")
    vc_section.addWidget(lbl_vc_label)

    btn_vc_install = QPushButton("⬇️ Install VC++")
    btn_vc_install.clicked.connect(self.download_vc)
    btn_vc_install.setToolTip("ដំឡើង VC++ Redistributable")
    btn_vc_install.setStyleSheet("""
        QPushButton {
            background-color: #6c757d;
            color: white;
            font-weight: bold;
            padding: 6px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #545b62;
        }
    """)
    vc_section.addWidget(btn_vc_install)

    vc_section.addStretch()
    dep_layout.addLayout(vc_section)

    # Download Progress
    self.dl_progress = QProgressBar()
    self.dl_progress.setVisible(False)
    self.dl_progress.setStyleSheet("""
        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 4px;
            text-align: center;
            height: 20px;
        }
        QProgressBar::chunk {
            background-color: #007bff;
            border-radius: 3px;
        }
    """)
    dep_layout.addWidget(self.dl_progress)

    dep_group.setLayout(dep_layout)
    main_layout.addWidget(dep_group)

    # ===== ៤. AUTO-SAVE =====
    as_group = QGroupBox("💾 Auto-Save (រក្សាទុកស្វ័យប្រវត្តិ)")
    as_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
    as_layout = QHBoxLayout()

    self.chk_autosave = QCheckBox("Enable Auto-Save")
    self.chk_autosave.setChecked(self.app_settings.get("autosave_enabled", False))
    self.chk_autosave.stateChanged.connect(self.update_autosave_timer)
    as_layout.addWidget(self.chk_autosave)

    as_layout.addWidget(QLabel("Interval:"))
    self.sb_autosave_interval = QSpinBox()
    self.sb_autosave_interval.setRange(1, 60)
    self.sb_autosave_interval.setSuffix(" min")
    self.sb_autosave_interval.setValue(self.app_settings.get("autosave_interval", 5))
    self.sb_autosave_interval.valueChanged.connect(self.update_autosave_timer)
    as_layout.addWidget(self.sb_autosave_interval)

    as_layout.addStretch()
    as_group.setLayout(as_layout)
    main_layout.addWidget(as_group)

    # ===== ៥. CONFIG MANAGEMENT (ថែមថ្មី) =====
    config_group = QGroupBox("⚙️ Configuration (ការកំណត់)")
    config_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
    config_layout = QHBoxLayout()

    # Export Config
    btn_export = QPushButton("📤 Export Config")
    btn_export.clicked.connect(self._export_config)
    btn_export.setToolTip("រក្សាទុកការកំណត់ជាឯកសារ")
    config_layout.addWidget(btn_export)

    # Import Config
    btn_import = QPushButton("📥 Import Config")
    btn_import.clicked.connect(self._import_config)
    btn_import.setToolTip("ផ្ទុកការកំណត់ពីឯកសារ")
    config_layout.addWidget(btn_import)

    # Reset Config
    btn_reset = QPushButton("🔄 Reset Settings")
    btn_reset.clicked.connect(self._reset_settings)
    btn_reset.setToolTip("កំណត់ការកំណត់ឡើងវិញ")
    btn_reset.setStyleSheet("""
        QPushButton {
            background-color: #dc3545;
            color: white;
            font-weight: bold;
            padding: 6px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #c82333;
        }
    """)
    config_layout.addWidget(btn_reset)

    config_group.setLayout(config_layout)
    main_layout.addWidget(config_group)

    # ===== ៦. LOGS =====
    log_group = QGroupBox("📝 Logs (កំណត់ហេតុ)")
    log_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
    log_layout = QVBoxLayout()

    # Log controls
    log_controls = QHBoxLayout()

    btn_clear_log = QPushButton("🗑️ Clear Logs")
    btn_clear_log.clicked.connect(lambda: self.log_box.clear())
    log_controls.addWidget(btn_clear_log)

    btn_save_log = QPushButton("💾 Save Logs")
    btn_save_log.clicked.connect(self._save_logs)
    log_controls.addWidget(btn_save_log)

    log_controls.addStretch()
    log_layout.addLayout(log_controls)

    # Log box
    self.log_box = QTextEdit()
    self.log_box.setReadOnly(True)
    self.log_box.setPlaceholderText("Logs will appear here...")
    self.log_box.setMaximumHeight(200)
    log_layout.addWidget(self.log_box)

    log_group.setLayout(log_layout)
    main_layout.addWidget(log_group)

    # ===== ៧. DEVELOPER INFO =====
    dev_group = QGroupBox("👨‍💻 About Developer (ព័ត៌មានអ្នកបង្កើត)")
    dev_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
    dev_layout = QFormLayout()

    lbl_name = QLabel("នូរ សារ៉ាត់ (Nou Sarat)")
    lbl_name.setStyleSheet("font-weight: bold; font-size: 11pt; color: #2b6cb0;")
    dev_layout.addRow("Name:", lbl_name)

    lbl_tele = QLabel("096 22 11 947")
    lbl_tele.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # type: ignore[attr-defined]
    lbl_tele.setStyleSheet("color: #6c757d;")
    dev_layout.addRow("Telegram:", lbl_tele)

    lbl_yt = QLabel('<a href="https://www.youtube.com/@TechFree2026" style="color: #dc3545; text-decoration: none;">▶ www.youtube.com/@TechFree2026</a>')
    lbl_yt.setOpenExternalLinks(True)
    dev_layout.addRow("YouTube:", lbl_yt)

    # Version
    lbl_version = QLabel("v15.6 FULL RVC WEBUI PRO")
    lbl_version.setStyleSheet("font-weight: bold; color: #28a745;")
    dev_layout.addRow("Version:", lbl_version)

    dev_group.setLayout(dev_layout)
    main_layout.addWidget(dev_group)

    # Add stretch to push everything up
    main_layout.addStretch()

    scroll_area.setWidget(widget)
    return scroll_area


# =============================
# Helper Methods (ថែមថ្មី)
# =============================

def _get_gpu_status(self):
    """Get GPU status for display"""
    import subprocess
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        ).decode("utf-8", errors="ignore").strip()

        if output:
            gpu_name = output.split("\n")[0].strip()
            return {
                "text": f"✓ {gpu_name}",
                "color": "#28a745"
            }
    except:
        pass

    return {
        "text": "⚠ No GPU (CPU Mode)",
        "color": "#ffc107"
    }


def _get_ffmpeg_status(self):
    """Get FFmpeg status for display"""
    import os
    import subprocess

    ffmpeg_path = self.app_settings.get("ffmpeg_path", "")

    if ffmpeg_path and os.path.exists(ffmpeg_path):
        try:
            output = subprocess.check_output(
                [ffmpeg_path, "-version"],
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode("utf-8", errors="ignore")

            version = output.split("\n")[0].strip()[:60]
            return {
                "text": f"✓ {version}",
                "color": "#28a745"
            }
        except:
            return {
                "text": f"⚠ Found (Error)",
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
                "text": f"✓ Found (Auto)",
                "color": "#28a745"
            }

    return {
        "text": "✗ Not Found",
        "color": "#dc3545"
    }


def _update_ffmpeg_status_label(self):
    """Update FFmpeg status label"""
    status = self._get_ffmpeg_status()
    self.lbl_ffmpeg_status.setText(status["text"])
    self.lbl_ffmpeg_status.setStyleSheet(f"color: {status['color']}; font-weight: bold;")


def _run_verification(self):
    """Run verification script"""
    import subprocess
    import sys

    self.log("🔍 Running installation verification...")

    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_installation.py")
        if os.path.exists(script_path):
            subprocess.Popen([sys.executable, script_path])
            self.log("✓ Verification script started")
        else:
            self.log("✗ verify_installation.py not found")
    except Exception as e:
        self.log(f"✗ Error: {e}")


def _test_gpu(self):
    """Test GPU"""
    import subprocess
    import sys

    self.log("🎮 Testing GPU...")

    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_gpu.py")
        if os.path.exists(script_path):
            subprocess.Popen([sys.executable, script_path])
            self.log("✓ GPU test started")
        else:
            self.log("✗ test_gpu.py not found")
    except Exception as e:
        self.log(f"✗ Error: {e}")


def install_ffmpeg_auto(self):
    """Install FFmpeg using install_ffmpeg.py"""
    import subprocess
    import sys

    self.log("⬇️ Starting FFmpeg auto-installation...")
    self.dl_progress.setVisible(True)
    self.dl_progress.setValue(0)

    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_ffmpeg.py")
        if os.path.exists(script_path):
            # Run in separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.log("✓ FFmpeg installer started")
            self.log("→ Please wait for installer to complete...")

            # Update status after delay
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(5000, lambda: self._update_ffmpeg_status_label())
        else:
            self.log("✗ install_ffmpeg.py not found")
            self.dl_progress.setVisible(False)
    except Exception as e:
        self.log(f"✗ Error: {e}")
        self.dl_progress.setVisible(False)


def _export_config(self):
    """Export configuration to file"""
    from PyQt5.QtWidgets import QFileDialog
    import json

    file_path, _ = QFileDialog.getSaveFileName(
        self, "Export Config", "", "JSON Files (*.json)"
    )

    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.app_settings, f, indent=2, ensure_ascii=False)
            self.log(f"✓ Config exported to: {file_path}")
        except Exception as e:
            self.log(f"✗ Export failed: {e}")


def _import_config(self):
    """Import configuration from file"""
    from PyQt5.QtWidgets import QFileDialog, QMessageBox
    import json

    file_path, _ = QFileDialog.getOpenFileName(
        self, "Import Config", "", "JSON Files (*.json)"
    )

    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.app_settings.update(config)
            self.save_app_settings()
            self.log(f"✓ Config imported from: {file_path}")
            QMessageBox.information(self, "Success", "Configuration imported successfully!")
        except Exception as e:
            self.log(f"✗ Import failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to import config:\n{e}")


def _reset_settings(self):
    """Reset all settings to defaults"""
    from PyQt5.QtWidgets import QMessageBox

    reply = QMessageBox.question(
        self,
        "Reset Settings",
        "Are you sure you want to reset all settings to defaults?\n(តើអ្នកប្រាកដថាចង់កំណត់ឡើងវិញមែនទេ?)",
        QMessageBox.Yes | QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        self.app_settings = {
            "autosave_enabled": False,
            "autosave_interval": 5,
            "ffmpeg_path": ""
        }
        self.save_app_settings()
        self.chk_autosave.setChecked(False)
        self.sb_autosave_interval.setValue(5)
        self.log("✓ Settings reset to defaults")


def _save_logs(self):
    """Save logs to file"""
    from PyQt5.QtWidgets import QFileDialog
    import datetime

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
