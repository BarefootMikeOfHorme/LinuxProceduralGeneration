# LPG Geometry Contract Matrix

Use this table during review. Do not mark a cell `pass` without current evidence.

| Area | Contract | Evidence required | Common failure |
| --- | --- | --- | --- |
| Package | `vaultmind_forge` is included by wheel/sdist | Inspect built wheel contents and clean-install import | Discovery rooted below the package directory |
| Optional native | Pure-Python features do not require a local generated wheel | Clean checkout import without build output | Eager import raises `ImportError` |
| ABI | Every called symbol is registered | Binding inventory and focused call test | `load_obj` or other symbol missing |
| Primitive | Dimensions and bounds match public constructor | Fixed-size bounds regression | Exporter reads nonexistent fields |
| Primitive | Closed primitives are watertight | Boundary-edge/manifold test | Cylinder has sides but no caps |
| CSG | Spanning triangles are clipped | Known-volume and face-topology regression | Whole triangle retained |
| Normals | Winding and normals are consistent | Dot-product/orientation assertions | Recomputed normals hide bad winding |
| Validation | Scores and topology checks are real | Adversarial fixture tests | Placeholder or constant fallback values |
| Optimization | Changes and residuals are observable | Before/after mesh assertions | No-op labeled optimized |
| OBJ | Loader and exporter preserve geometry | Parse and round-trip assertions | Missing loader binding |
| glTF | Complete buffers/accessors/indices are emitted | Standards-aware parser validation | JSON skeleton with no mesh payload |
| FBX | Valid FBX or explicit unsupported error | Signature/parser validation | OBJ text labeled FBX |
| OpenSCAD export | Every supported primitive is representable | Per-primitive assertions | Box/Pyramid attribute mismatch |
| OpenSCAD import | Rendered output becomes a real mesh | End-to-end round trip | Call to missing binding |
| Templates | Seeds and kwargs work for all counts | Deterministic repeated-run test | `count=1` drops options |
| Dimensions | Tuple dimensions scale component-wise | Non-uniform scaling test | Tuple multiplied by float |
| Tests | Assertions isolate output | Clean rerun in temporary directory | Root-level generated files and print-only success |

## Known review hotspots

These paths require focused attention when touched, but the checklist remains authoritative:

- `vaultmind_forge/forge_3d/__init__.py`
- `vaultmind_forge/forge_3d/primitives_all.py`
- `vaultmind_forge/forge_3d/mesh.py`
- `vaultmind_forge/forge_3d/factory.py`
- `vaultmind_forge/forge_3d/openscad_export.py`
- `vaultmind_forge/forge_3d/openscad_import.py`
- `vaultmind_forge/forge_3d/openscad_csg.py`
- `rust_core/src/python_bindings/mod.rs`
- `rust_core/src/python_bindings/engine_export.rs`
- `rust_core/src/csg/robust.rs`
- `rust_core/src/export/engine_formats.rs`
- `pyproject.toml`

## Minimal fixture families

Prefer small deterministic fixtures:

1. Unit cube and known dimensions.
2. Open cylinder and capped cylinder.
3. Sphere with fixed segment/detail counts.
4. Two overlapping boxes for difference and union.
5. Nested and coplanar boxes for CSG edge cases.
6. Open triangle and tetrahedron for manifold behavior.
7. Known OBJ with vertices, normals, and faces.
8. Minimal complete glTF mesh with one triangle.
9. Deterministic template pair with fixed seed.
10. Non-uniform tuple dimensions.

## Evidence language

Use precise wording:

- `Confirmed by static inspection` - the code directly demonstrates the behavior.
- `Confirmed by executed test` - include command, result, and environment.
- `Implemented but unverified` - source exists but no current runtime evidence.
- `Approximate` - behavior intentionally differs from the ideal contract.
- `Unsupported` - public API should reject or omit the capability.
- `Broken` - a defined path is expected to work but cannot satisfy its contract.
