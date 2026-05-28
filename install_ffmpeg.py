# -*- coding: utf-8 -*-
"""
FFmpeg Auto Installer for SRT Drama Tool
Automatically downloads and installs FFmpeg to a specified drive
and configures the application to detect it automatically.
"""

import os
import sys
import zipfile
import shutil
import urllib.request
import urllib.error  # For URLError exception type
import json
import platform
import subprocess
import time
from pathlib import Path

# Force UTF-8 encoding for stdout/stderr to prevent UnicodeEncodeError on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "app_settings.json")
RVC_CONFIG_FILE = os.path.join(SCRIPT_DIR, "rvc_config.json")


def get_app_data_dir():
    """Match SRT Drama Tool's runtime settings directory."""
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        app_dir = os.path.join(app_data, "SRTDramaTool")
    else:
        app_dir = os.path.join(os.path.expanduser("~"), ".srt_drama_tool")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


APPDATA_CONFIG_FILE = os.path.join(get_app_data_dir(), "app_settings.json")

# FFmpeg download URLs (Windows 64-bit static builds)
FFMPEG_URLS = {
    "main": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "alternative": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "fallback": "https://github.com/GyanD/codexffmpeg/releases/download/8.1.1/ffmpeg-8.1.1-essentials_build.zip"
}


def get_available_drives():
    """Get list of available drives on Windows."""
    if platform.system() != "Windows":
        return [os.path.expanduser("~")]

    drives = []
    for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        drive = f"{letter}:"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def find_best_drive():
    """Find the best drive with most free space on any PC."""
    available = get_available_drives()

    if not available:
        return None

    # Select drive with most free space
    best_drive = None
    max_space = 0

    for drive in available:
        try:
            usage = shutil.disk_usage(drive)
            if usage.free > max_space:
                max_space = usage.free
                best_drive = drive
        except Exception:
            continue

    return best_drive


def get_install_path():
    """Get FFmpeg installation path - auto-selects best drive on any PC."""
    drive = find_best_drive()

    if drive is None:
        # Fallback to script directory
        return os.path.join(SCRIPT_DIR, "ffmpeg")

    if platform.system() == "Windows" and drive.endswith(":"):
        drive = drive + "\\"

    return os.path.join(drive, "RVC_Tools", "FFmpeg")


