# Keep the Torch bundle focused on runtime inference/separation modules.
# TensorBoard is an optional training/logging integration and is not used by this app.
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

try:
    from PyInstaller.utils.hooks import PY_DYLIB_PATTERNS
except Exception:
    PY_DYLIB_PATTERNS = ["*.dll", "*.pyd", "*.so", "*.dylib"]

module_collection_mode = "pyz+py"
warn_on_missing_hiddenimports = False

datas = collect_data_files(
    "torch",
    excludes=[
        "**/*.h",
        "**/*.hpp",
        "**/*.cuh",
        "**/*.lib",
        "**/*.cpp",
        "**/*.pyi",
        "**/*.cmake",
    ],
)


def _exclude_optional_tensorboard(module_name: str) -> bool:
    optional_prefixes = (
        "torch.utils.tensorboard",
        "torch.testing",
        "torch.onnx",
        "torch._dynamo",
        "torch._inductor",
        "torch.distributed",
    )
    return not any(
        module_name == prefix or module_name.startswith(prefix + ".")
        for prefix in optional_prefixes
    )


hiddenimports = collect_submodules("torch", filter=_exclude_optional_tensorboard)
binaries = collect_dynamic_libs("torch", search_patterns=PY_DYLIB_PATTERNS + ["*.so.*"])
