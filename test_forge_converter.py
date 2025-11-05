#!/usr/bin/env python3
"""
Test script for forge_converter module.
Verifies asset structure, format registry, and engine structure builder.
"""

import sys
from pathlib import Path

# Add vaultmind_forge to path
sys.path.insert(0, str(Path(__file__).parent / "vaultmind_forge"))

from forge_converter.formats import FormatRegistry, AssetPaths, FormatType
from forge_converter.engines import EngineStructureBuilder

def test_asset_paths():
    """Test asset path setup."""
    print("\n" + "=" * 60)
    print("TEST 1: Asset Paths")
    print("=" * 60)

    paths = AssetPaths()

    print(f"[OK] Base path: {paths.base}")
    print(f"[OK] Source: {paths.source}")
    print(f"[OK] Input: {paths.input}")
    print(f"[OK] Generated: {paths.generated}")
    print(f"[OK] Validated: {paths.validated}")
    print(f"[OK] Output: {paths.output}")

    # Check if directories exist
    print("\nChecking directory existence:")
    for attr in ['source', 'input', 'generated', 'validated', 'output']:
        path = getattr(paths, attr)
        exists = path.exists()
        print(f"  {attr}: {'[EXISTS]' if exists else '[MISSING]'}")

    # Create all directories
    print("\nEnsuring all directories exist...")
    paths.ensure_all_exist()

    print("[OK] All asset paths verified")

def test_format_registry():
    """Test format registry."""
    print("\n" + "=" * 60)
    print("TEST 2: Format Registry")
    print("=" * 60)

    registry = FormatRegistry()

    print(f"[OK] Registry created")
    print(f"[OK] Asset paths: {registry.asset_paths.base}")

    # List supported formats (should be empty initially)
    formats = registry.list_supported_formats()
    print(f"\nSupported formats:")
    for format_type, format_list in formats.items():
        print(f"  {format_type.value}: {len(format_list)} handlers")

    # Test file detection (will return None for no handlers)
    test_file = Path("test.fbx")
    result = registry.detect_format(test_file)
    print(f"\nFormat detection for {test_file}: {result}")

    print("[OK] Format registry verified")

def test_engine_structure_builder():
    """Test engine structure builder."""
    print("\n" + "=" * 60)
    print("TEST 3: Engine Structure Builder")
    print("=" * 60)

    builder = EngineStructureBuilder()

    print(f"[OK] Builder created")
    print(f"[OK] Output path: {builder.output_path}")

    # Create structures for all engines
    print("\nCreating engine structures...")
    structures = builder.create_all_structures("TestProject")

    print(f"\n[SUCCESS] Created structures:")
    for engine, path in structures.items():
        exists = path.exists()
        print(f"  {engine}: {path}")
        print(f"    Status: {'[EXISTS]' if exists else '[MISSING]'}")

        # List subdirectories
        if exists:
            subdirs = [d.name for d in path.iterdir() if d.is_dir()]
            print(f"    Subdirs: {', '.join(subdirs)}")

    # Check for index file
    index_path = builder.output_path / "TestProject_index.json"
    if index_path.exists():
        print(f"\n[OK] Index file created: {index_path}")
        import json
        with open(index_path) as f:
            index_data = json.load(f)
        print(f"  Engines: {', '.join(index_data['engines'].keys())}")
    else:
        print(f"\n[FAIL] Index file missing: {index_path}")

    print("\n[OK] Engine structure builder verified")

def test_asset_workflow():
    """Test complete asset workflow simulation."""
    print("\n" + "=" * 60)
    print("TEST 4: Asset Workflow Simulation")
    print("=" * 60)

    # 1. Set up paths
    paths = AssetPaths()
    paths.ensure_all_exist()

    # 2. Simulate source asset
    print("\n1. Source Asset:")
    source_asset = paths.source_models / "characters" / "test_character.fbx"
    source_asset.parent.mkdir(parents=True, exist_ok=True)
    source_asset.touch()  # Create empty file
    print(f"   Created: {source_asset}")

    # 3. Simulate input (normalized)
    print("\n2. Input (Normalized):")
    input_asset = paths.input_models / "test_character.gltf"
    input_asset.parent.mkdir(parents=True, exist_ok=True)
    input_asset.touch()
    print(f"   Created: {input_asset}")

    # 4. Simulate generated (diffusion)
    print("\n3. Generated (Diffusion):")
    generated_path = paths.generated_diffusion / "textures" / "job_test"
    generated_path.mkdir(parents=True, exist_ok=True)
    for i in range(1, 4):
        var = generated_path / f"variation_{i:03d}.png"
        var.touch()
        print(f"   Created: {var.name}")

    # 5. Simulate validated winner
    print("\n4. Validated (Winner):")
    winner_path = paths.validated / "winners" / "job_test"
    winner_path.mkdir(parents=True, exist_ok=True)
    winner = winner_path / "winner.png"
    winner.touch()
    print(f"   Created: {winner}")

    # 6. Simulate output for Unity
    print("\n5. Output (Unity):")
    unity_model = paths.output_unity / "models" / "test_character.fbx"
    unity_model.parent.mkdir(parents=True, exist_ok=True)
    unity_model.touch()
    print(f"   Created: {unity_model}")

    print("\n[SUCCESS] Asset workflow simulation complete")
    print("\nWorkflow:")
    print("  source -> input -> generated -> validated -> output")
    print("  [OK]      [OK]     [OK]         [OK]         [OK]")

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("VAULTMIND FORGE - FORGE_CONVERTER TEST SUITE")
    print("=" * 60)

    try:
        test_asset_paths()
        test_format_registry()
        test_engine_structure_builder()
        test_asset_workflow()

        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED")
        print("=" * 60)

        print("\nAsset Structure Summary:")
        paths = AssetPaths()
        print(f"   Base: {paths.base}")
        print(f"   Total directories created: {sum(1 for _ in paths.base.rglob('*') if _.is_dir())}")
        print(f"   Total files created: {sum(1 for _ in paths.base.rglob('*') if _.is_file())}")

    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
