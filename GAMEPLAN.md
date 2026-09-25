# LPG Gameplan

**Project:** VaultMind Forge / Linux Procedural Generation  
**Workspace:** `C:\Users\Administrator\Desktop\Projects\LPG`  
**Plan version:** 0.1  
**Last updated:** 2026-09-24

## Mission

Grow LPG into a secure, modular, WSL/Linux-first AI creation platform that supports local and cloud providers, native Rust/PyO3 geometry, image/video/audio/3D conversion, optional Blender and game-engine workflows, and task-specific AI assistance without hardwiring one provider, interface, operating system, or engine.

AL1 Environment is a separate package/protocol layer. LPG may consume versioned AL1 profiles and artifacts, but LPG remains authoritative for creative runtime behavior and asset semantics.

## Working agreements

- Work one bounded subsystem or “arm” at a time.
- Define the contract before implementation.
- Build the smallest complete vertical path for that arm.
- Run a smoke path, then focused validation.
- Wire the arm into LPG and AL1 only after its local contract is acceptable.
- Do not call a print-only script a test.
- Do not treat historical reports, generated files, local binaries, or stale wheels as current evidence.
- Preserve all existing modified and untracked work.
- Never reset, clean, stash, restore, or delete during classification.
- Never open `.env`, private keys, tokens, or credential files.
- Ask before dependency installation, long-lived processes, Docker/native execution, external writes, commits, pushes, pull requests, or destructive cleanup.
- A user may choose among approved providers, interfaces, runtimes, and engines. No provider is architecturally privileged.

## Current baseline

Verified on 2026-09-24:

- Local Git root: this directory.
- Branch: `master`.
- Remote: `https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration.git`.
- Local `HEAD` and `origin/master`: `84b1ec82373bd068138883f94bd5abec5e096414`.
- No LPG staging or commit was performed.
- Existing tracked modifications: 4.
- Current non-ignored untracked entries: 91.
- Current untracked generated metadata under `outputs/`: 49 files.
- The parent `C:\Users\Administrator\Projects` Git root is accidental and must not be used.
- AL1 Environment has its own initialized Git repository on `main` with no commit yet.

### Current uncommitted classification

- Four modified tracked files form a coupled geometry/PyO3 change set.
- Eight `vaultmind_forge/forge_3d/` files are current source candidates.
- Four untracked Rust binding modules are required by the modified binding registry.
- `mod.rs.backup` is historical backup material.
- Two `openscad_modules/` files are source/prototype material.
- Seven examples are demonstrations, not authoritative tests.
- Three root test-like scripts are manual smoke probes.
- Forty-nine files under `outputs/` are generated metadata/examples and are not source.
- Three root reports and several untracked OpenSCAD/geometry docs are historical/design material.
- `write_bindings.py` is a generator with authority/output conflicts; preserve it but do not run it yet.
- `.opencode/` and `AGENTS.md` are local governance/tooling.
- `.continue/mcpServers/new-mcp-server.yaml` is an incomplete placeholder.

## Status legend

- `[ ]` Not started
- `[~]` In progress or partially evidenced
- `[x]` Complete for the stated scope
- `[!]` Blocked or requires a decision
- `[E]` Evidence exists but is not current
- `[S]` Smoke path only
- `[V]` Validated against the stated contract

## Phase 0 — Preserve and classify

- [x] Verify LPG Git root, branch, remote, and commit alignment.
- [x] Preserve four modified tracked files.
- [x] Complete initial tracked-overlay review.
- [x] Complete initial untracked-work classification.
- [x] Complete architecture, correctness, inventory, WSL, provider, Blender, and conversion research.
- [x] Create LPG review and geometry-contract skills.
- [x] Configure Context7 and read-only GitHub MCP for the LPG workspace.
- [x] Create this root gameplan.
- [ ] Create a reviewed evidence index without copying reports wholesale.
- [ ] Define the first committed change unit after user approval.
- [ ] Decide which generated outputs, if any, become fixtures or examples.
- [ ] Decide whether an initial local commit is appropriate and what it contains.

## Phase 1 — Canonical package and runtime contracts

Goal: establish one authoritative core with multiple clients.

Recommended shape:

```text
Python domain/core
  +-- CLI client
  +-- FastAPI client
  +-- official web/desktop client
  +-- NodeForge/Blender/external clients
  +-- Rust/PyO3 native capabilities
```

