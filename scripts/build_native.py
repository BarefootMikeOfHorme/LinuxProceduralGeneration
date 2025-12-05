#!/usr/bin/env python3
"""
Unified build script for VaultMind Forge native components.
Builds:
1. Rust validator (vmf_validator) via maturin
2. C++ validator (validator.dll/so) via compiler
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RUST_DIR = PROJECT_ROOT / "vaultmind_forge" / "native" / "rust" / "validator"
CPP_DIR = PROJECT_ROOT / "vaultmind_forge" / "native" / "cpp" / "validator"
NATIVE_LIBS_DIR = PROJECT_ROOT / "vaultmind_forge" / "forge_validator" / "native_libs"

def check_command(cmd):
    """Check if a command exists in PATH"""
    return shutil.which(cmd) is not None

def build_rust():
    """Build Rust extension using maturin"""
    print("Building Rust components...")
    
    if not check_command("cargo"):
        print("Error: 'cargo' not found. Please install Rust: https://rustup.rs/")
        return False

    try:
        # Check if maturin is installed
        subprocess.run([sys.executable, "-m", "maturin", "--version"], 
                      check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing maturin...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "maturin"])

    try:
        # Build release version
        # We use 'maturin develop' to install it directly into the current venv
        
        # Ensure VIRTUAL_ENV is set so maturin knows where to install
        env = os.environ.copy()
        if "VIRTUAL_ENV" not in env:
            # Try to guess from sys.prefix or look for .venv312
            if sys.prefix != sys.base_prefix:
                env["VIRTUAL_ENV"] = sys.prefix
            elif (PROJECT_ROOT / ".venv312").exists():
                env["VIRTUAL_ENV"] = str(PROJECT_ROOT / ".venv312")
            else:
                print("Warning: Could not determine VIRTUAL_ENV. maturin might fail.")

        cmd = [sys.executable, "-m", "maturin", "develop", "--release"]
        subprocess.check_call(cmd, cwd=RUST_DIR, env=env)
        print("Rust build successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Rust build failed: {e}")
        # Try to capture output if possible, though check_call usually prints to stdout
        return False

def build_cpp():
    """Build C++ shared library"""
    print("Building C++ components...")
    
    # Ensure output directory exists
    NATIVE_LIBS_DIR.mkdir(parents=True, exist_ok=True)
    
    system = platform.system()
    src_file = CPP_DIR / "validator.cpp"
    
    if system == "Windows":
        output_file = NATIVE_LIBS_DIR / "validator.dll"
        # Try MSVC (cl.exe) first, then MinGW (g++)
        if check_command("cl"):
            print("   Using MSVC (cl.exe)")
            # Simple compilation for DLL
            cmd = ["cl", "/LD", "/O2", str(src_file), f"/Fe{output_file}"]
        elif check_command("g++"):
            print("   Using MinGW (g++)")
            cmd = ["g++", "-shared", "-O3", "-o", str(output_file), str(src_file)]
        else:
            print("Error: No C++ compiler found (cl.exe or g++).")
            return False
    else:
        # Linux/Mac
        output_file = NATIVE_LIBS_DIR / "libvalidator.so"
        if system == "Darwin":
            output_file = NATIVE_LIBS_DIR / "libvalidator.dylib"
            
        if check_command("g++"):
            cmd = ["g++", "-shared", "-fPIC", "-O3", "-o", str(output_file), str(src_file)]
        elif check_command("clang++"):
            cmd = ["clang++", "-shared", "-fPIC", "-O3", "-o", str(output_file), str(src_file)]
        else:
            print("Error: No C++ compiler found (g++ or clang++).")
            return False

    try:
        subprocess.check_call(cmd, cwd=CPP_DIR)
        print(f"C++ build successful: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"C++ build failed: {e}")
        return False

def main():
    print("VaultMind Forge - Native Build System")
    print("========================================")
    
    rust_ok = build_rust()
    print("-" * 40)
    cpp_ok = build_cpp()
    
    print("========================================")
    if rust_ok and cpp_ok:
        print("All native components built successfully!")
        sys.exit(0)
    else:
        print("Some components failed to build.")
        sys.exit(1)

if __name__ == "__main__":
    main()
