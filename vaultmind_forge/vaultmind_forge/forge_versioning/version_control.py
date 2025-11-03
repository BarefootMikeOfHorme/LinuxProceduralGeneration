"""
VaultMind Forge - Asset Version Control
Git-style branching and version control for assets
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import shutil
import hashlib


class AssetStatus(str, Enum):
    """Asset modification status"""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


@dataclass
class AssetVersion:
    """Single version of an asset"""
    version_id: str
    asset_path: Path
    checksum: str
    timestamp: datetime
    message: str
    author: str = "VaultMind Forge"
    parent_version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "asset_path": str(self.asset_path),
            "checksum": self.checksum,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "author": self.author,
            "parent_version": self.parent_version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AssetVersion:
        return cls(
            version_id=data["version_id"],
            asset_path=Path(data["asset_path"]),
            checksum=data["checksum"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message=data["message"],
            author=data.get("author", "VaultMind Forge"),
            parent_version=data.get("parent_version"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Branch:
    """Version control branch"""
    name: str
    head: Optional[str] = None  # Version ID of head
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "head": self.head,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Branch:
        return cls(
            name=data["name"],
            head=data.get("head"),
            created_at=datetime.fromisoformat(data["created_at"]),
            description=data.get("description", ""),
        )


class AssetVersionControl:
    """
    Git-style version control for assets.

    Features:
    - Branching and merging
    - Version history tracking
    - Checksum-based change detection
    - Rollback to previous versions
    - Branch comparison

    Example:
        vcs = AssetVersionControl(repo_path="./asset_repo")

        # Create version
        version = vcs.commit(
            asset_path="character.png",
            message="Initial character design"
        )

        # Create branch
        vcs.create_branch("experiment", "Testing new style")

        # Checkout branch
        vcs.checkout("experiment")
    """

    def __init__(self, repo_path: Path | str):
        """
        Initialize asset version control.

        Args:
            repo_path: Path to version control repository
        """
        self.repo_path = Path(repo_path)
        self.vcs_dir = self.repo_path / ".vaultmind_vcs"
        self.versions_dir = self.vcs_dir / "versions"
        self.refs_dir = self.vcs_dir / "refs"
        self.config_path = self.vcs_dir / "config.json"

        self._initialize_repo()

    def _initialize_repo(self) -> None:
        """Initialize repository structure"""
        self.vcs_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(exist_ok=True)
        self.refs_dir.mkdir(exist_ok=True)

        if not self.config_path.exists():
            config = {
                "created_at": datetime.now().isoformat(),
                "current_branch": "main",
                "branches": {
                    "main": Branch(name="main", description="Main branch").to_dict()
                }
            }
            self._save_config(config)

    def _load_config(self) -> dict:
        """Load repository configuration"""
        return json.loads(self.config_path.read_text())

    def _save_config(self, config: dict) -> None:
        """Save repository configuration"""
        self.config_path.write_text(json.dumps(config, indent=2))

    def _compute_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _generate_version_id(self) -> str:
        """Generate unique version ID"""
        import uuid
        return f"v{uuid.uuid4().hex[:12]}"

    def commit(
        self,
        asset_path: Path | str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AssetVersion:
        """
        Create new version of asset.

        Args:
            asset_path: Path to asset file
            message: Commit message
            metadata: Optional metadata dictionary

        Returns:
            AssetVersion object
        """
        asset_path = Path(asset_path)

        if not asset_path.exists():
            raise FileNotFoundError(f"Asset not found: {asset_path}")

        config = self._load_config()
        current_branch = config["current_branch"]
        branch = Branch.from_dict(config["branches"][current_branch])

        # Compute checksum
        checksum = self._compute_checksum(asset_path)

        # Generate version ID
        version_id = self._generate_version_id()

        # Create version
        version = AssetVersion(
            version_id=version_id,
            asset_path=asset_path,
            checksum=checksum,
            timestamp=datetime.now(),
            message=message,
            parent_version=branch.head,
            metadata=metadata or {},
        )

        # Store version
        version_path = self.versions_dir / f"{version_id}.json"
        version_path.write_text(json.dumps(version.to_dict(), indent=2))

        # Copy asset to versions directory
        asset_copy = self.versions_dir / f"{version_id}{asset_path.suffix}"
        shutil.copy2(asset_path, asset_copy)

        # Update branch head
        branch.head = version_id
        config["branches"][current_branch] = branch.to_dict()
        self._save_config(config)

        return version

    def get_history(
        self,
        branch_name: Optional[str] = None,
        max_count: Optional[int] = None,
    ) -> List[AssetVersion]:
        """
        Get version history.

        Args:
            branch_name: Branch name (None = current branch)
            max_count: Maximum number of versions to return

        Returns:
            List of AssetVersion objects (newest first)
        """
        config = self._load_config()

        if branch_name is None:
            branch_name = config["current_branch"]

        if branch_name not in config["branches"]:
            raise ValueError(f"Branch '{branch_name}' does not exist")

        branch = Branch.from_dict(config["branches"][branch_name])

        if branch.head is None:
            return []

        # Traverse version history
        history = []
        current_version_id = branch.head

        while current_version_id:
            version_path = self.versions_dir / f"{current_version_id}.json"

            if not version_path.exists():
                break

            version_data = json.loads(version_path.read_text())
            version = AssetVersion.from_dict(version_data)
            history.append(version)

            if max_count and len(history) >= max_count:
                break

            current_version_id = version.parent_version

        return history

    def checkout(self, branch_name: str) -> None:
        """
        Switch to different branch.

        Args:
            branch_name: Branch name to checkout
        """
        config = self._load_config()

        if branch_name not in config["branches"]:
            raise ValueError(f"Branch '{branch_name}' does not exist")

        config["current_branch"] = branch_name
        self._save_config(config)

    def create_branch(
        self,
        branch_name: str,
        description: str = "",
        from_branch: Optional[str] = None,
    ) -> Branch:
        """
        Create new branch.

        Args:
            branch_name: Name for new branch
            description: Branch description
            from_branch: Branch to branch from (None = current branch)

        Returns:
            Branch object
        """
        config = self._load_config()

        if branch_name in config["branches"]:
            raise ValueError(f"Branch '{branch_name}' already exists")

        # Determine parent branch
        if from_branch is None:
            from_branch = config["current_branch"]

        if from_branch not in config["branches"]:
            raise ValueError(f"Branch '{from_branch}' does not exist")

        parent_branch = Branch.from_dict(config["branches"][from_branch])

        # Create new branch with same head as parent
        new_branch = Branch(
            name=branch_name,
            head=parent_branch.head,
            description=description,
        )

        config["branches"][branch_name] = new_branch.to_dict()
        self._save_config(config)

        return new_branch

    def list_branches(self) -> List[Branch]:
        """
        List all branches.

        Returns:
            List of Branch objects
        """
        config = self._load_config()
        return [
            Branch.from_dict(data)
            for data in config["branches"].values()
        ]

    def get_version(self, version_id: str) -> Optional[AssetVersion]:
        """
        Get specific version by ID.

        Args:
            version_id: Version ID

        Returns:
            AssetVersion object or None if not found
        """
        version_path = self.versions_dir / f"{version_id}.json"

        if not version_path.exists():
            return None

        version_data = json.loads(version_path.read_text())
        return AssetVersion.from_dict(version_data)

    def restore_version(
        self,
        version_id: str,
        output_path: Path | str,
    ) -> Path:
        """
        Restore asset from specific version.

        Args:
            version_id: Version ID to restore
            output_path: Path to restore asset to

        Returns:
            Path to restored asset
        """
        version = self.get_version(version_id)

        if version is None:
            raise ValueError(f"Version '{version_id}' not found")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Find stored asset
        asset_files = list(self.versions_dir.glob(f"{version_id}.*"))

        if not asset_files:
            raise FileNotFoundError(f"Asset file for version '{version_id}' not found")

        # Copy to output path
        shutil.copy2(asset_files[0], output_path)

        return output_path

    def get_current_branch(self) -> Branch:
        """Get currently checked out branch"""
        config = self._load_config()
        branch_name = config["current_branch"]
        return Branch.from_dict(config["branches"][branch_name])

    def compare_branches(
        self,
        branch_a: str,
        branch_b: str,
    ) -> Dict[str, Any]:
        """
        Compare two branches.

        Args:
            branch_a: First branch name
            branch_b: Second branch name

        Returns:
            Comparison dictionary with differences
        """
        config = self._load_config()

        if branch_a not in config["branches"]:
            raise ValueError(f"Branch '{branch_a}' does not exist")
        if branch_b not in config["branches"]:
            raise ValueError(f"Branch '{branch_b}' does not exist")

        branch_a_obj = Branch.from_dict(config["branches"][branch_a])
        branch_b_obj = Branch.from_dict(config["branches"][branch_b])

        history_a = self.get_history(branch_a, max_count=50)
        history_b = self.get_history(branch_b, max_count=50)

        # Find common ancestor
        version_ids_a = {v.version_id for v in history_a}
        common_ancestor = None

        for version in history_b:
            if version.version_id in version_ids_a:
                common_ancestor = version.version_id
                break

        return {
            "branch_a": branch_a,
            "branch_b": branch_b,
            "branch_a_head": branch_a_obj.head,
            "branch_b_head": branch_b_obj.head,
            "common_ancestor": common_ancestor,
            "diverged": branch_a_obj.head != branch_b_obj.head,
            "commits_ahead_a": len([v for v in history_a if v.version_id != common_ancestor]),
            "commits_ahead_b": len([v for v in history_b if v.version_id != common_ancestor]),
        }
