# LPG Geometry Change Checklist

## Before editing

- Read `AGENTS.md` and relevant nested instructions.
- Record Git status and preserve modified/untracked files.
- Identify the public contract and every caller.
- Identify whether the affected files are tracked, untracked, generated, or historical.
- Write a regression condition that the current implementation fails for the expected reason.

## Implementation checks

- [ ] Python import behavior is defined with and without the native extension.
- [ ] Package discovery includes the intended top-level package.
- [ ] PyO3 symbols and signatures match all Python callers.
- [ ] Primitive constructor fields match exporters, templates, and examples.
- [ ] Geometry has correct bounds, winding, normals, topology, and closedness.
- [ ] CSG clips spanning geometry and passes known regression cases.
- [ ] Import functions exist and parse valid and invalid input.
- [ ] Export extensions match actual file contents.
- [ ] Unsupported formats fail explicitly.
- [ ] OpenSCAD uses real attributes, registered bindings, and bounded subprocesses.
- [ ] Seeds, keyword forwarding, and tuple scaling are deterministic.
- [ ] Errors do not masquerade as successful generation.

## Test checks

- [ ] Tests assert geometry or file validity.
- [ ] Tests write only to temporary directories.
- [ ] Fixed seeds produce repeatable results.
- [ ] Every supported primitive has coverage.
- [ ] Capped/closed claims have manifold or boundary-edge coverage.
- [ ] CSG operations have known geometric expectations.
- [ ] Export tests validate signatures and parse the output.
- [ ] Round trips compare transformed geometry.
- [ ] A clean wheel/import path is tested when packaging changes.
- [ ] Failures identify the contract rather than only printing status.

## Reporting

Record:

- Files changed.
- Contract before and after.
- Tests added or updated.
- Exact commands run and outputs.
- Checks not run and why.
- Generated artifacts created during verification.
- Remaining compatibility and platform risks.
