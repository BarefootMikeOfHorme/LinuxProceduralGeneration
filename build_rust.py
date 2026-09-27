"""
Rust Build Wrapper with Python Compatibility Handling
Uses the dual-Python compatibility system for robust builds
"""

import os
import sys
import subprocess
from pathlib import Path
from python_compat import PythonCompatHandler


def build_rust_core(
    mode: str = "release",
    use_maturin: bool = True,
    verbose: bool = True
):
    """
    Build Rust core with proper Python compatibility handling

    Args:
        mode: Build mode ("release" or "debug")
        use_maturin: Whether to use maturin (True) or cargo (False)
        verbose: Print verbose output
    """
    project_root = Path(__file__).parent
    rust_core_dir = project_root / "rust_core"

    # Initialize compatibility handler
    handler = PythonCompatHandler(project_root)

    if verbose:
        print("=" * 70)
        print("Building Rust Core with Python Compatibility Handler")
        print("=" * 70)
        handler.print_status()
        print()

    # Get build configuration for PyO3/Rust
    build_config = handler.get_build_config(for_rust=True)

    if verbose:
        print("Build Configuration:")
        print(f"  Mode: {mode}")
        print(f"  Python: {build_config['python_version']} ({build_config['python_executable']})")
        print(f"  Build Tool: {'maturin' if use_maturin else 'cargo'}")
        print()

    # Prepare environment with PyO3 compatibility
    env = os.environ.copy()
    env.update(build_config["environment_variables"])

    # Build command
    if use_maturin:
        # Resolve maturin from the environment the compat handler selected,
        # rather than assuming a Windows venv layout. The previous lookup was
        # hardcoded to .venv312/Scripts/maturin.exe, so on WSL2 or Linux it
        # never resolved and the build could not run at all on the platform
        # this project targets. get_build_config already prefers a maturin
        # inside the selected environment and falls back to PATH.
        cmd = [
            build_config["maturin_command"][0],
            "build",
            f"--{mode}",
            "--interpreter", build_config["python_executable"],
        ]
    else:
        # Cargo build (for Rust-only components)
        cmd = ["cargo", "build", f"--{mode}"]

    if verbose:
        print(f"Executing: {' '.join(cmd)}")
        print(f"Working Directory: {rust_core_dir}")
        print("=" * 70)
        print()

    # Execute build
    try:
        result = subprocess.run(
            cmd,
            cwd=rust_core_dir,
            env=env,
            check=True,
            text=True,
            capture_output=not verbose
        )

        if verbose:
            print()
            print("=" * 70)
            print("Build Successful!")
            print("=" * 70)

        return True

    except subprocess.CalledProcessError as e:
        print()
        print("=" * 70)
        print("Build Failed!")
        print("=" * 70)
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        return False

    except FileNotFoundError as e:
        print(f"Error: Build tool not found: {e}")
        print("\nMake sure you have installed:")
        if use_maturin:
            print(f"  maturin, in the selected environment or on PATH:")
            print(f"    {build_config['python_executable']} -m pip install maturin")
        else:
            print("  Rust toolchain (cargo)")
        return False


def install_rust_package(verbose: bool = True):
    """
    Install the built Rust package into the Python environment

    Args:
        verbose: Print verbose output
    """
    project_root = Path(__file__).parent
    handler = PythonCompatHandler(project_root)
    env = handler.get_environment(purpose="pyo3")

    if verbose:
        print("=" * 70)
        print(f"Installing package into Python {env.version}")
        print("=" * 70)

    # Use maturin develop for development installation
    cmd = [
        "maturin", "develop",
        "--release",
        "-m", "rust_core/Cargo.toml"
    ]

    env_vars = os.environ.copy()
    env_vars["PYO3_PYTHON"] = str(env.executable)

    try:
        subprocess.run(cmd, cwd=project_root, env=env_vars, check=True)
        if verbose:
            print("\nPackage installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("\nPackage installation failed!")
        return False


def main():
    """CLI interface for Rust build wrapper"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build Rust core with Python compatibility handling"
    )
    parser.add_argument(
        "--mode",
        choices=["release", "debug"],
        default="release",
        help="Build mode (default: release)"
    )
    parser.add_argument(
        "--cargo",
        action="store_true",
        help="Use cargo instead of maturin"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install the package after building (maturin develop)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )

    args = parser.parse_args()

    verbose = not args.quiet
    use_maturin = not args.cargo

    # Build
    success = build_rust_core(
        mode=args.mode,
        use_maturin=use_maturin,
        verbose=verbose
    )

    if not success:
        sys.exit(1)

    # Install if requested
    if args.install and use_maturin:
        if not install_rust_package(verbose=verbose):
            sys.exit(1)


if __name__ == "__main__":
    main()
