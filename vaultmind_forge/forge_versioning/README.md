# forge_versioning

Git-style version control for digital assets in VaultMind Forge.

## Overview

`forge_versioning` provides comprehensive version control for digital assets (images, models, configs, etc.) with branching, merging, and history tracking capabilities. Unlike traditional Git designed for text files, this module is optimized for binary assets with checksum-based change detection and efficient storage.

## Key Features

- **Git-Style Branching**: Create, switch, and manage branches for experimental work
- **Version History**: Full history tracking with parent-child relationships
- **Checksum Verification**: SHA-256 checksums for integrity and change detection
- **Rollback Support**: Restore any previous version instantly
- **Branch Comparison**: Compare branches and find common ancestors
- **Metadata Support**: Attach custom metadata to each version
- **Lineage Integration**: Compatible with forge_lineage for provenance tracking
- **Lightweight Storage**: Efficient storage structure with minimal overhead
- **Asset Restoration**: Quickly restore any historical version

## Installation

```bash
pip install python>=3.10
```

No external dependencies required - uses Python standard library.

## Quick Start

```python
from vaultmind_forge.forge_versioning import AssetVersionControl

# Initialize repository
vcs = AssetVersionControl(repo_path="./my_project")

# Commit initial version
version = vcs.commit(
    asset_path="character.png",
    message="Initial character design",
    metadata={"iteration": 1, "artist": "Jane"}
)

# Make changes and commit
version2 = vcs.commit(
    asset_path="character.png",
    message="Updated character colors"
)

# Create experimental branch
vcs.create_branch("experiment", "Testing new style")
vcs.checkout("experiment")

# View history
history = vcs.get_history()
for v in history:
    print(f"{v.version_id}: {v.message}")
```

## API Reference

### AssetVersionControl

Main class for asset version control.

#### Constructor

```python
AssetVersionControl(repo_path: Path | str)
```

