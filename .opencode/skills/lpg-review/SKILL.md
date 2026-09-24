---
name: LPG Review
description: Perform systematic, evidence-backed, folder-by-folder reviews of the LPG repository and turn the findings into a prioritized action plan.
---

# LPG Review

## Purpose

Use this skill to understand LPG without losing the distinction between the committed baseline, current uncommitted work, historical reports, generated artifacts, and external variants such as NodeForge.

The default deliverable is read-only. Do not change code until the user approves a specific action.

## Required boundaries

1. Read `AGENTS.md` before reviewing or changing anything.
2. Verify the Git root and record `git status --short --branch` before any mutation.
3. Preserve all modified and untracked work. Never reset, clean, stash, restore, or overwrite it to simplify a review.
4. Never open `.env`. Inspect `.env.example` and variable names instead.
5. Do not install dependencies; start services or containers; run Docker; invoke native/security tools; or execute builds and tests during onboarding unless the user explicitly authorizes them and the repository documents the relevant command.
6. Treat `build/`, `dist/`, `target/`, `output/`, `outputs/`, `logs/`, `uploads/`, caches, binaries, and generated wheels as local artifacts rather than source evidence.
7. Treat dated completion, smoke-test, and release reports as historical unless their exact evidence is reproduced for the current worktree.
8. Keep `C:\Users\Administrator\Desktop\Projects\NodeForge` separate. It is not a branch, submodule, frontend authority, or proven runtime dependency of LPG.
9. Classify claims as one of:
   - **Confirmed current** - directly verified in the current worktree.
   - **Committed baseline** - present in tracked source but not independently exercised.
   - **Historical claim** - found only in a report or dated document.
   - **Inference** - plausible but not proven.
   - **Unverified** - requires an authorized check.
10. Ask before any mutation, installation, long-lived process, external write, branch operation, commit, push, or pull request.

## Review workflow

### 1. Establish the baseline

Record:

- Git root, branch, remote, current commit, and ahead/behind state.
- Modified tracked files and untracked entries.
- Root documentation, manifests, environment template, ignore rules, and deployment files.
- Existing instructions and nested `AGENTS.md` files.

Do not change the worktree merely to make this baseline cleaner.

### 2. Build the repository map

Identify authoritative entry points and separate them from wrappers and experiments. At minimum inspect:

- `backend/api.py`, `backend/core/`, executors, persistence, and backend support modules.
- `vaultmind_forge/`, its protocol, loader, validator, and major `forge_*` domains.
- `rust_core/` and the native Rust validator.
- `vaultmind_forge/native/cpp/` and `backend/native/cpp/legacy/`.
- `src/` and its relationship to the separate NodeForge repository.
- `tests/`, root test-like scripts, examples, scripts, packaging, Docker, assets, data, outputs, and docs.

Trace at least these flows when relevant:

1. API or CLI request -> workflow model -> registry -> DAG validation -> executor -> persistence.
2. Geometry request -> Python API -> Rust/PyO3 -> mesh/CSG/validation -> export.
3. OpenSCAD source -> render -> import -> mesh -> CSG or export.
4. Node request -> local validation or Python subprocess -> response/job state.

### 3. Review folders in dependency order

Use `references/folder-checklist.md`. Review upstream contracts before downstream implementations and shared kernels before feature modules.

For every folder record:

- Purpose and ownership.
- Public entry points and contracts.
- Upstream and downstream dependencies.
- State, persistence, and side effects.
- Tests and executable verification.
- Documentation and examples.
- Generated or accidental artifacts.
- Correctness, security, maintainability, and portability concerns.
- Recommended action, priority, effort, risk, dependencies, and acceptance criteria.

### 4. Reconcile cross-cutting contracts

Explicitly compare:

- FastAPI versus the Node API.
- SQLite execution state versus in-memory job state.
- Python versus native validation backends.
- Duplicate native loaders and build paths.
- `pyproject.toml` versus requirements files and Docker installation.
- Source versus generated/vendor asset ownership.
- Committed source versus current untracked work.
- Current documentation versus historical completion claims.
- LPG deployment assumptions versus the absent frontend and separate NodeForge repository.

Do not recommend broad polyglot parity until the smallest authoritative path has been identified and stabilized.

### 5. Produce an action plan

Order work by dependency, not by subsystem size:

1. Protect existing work and establish trustworthy baselines.
2. Fix confirmed crash paths and correctness defects.
3. Define canonical APIs, state ownership, validator behavior, and packaging.
4. Add assertion-based tests at the narrowest useful layers.
5. Integrate native acceleration behind stable, tested contracts.
6. Repair documentation, examples, deployment, and release workflows.
7. Defer broad feature expansion until the foundation is reproducible.

Every action must include:

- Problem and evidence.
- Scope and explicit non-scope.
- Dependencies and prerequisites.
- Acceptance criteria.
- Verification evidence required.
- Rollback or recovery approach.
- Relative effort and risk.

Use `references/review-template.md` for the final report.

## Completion standard

A review is complete only when it:

- Covers every requested folder or explicitly records an excluded area.
- Distinguishes current evidence from historical claims.
- Preserves the dirty worktree.
- Reconciles conflicting architecture and documentation.
- Identifies the smallest viable authoritative runtime path.
- Ends with sequenced, measurable actions rather than a generic backlog.
