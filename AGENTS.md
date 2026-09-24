# VaultMind Forge (LPG)

Workspace identity: LPG

Root: `C:\Users\Administrator\Desktop\Projects\LPG`

This is the primary polyglot VaultMind Forge source repository. It contains
Python, Rust, C++, Node, deployment, generated assets, and evaluation material.
It is not the same workspace as the detached NodeForge variant.

## Repository state

- Local Git root: this directory.
- Remote: `https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration.git`.
- The current worktree already has four modified tracked files and many
  untracked entries. Preserve them; do not reset, clean, stash, or overwrite.
- The parent `C:\Users\Administrator\Desktop\Projects` repository is an empty
  accidental Git root and must never be used for LPG Git decisions.

## Relationship to NodeForge

`C:\Users\Administrator\Desktop\Projects\NodeForge` is an intentional Node/React
variant intended to utilize LPG's node concepts and forge workflow. It is not a
branch, submodule, or currently proven runtime dependency. Do not merge or
replace either side without an explicit authority decision.

## Source and generated boundaries

- Python package root: `vaultmind_forge/`.
- FastAPI entry: `backend/api.py`.
- Rust crates: `rust_core/` and the native validator crate.
- C++ validators: `vaultmind_forge/native/cpp/` and the legacy backend path.
- Node API: `src/server.js`.
- `.env` exists and is ignored; never open or stage it.
- `build`, `dist`, `target`, `output`, `logs`, `uploads`, and similar paths are
  generated/local state, not automatic validation targets.
- Vendored or large assets require an explicit storage/provenance decision.

## Toolchain and safety

The repository documents Python, Rust, C++, Node, Docker, and native build/test
paths, but there is no single agreed lint/format/typecheck contract. The
frontend referenced by deployment files is not present in LPG; NodeForge may
contain a detached copy, but that does not make it authoritative.

Do not install dependencies, start the backend, run Docker, launch port-8000
processes, use `start_backend.py`, or run native/security tooling during
workspace onboarding. Preserve historical smoke/build reports as historical,
not current evidence.
