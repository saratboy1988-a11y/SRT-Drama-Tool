# -*- coding: utf-8 -*-
"""
GPU Test Script for RVC Tool
Tests GPU availability, VRAM, and CUDA compatibility
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path


def detect_gpu():
    """Detect GPU information on any system."""
    result = {
        "gpu_detected": False,
        "gpu_name": None,
        "gpu_type": None,
        "vram_total": None,
        "vram_available": None,
        "cuda_version": None,
        "driver_version": None,
        "gpu_info": {}
    }

    system = platform.system()

    if system == "Windows":
        result = detect_gpu_windows(result)
    elif system == "Linux":
        result = detect_gpu_linux(result)
    elif system == "Darwin":  # macOS
        result = detect_gpu_macos(result)

    return result


def detect_gpu_windows(result):
    """Detect GPU on Windows."""
    # Try nvidia-smi first (most reliable for CUDA GPUs)
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version",
             "--format=csv,noheader,nounits"],
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        ).decode("utf-8", errors="ignore").strip()

        lines = output.split("\n")
        if lines and len(lines) > 0:
            parts = [p.strip() for p in lines[0].split(",")]
            if len(parts) >= 4:
                result["gpu_detected"] = True
                result["gpu_name"] = parts[0]
                result["gpu_type"] = "NVIDIA"
                try:
                    result["vram_total"] = float(parts[1])  # MB
                    result["vram_available"] = float(parts[2])  # MB
                except ValueError:
                    pass
                result["driver_version"] = parts[3]

                # Get CUDA version
                try:
                    cuda_output = subprocess.check_output(
                        ["nvidia-smi", "--query-gpu=compute_cap",
                         "--format=csv,noheader,nounits"],
                        stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    ).decode("utf-8", errors="ignore").strip()

                    if cuda_output:
                        result["cuda_version"] = cuda_output
                except Exception:
                    pass

                return result
    except Exception:
        pass

    # Try DirectML (AMD/Intel GPUs)
    try:
        output = subprocess.check_output(
            ["wmic", "path", "win32_VideoController", "get", "Name,AdapterRAM,DriverVersion"],
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        ).decode("utf-8", errors="ignore")

        lines = [line.strip() for line in output.split("\n") if line.strip() and "Name" not in line]
        if lines:
            parts = [p.strip() for p in lines[0].split() if p]
            if parts:
                result["gpu_detected"] = True
                result["gpu_name"] = " ".join(parts[:-2]) if len(parts) > 2 else parts[0]

                # Try to get RAM
                try:
                    ram_bytes = int(parts[-2]) if len(parts) >= 2 else 0
                    result["vram_total"] = ram_bytes / (1024**2)  # Convert to MB
                except (ValueError, IndexError):
                    pass

                result["driver_version"] = parts[-1] if parts else None
                result["gpu_type"] = "AMD/Intel (DirectML)"

                return result
    except Exception:
        pass

    return result


def detect_gpu_linux(result):
    """Detect GPU on Linux."""
    # Try nvidia-smi
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version",
             "--format=csv,noheader,nounits"],
            stderr=subprocess.STDOUT
        ).decode("utf-8", errors="ignore").strip()

        lines = output.split("\n")
        if lines and len(lines) > 0:
            parts = [p.strip() for p in lines[0].split(",")]
            if len(parts) >= 4:
                result["gpu_detected"] = True
                result["gpu_name"] = parts[0]
                result["gpu_type"] = "NVIDIA"
                try:
                    result["vram_total"] = float(parts[1])
                    result["vram_available"] = float(parts[2])
                except ValueError:
                    pass
                result["driver_version"] = parts[3]

                return result
    except Exception:
        pass

    # Try lspci (for AMD/Intel)
    try:
        output = subprocess.check_output(
            ["lspci", "|", "grep", "-i", "vga"],
            shell=True,
            stderr=subprocess.STDOUT
        ).decode("utf-8", errors="ignore").strip()

        if output:
            result["gpu_detected"] = True
            result["gpu_name"] = output
            result["gpu_type"] = "AMD/Intel (Linux)"
            return result
    except Exception:
        pass

    return result


def detect_gpu_macos(result):
    """Detect GPU on macOS."""
    try:
        output = subprocess.check_output(
            ["system_profiler", "SPDisplaysDataType"],
            stderr=subprocess.STDOUT
        ).decode("utf-8", errors="ignore")

        for line in output.split("\n"):
            line = line.strip()
            if "Chipset Model:" in line:
                result["gpu_detected"] = True
                result["gpu_name"] = line.split(":", 1)[1].strip()
                result["gpu_type"] = "Apple Silicon/AMD"
            elif "VRAM" in line:
                try:
                    vram_str = line.split(":", 1)[1].strip()
                    if "MB" in vram_str:
                        result["vram_total"] = float(vram_str.replace("MB", "").strip())
                    elif "GB" in vram_str:
                        result["vram_total"] = float(vram_str.replace("GB", "").strip()) * 1024
                except ValueError:
                    pass

        if result["gpu_detected"]:
            return result
    except Exception:
        pass

    return result


def test_pytorch_gpu():
    """Test if PyTorch can access GPU."""
    result = {
        "pytorch_installed": False,
        "pytorch_version": None,
        "cuda_available": False,
        "cuda_version": None,
        "gpu_device_name": None,
        "gpu_count": 0,
        "can_allocate_gpu": False
    }

    try:
        import torch
        result["pytorch_installed"] = True
        result["pytorch_version"] = torch.__version__

        if torch.cuda.is_available():
            result["cuda_available"] = True
            result["cuda_version"] = torch.version.cuda  # type: ignore[attr-defined]
            result["gpu_device_name"] = torch.cuda.get_device_name(0)
            result["gpu_count"] = torch.cuda.device_count()

            # Test if we can actually allocate memory on GPU
            try:
                with torch.cuda.device(0):
                    torch.cuda.empty_cache()
                    result["can_allocate_gpu"] = True
            except Exception:
                pass

        return result
    except ImportError:
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def test_directml_gpu():
    """Test DirectML for AMD/Intel GPUs."""
    result = {
        "directml_available": False,
        "gpu_name": None
    }

    try:
        import torch
        try:
            import torch_directml  # type: ignore[import-not-found]

            if torch_directml.is_available():
                result["directml_available"] = True
                result["gpu_name"] = torch_directml.device_name(0)
        except ImportError:
            # torch_directml not installed, skip
            pass

        return result
    except ImportError:
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def gpu_benchmark():
    """Run a simple GPU benchmark."""
    result = {
        "benchmark_done": False,
        "matrix_size": 1000,
        "time_seconds": None,
        "error": None
    }

    try:
        import torch
        import time

        if not torch.cuda.is_available():
            result["error"] = "No CUDA GPU available"
            return result

        # Matrix multiplication benchmark
        size = result["matrix_size"]

        # Warmup
        torch.cuda.empty_cache()

        # Create random matrices on GPU
        start_time = time.time()
        a = torch.randn(size, size, device="cuda")
        b = torch.randn(size, size, device="cuda")

        # Matrix multiplication
        c = torch.mm(a, b)

        # Synchronize
        torch.cuda.synchronize()

        end_time = time.time()
        result["time_seconds"] = end_time - start_time
        result["benchmark_done"] = True

        # Clean up
        del a, b, c
        torch.cuda.empty_cache()

    except ImportError:
        result["error"] = "PyTorch not installed"
    except Exception as e:
        result["error"] = str(e)

    return result


def diagnose_gpu_problems():
    """Diagnose why GPU is not working on laptops with RTX 3050."""
    diagnosis = {
        "nvidia_driver_installed": False,
        "nvidia_smi_works": False,
        "cuda_in_path": False,
        "pytorch_cuda_version": None,
        "pytorch_is_cuda": False,
        "cuda_visible_devices": None,
        "issues": [],
        "solutions": []
    }

    # 1. Check nvidia-smi
    try:
        output = subprocess.check_output(
            ["nvidia-smi"],
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        ).decode("utf-8", errors="ignore")

        diagnosis["nvidia_driver_installed"] = True
        diagnosis["nvidia_smi_works"] = True

        # Extract CUDA version from nvidia-smi
        for line in output.split("\n"):
            if "CUDA Version" in line:
                import re
                match = re.search(r"CUDA Version:\s*([\d.]+)", line)
                if match:
                    diagnosis["system_cuda_version"] = match.group(1)
                break
    except Exception:
        diagnosis["issues"].append("❌ Driver NVIDIA មិនទាន់ដំឡើង ឬ nvidia-smi មិនដំណើរការ")
        diagnosis["solutions"].append("→ ទាញយក Driver NVIDIA: https://www.nvidia.com/Download/index.aspx")

    # 2. Check CUDA in PATH
    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path:
        diagnosis["cuda_in_path"] = True
    else:
        # Check if nvcc exists anywhere
        nvcc_found = False
        for path_dir in os.environ.get("PATH", "").split(";"):
            if "CUDA" in path_dir.upper() and os.path.exists(os.path.join(path_dir, "nvcc.exe")):
                nvcc_found = True
                diagnosis["cuda_in_path"] = True
                break

        if not diagnosis["cuda_in_path"]:
            diagnosis["issues"].append("⚠️ CUDA Toolkit មិនទាន់មានក្នុង PATH")
            diagnosis["solutions"].append("→ ដំឡើង CUDA Toolkit 11.8: https://developer.nvidia.com/cuda-11-8-0-download-archive")

    # 3. Check PyTorch
    try:
        import torch
        diagnosis["pytorch_cuda_version"] = torch.version.cuda  # type: ignore[attr-defined]
        diagnosis["pytorch_is_cuda"] = torch.cuda.is_available()

        if not torch.cuda.is_available():
            # Check if it's CPU-only version
            if "cpu" in torch.__version__.lower() or not hasattr(torch, 'cuda'):
                diagnosis["issues"].append("❌ PyTorch កំណែ CPU-only ត្រូវបានដំឡើង")
                diagnosis["solutions"].append("→ ដក PyTorch ចេញ: pip uninstall torch torchvision torchaudio")
                diagnosis["solutions"].append("→ ដំឡើង PyTorch CUDA: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
            else:
                diagnosis["issues"].append("❌ PyTorch កំណែ CUDA ត្រូវបានដំឡើង ប៉ុន្តែ GPU មិនត្រូវបានរកឃើញ")
                diagnosis["solutions"].append("→ មូលហេតុដែលអាចកើត:")
                diagnosis["solutions"].append("   - Laptop កំពុងប្រើ Intel GPU (ប្តូរទៅ High Performance ក្នុង Windows Graphics Settings)")
                diagnosis["solutions"].append("   - Driver NVIDIA ចាស់ពេក (ត្រូវ Update ទៅកំណែចុងក្រោយ)")
                diagnosis["solutions"].append("   - CUDA មិនត្រូវគ្នា (PyTorch ត្រូវការ CUDA 11.8 ប៉ុន្តែ System មានកំណែផ្សេង)")
    except ImportError:
        diagnosis["issues"].append("❌ PyTorch មិនទាន់ដំឡើង")
        diagnosis["solutions"].append("→ ដំឡើង PyTorch ជាមួយ CUDA: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")

    # 4. Check CUDA_VISIBLE_DEVICES
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    diagnosis["cuda_visible_devices"] = cuda_visible
    if cuda_visible == "-1":
        diagnosis["issues"].append("❌ CUDA_VISIBLE_DEVICES=-1 (GPU ត្រូវបានបិទដោយ Environment Variable)")
        diagnosis["solutions"].append("→ ដក CUDA_VISIBLE_DEVICES=-1 ចេញពី Environment Variables")
    elif cuda_visible:
        diagnosis["solutions"].append(f"→ CUDA_VISIBLE_DEVICES={cuda_visible}")

    return diagnosis


def print_gpu_info():
    """Print comprehensive GPU information."""
    print(f"\n{'='*60}")
    print("ការតេស្ត និងរកមើល GPU សម្រាប់ RVC Tool")
    print(f"{'='*60}\n")

    # System Info
    print("ព័ត៌មានប្រព័ន្ធ:")
    print(f"  ប្រព័ន្ធប្រតិបត្តិការ: {platform.system()} {platform.release()}")
    print(f"  Python: {platform.python_version()}")
    print(f"  Machine: {platform.machine()}\n")

    # GPU Detection
    gpu_info = detect_gpu()
    print("ការរកឃើញ GPU:")
    if gpu_info["gpu_detected"]:
        print(f"  ✓ រកឃើញ GPU: {gpu_info['gpu_name']}")
        print(f"  ប្រភេទ: {gpu_info['gpu_type']}")
        if gpu_info.get("vram_total"):
            vram_gb = gpu_info["vram_total"] / 1024
            print(f"  VRAM: {vram_gb:.1f} GB")
        if gpu_info.get("driver_version"):
            print(f"  Driver: {gpu_info['driver_version']}")
        if gpu_info.get("cuda_version"):
            print(f"  CUDA Compute: {gpu_info['cuda_version']}")
    else:
        print("  ✗ មិនរកឃើញ GPU (កំពុងប្រើ CPU)")
    print()

    # PyTorch GPU Test
    print("ការតេស្ត GPU របស់ PyTorch:")
    torch_info = test_pytorch_gpu()
    if torch_info["pytorch_installed"]:
        print(f"  ✓ PyTorch: {torch_info['pytorch_version']}")
        if torch_info["cuda_available"]:
            print(f"  ✓ CUDA អាចប្រើបាន")
            print(f"  GPU: {torch_info['gpu_device_name']}")
            print(f"  ចំនួន GPU: {torch_info['gpu_count']}")
            if torch_info["can_allocate_gpu"]:
                print(f"  ✓ ការបម្រុងអង្គចងចាំ GPU: ជោគជ័យ")
        else:
            print("  ✗ CUDA មិនអាចប្រើបាន")
            print("  → PyTorch កំពុងប្រើ CPU ទោះបីមាន GPU ក៏ដោយ")
    else:
        print("  ✗ PyTorch មិនទាន់ដំឡើង")
    print()

    # GPU Diagnosis (for laptop issues)
    print("ការវិភាគបញ្ហា GPU (ជួសជុល Laptop RTX 3050):")
    diagnosis = diagnose_gpu_problems()

    if diagnosis["nvidia_smi_works"]:
        print(f"  ✓ Driver NVIDIA: ដំឡើងរួចហើយ")
    else:
        print(f"  ✗ Driver NVIDIA: មិនដំណើរការ")

    if diagnosis["pytorch_is_cuda"]:
        print(f"  ✓ PyTorch CUDA: ដំណើរការល្អ")
    else:
        print(f"  ✗ PyTorch CUDA: មិនដំណើរការ")

    if diagnosis.get("system_cuda_version"):
        print(f"  កំណែ CUDA របស់ System: {diagnosis['system_cuda_version']}")
    if diagnosis.get("pytorch_cuda_version"):
        print(f"  កំណែ CUDA របស់ PyTorch: {diagnosis['pytorch_cuda_version']}")

    if diagnosis["issues"]:
        print(f"\n  បញ្ហាដែលរកឃើញ:")
        for issue in diagnosis["issues"]:
            print(f"    {issue}")

        print(f"\n  ដំណោះស្រាយ:")
        for solution in diagnosis["solutions"]:
            print(f"    {solution}")
    else:
        print(f"  ✓ មិនរកឃើញបញ្ហាអ្វីឡើយ")
    print()

    # DirectML Test
    print("ការតេស្ត DirectML (AMD/Intel):")
    directml_info = test_directml_gpu()
    if directml_info.get("directml_available"):
        print(f"  ✓ DirectML អាចប្រើបាន")
        print(f"  GPU: {directml_info['gpu_name']}")
    else:
        print("  ✗ DirectML មិនអាចប្រើបាន")
    print()

    # GPU Benchmark
    if torch_info["cuda_available"]:
        print("ការតេស្តល្បឿន GPU (Matrix 1000x1000):")
        benchmark = gpu_benchmark()
        if benchmark["benchmark_done"]:
            print(f"  ✓ បញ្ចប់ក្នុង {benchmark['time_seconds']:.3f} វិនាទី")
        else:
            print(f"  ✗ បរាជ័យ: {benchmark['error']}")
        print()

    # RVC Compatibility
    print("ភាពឆបគ្នាជាមួយ RVC:")
    if gpu_info["gpu_detected"] and torch_info["cuda_available"]:
        print("  ✓ GPU រួចរាល់សម្រាប់ RVC")
        print("  → ការបម្លែងសំឡេងនឹងប្រើ GPU ពន្លឿនល្បឿន")
    elif gpu_info["gpu_detected"] and directml_info.get("directml_available"):
        print("  ✓ របៀប DirectML GPU រួចរាល់សម្រាប់ RVC")
        print("  → ការបម្លែងសំឡេងនឹងប្រើ DirectML")
    else:
        print("  ⚠ ប្រើបានតែ CPU ប៉ុណ្ណោះ")
        print("  → ការបម្លែងសំឡេងនឹងយឺត")
        print("  → ដំឡើង PyTorch CUDA ដើម្បីប្រើ GPU:")
        print("     pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print()


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="ការតេស្ត និងរកមើល GPU សម្រាប់ RVC Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ឧទាហរណ៍:
  # តេស្ត GPU ពេញលេញ (ណែនាំ)
  python test_gpu.py

  # គ្រាន់តែរកមើល GPU
  python test_gpu.py --detect

  # តេស្តល្បឿន GPU តែប៉ុណ្ណោះ
  python test_gpu.py --benchmark

  # រក្សាទុកលទ្ធផលជា JSON
  python test_gpu.py --save gpu_report.json
        """
    )

    parser.add_argument('--detect', action='store_true', help='គ្រាន់តែរកមើល GPU មិនតេស្តល្បឿន')
    parser.add_argument('--benchmark', action='store_true', help='តេស្តល្បឿន GPU តែប៉ុណ្ណោះ')
    parser.add_argument('--save', type=str, help='រក្សាទុកលទ្ធផលជាឯកសារ JSON')

    args = parser.parse_args()

    # Save mode
    if args.save:
        all_results = {
            "system": {
                "os": platform.system(),
                "os_release": platform.release(),
                "python": platform.python_version(),
                "machine": platform.machine()
            },
            "gpu_detection": detect_gpu(),
            "pytorch": test_pytorch_gpu(),
            "directml": test_directml_gpu()
        }

        if test_pytorch_gpu().get("cuda_available"):
            all_results["benchmark"] = gpu_benchmark()

        with open(args.save, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

        print(f"✓ របាយការណ៍ GPU ត្រូវបានរក្សាទុក: {args.save}")
        return

    # Benchmark only
    if args.benchmark:
        print(f"\n{'='*60}")
        print("ការតេស្តល្បឿន GPU")
        print(f"{'='*60}\n")

        torch_info = test_pytorch_gpu()
        if torch_info.get("cuda_available"):
            print("កំពុងតេស្តល្បឿន...")
            benchmark = gpu_benchmark()
            if benchmark["benchmark_done"]:
                print(f"✓ Matrix 1000x1000: {benchmark['time_seconds']:.3f} វិនាទី")
            else:
                print(f"✗ បរាជ័យ: {benchmark['error']}")
        else:
            print("✗ មិនមាន CUDA GPU សម្រាប់តេស្តល្បឿន")
        print()
        return

    # Full test (default)
    print_gpu_info()


if __name__ == "__main__":
    main()
