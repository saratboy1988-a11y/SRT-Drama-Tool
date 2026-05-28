# -*- mode: python ; coding: utf-8 -*-
# install_ffmpeg.spec - Simple spec for FFmpeg installer script
# Only use this if you REALLY need install_ffmpeg.exe

import sys
sys.setrecursionlimit(2000)

a = Analysis(
    ['install_ffmpeg.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5',          # Not needed
        'pygame',         # Not needed
        'pydub',          # Not needed
        'edge_tts',       # Not needed
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='install_ffmpeg',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Must be True to show download progress
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='NONE',
)
