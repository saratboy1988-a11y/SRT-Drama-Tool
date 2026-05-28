# -*- coding: utf-8 -*-
"""
Export Tab - Professional Sidebar Menu Design
ជំនួស build_export_tab() ក្នុង RVC Tool.py
"""

import os
import json
import subprocess
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QGridLayout, QStackedWidget,
    QLabel, QPushButton, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox,
    QProgressBar, QLineEdit, QGroupBox, QScrollArea, QFileDialog, QMessageBox
)

# =============================
# Export Tab (Professional Sidebar Menu Design)
# =============================

def build_export_tab(self):
    """Build professional Export tab with sidebar menu"""

    # Main container with sidebar + content
    main_widget = QWidget()
    main_layout = QHBoxLayout(main_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # ===== SIDEBAR MENU =====
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

    # Title
    lbl_title = QLabel("📤 EXPORT")
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
    lbl_title.setAlignment(Qt.AlignCenter)  # type: ignore[attr-defined]
    sidebar_layout.addWidget(lbl_title)

    # Menu buttons
    self.export_menu_buttons = {}
    menu_items = [
        ("📁", "output", "Output Settings"),
        ("🎬", "video", "Video Processing"),
        ("🎵", "audio", "Audio Export"),
        ("📄", "subtitles", "Subtitles"),
        ("⚡", "process", "Process & Export")
    ]

    for icon, key, label in menu_items:
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
        btn.clicked.connect(lambda checked, k=key: self._show_export_page(k))
        sidebar_layout.addWidget(btn)
        self.export_menu_buttons[key] = btn

    sidebar_layout.addStretch()

    # Version at bottom
    lbl_version_bottom = QLabel("v15.6 PRO")
    lbl_version_bottom.setStyleSheet("""
        QLabel {
            color: #7f8c8d;
            font-size: 9pt;
            padding: 10px;
            border-top: 1px solid #34495e;
        }
    """)
    lbl_version_bottom.setAlignment(Qt.AlignCenter)  # type: ignore[attr-defined]
    sidebar_layout.addWidget(lbl_version_bottom)

    main_layout.addWidget(sidebar)

    # ===== CONTENT AREA =====
    content_area = QWidget()
    content_area.setStyleSheet("""
        QWidget {
            background-color: #f8f9fa;
        }
    """)
    content_layout = QVBoxLayout(content_area)
    content_layout.setContentsMargins(0, 0, 0, 0)

    # Stack widget for pages
    self.export_stack = QStackedWidget()
    self.export_stack.setStyleSheet("""
        QStackedWidget {
            background-color: white;
            border: none;
        }
    """)

    # Create pages
    self.export_stack.addWidget(self._create_output_settings_page())
    self.export_stack.addWidget(self._create_video_processing_page())
    self.export_stack.addWidget(self._create_audio_export_page())
    self.export_stack.addWidget(self._create_subtitles_page())
    self.export_stack.addWidget(self._create_process_export_page())

    content_layout.addWidget(self.export_stack)
    main_layout.addWidget(content_area, 1)

    # Select first menu item by default
    self._show_export_page("output")

    return main_widget


def _show_export_page(self, page_key):
    """Show selected export page"""
    # Update menu buttons
    for key, btn in self.export_menu_buttons.items():
        btn.setChecked(key == page_key)

    # Map page keys to indices
    page_map = {
        "output": 0,
        "video": 1,
        "audio": 2,
        "subtitles": 3,
        "process": 4
    }

    self.export_stack.setCurrentIndex(page_map.get(page_key, 0))


def _create_styled_export_group(self, title, layout):
    """Create professional styled group box for export"""
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


def _create_output_settings_page(self):
    """Create Output Settings page"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(30, 30, 30, 30)
    layout.setSpacing(20)

    # Header
    header = QLabel("📁 Output Settings (ការកំណត់)")
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

    # Output folder
    folder_group = self._create_styled_export_group("Output Folder", QVBoxLayout())
    folder_row = QHBoxLayout()

    self.output_folder = QLineEdit(self.app_settings.get("last_output_dir", ""))
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

    btn_browse = QPushButton("📂 Browse")
    btn_browse.setFixedHeight(45)
    btn_browse.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
    btn_browse.clicked.connect(self.select_folder)
    btn_browse.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #007bff, stop:1 #0056b3);
            color: white;
            font-size: 11pt;
            font-weight: bold;
            border-radius: 6px;
            padding: 0 20px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0056b3, stop:1 #004085);
        }
    """)
    folder_row.addWidget(btn_browse)

    btn_open = QPushButton("📂 Open Folder")
    btn_open.setFixedHeight(45)
    btn_open.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
    btn_open.clicked.connect(self.open_output_folder)
    btn_open.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #28a745, stop:1 #1e7e34);
            color: white;
            font-size: 11pt;
            font-weight: bold;
            border-radius: 6px;
            padding: 0 20px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1e7e34, stop:1 #155d27);
        }
    """)
    folder_row.addWidget(btn_open)

    folder_group.layout().addLayout(folder_row)
    layout.addWidget(folder_group)

    # Quality & Options
    quality_group = self._create_styled_export_group("Quality & Options", QVBoxLayout())

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

    quality_group.layout().addLayout(quality_row)

    # Options row
    opts_row = QHBoxLayout()

    self.chk_autoplay = QCheckBox("Auto-play after export")
    self.chk_autoplay.setChecked(self.app_settings.get("auto_play", True))
    self.chk_autoplay.setFont(QFont("Segoe UI", 10))
    opts_row.addWidget(self.chk_autoplay)

    opts_row.addStretch()
    quality_group.layout().addLayout(opts_row)

    layout.addWidget(quality_group)
    layout.addStretch()

    scroll.setWidget(widget)
    return scroll


def _create_video_processing_page(self):
    """Create Video Processing page"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(30, 30, 30, 30)
    layout.setSpacing(20)

    # Header
    header = QLabel("🎬 Video Processing (កែសម្រួលវីដេអូ)")
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

    # General settings
    general_group = self._create_styled_export_group("General Settings", QFormLayout())

    self.cb_codec = QComboBox()
    self.cb_codec.addItems(["H.264 (AVC) - Standard"])
    self.cb_codec.setEnabled(False)
    general_group.layout().addRow("Video Codec:", self.cb_codec)

    self.cb_resolution = QComboBox()
    self.cb_resolution.addItems(["Original (រក្សាដើម)", "1920x1080 (1080p)", "1280x720 (720p)", "720x480 (480p)", "3840x2160 (4K)"])
    self.cb_resolution.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
    general_group.layout().addRow("Resolution:", self.cb_resolution)

    self.cb_preset = QComboBox()
    self.cb_preset.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower"])
    self.cb_preset.setCurrentText("medium")
    self.cb_preset.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
    general_group.layout().addRow("Encoder Speed:", self.cb_preset)

    self.chk_gpu = QCheckBox("Use NVIDIA GPU (H.264 NVENC)")
    self.chk_gpu.setChecked(self.app_settings.get("use_gpu", True))
    self.chk_gpu.setFont(QFont("Segoe UI", 10))
    general_group.layout().addRow("Hardware Accel:", self.chk_gpu)

    self.chk_lip_sync = QCheckBox("Enable Lip-Sync (SRT Characters)")
    self.chk_lip_sync.setChecked(self.app_settings.get("enable_lip_sync", False))
    self.chk_lip_sync.setFont(QFont("Segoe UI", 10))
    self.chk_lip_sync.setToolTip("Apply lip-sync using detected SRT characters. Requires AI models (placeholder)")
    general_group.layout().addRow("Lip-Sync:", self.chk_lip_sync)

    self.sb_crf = QSpinBox()
    self.sb_crf.setRange(0, 51)
    self.sb_crf.setValue(23)
    self.sb_crf.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
    general_group.layout().addRow("Quality (CRF 0-51):", self.sb_crf)

    layout.addWidget(general_group)

    # Color & Crop
    color_group = self._create_styled_export_group("Color & Crop", QFormLayout())

    self.cb_crop_preset = QComboBox()
    self.cb_crop_preset.addItems(["Custom", "16:9 (YouTube Landscape)", "9:16 (TikTok/Reels)", "1:1 (Square)", "4:5 (Facebook)"])
    self.cb_crop_preset.currentIndexChanged.connect(self.on_crop_preset_changed)
    self.cb_crop_preset.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
    color_group.layout().addRow("Crop Preset:", self.cb_crop_preset)

    self.sb_brightness = QDoubleSpinBox()
    self.sb_brightness.setRange(-1.0, 1.0)
    self.sb_brightness.setSingleStep(0.1)
    self.sb_brightness.setValue(0.0)
    self.sb_brightness.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
    color_group.layout().addRow("Brightness:", self.sb_brightness)

    self.sb_contrast = QDoubleSpinBox()
    self.sb_contrast.setRange(-2.0, 2.0)
    self.sb_contrast.setSingleStep(0.1)
    self.sb_contrast.setValue(1.0)
    self.sb_contrast.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
    color_group.layout().addRow("Contrast:", self.sb_contrast)

    self.sb_saturation = QDoubleSpinBox()
    self.sb_saturation.setRange(0.0, 3.0)
    self.sb_saturation.setSingleStep(0.1)
    self.sb_saturation.setValue(1.0)
    self.sb_saturation.setStyleSheet("padding: 8px; font-size: 10pt; border: 2px solid #3498db; border-radius: 5px;")
    color_group.layout().addRow("Saturation:", self.sb_saturation)

    layout.addWidget(color_group)
    layout.addStretch()

    scroll.setWidget(widget)
    return scroll