- [ ] Confirm Python as the orchestration/domain authority.
- [ ] Confirm Rust/PyO3 as the trusted native capability boundary.
- [ ] Define the role of the Node API; default to non-authoritative until proven.
- [ ] Define the NodeForge boundary and frontend ownership.
- [ ] Select canonical workflow, execution, output, and lineage roots.
- [ ] Define versioned capability and asset-envelope schemas.
- [ ] Define client contract versioning.
- [ ] Define provider-neutral request/response/error contracts.
- [ ] Define service/task/profile contracts shared with AL1.

## Phase 2 — Clean Python/package startup

Goal: remove import and installation ambiguity before feature expansion.

- [x] Remove the nonexistent telemetry call while retaining local analytics.
- [x] Make the missing optional node module non-fatal without advertising absent nodes.
- [x] Resolve `execution_order` versus `get_execution_order()` mismatch.
- [x] Correct the CLI schema path to the existing package schema.
- [x] Correct `pyproject.toml` package discovery for `vaultmind_forge` and `backend`.
- [x] Define `pyproject.toml` as the installable dependency contract with `api`, `ai`, `native-build`, `dev`, and `procedural` extras.
- [x] Mark requirements files as pinned full-environment locks rather than package dependency authority.
- [ ] Reconcile Docker dependency installation with the selected profile contract.
- [ ] Align Python/Rust/native version metadata.
- [x] Remove production imports that depend on `rust_core/target/wheels`.
- [x] Define clean source, wheel, sdist, and native-extension behavior.
- [x] Run authorized narrow source smoke for TOML, package import, registry, CLI, and schema loading.
- [x] Build and isolated-import the current wheel without dependency installation.
- [x] Import the FastAPI application with the current SlowAPI middleware/handler contract.
- [ ] Add characterization tests before changing startup behavior.

### Phase 2 exit criteria

- Clean Python package import does not require local generated wheels.
- Native feature failure is explicit and capability-scoped.
- Registry and FastAPI application can be imported in a clean environment.
- CLI entry points are documented and callable.
- Dependency sources have one declared authority.

## Arm 1 — Current implementation pass

**Date:** 2026-09-24  
**Status:** `[V]` package/import contract validated; native operation and deployment follow-ups remain

### Changes in this pass

- `backend/api.py`
  - Removed the malformed/undefined telemetry call.
  - Retained local analytics as the supported reporting path.
  - Replaced nonexistent `engine.execution_order` access with `get_execution_order()`.
  - Updated SlowAPI integration to the current module-level handler and ASGI middleware contract.
  - FastAPI import smoke passed with 20 routes.
- `backend/core/registry.py`
  - Made the absent optional `additional_nodes` module non-fatal.
  - Preserved strict failure for unrelated nested import errors.
- `backend/core/engine.py`
  - Stored the active workflow when `execute_workflow()` runs so `get_execution_order()` returns the actual order.
- `pyproject.toml`
  - Corrected package discovery to the repository root.
  - Included `vaultmind_forge*` and `backend*` namespace packages.
  - Added `api`, `ai`, `native-build`, `dev`, and `procedural` dependency profiles.
- `requirements.txt` and `requirements-dev.txt`
  - Clarified that they are pinned environment locks, not package-extra authority.
- `README.md`
  - Updated the quick-start dependency examples to use installable profiles.
- `vaultmind_forge/forge_3d/_native.py`
  - Added an explicit lazy native-extension loader.
  - Removed implicit `rust_core/target/wheels` path injection.
  - Added the explicit `VAULTMIND_NATIVE_EXTENSION_PATH` development override.
- `vaultmind_forge/forge_3d/primitives_all.py`
  - Converted native access to a lazy proxy.
- `vaultmind_forge/forge_3d/mesh.py`
  - Routed native export access through the lazy loader.
- `vaultmind_forge/forge_3d/openscad_import.py`
  - Removed direct generated-wheel path insertion.

### Evidence and limits

- `git diff --check` completed without whitespace errors; Git reported existing CRLF normalization warnings for touched files.
- Authorized narrow smoke checks passed:
  - `pyproject.toml` parsed successfully.
  - `vaultmind_forge.forge_3d` imported without loading a native extension.
  - `create_default_registry()` constructed successfully with 15 available executors.
  - The CLI module imported with 7 registered commands.
  - `vaultmind_forge/config/schemas/job.schema.json` parsed successfully.
