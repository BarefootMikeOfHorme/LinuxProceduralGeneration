"""
Dual-Python Compatibility Handler for LPG Project
Manages Python 3.12 (stable/PyO3) and Python 3.14 (cutting-edge) environments
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Literal, Optional, Dict, Any
from dataclasses import dataclass


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
        """Detect and configure available Python environments"""
        envs = {}

        # Python 3.12 (PyO3 compatible, production)
        py312_path = self.project_root / ".venv312" / "Scripts" / "python.exe"
        if py312_path.exists():
            envs["3.12"] = PythonEnvironment(
                version="3.12",
                executable=py312_path,
                venv_path=self.project_root / ".venv312",
                use_case="Rust bindings (PyO3), production builds, stable features",
                pyo3_compatible=True
            )

        # Python 3.14 (cutting-edge, experimental)
        py314_path = Path(r"C:\Python314\python.exe")
        if py314_path.exists():
            envs["3.14"] = PythonEnvironment(
                version="3.14",
                executable=py314_path,
                venv_path=None,
                use_case="Experimental features, latest Python capabilities",
                pyo3_compatible=False  # Not yet supported by PyO3
            )

        return envs

    def get_environment(
        self,
        version: Optional[Literal["3.12", "3.14"]] = None,
        purpose: Optional[Literal["pyo3", "rust", "general", "experimental"]] = None
    ) -> PythonEnvironment:
        """
        Get appropriate Python environment based on version or purpose

        Args:
            version: Specific version to use ("3.12" or "3.14")
            purpose: Use case ("pyo3"/"rust" -> 3.12, "experimental" -> 3.14, "general" -> auto)

        Returns:
            PythonEnvironment configuration
        """
        if version:
            if version not in self.environments:
                raise ValueError(f"Python {version} not available. Available: {list(self.environments.keys())}")
            return self.environments[version]

        # Auto-select based on purpose
        if purpose in ("pyo3", "rust"):
            # PyO3 requires compatible version
            for env in self.environments.values():
                if env.pyo3_compatible:
                    return env
            raise RuntimeError("No PyO3-compatible Python environment found")

        elif purpose == "experimental":
            # Prefer latest version
            if "3.14" in self.environments:
                return self.environments["3.14"]

        # Default: prefer stable (3.12)
        if "3.12" in self.environments:
            return self.environments["3.12"]

        # Fallback to any available
        return next(iter(self.environments.values()))

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

        # Set environment variables for PyO3 if needed
        env_vars = os.environ.copy()
        if purpose in ("pyo3", "rust") or version == "3.12":
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
            config["maturin_command"] = [
                "maturin", "build", "--release",
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
