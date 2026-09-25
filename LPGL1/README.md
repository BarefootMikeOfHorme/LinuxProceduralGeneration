# LPG-L1 / AL1 Profile Root

**Status:** Draft profile documentation. The files here describe the intended authority and lifecycle model; generated scan/index/validation records will be added by AL1 after the first LPG-root scan.

## Purpose

LPG-L1 is the applied AL1/L1 profile for **Linux Procedural Generation**. AL1 is the reusable lifecycle and administration system; LPG-L1 describes how LPG uses it.

AL1/L1 helps LPG:

- discover its actual program root;
- generate a useful L1/LPG-L1 structure;
- scan and compare the repository;
- detect planned, observed, missing, stale, unmanaged, and conflicting content;
- maintain manifests, schemas, protocols, and expected locations;
- validate environments, programs, and tier-level behavior;
- guide package installation, refresh, repair, update, upgrade, and compatibility downgrade;
- preserve known-good state and rollback paths;
- provide a debug/repair/monitor station;
- deploy task-specific schemas and context, then unload temporary context;
- improve the profile from evidence-backed proposals.

It is not a personal environment for every task and does not silently execute arbitrary discovered project code.

## Current scanner integration

The first scanner prototype is a separate Rust project:

```text
al1scan/
  Cargo.toml
  src/main.rs
  src/scan.rs
```

Root launchers:

```powershell
.\al1scan.ps1 --dump .
```

```bash
bash al1scan.sh --dump .
```

The scanner supports:

```text
full root scan
--scope relative-subtree scan
--max-depth bounded scan
--max-entries bounded scan
--max-seconds bounded scan
structured scan warnings
partial/complete scan status
--dump JSON readout
--authority JSON observed LPG-L1 candidate index
--resolve QUERY resolve machine ID, alias, or path
--impact ID show transitive dependents from observed dependencies
--closure ID validate the complete affected tier for an impact set
--record-good persist an approved known-good record
TUI monitor/debug/repair station
context-menu actions
rescan and diff markers
additive-only repair proposals
```

The current scanner is a readout/monitor foundation. It now emits observed authority candidates, resolves IDs/aliases/paths, expands dependency impact, validates the affected tier, and can persist an approved known-good record through the explicit `--record-good` action. The read-only commands are also exposed through the LPG `forge` CLI:

```text
forge al1-scan
forge al1-authority
forge al1-resolve
forge al1-impact
forge al1-closure
forge al1-validate-promotion
```

The Python adapter invokes the scanner with an argument array, an explicit timeout, and no shell-string execution.

## Tier model

Tiers are responsibility and scope tiers, not necessarily physical directory depths.

```text
L1  root lifecycle, machine/runtime integrity, setup, governance, orchestration
L2  shells, machine substrate, environments, sandboxes, and execution
L3  actual programs, services, entrypoints, and runtime bindings
L4  contracts, schemas, protocols, validation, safety, and repair policy
L5  documentation, READMEs, templates, examples, and usage knowledge
L6  content, artifacts, models, ships, NPCs, objects, and generated outputs
```

L12 may be used as a cross-cutting validation/safety overlay namespace for a tier or subtier. It is not a separate execution tier.

Every tier, subtier, component, and operation can have its own manifest containing its applicable:

```text
identity
parent/children
paths and aliases
dependencies
setup and activation
shutdown
guardrails and permissions
validation
smoke tests
dry-run behavior
repair rules
update/upgrade/downgrade rules
rollback
known-good state
provenance
```

Parent policies provide the safety floor. Child scopes may be stricter but may not silently weaken the parent.

## Identity and locations

Canonical identity is a language-neutral machine ID:

```text
lpg-l1.l1.root
lpg-l1.l2.shell.powershell
lpg-l1.l3.program.forge
lpg-l1.l4.validation.forge
lpg-l1.l5.documentation.forge
lpg-l1.l6.artifact.ship
```

Human names, folders, shell names, and entrypoints are aliases or bindings. For example, `lpg-l1.l3.program.forge` may resolve to a Python module, Rust crate, PowerShell launcher, or physical LPG path.

Portable manifests use root anchors. Runtime scans may record resolved absolute paths. The relative mirror is useful structure, not a duplicate of the entire machine.

