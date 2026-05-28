# -*- coding: utf-8 -*-
"""
PyTorch Auto Installer for SRT Drama Tool.
Installs CUDA PyTorch when an NVIDIA GPU is detected, with a CPU fallback.
"""

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import sysconfig

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "app_settings.json")
CUDA_INDEX_URL = "https://download.pytorch.org/whl/cu118"
CPU_INDEX_URL = "https://download.pytorch.org/whl/cpu"


def creation_flags() -> int:
    return subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def get_app_data_dir() -> str:
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        app_dir = os.path.join(app_data, "SRTDramaTool")
    else:
        app_dir = os.path.join(os.path.expanduser("~"), ".srt_drama_tool")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


APPDATA_CONFIG_FILE = os.path.join(get_app_data_dir(), "app_settings.json")


def detect_nvidia_gpu() -> bool:
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            stderr=subprocess.STDOUT,
            creationflags=creation_flags(),
        ).decode("utf-8", errors="ignore").strip()
        return bool(output)
    except Exception:
        return False


def get_pytorch_status() -> dict:
    status_code = """
import json
try:
    import torch
    print(json.dumps({
        "installed": True,
        "version": getattr(torch, "__version__", "unknown"),
        "cuda": bool(torch.cuda.is_available()),
    }))
except Exception:
    print(json.dumps({"installed": False, "version": None, "cuda": False}))
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", status_code],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            creationflags=creation_flags(),
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip().splitlines()[-1])
    except Exception:
        pass

    return {"installed": False, "version": None, "cuda": False}


def verify_pytorch_install(expect_cuda: bool) -> bool:
    verify_code = (
        "import torch; "
        "print(f'PyTorch version: {torch.__version__}'); "
        "print(f'CUDA available: {torch.cuda.is_available()}'); "
        f"raise SystemExit(0 if torch.cuda.is_available() == {expect_cuda!r} else 2)"
    )
    result = subprocess.run([sys.executable, "-c", verify_code], creationflags=creation_flags())
    return result.returncode == 0


def update_config_files(installed: bool, cuda: bool) -> None:
    for config_file in (CONFIG_FILE, APPDATA_CONFIG_FILE):
        try:
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
            else:
                config = {}

            config["pytorch_installed"] = bool(installed)
            config["pytorch_cuda"] = bool(cuda)

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✓ Updated {config_file}", flush=True)
        except Exception as e:
            print(f"⚠ Could not update {config_file}: {e}", flush=True)


def cleanup_stale_package_dirs() -> bool:
    """Remove pip backup directories left by interrupted torch/numpy installs."""
    site_package_dirs = {
        sysconfig.get_paths().get("purelib"),
        sysconfig.get_paths().get("platlib"),
    }
    stale_names = {"~orch", "~orchgen", "~umpy", "~umpy.libs"}
    cleaned = True

    for site_package_dir in sorted(path for path in site_package_dirs if path):
        for name in stale_names:
            stale_path = os.path.join(site_package_dir, name)
            if not os.path.exists(stale_path):
                continue
            try:
                shutil.rmtree(stale_path)
                print(f"Removed stale pip backup: {stale_path}", flush=True)
            except Exception as e:
                cleaned = False
                print(f"⚠ Could not remove stale pip backup {stale_path}: {e}", flush=True)

    return cleaned


def build_install_command(index_url: str, force_reinstall: bool = False) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "torch",
        "torchvision",
        "torchaudio",
        "--index-url",
        index_url,
        "--no-cache-dir",
        "--progress-bar",
        "off",
        "-U",
    ]
    if force_reinstall:
        cmd.append("--force-reinstall")
    return cmd


def run_pip_install(cmd: list[str]) -> int:
    print("-> Running command:", flush=True)
    print("   " + " ".join(cmd), flush=True)

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=creation_flags(),
    )

    last_percent = -1
    buffer = ""
    access_denied = False

    def handle_line(raw_line: str) -> None:
        nonlocal last_percent, access_denied
        line = raw_line.strip()
        if not line:
            return
        if "access is denied" in line.lower() or "[winerror 5]" in line.lower():
            access_denied = True

        progress_match = re.search(r"Progress\s+(\d+)\s+of\s+(\d+)", line)
        if progress_match:
            downloaded = int(progress_match.group(1))
            total = int(progress_match.group(2))
            if total > 0:
                percent = min(100, int(downloaded * 100 / total))
                if percent != last_percent:
                    last_percent = percent
                    print(f"  Downloading: {percent}%", flush=True)
            return

        print(line, flush=True)

    if process.stdout:
        while True:
            char = process.stdout.read(1)
            if char == "" and process.poll() is not None:
                break
            if char in ("\n", "\r"):
                handle_line(buffer)
                buffer = ""
            else:
                buffer += char

    if buffer:
        handle_line(buffer)

    return_code = process.wait()
    print(f"-> pip exited with code: {return_code}", flush=True)
    if access_denied:
        print("-> Windows denied access to a package file. Close SRT Drama Tool and all Python processes, then retry.", flush=True)
        return 5
    return return_code


def install_pytorch() -> bool:
    print("=" * 60)
    print("PyTorch Auto Installer for SRT Drama Tool")
    print("=" * 60)
    print()

    has_nvidia = detect_nvidia_gpu()
    current_status = get_pytorch_status()
    print(f"GPU Detection: {'NVIDIA GPU found' if has_nvidia else 'No NVIDIA GPU'}")
    if current_status["installed"]:
        print(f"Current PyTorch: {current_status['version']} | CUDA: {current_status['cuda']}")
    print()

    if current_status["installed"] and ((not has_nvidia) or current_status["cuda"]):
        print("✓ Existing PyTorch is usable. No reinstall needed.")
        update_config_files(True, current_status["cuda"])
        return True

    if not cleanup_stale_package_dirs():
        print()
        print("=" * 60)
        print("Could not clean previous failed PyTorch install files!")
        print("=" * 60)
        print("Troubleshooting:")
        print("  1. Close SRT Drama Tool and any running python.exe processes that use this virtual environment")
        print("  2. Delete leftover ~orch and ~umpy folders from .venv\\Lib\\site-packages")
        print("  3. Run the PyTorch installer again")
        update_config_files(False, False)
        return False

    if has_nvidia:
        print("Installing PyTorch with CUDA support...")
        print("Using: CUDA 11.8 wheel index")
        cmd = build_install_command(CUDA_INDEX_URL, force_reinstall=current_status["installed"])
        expected_cuda = True
    else:
        print("Installing PyTorch CPU version...")
        cmd = build_install_command(CPU_INDEX_URL)
        expected_cuda = False

    print()
    print("This may take 5-10 minutes depending on internet speed...")
    print()

    pip_returncode = run_pip_install(cmd)

    if pip_returncode != 0 and has_nvidia and pip_returncode != 5:
        print()
        print("⚠ CUDA PyTorch install failed. Trying CPU-only PyTorch as fallback...")
        cmd = build_install_command(CPU_INDEX_URL)
        pip_returncode = run_pip_install(cmd)
        expected_cuda = False

    if pip_returncode != 0:
        print()
        print("=" * 60)
        print("❌ PyTorch installation failed!")
        print("=" * 60)
        print("Troubleshooting:")
        if pip_returncode == 5:
            print("  1. Close SRT Drama Tool and any running python.exe processes that use this virtual environment")
            print("  2. Reopen the app and run the installer again, or run install_pytorch.py from a separate terminal")
            print("  3. If leftover ~orch or ~umpy folders remain after closing Python, delete them and retry")
        else:
            print("  1. Check your internet connection")
            print("  2. Upgrade pip: python -m pip install --upgrade pip")
            print("  3. Try manual CUDA install:")
        print(f"     python -m pip install --force-reinstall torch torchvision torchaudio --index-url {CUDA_INDEX_URL} --no-cache-dir")
        update_config_files(False, False)
        return False

    print()
    print("Verifying installation...")
    verified = verify_pytorch_install(expect_cuda=expected_cuda)
    if not verified:
        print()
        print("=" * 60)
        print("❌ PyTorch verification failed!")
        print("=" * 60)
        update_config_files(False, False)
        return False

    status = get_pytorch_status()
    print()
    print("=" * 60)
    print("✅ PyTorch installation completed successfully!")
    print("=" * 60)
    print(f"PyTorch: {status['version']}")
    print(f"CUDA available: {status['cuda']}")
    update_config_files(True, status["cuda"])
    print()
    print("Restart SRT Drama Tool to use PyTorch features.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Install PyTorch for SRT Drama Tool")
    parser.add_argument("--pause", action="store_true", help="Wait for Enter before closing")
    args = parser.parse_args()

    success = install_pytorch()
    if success:
        print("\nPyTorch is ready.")
    else:
        print("\nPyTorch installation encountered issues.")
        print("The application can still work with CPU processing.")

    if args.pause:
        input("\nPress Enter to close...")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
