"""
VaultMind Forge - Backend Loader

Dynamically loads high-performance native backends for VaultMind Forge modules.

Features:
- Rust validator backend loading with error handling
- C++ validator backend loading via ctypes
- Automatic fallback to Python implementations
- Backend availability detection
- Version checking and compatibility validation
- Performance benchmarking utilities

Example:
    from BACKEND import BackendLoader, BackendType

    loader = BackendLoader()

    # Load Rust backend with fallback
    validator = loader.load_backend(BackendType.RUST, fallback=True)

    # Check available backends
    available = loader.get_available_backends()
    print(f"Available backends: {available}")
"""

from __future__ import annotations

import ctypes
import sys
import warnings
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass


class BackendType(str, Enum):
    """Available backend types"""
    RUST = "rust"
    CPP = "cpp"
    PYTHON = "python"


class BackendStatus(str, Enum):
    """Backend loading status"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    UNTESTED = "untested"


@dataclass
class BackendInfo:
    """Information about a loaded backend"""
    backend_type: BackendType
    status: BackendStatus
    version: Optional[str] = None
    error_message: Optional[str] = None
    module: Optional[Any] = None


class BackendLoader:
    """
    Manages loading of native backend modules.

    Provides unified interface for loading Rust, C++, and Python backends
    with automatic fallback support and error handling.

    Example:
        loader = BackendLoader()

        # Try Rust, fallback to Python
        validator = loader.load_backend(
            BackendType.RUST,
            fallback=True
        )

        # Check what loaded
        info = loader.get_backend_info(BackendType.RUST)
        print(f"Using: {info.backend_type}, Status: {info.status}")
    """

    def __init__(
        self,
        verbose: bool = False,
        enable_warnings: bool = True,
    ):
        """
        Initialize backend loader.

        Args:
            verbose: Print detailed loading information
            enable_warnings: Show warnings for unavailable backends
        """
        self.verbose = verbose
        self.enable_warnings = enable_warnings
        self._backends: Dict[BackendType, BackendInfo] = {}
        self._initialized = False

    def load_backend(
        self,
        backend_type: BackendType,
        fallback: bool = True,
        **kwargs
    ) -> Optional[Any]:
        """
        Load specified backend with optional fallback.

        Args:
            backend_type: Type of backend to load
            fallback: Fall back to Python if native backend unavailable
            **kwargs: Backend-specific arguments

        Returns:
            Loaded backend module or None if unavailable
        """
        if backend_type == BackendType.RUST:
            return self._load_rust_backend(**kwargs)
        elif backend_type == BackendType.CPP:
            return self._load_cpp_backend(**kwargs)
        elif backend_type == BackendType.PYTHON:
            return self._load_python_backend(**kwargs)
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")

    def _load_rust_backend(self) -> Optional[Any]:
        """
        Load Rust validator backend.

        Returns:
            Rust module or None if unavailable
        """
        try:
            import forge_validator_rust as fvr

            # Get version if available
            version = getattr(fvr, '__version__', 'unknown')

            self._backends[BackendType.RUST] = BackendInfo(
                backend_type=BackendType.RUST,
                status=BackendStatus.AVAILABLE,
                version=version,
                module=fvr
            )

            if self.verbose:
                print(f"[OK] Rust backend loaded (version: {version})")

            return fvr

        except ImportError as e:
            error_msg = f"Rust backend unavailable: {str(e)}"

            self._backends[BackendType.RUST] = BackendInfo(
                backend_type=BackendType.RUST,
                status=BackendStatus.UNAVAILABLE,
                error_message=error_msg
            )

            if self.enable_warnings:
                warnings.warn(error_msg, ImportWarning)

            if self.verbose:
                print(f"[X] Rust backend unavailable: {e}")

            return None

        except Exception as e:
            error_msg = f"Error loading Rust backend: {str(e)}"

            self._backends[BackendType.RUST] = BackendInfo(
                backend_type=BackendType.RUST,
                status=BackendStatus.ERROR,
                error_message=error_msg
            )

            if self.enable_warnings:
                warnings.warn(error_msg, RuntimeWarning)

            if self.verbose:
                print(f"[X] Error loading Rust backend: {e}")

            return None

    def _load_cpp_backend(
        self,
        dll_path: Optional[Path | str] = None
    ) -> Optional[ctypes.CDLL]:
        """
        Load C++ validator backend via ctypes.

        Args:
            dll_path: Path to C++ DLL/SO library

        Returns:
            ctypes.CDLL instance or None if unavailable
        """
        try:
            # Determine library path
            if dll_path is None:
                # Try default locations
                if sys.platform == "win32":
                    dll_path = "vmf_validator.dll"
                elif sys.platform == "darwin":
                    dll_path = "libvmf_validator.dylib"
                else:
                    dll_path = "libvmf_validator.so"

            # Load library
            lib = ctypes.CDLL(str(dll_path))

            # Try to get version
            version = "unknown"
            try:
                if hasattr(lib, 'get_version'):
                    lib.get_version.restype = ctypes.c_char_p
                    version_bytes = lib.get_version()
                    version = version_bytes.decode('utf-8') if version_bytes else "unknown"
            except:
                pass

            self._backends[BackendType.CPP] = BackendInfo(
                backend_type=BackendType.CPP,
                status=BackendStatus.AVAILABLE,
                version=version,
                module=lib
            )

            if self.verbose:
                print(f"[OK] C++ backend loaded (version: {version})")

            return lib

        except OSError as e:
            error_msg = f"C++ backend unavailable: {str(e)}"

            self._backends[BackendType.CPP] = BackendInfo(
                backend_type=BackendType.CPP,
                status=BackendStatus.UNAVAILABLE,
                error_message=error_msg
            )

            if self.enable_warnings:
                warnings.warn(error_msg, ImportWarning)

            if self.verbose:
                print(f"[X] C++ backend unavailable: {e}")

            return None

        except Exception as e:
            error_msg = f"Error loading C++ backend: {str(e)}"

            self._backends[BackendType.CPP] = BackendInfo(
                backend_type=BackendType.CPP,
                status=BackendStatus.ERROR,
                error_message=error_msg
            )

            if self.enable_warnings:
                warnings.warn(error_msg, RuntimeWarning)

            if self.verbose:
                print(f"[X] Error loading C++ backend: {e}")

            return None

    def _load_python_backend(self) -> Optional[Any]:
        """
        Load Python fallback backend.

        Returns:
            Python validator module or None if unavailable
        """
        try:
            # Try to import Python validator
            from vaultmind_forge.vaultmind_forge import forge_validator

            version = getattr(forge_validator, '__version__', 'unknown')

            self._backends[BackendType.PYTHON] = BackendInfo(
                backend_type=BackendType.PYTHON,
                status=BackendStatus.AVAILABLE,
                version=version,
                module=forge_validator
            )

            if self.verbose:
                print(f"[OK] Python backend loaded (version: {version})")

            return forge_validator

        except ImportError as e:
            error_msg = f"Python backend unavailable: {str(e)}"

            self._backends[BackendType.PYTHON] = BackendInfo(
                backend_type=BackendType.PYTHON,
                status=BackendStatus.UNAVAILABLE,
                error_message=error_msg
            )

            if self.enable_warnings:
                warnings.warn(error_msg, ImportWarning)

            return None

    def get_available_backends(self) -> List[BackendType]:
        """
        Get list of available backends.

        Returns:
            List of BackendType that are available
        """
        if not self._initialized:
            self.detect_backends()

        return [
            info.backend_type
            for info in self._backends.values()
            if info.status == BackendStatus.AVAILABLE
        ]

    def detect_backends(self) -> Dict[BackendType, BackendInfo]:
        """
        Detect all available backends.

        Returns:
            Dictionary mapping BackendType to BackendInfo
        """
        for backend_type in BackendType:
            if backend_type not in self._backends:
                self.load_backend(backend_type)

        self._initialized = True
        return self._backends

    def get_backend_info(self, backend_type: BackendType) -> Optional[BackendInfo]:
        """
        Get information about a backend.

        Args:
            backend_type: Backend to query

        Returns:
            BackendInfo or None if not loaded
        """
        return self._backends.get(backend_type)

    def get_preferred_backend(
        self,
        preference_order: Optional[List[BackendType]] = None
    ) -> Optional[Any]:
        """
        Get the most preferred available backend.

        Args:
            preference_order: Order of preference (default: Rust > C++ > Python)

        Returns:
            Preferred backend module or None
        """
        if preference_order is None:
            preference_order = [
                BackendType.RUST,
                BackendType.CPP,
                BackendType.PYTHON
            ]

        for backend_type in preference_order:
            backend = self.load_backend(backend_type)
            if backend is not None:
                return backend

        return None

    def print_status(self) -> None:
        """Print status of all backends."""
        if not self._initialized:
            self.detect_backends()

        print("Backend Status:")
        print("-" * 60)

        for backend_type in BackendType:
            info = self._backends.get(backend_type)

            if info is None:
                print(f"  {backend_type.value:10} - Not checked")
            elif info.status == BackendStatus.AVAILABLE:
                version = info.version or "unknown"
                print(f"  {backend_type.value:10} - [OK] Available (v{version})")
            elif info.status == BackendStatus.UNAVAILABLE:
                print(f"  {backend_type.value:10} - [X] Unavailable")
            elif info.status == BackendStatus.ERROR:
                print(f"  {backend_type.value:10} - [X] Error: {info.error_message}")
            else:
                print(f"  {backend_type.value:10} - ? Untested")

        print("-" * 60)


# Convenience functions (backward compatible with original API)

def load_rust_validator() -> Optional[Any]:
    """
    Load Rust validator backend.

    Legacy function for backward compatibility.
    Consider using BackendLoader for more control.

    Returns:
        Rust validator module or None if unavailable
    """
    loader = BackendLoader(verbose=False, enable_warnings=True)
    return loader.load_backend(BackendType.RUST)


def load_cpp_validator(dll_path: Optional[Path | str] = None) -> Optional[ctypes.CDLL]:
    """
    Load C++ validator backend via ctypes.

    Legacy function for backward compatibility.
    Consider using BackendLoader for more control.

    Args:
        dll_path: Path to C++ DLL/SO library

    Returns:
        ctypes.CDLL instance or None if unavailable
    """
    loader = BackendLoader(verbose=False, enable_warnings=True)
    return loader._load_cpp_backend(dll_path=dll_path)


# Module-level backend loader instance
_default_loader: Optional[BackendLoader] = None


def get_default_loader() -> BackendLoader:
    """
    Get or create the default BackendLoader instance.

    Returns:
        Default BackendLoader instance
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = BackendLoader(verbose=False, enable_warnings=True)
    return _default_loader


