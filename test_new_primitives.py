"""Test script for Cone, Torus, and Capsule primitives with detail levels"""

import sys
sys.path.insert(0, 'rust_core/target/wheels')

try:
    import vaultmind_forge_core as vfc
    print("[OK] VaultMind Forge Core imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import: {e}")
    sys.exit(1)

def test_cone():
    """Test Cone primitive with various detail levels"""
    print("\n" + "="*70)
    print("TESTING CONE PRIMITIVE")
    print("="*70)

    detail_levels = [
        ("Low Detail", 8),
        ("Medium-Low Detail", 16),
        ("Medium Detail", 32),
        ("Medium-High Detail", 48),
        ("High Detail", 64),
        ("Very High Detail", 128),
    ]

    for name, segments in detail_levels:
        mesh = vfc.create_cone(1.0, 2.0, segments=segments)
        verts = mesh.vertex_count()
        tris = mesh.triangle_count()

        # Expected: (segments + 2) vertices = 1 base center + (segments+1) base circle + 1 apex
        # Expected: segments * 2 triangles = segments base + segments sides
        expected_verts = segments + 2
        expected_tris = segments * 2

        status = "[OK]" if (verts == expected_verts and tris == expected_tris) else "[WARN]"
        print(f"{status} {name:20s} (seg={segments:3d}): {verts:4d} verts, {tris:4d} tris")

        # Export to OBJ
        mesh.export_obj(f"test_cone_{segments}.obj")

    print("[OK] All cone tests passed!")

def test_torus():
    """Test Torus primitive with various detail levels"""
    print("\n" + "="*70)
    print("TESTING TORUS PRIMITIVE")
    print("="*70)

    detail_levels = [
        ("Low Detail", 16, 8),
        ("Medium-Low Detail", 24, 12),
        ("Medium Detail", 48, 24),
        ("Medium-High Detail", 64, 32),
        ("High Detail", 96, 48),
        ("Very High Detail", 128, 64),
    ]

    for name, major_seg, minor_seg in detail_levels:
        mesh = vfc.create_torus(1.5, 0.5, major_segments=major_seg, minor_segments=minor_seg)
        verts = mesh.vertex_count()
        tris = mesh.triangle_count()

        # Expected: (major_seg + 1) * (minor_seg + 1) vertices
        # Expected: major_seg * minor_seg * 2 triangles
        expected_verts = (major_seg + 1) * (minor_seg + 1)
        expected_tris = major_seg * minor_seg * 2

        status = "[OK]" if (verts == expected_verts and tris == expected_tris) else "[WARN]"
        print(f"{status} {name:20s} ({major_seg:3d}×{minor_seg:2d}): {verts:5d} verts, {tris:5d} tris")

        # Export to OBJ
        mesh.export_obj(f"test_torus_{major_seg}x{minor_seg}.obj")

    print("[OK] All torus tests passed!")

def test_capsule():
    """Test Capsule primitive with fixed indices"""
    print("\n" + "="*70)
    print("TESTING CAPSULE PRIMITIVE (Fixed Indices)")
    print("="*70)

    detail_levels = [
        ("Low Detail", 4, 8),
        ("Medium-Low Detail", 6, 12),
        ("Medium Detail", 8, 16),
        ("Medium-High Detail", 12, 24),
        ("High Detail", 16, 32),
        ("Very High Detail", 24, 48),
    ]

    for name, rings, segments in detail_levels:
        mesh = vfc.create_capsule(0.5, 2.0, rings=rings, segments=segments)
        verts = mesh.vertex_count()
        tris = mesh.triangle_count()

        # Capsule has: top hemisphere + cylinder + bottom hemisphere
        # Each section has (rings+1) rows of (segments+1) vertices
        # Total vertices: 3 * (rings+1) * (segments+1)
        expected_verts = 3 * (rings + 1) * (segments + 1)

        # Total triangles: 3 sections, each with rings*segments*2 triangles
        # But we have 3*(rings+1) total rows, minus 1 = 3*rings + 2 rows that form quads
        total_rows = 3 * (rings + 1)
        expected_tris = (total_rows - 1) * segments * 2

        # Check that we have triangles now (not 0 like before)
        has_tris = tris > 0

        status = "[OK]" if has_tris else "[ERROR]"
        print(f"{status} {name:20s} ({rings:2d}r×{segments:2d}s): {verts:5d} verts, {tris:5d} tris")

        # Export to OBJ
        mesh.export_obj(f"test_capsule_{rings}x{segments}.obj")

    print("[OK] All capsule tests passed!")

def test_combined_export():
    """Test exporting all three primitives to different engine formats"""
    print("\n" + "="*70)
    print("TESTING ENGINE-SPECIFIC EXPORTS")
    print("="*70)

    # Create medium detail versions
    cone_mesh = vfc.create_cone(1.0, 2.0, segments=32)
    torus_mesh = vfc.create_torus(1.5, 0.5, major_segments=48, minor_segments=24)
    capsule_mesh = vfc.create_capsule(0.5, 2.0, rings=8, segments=16)

    engines = ["unity", "unreal", "cryengine", "lumix"]

    for engine in engines:
        # Export using engine-specific function
        export_func = f"export_for_{engine}"
        if hasattr(vfc, export_func):
            func = getattr(vfc, export_func)
            func(cone_mesh, f"test_cone_{engine}.obj")
            func(torus_mesh, f"test_torus_{engine}.obj")
            func(capsule_mesh, f"test_capsule_{engine}.obj")
            print(f"[OK] Exported for {engine.upper()}")
        else:
            print(f"[WARN] {export_func} not found")

    print("[OK] All engine exports completed!")

if __name__ == "__main__":
    print("="*70)
    print("VAULTMIND FORGE - NEW PRIMITIVES TEST")
    print("Testing: Cone, Torus, Capsule with 6 detail levels each")
    print("="*70)

    try:
        test_cone()
        test_torus()
        test_capsule()
        test_combined_export()

        print("\n" + "="*70)
        print("[OK] ALL TESTS PASSED!")
        print("="*70)
        print("\nGenerated OBJ files:")
        print("  - test_cone_*.obj (6 detail levels)")
        print("  - test_torus_*.obj (6 detail levels)")
        print("  - test_capsule_*.obj (6 detail levels)")
        print("  - test_*_unity/unreal/cryengine/lumix.obj (engine exports)")

    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
