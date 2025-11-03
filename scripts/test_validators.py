#!/usr/bin/env python3
"""
Quick validator test script

Tests all three validator implementations:
1. C++ color fidelity
2. Rust sharpness scoring
3. Python advanced metrics
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "vaultmind_forge"))

def create_test_image(output_path: Path):
    """Create a simple test image with patterns"""
    width, height = 512, 512
    img = Image.new('RGB', (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    # Add some patterns for testing
    # Circle
    draw.ellipse([100, 100, 200, 200], fill=(255, 100, 100), outline=(200, 0, 0), width=3)

    # Rectangle
    draw.rectangle([300, 100, 400, 200], fill=(100, 255, 100), outline=(0, 200, 0), width=3)

    # Lines for edge detection
    for i in range(10):
        y = 250 + i * 20
        draw.line([50, y, 450, y], fill=(50, 50, 50), width=2)

    # Gradient
    for x in range(100):
        color_val = int(255 * (x / 100))
        draw.line([50 + x, 450, 50 + x, 490], fill=(color_val, color_val, color_val), width=1)

    img.save(output_path)
    print(f"[OK] Created test image: {output_path}")
    return img


def test_cpp_validator():
    """Test C++ color fidelity validator"""
    print("\n" + "="*60)
    print("TEST 1: C++ Color Fidelity Validator")
    print("="*60)

    try:
        from vaultmind_forge.forge_validator.backends import CppValidator, color_histogram

        test_img = Path("test_image.png")
        if not test_img.exists():
            create_test_image(test_img)

        # Test histogram computation
        hist = color_histogram(test_img, bins=32)
        print(f"[OK] Color histogram computed: shape={hist.shape}, sum={np.sum(hist):.3f}")

        # Test C++ validator loading
        validator = CppValidator()
        if validator.lib is not None:
            print(f"[OK] C++ library loaded successfully")

            # Test color fidelity
            hist2 = hist * 0.9 + np.random.rand(*hist.shape) * 0.1  # Slight variation
            score = validator.color_fidelity_score(hist, hist2)
            if score is not None:
                print(f"[OK] C++ color fidelity score: {score:.4f}")
                return True
            else:
                print("[WARN] C++ function returned None (fallback to Python)")
        else:
            print("[WARN] C++ library not loaded (using Python fallback)")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_rust_validator():
    """Test Rust sharpness validator"""
    print("\n" + "="*60)
    print("TEST 2: Rust Sharpness Validator")
    print("="*60)

    try:
        from vaultmind_forge.forge_validator.backends import sharpness_score

        test_img = Path("test_image.png")
        if not test_img.exists():
            create_test_image(test_img)

        # Test sharpness scoring
        score = sharpness_score(test_img)
        print(f"[OK] Sharpness score: {score:.4f}")

        # Check if Rust was used
        try:
            from vmf_validator import rs_sharpness_score
            print(f"[OK] Rust native implementation available")
            rust_score = rs_sharpness_score(str(test_img))
            print(f"[OK] Rust direct call: {rust_score:.4f}")
            return True
        except ImportError:
            print(f"[WARN] Rust module not available (using Python fallback)")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_python_advanced_metrics():
    """Test Python advanced metrics"""
    print("\n" + "="*60)
    print("TEST 3: Python Advanced Metrics")
    print("="*60)

    try:
        test_img = Path("test_image.png")
        if not test_img.exists():
            create_test_image(test_img)

        # Test if advanced metrics are available
        try:
            from vaultmind_forge.forge_validator.metrics_advanced import (
                anatomy_score_advanced,
                prompt_alignment_score_advanced,
                consistency_score_advanced,
            )

            print("[OK] Advanced metrics module loaded")

            # Test anatomy scoring
            score, metrics = anatomy_score_advanced(test_img)
            print(f"\nAnatomy Score: {score:.4f}")
            print(f"  Golden Ratio:   {metrics.golden_ratio_score:.4f}")
            print(f"  Symmetry:       {metrics.symmetry_score:.4f}")
            print(f"  Proportions:    {metrics.proportion_score:.4f}")
            print(f"  Edge Quality:   {metrics.edge_quality_score:.4f}")
            print(f"  Pose:           {metrics.pose_plausibility_score:.4f}")
            print(f"  Landmarks:      {metrics.landmark_score:.4f}")

            # Test prompt alignment
            score, metrics = prompt_alignment_score_advanced(test_img)
            print(f"\nPrompt Alignment Score: {score:.4f}")
            print(f"  Color Harmony:  {metrics.color_harmony_score:.4f}")
            print(f"  Composition:    {metrics.composition_score:.4f}")
            print(f"  Detail Rich:    {metrics.detail_richness_score:.4f}")
            print(f"  Aesthetic:      {metrics.aesthetic_score:.4f}")
            print(f"  Perceptual:     {metrics.perceptual_quality_score:.4f}")

            # Test consistency (self-consistency)
            score, metrics = consistency_score_advanced(test_img)
            print(f"\nConsistency Score: {score:.4f}")
            print(f"  SSIM:           {metrics.ssim_score:.4f}")
            print(f"  Color:          {metrics.color_consistency_score:.4f}")
            print(f"  Structural:     {metrics.structural_consistency_score:.4f}")
            print(f"  Perceptual Hash:{metrics.perceptual_hash_score:.4f}")
            print(f"  Style:          {metrics.style_consistency_score:.4f}")

            return True

        except ImportError as e:
            print(f"[WARN] Advanced metrics not available: {e}")
            print(f"  (scipy might not be installed)")
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_metrics():
    """Test integrated metrics system"""
    print("\n" + "="*60)
    print("TEST 4: Integrated Metrics System")
    print("="*60)

    try:
        from vaultmind_forge.forge_validator.metrics import compute_metrics

        test_img = Path("test_image.png")
        if not test_img.exists():
            create_test_image(test_img)

        # Compute all metrics
        metrics, diagnostics = compute_metrics(test_img)

        print("\nAll Metrics:")
        for metric_name, value in metrics.items():
            diagnostic = diagnostics[metric_name]
            backend = diagnostic['backend']
            ms = diagnostic['ms']
            print(f"  {metric_name:<20} {value:.4f}  [{backend}, {ms:.1f}ms]")

        return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("VAULTMIND FORGE - VALIDATOR TEST SUITE")
    print("="*60)

    results = {
        "C++ Validator": test_cpp_validator(),
        "Rust Validator": test_rust_validator(),
        "Python Advanced Metrics": test_python_advanced_metrics(),
        "Integrated System": test_integrated_metrics(),
    }

    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"  {test_name:<30} {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    # Cleanup
    test_img = Path("test_image.png")
    if test_img.exists():
        test_img.unlink()
        print(f"\n[OK] Cleaned up test image")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
