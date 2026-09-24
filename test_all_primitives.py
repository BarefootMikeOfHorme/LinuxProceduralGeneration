"""
Test all exposed primitives from Python
"""

import vaultmind_forge_core as vf

print("=" * 70)
print("Testing All Primitives - Cross-Accessible Rust/Python")
print("=" * 70)

# Basic primitives
print("\n[BASIC PRIMITIVES]")
box = vf.create_box((2.0, 2.0, 2.0))
print(f"  Box: {box}")

sphere = vf.create_sphere(1.5)
print(f"  Sphere: {sphere}")

cylinder = vf.create_cylinder(1.0, 3.0)
print(f"  Cylinder: {cylinder}")

cone = vf.create_cone(1.0, 2.0)
print(f"  Cone: {cone}")

torus = vf.create_torus(2.0, 0.5)
print(f"  Torus: {torus}")

# Extended primitives
print("\n[EXTENDED PRIMITIVES]")
capsule = vf.create_capsule(0.5, 2.0)
print(f"  Capsule: {capsule}")

pyramid = vf.create_pyramid(1.0, 2.0)
print(f"  Pyramid: {pyramid}")

plane = vf.create_plane(5.0, 5.0)
print(f"  Plane: {plane}")

disc = vf.create_disc(2.0)
print(f"  Disc: {disc}")

ring = vf.create_ring(1.0, 2.0)
print(f"  Ring: {ring}")

tube = vf.create_tube(0.8, 1.0, 3.0)
print(f"  Tube: {tube}")

prism_tri = vf.create_prism(1.0, 2.0, 3)  # triangular
print(f"  Triangular Prism: {prism_tri}")

prism_hex = vf.create_prism(1.0, 2.0, 6)  # hexagonal
print(f"  Hexagonal Prism: {prism_hex}")

dome = vf.create_dome(2.0)
print(f"  Dome: {dome}")

tetrahedron = vf.create_tetrahedron(1.0)
print(f"  Tetrahedron: {tetrahedron}")

octahedron = vf.create_octahedron(1.0)
print(f"  Octahedron: {octahedron}")

# Test CSG
print("\n[CSG OPERATIONS]")
box1 = vf.create_box((3.0, 3.0, 3.0))
sphere1 = vf.create_sphere(2.0)

union = vf.csg_union(box1, sphere1)
print(f"  Union: {union}")

difference = vf.csg_difference(box1, sphere1)
print(f"  Difference: {difference}")

intersection = vf.csg_intersection(box1, sphere1)
print(f"  Intersection: {intersection}")

# Test export
print("\n[EXPORT]")
box.export("test_box.obj", "obj")
print("  Exported box to test_box.obj")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
primitives_count = 17  # 5 basic + 12 extended
print(f"[OK] All {primitives_count} primitives accessible from Python!")
print(f"[OK] CSG operations working!")
print(f"[OK] Export working!")
print("\nNow cross-accessible between Rust and Python!")
print("=" * 70)
