"""
Test script to verify pipeline path structure and all procedural generation destinations
"""

from pathlib import Path
import sys

# Add vaultmind_forge to path
sys.path.insert(0, str(Path(__file__).parent))

from vaultmind_forge.forge_executor.pipeline import AssetPipeline

def test_pipeline_paths():
    """Test that all pipeline paths are created correctly"""
    print("=" * 60)
    print("PIPELINE PATH STRUCTURE TEST")
    print("=" * 60)
    print()

    # Initialize pipeline
    pipeline = AssetPipeline()

    print(f"Base Path: {pipeline.base_path}")
    print()

    # Test generated paths
    print("GENERATED ASSET PATHS:")
    print("-" * 60)
    gen_types = ['textures', 'models', 'materials', 'animations', 'environments',
                 'characters', 'props', 'effects', 'audio', 'standard']

    for gen_type in gen_types:
        path = pipeline.get_path('generated', gen_type)
        exists = "EXISTS" if path.exists() else "MISSING"
        print(f"  {gen_type:15} -> [{exists}]")
        print(f"    {path}")
    print()

    # Test validated paths
    print("VALIDATED ASSET PATHS:")
    print("-" * 60)
    val_types = ['winners', 'rejected', 'flagged']

    for val_type in val_types:
        path = pipeline.get_path('validated', val_type)
        exists = "EXISTS" if path.exists() else "MISSING"
        print(f"  {val_type:15} -> [{exists}]")
        print(f"    {path}")
    print()

    # Test output paths
    print("ENGINE OUTPUT PATHS:")
    print("-" * 60)
    engines = ['unity', 'unreal', 'godot', 'web', 'blender']

    for engine in engines:
        path = pipeline.get_path('output', engine)
        exists = "EXISTS" if path.exists() else "MISSING"
        print(f"  {engine:15} -> [{exists}]")
        print(f"    {path}")
    print()

    # Test packages and temp paths
    print("OTHER PATHS:")
    print("-" * 60)
    packages_path = pipeline.get_path('packages', None)
    temp_path = pipeline.get_path('temp', None)

    print(f"  packages -> [{'EXISTS' if packages_path.exists() else 'MISSING'}]")
    print(f"    {packages_path}")
    print(f"  temp -> [{'EXISTS' if temp_path.exists() else 'MISSING'}]")
    print(f"    {temp_path}")
    print()

    # Count total directories
    total_dirs = len(gen_types) + len(val_types) + len(engines) + 2
    print("=" * 60)
    print(f"TOTAL DIRECTORIES CREATED: {total_dirs}")
    print("=" * 60)
    print()

    # Test different asset type generations
    print("TESTING DIFFERENT ASSET TYPE GENERATIONS:")
    print("-" * 60)

    test_cases = [
        ("fantasy sword texture", "textures"),
        ("medieval knight character", "characters"),
        ("stone wall material", "materials"),
        ("running animation", "animations"),
        ("forest environment", "environments"),
        ("wooden crate prop", "props"),
        ("fire particle effect", "effects"),
    ]

    for prompt, asset_type in test_cases:
        print(f"\nGenerating: {asset_type.upper()}")
        print(f"  Prompt: '{prompt}'")

        # Simulate pipeline execution to verify path
        result = pipeline.run_generation_pipeline(
            prompt=prompt,
            output_type=asset_type,
            target_engines=["unity", "unreal"]
        )

        print(f"  Success: {result.success}")
        print(f"  Outputs: {list(result.outputs.keys())}")

    print()
    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline_paths()