def _create_audio_export_page(self):
    """Create Audio Export page"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(30, 30, 30, 30)
    layout.setSpacing(20)

    # Header
    header = QLabel("🎵 Audio Export (នាំចេញអូឌីយ៉ូ)")
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

    # Audio options
    audio_group = self._create_styled_export_group("Audio Options", QVBoxLayout())

    volume_row = QHBoxLayout()
    volume_row.addWidget(QLabel("Original Audio Volume:"))

    self.slider_orig_vol = QSlider(QT_HORIZONTAL)  # type: ignore
    self.slider_orig_vol.setRange(0, 100)
    self.slider_orig_vol.setValue(0)
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
    volume_row.addWidget(self.slider_orig_vol)

    audio_group.layout().addLayout(volume_row)

    # Export buttons
    export_layout = QHBoxLayout()

    btn_wav = QPushButton("🎵 Export WAV")
    btn_wav.setFixedHeight(60)
    btn_wav.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
    btn_wav.clicked.connect(self.export_wav)
    btn_wav.setStyleSheet("""
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
    export_layout.addWidget(btn_wav)

    audio_group.layout().addLayout(export_layout)

    layout.addWidget(audio_group)
    layout.addStretch()

    scroll.setWidget(widget)
    return scroll


def _create_subtitles_page(self):
    """Create Subtitles page"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(30, 30, 30, 30)
    layout.setSpacing(20)

    # Header
    header = QLabel("📄 Subtitles & Transcript (អត្ថបទ/ចំណងជើង)")
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

    # Options
    opts_group = self._create_styled_export_group("Subtitle Options", QVBoxLayout())

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

    opts_group.layout().addLayout(opts_layout)
    layout.addWidget(opts_group)

    # Export buttons
    export_group = self._create_styled_export_group("Export Subtitles", QHBoxLayout())

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
    export_group.layout().addWidget(btn_srt)

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
    export_group.layout().addWidget(btn_txt)

    layout.addWidget(export_group)
    layout.addStretch()

    scroll.setWidget(widget)
    return scroll


def _create_process_export_page(self):
    """Create Process & Export page"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(30, 30, 30, 30)
    layout.setSpacing(20)

    # Header
    header = QLabel("⚡ Process & Export (ដំណើរការ)")
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

    # Time range
    time_group = self._create_styled_export_group("Time Range (កាត់យកតាមម៉ោង)", QVBoxLayout())

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
    time_group.layout().addLayout(cut_layout)
    layout.addWidget(time_group)

    # Export buttons
    export_group = self._create_styled_export_group("Export Actions", QVBoxLayout())

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

    btn_mp4 = QPushButton("🎬 Export MP4 Dub")
    btn_mp4.setFixedHeight(60)
    btn_mp4.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
    btn_mp4.clicked.connect(self.export_mp4)
    btn_mp4.setStyleSheet("""
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
    btn_layout.addWidget(btn_mp4)

    export_group.layout().addLayout(btn_layout)

    # Progress bar
    self.export_progress = QProgressBar()
    self.export_progress.setValue(0)
    self.export_progress.setFixedHeight(30)
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
    export_group.layout().addWidget(self.export_progress)

    layout.addWidget(export_group)
    layout.addStretch()

    scroll.setWidget(widget)
    return scroll
