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
