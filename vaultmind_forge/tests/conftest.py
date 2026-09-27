"""Pytest configuration for the LPG test suite.

Two jobs, both about making a class of import defect loud instead of silent.

1. Guarantee the repository root is importable, so tests can use real package
   imports (`from vaultmind_forge.forge_batch import ...`).

   The root is added to sys.path, NOT the `vaultmind_forge/` package directory.
   Adding the package directory is what let submodules load as top-level
   modules, which in turn made sibling-relative imports like
   `from ..forge_executor.pipeline import ...` resolve against the wrong parent
   and either fail outright or succeed as a *second, distinct* copy of the
   module. That duplication is not cosmetic: it produces two instances of
   module-level singletons, including `forge_bots.native_bridge`'s
   `get_native_bridge`.

2. Fail the run if any test mutates sys.path.

   Eight test modules used to do `sys.path.insert(0, ...)` at import time. That
   is invisible in a single-module run and quietly changes what every later
   test imports, so it made the suite order-dependent and let real install-time
   import failures pass. The check below turns any recurrence into a collection
   error naming the offender.

The package is also installed in editable mode in the supported venvs, so this
root entry is a fallback for running against a source tree that is not
installed. It resolves the same module identity either way.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Repository root: the parent of the `vaultmind_forge` package directory.
REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Snapshot taken before any test module is imported. `pytest_collection_modifyitems`
# runs after collection, by which point every test module has been imported and any
# sys.path mutation has already happened, so comparing the two detects the edit
# regardless of which module made it or what order the suite ran in.
_SYS_PATH_AT_CONFIG = list(sys.path)


# ---------------------------------------------------------------------------
# Async backend: asyncio only.
#
# anyio 4.11's bundled pytest plugin declares its fixture as
# `params=get_all_backends()`, which returns ("asyncio", "trio") whether or not
# trio is installed. Every test marked `@pytest.mark.anyio` is therefore
# parametrized over trio, and each trio case fails at collection time inside
# anyio's own backend loader with `ModuleNotFoundError: No module named
# 'trio'`. That produced 42 failures across three modules, none of them related
# to LPG code.
#
# LPG's async contract is asyncio: `pytest-asyncio` is the declared dev
# dependency, and neither the README, pyproject, nor the requirements locks
# mention trio anywhere. trio is not an intended target, so it is not installed
# and not tested. Pinning the fixture states that intent explicitly instead of
# inheriting a default that reports backends LPG never asked to support.
#
# If trio support is ever genuinely wanted, install it and add it to the `dev`
# extra, then widen the tuple here.
# ---------------------------------------------------------------------------


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _sys_path_intruders() -> list[str]:
    """Return entries added to sys.path after this conftest was loaded."""
    baseline = set(_SYS_PATH_AT_CONFIG)
    return [entry for entry in sys.path if entry not in baseline]


def pytest_collection_modifyitems(config, items):
    """Fail collection if a test module mutated sys.path."""
    intruders = _sys_path_intruders()
    if not intruders:
        return

    package_dir = str(REPO_ROOT / "vaultmind_forge")
    offenders = sorted(
        str(item.module.__file__)
        for item in items
        if getattr(item.module, "__file__", None) and _module_mutated_path(item.module, package_dir)
    )

    detail = "\n".join(f"  added: {entry}" for entry in intruders)
    if offenders:
        detail += "\n  modules importing with a mutated sys.path:\n"
        detail += "\n".join(f"    {name}" for name in offenders)

    raise pytest.UsageError(
        "sys.path was mutated during test collection, which changes what later "
        "tests import and hides install-time import failures.\n"
        f"{detail}\n\n"
        "Import through the package instead "
        "(`from vaultmind_forge.forge_batch import ...`) and delete the "
        "`sys.path.insert` line. The repository root is already on sys.path via "
        "this conftest; the `vaultmind_forge/` package directory must never be "
        "added, because that loads submodules as top-level modules and splits "
        "module identity."
    )


def _module_mutated_path(module, package_dir: str) -> bool:
    """
    Report whether a test module appears to have added the package directory.

    Adding the bare package directory is the specific mistake that breaks
    sibling-relative imports, so it is named explicitly. A module may also have
    inserted some other path; the UsageError lists every added entry regardless,
    so the specific module is a best-effort attribution rather than the only
    signal.
    """
    source_file = getattr(module, "__file__", None)
    if not source_file:
        return False

    try:
        text = Path(source_file).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False

    return "sys.path" in text and package_dir in text
