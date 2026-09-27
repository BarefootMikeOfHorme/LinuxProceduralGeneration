"""
Test comprehensive output structure for all media types
Verifies directory creation and path resolution
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from forge_procedural import ProceduralGenerator, get_output_structure, ensure_output_directories


def test_output_structure_creation():
    """Test that all output directories are created"""
    print("\n=== Test 1: Output Structure Creation ===")

    try:
        structure = get_output_structure()
        count = structure.ensure_all_directories()

        print(f"[OK] Created {count} output directories")

        # Verify some key paths exist
        test_paths = [
            structure.get_path('procedural', 'textures', 'clouds'),
            structure.get_path('procedural', 'terrain', 'mountains'),
            structure.get_path('3d', 'meshes', 'fbx'),
            structure.get_path('audio', 'music', 'ambient'),
            structure.get_path('engines', 'unity', 'packages'),
        ]

        for path in test_paths:
            assert path.exists(), f"Path doesn't exist: {path}"
            print(f"  [OK] {path}")

        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_category_listing():
    """Test category listing functionality"""
    print("\n=== Test 2: Category Listing ===")

    try:
        structure = get_output_structure()
        categories = structure.list_categories()

        print(f"[OK] Found {len(categories)} top-level categories:")
        for category, subcategories in categories.items():
            print(f"  - {category}: {len(subcategories)} subcategories")

        # Verify expected categories
        expected = ['procedural', '2d', '3d', 'audio', 'video', 'environments', 'special', 'engines']
        for cat in expected:
            assert cat in categories, f"Missing category: {cat}"

        print(f"[OK] All expected categories present")
        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_path_resolution():
    """Test path resolution"""
    print("\n=== Test 3: Path Resolution ===")

    structure = get_output_structure()
    test_cases = [
        # Procedural paths
        ('procedural', 'noise', 'perlin'),
        ('procedural', 'textures', 'marble'),
        ('procedural', 'terrain', 'islands'),
        ('procedural', 'patterns', 'fractals'),

        # 2D paths
        ('2d', 'images', 'png'),
        ('2d', 'textures', 'normal'),
        ('2d', 'sprites', 'characters'),
        ('2d', 'ui', 'icons'),

        # 3D paths
        ('3d', 'meshes', 'obj'),
        ('3d', 'meshes', 'fbx'),
        ('3d', 'meshes', 'gltf'),
        ('3d', 'models', 'weapons'),
        ('3d', 'materials', 'pbr'),
        ('3d', 'animations', 'skeletal'),

        # Audio paths
        ('audio', 'music', 'combat'),
        ('audio', 'sfx', 'weapons'),
        ('audio', 'voice', 'dialogue'),
        ('audio', 'formats', 'wav'),

        # Video paths
        ('video', 'cutscenes'),
        ('video', 'formats', 'mp4'),

        # Environment paths
        ('environments', 'biomes', 'forest'),
        ('environments', 'levels', 'dungeons'),
        ('environments', 'skyboxes', 'space'),

        # Special paths
        ('special', 'vfx', 'particles'),
        ('special', 'shaders', 'hlsl'),
        ('special', 'lighting', 'hdri'),

        # Engine paths
        ('engines', 'unity', 'prefabs'),
        ('engines', 'unreal', 'blueprints'),
        ('engines', 'godot', 'scenes'),
        ('engines', 'web', 'threejs'),
    ]

    passed = 0
    failed = 0

    for path_components in test_cases:
        try:
            path = structure.get_path(*path_components)
            assert isinstance(path, Path), "Not a Path object"
            assert path.exists(), f"Path doesn't exist: {path}"
            passed += 1
        except Exception as e:
            print(f"[FAIL] {' -> '.join(path_components)}: {e}")
            failed += 1

    print(f"[OK] Path resolution: {passed} passed, {failed} failed")
    return failed == 0


def test_all_paths_flat():
    """Test getting all paths as flat dictionary"""
    print("\n=== Test 4: Flat Path Dictionary ===")

    try:
        structure = get_output_structure()
        all_paths = structure.get_all_paths()

        print(f"[OK] Retrieved {len(all_paths)} total endpoint paths")

        # Show some examples
        examples = list(all_paths.items())[:10]
        for key, path in examples:
            print(f"  {key}: {path}")

        # Verify they're all Path objects
        for key, path in all_paths.items():
            assert isinstance(path, Path), f"{key} is not a Path object"

        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_generator_integration():
    """Test ProceduralGenerator integration with output structure"""
    print("\n=== Test 5: Generator Integration ===")

    try:
        # Initialize generator (should create all dirs automatically)
        gen = ProceduralGenerator()

        print(f"[OK] Generator initialized with output structure")

        # Verify generator has output structure
        assert hasattr(gen, 'output'), "Generator missing output attribute"
        assert gen.output is not None, "Generator output is None"

        print(f"[OK] Generator has access to output structure")

        # Test path access through generator
        clouds_path = gen.output.get_path('procedural', 'textures', 'clouds')
        print(f"[OK] Can access paths through generator: {clouds_path}")

        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auto_save_paths():
    """Test automatic save path methods"""
    print("\n=== Test 6: Auto-Save Path Methods ===")

    try:
        gen = ProceduralGenerator()

        # Generate a texture
        texture = gen.generate_texture('clouds', size=(256, 256), seed=42)
        print(f"[OK] Generated clouds texture: {texture.shape}")

        # Save with automatic path resolution
        saved_path = gen.save_texture_auto(texture, 'test_clouds_auto', category='clouds')
        print(f"[OK] Saved to: {saved_path}")

        assert saved_path.exists(), "File wasn't saved"
        assert saved_path.stat().st_size > 0, "File is empty"
        print(f"[OK] File verified: {saved_path.stat().st_size} bytes")

        # Generate terrain
        terrain = gen.generate_terrain('mountains', size=(256, 256), seed=42)
        print(f"[OK] Generated mountains terrain: {terrain.shape}")

        # Save with automatic path resolution
        saved_path = gen.save_heightmap_auto(terrain, 'test_mountains_auto', terrain_type='mountains')
        print(f"[OK] Saved to: {saved_path}")

        assert saved_path.exists(), "File wasn't saved"
        assert saved_path.stat().st_size > 0, "File is empty"
        print(f"[OK] File verified: {saved_path.stat().st_size} bytes")

        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run complete test suite"""
    print("=" * 70)
    print("COMPREHENSIVE OUTPUT STRUCTURE TEST SUITE")
    print("=" * 70)

    tests = [
        test_output_structure_creation,
        test_category_listing,
        test_path_resolution,
        test_all_paths_flat,
        test_generator_integration,
        test_auto_save_paths,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n[ERROR] Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        print("\nComprehensive output structure ready with:")
        structure = get_output_structure()
        all_paths = structure.get_all_paths()
        print(f"  - {len(all_paths)} total output endpoints")
        print(f"  - Procedural generation paths")
        print(f"  - 2D/3D asset paths")
        print(f"  - Audio/Video paths")
        print(f"  - Game environment paths")
        print(f"  - Engine-specific export paths")
        print(f"  - VFX, shaders, lighting paths")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