- Clean distribution check passed:
  - Built `vaultmind_forge-0.1.0-py3-none-any.whl` into the approved OpenCode temp directory.
  - Wheel contained `vaultmind_forge/__init__.py`, `vaultmind_forge/forge_3d/_native.py`, and `backend/api.py`.
  - Installed with `--no-deps` into an isolated target.
  - Imported `vaultmind_forge.forge_3d` successfully from outside the source tree.
- `python -m vaultmind_forge --help` passed from source and from an isolated installed wheel.
- The package build created ignored local `build/`, `dist/`, and `vaultmind_forge.egg-info/` artifacts; they were preserved and not staged.
- The missing additional-node implementations remain unimplemented and are not advertised by the registry when absent.
- Native extension operation, Docker, and service startup remain intentionally unrun.
- The next active arm is native geometry correctness; residual characterization tests, Docker profile work, and version alignment remain tracked in later phases.

### Next Arm 1 step

Review and correct the remaining startup/package contract before moving to geometry:

- align Docker dependency installation and version metadata;
- define and add focused characterization checks;
- verify clean import and registry construction only after authorization.

## Ubuntu base-function gate

**Date:** 2026-09-24  
**Status:** `[V]` WSL2/Python 3.12/build123d/native wheel/CLI smoke passed

- Ubuntu WSL2 is the first Linux runtime target.
- Ubuntu system `python3` is 3.14, which is too new for the current PyO3 0.22 toolchain.
- Ubuntu provides `/usr/bin/python3.12`; LPG uses `.venv-linux` with Python 3.12.13.
- build123d 0.13.0 and OCP installed successfully in `.venv-linux`.
- Maturin built the Linux native wheel:
  `vaultmind_forge_core-0.1.0-cp312-cp312-linux_x86_64.whl`.
- The Linux native wheel installed and imported successfully.
- Ubuntu base smoke passed:
  - `forge doctor`
  - `forge cad-capabilities`
  - `forge cad-execute`
  - Native cylinder creation
  - STEP output: 15,392 bytes
  - STL output: 684 bytes
- Ubuntu Cargo tests passed with explicit `PYO3_PYTHON=.venv-linux/bin/python`: 35 passed.
- The base program is now runnable and testable in Ubuntu WSL2.

## LPG-L1 scanner and monitor foundation

**Date:** 2026-09-25
**Status:** `[V]` read-only monitor/debug/repair foundation validated; manifest authority remains next

- `al1scan/` is a dedicated Rust scanner project and is tracked.
- Root launchers are available as `al1scan.ps1` and `al1scan.sh`.
- Scanner supports full-root, scoped subtree, and bounded-depth scans.
- Scanner emits machine-readable tree reports and summary reports.
- Resource limits are available for entries, bytes, depth, and duration.
- Partial scans emit structured warnings and `complete: false` rather than synthesizing deletions.
- Symlinks, Windows reparse points, external directory targets, secret-like paths, and opaque generated roots are handled explicitly.
- Repair actions remain additive-only, confirmation-gated, and non-overwriting.
- Report/repair writes verify that their parent remains within the scan root.
- Windows and WSL/Linux launcher smoke passed.
- Rust validation passed: 8 tests, Clippy with warnings denied, formatting check, and release build.
- The scanner is currently a monitor/readout/diff/repair foundation, not yet the canonical LPG-L1 manifest or package lifecycle authority.
- The initial `LPGL1/` profile README, draft profile, and amendable TODO are tracked.
- `.venv-linux/`, `.al1-incoming/`, `.al1scan_reports/`, `.opencode/`, and `.continue/` are local/generated state and are not program source.

### Next LPG-L1 scanner step

Implement the canonical recursive component manifest and location authority:

- define machine IDs and parent/child relationships;
- define alias and path bindings;
- define observed/planned/missing/conflict states;
- define schema dispatch and ownership;
- connect scanner observations to generated LPG-L1 records;
- preserve partial scan results without promoting them to approved state;
- add focused resolver and manifest tests before package/setup lifecycle work.

## Arm 2 — Native geometry current pass

**Date:** 2026-09-24  
**Status:** `[V]` native geometry core validated; OpenSCAD external render remains environment-blocked

