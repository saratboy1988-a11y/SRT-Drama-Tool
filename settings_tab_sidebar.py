# -*- coding: utf-8 -*-
"""
Settings Tab - Professional Sidebar Menu Design
វិធីប្រើ: ជំនួស build_settings_tab() ក្នុង RVC Tool.py
"""

import os
import json
import shutil
import platform
import subprocess
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QGridLayout, QStackedLayout,
    QLabel, QPushButton, QCheckBox, QSpinBox, QProgressBar, QTextEdit,
    QGroupBox, QScrollArea, QFileDialog, QMessageBox
)

# =============================
# Settings Tab (Professional Sidebar Menu Design)
# =============================

def build_settings_tab(self):
    """Build professional Settings tab with sidebar menu"""
    from PyQt5.QtCore import QSize

    # Main container
    main_widget = QWidget()
    main_layout = QHBoxLayout(main_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # ===== LEFT SIDEBAR MENU =====
    sidebar = QWidget()
    sidebar.setFixedWidth(220)
    sidebar.setStyleSheet("""
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2c3e50, stop:1 #34495e);
        }
    """)
    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setContentsMargins(0, 0, 0, 0)
    sidebar_layout.setSpacing(2)

    # Header
    header = QLabel("⚙️ SETTINGS")
    header.setAlignment(Qt.AlignCenter)  # type: ignore[attr-defined]
    header.setFixedHeight(60)
    header.setStyleSheet("""
        QLabel {
            color: white;
            font-size: 14pt;
            font-weight: bold;
            border-bottom: 2px solid #34495e;
            background-color: #1a252f;
        }
    """)
    sidebar_layout.addWidget(header)

    # Menu buttons container
    menu_container = QWidget()
    menu_layout = QVBoxLayout(menu_container)
    menu_layout.setContentsMargins(10, 10, 10, 10)
    menu_layout.setSpacing(5)

    # Create menu buttons
    self.menu_buttons = {}
    menu_items = [
        ("system", "💻", "System Info"),
        ("software", "📦", "Software"),
        ("actions", "⚡", "Quick Actions"),
        ("autosave", "💾", "Auto-Save"),
        ("config", "⚙️", "Configuration"),
        ("logs", "📝", "Logs"),
        ("about", "👨‍💻", "About")
    ]

    for key, icon, text in menu_items:
        btn = QPushButton(f"{icon}  {text}")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ecf0f1;
                text-align: left;
                padding-left: 15px;
                font-size: 11pt;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background-color: #3498db;
                font-weight: bold;
            }
        """)
        btn.setCheckable(True)
        btn.clicked.connect(lambda checked, k=key: self._switch_settings_page(k))
        self.menu_buttons[key] = btn
        menu_layout.addWidget(btn)

    menu_layout.addStretch()
    sidebar_layout.addWidget(menu_container)

    # Footer with version
    footer = QLabel("v15.6 PRO")
    footer.setAlignment(Qt.AlignCenter)  # type: ignore[attr-defined]
    footer.setFixedHeight(40)
    footer.setStyleSheet("""
        QLabel {
            color: #7f8c8d;
            font-size: 9pt;
            border-top: 1px solid #34495e;
        }
    """)
    sidebar_layout.addWidget(footer)

    # ===== RIGHT CONTENT AREA =====
    content_widget = QWidget()
    content_widget.setStyleSheet("""
        QWidget {
            background-color: #f8f9fa;
        }
    """)
    self.content_layout = QStackedLayout(content_widget)

    # Create pages
    self._create_system_info_page()
    self._create_software_page()
    self._create_quick_actions_page()
    self._create_autosave_page()
    self._create_config_page()
    self._create_logs_page()
    self._create_about_page()

    # Add to main layout
    main_layout.addWidget(sidebar)
    main_layout.addWidget(content_widget, 1)

    # Set default page
    self._switch_settings_page("system")
    return main_widget


def _switch_settings_page(self, page_key):
    """Switch to selected settings page"""
    # Update button states
    for key, btn in self.menu_buttons.items():
        btn.setChecked(key == page_key)

    # Switch page
    page_index = {
        "system": 0,
        "software": 1,
        "actions": 2,
        "autosave": 3,
        "config": 4,
        "logs": 5,
        "about": 6
    }
    self.content_layout.setCurrentIndex(page_index[page_key])


def _create_styled_button(self, text, color, hover_color=None):
    """Create professional styled button"""
    if hover_color is None:
        hover_color = color

    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            color: white;
            font-weight: bold;
            padding: 10px 16px;
            border-radius: 6px;
            font-size: 10pt;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {hover_color};
        }}
    """)
    return btn