def download_ffmpeg(install_path, progress_callback=None):
    """
    Download and install FFmpeg.

    Args:
        install_path: Where to install FFmpeg
        progress_callback: Optional callback for progress updates
    """
    def report_progress(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)

    # Create installation directory
    try:
        os.makedirs(install_path, exist_ok=True)
        report_progress(f"✓ Installation directory: {install_path}")
    except PermissionError as e:
        report_progress(f"✗ Permission denied: {install_path}")
        report_progress(f"💡 Try running as Administrator or choose a different location")
        return False
    except Exception as e:
        report_progress(f"✗ Failed to create directory: {e}")
        return False

    # Try downloading from different sources
    zip_path = None
    extract_path = None

    for source_name, url in FFMPEG_URLS.items():
        try:
            report_progress(f"\n{'='*60}")
            report_progress(f"Downloading FFmpeg from {source_name}...")
            report_progress(f"{'='*60}")

            zip_filename = f"ffmpeg_{source_name}.zip"
            zip_path = os.path.join(install_path, zip_filename)
            extract_path = os.path.join(install_path, "temp_extract")

            # Download with progress
            last_reported_percent = {"value": -1}
            download_started_at = time.monotonic()

            def download_progress(count, block_size, total_size):
                if total_size > 0:
                    percent = int(count * block_size * 100 / total_size)
                    downloaded = count * block_size / (1024 * 1024)
                    total = total_size / (1024 * 1024)
                    elapsed = max(time.monotonic() - download_started_at, 0.1)
                    speed = downloaded / elapsed

                    should_report = (
                        percent == 100
                        or percent == 0 and last_reported_percent["value"] == -1
                        or percent >= last_reported_percent["value"] + 5
                    )
                    if should_report:
                        last_reported_percent["value"] = percent
                        msg = f"  Downloading: {percent}% ({downloaded:.1f}/{total:.1f} MB, {speed:.1f} MB/s)"
                        print(msg, flush=True)  # Print to stdout so app can capture
                        if progress_callback:
                            progress_callback(msg)

            # Try download with timeout
            try:
                urllib.request.urlretrieve(url, zip_path, download_progress)
                report_progress("✓ Download complete")
            except PermissionError as e:
                report_progress(f"✗ Download blocked by Antivirus/Permissions: {e}")
                report_progress(f"💡 Try: 1) Disable Antivirus temporarily, or 2) Manual install")
                continue
            except urllib.error.URLError as e:
                report_progress(f"✗ Network error: {e}")
                report_progress(f"💡 Check internet connection or try manual install")
                continue
            
            # Extract ZIP
            report_progress("\nExtracting FFmpeg...")
            os.makedirs(extract_path, exist_ok=True)

            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Get total files for progress
                    file_list = zip_ref.namelist()
                    total_files = len(file_list)
                    print(f"  Extracting {total_files} files...", flush=True)
                    
                    for i, member in enumerate(file_list, 1):
                        zip_ref.extract(member, extract_path)
                        if i % 50 == 0 or i == total_files:
                            extract_pct = int(i * 100 / total_files)
                            print(f"  Extracting: {extract_pct}% ({i}/{total_files} files)", flush=True)
                            
                report_progress("✓ Extraction complete")
            except PermissionError as e:
                report_progress(f"✗ Extraction failed - Antivirus may be blocking: {e}")
                report_progress(f"💡 Solution: Disable Antivirus temporarily, then retry")
                continue
            except zipfile.BadZipFile as e:
                report_progress(f"✗ Corrupted download: {e}")
                report_progress(f"💡 Try again or use manual install")
                continue
            
            # Find FFmpeg binaries
            ffmpeg_exe = None
            ffprobe_exe = None
            
            # Search for ffmpeg.exe in extracted files
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    if file.lower() == "ffmpeg.exe" and ffmpeg_exe is None:
                        ffmpeg_exe = os.path.join(root, file)
                    elif file.lower() == "ffprobe.exe" and ffprobe_exe is None:
                        ffprobe_exe = os.path.join(root, file)
            
            if ffmpeg_exe is None:
                report_progress("✗ ffmpeg.exe not found in archive")
                shutil.rmtree(extract_path, ignore_errors=True)
                continue
            if ffprobe_exe is None:
                report_progress("✗ ffprobe.exe not found in archive")
                shutil.rmtree(extract_path, ignore_errors=True)
                continue
            
            # Copy binaries to install path
            report_progress("\nInstalling FFmpeg...")

            try:
                bin_dir = os.path.join(install_path, "bin")
                os.makedirs(bin_dir, exist_ok=True)

                shutil.copy2(ffmpeg_exe, os.path.join(bin_dir, "ffmpeg.exe"))
                report_progress("✓ Installed ffmpeg.exe")

                shutil.copy2(ffprobe_exe, os.path.join(bin_dir, "ffprobe.exe"))
                report_progress("✓ Installed ffprobe.exe")

                # Copy DLLs if any
                for root, dirs, files in os.walk(extract_path):
                    for file in files:
                        if file.lower().endswith('.dll'):
                            src = os.path.join(root, file)
                            dst = os.path.join(bin_dir, file)
                            try:
                                shutil.copy2(src, dst)
                            except PermissionError:
                                report_progress(f"⚠️ Could not copy {file} (may not be needed)")

                # Clean up
                shutil.rmtree(extract_path, ignore_errors=True)
                if os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                    except:
                        pass

                report_progress("\n✓ FFmpeg installed successfully!")
                report_progress(f"📍 Location: {bin_dir}")
                return True

            except PermissionError as e:
                report_progress(f"✗ Installation failed - Permission denied: {e}")
                report_progress(f"💡 Try: 1) Run as Administrator, or 2) Choose different drive")
                continue
            except Exception as e:
                report_progress(f"✗ Installation error: {e}")
                continue
            
        except Exception as e:
            report_progress(f"✗ Failed to download from {source_name}: {e}")
            if zip_path and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
            continue
    
    report_progress("\n✗ All download sources failed")
    return False


