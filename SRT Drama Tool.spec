# -*- mode: python ; coding: utf-8 -*-

# Fix RecursionError: Increase recursion limit BEFORE anything else
import sys
sys.setrecursionlimit(5000)

# Manually collect edge_tts dependencies (avoid collect_all which pulls too much)
datas = [
    ('version.txt', '.'),
    ('app_settings.json', '.'),
    ('requirements.txt', '.'),
    ('license_server_config.json', '.'),
    ('install_ffmpeg.py', '.'),
    ('install_pytorch.py', '.'),
    ('verify_installation.py', '.'),
    ('test_gpu.py', '.'),
    ('logo.ico', '.'),
    ('srt_drama_tool.png', '.'),
    ('splash_logo.png', '.'),
]

binaries = []

hiddenimports = [
    'edge_tts',
    'edge_tts.communicate',
    'edge_tts.submaker',
    'edge_tts.util',
    'pydub',
    'pydub.audio_segment',
    'pydub.effects',
    'pygame',
    'pygame.mixer',
    'aiohttp',
    'certifi',
    # asyncio is stdlib - do NOT add to hiddenimports (causes circular import)
]

a = Analysis(
    ['SRT Drama Tool.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pandas',
        'sqlalchemy',
        'openpyxl',
        'matplotlib',
        'scipy',
        'numpy.testing',
        'IPython',
        'jupyter_client',
        'notebook',
        'tkinter',
        'PyQt5.QtTest',
        'cryptography',
        # Do NOT exclude asyncio - it's needed and will be auto-included
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='SRT Drama Tool',
    debug=False,
    bootloader_ignore_signals=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico',
    exclude_binaries=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SRT Drama Tool',
)
