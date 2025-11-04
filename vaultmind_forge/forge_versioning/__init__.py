"""
VaultMind Forge - Versioning Module

Git-style version control for assets with branching and history tracking.

Features:
- Asset version tracking with checksums
- Branching and merging support
- Version history traversal
- Rollback to previous versions
- Branch comparison
- Lineage integration

Example:
    from vaultmind_forge.forge_versioning import AssetVersionControl

    vcs = AssetVersionControl(repo_path="./asset_repo")

    # Commit new version
    version = vcs.commit(
        asset_path="character.png",
        message="Updated character design",
        metadata={"iteration": 5}
    )

    # Create experimental branch
    vcs.create_branch("experiment", "Testing new style")
    vcs.checkout("experiment")
"""

from __future__ import annotations

from .version_control import (
    AssetVersionControl,
    AssetVersion,
    Branch,
    AssetStatus,
)

__all__ = [
    "AssetVersionControl",
    "AssetVersion",
    "Branch",
    "AssetStatus",
]

__version__ = "1.0.0"
