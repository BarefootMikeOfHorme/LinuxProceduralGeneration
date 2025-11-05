"""
VaultMind Forge - Native Backend Loader
========================================

PASS 1: Core Structure
----------------------
Dynamic loading system for C++/Rust validation backends with fallback handling.

Philosophy:
- Load native backends when available (performance)
- Graceful fallback to Python (compatibility)
- Clear error messages for missing dependencies
- Cross-platform support (Windows/Linux/macOS)

Architecture:
  forge_loader.py (this file)
      ↓
  ┌───┴───┐
  │       │
  Rust    C++
  .so     .dll/.so
  .dylib  .dylib
"""

from __future__ import annotations

import os
import sys
import ctypes
import platform
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class BackendType(str, Enum):
    """Available backend types"""
    RUST = "rust"
    CPP = "cpp"
    PYTHON = "python"


class BackendStatus(str, Enum):
    """Backend loading status"""
    LOADED = "loaded"
    FALLBACK = "fallback"
    FAILED = "failed"
    NOT_FOUND = "not_found"


@dataclass
class BackendInfo:
    """Information about a loaded backend"""
    backend_type: BackendType
    status: BackendStatus
    version: Optional[str] = None
    path: Optional[Path] = None
    error: Optional[str] = None
    module: Optional[Any] = None