### Changes in this pass

- `rust_core/src/geometry/primitives.rs`
  - Added finite/positive parameter and minimum tessellation validation.
  - Added cylinder cap centers and corrected side winding.
  - Corrected cone and torus winding.
  - Added signed-volume and invalid-parameter tests.
- `rust_core/src/geometry/extended_primitives.rs`
  - Added capsule parameter validation.
  - Corrected capsule winding.
  - Added a signed-volume and validation test.
- `rust_core/src/mesh/obj.rs`
  - Added validated OBJ parsing for vertices, UVs, normals, polygon triangulation, and positive/negative indices.
  - Added malformed-input and attribute tests.
- `rust_core/src/mesh/validation.rs`
  - Reports unchecked self-intersection detection as unknown.
  - Corrected normalized-edge manifold counting.
- `rust_core/src/mesh/advanced_optimizer.rs` and `python_bindings/optimization.rs`
  - QEM now fails explicitly instead of returning an unchanged mesh as success.
- `rust_core/src/csg/robust.rs`
  - Replaced the invalid ray-parity heuristic with Parry solid containment.
  - Added segment/triangle boundary detection.
  - Spanning CSG cases now return explicit errors; disjoint union remains supported.
- `rust_core/src/mesh/mod.rs` and `python_bindings/mod.rs`
  - Exposed the OBJ loader through the Rust mesh module and PyO3 API.
- `rust_core/src/export/mod.rs` and `engine_formats.rs`
  - OBJ faces now reference UVs and normals only when those attributes exist.
  - FBX/glTF requests now fail explicitly instead of writing placeholder files.
  - Unity/Unreal/Godot engine exports accept only validated OBJ output.
- `rust_core/pyproject.toml`
  - Added the explicit Maturin native package/build contract.

### Evidence and limits

- Cargo first attempted offline testing and reported the missing cached `approx v0.5.1` dependency.
- After explicit approval, Cargo fetched the repository's declared Rust dependencies into the local cache.
- With the existing `.venv312` supplied to PyO3, focused tests passed:
  - `cargo test --manifest-path rust_core/Cargo.toml validation::`: 4 passed.
  - `cargo test --manifest-path rust_core/Cargo.toml advanced_optimizer::`: 4 passed.
  - `cargo test --manifest-path rust_core/Cargo.toml geometry::`: 13 passed.
  - `cargo test --manifest-path rust_core/Cargo.toml obj::`: 3 passed.
  - `cargo test --manifest-path rust_core/Cargo.toml export::`: 4 passed.
  - `cargo test --manifest-path rust_core/Cargo.toml csg::`: 4 passed.
  - `cargo test --manifest-path rust_core/Cargo.toml export::`: 5 passed.
- The native Maturin package built as `vaultmind_forge_core-0.1.0` and imported successfully in an isolated target.
- Python ABI probe passed for primitives, OBJ loading, unknown self-intersection status, CSG refusal, and QEM refusal.
- `rust_core/src/mesh/mod.rs` fixed duplicate-vertex cleanup to remap triangle indices before compacting vertices.
- Full `cargo test --manifest-path rust_core/Cargo.toml` passed: 35 tests, 0 failures; doc-tests also passed.
- Final Maturin build from the current source produced `vaultmind_forge_core-0.1.0`; isolated Python import passed.
- Final Python ABI probe passed primitives, OBJ export/import, Godot OBJ, Unity FBX refusal, unknown self-intersection status, CSG refusal, and QEM refusal.
- OpenSCAD executable discovery and unsupported-format refusal smoke checks passed, but an actual OpenSCAD render round trip is blocked because OpenSCAD is not installed in this environment.
- Existing unrelated compiler warnings remain; no new validation-helper warning remains.
- Self-intersection validation now reports `None`/unknown until a real check is implemented.
- QEM now returns an explicit unsupported error instead of an unchanged mesh.
- Signed-volume tests now have current passing evidence for the tested primitives.

### Next Arm 2 step

The native geometry core is validated. Install/detect OpenSCAD in a WSL/Linux profile when available for the external render round trip; otherwise carry the explicit unavailable/unsupported contract into the installer arm and proceed to asset conversion.

## Phase 3 — Native geometry/PyO3 arm

Goal: make native geometry correctly packaged and mathematically honest.

