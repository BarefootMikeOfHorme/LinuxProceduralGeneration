#!/usr/bin/env python3
"""
Test suite for Rust validator functions via PyO3 bindings

Tests the production-quality image quality metrics:
- rs_sharpness_score()
- rs_color_fidelity()
- rs_contrast_score()

Supports both Python 3.13 and 3.14+ via adaptive build system.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_rust_validator_import():
    """Test that Rust validator module can be imported"""
    print("\n=== Test 1: Import Rust Validator Module ===")

    try:
        import vmf_validator
        print("✅ Successfully imported vmf_validator")

        # Check available functions
        expected_functions = [
            'rs_sharpness_score',
            'rs_color_fidelity',
            'rs_contrast_score',
            'generate_perlin_texture',
            'generate_simplex_pattern',
            'generate_fbm_heightmap',
            'generate_variation_seeds',
            'generate_perlin_advanced'
        ]

        available = []
        missing = []

        for func_name in expected_functions:
            if hasattr(vmf_validator, func_name):
                available.append(func_name)
                print(f"  ✅ {func_name}")
            else:
                missing.append(func_name)
                print(f"  ❌ {func_name} (missing)")

        print(f"\nAvailable: {len(available)}/{len(expected_functions)} functions")

        return len(missing) == 0

    except ImportError as e:
        print(f"❌ Failed to import vmf_validator: {e}")
        print("\nTroubleshooting:")
        print("1. Build the Rust module:")
        print("   cd vaultmind_forge/native/rust/validator")
        print("   cargo build --release")
        print("2. Copy .so/.pyd to Python path")
        return False


def test_sharpness_validator():
    """Test sharpness score on test images"""
    print("\n=== Test 2: Sharpness Validator ===")

    try:
        import vmf_validator
    except ImportError:
        print("⚠️  Skipping - vmf_validator not available")
        return False

    # Find test images
    test_images = list(Path(project_root / "assets").rglob("*.png"))[:3]

    if not test_images:
        print("⚠️  No test images found in assets/")
        return False

    print(f"Testing on {len(test_images)} images:")

    scores = []
    for img_path in test_images:
        try:
            score = vmf_validator.rs_sharpness_score(str(img_path))
            scores.append(score)
            print(f"  ✅ {img_path.name}: sharpness = {score:.4f}")
        except Exception as e:
            print(f"  ❌ {img_path.name}: {e}")
            return False

    # Validate score range
    for score in scores:
        if not (0.0 <= score <= 1.0):
            print(f"❌ Invalid score range: {score}")
            return False

    avg_score = sum(scores) / len(scores)
    print(f"\n✅ Average sharpness: {avg_score:.4f}")
    print(f"✅ Range: {min(scores):.4f} - {max(scores):.4f}")

    return True


def test_color_fidelity_validator():
    """Test color fidelity score on test images"""
    print("\n=== Test 3: Color Fidelity Validator ===")

    try:
        import vmf_validator
    except ImportError:
        print("⚠️  Skipping - vmf_validator not available")
        return False

    # Find test images
    test_images = list(Path(project_root / "assets").rglob("*.png"))[:3]

    if not test_images:
        print("⚠️  No test images found in assets/")
        return False

    print(f"Testing on {len(test_images)} images:")

    scores = []
    for img_path in test_images:
        try:
            score = vmf_validator.rs_color_fidelity(str(img_path))
            scores.append(score)
            print(f"  ✅ {img_path.name}: color_fidelity = {score:.4f}")
        except Exception as e:
            print(f"  ❌ {img_path.name}: {e}")
            return False

    # Validate score range
    for score in scores:
        if not (0.0 <= score <= 1.0):
            print(f"❌ Invalid score range: {score}")
            return False

    avg_score = sum(scores) / len(scores)
    print(f"\n✅ Average color fidelity: {avg_score:.4f}")
    print(f"✅ Range: {min(scores):.4f} - {max(scores):.4f}")

    return True


def test_contrast_validator():
    """Test contrast score on test images"""
    print("\n=== Test 4: Contrast Validator ===")

    try:
        import vmf_validator
    except ImportError:
        print("⚠️  Skipping - vmf_validator not available")
        return False

    # Find test images
    test_images = list(Path(project_root / "assets").rglob("*.png"))[:3]

    if not test_images:
        print("⚠️  No test images found in assets/")
        return False

    print(f"Testing on {len(test_images)} images:")

    scores = []
    for img_path in test_images:
        try:
            score = vmf_validator.rs_contrast_score(str(img_path))
            scores.append(score)
            print(f"  ✅ {img_path.name}: contrast = {score:.4f}")
        except Exception as e:
            print(f"  ❌ {img_path.name}: {e}")
            return False

    # Validate score range
    for score in scores:
        if not (0.0 <= score <= 1.0):
            print(f"❌ Invalid score range: {score}")
            return False

    avg_score = sum(scores) / len(scores)
    print(f"\n✅ Average contrast: {avg_score:.4f}")
    print(f"✅ Range: {min(scores):.4f} - {max(scores):.4f}")

    return True


def test_all_metrics_combined():
    """Test all three metrics on a single image for comprehensive analysis"""
    print("\n=== Test 5: Combined Metrics Analysis ===")

    try:
        import vmf_validator
    except ImportError:
        print("⚠️  Skipping - vmf_validator not available")
        return False

    # Find a test image
    test_images = list(Path(project_root / "assets").rglob("*.png"))

    if not test_images:
        print("⚠️  No test images found in assets/")
        return False

    test_img = test_images[0]
    print(f"Analyzing: {test_img.name}\n")

    try:
        sharpness = vmf_validator.rs_sharpness_score(str(test_img))
        color_fidelity = vmf_validator.rs_color_fidelity(str(test_img))
        contrast = vmf_validator.rs_contrast_score(str(test_img))

        print(f"  Sharpness:      {sharpness:.4f} {'✅' if sharpness > 0.5 else '⚠️'}")
        print(f"  Color Fidelity: {color_fidelity:.4f} {'✅' if color_fidelity > 0.5 else '⚠️'}")
        print(f"  Contrast:       {contrast:.4f} {'✅' if contrast > 0.5 else '⚠️'}")

        # Calculate overall quality score
        overall = (sharpness * 0.4 + color_fidelity * 0.35 + contrast * 0.25)
        print(f"\n  Overall Quality: {overall:.4f} {'✅' if overall > 0.6 else '⚠️'}")

        if overall > 0.7:
            print("  Rating: Excellent")
        elif overall > 0.6:
            print("  Rating: Good")
        elif overall > 0.5:
            print("  Rating: Acceptable")
        else:
            print("  Rating: Needs Improvement")

        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_python_version_compatibility():
    """Test Python version and PyO3 compatibility"""
    print("\n=== Test 6: Python Version Compatibility ===")

    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

    if python_version.major == 3:
        if python_version.minor == 13:
            print("✅ Python 3.13 - Native PyO3 support")
            return True
        elif python_version.minor >= 14:
            print("✅ Python 3.14+ - Using ABI3 forward compatibility")
            print("  (Enabled via build.rs auto-detection)")
            return True
        else:
            print(f"⚠️  Python 3.{python_version.minor} - May have limited support")
            return True
    else:
        print(f"❌ Unsupported Python version: {python_version.major}.{python_version.minor}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Rust Validator Test Suite")
    print("Multi-Python Version Support (3.13 and 3.14+)")
    print("=" * 60)

    tests = [
        ("Python Version Compatibility", test_python_version_compatibility),
        ("Rust Module Import", test_rust_validator_import),
        ("Sharpness Validator", test_sharpness_validator),
        ("Color Fidelity Validator", test_color_fidelity_validator),
        ("Contrast Validator", test_contrast_validator),
        ("Combined Metrics", test_all_metrics_combined),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