class NativeBackendLoader:
    """
    PASS 1: Core backend loading infrastructure

    Responsibilities:
    - Locate platform-specific shared libraries
    - Load backends dynamically
    - Track loading status
    - Provide fallback mechanism
    """

    def __init__(self, native_dir: Optional[Path] = None):
        """
        Initialize backend loader

        Args:
            native_dir: Path to native/ directory, defaults to ../native
        """
        self.native_dir = native_dir or self._find_native_dir()
        self.backends: Dict[str, BackendInfo] = {}
        self.platform = platform.system().lower()

        logger.info(f"NativeBackendLoader initialized for platform: {self.platform}")
        logger.info(f"Native directory: {self.native_dir}")

    def _find_native_dir(self) -> Path:
        """
        Locate the native/ directory relative to this file

        Returns:
            Path to native/ directory
        """
        # Assume native/ is at vaultmind_forge/native
        current_file = Path(__file__).resolve()
        native_dir = current_file.parent / "native"

        if not native_dir.exists():
            logger.warning(f"Native directory not found at {native_dir}")
            # Create it if missing
            native_dir.mkdir(parents=True, exist_ok=True)

        return native_dir

    def _get_library_name(self, backend_name: str, backend_type: BackendType) -> str:
        """
        Get platform-specific library name

        Args:
            backend_name: Name of the backend (e.g., 'validator')
            backend_type: Type of backend (rust/cpp)

        Returns:
            Library filename for current platform
        """
        # Library naming conventions
        if self.platform == "windows":
            if backend_type == BackendType.RUST:
                return f"{backend_name}.dll"
            else:  # C++
                return f"vmf_{backend_name}.dll"
        elif self.platform == "darwin":  # macOS
            if backend_type == BackendType.RUST:
                return f"lib{backend_name}.dylib"
            else:
                return f"libvmf_{backend_name}.dylib"
        else:  # Linux
            if backend_type == BackendType.RUST:
                return f"lib{backend_name}.so"
            else:
                return f"libvmf_{backend_name}.so"

    def _find_library(self, backend_name: str, backend_type: BackendType) -> Optional[Path]:
        """
        Search for library file in native directory

        Args:
            backend_name: Name of the backend
            backend_type: Type of backend

        Returns:
            Path to library if found, None otherwise
        """
        lib_name = self._get_library_name(backend_name, backend_type)

        # Search paths
        search_paths = [
            self.native_dir / backend_type.value / backend_name / lib_name,
            self.native_dir / backend_type.value / "build" / "release" / lib_name,
            self.native_dir / backend_type.value / "target" / "release" / lib_name,
            self.native_dir / lib_name,
        ]

        for path in search_paths:
            if path.exists():
                logger.info(f"Found library at {path}")
                return path

        logger.warning(f"Library {lib_name} not found in search paths")
        return None

    def load_rust_validator(self) -> BackendInfo:
        """
        Load Rust validator backend

        Returns:
            BackendInfo with loading status
        """
        backend_name = "validator"
        backend_type = BackendType.RUST

        # Find library
        lib_path = self._find_library(backend_name, backend_type)

        if not lib_path:
            return BackendInfo(
                backend_type=backend_type,
                status=BackendStatus.NOT_FOUND,
                error=f"Rust validator library not found in {self.native_dir}"
            )

        try:
            # Try importing as Python extension module (PyO3)
            # This is more robust than ctypes for Rust+PyO3
            import importlib.util
            spec = importlib.util.spec_from_file_location("rust_validator", str(lib_path))

            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules["rust_validator"] = module
                spec.loader.exec_module(module)

                version = getattr(module, "__version__", "unknown")

                info = BackendInfo(
                    backend_type=backend_type,
                    status=BackendStatus.LOADED,
                    version=version,
                    path=lib_path,
                    module=module
                )

                self.backends["rust_validator"] = info
                logger.info(f"Successfully loaded Rust validator v{version}")
                return info
            else:
                raise ImportError("Could not create module spec")

        except Exception as e:
            logger.error(f"Failed to load Rust validator: {e}")
            return BackendInfo(
                backend_type=backend_type,
                status=BackendStatus.FAILED,
                path=lib_path,
                error=str(e)
            )

    def load_cpp_validator(self) -> BackendInfo:
        """
        Load C++ validator backend via ctypes

        Returns:
            BackendInfo with loading status
        """
        backend_name = "validator"
        backend_type = BackendType.CPP

        # Find library
        lib_path = self._find_library(backend_name, backend_type)

        if not lib_path:
            return BackendInfo(
                backend_type=backend_type,
                status=BackendStatus.NOT_FOUND,
                error=f"C++ validator library not found in {self.native_dir}"
            )

        try:
            # Load via ctypes
            lib = ctypes.CDLL(str(lib_path))

            # Check for version function (ABI-safe)
            if hasattr(lib, "vmf_validator_version"):
                lib.vmf_validator_version.restype = ctypes.c_char_p
                version = lib.vmf_validator_version().decode('utf-8')
            else:
                version = "unknown"

            info = BackendInfo(
                backend_type=backend_type,
                status=BackendStatus.LOADED,
                version=version,
                path=lib_path,
                module=lib
            )

            self.backends["cpp_validator"] = info
            logger.info(f"Successfully loaded C++ validator v{version}")
            return info

        except Exception as e:
            logger.error(f"Failed to load C++ validator: {e}")
            return BackendInfo(
                backend_type=backend_type,
                status=BackendStatus.FAILED,
                path=lib_path,
                error=str(e)
            )

    def get_backend(self, name: str) -> Optional[BackendInfo]:
        """
        Get loaded backend by name

        Args:
            name: Backend name (e.g., 'rust_validator')

        Returns:
            BackendInfo if loaded, None otherwise
        """
        return self.backends.get(name)

    def list_backends(self) -> Dict[str, BackendInfo]:
        """
        List all loaded backends

        Returns:
            Dictionary of backend name to BackendInfo
        """
        return self.backends.copy()


    def discover_backends(self) -> Dict[str, list[BackendType]]:
        """
        PASS 2: Discover all available backends in native directory

        Returns:
            Dictionary mapping backend names to available types
        """
        discovered = {}

        # Check for validator backends
        for backend_type in [BackendType.RUST, BackendType.CPP]:
            lib_path = self._find_library("validator", backend_type)
            if lib_path:
                if "validator" not in discovered:
                    discovered["validator"] = []
                discovered["validator"].append(backend_type)

        logger.info(f"Discovered backends: {discovered}")
        return discovered

    def auto_load_all(self, prefer: BackendType = BackendType.RUST) -> Dict[str, BackendInfo]:
        """
        PASS 2: Automatically load all available backends

        Args:
            prefer: Preferred backend type when multiple are available

        Returns:
            Dictionary of loaded backends
        """
        discovered = self.discover_backends()
        loaded = {}

        for backend_name, available_types in discovered.items():
            # Try preferred type first
            if prefer in available_types:
                selected_type = prefer
            else:
                # Fall back to first available
                selected_type = available_types[0]

            # Load the backend
            if backend_name == "validator":
                if selected_type == BackendType.RUST:
                    info = self.load_rust_validator()
                elif selected_type == BackendType.CPP:
                    info = self.load_cpp_validator()
                else:
                    continue

                if info.status == BackendStatus.LOADED:
                    loaded[f"{selected_type.value}_{backend_name}"] = info

        return loaded

    def load_with_fallback(
        self,
        backend_name: str,
        preference_order: list[BackendType] = None
    ) -> BackendInfo:
        """
        PASS 2: Load backend with fallback chain

        Args:
            backend_name: Name of backend to load
            preference_order: Ordered list of backend types to try

        Returns:
            BackendInfo for first successfully loaded backend
        """
        if preference_order is None:
            preference_order = [BackendType.RUST, BackendType.CPP, BackendType.PYTHON]

        errors = []

        for backend_type in preference_order:
            try:
                if backend_name == "validator":
                    if backend_type == BackendType.RUST:
                        info = self.load_rust_validator()
                    elif backend_type == BackendType.CPP:
                        info = self.load_cpp_validator()
                    elif backend_type == BackendType.PYTHON:
                        # Return fallback info for Python
                        return BackendInfo(
                            backend_type=BackendType.PYTHON,
                            status=BackendStatus.FALLBACK,
                            version="fallback",
                            error="Using Python fallback implementation"
                        )
                    else:
                        continue

                    if info.status == BackendStatus.LOADED:
                        return info
                    else:
                        errors.append(f"{backend_type.value}: {info.error}")

            except Exception as e:
                errors.append(f"{backend_type.value}: {str(e)}")
                continue

        # All backends failed
        logger.warning(f"All backends failed for {backend_name}: {errors}")
        return BackendInfo(
            backend_type=BackendType.PYTHON,
            status=BackendStatus.FALLBACK,
            error=f"All backends failed, using Python fallback. Errors: {errors}"
        )


