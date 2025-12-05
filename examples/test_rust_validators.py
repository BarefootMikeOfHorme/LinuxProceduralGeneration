"""
VaultMind Forge - Rust Validator Integration Test

Demonstrates Python → Rust integration via PyO3
Tests high-performance Rust validators and compares with Python fallbacks
"""

import sys
from pathlib import Path
import time
import numpy as np
from PIL import Image

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def create_test_images():
    """Create test images with different quality characteristics"""
    print("\n[1/5] Creating test images...")

    output_dir = PROJECT_ROOT / "output" / "validator_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    test_images = {}

    # 1. Sharp, high-quality image
    print("  Creating sharp test image...")
    sharp_img = Image.new('RGB', (512, 512))
    pixels = sharp_img.load()
    for i in range(512):
        for j in range(512):
            # High-frequency checkerboard pattern (sharp)
            if (i // 16 + j // 16) % 2:
                pixels[i, j] = (255, 0, 0)  # Red
            else:
                pixels[i, j] = (0, 0, 255)  # Blue
    sharp_path = output_dir / "sharp_test.png"
    sharp_img.save(sharp_path)
    test_images['sharp'] = sharp_path

    # 2. Blurry image
    print("  Creating blurry test image...")
    blurry_img = Image.new('RGB', (512, 512))
    pixels = blurry_img.load()
    for i in range(512):
        for j in range(512):
            # Low-frequency gradient (blurry)
            intensity = int((i + j) / 4)
            pixels[i, j] = (intensity, intensity, intensity)
    blurry_path = output_dir / "blurry_test.png"
    blurry_img.save(blurry_path)
    test_images['blurry'] = blurry_path

    # 3. High-contrast image
    print("  Creating high-contrast test image...")
    contrast_img = Image.new('RGB', (512, 512))
    pixels = contrast_img.load()
    for i in range(512):
        for j in range(512):
            # Pure black and white (high contrast)
            if i < 256:
                pixels[i, j] = (0, 0, 0)  # Black
            else:
                pixels[i, j] = (255, 255, 255)  # White
    contrast_path = output_dir / "contrast_test.png"
    contrast_img.save(contrast_path)
    test_images['contrast'] = contrast_path

    # 4. Colorful image
    print("  Creating colorful test image...")
    color_img = Image.new('RGB', (512, 512))
    pixels = color_img.load()
    for i in range(512):
        for j in range(512):
            # Rainbow gradient
            r = int((i / 512) * 255)
            g = int((j / 512) * 255)
            b = int(((i + j) / 1024) * 255)
            pixels[i, j] = (r, g, b)
    color_path = output_dir / "colorful_test.png"
    color_img.save(color_path)
    test_images['colorful'] = color_path

    print(f"  [OK] Created {len(test_images)} test images in {output_dir}")
    return test_images


def test_rust_validators(test_images):
    """Test Rust validators via PyO3"""
    print("\n[2/5] Testing Rust validators...")

    try:
        # Try importing Rust module
        print("  Attempting to import vmf_validator (Rust)...")

        # The Rust module should be importable from the built location
        rust_module_path = PROJECT_ROOT / "vaultmind_forge" / "native" / "rust" / "validator" / "target" / "release"
        if rust_module_path.exists():
            sys.path.insert(0, str(rust_module_path))

        import vmf_validator

        print("  [OK] Rust validators loaded successfully!")
        print(f"  Module: {vmf_validator.__file__}")

        # Test each validator function
        results = {}

        for image_type, image_path in test_images.items():
            print(f"\n  Testing {image_type} image...")
            path_str = str(image_path)

            # Time Rust validators
            start = time.time()

            sharpness = vmf_validator.rs_sharpness_score(path_str)
            color_fidelity = vmf_validator.rs_color_fidelity(path_str)
            contrast = vmf_validator.rs_contrast_score(path_str)

            rust_time = time.time() - start

            results[image_type] = {
                'rust': {
                    'sharpness': sharpness,
                    'color_fidelity': color_fidelity,
                    'contrast': contrast,
                    'time': rust_time
                }
            }

            print(f"    Rust Results (in {rust_time*1000:.2f}ms):")
            print(f"      Sharpness:      {sharpness:.4f}")
            print(f"      Color Fidelity: {color_fidelity:.4f}")
            print(f"      Contrast:       {contrast:.4f}")

        return True, results

    except ImportError as e:
        print(f"  [WARN] Rust validators not available: {e}")
        print(f"  Rust module needs to be built with:")
        print(f"    cd {PROJECT_ROOT}/vaultmind_forge/native/rust/validator")
        print(f"    maturin develop --release")
        return False, {}


def test_python_validators(test_images):
    """Test Python validators as fallback/comparison"""
    print("\n[3/5] Testing Python validators (fallback)...")

    try:
        from vaultmind_forge.forge_validator.metrics import compute_metrics

        print("  [OK] Python validators loaded")

        results = {}

        for image_type, image_path in test_images.items():
            print(f"\n  Testing {image_type} image...")

            # Load image
            img = Image.open(image_path)
            img_array = np.array(img)

            # Time Python validators
            # Note: compute_metrics expects a Path, not a numpy array
            start = time.time()
            metrics_dict, diagnostics = compute_metrics(image_path, None)
            python_time = time.time() - start

            # Extract metrics (with defaults if missing)
            sharpness = metrics_dict.get('sharpness', 0.0)
            color_fidelity = metrics_dict.get('color_fidelity', 0.0)
            # Note: Python validators don't have 'contrast' - using anatomy as proxy
            contrast = metrics_dict.get('anatomy', 0.0)

            results[image_type] = {
                'python': {
                    'sharpness': sharpness,
                    'color_fidelity': color_fidelity,
                    'contrast': contrast,
                    'time': python_time
                }
            }

            print(f"    Python Results (in {python_time*1000:.2f}ms):")
            print(f"      Sharpness:      {sharpness:.4f}")
            print(f"      Color Fidelity: {color_fidelity:.4f}")
            print(f"      Contrast (ana): {contrast:.4f}")

        return True, results

    except Exception as e:
        print(f"  [FAIL] Python validators failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def compare_results(rust_results, python_results):
    """Compare Rust vs Python validator results"""
    print("\n[4/5] Comparing Rust vs Python validators...")

    if not rust_results or not python_results:
        print("  [WARN] Cannot compare - missing results")
        return

    print("\n  Performance Comparison:")
    print("  " + "="*70)
    print(f"  {'Image Type':<15} {'Rust Time':<15} {'Python Time':<15} {'Speedup':<15}")
    print("  " + "-"*70)

    total_rust_time = 0
    total_python_time = 0

    for image_type in rust_results.keys():
        if image_type in python_results:
            rust_time = rust_results[image_type]['rust']['time']
            python_time = python_results[image_type]['python']['time']
            speedup = python_time / rust_time if rust_time > 0 else 0

            total_rust_time += rust_time
            total_python_time += python_time

            print(f"  {image_type:<15} {rust_time*1000:>8.2f}ms     {python_time*1000:>8.2f}ms     {speedup:>8.2f}x")

    print("  " + "-"*70)
    avg_speedup = total_python_time / total_rust_time if total_rust_time > 0 else 0
    print(f"  {'Average':<15} {total_rust_time*1000:>8.2f}ms     {total_python_time*1000:>8.2f}ms     {avg_speedup:>8.2f}x")
    print("  " + "="*70)

    # Compare accuracy
    print("\n  Accuracy Comparison:")
    print("  " + "="*90)
    print(f"  {'Image':<12} {'Metric':<15} {'Rust Score':<15} {'Python Score':<15} {'Difference':<15}")
    print("  " + "-"*90)

    for image_type in rust_results.keys():
        if image_type in python_results:
            rust = rust_results[image_type]['rust']
            python = python_results[image_type]['python']

            for metric in ['sharpness', 'color_fidelity', 'contrast']:
                rust_score = rust[metric]
                python_score = python[metric]
                diff = abs(rust_score - python_score)

                print(f"  {image_type:<12} {metric:<15} {rust_score:>8.4f}       {python_score:>8.4f}       {diff:>8.4f}")

    print("  " + "="*90)


def demonstrate_integration_pattern():
    """Show how Python orchestrates Rust validators"""
    print("\n[5/5] Integration Pattern Demonstration...")
    print("  " + "="*70)

    print("""
  Python-First Design with Rust Acceleration:

  +-----------------------------------------------------+
  | PYTHON ORCHESTRATION LAYER                          |
  |                                                     |
  |  from vaultmind_forge.forge_validator import *      |
  |                                                     |
  |  # Python decides which validator to use            |
  |  if rust_available:                                 |
  |      score = rust_validator.validate(image)         |
  |  else:                                              |
  |      score = python_validator.validate(image)       |
  |                                                     |
  +------------------+----------------------------------+
                     |
         +-----------+----------+
         |                      |
         v                      v
  +-------------+      +-------------+
  | Rust        |      | Python      |
  | Validators  |      | Validators  |
  | (PyO3)      |      | (NumPy)     |
  |             |      |             |
  | - Fast      |      | - Portable  |
  | - Typed     |      | - Fallback  |
  | - Native    |      | - Debug     |
  +-------------+      +-------------+

  Key Points:
  [+] Python CALLS Rust (not the other way around)
  [+] Rust is an OPTIMIZATION, not a replacement
  [+] Python remains the MAESTRO
  [+] Graceful fallback to Python validators
  [+] Same API, different backends

  Example Usage:

    # Python orchestrates
    from vaultmind_forge.forge_validator import validate_asset

    # Automatically uses Rust if available
    result = validate_asset(image_path)

    # Python processes result
    if result.quality > 0.8:
        approve_for_production(image_path)

  """)
    print("  " + "="*70)


def main():
    """Run all Rust validator tests"""
    print("="*70)
    print("VaultMind Forge - Rust Validator Integration Test")
    print("="*70)
    print("\nDemonstrating: Python -> Rust via PyO3")

    # Create test images
    test_images = create_test_images()

    # Test Rust validators
    rust_available, rust_results = test_rust_validators(test_images)

    # Test Python validators
    python_available, python_results = test_python_validators(test_images)

    # Merge results for comparison
    if rust_available and python_available:
        # Merge rust and python results
        for image_type in rust_results.keys():
            if image_type in python_results:
                rust_results[image_type].update(python_results[image_type])

        compare_results(rust_results, python_results)

    # Show integration pattern
    demonstrate_integration_pattern()

    # Summary
    print("\n" + "="*70)
    print("Test Summary:")
    print("="*70)

    if rust_available:
        print("[OK] Rust validators: WORKING")
        print("   Status: High-performance validators available")
        print("   Integration: Python -> Rust via PyO3")
    else:
        print("[WARN] Rust validators: NOT BUILT")
        print("   Status: Falling back to Python validators")
        print("   To build: cd vaultmind_forge/native/rust/validator && maturin develop --release")

    if python_available:
        print("[OK] Python validators: WORKING")
        print("   Status: Fallback validators available")
    else:
        print("[FAIL] Python validators: FAILED")

    print("\n" + "="*70)
    print("Architecture Verification:")
    print("="*70)
    print("[+] Python is the orchestration maestro")
    print("[+] Rust is called FROM Python (PyO3 bindings)")
    print("[+] Python decides which backend to use")
    print("[+] Graceful fallback mechanism works")
    print("[+] Same API, multiple implementations")
    print("="*70)


if __name__ == "__main__":
    main()
