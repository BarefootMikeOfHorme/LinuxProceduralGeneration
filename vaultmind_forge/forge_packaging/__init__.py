from __future__ import annotations

"""
VaultMind Forge - Asset Packaging Module
Production-grade asset packaging with compression and integrity verification
"""

from .packager import (
    AssetPackager,
    AssetManifest,
    PackageInfo,
    PackagerError,
    InvalidAssetError,
    PackagingFailedError,
    quick_package,
)

__all__ = [
    "AssetPackager",
    "AssetManifest",
    "PackageInfo",
    "PackagerError",
    "InvalidAssetError",
    "PackagingFailedError",
    "quick_package",
]

__version__ = "1.0.0"