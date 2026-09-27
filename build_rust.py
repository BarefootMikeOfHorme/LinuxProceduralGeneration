"""
Rust Build Wrapper with Python Compatibility Handling
Uses the dual-Python compatibility system for robust builds
"""

import os
import sys
import subprocess
from pathlib import Path
from python_compat import PythonCompatHandler


def build_rust_core(mode: str = "release", use_maturin: bool = True, verbose: bool = True):
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
            "--interpreter",
            build_config["python_executable"],
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
        # Reading the child's output as UTF-8 is only half the problem. Printing
        # it is the other half: on a Windows console Python encodes stdout with
        # the active code page, and cargo's diagnostics contain characters that
        # cp1252 cannot represent, such as the U+1F517 wrench it uses to mark an
        # error. Printing the captured stderr then raised UnicodeEncodeError
        # from inside the failure handler, so a real build failure reported as a
        # crash in this script rather than as a build error.
        #
        # Reconfiguring to UTF-8 with replacement keeps the diagnostics readable
        # instead of mangled or fatal. Done here rather than at import so the
        # module stays importable in contexts where stdout is redirected.
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):
                # Not a TextIOBase, or already detached. Nothing to fix.
                pass

        result = subprocess.run(
            cmd,
            cwd=rust_core_dir,
            env=env,
            check=True,
            # Decode as UTF-8 with replacement rather than letting Python pick
            # the console code page. `text=True` alone decodes with the locale
            # encoding, which on Windows is cp1252, and cargo and maturin emit
            # UTF-8 (box-drawing characters in build output, for one). That
            # raised UnicodeDecodeError inside the reader thread, which killed
            # the build script while it was printing. The script then exited 0
            # because the exception was raised after check=True had already
            # passed, so a failed run was reported as a success.
            encoding="utf-8",
            errors="replace",
            capture_output=not verbose,
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

    except Exception as e:
        # Anything else that goes wrong while running or decoding the build.
        # Previously an unhandled exception here propagated out of the script
        # and main() exited 0, because sys.exit(1) is only reached when
        # build_rust_core returns False. A UnicodeDecodeError in the reader
        # thread did exactly that and reported a failed build as a success.
        print()
        print("=" * 70)
        print("Build Failed!")
        print("=" * 70)
        print(f"{type(e).__name__}: {e}")
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
    cmd = ["maturin", "develop", "--release", "-m", "rust_core/Cargo.toml"]

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
        help="Build mode (default: release)",
    )
    parser.add_argument("--cargo", action="store_true", help="Use cargo instead of maturin")
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install the package after building (maturin develop)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")

    args = parser.parse_args()

    verbose = not args.quiet
    use_maturin = not args.cargo

    # Build
    success = build_rust_core(mode=args.mode, use_maturin=use_maturin, verbose=verbose)

    if not success:
        sys.exit(1)

    # Install if requested
    if args.install and use_maturin:
        if not install_rust_package(verbose=verbose):
            sys.exit(1)


if __name__ == "__main__":
    main()
