from __future__ import annotations

import ctypes
import sys
from pathlib import Path
from typing import Optional

from PIL import Image
import numpy as np

# Try Rust pyo3 module
try:
    from vmf_validator import rs_sharpness_score as rs_sharpness_score_rs  # type: ignore
except Exception:  # noqa: BLE001
    rs_sharpness_score_rs = None  # type: ignore


def _numpy_sharpness_score(path: Path) -> float:
    img = Image.open(path).convert("L")
    arr = np.asarray(img, dtype=np.float32) / 255.0
    gx = np.gradient(arr, axis=0)
    gy = np.gradient(arr, axis=1)
    g = np.hypot(gx, gy)
    score = float(np.clip(np.var(g), 0.0, 1.0))
    return score


def sharpness_score(path: Path) -> float:
    if rs_sharpness_score_rs is not None:
        try:
            return float(rs_sharpness_score_rs(str(path)))
        except Exception:  # noqa: BLE001
            pass
    return _numpy_sharpness_score(path)


class CppValidator:
    def __init__(self) -> None:
        self.lib: Optional[ctypes.CDLL] = None
        self._load()

    def _load(self) -> None:
        candidates = []
        if sys.platform.startswith("win"):
            # First try installed location (next to this module)
            candidates.append(Path(__file__).resolve().parent / "native_libs" / "vmf_validator_cpp.dll")
            # Then try build directories
            candidates.append(Path(__file__).resolve().parents[4] / "build" / "bin" / "vmf_validator_cpp.dll")
            candidates.append(Path(__file__).resolve().parents[2] / "native" / "cpp" / "validator" / "Release" / "vmf_validator_cpp.dll")
            candidates.append(Path(__file__).resolve().parents[2] / "native" / "cpp" / "validator" / "vmf_validator_cpp.dll")
        elif sys.platform == "darwin":
            candidates.append(Path(__file__).resolve().parents[2] / "native" / "cpp" / "validator" / "libvmf_validator_cpp.dylib")
        else:
            candidates.append(Path(__file__).resolve().parents[2] / "native" / "cpp" / "validator" / "libvmf_validator_cpp.so")
        for c in candidates:
            if c.exists():
                try:
                    self.lib = ctypes.CDLL(str(c))
                except OSError:
                    continue
                break

    def color_fidelity_score(self, h1: np.ndarray, h2: np.ndarray) -> Optional[float]:
        if self.lib is None:
            return None
        fn = getattr(self.lib, "cpp_color_fidelity_score", None)
        if fn is None:
            return None
        fn.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_int]
        fn.restype = ctypes.c_float
        n = int(h1.size)
        if h2.size != n:
            return None
        a = np.ascontiguousarray(h1, dtype=np.float32)
        b = np.ascontiguousarray(h2, dtype=np.float32)
        return float(fn(a.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), b.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), n))


cpp_validator_singleton = CppValidator()


def color_histogram(path: Path, bins: int = 32) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img, dtype=np.float32) / 255.0
    hist = []
    for ch in range(3):
        h, _ = np.histogram(arr[..., ch], bins=bins, range=(0.0, 1.0), density=True)
        hist.append(h)
    h3 = np.concatenate(hist, axis=0)
    h3 = h3 / (np.sum(h3) + 1e-8)
    return h3.astype(np.float32)


def color_fidelity_score(path: Path, ref_path: Optional[Path]) -> float:
    h = color_histogram(path)
    if ref_path is None or not ref_path.exists():
        # Self-consistency: max score
        return 1.0
    href = color_histogram(ref_path)
    v = cpp_validator_singleton.color_fidelity_score(h, href)
    if v is not None:
        return float(v)
    # Fallback Bhattacharyya in Python
    bc = float(np.sum(np.sqrt(h * href)))
    return float(np.clip(bc, 0.0, 1.0))