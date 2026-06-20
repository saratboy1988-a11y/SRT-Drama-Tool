# -*- mode: python ; coding: utf-8 -*-

# Fix RecursionError: Increase recursion limit BEFORE anything else
import sys
sys.setrecursionlimit(5000)
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# Manually collect edge_tts dependencies (avoid collect_all which pulls too much)
datas = [
    ('version.txt', '.'),
    ('app_settings.json', '.'),
    ('requirements.txt', '.'),
    ('license_server_config.json', '.'),
    ('License Server Launcher.py', '.'),
    ('Run License Server.bat', '.'),
    ('license_server/license_api.py', 'license_server'),
    ('license_server/requirements.txt', 'license_server'),
    ('license_server/README.md', 'license_server'),
    ('install_ffmpeg.py', '.'),
    ('install_pytorch.py', '.'),
    ('verify_installation.py', '.'),
    ('test_gpu.py', '.'),
    ('logo.ico', '.'),
    ('srt_drama_tool.png', '.'),
    ('splash_logo.png', '.'),
]

for package_name in ('demucs', 'dora', 'omegaconf', 'openunmix', 'julius'):
    datas += collect_data_files(package_name)

binaries = []
for package_name in ('torchaudio', 'torch'):
    binaries += collect_dynamic_libs(package_name)

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
    'torch',
    'torchaudio',
    'demucs',
    'demucs.separate',
    'openunmix',
    'julius',
    'lameenc',
    'einops',
    'dora',
    'omegaconf',
    # asyncio is stdlib - do NOT add to hiddenimports (causes circular import)
]

for package_name in ('demucs', 'dora', 'omegaconf', 'openunmix', 'julius'):
    hiddenimports += collect_submodules(package_name)

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
    upx=False,
    upx_exclude=[],
    name='SRT Drama Tool',
)
