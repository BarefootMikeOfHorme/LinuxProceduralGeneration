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