- [x] Review the coupled `forge_3d` and `python_bindings` source set atomically.
- [x] Correct cone, torus, and capsule winding/normals.
- [x] Decide capped versus uncapped cylinder semantics and implement the chosen contract.
- [x] Reject invalid dimensions, segment counts, ring counts, and non-finite inputs.
- [~] Correct UV generation and OBJ texture references.
- [x] Implement real clipping or explicitly disable incomplete CSG operations.
- [x] Implement/register a real OBJ loader or use a validated Python loader.
- [x] Reject unsupported FBX/glTF requests until valid output exists.
- [x] Correct self-intersection validation and QEM false-success behavior.
- [~] Add per-primitive bounds, topology, winding, manifoldness, and determinism tests.
- [x] Add standards-aware export parsing tests.
- [x] Package native geometry with an explicit PyO3/maturin or equivalent build contract.
- [ ] Define trusted in-process versus isolated-worker operations.

### Phase 3 exit criteria

- A clean environment can install and use the documented native geometry profile.
- Every supported primitive has a valid topology contract.
- Unsupported operations fail honestly.
- Export files are genuinely parseable.
- No stale local wheel can silently satisfy the API.

## Phase 4 — AL1 package and task layer

Goal: provide a package-manager/library foundation for composable services without copying AL1 into LPG.

- [ ] Define the `al1-environment` package identity and versioning.
- [ ] Define a machine-readable AL1 profile bundle.
- [ ] Define `init`, `install`, `profile`, `doctor`, `task`, and `export` interfaces.
- [ ] Implement a service registry with capability declarations.
- [ ] Implement task-scoped build/provision/run/teardown.
- [ ] Implement one event and lineage path.
- [ ] Implement default monitoring and security groups.
- [ ] Keep creation groups open, capability-driven, and user-selected.
- [ ] Add debug, compile, validate, convert, image, video, music, game-module, and observation task profiles.
- [ ] Add LPG profile consumption without importing AL1 runtime internals.
- [ ] Preserve LPG authority over geometry and creative semantics.

## Phase 5 — AI provider layer

Goal: local/cloud neutrality with explicit placement, capability, privacy, and provenance.

- [ ] Define canonical request, response, capability, error, and provenance schemas.
- [ ] Implement capability probing rather than assuming OpenAI compatibility.
- [ ] Add local adapters for supported runtimes.
- [ ] Add NVIDIA, OpenAI, and Hugging Face adapters.
- [ ] Add explicit local-only, local-first, managed, and experimental policies.
- [ ] Prohibit silent local-to-cloud fallback.
- [ ] Add secret references and redacted logs.
- [ ] Add model artifact revision, digest, license, and deployment metadata.
- [ ] Create measured 6–32 GB VRAM profiles.
- [ ] Add model catalog and hardware-fit diagnostics.
- [ ] Keep GitHub MCP in the agent/tool plane, separate from LPG product runtime.

## Phase 6 — Asset conversion and workers

Goal: make conversion a first-class, loss-aware, secure subsystem.

- [x] Define a common asset envelope and typed intermediate representations.
- [x] Define conversion statuses: exact, reinterpreted, approximated, lossy, dropped, unsupported, failed, unchecked.
- [~] Implement geometry conversion adapters.
- [~] Implement image conversion adapters.
- [ ] Implement video/audio conversion through isolated FFmpeg/media workers.
- [ ] Implement Blender external worker protocol.
- [ ] Implement OpenSCAD external worker protocol.
- [x] Implement build123d B-rep adapter and capability profile.
- [~] Implement FreeCADCmd headless worker and capability profile.
- [ ] Implement optional Godot/engine adapters.
- [ ] Add stream, metadata, color-space, transform, and loss reports.
- [ ] Add archive, path, symlink, resource, and parser-security controls.
- [~] Add independent output validation and round-trip tests.

## Arm 3 — Asset envelope and conversion honesty

**Date:** 2026-09-24  
**Status:** `[V]` envelope, OBJ adapter, and image adapter smoke validated; broader formats pending

### Changes in this pass

- `vaultmind_forge/forge_converter/contracts.py`
  - Added the canonical `ConversionEnvelope`.
  - Added explicit `ConversionLossStatus` values: exact, reinterpreted, approximated, lossy, dropped, unsupported, failed, unchecked.
  - Added JSON-compatible serialization and provenance fields.
