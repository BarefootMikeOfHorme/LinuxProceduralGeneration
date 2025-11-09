"""
Test suite for forge_procedural module
Verifies all procedural generation functionality end-to-end
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from forge_procedural import ProceduralGenerator, NoiseType, NoisePreset
import numpy as np


def test_generator_initialization():
    """Test generator initializes with Rust backend"""
    print("\n=== Test 1: Generator Initialization ===")
    try:
        gen = ProceduralGenerator()
        print("[OK] ProceduralGenerator initialized")
        return True
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        return False


def test_texture_presets():
    """Test all texture presets"""
    print("\n=== Test 2: Texture Presets ===")
    gen = ProceduralGenerator()

    texture_presets = ['clouds', 'marble', 'wood_grain', 'water', 'fire', 'smoke']
    passed = 0
    failed = 0

    for preset_name in texture_presets:
        try:
            texture = gen.generate_texture(preset_name, size=(256, 256), seed=42)

            # Validate output
            assert isinstance(texture, np.ndarray), "Output is not numpy array"
            assert texture.shape == (256, 256), f"Wrong shape: {texture.shape}"
            assert texture.dtype == np.uint8, f"Wrong dtype: {texture.dtype}"
            assert texture.min() >= 0 and texture.max() <= 255, "Values out of range"

            print(f"[OK] Preset '{preset_name}': {texture.shape}, range [{texture.min()}-{texture.max()}]")
            passed += 1

        except Exception as e:
            print(f"[FAIL] Preset '{preset_name}': {e}")
            failed += 1

    print(f"\nTexture Presets: {passed} passed, {failed} failed")
    return failed == 0


def test_terrain_presets():
    """Test all terrain presets"""
    print("\n=== Test 3: Terrain Presets ===")
    gen = ProceduralGenerator()

    terrain_presets = ['rolling_hills', 'mountains', 'desert_dunes', 'rocky']
    passed = 0
    failed = 0

    for preset_name in terrain_presets:
        try:
            heightmap = gen.generate_terrain(preset_name, size=(256, 256), seed=42)

            # Validate output
            assert isinstance(heightmap, np.ndarray), "Output is not numpy array"
            assert heightmap.shape == (256, 256), f"Wrong shape: {heightmap.shape}"
            assert heightmap.dtype == np.float32, f"Wrong dtype: {heightmap.dtype}"
            assert heightmap.min() >= 0.0 and heightmap.max() <= 1.0, "Values out of range"

            print(f"[OK] Preset '{preset_name}': {heightmap.shape}, range [{heightmap.min():.3f}-{heightmap.max():.3f}]")
            passed += 1

        except Exception as e:
            print(f"[FAIL] Preset '{preset_name}': {e}")
            failed += 1

    print(f"\nTerrain Presets: {passed} passed, {failed} failed")
    return failed == 0


def test_noise_types():
    """Test direct noise type usage"""
    print("\n=== Test 4: Direct Noise Types ===")
    gen = ProceduralGenerator()

    tests = [
        (NoiseType.PERLIN, {'scale': 4.0, 'octaves': 4}),
        (NoiseType.SIMPLEX, {'frequency': 0.02}),
        (NoiseType.PERLIN_ADVANCED, {'scale': 3.0, 'octaves': 6, 'contrast': 1.2, 'brightness': 0.1}),
    ]

    passed = 0
    failed = 0

    for noise_type, params in tests:
        try:
            texture = gen.generate_texture(noise_type, size=(128, 128), seed=123, **params)

            assert isinstance(texture, np.ndarray), "Output is not numpy array"
            assert texture.shape == (128, 128), f"Wrong shape: {texture.shape}"

            print(f"[OK] NoiseType.{noise_type.value}: {texture.shape}")
            passed += 1

        except Exception as e:
            print(f"[FAIL] NoiseType.{noise_type.value}: {e}")
            failed += 1

    print(f"\nDirect Noise Types: {passed} passed, {failed} failed")
    return failed == 0


def test_variations():
    """Test variation generation"""
    print("\n=== Test 5: Variation Generation ===")
    gen = ProceduralGenerator()

    try:
        variations = gen.generate_variations('clouds', count=5, size=(128, 128), base_seed=42)

        # Validate
        assert len(variations) == 5, f"Expected 5 variations, got {len(variations)}"

        for i, texture in enumerate(variations):
            assert isinstance(texture, np.ndarray), f"Variation {i} is not numpy array"
            assert texture.shape == (128, 128), f"Variation {i} wrong shape: {texture.shape}"

        # Check that variations are actually different
        unique_count = 0
        for i in range(len(variations)):
            for j in range(i+1, len(variations)):
                if not np.array_equal(variations[i], variations[j]):
                    unique_count += 1

        assert unique_count > 0, "All variations are identical!"

        print(f"[OK] Generated 5 variations, {unique_count} unique pairs")
        return True

    except Exception as e:
        print(f"[FAIL] Variation generation: {e}")
        return False


def test_parameter_override():
    """Test parameter override for presets"""
    print("\n=== Test 6: Parameter Override ===")
    gen = ProceduralGenerator()

    try:
        # Generate with preset defaults
        texture1 = gen.generate_texture('clouds', size=(128, 128), seed=42)

        # Generate with overridden parameters
        texture2 = gen.generate_texture('clouds', size=(128, 128), seed=42, octaves=12, scale=10.0)

        # They should be different due to parameter override
        assert not np.array_equal(texture1, texture2), "Parameter override had no effect!"

        print(f"[OK] Parameter override produces different output")
        return True

    except Exception as e:
        print(f"[FAIL] Parameter override: {e}")
        return False


def test_seed_reproducibility():
    """Test that same seed produces same output"""
    print("\n=== Test 7: Seed Reproducibility ===")
    gen = ProceduralGenerator()

    try:
        texture1 = gen.generate_texture('marble', size=(128, 128), seed=999)
        texture2 = gen.generate_texture('marble', size=(128, 128), seed=999)

        assert np.array_equal(texture1, texture2), "Same seed produced different outputs!"

        print(f"[OK] Seed reproducibility verified")
        return True

    except Exception as e:
        print(f"[FAIL] Seed reproducibility: {e}")
        return False


def test_list_presets():
    """Test preset listing"""
    print("\n=== Test 8: List Presets ===")

    try:
        all_presets = ProceduralGenerator.list_presets('all')
        texture_presets = ProceduralGenerator.list_presets('texture')
        terrain_presets = ProceduralGenerator.list_presets('terrain')

        assert len(all_presets) == 10, f"Expected 10 presets, got {len(all_presets)}"
        assert len(texture_presets) == 6, f"Expected 6 texture presets, got {len(texture_presets)}"
        assert len(terrain_presets) == 4, f"Expected 4 terrain presets, got {len(terrain_presets)}"

        print(f"[OK] All presets: {len(all_presets)}")
        print(f"[OK] Texture presets: {len(texture_presets)}")
        print(f"[OK] Terrain presets: {len(terrain_presets)}")

        return True

    except Exception as e:
        print(f"[FAIL] List presets: {e}")
        return False


def test_file_save():
    """Test saving textures and heightmaps"""
    print("\n=== Test 9: File I/O ===")
    gen = ProceduralGenerator()

    output_dir = Path(__file__).parent / "procedural_test_output"
    output_dir.mkdir(exist_ok=True)

    try:
        # Generate and save texture
        texture = gen.generate_texture('fire', size=(256, 256), seed=42)
        texture_path = output_dir / "test_fire_texture.png"
        ProceduralGenerator.save_texture(texture, texture_path)

        assert texture_path.exists(), "Texture file not saved"
        assert texture_path.stat().st_size > 0, "Texture file is empty"

        print(f"[OK] Saved texture: {texture_path.name} ({texture_path.stat().st_size} bytes)")

        # Generate and save heightmap
        heightmap = gen.generate_terrain('mountains', size=(256, 256), seed=42)
        heightmap_path = output_dir / "test_mountains_heightmap.png"
        ProceduralGenerator.save_heightmap(heightmap, heightmap_path)

        assert heightmap_path.exists(), "Heightmap file not saved"
        assert heightmap_path.stat().st_size > 0, "Heightmap file is empty"

        print(f"[OK] Saved heightmap: {heightmap_path.name} ({heightmap_path.stat().st_size} bytes)")

        print(f"\nTest outputs saved to: {output_dir}")
        return True

    except Exception as e:
        print(f"[FAIL] File I/O: {e}")
        return False


def run_all_tests():
    """Run complete test suite"""
    print("=" * 60)
    print("PROCEDURAL GENERATION MODULE TEST SUITE")
    print("=" * 60)

    tests = [
        test_generator_initialization,
        test_texture_presets,
        test_terrain_presets,
        test_noise_types,
        test_variations,
        test_parameter_override,
        test_seed_reproducibility,
        test_list_presets,
        test_file_save,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n[ERROR] Test crashed: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