def _create_styled_group(self, title, layout):
    """Create professional styled group box"""
    group = QGroupBox(title)
    group.setFont(QFont("Segoe UI", 11, QFont.Bold))
    group.setLayout(layout)
    group.setStyleSheet("""
        QGroupBox {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
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


def _create_system_info_page(self):
    """Create System Info page"""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)

    # Title
    title = QLabel("💻 System Information")
    title.setFont(QFont("Segoe UI", 16, QFont.Bold))
    title.setStyleSheet("color: #2c3e50; padding-bottom: 10px;")
    layout.addWidget(title)

    # Scroll area
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("border: none;")

    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)
    scroll_layout.setSpacing(15)

    # System Status Group
    status_layout = QFormLayout()
    status_layout.setSpacing(12)

    # Python
    lbl_python = QLabel(f"✓ Python {platform.python_version()}")
    lbl_python.setStyleSheet("color: #28a745; font-weight: bold; font-size: 11pt;")
    status_layout.addRow("Python:", lbl_python)

    # GPU
    gpu_status = self._get_gpu_status()
    lbl_gpu = QLabel(gpu_status["text"])
    lbl_gpu.setStyleSheet(f"color: {gpu_status['color']}; font-weight: bold; font-size: 11pt;")
    status_layout.addRow("GPU:", lbl_gpu)

    # FFmpeg
    ffmpeg_status = self._get_ffmpeg_status()
    lbl_ffmpeg = QLabel(ffmpeg_status["text"])
    lbl_ffmpeg.setStyleSheet(f"color: {ffmpeg_status['color']}; font-weight: bold; font-size: 11pt;")
    status_layout.addRow("FFmpeg:", lbl_ffmpeg)

    # Disk
    try:
        usage = shutil.disk_usage(".")
        free_gb = usage.free / (1024**3)
        lbl_disk = QLabel(f"✓ {free_gb:.1f} GB Free")
        lbl_disk.setStyleSheet("color: #28a745; font-weight: bold; font-size: 11pt;")
    except:
        lbl_disk = QLabel("⚠ Unknown")
        lbl_disk.setStyleSheet("color: #ffc107; font-size: 11pt;")
    status_layout.addRow("Disk Space:", lbl_disk)

    # OS
    lbl_os = QLabel(f"{platform.system()} {platform.release()}")
    lbl_os.setStyleSheet("font-weight: bold; font-size: 11pt;")
    status_layout.addRow("Operating System:", lbl_os)

    # Machine
    lbl_machine = QLabel(platform.machine())
    lbl_machine.setStyleSheet("font-weight: bold; font-size: 11pt;")
    status_layout.addRow("Architecture:", lbl_machine)

    status_group = self._create_styled_group("System Status", status_layout)
    scroll_layout.addWidget(status_group)
    scroll_layout.addStretch()

    scroll.setWidget(scroll_widget)
    layout.addWidget(scroll)

    self.content_layout.addWidget(page)


def _create_software_page(self):
    """Create Required Software page"""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)

    # Title
    title = QLabel("📦 Required Software")
    title.setFont(QFont("Segoe UI", 16, QFont.Bold))
    title.setStyleSheet("color: #2c3e50; padding-bottom: 10px;")
    layout.addWidget(title)

    # Scroll area
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("border: none;")

    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)
    scroll_layout.setSpacing(15)

    # FFmpeg Section
    ffmpeg_layout = QVBoxLayout()
    ffmpeg_layout.setSpacing(10)

    ffmpeg_desc = QLabel("FFmpeg is required for audio/video processing")
    ffmpeg_desc.setStyleSheet("color: #6c757d; font-size: 10pt;")
    ffmpeg_layout.addWidget(ffmpeg_desc)

    ffmpeg_btn = self._create_styled_button("⬇️ Install FFmpeg (Auto)", "#17a2b8", "#138496")
    ffmpeg_btn.clicked.connect(self.install_ffmpeg_auto)
    ffmpeg_layout.addWidget(ffmpeg_btn)

    # Status
    self.lbl_ffmpeg_status = QLabel()
    self._update_ffmpeg_status_label()
    self.lbl_ffmpeg_status.setFont(QFont("Segoe UI", 10))
    ffmpeg_layout.addWidget(self.lbl_ffmpeg_status)

    ffmpeg_group = self._create_styled_group("FFmpeg (Audio/Video Processing)", ffmpeg_layout)
    scroll_layout.addWidget(ffmpeg_group)

    # VC++ Section
    vc_layout = QVBoxLayout()
    vc_layout.setSpacing(10)

    vc_desc = QLabel("Visual C++ Redistributable is required for some features")
    vc_desc.setStyleSheet("color: #6c757d; font-size: 10pt;")
    vc_layout.addWidget(vc_desc)

    vc_btn = self._create_styled_button("⬇️ Install VC++ Redistributable", "#6c757d", "#545b62")
    vc_btn.clicked.connect(self.download_vc)
    vc_layout.addWidget(vc_btn)

    vc_group = self._create_styled_group("VC++ Redistributable", vc_layout)
    scroll_layout.addWidget(vc_group)

    # Progress bar
    self.dl_progress = QProgressBar()
    self.dl_progress.setVisible(False)
    self.dl_progress.setFixedHeight(8)
    self.dl_progress.setStyleSheet("""
        QProgressBar {
            border: 1px solid #dee2e6;
            border-radius: 4px;
            text-align: center;
            background-color: #e9ecef;
        }
        QProgressBar::chunk {
            background-color: #007bff;
            border-radius: 3px;
        }
    """)
    scroll_layout.addWidget(self.dl_progress)

    scroll_layout.addStretch()
    scroll.setWidget(scroll_widget)
    layout.addWidget(scroll)

    self.content_layout.addWidget(page)


def _create_quick_actions_page(self):
    """Create Quick Actions page"""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)

    # Title
    title = QLabel("⚡ Quick Actions")
    title.setFont(QFont("Segoe UI", 16, QFont.Bold))
    title.setStyleSheet("color: #2c3e50; padding-bottom: 10px;")
    layout.addWidget(title)

    # Scroll area
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("border: none;")

    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)
    scroll_layout.setSpacing(15)

    # Actions grid
    actions_layout = QGridLayout()
    actions_layout.setSpacing(15)

    # Verify Installation
    btn_verify = self._create_styled_button("🔍 Verify Installation", "#007bff", "#0056b3")
    btn_verify.setFixedHeight(60)
    btn_verify.clicked.connect(self._run_verification)
    actions_layout.addWidget(btn_verify, 0, 0)

    # Test GPU
    btn_gpu = self._create_styled_button("🎮 Test GPU", "#28a745", "#1e7e34")
    btn_gpu.setFixedHeight(60)
    btn_gpu.clicked.connect(self._test_gpu)
    actions_layout.addWidget(btn_gpu, 0, 1)

    # Clear Cache
    btn_cache = self._create_styled_button("🧹 Clear Cache", "#ffc107", "#e0a800")
    btn_cache.setFixedHeight(60)
    btn_cache.setStyleSheet(btn_cache.styleSheet().replace("white", "#333"))
    btn_cache.clicked.connect(self.clear_cache_manual)
    actions_layout.addWidget(btn_cache, 1, 0)

    # Refresh Status
    btn_refresh = self._create_styled_button("🔄 Refresh Status", "#6f42c1", "#5a32a3")
    btn_refresh.setFixedHeight(60)
    btn_refresh.clicked.connect(lambda: self._update_ffmpeg_status_label())
    actions_layout.addWidget(btn_refresh, 1, 1)

    actions_group = self._create_styled_group("Available Actions", actions_layout)
    scroll_layout.addWidget(actions_group)
    scroll_layout.addStretch()

    scroll.setWidget(scroll_widget)
    layout.addWidget(scroll)

    self.content_layout.addWidget(page)


def _create_autosave_page(self):
    """Create Auto-Save page"""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)

    # Title
    title = QLabel("💾 Auto-Save Settings")
    title.setFont(QFont("Segoe UI", 16, QFont.Bold))
    title.setStyleSheet("color: #2c3e50; padding-bottom: 10px;")
    layout.addWidget(title)

    # Scroll area
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("border: none;")

    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)
    scroll_layout.setSpacing(15)

    # Auto-Save Group
    autosave_layout = QVBoxLayout()
    autosave_layout.setSpacing(15)

    desc = QLabel("Automatically save your work at regular intervals to prevent data loss")
    desc.setStyleSheet("color: #6c757d; font-size: 10pt;")
    autosave_layout.addWidget(desc)

    # Enable checkbox
    self.chk_autosave = QCheckBox("Enable Auto-Save")
    self.chk_autosave.setChecked(self.app_settings.get("autosave_enabled", False))
    self.chk_autosave.stateChanged.connect(self.update_autosave_timer)
    self.chk_autosave.setFont(QFont("Segoe UI", 11))
    autosave_layout.addWidget(self.chk_autosave)

    # Interval
    interval_layout = QHBoxLayout()
    interval_layout.addWidget(QLabel("Save every:"))
    self.sb_autosave_interval = QSpinBox()
    self.sb_autosave_interval.setRange(1, 60)
    self.sb_autosave_interval.setSuffix(" min")
    self.sb_autosave_interval.setValue(self.app_settings.get("autosave_interval", 5))
    self.sb_autosave_interval.valueChanged.connect(self.update_autosave_timer)
    self.sb_autosave_interval.setFont(QFont("Segoe UI", 11))
    interval_layout.addWidget(self.sb_autosave_interval)
    interval_layout.addStretch()
    autosave_layout.addLayout(interval_layout)

    autosave_group = self._create_styled_group("Auto-Save Configuration", autosave_layout)
    scroll_layout.addWidget(autosave_group)

    # Start timer if enabled
    self.update_autosave_timer()

    scroll_layout.addStretch()
    scroll.setWidget(scroll_widget)
    layout.addWidget(scroll)

    self.content_layout.addWidget(page)


def _create_config_page(self):
    """Create Configuration page"""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)

    # Title
    title = QLabel("⚙️ Configuration Management")
    title.setFont(QFont("Segoe UI", 16, QFont.Bold))
    title.setStyleSheet("color: #2c3e50; padding-bottom: 10px;")
    layout.addWidget(title)

    # Scroll area
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("border: none;")

    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)
    scroll_layout.setSpacing(15)

    # Config actions
    config_layout = QVBoxLayout()
    config_layout.setSpacing(12)

    desc = QLabel("Export, import, or reset your configuration settings")
    desc.setStyleSheet("color: #6c757d; font-size: 10pt;")
    config_layout.addWidget(desc)

    # Export
    btn_export = self._create_styled_button("📤 Export Configuration", "#28a745", "#1e7e34")
    btn_export.clicked.connect(self._export_config)
    config_layout.addWidget(btn_export)

    # Import
    btn_import = self._create_styled_button("📥 Import Configuration", "#007bff", "#0056b3")
    btn_import.clicked.connect(self._import_config)
    config_layout.addWidget(btn_import)

    # Reset
    btn_reset = self._create_styled_button("🔄 Reset to Defaults", "#dc3545", "#c82333")
    btn_reset.clicked.connect(self._reset_settings)
    config_layout.addWidget(btn_reset)

    config_group = self._create_styled_group("Configuration Actions", config_layout)
    scroll_layout.addWidget(config_group)
    scroll_layout.addStretch()

    scroll.setWidget(scroll_widget)
    layout.addWidget(scroll)

    self.content_layout.addWidget(page)


def _create_logs_page(self):
    """Create Logs page"""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)

    # Title
    title = QLabel("📝 Activity Logs")
    title.setFont(QFont("Segoe UI", 16, QFont.Bold))
    title.setStyleSheet("color: #2c3e50; padding-bottom: 10px;")
    layout.addWidget(title)

    # Controls
    controls_layout = QHBoxLayout()

    btn_clear = self._create_styled_button("🗑️ Clear Logs", "#6c757d", "#545b62")
    btn_clear.setFixedHeight(40)
    btn_clear.clicked.connect(lambda: self.log_box.clear())
    controls_layout.addWidget(btn_clear)

    btn_save = self._create_styled_button("💾 Save Logs", "#17a2b8", "#138496")
    btn_save.setFixedHeight(40)
    btn_save.clicked.connect(self._save_logs)
    controls_layout.addWidget(btn_save)

    controls_layout.addStretch()
    layout.addLayout(controls_layout)

    # Log box
    self.log_box = QTextEdit()
    self.log_box.setReadOnly(True)
    self.log_box.setPlaceholderText("Logs will appear here...")
    self.log_box.setFont(QFont("Consolas", 9))
    self.log_box.setStyleSheet("""
        QTextEdit {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 10px;
        }
    """)
    layout.addWidget(self.log_box)

    self.content_layout.addWidget(page)


def _create_about_page(self):
    """Create About page"""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)

    # Title
    title = QLabel("👨‍💻 About Developer")
    title.setFont(QFont("Segoe UI", 16, QFont.Bold))
    title.setStyleSheet("color: #2c3e50; padding-bottom: 10px;")
    layout.addWidget(title)

    # Scroll area
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("border: none;")

    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)
    scroll_layout.setSpacing(15)

    # Developer Info Group
    dev_layout = QFormLayout()
    dev_layout.setSpacing(12)

    lbl_name = QLabel("នូរ សារ៉ាត់ (Nou Sarat)")
    lbl_name.setStyleSheet("font-weight: bold; font-size: 12pt; color: #2b6cb0;")
    dev_layout.addRow("Name:", lbl_name)

    lbl_tele = QLabel("096 22 11 947")
    lbl_tele.setTextInteractionFlags(Qt.TextSelectableByMouse)  # type: ignore
    lbl_tele.setStyleSheet("font-size: 11pt; color: #6c757d;")
    dev_layout.addRow("Telegram:", lbl_tele)

    lbl_yt = QLabel('<a href="https://www.youtube.com/@TechFree2026" style="color: #dc3545; text-decoration: none; font-weight: bold;">▶ www.youtube.com/@TechFree2026</a>')
    lbl_yt.setOpenExternalLinks(True)
    lbl_yt.setStyleSheet("font-size: 10pt;")
    dev_layout.addRow("YouTube:", lbl_yt)

    lbl_version = QLabel("v15.6 FULL RVC WEBUI PRO")
    lbl_version.setStyleSheet("font-weight: bold; font-size: 11pt; color: #28a745;")
    dev_layout.addRow("Version:", lbl_version)

    dev_group = self._create_styled_group("Developer Information", dev_layout)
    scroll_layout.addWidget(dev_group)

    # App Info
    app_layout = QVBoxLayout()
    app_layout.setSpacing(10)

    app_desc = QLabel("RVC Tool is a professional voice conversion application powered by AI technology. It allows you to convert text to speech and apply voice models to create high-quality audio content.")
    app_desc.setWordWrap(True)
    app_desc.setStyleSheet("color: #6c757d; font-size: 10pt; line-height: 1.5;")
    app_layout.addWidget(app_desc)

    app_group = self._create_styled_group("About This Application", app_layout)
    scroll_layout.addWidget(app_group)

    scroll_layout.addStretch()
    scroll.setWidget(scroll_widget)
    layout.addWidget(scroll)

    self.content_layout.addWidget(page)