- `vaultmind_forge/forge_converter/converter.py`
  - Added envelope conversion and loss status to results.
  - Placeholder model, texture, and animation paths now fail explicitly instead of copying files and reporting success.
  - Missing sources report `failed`; unsupported adapters report `unsupported`.
  - Added a native OBJ-to-OBJ adapter for Godot/Unity/Unreal/generic targets.
  - Added a Pillow image adapter for PNG, JPEG, WebP, TIFF, and BMP with explicit loss metadata.
  - Added `target_format` selection for image outputs through conversion options.
- `vaultmind_forge/forge_converter/validation.py`
  - Added independent OBJ structural validation and Pillow image validation.
  - Integrated validator evidence into conversion results.
- `vaultmind_forge/forge_converter/__init__.py`
  - Exported contract, options, and validation APIs.
- `forge_intake` now exposes the canonical envelope, preserves legacy status compatibility, validates OBJ independently, triangulates polygon faces, reports OBJ loss as `reinterpreted`, and rejects malformed image/OBJ input.
- Placeholder glTF/FBX/COLLADA/USD/STL/PLY/scene intake paths now return explicit `unsupported` results.
- Package-qualified and legacy top-level intake imports remain supported.

### Evidence and limits

- Asset-contract smoke passed for contract import, JSON serialization, unsupported outcomes, failed outcomes, and absence of copied output.
- OBJ adapter smoke passed: native OBJ parse/export to Godot OBJ reported `reinterpreted` and produced a file.
- Image adapter smoke passed: RGB PNG → JPEG reported `lossy` and produced a file.
- Independent validators passed: malformed OBJ rejected; valid image accepted.
- Persistent contract tests added in `vaultmind_forge/tests/test_asset_contracts.py`; targeted result: 4 passed.
- Final Python package wheel rebuilt and isolated import passed with the new contract exports.
- Unvalidated image output format correctly reported `unsupported` without output.
- `forge_intake` OBJ and unsupported-format smoke passed through the canonical envelope, including legacy top-level import compatibility.
- Intake placeholder formats now return `unsupported` rather than success.
- Media, Blender, archive, and broader 3D adapters remain unimplemented.

### Next Arm 3 step

Add persistent round-trip tests for the independent validators and migrate the remaining `forge_intake` parsers from placeholder metadata to validated adapter results.

## Phase 7 — Blender and optional engine arms

Each arm follows the same completion policy:

```text
contract -> build/provision -> smoke -> validate -> wire -> document -> advance
```

### build123d B-rep arm

- [x] Make build123d the default Python B-rep dependency.
- [x] Add build123d capability detection and version capture.
- [x] Add isolated structured-plan Python CAD worker contract.
- [ ] Add isolated arbitrary-source execution contract.
- [x] Add trusted fixed STEP/STL generation and independent validation.
- [ ] Add build123d bake-off against CadQuery/OCCT alternatives.

### FreeCAD arm

- [x] Mark FreeCAD as the recommended secondary GUI/headless CAD application.
- [x] Add FreeCAD/FreeCADCmd detection without auto-installing it.
- [ ] Define FreeCAD document/STEP/IGES job contract.
- [ ] Add isolated FreeCAD worker and resource limits.
- [ ] Add independent STEP/IGES/FCStd output validation.

### Blender arm

- [ ] Research and pin the supported Blender LTS version.
- [ ] Define JSON job/result contract.
- [ ] Build isolated controller and per-job directories.
- [ ] Implement safe background scene construction/import.
- [ ] Implement render and export operations.
- [ ] Implement timeouts, cancellation, process-group cleanup, and staged publication.
- [ ] Validate `.blend`, GLB/glTF, and render outputs independently.
- [ ] Add Blender capability profile to AL1.
- [ ] Connect Blender to LPG asset tasks.
- [ ] Mark Blender experimental, smoke-passed, validated, or complete.

### OpenSCAD arm

- [ ] Define supported SCAD subset and external tool contract.
- [ ] Correct primitive field mappings.
- [ ] Implement real OBJ handoff.
- [ ] Add export/import/render round-trip validation.
- [ ] Add resource and subprocess safety controls.
- [ ] Connect OpenSCAD to LPG/AL1 task profiles.

### Game-engine arms

