# LPG Folder Review Checklist

Use this checklist selectively. Record `not present`, `not applicable`, or `not reviewed` rather than silently skipping an area.

## 1. Repository root

- README claims versus current source.
- `AGENTS.md` and nested instructions.
- `pyproject.toml`, requirements, ignore rules, and environment template.
- Root scripts and test-like files.
- Build, distribution, archive, and generated artifacts.
- Remote, branch, dirty-worktree, and provenance concerns.

## 2. `vaultmind_forge/`

- Package public API and import side effects.
- `PROTOCOL.md` versus implemented stages.
- Core, loader, validator, and CLI ownership.
- Domain modules under `forge_*`.
- Duplicated abstractions and public/private boundaries.
- Optional native dependencies and fallback behavior.
- Tests, examples, and package inclusion.

## 3. `backend/`

- FastAPI route ownership and request/response schemas.
- `core/` DAG, type compatibility, registry, and executors.
- Persistence and migration behavior.
- Authentication, rate limiting, middleware, analytics, and error handling.
- Filesystem access and path containment.
- Legacy code and compatibility promises.

## 4. `rust_core/`

- Crate and feature definitions.
- Public Rust API and Python/PyO3 binding surface.
- Geometry, CSG, mesh, optimization, validation, templates, and export modules.
- Ownership between tracked baseline and current untracked files.
- Test coverage, feature combinations, and release packaging.

## 5. Native validators and C++

- `vaultmind_forge/native/rust/validator/`.
- `vaultmind_forge/native/cpp/validator/`.
- `backend/native/cpp/legacy/`.
- Canonical versus legacy ownership.
- Symbol parity, FFI safety, build systems, and fallback semantics.

## 6. `src/` Node API

- Server, handlers, Python bridge, and Node-side forge modules.
- API overlap with FastAPI.
- Job durability and process lifecycle.
- Port, host, CORS, authentication, and validation behavior.
- Dependency on Python, native libraries, frontend files, and models.
- Experimental versus authoritative status.

## 7. Tests and validation

- Assertion-based automated tests versus print-only smoke scripts.
- Unit, integration, ABI, packaging, API, Docker, and end-to-end coverage.
- Temporary-file isolation and deterministic fixtures.
- Documented commands and expected evidence.
- Native and platform matrices.

## 8. Scripts and examples

- Whether examples match current constructors and return types.
- Duplicate entry points and generated root artifacts.
- OpenSCAD, batch generation, game templates, and smart-object workflows.
- Safe subprocess, timeout, temporary-directory, and path handling.

## 9. Packaging and deployment

- Dockerfile build context and absent dependencies.
- Dependency truth across project metadata and requirements.
- Model and asset portability.
- API port, authentication, CORS, persistence, and health checks.
- Single-instance versus distributed assumptions.
- Reproducibility from LPG alone.

## 10. Assets, data, outputs, checkpoints, and models

- Provenance, licensing, hashes, and download instructions.
- Source versus generated ownership.
- Repository size and ignore behavior.
- Local absolute paths and machine-specific assumptions.
- Retention, cleanup, and backup needs.

## 11. Documentation and archives

- Current architecture map versus dated completion reports.
- Conflicting counts, statuses, commands, and examples.
- Historical evidence clearly labeled.
- Broken links, stale paths, and duplicated documents.
- Documentation updates coupled to future behavior changes.

## 12. Cross-cutting synthesis

- Draw the actual dependency graph.
- Select the smallest authoritative execution path.
- List duplicate APIs, loaders, validators, schemas, and state stores.
- Rank findings by impact and confidence.
- Convert findings into dependency-ordered actions with acceptance criteria.
