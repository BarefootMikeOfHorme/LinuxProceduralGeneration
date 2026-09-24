# LPG Review Report Template

## Review metadata

- Repository:
- Review date:
- Git root:
- Branch and commit:
- Remote synchronization state:
- Worktree state:
- Scope:
- Exclusions and authorization limits:

## Executive assessment

Summarize:

- What LPG actually implements today.
- The strongest stable subsystem.
- The smallest credible authoritative runtime path.
- The highest-risk contradictions.
- Recommended immediate sequence.

## Folder coverage matrix

| Folder | Purpose | Entry points | Tests | Docs | Current evidence | Coverage |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

## Runtime and dependency maps

Record the actual flows through API/CLI, DAG execution, persistence, geometry/native code, OpenSCAD, and Node. Mark inferred edges explicitly.

## Findings

| ID | Severity | Confidence | Area | Finding | Evidence | Impact |
| --- | --- | --- | --- | --- | --- | --- |
| LPG-001 | P0/P1/P2/P3 | Confirmed/Committed/Historical/Inference |  |  | `path:line` |  |

### Finding detail

For each finding include:

- Problem statement.
- Evidence and affected paths.
- User or operational impact.
- Why existing tests or documentation do not prevent it.
- Smallest credible correction.
- Non-scope and tradeoffs.
- Required verification.

## Action plan

| Order | Action | Problems addressed | Priority | Effort | Risk | Dependencies | Acceptance evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 |  |  |  |  |  |  |  |

Sequence actions into:

1. Protect and baseline.
2. Correctness and crash prevention.
3. Canonical contracts and architecture.
4. Automated verification.
5. Native and workflow integration.
6. Documentation and deployment.
7. Product growth and release readiness.

## Intentionally unchanged

List source, generated state, dependencies, services, remote systems, and architecture decisions not modified during the review.

## Open decisions

Record only decisions that require user authority, such as frontend ownership, Node API future, model distribution, broad refactors, or dependency migrations.

## Next review checkpoint

Name the next folder or subsystem and the evidence that must be gathered before mutation.
