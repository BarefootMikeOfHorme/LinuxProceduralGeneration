"""Lazy native-geometry loading for the Python package.

The native extension is an optional runtime capability. It should be installed
with the package or supplied through an explicit development path; generated
repository build directories are never added to ``sys.path`` implicitly.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import ModuleType


class NativeGeometryUnavailable(ImportError):
    """Raised when the optional native geometry extension is unavailable."""


def _configured_paths() -> list[Path]:
    value = os.getenv("VAULTMIND_NATIVE_EXTENSION_PATH")
    if not value:
        return []

    configured = Path(value).expanduser()
    if configured.is_dir():
        return [configured]
    return [configured.parent]


def load_native() -> ModuleType:
    """Load ``vaultmind_forge_core`` from the environment or an explicit path."""
    try:
        return importlib.import_module("vaultmind_forge_core")
    except ModuleNotFoundError as exc:
        if exc.name != "vaultmind_forge_core":
            raise

        for candidate in _configured_paths():
            candidate_text = str(candidate)
            if candidate_text not in sys.path:
                sys.path.insert(0, candidate_text)
            try:
                return importlib.import_module("vaultmind_forge_core")
            except ModuleNotFoundError as retry_exc:
                if retry_exc.name != "vaultmind_forge_core":
                    raise

    raise NativeGeometryUnavailable(
        "The native geometry extension 'vaultmind_forge_core' is unavailable. "
        "Install the native LPG geometry package or set "
        "VAULTMIND_NATIVE_EXTENSION_PATH to an explicit extension directory "
        "for development. Generated rust_core/target directories are not "
        "searched implicitly."
    )