- [ ] Define valid interchange targets and feature-loss policy.
- [ ] Implement validated glTF/GLB/OBJ/STL paths.
- [ ] Keep FBX unsupported until a real implementation exists.
- [ ] Add Godot/Unity/Unreal adapters only as external project/export workers.
- [ ] Add target-project validation and packaging.

## Arm 4 — Default build123d B-rep runtime

**Date:** 2026-09-24  
**Status:** `[V]` default dependency, trusted fixed adapter, GUI-safe envelope, AI plan layer, and isolated structured-plan worker validated; arbitrary source worker pending

- build123d is now a base `pyproject.toml` dependency.
- build123d `0.13.0` is installed in LPG's `.venv312` program environment.
- `cadquery-ocp-novtk 8.0.1.0.0` is installed as its geometry runtime.
- `forge_converter/build123d_adapter.py` exposes capability detection, fixed trusted box → STEP/STL generation, and a GUI/API-safe `ConversionEnvelope`.
- `forge_converter/build123d_ai.py` exposes an allowlisted AI operation manifest, structured plan parser, boolean combination support, path-safe naming, and GUI/API-safe plan execution.
- `forge_converter/build123d_worker.py` runs structured plans in a child process with JSON job/result files, timeout handling, and isolated output directories.
- `forge_cli.py` exposes `cad-capabilities` and `cad-execute` JSON interaction points for shell, AI, and future GUI clients.
- Arbitrary Python remains explicitly disabled in the AI tool manifest; it is reserved for the future source-worker boundary.
- Arbitrary user build123d source remains unsupported in the current worker.
- `forge_converter/cad_profiles.py` exposes wizard-readable CAD profile metadata with build123d as default and FreeCAD/OpenSCAD/Blender as optional secondary profiles.
- FreeCAD remains the recommended secondary GUI/headless application for later wizard provisioning.

Validation:

- build123d capability probe passed.
- STEP output: 15,418 bytes for a test box.
- STL output: 684 bytes for a test box.
- `pip check` reported no broken requirements.
- Targeted asset contract tests: 12 passed.
- GUI-safe build123d envelope test passed for a fixed box with STEP/STL output.
- Structured AI plan smoke passed for a box-minus-cylinder boolean plan.
- CAD profile registry test passed: build123d default; FreeCAD/OpenSCAD/Blender optional.
- Isolated structured-plan worker test passed with STEP/STL output.
- FreeCAD detection smoke passed without launching or installing FreeCAD.
- CLI `cad-capabilities` and isolated `cad-execute` smoke passed with STEP/STL output.
- Installed `.venv312\Scripts\forge.exe --help` and `forge cad-capabilities` passed after fixing package-qualified imports.
- `forge doctor` reports Python, build123d, FreeCAD, native extension, Cargo, OpenSCAD, Blender, FFmpeg, and Docker capability state without launching tools or reading secrets.

## Phase 8 — WSL/Linux package manager and wizard

Goal: quick guided setup that coordinates existing package tools and remains explicit.

- [ ] Choose initial supported distributions and architectures.
- [ ] Define native, user-service, hybrid, and Docker profiles.
- [ ] Detect WSL mode, systemd, package health, Docker endpoint, GPU, VRAM, disk, and tools.
- [ ] Produce dry-run plans before mutation.
- [ ] Make install resumable and idempotent.
- [ ] Use operation journals and compensating rollback.
- [ ] Never auto-start Docker or install GPU drivers.
- [ ] Add clean TTY, JSON, and NDJSON output.
- [ ] Add health/readiness checks.
- [ ] Add secure credential/reference setup.
- [ ] Add beginner-friendly explanations without hiding technical choices.

## Phase 9 — Official UX

Goal: one coherent LPG-owned setup and creation experience.

- [ ] Choose the initial frontend approach after API contracts stabilize.
- [ ] Provide setup wizard, provider selection, VRAM profile selection, task dashboard, asset library, and diagnostics.
- [ ] Keep CLI and FastAPI first-class alternatives.
- [ ] Keep NodeForge separate unless explicitly promoted.
- [ ] Add AI-assisted diagnostics with approval boundaries.
- [ ] Add tutorials for Linux/WSL beginners and advanced users.

## Phase 10 — Security floor and content protection

Cross-cutting from the first implementation phase.

