from __future__ import annotations

import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
from PIL import Image

from .backends import color_fidelity_score, sharpness_score

# Import advanced metrics (production-grade implementations)
try:
    from .metrics_advanced import (
        anatomy_score_advanced,
        prompt_alignment_score_advanced,
        consistency_score_advanced,
    )
    ADVANCED_METRICS_AVAILABLE = True
except ImportError:
    ADVANCED_METRICS_AVAILABLE = False

# Configuration: Use advanced metrics by default if available
USE_ADVANCED_METRICS = os.getenv('VMF_USE_ADVANCED_METRICS', 'true').lower() in ('true', '1', 'yes')

@dataclass
class Diagnostic:
    backend: str
    ok: bool
    ms: float
    error: Optional[str] = None


def _timed(fn, *args, **kwargs) -> Tuple[float, Optional[Exception], Optional[float]]:
    t0 = time.perf_counter()
    try:
        v = fn(*args, **kwargs)
        ms = (time.perf_counter() - t0) * 1000.0
        return v, None, ms
    except Exception as e:  # noqa: BLE001
        ms = (time.perf_counter() - t0) * 1000.0
        return None, e, ms


def anatomy_score(asset: Path) -> float:
    """
    Evaluate anatomical plausibility using heuristic checks.

    This checks:
    1. Edge density (more detail = better anatomy representation)
    2. Aspect ratio (reasonable proportions for characters)
    3. Symmetry (bilateral symmetry common in characters)

    Returns score in [0, 1] where higher is better.
    """
    img = Image.open(asset).convert("L")
    arr = np.asarray(img, dtype=np.float32) / 255.0
    h, w = arr.shape

    # Edge density score (0-0.4)
    gx = np.gradient(arr, axis=1)
    gy = np.gradient(arr, axis=0)
    edges = np.hypot(gx, gy)
    edge_density = float(np.mean(edges > 0.1))
    edge_score = min(edge_density * 2.0, 0.4)  # Max 0.4 contribution

    # Aspect ratio score (0-0.3)
    aspect_ratio = w / h if h > 0 else 1.0
    # Prefer ratios between 0.5 and 2.0 (reasonable for characters)
    if 0.5 <= aspect_ratio <= 2.0:
        aspect_score = 0.3
    else:
        aspect_score = 0.3 * (1.0 - min(abs(aspect_ratio - 1.0), 1.0))

    # Symmetry score (0-0.3)
    # Check horizontal symmetry (left-right flip)
    left_half = arr[:, :w//2]
    right_half = np.fliplr(arr[:, w//2:])
    min_width = min(left_half.shape[1], right_half.shape[1])
    left_crop = left_half[:, :min_width]
    right_crop = right_half[:, :min_width]
    symmetry_diff = float(np.mean(np.abs(left_crop - right_crop)))
    symmetry_score = 0.3 * (1.0 - min(symmetry_diff, 1.0))

    total_score = edge_score + aspect_score + symmetry_score
    return float(np.clip(total_score, 0.0, 1.0))


def prompt_alignment_score(asset: Path, prompt: Optional[str] = None) -> float:
    """
    Evaluate how well the image aligns with the prompt.

    Without ML models (CLIP), this uses heuristic checks:
    1. Color saturation (vibrant for anime/fantasy, muted for realistic)
    2. Brightness distribution (balanced lighting)
    3. Contrast (clear subject definition)

    Returns score in [0, 1] where higher indicates better alignment.
    """
    img = Image.open(asset).convert("RGB")
    arr = np.asarray(img, dtype=np.float32) / 255.0

    # Color saturation score (0-0.35)
    hsv = np.asarray(img.convert("HSV"), dtype=np.float32) / 255.0
    saturation = hsv[:, :, 1]
    mean_saturation = float(np.mean(saturation))
    # Higher saturation preferred (0.3-0.7 range is good)
    if 0.3 <= mean_saturation <= 0.7:
        saturation_score = 0.35
    else:
        saturation_score = 0.35 * (1.0 - min(abs(mean_saturation - 0.5) / 0.5, 1.0))

    # Brightness distribution score (0-0.35)
    gray = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    brightness_hist, _ = np.histogram(gray, bins=10, range=(0.0, 1.0))
    brightness_hist = brightness_hist / (np.sum(brightness_hist) + 1e-8)
    # Prefer balanced distribution (not too concentrated)
    entropy = -np.sum(brightness_hist * np.log(brightness_hist + 1e-8))
    max_entropy = np.log(10)  # Maximum for 10 bins
    brightness_score = 0.35 * (entropy / max_entropy)

    # Contrast score (0-0.3)
    contrast = float(np.std(gray))
    # Good contrast is around 0.2-0.3 std
    if 0.2 <= contrast <= 0.3:
        contrast_score = 0.3
    else:
        contrast_score = 0.3 * (1.0 - min(abs(contrast - 0.25) / 0.25, 1.0))

    total_score = saturation_score + brightness_score + contrast_score
    return float(np.clip(total_score, 0.0, 1.0))


def consistency_score(asset: Path, reference: Optional[Path] = None) -> float:
    """
    Evaluate consistency between asset and reference.

    If no reference provided, checks internal consistency (self-consistency).
    Measures:
    1. Color consistency (histogram similarity)
    2. Edge/structure consistency
    3. Texture consistency

    Returns score in [0, 1] where higher is more consistent.
    """
    img = Image.open(asset).convert("RGB")
    arr = np.asarray(img, dtype=np.float32) / 255.0

    if reference is None or not reference.exists():
        # Self-consistency: check image quality metrics
        # 1. Color uniformity across regions (0-0.4)
        h, w, _ = arr.shape
        regions = [
            arr[:h//2, :w//2],  # Top-left
            arr[:h//2, w//2:],  # Top-right
            arr[h//2:, :w//2],  # Bottom-left
            arr[h//2:, w//2:],  # Bottom-right
        ]
        mean_colors = [np.mean(r, axis=(0, 1)) for r in regions]
        color_variance = float(np.var(mean_colors))
        color_consistency = 0.4 * (1.0 - min(color_variance / 0.1, 1.0))

        # 2. Edge consistency (0-0.3)
        gray = np.asarray(Image.open(asset).convert("L"), dtype=np.float32) / 255.0
        edges = np.gradient(gray)
        edge_strength = float(np.mean([np.std(e) for e in edges]))
        edge_consistency = 0.3 * min(edge_strength / 0.2, 1.0)

        # 3. Texture consistency (0-0.3)
        texture_variance = float(np.var(arr))
        texture_consistency = 0.3 * min(texture_variance / 0.05, 1.0)

        total_score = color_consistency + edge_consistency + texture_consistency
        return float(np.clip(total_score, 0.0, 1.0))

    # Compare with reference
    ref_img = Image.open(reference).convert("RGB")
    ref_arr = np.asarray(ref_img, dtype=np.float32) / 255.0

    # Resize reference to match asset if needed
    if ref_arr.shape != arr.shape:
        ref_img = ref_img.resize((arr.shape[1], arr.shape[0]), Image.Resampling.LANCZOS)
        ref_arr = np.asarray(ref_img, dtype=np.float32) / 255.0

    # Color histogram similarity (0-0.5)
    color_score = 0.0
    for ch in range(3):
        hist1, _ = np.histogram(arr[:, :, ch], bins=32, range=(0.0, 1.0))
        hist2, _ = np.histogram(ref_arr[:, :, ch], bins=32, range=(0.0, 1.0))
        hist1 = hist1 / (np.sum(hist1) + 1e-8)
        hist2 = hist2 / (np.sum(hist2) + 1e-8)
        # Bhattacharyya coefficient
        bc = float(np.sum(np.sqrt(hist1 * hist2)))
        color_score += bc / 3.0
    color_score *= 0.5

    # Structure similarity (0-0.5)
    gray1 = np.mean(arr, axis=2)
    gray2 = np.mean(ref_arr, axis=2)
    # Normalized cross-correlation
    gray1_norm = gray1 - np.mean(gray1)
    gray2_norm = gray2 - np.mean(gray2)
    correlation = float(np.sum(gray1_norm * gray2_norm) /
                       (np.sqrt(np.sum(gray1_norm**2) * np.sum(gray2_norm**2)) + 1e-8))
    structure_score = 0.5 * (correlation + 1.0) / 2.0  # Map [-1, 1] to [0, 1]

    total_score = color_score + structure_score
    return float(np.clip(total_score, 0.0, 1.0))


def compute_metrics(asset: Path, color_ref: Optional[Path] = None) -> Tuple[Dict[str, float], Dict[str, Dict]]:
    metrics: Dict[str, float] = {}
    diagnostics: Dict[str, Dict] = {}

    # Sharpness
    v, err, ms = _timed(sharpness_score, asset)
    if err is None:
        metrics["sharpness"] = float(v)
        backend = "rust" if v in (0.0,) else "rust_or_py"  # heuristic placeholder
        diagnostics["sharpness"] = asdict(Diagnostic(backend=backend, ok=True, ms=ms))
    else:
        # fallback already attempted inside sharpness_score; record failure
        metrics["sharpness"] = 0.0
        diagnostics["sharpness"] = asdict(Diagnostic(backend="fallback", ok=False, ms=ms, error=str(err)))

    # Color fidelity
    v2, err2, ms2 = _timed(color_fidelity_score, asset, color_ref)
    if err2 is None:
        metrics["color_fidelity"] = float(v2)
        diagnostics["color_fidelity"] = asdict(Diagnostic(backend="cpp_or_py", ok=True, ms=ms2))
    else:
        metrics["color_fidelity"] = 0.0
        diagnostics["color_fidelity"] = asdict(Diagnostic(backend="fallback", ok=False, ms=ms2, error=str(err2)))

    # Anatomy score - Use advanced if available
    if ADVANCED_METRICS_AVAILABLE and USE_ADVANCED_METRICS:
        v3, err3, ms3 = _timed(lambda p: anatomy_score_advanced(p)[0], asset)
        backend_name = "python_advanced_anatomy"
    else:
        v3, err3, ms3 = _timed(anatomy_score, asset)
        backend_name = "python_heuristic"

    if err3 is None:
        metrics["anatomy"] = float(v3)
        diagnostics["anatomy"] = asdict(Diagnostic(backend=backend_name, ok=True, ms=ms3))
    else:
        metrics["anatomy"] = 0.0
        diagnostics["anatomy"] = asdict(Diagnostic(backend="fallback", ok=False, ms=ms3, error=str(err3)))

    # Prompt alignment score - Use advanced if available
    if ADVANCED_METRICS_AVAILABLE and USE_ADVANCED_METRICS:
        v4, err4, ms4 = _timed(lambda p: prompt_alignment_score_advanced(p, None)[0], asset)
        backend_name = "python_advanced_prompt_alignment"
    else:
        v4, err4, ms4 = _timed(prompt_alignment_score, asset, None)
        backend_name = "python_heuristic"

    if err4 is None:
        metrics["prompt_alignment"] = float(v4)
        diagnostics["prompt_alignment"] = asdict(Diagnostic(backend=backend_name, ok=True, ms=ms4))
    else:
        metrics["prompt_alignment"] = 0.0
        diagnostics["prompt_alignment"] = asdict(Diagnostic(backend="fallback", ok=False, ms=ms4, error=str(err4)))

    # Consistency score - Use advanced if available
    if ADVANCED_METRICS_AVAILABLE and USE_ADVANCED_METRICS:
        v5, err5, ms5 = _timed(lambda p: consistency_score_advanced(p, color_ref)[0], asset)
        backend_name = "python_advanced_consistency"
    else:
        v5, err5, ms5 = _timed(consistency_score, asset, color_ref)
        backend_name = "python_heuristic"

    if err5 is None:
        metrics["consistency"] = float(v5)
        diagnostics["consistency"] = asdict(Diagnostic(backend=backend_name, ok=True, ms=ms5))
    else:
        metrics["consistency"] = 0.0
        diagnostics["consistency"] = asdict(Diagnostic(backend="fallback", ok=False, ms=ms5, error=str(err5)))

    return metrics, diagnostics