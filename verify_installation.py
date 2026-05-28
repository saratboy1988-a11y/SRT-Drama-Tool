# -*- coding: utf-8 -*-
"""
RVC Tool - ផ្ទៀងផ្ទាត់ការដំឡើង
ពិនិត្យមើលថាតើគ្រប់សមាសធាតុទាំងអស់ត្រូវបានដំឡើងត្រឹមត្រូវឬអត់
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS_FILE = os.path.join(SCRIPT_DIR, "requirements.txt")


def check_python_version():
    """ពិនិត្យកំណែ Python"""
    result = {
        "passed": False,
        "current_version": platform.python_version(),
        "required_version": "3.8+",
        "message": ""
    }

    # Python 3.8+ required
    if sys.version_info >= (3, 8):
        result["passed"] = True
        result["message"] = f"✓ កំណែ Python {platform.python_version()} ត្រឹមត្រូវ"
    else:
        result["message"] = f"✗ ត្រូវការ Python 3.8+ (បច្ចុប្បន្ន: {platform.python_version()})"

    return result


def check_required_files():
    """ពិនិត្យឯកសារសំខាន់ៗ"""
    result = {
        "passed": True,
        "missing_files": [],
        "found_files": [],
        "message": ""
    }

    required_files = [
        "RVC Tool.py",
        "app_settings.json",
        "rvc_config.json",
        "requirements.txt",
        "download_models.py",
        "install_ffmpeg.py",
        "test_gpu.py"
    ]

    for file in required_files:
        file_path = os.path.join(SCRIPT_DIR, file)
        if os.path.exists(file_path):
            result["found_files"].append(file)
        else:
            result["missing_files"].append(file)
            result["passed"] = False

    if result["passed"]:
        result["message"] = f"✓ ឯកសារទាំង {len(result['found_files'])} ត្រូវបានរកឃើញ"
    else:
        result["message"] = f"✗ ឯកសារ {len(result['missing_files'])} បាត់: {', '.join(result['missing_files'])}"

    return result


def check_python_packages():
    """ពិនិត្យ Python Packages"""
    result = {
        "passed": True,
        "installed": [],
        "missing": [],
        "message": ""
    }

    required_packages = [
        "PyQt5",
        "edge_tts",
        "pydub",
        "gradio_client"
    ]

    for package in required_packages:
        try:
            # Handle different import names
            if package == "edge_tts":
                __import__("edge_tts")
            elif package == "gradio_client":
                __import__("gradio_client")
            else:
                __import__(package)
            result["installed"].append(package)
        except ImportError:
            result["missing"].append(package)
            result["passed"] = False

    if result["passed"]:
        result["message"] = f"✓ Packages ទាំង {len(result['installed'])} ត្រូវបានដំឡើង"
    else:
        result["message"] = f"✗ Packages បាត់: {', '.join(result['missing'])}"
        result["message"] += "\n  → ដំឡើង: pip install " + " ".join(result["missing"])

    return result


def check_ffmpeg():
    """ពិនិត្យ FFmpeg"""
    result = {
        "passed": False,
        "ffmpeg_path": None,
        "ffprobe_path": None,
        "version": None,
        "message": ""
    }

    # Search paths
    search_paths = [
        os.path.join(SCRIPT_DIR, "ffmpeg", "bin"),
        os.path.join(SCRIPT_DIR, "ffmpeg_bin"),
        SCRIPT_DIR,
        os.path.expanduser("~\\RVC_Tools\\FFmpeg\\bin")
    ]

    # Add PATH directories
    search_paths.extend(os.environ.get("PATH", "").split(os.pathsep))

    # Find ffmpeg.exe
    for path in search_paths:
        if not path or not os.path.exists(path):
            continue

        ffmpeg_exe = os.path.join(path, "ffmpeg.exe")
        if os.path.exists(ffmpeg_exe):
            result["ffmpeg_path"] = ffmpeg_exe
            result["passed"] = True

            # Get version
            try:
                output = subprocess.check_output(
                    [ffmpeg_exe, "-version"],
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW
                ).decode("utf-8", errors="ignore")

                for line in output.split("\n"):
                    if "ffmpeg version" in line.lower():
                        result["version"] = line.strip()[:100]
                        break
            except Exception:
                pass

            # Find ffprobe
            ffprobe_exe = os.path.join(path, "ffprobe.exe")
            if os.path.exists(ffprobe_exe):
                result["ffprobe_path"] = ffprobe_exe

            break

    if result["passed"]:
        result["message"] = f"✓ FFmpeg ត្រូវបានរកឃើញ"
        if result["version"]:
            result["message"] += f"\n    {result['version']}"
    else:
        result["message"] = "✗ FFmpeg មិនត្រូវបានរកឃើញ"
        result["message"] += "\n  → ដំណើរការ: python install_ffmpeg.py"

    return result


def check_gpu():
    """ពិនិត្យ GPU"""
    result = {
        "passed": False,
        "gpu_name": None,
        "cuda_available": False,
        "message": ""
    }

    # Check nvidia-smi
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        ).decode("utf-8", errors="ignore").strip()

        if output:
            result["gpu_name"] = output.split("\n")[0].strip()
            result["passed"] = True
    except Exception:
        pass

    # Check PyTorch CUDA
    try:
        import torch
        if torch.cuda.is_available():
            result["cuda_available"] = True
            result["passed"] = True
            if not result["gpu_name"]:
                result["gpu_name"] = torch.cuda.get_device_name(0)
    except ImportError:
        pass
    except Exception:
        pass

    if result["passed"]:
        result["message"] = f"✓ GPU: {result['gpu_name']}"
        if result["cuda_available"]:
            result["message"] += " (CUDA ដំណើរការ)"
        else:
            result["message"] += " (CUDA មិនដំណើរការ)"
    else:
        result["message"] = "⚠ មិនរកឃើញ GPU (នឹងប្រើ CPU)"

    return result


def check_config_files():
    """ពិនិត្យឯកសារ Configuration"""
    result = {
        "passed": True,
        "configs": {},
        "message": ""
    }

    # Check app_settings.json
    settings_file = os.path.join(SCRIPT_DIR, "app_settings.json")
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            result["configs"]["app_settings"] = "✓ ត្រឹមត្រូវ"
        except Exception as e:
            result["configs"]["app_settings"] = f"✗ ខុស: {str(e)}"
            result["passed"] = False
    else:
        result["configs"]["app_settings"] = "✗ បាត់"
        result["passed"] = False

    # Check rvc_config.json
    rvc_file = os.path.join(SCRIPT_DIR, "rvc_config.json")
    if os.path.exists(rvc_file):
        try:
            with open(rvc_file, 'r', encoding='utf-8') as f:
                rvc_config = json.load(f)
            result["configs"]["rvc_config"] = "✓ ត្រឹមត្រូវ"
        except Exception as e:
            result["configs"]["rvc_config"] = f"✗ ខុស: {str(e)}"
            result["passed"] = False
    else:
        result["configs"]["rvc_config"] = "✗ បាត់"
        result["passed"] = False

    if result["passed"]:
        result["message"] = "✓ ឯកសារ Configuration ត្រឹមត្រូវ"
    else:
        result["message"] = "✗ មានបញ្ហាក្នុង Configuration"

    return result


def check_models_directory():
    """ពិនិត្យថត Models"""
    result = {
        "passed": True,
        "models_dir": os.path.join(SCRIPT_DIR, "rvc_models"),
        "model_count": 0,
        "message": ""
    }

    if os.path.exists(result["models_dir"]):
        # Count models
        for item in os.listdir(result["models_dir"]):
            item_path = os.path.join(result["models_dir"], item)
            if os.path.isdir(item_path):
                result["model_count"] += 1

        if result["model_count"] > 0:
            result["message"] = f"✓ រកឃើញ Models {result['model_count']}"
        else:
            result["message"] = "⚠ ថត Models ទទេ (មិនទាន់មាន Models)"
    else:
        result["message"] = "⚠ ថត Models មិនទាន់មាន (នឹងបង្កើតស្វ័យប្រវត្តិពេលទាញយក)"

    return result


def check_disk_space():
    """ពិនិត្យទំហំថាស"""
    result = {
        "passed": True,
        "drive": SCRIPT_DIR[:2],
        "free_gb": 0,
        "required_gb": 10,
        "message": ""
    }

    try:
        usage = shutil.disk_usage(result["drive"])
        result["free_gb"] = usage.free / (1024**3)

        if result["free_gb"] >= result["required_gb"]:
            result["message"] = f"✓ ទំហំថាសទំនេរ: {result['free_gb']:.1f} GB"
        else:
            result["passed"] = False
            result["message"] = f"⚠ ទំហំថាសទំនេរតិចពេក: {result['free_gb']:.1f} GB (ត្រូវការ {result['required_gb']} GB+)"
    except Exception:
        result["message"] = "⚠ មិនអាចពិនិត្យទំហំថាស"

    return result


def run_all_checks():
    """ដំណើរការការត្រួតពិនិត្យទាំងអស់"""
    print(f"\n{'='*60}")
    print("RVC Tool - ផ្ទៀងផ្ទាត់ការដំឡើង")
    print(f"{'='*60}\n")
    print(f"ថតដំឡើង: {SCRIPT_DIR}")
    print(f"ប្រព័ន្ធ: {platform.system()} {platform.release()}")
    print(f"កាលបរិច្ឆេទ: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    checks = []

    # 1. Python Version
    print("១. ពិនិត្យកំណែ Python...")
    check = check_python_version()
    checks.append(("កំណែ Python", check))
    print(f"   {check['message']}\n")

    # 2. Required Files
    print("២. ពិនិត្យឯកសារសំខាន់ៗ...")
    check = check_required_files()
    checks.append(("ឯកសារសំខាន់ៗ", check))
    print(f"   {check['message']}\n")

    # 3. Python Packages
    print("៣. ពិនិត្យ Python Packages...")
    check = check_python_packages()
    checks.append(("Python Packages", check))
    print(f"   {check['message']}\n")

    # 4. FFmpeg
    print("៤. ពិនិត្យ FFmpeg...")
    check = check_ffmpeg()
    checks.append(("FFmpeg", check))
    print(f"   {check['message']}\n")

    # 5. GPU
    print("៥. ពិនិត្យ GPU...")
    check = check_gpu()
    checks.append(("GPU", check))
    print(f"   {check['message']}\n")

    # 6. Configuration
    print("៦. ពិនិត្យ Configuration...")
    check = check_config_files()
    checks.append(("Configuration", check))
    print(f"   {check['message']}\n")

    # 7. Models
    print("៧. ពិនិត្យ Models...")
    check = check_models_directory()
    checks.append(("Models", check))
    print(f"   {check['message']}\n")

    # 8. Disk Space
    print("៨. ពិនិត្យទំហំថាស...")
    check = check_disk_space()
    checks.append(("ទំហំថាស", check))
    print(f"   {check['message']}\n")

    # Summary
    print(f"{'='*60}")
    print("សេចក្តីសង្ខេប")
    print(f"{'='*60}\n")

    total = len(checks)
    passed = sum(1 for _, check in checks if check["passed"])
    failed = total - passed

    print(f"ការត្រួតពិនិត្យសរុប: {total}")
    print(f"✓ ជោគជ័យ: {passed}")
    print(f"✗ បរាជ័យ: {failed}\n")

    if failed == 0:
        print("🎉 ការដំឡើង RVC Tool ត្រឹមត្រូវទាំងអស់!")
        print("   → អ្នកអាចចាប់ផ្តើមប្រើប្រាស់បានហើយ\n")
    else:
        print("⚠ មានបញ្ហាដែលត្រូវដោះស្រាយ:\n")

        for name, check in checks:
            if not check["passed"]:
                print(f"  • {name}:")
                print(f"    {check['message']}\n")

        print("ដោះស្រាយបញ្ហា:")
        print("  → ដំឡើង packages បាត់: pip install -r requirements.txt")
        print("  → ដំឡើង FFmpeg: python install_ffmpeg.py")
        print("  → តេស្ត GPU: python test_gpu.py\n")

    return failed == 0


def main():
    """មុខងារសំខាន់"""
    import argparse

    parser = argparse.ArgumentParser(
        description="RVC Tool - ផ្ទៀងផ្ទាត់ការដំឡើង",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ឧទាហរណ៍:
  # ផ្ទៀងផ្ទាត់ការដំឡើងទាំងអស់
  python verify_installation.py

  # រក្សាទុករបាយការណ៍ជា JSON
  python verify_installation.py --save report.json

  # ពិនិត្យតែ FFmpeg និង GPU
  python verify_installation.py --quick
        """
    )

    parser.add_argument('--save', type=str, help='រក្សាទុករបាយការណ៍ជា JSON')
    parser.add_argument('--quick', action='store_true', help='ពិនិត្យតែ FFmpeg និង GPU')

    args = parser.parse_args()

    if args.quick:
        print(f"\n{'='*60}")
        print("RVC Tool - ការត្រួតពិនិត្យរហ័ស")
        print(f"{'='*60}\n")

        print("ពិនិត្យ FFmpeg...")
        ffmpeg = check_ffmpeg()
        print(f"  {ffmpeg['message']}\n")

        print("ពិនិត្យ GPU...")
        gpu = check_gpu()
        print(f"  {gpu['message']}\n")

        if ffmpeg["passed"] and gpu["passed"]:
            print("✓ ការត្រួតពិនិត្យរហ័សជោគជ័យ!")
        else:
            print("✗ មានបញ្ហាត្រូវដោះស្រាយ")
        print()
        return

    # Full verification
    success = run_all_checks()

    # Save report if requested
    if args.save:
        report = {
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "install_dir": SCRIPT_DIR,
            "python_version": platform.python_version(),
            "checks": {
                "python_version": check_python_version(),
                "required_files": check_required_files(),
                "packages": check_python_packages(),
                "ffmpeg": check_ffmpeg(),
                "gpu": check_gpu(),
                "config": check_config_files(),
                "models": check_models_directory(),
                "disk_space": check_disk_space()
            },
            "overall_success": success
        }

        with open(args.save, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"✓ របាយការណ៍ត្រូវបានរក្សាទុក: {args.save}\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    import shutil
    main()