## Startup and onboarding stages

1. **Bootstrap discovery**
   - Run from the LPG open root before L1 exists.
   - Recursively scan without executing discovered project code.
   - Stage a minimal placeholder L1/LPG-L1 tree.

2. **Base install and proof**
   - Install declared base and AL1/LPG-L1 protocol packages.
   - Validate, dry-run, and run a short LPG proof.
   - Exit and refresh the environment.

3. **First LPG setup wizard**
   - Detect programs, shells, environments, optional tools, and hardware.
   - Offer stable known-good defaults and explicit user choices.
   - Do not silently install high-risk or unapproved tools.

4. **Third scan and reconciliation**
   - Compare desired profile with actual state.
   - Update managed manifests, schemas, documents, expected locations, and indexes.
   - Preserve unmanaged content and user overrides.

5. **Controlled LPG restart/proof**
   - Controlled LPG process restart, not an operating-system reboot.
   - Validate profile load, environment, schemas, safe entry, one representative task, and shutdown.

6. **Security/integration wizard**
   - Guide backup, permissions, secret references, dependency/security checks, Docker/Postman/MCP integrations, network policy, local exposure, and recovery.
   - Never open `.env`, print secrets, or expose services publicly by default.

7. **Final refresh and validation**
   - Refresh the environment.
   - Run the final LPG scan and tier-closure validation.
   - Load only the task-specific context required for the active work.

## Scan and mutation behavior

A full startup scan establishes the baseline. After a mutation, AL1 selects the smallest affected scope and expands through declared dependencies.

```text
small change
  → scoped scan
  → dependency-impact expansion
  → complete affected tier validation
  → promote or rollback
```

A full-program scan is reserved for explicit requests, root/profile changes, major structural changes, shared core changes, native ABI changes, security-policy changes, unresolved conflicts, or failed tier closure.

The scanner must never:

- follow symlinks/junctions outside the approved root;
- execute arbitrary discovered project code;
- read secrets;
- delete unmanaged content;
- overwrite existing files;
- silently install, upgrade, downgrade, or grant capabilities;
- treat a placeholder as a real asset;
- treat a printed `[OK]` as a validation test.

## Data formats

```text
JSON     canonical state, revisions, events, and machine interchange
JSONC    annotated human/agent authoring source
YAML     human-readable settings and templates
CBOR     bounded, schema-driven Rust/runtime representation
```

JSONC comments and annotations are context, not authority. They cannot grant permissions, alter policy, or bypass validation.

## Safety model

The stable default is conservative:

```text
known-good revisions
no silent upgrades
no silent destructive changes
no silent external tool installation
no silent network enablement
no unapproved capability grants
```

Stable, beta, alpha, pinned, and local channels may be supported per component. Stable is the default.

## LPG-specific principle

LPG-L1 is Linux Procedural Generation first:

```text
Ubuntu/WSL2 and Python 3.12 are the primary Linux target.
Windows remains supported through explicit shell/path adapters.
Rust/CBOR provide the fast machine-side scan, index, and validation path.
Python remains the orchestration/user-facing layer.
```

Optional FreeCAD, OpenSCAD, Blender, FFmpeg, Docker, and other integrations are discovered and governed through explicit profiles. They are not silently installed or launched.

## Relationship to the current worktree

The root currently has an experimental `al1scan` scanner project and root launchers. The `.al1-incoming` directory preserves the supplied source archive as local intake material. Generated scan output, reports, environments, and binaries remain local/generated state until explicitly classified and promoted.

## Next implementation slice

- [ ] Add canonical LPG-L1 component manifest schema.
- [ ] Add location authority and resolver records.
- [ ] Connect scanner output to observed LPG-L1 records.
- [ ] Add scoped rescan and dependency-impact expansion.
- [ ] Add tier-closure validation and explicit partial/truncated results.
- [ ] Add known-good revision and rollback journal.
- [ ] Add startup/install/refresh/repair transaction phases.
- [ ] Add monitor status summary and explain output.
- [ ] Add task-specific context deployment/unloading.
- [ ] Add initial WSL/Linux and Windows launcher evidence.