def detect_ffmpeg(install_path=None):
    """
    Detect FFmpeg installation.
    Priority: Custom install path > System PATH
    Does NOT search SCRIPT_DIR or ffmpeg_bin to avoid detecting dev folder files.

    Returns:
        dict with ffmpeg_path, ffprobe_path, version
    """
    result = {
        "found": False,
        "ffmpeg_path": None,
        "ffprobe_path": None,
        "version": None,
        "bin_dir": None
    }

    search_paths = []

    # 1. Check custom install path (highest priority)
    if install_path:
        search_paths.append(os.path.join(install_path, "bin"))

    # 2. Check user-wide install (NOT SCRIPT_DIR to avoid dev folder)
    search_paths.append(os.path.join(os.path.expanduser("~"), "RVC_Tools", "FFmpeg", "bin"))

    # 3. Check system PATH only (exclude SCRIPT_DIR to avoid dev folder detection)
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    for p in path_dirs:
        # Skip if it's inside the script directory (dev folder)
        if p and os.path.abspath(p).startswith(os.path.abspath(SCRIPT_DIR)):
            continue
        search_paths.append(p)

    # Remove duplicates while preserving order
    seen = set()
    unique_paths = []
    for p in search_paths:
        if p and p not in seen:
            seen.add(p)
            unique_paths.append(p)
    search_paths = unique_paths
    
    # Search for ffmpeg.exe
    for path in search_paths:
        if not path or not os.path.exists(path):
            continue
        
        ffmpeg_exe = os.path.join(path, "ffmpeg.exe")
        ffprobe_exe = os.path.join(path, "ffprobe.exe")
        
        if os.path.exists(ffmpeg_exe):
            result["found"] = True
            result["ffmpeg_path"] = ffmpeg_exe
            result["bin_dir"] = path
            
            if os.path.exists(ffprobe_exe):
                result["ffprobe_path"] = ffprobe_exe
            
            # Get version
            try:
                version_output = subprocess.check_output(
                    [ffmpeg_exe, "-version"],
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                ).decode("utf-8", errors="ignore")
                
                # Extract version line
                for line in version_output.split("\n"):
                    if "ffmpeg version" in line.lower():
                        result["version"] = line.strip()
                        break
            except Exception:
                pass
            
            break
    
    return result