**Parameters:**
- `repo_path`: Path to version control repository (will be created if doesn't exist)

#### Methods

##### commit()

Create a new version of an asset.

**Parameters:**
- `asset_path` (Path | str): Path to asset file to commit
- `message` (str): Commit message describing changes
- `metadata` (Dict[str, Any], optional): Custom metadata dictionary

**Returns:** AssetVersion object

**Example:**
```python
version = vcs.commit(
    asset_path="model.obj",
    message="Fixed topology issues",
    metadata={"poly_count": 15000, "uv_mapped": True}
)
```

##### get_history()

Get version history for a branch.

**Parameters:**
- `branch_name` (str, optional): Branch name (None = current branch)
- `max_count` (int, optional): Maximum versions to return

**Returns:** List[AssetVersion] (newest first)

##### checkout()

Switch to a different branch.

**Parameters:**
- `branch_name` (str): Branch name to checkout

##### create_branch()

Create a new branch.

**Parameters:**
- `branch_name` (str): Name for new branch
- `description` (str, optional): Branch description
- `from_branch` (str, optional): Branch to branch from (None = current)

**Returns:** Branch object

##### list_branches()

List all branches in the repository.

**Returns:** List[Branch]

##### get_version()

Get a specific version by ID.

**Parameters:**
- `version_id` (str): Version ID to retrieve

**Returns:** AssetVersion or None if not found

##### restore_version()

Restore an asset from a specific version.

**Parameters:**
- `version_id` (str): Version ID to restore
- `output_path` (Path | str): Path to restore asset to

**Returns:** Path to restored asset

##### get_current_branch()

Get the currently checked out branch.

**Returns:** Branch object

##### compare_branches()

Compare two branches.

**Parameters:**
- `branch_a` (str): First branch name
- `branch_b` (str): Second branch name

**Returns:** Dictionary with comparison information

### AssetVersion

Represents a single version of an asset.

**Attributes:**
- `version_id` (str): Unique version identifier
- `asset_path` (Path): Path to original asset
- `checksum` (str): SHA-256 checksum
- `timestamp` (datetime): Version creation time
- `message` (str): Commit message
- `author` (str): Author name
- `parent_version` (str, optional): Parent version ID
- `metadata` (dict): Custom metadata

### Branch

Represents a version control branch.

**Attributes:**
- `name` (str): Branch name
- `head` (str, optional): Version ID at branch head
- `created_at` (datetime): Branch creation time
- `description` (str): Branch description

### AssetStatus

Enum for asset modification status.

- **ADDED**: New asset
- **MODIFIED**: Existing asset modified
- **DELETED**: Asset deleted
- **UNCHANGED**: No changes

## Usage Examples

### Basic Versioning Workflow

```python
from vaultmind_forge.forge_versioning import AssetVersionControl

# Initialize repository
vcs = AssetVersionControl(repo_path="./assets")

# Commit initial asset
v1 = vcs.commit(
    asset_path="character.png",
    message="Initial character design"
)

# Work on asset, then commit changes
v2 = vcs.commit(
    asset_path="character.png",
    message="Added facial details",
    metadata={"iteration": 2}
)

# View history
history = vcs.get_history()
for version in history:
    print(f"{version.timestamp}: {version.message}")
```

### Branching for Experiments

```python
vcs = AssetVersionControl(repo_path="./assets")

# Initial work on main branch
vcs.commit("model.obj", "Base model complete")

# Create experimental branch
vcs.create_branch("high_poly", "High-poly version experiment")
vcs.checkout("high_poly")

# Work on experimental version
vcs.commit("model.obj", "Increased subdivision to 4 levels")
vcs.commit("model.obj", "Added fine details")

# Switch back to main
vcs.checkout("main")

# Continue main work
vcs.commit("model.obj", "Optimized for game engine")
```

### Comparing Branches

```python
vcs = AssetVersionControl(repo_path="./assets")

# Compare two branches
comparison = vcs.compare_branches("main", "experiment")

print(f"Branch A: {comparison['branch_a']}")
print(f"Branch B: {comparison['branch_b']}")
print(f"Diverged: {comparison['diverged']}")
print(f"Commits ahead (A): {comparison['commits_ahead_a']}")
print(f"Commits ahead (B): {comparison['commits_ahead_b']}")
print(f"Common ancestor: {comparison['common_ancestor']}")
```

### Restoring Previous Versions

```python
vcs = AssetVersionControl(repo_path="./assets")

# Get history
history = vcs.get_history()

# Find version to restore
target_version = history[5]  # 6th most recent
print(f"Restoring: {target_version.message}")

# Restore to working directory
vcs.restore_version(
    version_id=target_version.version_id,
    output_path="./restored/character.png"
)
```

### Multi-Asset Tracking

```python
vcs = AssetVersionControl(repo_path="./game_assets")

# Track different asset types
vcs.commit("textures/character_diffuse.png", "Initial diffuse map")
vcs.commit("textures/character_normal.png", "Initial normal map")
vcs.commit("models/character.fbx", "Initial character model")

# Update related assets together
vcs.commit("textures/character_diffuse.png", "Updated colors")
vcs.commit("models/character.fbx", "Updated UV layout")

# View complete history
history = vcs.get_history()
```

### Working with Metadata

```python
vcs = AssetVersionControl(repo_path="./assets")

# Commit with rich metadata
version = vcs.commit(
    asset_path="render.png",
    message="Final render with new lighting",
    metadata={
        "render_time": "45min",
        "samples": 1024,
        "resolution": "4K",
        "engine": "Cycles",
        "denoised": True,
        "passes": ["combined", "diffuse", "glossy"]
    }
)

# Later, retrieve and use metadata
retrieved = vcs.get_version(version.version_id)
print(f"Render samples: {retrieved.metadata['samples']}")
print(f"Render time: {retrieved.metadata['render_time']}")
```

### Branch Workflow for Team Collaboration

```python
vcs = AssetVersionControl(repo_path="./shared_assets")

# Main branch - production assets
vcs.checkout("main")
vcs.commit("logo.svg", "Production logo v1.0")

# Artist 1 creates feature branch
vcs.create_branch("artist1_updates", "Color scheme exploration")
vcs.checkout("artist1_updates")
vcs.commit("logo.svg", "Tried blue color scheme")

# Artist 2 creates another branch
vcs.checkout("main")
vcs.create_branch("artist2_updates", "Typography updates")
vcs.checkout("artist2_updates")
vcs.commit("logo.svg", "Updated font to Helvetica")

# Review both branches
branches = vcs.list_branches()
for branch in branches:
    print(f"{branch.name}: {branch.description}")
    history = vcs.get_history(branch.name, max_count=3)
    for v in history:
        print(f"  - {v.message}")
```

### Rollback Workflow

```python
vcs = AssetVersionControl(repo_path="./assets")

# Current state
current_branch = vcs.get_current_branch()
history = vcs.get_history(max_count=10)

# Something went wrong, find last good version
for version in history:
    if "stable" in version.metadata.get("tags", []):
        print(f"Rolling back to: {version.message}")
        vcs.restore_version(
            version_id=version.version_id,
            output_path="./working/asset.png"
        )
        break
```

## Repository Structure

```
repo_path/
├── .vaultmind_vcs/
│   ├── config.json          # Repository configuration
│   ├── versions/            # Version storage
│   │   ├── v1a2b3c4d.json  # Version metadata
│   │   ├── v1a2b3c4d.png   # Version asset
│   │   ├── v2e3f4g5h.json
│   │   └── v2e3f4g5h.png
│   └── refs/                # Branch references
└── [your assets]            # Working directory
```

## Technical Details

### Version ID Generation

Version IDs are generated using UUID4 and truncated to 12 characters:
- Format: `v{uuid4_hex[:12]}`
- Example: `v1a2b3c4d5e6f`
- Collision probability: negligible for typical use

### Checksum Computation

SHA-256 checksums are computed for:
- Change detection (has asset been modified?)
- Data integrity verification
- Deduplication opportunities

### Storage Strategy

- Each version stores both metadata (JSON) and asset copy
- Branching doesn't duplicate history - only divergent commits
- Future optimization: content-addressable storage for deduplication

### Branch Implementation

Branches are lightweight:
- Store only head pointer and metadata
- Share history with parent branch until divergence
- No filesystem changes required for branching

## Performance Considerations

### Storage Efficiency

- **Small assets** (<10MB): Minimal overhead
- **Large assets** (>100MB): Consider external storage system
- **Many versions**: Storage grows linearly with commits

### History Traversal

- Traversing history is O(n) where n = number of versions
- Max count parameter recommended for deep histories
- Consider pagination for very large repositories

### Checksum Computation

- SHA-256 is fast but depends on file size
- ~500MB/s on modern systems
- Consider caching for frequently accessed assets

## Integration with VaultMind Forge

This module integrates with:

- **forge_lineage**: Version control feeds provenance tracking
- **forge_packaging**: Package specific versions for distribution
- **forge_executor**: Track input/output versions in pipelines
- **forge_monitor**: Monitor version creation and changes
- **forge_validator**: Validate assets before committing

## Limitations

- **No merge functionality**: Branch comparison only, no auto-merge
- **No delta compression**: Each version stores full asset copy
- **No remote sync**: Local-only repository (for now)
- **Text diff not supported**: Binary-only change detection
- **No git interoperability**: Separate system from Git

## Future Enhancements

### Phase 1: Storage Optimization
- [ ] Content-addressable storage (CAS) for deduplication
- [ ] Delta compression for similar versions
- [ ] External storage adapter for large assets
- [ ] LFS-style pointer files

### Phase 2: Collaboration
- [ ] Remote repository support
- [ ] Push/pull operations
- [ ] Conflict detection
- [ ] Lock files for concurrent access

### Phase 3: Advanced Features
- [ ] Automatic merge strategies for non-conflicting changes
- [ ] Visual diff for images
- [ ] Binary diff algorithms
- [ ] Tag support for releases

### Phase 4: Integration
- [ ] Git-style hooks (pre-commit, post-commit)
- [ ] CI/CD integration
- [ ] Asset pipeline triggers
- [ ] Notification system

## Comparison with Git

| Feature | forge_versioning | Git |
|---------|------------------|-----|
| Binary assets | Optimized | Possible but inefficient |
| Branching | Yes | Yes |
| Merging | Not yet | Yes |
| Checksums | SHA-256 | SHA-1 |
| Remote sync | Planned | Yes |
| Diff | Binary comparison | Text diff |
| Storage | Full copies | Packed objects |
| Speed (large files) | Fast | Slow |
| Metadata | Rich support | Limited |

## Best Practices

### Commit Messages

Write descriptive commit messages:
```python
# Good
vcs.commit("model.obj", "Reduced poly count from 50k to 15k for mobile")

# Bad
vcs.commit("model.obj", "Updated")
```

### Branch Naming

Use descriptive branch names:
- `feature/high-poly-variant`
- `experiment/new-textures`
- `bugfix/uv-seams`

### Metadata Usage

Include relevant metadata:
```python
metadata = {
    "software": "Blender 3.6",
    "plugin_versions": {"addon_name": "1.2.0"},
    "render_settings": {...},
    "author": "jane.doe",
    "review_status": "pending"
}
```

### Regular Commits

Commit frequently at logical milestones:
- After significant changes
- Before risky experiments
- After successful iterations
- Before breaks/end of day

## Contributing

When contributing to forge_versioning, ensure:
1. Storage format remains backward compatible
2. Version ID generation stays collision-resistant
3. Checksum algorithm consistency
4. Test coverage for branch operations
5. Documentation of storage format changes

## License

Part of the VaultMind Forge project. See main repository for license details.