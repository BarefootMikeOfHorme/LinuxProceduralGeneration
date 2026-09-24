---
name: LPG Geometry Contracts
description: Review and change LPG's Python, Rust, PyO3, mesh, CSG, export, import, template, and OpenSCAD workflows against concrete geometry and packaging contracts.
---

# LPG Geometry Contracts

## Purpose

Use this skill whenever work touches `vaultmind_forge/forge_3d/`, `rust_core/`, native validators, geometry exports/imports, procedural mesh generation, game templates, smart objects, or OpenSCAD integration.

The goal is not to prove that code runs. The goal is to establish that the public contract is real, geometrically correct, reproducible from a clean environment, and honestly represented.

## Safety and evidence boundaries

1. Read `AGENTS.md` and preserve all existing modified and untracked work.
2. Never use `rust_core/target/`, a local wheel, or another generated binary as proof that a clean build works.
3. Do not open `.env`, install dependencies, invoke OpenSCAD, start services, or run native/build tooling during onboarding without explicit authorization.
4. Run only verification commands documented by the repository. If no command exists, propose the missing contract rather than inventing a passing check.
5. Do not overwrite user work to obtain a green result.
6. Distinguish committed source, current untracked source, historical reports, and unverified behavior.
7. A file with the requested extension is not evidence that its contents are a valid format.

## Canonical geometry flow

Use this as the conceptual path, then verify the actual implementation:

```text
Python API
  -> primitive or imported mesh
  -> optional validation and optimization
  -> optional CSG
  -> Python/Rust representation boundary
  -> export or round trip
```

At every arrow, record the schema, ownership, failure behavior, and whether the step is implemented, approximate, optional, or unsupported.

## Contract checklist

Use `references/contract-matrix.md` for detailed checks.

### 1. Packaging and import

- A clean checkout can import supported pure-Python functionality without a repository-local prebuilt wheel.
- Optional native features fail clearly and only when invoked, or packaging builds and declares the extension correctly.
- The top-level `vaultmind_forge` package is included by the distribution configuration.
- No production import depends on manually inserting `target/wheels` or another generated directory into `sys.path`.
- Wheel tags, feature flags, and supported Python/Rust versions agree.
- Error messages identify the missing capability, expected build, and fallback behavior.

### 2. Python/Rust ABI

- Every symbol called from Python is registered by the active module.
- Argument names, arity, optional arguments, return types, and raised exceptions match.
- Module names and wheel import names match.
- Stale wheels cannot silently shadow the current Rust source.
- The public Python API exposes capabilities honestly; it must not synthesize successful metrics or placeholders for missing native functions.

### 3. Primitive geometry

For every primitive, verify against its documented contract:

- Constructor fields match examples and exporters.
- Vertex and face counts are deterministic for fixed parameters.
- Bounds, dimensions, axes, and origin are correct.
- Triangle winding and normals are consistent.
- Promised caps or closed surfaces are actually closed.
- Default dimensions do not create zero-area or NaN geometry.
- Segment and detail settings affect topology predictably.
- Coordinate conventions agree across Python, Rust, OpenSCAD, and engine exporters.

### 4. CSG

- Intersecting triangles are clipped rather than retained whole.
- Union, difference, and intersection remove or introduce faces according to the classified operation.
- Coplanar and near-coplanar cases have defined behavior.
- Internal faces do not survive merely because the source triangle is classified as spanning.
- Results preserve expected bounds and have plausible volume, orientation, and manifoldness.
- Empty, single-triangle, open-mesh, nested-mesh, and touching-mesh inputs have defined outcomes.

### 5. Mesh validation and optimization

- Validation distinguishes topology, normals, bounds, NaN/Inf values, duplicate faces, boundary edges, and manifoldness.
- Optimization reports whether it changed vertices, triangles, error, or nothing.
- A no-op or approximation is never reported as successful optimization.
- Quality thresholds are explicit and testable.

### 6. Import and export

- Import functions and bindings referenced by Python actually exist.
- Parsers reject or clearly report malformed input.
- The requested extension, file signature, and file contents agree.
- OBJ/STL/PLY exports are parseable and preserve expected geometry.
- glTF exports include valid buffers, buffer views, accessors, indices, materials, and mesh data.
- FBX is either implemented as valid FBX or explicitly unsupported; it must never be OBJ with an FBX comment.
- Round-trip tests compare geometry, not only file existence.

### 7. OpenSCAD

- Exporter code reads actual primitive attributes.
- Every supported primitive has an intentional OpenSCAD representation.
- Importer calls registered bindings or uses a correctly implemented parser.
- Render commands use argument arrays, bounded timeouts, isolated temporary paths, and checked exit status.
- SCAD -> render -> mesh -> SCAD or export preserves expected geometry within stated tolerances.
- Documented limitations match current behavior.

### 8. Templates, smart objects, and game properties

- `count=1` follows the same seed, randomization, and keyword forwarding behavior as larger counts.
- Tuple-valued dimensions are scaled component-wise.
- Presets use fields accepted by their constructors.
- Game-engine property metadata matches the emitted asset and naming conventions.
- Factory and smart-object methods return the documented types.

### 9. Tests

Geometry tests must assert properties. A script that prints `[OK]`, creates a file, or reaches the end without assertions is a smoke demonstration, not a passing test.

Required test categories include:

- Pure geometry invariants for every primitive.
- Known bounds, topology, and watertightness.
- CSG regression meshes with known results.
- Import/export parser and signature checks.
- Engine-format validity and explicit unsupported behavior.
- OpenSCAD export for every supported primitive and bounded round-trip cases.
- Python/Rust binding conformance.
- Clean package build and clean-install import.
- Deterministic templates and game properties.
- Temporary output isolation; tests must not write generated files into the repository root.

## Review and change workflow

1. Map the public Python API, Rust API, PyO3 registrations, file formats, and callers.
2. Build a contract table with columns for promised behavior, implementation, evidence, status, and smallest correction.
3. Reproduce suspected defects with the smallest static or assertion-based check available.
4. Before changing behavior, add or identify the regression test that should fail for the right reason.
5. Make the smallest coherent correction without disturbing unrelated user work.
6. Verify in increasing cost order:
   - Static inspection or compilation check.
   - Focused Rust unit test.
   - Focused Python test against the active extension.
   - Clean wheel build and clean-environment import.
   - OpenSCAD or external-tool round trip.
   - Container build only after separate authorization.
7. Report exact commands and outputs. Historical reports are not substitutes.

## Severity guidance

- **P0:** security boundary, data loss, or widespread unusable output.
- **P1:** import/package failure, false success for core geometry, invalid engine assets, or mathematically incorrect core operations.
- **P2:** valid workflows fail for specific primitives or options, or determinism/contract mismatches.
- **P3:** documentation, ergonomics, or non-critical diagnostics.

## Definition of done

Geometry work is done only when:

- Public and internal contracts agree.
- Clean-environment behavior is understood.
- Core claims have assertion-based regression coverage.
- Output files are valid for their declared formats.
- Optional native behavior is explicit and safely detectable.
- No generated artifact or historical report is presented as current proof.
- Intentionally unsupported operations return clear errors rather than plausible fake files or scores.
