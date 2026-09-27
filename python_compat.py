"""
Dual-Python Compatibility Handler for LPG Project
Manages Python 3.12 (stable/PyO3) and Python 3.14 (cutting-edge) environments
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Literal, Optional, Dict, Any
from dataclasses import dataclass

# Virtualenv directory names to probe, in priority order. The list is
# deliberately platform-agnostic: the same names are searched on every host and
# the interpreter layout inside them is resolved per platform by
# `_interpreter_in_venv` below. `.venv-linux` is first-class because the
# validated Ubuntu/WSL2 target uses it, not because Linux needs different names.
VENV_CANDIDATES = (".venv312", ".venv-linux", ".venv", "venv")

# Interpreters to probe on PATH for a non-venv install, newest first.
PATH_PYTHON_CANDIDATES = ("python3.14", "python3.12")


def _interpreter_in_venv(venv_dir: Path) -> Optional[Path]:
    """
    Return the interpreter inside a virtualenv directory, for this platform.

    A venv puts executables in `Scripts` on Windows and `bin` on POSIX, and
    Windows appends `.exe`. Hardcoding either layout means the lookup silently
    finds nothing on the other platform, which is how a Linux or WSL2 host ends
    up with no detected environments at all.
    """
    if os.name == "nt":
        relative = (("Scripts", "python.exe"), ("Scripts", "python"))
    else:
        relative = (("bin", "python"), ("bin", "python3"))

    for parts in relative:
        candidate = venv_dir.joinpath(*parts)
        if candidate.is_file():
            return candidate
    return None


def _probe_version(executable: Path) -> Optional[str]:
    """
    Ask an interpreter for its version as `major.minor`, or None if unusable.

    The version is read from the interpreter rather than inferred from the
    directory name, so a mislabelled or stale venv cannot claim to be a
    PyO3-compatible 3.12 when it is something else.
    """
    try:
        result = subprocess.run(
            [str(executable), "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


@dataclass
class PythonEnvironment:
    """Represents a Python environment configuration"""
    version: str
    executable: Path
    venv_path: Optional[Path]
    use_case: str
    pyo3_compatible: bool


class PythonCompatHandler:
    """Handles dual-Python environment management and routing"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent
        self.environments = self._detect_environments()

    def _detect_environments(self) -> Dict[str, PythonEnvironment]:
        """
        Detect and configure available Python environments.

        An explicit VAULTMIND_VENV_PATH wins, then the running interpreter if it
        is already a suitable virtualenv, then the known venv directory names,
        then PATH. Every candidate is resolved through
        `_interpreter_in_venv`, so the same code works on Windows and on
        WSL2/Linux rather than only on the platform the venv was created on.
        """
        envs: Dict[str, PythonEnvironment] = {}

        def register(executable: Path, venv_path: Optional[Path], use_case: str) -> None:
            version = _probe_version(executable)
            if version is None:
                return
            # First environment found for a version wins, so the priority
            # order below decides the answer rather than dict ordering.
            if version in envs:
                return
            envs[version] = PythonEnvironment(
                version=version,
                executable=executable,
                venv_path=venv_path,
                use_case=use_case,
                # PyO3 0.22 does not support 3.14; 3.12 is the supported build
                # target. Derived from the probed version so this stays true if
                # the toolchain moves, instead of hardcoding one version.
                pyo3_compatible=version == "3.12",
            )

        # 1. Explicit override, same env var config.py already honours.
        override = os.getenv("VAULTMIND_VENV_PATH")
        if override:
            venv_dir = Path(override)
            found = _interpreter_in_venv(venv_dir)
            if found is not None:
                register(found, venv_dir, "Explicit VAULTMIND_VENV_PATH override")

        # 2. The interpreter running this code, when it is already a venv.
        # This is the common case during a build and avoids depending on a
        # directory name at all.
        if sys.prefix != sys.base_prefix:
            register(
                Path(sys.executable),
                Path(sys.prefix),
                "Currently active virtualenv",
            )

        # 3. Known venv directories, in priority order.
        for venv_name in VENV_CANDIDATES:
            venv_dir = self.project_root / venv_name
            if not venv_dir.is_dir():
                continue
            found = _interpreter_in_venv(venv_dir)
            if found is not None:
                register(found, venv_dir, "Rust bindings (PyO3), production builds, stable features")

        # 4. PATH interpreters, for hosts using a system or pyenv install with
        # no project venv. This replaces a hardcoded C:\\Python314 path that
        # could only ever be true on one machine.
        for name in PATH_PYTHON_CANDIDATES:
            found = shutil.which(name)
            if found:
                register(
                    Path(found),
                    None,
                    "Interpreter found on PATH",
                )

        return envs

    def _version_key(self, version: str) -> tuple:
        """Sort key for '3.9' < '3.10' < '3.14'. Plain string compare gets
        that ordering wrong, which would make 3.9 look newer than 3.12."""
        try:
            parts = version.split(".")
            return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
        except (ValueError, IndexError):
            return (0, 0)

    def get_environment(
        self,
        version: Optional[str] = None,
        purpose: Optional[Literal["pyo3", "rust", "general", "experimental"]] = None
    ) -> PythonEnvironment:
        """
        Get appropriate Python environment based on version or purpose

        Args:
            version: Specific version to use, e.g. "3.12"
            purpose: Use case ("pyo3"/"rust" -> PyO3-compatible, "experimental"
                -> newest available, "general" -> PyO3-compatible then newest)

        Returns:
            PythonEnvironment configuration

        Selection is derived from the probed `pyo3_compatible` flag and the
        actual detected versions, not from hardcoded "3.12"/"3.14" keys, so it
        keeps working when the toolchain moves to a new version.
        """
        if not self.environments:
            searched = ", ".join(VENV_CANDIDATES)
            raise RuntimeError(
                "No Python environment found. Searched virtualenv directories "
                f"[{searched}] under {self.project_root}, the active "
                "interpreter, and PATH. Create one, or point "
                "VAULTMIND_VENV_PATH at an existing environment."
            )

        if version:
            if version not in self.environments:
                raise ValueError(
                    f"Python {version} not available. "
                    f"Available: {sorted(self.environments, key=self._version_key)}"
                )
            return self.environments[version]

        newest = max(
            self.environments.values(), key=lambda e: self._version_key(e.version)
        )

        if purpose == "experimental":
            return newest

        # PyO3 builds need a compatible interpreter. This is also the default
        # choice, because a PyO3-compatible interpreter is the one that can
        # build and run the native core.
        for env in self.environments.values():
            if env.pyo3_compatible:
                return env

        if purpose in ("pyo3", "rust"):
            raise RuntimeError(
                "No PyO3-compatible Python environment found. PyO3 0.22 requires "
                f"Python 3.12. Detected: "
                f"{sorted(self.environments, key=self._version_key)}"
            )

        return newest

    def run_command(
        self,
        command: list[str],
        version: Optional[Literal["3.12", "3.14"]] = None,
        purpose: Optional[Literal["pyo3", "rust", "general", "experimental"]] = None,
        **kwargs
    ) -> subprocess.CompletedProcess:
        """
        Run a command with the appropriate Python environment

        Args:
            command: Command to run (e.g., ["python", "-m", "pip", "install", "numpy"])
            version: Specific Python version to use
            purpose: Purpose-based auto-selection
            **kwargs: Additional arguments for subprocess.run

        Returns:
            CompletedProcess result
        """
        env = self.get_environment(version, purpose)

        # Replace "python" with actual executable path
        if command[0] in ("python", "python.exe"):
            command[0] = str(env.executable)

        # Set environment variables for PyO3 if needed. Keyed off the resolved
        # environment's compatibility flag rather than a hardcoded version
        # string, so an explicitly requested 3.12 is covered even when no
        # purpose was given.
        env_vars = os.environ.copy()
        if purpose in ("pyo3", "rust") or env.pyo3_compatible:
            env_vars["PYO3_PYTHON"] = str(env.executable)

        return subprocess.run(command, env=env_vars, **kwargs)

    def get_build_config(self, for_rust: bool = True) -> Dict[str, Any]:
        """
        Get configuration for building Rust extensions

        Args:
            for_rust: Whether this is for Rust/PyO3 builds

        Returns:
            Configuration dictionary with paths and environment variables
        """
        env = self.get_environment(purpose="pyo3" if for_rust else "general")

        config = {
            "python_executable": str(env.executable),
            "python_version": env.version,
            "venv_path": str(env.venv_path) if env.venv_path else None,
            "environment_variables": {
                "PYO3_PYTHON": str(env.executable),
            }
        }

        if for_rust:
            # Prefer a maturin that lives in the selected environment, so the
            # build uses the same interpreter it will be installed into.
            # `maturin` is still the fallback for a host that installs it
            # globally or on PATH. Resolution is platform-aware: a Windows venv
            # has Scripts/maturin.exe, a POSIX one bin/maturin.
            local_maturin = None
            if env.venv_path is not None:
                if os.name == "nt":
                    local_maturin = env.venv_path / "Scripts" / "maturin.exe"
                else:
                    local_maturin = env.venv_path / "bin" / "maturin"
                if not local_maturin.is_file():
                    local_maturin = None

            maturin = str(local_maturin) if local_maturin else (shutil.which("maturin") or "maturin")
            config["maturin_command"] = [
                maturin, "build", "--release",
                "--interpreter", str(env.executable)
            ]

        return config

    def print_status(self):
        """Print current environment status"""
        print("=" * 70)
        print("Python Environment Status")
        print("=" * 70)

        for version, env in self.environments.items():
            print(f"\nPython {version}:")
            print(f"  Executable: {env.executable}")
            print(f"  Virtual Env: {env.venv_path or 'N/A'}")
            print(f"  Use Case: {env.use_case}")
            print(f"  PyO3 Compatible: {'YES' if env.pyo3_compatible else 'NO'}")
            print(f"  Available: {'YES' if env.executable.exists() else 'NO'}")

        print("\n" + "=" * 70)
        print("Recommended Usage:")
        print("  - Rust builds (PyO3): Python 3.12")
        print("  - Experimental features: Python 3.14")
        print("  - General development: Python 3.12 (stable)")
        print("=" * 70)


def main():
    """CLI interface for Python compatibility handler"""
    handler = PythonCompatHandler()

    if len(sys.argv) < 2:
        handler.print_status()
        print("\nUsage:")
        print("  python python_compat.py status          - Show environment status")
        print("  python python_compat.py build-config    - Get Rust build config")
        print("  python python_compat.py run <version> <command...>  - Run command with specific Python")
        return

    command = sys.argv[1]

    if command == "status":
        handler.print_status()

    elif command == "build-config":
        config = handler.get_build_config(for_rust=True)
        print(json.dumps(config, indent=2))

    elif command == "run" and len(sys.argv) >= 4:
        version = sys.argv[2]
        cmd = sys.argv[3:]
        result = handler.run_command(cmd, version=version)
        sys.exit(result.returncode)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
