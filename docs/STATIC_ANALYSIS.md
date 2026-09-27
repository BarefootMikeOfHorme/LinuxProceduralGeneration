# Static analysis: mypy and black

Neither tool was installed, so nothing mechanically caught type or format
drift. Both are declared in the `dev` extra of `pyproject.toml`; they are now
installed and configured.

## What the tools report

Measured 2026-09-27, mypy 2.3.1, black 26.5.1, on `vaultmind_forge`:

| Tool | Baseline at introduction | Current |
|---|---|---|
| mypy | 431 errors across 82 files (169 checked) | 431 |
| black --check | 220 of 241 tracked files would be reformatted | 194 |

## Why this is not a blocking gate

Neither number is acceptable as a pass/fail threshold on day one, and turning
either into one would be dishonest.

**mypy's 431 errors are not 431 defects.** The largest categories are
`attr-defined` and `arg-type`, and most come from untyped third-party surfaces
(build123d, trimesh, torch) and from `Optional` values that are genuinely
narrowed by checks at runtime. Many are real; the point is that "431 errors"
cannot be read as "431 bugs", and a gate at that number would pass while real
problems remain.

**black would rewrite 91% of the codebase.** Running it repo-wide would produce
a diff touching nearly every file, burying any behavioural change in formatting
noise and making review impossible. Worse, it would rewrite the user's
uncommitted `examples/*.py` work along with everything else.

The 19 files this session actually modified *were* formatted, which brought the
count from 220 to 194. `-EnforceFormat` requires that files changed in recent
commits stay clean, so new work does not add to the backlog while the remaining
194 are worked down deliberately.

## What is enforced instead

A **ratchet**, not a gate. `scripts/verify.ps1` records the current counts and
fails if either number rises. That is the property that actually matters: debt
cannot silently grow, and a reduction is visible and creditable.

The baseline lives in `scripts/verify.ps1` as `MYPY_ERROR_BASELINE` and
`BLACK_FILE_BASELINE`. Raising either is a deliberate decision to accept more
debt and belongs in a commit message that says so. Lowering one is progress,
and the script says so when it detects one so the credit is not lost.

The ratchet is tested, not assumed: injecting a single type error into a new
module makes the run fail with `432 errors, baseline is 431`. If mypy produces
no parsable summary the script records the count as *unknown* and fails rather
than defaulting to 0, because treating an unparsable run as a clean one would
falsely credit a 431-error improvement.

## Scope

Both tools exclude `study-copies/`, which holds the exact pre-repair bytes of
earlier revisions. Reformatting those would destroy the only record of what a
file looked like before a repair, and they are not program source.

The formatter also skips the user's untracked `examples/*.py` files. They are
not covered by the baseline and should not be rewritten as a side effect of
adding tooling.

## Defects this already found

Running mypy immediately surfaced real bugs that the test suite did not catch,
because they sat in code paths no test exercised.

**`usd_handler.py` raised `NameError` on any conversion with UVs.** The method
imported `Usd, UsdGeom` but used `Gf.Vec2f` for UV pairs and
`Sdf.ValueTypeNames` for the texcoord primvar. Both names were undefined in
that scope. The path is only reached when a source mesh carries a `uv`
attribute, and a bare `except` nearby turned a load failure into a clean
`ConversionError`, so the `NameError` raised later was not attributable to the
missing import. Now imports `Gf, Sdf` and the bare `except` is narrowed and
chains the cause.

**Eight test modules would raise `NameError` if run directly.** They call
`sys.exit()` in a `__main__` guard, and an earlier change removed their
`import sys` while converting them to package imports. Under pytest that block
never executes, so all of them still passed. Running any file directly failed
with `NameError: name 'sys' is not defined`. The import is restored and every
module is now verified to run standalone, not merely to pass under pytest.

**Four modules annotated types that did not exist in their namespace.**
`openscad_import.py` and `openscad_csg.py` annotate return values as `'Mesh'`,
`forge_validator/backends.py` annotates `'np.ndarray'`, `forge_bots/scheduler.py`
annotates `'BatchProcessor'`, and `style_profile_manager.py` annotates
`'QualityGuardianAgent'`. In every case the name was resolvable at runtime
through a function-local import, so nothing broke, but the annotations could
not be checked and `typing.get_type_hints` on those functions would have
raised. Each is now a `TYPE_CHECKING` import, which resolves for type checkers
without creating an import cycle or a runtime dependency.

**A validator fallback reported a passing score for an unmeasurable asset.**
`forge_validator/backends.py` returned a fixed `0.7` when scipy was
unavailable. scipy is a core dependency, so that branch can only fire when the
environment is broken, and a validator that cannot measure sharpness was
reporting the asset as fine. It now computes a real numpy gradient measure, and
lets an `ImportError` from numpy itself propagate rather than absorbing it.

## Native extension findings

Adding native tests surfaced a problem that no amount of Python type checking
would have: **the extension Python was loading was nine months stale.**

`vaultmind_forge_core` resolved to
`.venv312/Lib/site-packages/vaultmind_forge_core/vaultmind_forge_core.cp312-win_amd64.pyd`,
dated 2025-12-14, 514560 bytes. The freshly built wheel is 243808 bytes. The
stale build reported a freshly created 2x2x2 box as **non-manifold with 36
problem edges**.

The geometry was fine. A temporary Rust probe printing the same mesh's indices
and validation report gave `manifold=true non_manifold=0 valid=true` for the
identical mesh, and the Rust unit test `test_validate_valid_mesh` passed
throughout. A box has 18 undirected edges each shared by exactly two faces,
confirmed by parsing the exported OBJ. So the geometry code and the validator
were both correct, and only the old binary disagreed.

Installing the current wheel fixed it: the same box now reports
`manifold=True non_manifold=0 valid=True`.

Two real native defects remain, both pinned by tests so they cannot regress
unnoticed.

**`create_sphere` collapses both poles.** `to_mesh` walks a
`(rings + 1) x (segments + 1)` grid, so the first and last rows place
`segments + 1` vertices on the same pole point. Result: 64 degenerate triangles,
79 duplicate vertices, 96 non-manifold edges, 96 boundary edges. A box
validates clean; a sphere does not, which is not a defensible state for a
default primitive.

**CSG is not implemented, and one of the three fails silently.** `csg_union`
and `csg_intersection` raise "encountered a spanning triangle; boundary
clipping is not implemented", which is correct and honest. `csg_difference` is
worse: it **succeeds and returns its first operand unchanged**. A 4x4x4 box
minus a 1.5-radius sphere comes back as the same 8-vertex, 12-triangle box, and
it validates as a clean manifold mesh. Nothing downstream can tell that no
cutting occurred. That is the most dangerous shape a stub can take.

The stale binary masked all of this. A validator that reported everything as
broken on a correct box would have been dismissed as noise, and nobody would
have been looking closely enough to notice that `csg_difference` was a no-op.

`test_difference_returns_the_operand_unchanged` is written to fail loudly if
that ever starts working, at which point it should be rewritten to assert real
geometry rather than deleted.

## Running it

```powershell
pwsh -NoProfile -File scripts/verify.ps1
```

Reports the mypy error count and the black file count, and fails if either has
risen above baseline. `scripts/verify.ps1 -EnforceFormat` additionally checks
that every file *this* tooling has touched is black-clean, so new work does not
add to the debt while the existing backlog is worked down separately.