- [ ] Define content classifications.
- [ ] Define capability grants and deny-by-default resolution.
- [ ] Enforce mandatory baseline in every profile.
- [ ] Add scoped network and egress policy.
- [ ] Add remote-access authentication and origin protections.
- [ ] Add prompt/tool-output injection defenses.
- [ ] Add sandboxing for untrusted assets and media.
- [ ] Add export approval, watermarking, and provenance options.
- [ ] Add key references, rotation, and revocation.
- [ ] Add redacted tamper-evident audit records.
- [ ] Add time-limited break-glass escalation.
- [ ] Add adversarial tests for unauthorized access and data exfiltration.

## Phase 11 — Verification, CI, and release

- [ ] Convert smoke scripts into assertion-based tests or clearly label them manual.
- [ ] Add focused tests before each behavior change.
- [ ] Establish documented Python, Rust, C++, Node, package, Docker, and security checks.
- [ ] Add CI only for reproducible checks.
- [ ] Add clean-checkout and clean-environment tests.
- [ ] Reconcile README, architecture maps, reports, and current source.
- [ ] Archive historical reports without treating them as current evidence.
- [ ] Define initial commit, release, and remote synchronization policy.

## Cross-cutting acceptance rules

Every completed arm must state:

- What was implemented.
- Which files changed.
- Which contract it satisfies.
- Which smoke command was run.
- Which validation commands were run.
- Exact outputs and limitations.
- What remains unsupported.
- How to roll back or disable it.
- Which AL1 profile/service/task represents it.
- Which LPG interface exposes it.

## Evidence register

The following agent research/read-only passes are retained as working evidence:

- LPG architecture and inventory review.
- LPG correctness and regression review.
- LPG tracked-overlay and untracked-work classification.
- WSL/Linux installer and Docker research.
- Provider-neutral AI, model, VRAM, and provenance research.
- Blender integration and background-worker research.
- PyO3/Rust engine, geometry, and media-conversion research.
- AL1 protocol inventory, architecture, and consistency reviews.

These reports are inputs, not automatic current verification. Future changes should cite source files, current commands, and new evidence.

## Session handoff

### Current handoff — 2026-09-25

```text
Last active arm: LPG-L1 scanner and monitor foundation
Status: [V] scanner/monitor foundation validated; canonical manifest/location authority pending
Files changed: LPGL1/README.md, LPGL1/L1/profile.jsonc, LPGL1/L1/TODO.md; al1scan/Cargo.toml, Cargo.lock, src/main.rs, src/scan.rs; al1scan.ps1; al1scan.sh; native QEM guard and corrected binding smoke
Checks run: al1scan cargo test (8 passed); cargo clippy --all-targets -- -D warnings; cargo fmt --check; release build; Windows launcher summary/dump smoke; WSL/Linux launcher smoke; resource-limit partial-scan smoke; git diff --check
Evidence: GAMEPLAN.md LPG-L1 scanner section; commit 9e98520 pushed to origin/master
Open questions: canonical recursive manifest schema; location resolver; dependency-impact graph; tier-closure validation; known-good/rollback journal; package/setup lifecycle integration
Known limitations: scanner tier/status inference is heuristic; no manifest authority yet; repairs are additive-only; tier closure and dependency expansion are planned; generated outputs and local environments remain untracked
Next smallest step: implement the canonical LPG-L1 recursive component manifest and location authority, then connect scanner observations without promoting partial scans
```

At the end of each future work session, update the same fields with current evidence.

## Decisions to revisit at gates

- Primary LPG interface and Node API role.
- Official frontend ownership and NodeForge relationship.
- Canonical execution, output, and lineage roots.
- Native Rust versus legacy C++ ownership.
- AL1 package language/distribution form.
- Optional Blender version and packaging route.
- Build123d versus CadQuery as the first Python B-rep adapter.
- FreeCAD packaging route and FreeCADCmd worker contract.
- Model catalog and VRAM admission policy.
- Initial commit contents and generated-fixture policy.

## Immediate next action

The scanner/monitor foundation is validated and the native QEM smoke fix is tracked.

The next active step is:

**Canonical LPG-L1 manifest and location authority.**

Define the recursive component identity model, machine IDs, aliases, path bindings, ownership, schema dispatch, and planned/observed/missing/conflict states. Connect scanner observations without promoting partial scans to approved state.
