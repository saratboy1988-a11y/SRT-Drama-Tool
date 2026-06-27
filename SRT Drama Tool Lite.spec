# -*- mode: python ; coding: utf-8 -*-

# Lite online-dependency build: excludes PyTorch/Demucs AI packages from the EXE.
# Users install those later from Settings -> Required Software.
import sys
sys.setrecursionlimit(5000)
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

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

# NumPy is still useful for non-AI audio helpers and is small compared with Torch.
datas += collect_data_files('numpy')
binaries = collect_dynamic_libs('numpy')

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
    'numpy',
    'numpy.core',
    'numpy.core.multiarray',
    'numpy._core',
    'numpy._core.multiarray',
    'numpy._core._multiarray_umath',
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
        'torch',
        'torchaudio',
        'torchvision',
        'demucs',
        'dora',
        'dora_search',
        'omegaconf',
        'openunmix',
        'julius',
        'einops',
        'lameenc',
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
        'tensorboard',
        'torch.utils.tensorboard',
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
    name='SRT Drama Tool Lite',
)
