# LPG-L1 Initial TODO

This list is intentionally amendable. It is the first L1 worklist, not a generated scan result.

## Scanner foundation

- [x] Place the scanner in a dedicated `al1scan` Rust project.
- [x] Add Windows `al1scan.ps1` launcher.
- [x] Add WSL/Linux `al1scan.sh` launcher.
- [x] Add full-root `--dump` mode.
- [x] Add JSON `--summary` monitor output.
- [x] Add relative `--scope` subtree scans.
- [x] Add bounded `--max-depth` scans.
- [x] Add bounded `--max-entries` and `--max-seconds` scans.
- [x] Emit structured warnings and partial/complete scan status.
- [x] Add TUI monitor/debug/repair station.
- [x] Add context-menu browse/report/copy actions.
- [x] Preserve additive-only repair confirmation.
- [x] Block symlink/junction traversal by default.
- [x] Exclude secret-like paths and generated/cache roots.
- [x] Mark depth-limited directories as truncated.
- [x] Use high-resolution modification timestamps for scan diffs.
- [ ] Add scan resource budgets: files, bytes, duration, and node count.
- [ ] Add structured warnings for unreadable or skipped entries.
- [ ] Add scoped repair rescans instead of full-root rescans.

## LPG-L1 authority

- [x] Define the canonical LPG-L1 profile manifest schema.
- [x] Define the component/node manifest schema.
- [x] Define the location-index schema.
- [x] Define the recursive component instance generator.
- [x] Implement machine IDs and parent/child relationships.
- [x] Implement alias and path resolution.
- [x] Emit observed candidate records.
- [x] Preserve partial scan state.
- [x] Define the authority promotion evidence schema.
- [x] Reject promotion of partial, incomplete, or insufficiently validated candidates.
- [x] Wire read-only promotion validation through the CLI.
- [x] Add dependency-impact expansion.
- [x] Add explicit dependency edge types to the authority contract.
- [x] Add read-only `--impact` command output.
- [x] Add tier-closure validation.
- [x] Add read-only `--closure` command output.
- [ ] Persist known-good promotion/rollback records.
- [ ] Define recursive component/node manifest schema.
- [ ] Define tier and subtier naming grammar.
- [ ] Define machine-ID, alias, and physical-path bindings.
- [ ] Implement the location index.
- [ ] Implement the level map.
- [ ] Implement the path-alias registry.
- [ ] Implement expected-location rules.
- [ ] Implement ownership and schema-dispatch records.
- [ ] Implement missing/planned/conflict records.
- [ ] Add a resolver for machine ID, human name, path, and alias queries.

## Lifecycle

- [ ] Define L1 startup states and failure states.
- [ ] Implement bootstrap discovery from the LPG open root.
- [ ] Implement minimal placeholder L1 tree materialization.
- [ ] Implement observed/approved/active diagram separation.
- [ ] Implement install sequence handoff.
- [ ] Implement environment refresh sequence.
- [ ] Implement scoped mutation rescans.
- [ ] Implement dependency-impact expansion.
- [ ] Implement tier-closure validation.
- [ ] Implement known-good revision tracking.
- [ ] Implement rollback journal.
- [ ] Implement controlled LPG restart/proof sequence.
- [ ] Implement final security/integration wizard handoff.

## Validation and safety

- [ ] Give every tier/subtier/component its own guardrails and validation contract.
- [ ] Add TOML/requirements/native-manifest compatibility checks.
- [ ] Separate repair mutation from report/export mutation.
- [ ] Add explicit dry-run and explain output.
- [ ] Add stable/beta/alpha/pinned channel policy.
- [ ] Add program-specific environment and hardware requirements.
- [ ] Add task-specific context deployment and unloading.
- [ ] Add AI proposal review before adding packages, MCPs, providers, or references.
- [ ] Add WSL/Linux and Windows evidence to the profile.

## Explicit non-goals for this slice

- [ ] Do not build a full provider layer yet.
- [ ] Do not start a permanent AL1 server yet.
- [ ] Do not rewrite the native geometry crate.
- [ ] Do not install FreeCAD, OpenSCAD, Blender, Docker, or GPU drivers automatically.
- [ ] Do not duplicate the entire machine tree.
- [ ] Do not treat generated reports, wheels, caches, or outputs as source authority.
