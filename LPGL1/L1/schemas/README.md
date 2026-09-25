# LPG-L1 Schema Registry

This directory contains strict JSON Schemas for the canonical LPG-L1 authority layer.

Current schemas:

- `component.manifest.schema.json`
  - recursive component/tier/subtier/program/artifact contract;
  - machine identity, aliases, paths, ownership, representations, dependencies, guardrails, validation, lifecycle, provenance, and children.
- `location-index.schema.json`
  - derived location authority index;
  - maps canonical IDs to aliases, root-relative/resolved paths, lifecycle state, ownership, schema, and scan provenance.
- `promotion-evidence.schema.json`
  - read-only input payload for the promotion gate;
  - requires complete scan, schema, security, system-requirement, tier-closure, digest, and known-good fields.
- `authority-promotion.schema.json`
  - durable record for observed-to-validated/approved promotion;
  - requires complete scan, schema, security, system-requirement, tier-closure, digest, and known-good evidence.
- `tier-closure.schema.json`
  - read-only report for the complete affected tier of a dependency impact set;
  - records per-component state, ownership, schema binding, status, and reasons.
- `known-good.schema.json`
  - append-only local record for a promotion that passed the evidence gate;
  - stored under ignored `.al1-state/known-good/` and never written for rejected or partial scans.
- `rollback-verification.schema.json`
  - read-only report for whether a persisted known-good record is a valid current rollback target.
- `lifecycle-stage.schema.json` (inert)
  - ordered setup/install stage with entry criteria, exit validation, and known-good binding;
  - a failed stage may not be recorded complete or known-good.
- `scan-choice.schema.json` (inert)
  - per-candidate detection state, compatibility reasons, offered options, and the user's explicit decision;
  - three-state detection is deliberate: `present_and_valid`, `present_invalid`, `absent`.
- `install-task.schema.json` (inert)
  - one bounded, reversible, approval-gated operation with declared reads, writes, validation, and rollback;
  - surface-neutral by design.
- `install-plan.schema.json` (inert)
  - deterministic ordered plan derived from a complete scan plus the applied profile;
  - skipped tasks must always carry a reason.
- `surface-binding.schema.json` (inert)
  - UI-neutral binding between an authority record and a presentation surface;
  - declares the prohibition set that keeps a surface from becoming the authority.

The inert schemas above are contracts only. Nothing reads or writes them yet, and
they are not part of the promotion gate. They exist so the first wizard can be
built as a Windows-style UI for ease of use while the authority layer stays
surface-neutral and the same records can later drive CLI, TUI, web, desktop, MCP,
and AI-agent surfaces.

These schemas do not make scanner output authoritative.

```text
observed scan
  → location/index candidate
  → validation
  → approved profile
  → active runtime state
```

A partial scan may produce warnings and candidate records, but it must not silently promote itself to `validated` or `active` state.

The schemas are strict machine contracts. Human-oriented annotations belong in JSONC comments or `x-al1` metadata and cannot grant capabilities, bypass policy, or replace the canonical component identity.