class BackendRegistry:
    """
    PASS 2: Global registry for managing loaded backends

    Singleton pattern for application-wide backend access
    """
    _instance: Optional['BackendRegistry'] = None
    _loader: Optional[NativeBackendLoader] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, native_dir: Optional[Path] = None) -> 'BackendRegistry':
        """
        Initialize the backend registry

        Args:
            native_dir: Path to native/ directory

        Returns:
            Initialized registry instance
        """
        instance = cls()
        if not cls._initialized:
            cls._loader = NativeBackendLoader(native_dir)
            cls._initialized = True
            logger.info("BackendRegistry initialized")
        return instance

    @classmethod
    def get_loader(cls) -> NativeBackendLoader:
        """
        Get the backend loader instance

        Returns:
            NativeBackendLoader instance

        Raises:
            RuntimeError: If registry not initialized
        """
        if not cls._initialized or cls._loader is None:
            raise RuntimeError("BackendRegistry not initialized. Call initialize() first.")
        return cls._loader

    @classmethod
    def load_validator(
        cls,
        prefer: BackendType = BackendType.RUST
    ) -> BackendInfo:
        """
        Load validator backend with preference

        Args:
            prefer: Preferred backend type

        Returns:
            BackendInfo for loaded validator
        """
        loader = cls.get_loader()
        return loader.load_with_fallback("validator", [prefer, BackendType.PYTHON])

    @classmethod
    def get_backend(cls, name: str) -> Optional[BackendInfo]:
        """
        Get backend by name from registry

        Args:
            name: Backend name

        Returns:
            BackendInfo if loaded, None otherwise
        """
        loader = cls.get_loader()
        return loader.get_backend(name)


# Convenience functions for simple usage
def load_validator(prefer: BackendType = BackendType.RUST) -> BackendInfo:
    """
    PASS 2: Convenience function to load validator backend

    Args:
        prefer: Preferred backend type

    Returns:
        BackendInfo for loaded validator

    Example:
        >>> from vaultmind_forge.forge_loader import load_validator, BackendType
        >>> info = load_validator(prefer=BackendType.RUST)
        >>> if info.status == BackendStatus.LOADED:
        ...     validator = info.module
    """
    registry = BackendRegistry.initialize()
    return registry.load_validator(prefer)


def get_loader() -> NativeBackendLoader:
    """
    PASS 2: Get the global backend loader instance

    Returns:
        NativeBackendLoader instance

    Example:
        >>> from vaultmind_forge.forge_loader import get_loader
        >>> loader = get_loader()
        >>> backends = loader.discover_backends()
    """
    registry = BackendRegistry.initialize()
    return registry.get_loader()


# END PASS 2
# Backend discovery and auto-loading complete. Next passes will add:
# - Pass 3: Comprehensive error handling, fallback chains, validation
# - Pass 4: Full documentation, examples, integration helpers