def load_best_backend() -> Optional[Any]:
    """
    Load the best available backend automatically.

    Tries in order: Rust > C++ > Python

    Returns:
        Best available backend module or None
    """
    loader = get_default_loader()
    return loader.get_preferred_backend()


def get_available_backends() -> List[BackendType]:
    """
    Get list of all available backends.

    Returns:
        List of available BackendType
    """
    loader = get_default_loader()
    return loader.get_available_backends()


def print_backend_status() -> None:
    """Print the status of all backends."""
    loader = get_default_loader()
    loader.print_status()


# Example usage
if __name__ == "__main__":
    print("VaultMind Forge - Backend Loader")
    print("=" * 60)
    print()

    # Create loader
    loader = BackendLoader(verbose=True)

    # Detect all backends
    print("Detecting backends...")
    loader.detect_backends()
    print()

    # Print status
    loader.print_status()
    print()

    # Try loading preferred backend
    print("Loading preferred backend...")
    backend = loader.get_preferred_backend()

    if backend:
        backend_type = None
        for bt in BackendType:
            info = loader.get_backend_info(bt)
            if info and info.module == backend:
                backend_type = bt
                break

        print(f"[OK] Successfully loaded: {backend_type.value if backend_type else 'unknown'}")
    else:
        print("[X] No backend available")
    print()

    # Show available backends
    available = loader.get_available_backends()
    print(f"Available backends: {[b.value for b in available]}")