def update_config_files(ffmpeg_path, ffprobe_path, bin_dir):
    """Update configuration files with FFmpeg paths."""
    updates = []
    
    # Update app_settings.json
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except Exception:
            settings = {}
    else:
        settings = {}
    
    settings["ffmpeg_path"] = ffmpeg_path
    settings["ffprobe_path"] = ffprobe_path
    settings["ffmpeg_bin_dir"] = bin_dir
    settings["ffmpeg_auto_detect"] = True
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    
    updates.append(f"✓ Updated {CONFIG_FILE}")
    
    # Update runtime settings in AppData; this is what the main app uses.
    try:
        if os.path.exists(APPDATA_CONFIG_FILE):
            with open(APPDATA_CONFIG_FILE, 'r', encoding='utf-8') as f:
                appdata_settings = json.load(f)
        else:
            appdata_settings = {}

        appdata_settings["ffmpeg_path"] = ffmpeg_path
        appdata_settings["ffprobe_path"] = ffprobe_path
        appdata_settings["ffmpeg_bin_dir"] = bin_dir
        appdata_settings["ffmpeg_auto_detect"] = True

        with open(APPDATA_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(appdata_settings, f, indent=2, ensure_ascii=False)
        updates.append(f"✓ Updated {APPDATA_CONFIG_FILE}")
    except Exception as e:
        updates.append(f"✗ Could not update {APPDATA_CONFIG_FILE}: {e}")

    # Update rvc_config.json
    if os.path.exists(RVC_CONFIG_FILE):
        try:
            with open(RVC_CONFIG_FILE, 'r', encoding='utf-8') as f:
                rvc_config = json.load(f)
        except Exception:
            rvc_config = {}
    else:
        rvc_config = {}
    
    rvc_config["ffmpeg_path"] = ffmpeg_path
    rvc_config["ffprobe_path"] = ffprobe_path
    rvc_config["ffmpeg_auto_detect"] = True
    
    with open(RVC_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(rvc_config, f, indent=2, ensure_ascii=False)
    
    updates.append(f"✓ Updated {RVC_CONFIG_FILE}")
    
    return updates


def add_to_system_path(bin_dir):
    """Add FFmpeg to system PATH (Windows)."""
    if platform.system() != "Windows":
        return False
    
    try:
        # Get current PATH from registry
        with subprocess.Popen(
            ["reg", "query", "HKCU\\Environment", "/v", "PATH"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        ) as proc:
            stdout, _ = proc.communicate()
            current_path = stdout.decode("utf-8", errors="ignore")
        
        # Check if already in PATH
        if bin_dir.lower() in current_path.lower():
            print("✓ FFmpeg already in system PATH")
            return True
        
        # Add to PATH
        with subprocess.Popen(
            ["setx", "PATH", f"%PATH%;{bin_dir}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        ) as proc:
            proc.communicate()
        
        print("✓ Added FFmpeg to system PATH")
        return True
        
    except Exception as e:
        print(f"✗ Failed to update system PATH: {e}")
        return False


def main():
    """Main installation function."""
    import argparse
    import time
    
    parser = argparse.ArgumentParser(
        description="FFmpeg Auto Installer for SRT Drama Tool - Works on any PC automatically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-install FFmpeg (recommended - works on any PC)
  python install_ffmpeg.py

  # Just detect FFmpeg
  python install_ffmpeg.py --detect

  # Update config files after detection
  python install_ffmpeg.py --detect --update-config

  # List available drives
  python install_ffmpeg.py --list-drives
        """
    )

    parser.add_argument('--detect', action='store_true', help='Only detect FFmpeg, don\'t install')
    parser.add_argument('--update-config', action='store_true', help='Update config files after detection/installation')
    parser.add_argument('--list-drives', action='store_true', help='List available drives')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("FFmpeg Auto Installer for SRT Drama Tool")
    print(f"{'='*60}\n")
    
    # List drives
    if args.list_drives:
        drives = get_available_drives()
        print("Available drives:")
        for drive in drives:
            try:
                usage = shutil.disk_usage(drive)
                free_gb = usage.free / (1024**3)
                print(f"  {drive} - {free_gb:.1f} GB free")
            except Exception:
                print(f"  {drive}")
        print()
    
    # Detect mode
    if args.detect:
        print("Detecting FFmpeg...\n")
        result = detect_ffmpeg()
        
        if result["found"]:
            print(f"✓ FFmpeg found!")
            print(f"  Path: {result['ffmpeg_path']}")
            if result['ffprobe_path']:
                print(f"  ffprobe: {result['ffprobe_path']}")
            if result['version']:
                print(f"  Version: {result['version']}")
            
            if args.update_config:
                bin_dir = result['bin_dir']
                update_config_files(result['ffmpeg_path'], result.get('ffprobe_path', ''), bin_dir)
        else:
            print("✗ FFmpeg not found. Run without --detect to install.")
        
        return
    
    # Determine installation path (fully automatic)
    install_path = get_install_path()
    print(f"Installation path: {install_path}\n")
    
    # Check if FFmpeg already exists IN THE TARGET INSTALLATION PATH
    # We ignore FFmpeg found in other places (like Music Studio) to ensure a clean install for this app
    existing = detect_ffmpeg(install_path)
    if existing["found"]:
        print("✓ FFmpeg already installed at target location:")
        print(f"  ffmpeg: {existing['ffmpeg_path']}")
        if existing.get('ffprobe_path'):
            print(f"  ffprobe: {existing['ffprobe_path']}")
        print()

        if not existing.get('ffprobe_path'):
            print("⚠ ffprobe.exe is missing. Downloading full FFmpeg package to add it...\n")
        else:
            updates = update_config_files(
                existing['ffmpeg_path'],
                existing.get('ffprobe_path', ''),
                existing['bin_dir']
            )
            for update in updates:
                print(update)

            return
    
    # Download and install
    success = download_ffmpeg(install_path)
    
    if success:
        # Detect installed version
        result = detect_ffmpeg(install_path)
        
        if result["found"]:
            print(f"\n✓ FFmpeg installed successfully!")
            print(f"  ffmpeg: {result['ffmpeg_path']}")
            if result.get('ffprobe_path'):
                print(f"  ffprobe: {result['ffprobe_path']}")
            if result['version']:
                print(f"  {result['version']}")
            
            # Update config files automatically
            updates = update_config_files(
                result['ffmpeg_path'],
                result.get('ffprobe_path', ''),
                result['bin_dir']
            )
            
            for update in updates:
                print(update)

            print(f"\n{'='*60}")
            print("✓ FFmpeg is ready! SRT Drama Tool will detect it automatically.")
            print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print("✗ Installation failed. Please try manual installation below.")
        print(f"{'='*60}\n")
        print_manual_install_guide(install_path)
        sys.exit(1)


def print_manual_install_guide(install_path):
    """Print manual installation instructions when auto-install fails"""
    print("\n" + "="*60)
    print("⚠️  MANUAL INSTALLATION REQUIRED")
    print("="*60)
    print("\n🔍 Possible causes for auto-install failure:")
    print("  1. Antivirus software is blocking download/extraction")
    print("  2. No internet connection or firewall blocking")
    print("  3. Permission denied (try running as Administrator)")
    print("  4. Corporate network restrictions")
    print("\n" + "-"*60)
    print("📖 MANUAL INSTALLATION STEPS:")
    print("-"*60)
    print(f"\n1️⃣  Download FFmpeg from one of these sources:")
    print("   • https://www.gyan.dev/ffmpeg/builds/ (Recommended)")
    print("   • https://github.com/BtbN/FFmpeg-Builds/releases")
    print("   • https://github.com/GyanD/codexffmpeg/releases")
    print("\n2️⃣  Choose: 'ffmpeg-*-full' or 'ffmpeg-*-latest' (Windows 64-bit)")
    print("   • Download the ZIP file (not .7z)")
    print("\n3️⃣  Extract the downloaded archive")
    print("   • Right-click → Extract All")
    print("   • Note the extraction folder")
    print("\n4️⃣  Copy files to this location:")
    print(f"   📍 {install_path}\\bin\\")
    print("\n   You need these files in the bin folder:")
    print("   • ffmpeg.exe (required)")
    print("   • ffprobe.exe (recommended)")
    print("   • Any .dll files from the extracted folder")
    print("\n5️⃣  Restart SRT Drama Tool")
    print("   • The app will detect FFmpeg automatically")
    print("\n" + "-"*60)
    print("💡 QUICK FIXES FOR ANTIVIRUS:")
    print("-"*60)
    print("  • Windows Defender: Settings → Virus & threat protection")
    print("    → Add exclusion for: Python.exe and app folder")
    print("  • Other AV: Temporarily disable during installation")
    print("  • Corporate PC: Ask IT department to whitelist Python")
    print("\n" + "-"*60)
    print("🛡️  PORTABLE FFMPEG OPTION:")
    print("-"*60)
    print("  If you can't install to system folders:")
    print("  1. Extract FFmpeg to any folder you have access to")
    print("  2. In SRT Drama Tool → Settings tab")
    print("  3. Set FFmpeg path to your extracted ffmpeg.exe")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
