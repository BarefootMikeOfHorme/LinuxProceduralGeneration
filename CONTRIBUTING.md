# Contributing to VaultMind Forge

Thank you for your interest in contributing to VaultMind Forge! This document provides guidelines and instructions for contributing to the project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Documentation Standards](#documentation-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Commit Message Guidelines](#commit-message-guidelines)
8. [Pull Request Process](#pull-request-process)
9. [Module Development](#module-development)
10. [Architecture Principles](#architecture-principles)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

### Our Standards

✅ **Do:**
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

❌ **Don't:**
- Use sexualized language or imagery
- Make trolling, insulting/derogatory comments, or personal/political attacks
- Engage in public or private harassment
- Publish others' private information without permission
- Engage in other conduct which could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+ (for API server)
- CMake 3.15+ (for C++ components)
- Rust 1.70+ (for Rust validator)
- Git

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/vaultmind-forge/vaultmind-forge.git
cd vaultmind-forge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .  # Install in development mode

# Install pre-commit hooks (if using)
pre-commit install

# Build native components (optional)
cmake -B build
cmake --build build

# Run tests
pytest
```

### Repository Structure

```
vaultmind-forge/
├── vaultmind_forge/        # Python package
│   ├── forge_*/            # Individual modules
│   ├── config/             # Configuration files
│   └── native/             # C++/Rust components
├── assets/                 # Asset storage
├── docs/                   # Documentation
├── tests/                  # Test suite
└── scripts/                # Utility scripts
```

---

## Development Workflow

### 1. Create a Branch

```bash
# Feature branch
git checkout -b feature/asset-deduplication

# Bug fix branch
git checkout -b fix/validator-crash

# Documentation branch
git checkout -b docs/api-improvements
```

### Branch Naming Conventions

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `perf/` - Performance improvements

### 2. Make Changes

Follow the [Code Standards](#code-standards) and ensure your changes:
- Are focused on a single concern
- Include appropriate tests
- Update relevant documentation
- Pass all existing tests

### 3. Commit Changes

Follow [Commit Message Guidelines](#commit-message-guidelines):

```bash
git add .
git commit -m "feat(forge_intake): add multi-version asset detection"
```

### 4. Push and Create PR

```bash
git push origin feature/asset-deduplication
```

Then create a Pull Request on GitHub.

---

## Code Standards

### Python Code Style

We follow **PEP 8** with some modifications:

```python
# Good: Clear, documented, type-hinted
def convert_asset(
    filepath: Path,
    asset_id: str,
    config: Optional[Dict] = None
) -> ConversionResult:
    """
    Convert asset to VAF format.

    Args:
        filepath: Path to source asset file
        asset_id: Unique asset identifier (SHA256)
        config: Optional conversion configuration

    Returns:
        ConversionResult with status and VAF data

    Raises:
        ValueError: If filepath doesn't exist
        ConversionError: If conversion fails
    """
    if not filepath.exists():
        raise ValueError(f"File not found: {filepath}")

    # Implementation
    ...
```

#### Python Standards Checklist

✅ **Required:**
- Type hints for all function signatures
- Docstrings for all public functions/classes (Google style)
- Maximum line length: 100 characters (soft limit), 120 (hard limit)
- Use `pathlib.Path` instead of string paths
- Use f-strings for formatting
- Use dataclasses for data structures

❌ **Avoid:**
- Global mutable state
- Bare `except:` clauses
- Single-letter variable names (except loop counters)
- Wildcard imports (`from module import *`)

### C++ Code Style

```cpp
// Good: Modern C++17, clear naming
class AssetValidator {
public:
    explicit AssetValidator(const ValidatorConfig& config);

    /**
     * Validate asset against schema.
     *
     * @param asset_data JSON asset data
     * @param schema_path Path to JSON schema
     * @return ValidationResult with status and errors
     */
    ValidationResult validate(
        const nlohmann::json& asset_data,
        const std::filesystem::path& schema_path
    ) const;

private:
    ValidatorConfig config_;
    std::unique_ptr<SchemaCache> schema_cache_;
};
```

#### C++ Standards Checklist

✅ **Required:**
- Modern C++17 features
- RAII for resource management
- `const` correctness
- Smart pointers (avoid raw pointers)
- Doxygen-style comments

### JavaScript/TypeScript Code Style

```javascript
// Good: Clear, documented, modern JS
/**
 * Fetch asset lineage from API.
 *
 * @param {string} assetId - Asset identifier
 * @returns {Promise<Lineage>} Asset lineage data
 */
async function fetchAssetLineage(assetId) {
    const response = await fetch(`/api/lineage/${assetId}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch lineage: ${response.status}`);
    }
    return response.json();
}
```

---

## Documentation Standards

### Module README Structure

Every `forge_*` module must have a `README.md` following this template:

```markdown
# forge_modulename

One-line description of the module.

## Overview

Detailed description of module purpose and capabilities.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
pip install vaultmind-forge[modulename]
```

## Quick Start

```python
from vaultmind_forge.forge_modulename import MainClass

# Example usage
```

## API Reference

### `MainClass`

Description of main class.

#### Methods

##### `method_name(param1, param2)`

Description, parameters, returns, raises.

## Configuration

Configuration options and examples.

## Examples

Real-world examples.

## Architecture

How the module works internally.

## See Also

Links to related modules.
```

### Docstring Standards

Use **Google Style** docstrings:

```python
def process_asset(
    asset_path: Path,
    config: ProcessConfig,
    validate: bool = True
) -> ProcessResult:
    """
    Process asset through complete pipeline.

    This function handles the complete asset processing workflow including
    validation, conversion, metadata extraction, and lineage tracking.

    Args:
        asset_path: Path to source asset file. Must exist and be readable.
        config: Processing configuration with format options and validation rules.
        validate: Whether to validate asset before processing. Defaults to True.

    Returns:
        ProcessResult containing:
            - status: ProcessStatus enum (SUCCESS, PARTIAL, FAILED)
            - output_path: Path to processed asset (if successful)
            - metadata: Extracted asset metadata
            - warnings: List of warning messages
            - errors: List of error messages (if failed)

    Raises:
        FileNotFoundError: If asset_path doesn't exist.
        ValidationError: If validation fails and config.strict_validation is True.
        ProcessingError: If critical processing error occurs.

    Example:
        >>> config = ProcessConfig(output_format="vaf_full", validate=True)
        >>> result = process_asset(Path("model.fbx"), config)
        >>> if result.status == ProcessStatus.SUCCESS:
        ...     print(f"Processed to: {result.output_path}")

    See Also:
        - validate_asset(): Standalone validation function
        - convert_asset(): Format conversion only
        - ProcessConfig: Configuration options reference

    Note:
        Large assets (>100MB) may take several minutes to process.
        Progress can be tracked via the callback parameter.

    Warning:
        Processing modifies the asset. Always work on copies if preserving
        the original is important.
    """
```

### Documentation Checklist

✅ **Every contribution must include:**
- Updated README.md (if adding features)
- Updated CHANGELOG.md
- Docstrings for all new functions/classes
- Comments for complex logic
- Examples for new features
- Updated API documentation (if changing APIs)

---

## Testing Guidelines

### Test Structure

```python
# tests/test_forge_intake.py
import pytest
from pathlib import Path
from vaultmind_forge.forge_intake import MultiVersionHandler

class TestMultiVersionHandler:
    """Test suite for multi-version asset handling."""

    @pytest.fixture
    def handler(self):
        """Create handler instance for tests."""
        return MultiVersionHandler()

    @pytest.fixture
    def sample_assets(self, tmp_path):
        """Create sample asset files."""
        assets = []
        for ext in ['.fbx', '.obj', '.glb']:
            asset = tmp_path / f"robot{ext}"
            asset.write_text("sample data")
            assets.append(asset)
        return assets

    def test_normalize_asset_name(self, handler):
        """Test asset name normalization."""
        assert handler.normalize_asset_name("10-robot_character.fbx") == "robot_character"
        assert handler.normalize_asset_name("robot-v2.obj") == "robot"

    def test_group_asset_variants(self, handler, sample_assets):
        """Test grouping of asset variants."""
        groups = handler.group_asset_variants(sample_assets)
        assert len(groups) == 1
        assert "robot" in groups
        assert len(groups["robot"]) == 3

    def test_select_primary_variant(self, handler, sample_assets):
        """Test primary variant selection."""
        groups = handler.group_asset_variants(sample_assets)
        variants = groups["robot"]
        primary = handler.select_primary_variant(variants)
        assert primary.format == ".glb"  # Highest priority
```

### Testing Standards

✅ **Required:**
- Unit tests for all new functions
- Integration tests for workflows
- Docstring examples as doctests (when appropriate)
- Test coverage > 80% for new code
- Tests must pass on all platforms (Windows, macOS, Linux)

#### Test Naming

- `test_<function_name>` - Basic functionality test
- `test_<function_name>_<scenario>` - Specific scenario
- `test_<function_name>_raises_<exception>` - Error cases

#### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_forge_intake.py

# With coverage
pytest --cov=vaultmind_forge --cov-report=html

# Fast tests only
pytest -m "not slow"
```

---

## Commit Message Guidelines

We follow **Conventional Commits** specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Formatting, missing semicolons, etc. (no code change)
- `refactor` - Code refactoring (no functional change)
- `perf` - Performance improvement
- `test` - Adding/updating tests
- `build` - Build system or dependencies
- `ci` - CI configuration
- `chore` - Other changes (maintenance)

### Examples

```bash
# Feature
feat(forge_intake): add multi-version asset detection

Automatically groups different format versions of the same asset
(e.g., robot.fbx + robot.obj) and merges them intelligently.

Closes #42

# Bug fix
fix(validator): handle null values in JSON schema validation

The validator was crashing when encountering null values in
optional fields. Now correctly handles null as valid for
optional properties.

Fixes #123

# Documentation
docs(README): add VAF pipeline architecture diagram

Added comprehensive diagram showing asset flow through
intake, conversion, and output stages.

# Breaking change
feat(api)!: change asset ID format to SHA256

BREAKING CHANGE: Asset IDs now use SHA256 instead of MD5.
Existing asset IDs will need to be regenerated.

Migration guide: docs/MIGRATION_0.4.md
```

### Subject Line Rules

- Use imperative mood ("add" not "added" or "adds")
- Don't capitalize first letter
- No period at the end
- Maximum 72 characters
- Be specific and concise

---

## Pull Request Process

### 1. Before Creating PR

✅ **Checklist:**
- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts with main branch
- [ ] Commit messages follow guidelines
- [ ] Self-review completed

### 2. PR Template

When creating a PR, use this template:

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to break)
- [ ] Documentation update

## How Has This Been Tested?

Describe testing performed:
- Test A
- Test B

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Code commented (particularly complex areas)
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added covering changes
- [ ] All tests pass locally
- [ ] Changes generate no breaking changes (or documented if they do)

## Screenshots (if applicable)

Add screenshots for UI changes.

## Related Issues

Closes #issue_number
```

### 3. Review Process

- At least one approval required before merging
- Address all review comments
- Keep PR focused (< 400 lines preferred)
- Respond to feedback within 48 hours

### 4. After Approval

- Squash commits if needed for clean history
- Ensure CI passes
- Merge using "Squash and merge" or "Rebase and merge"

---

## Module Development

### Creating a New Module

```bash
# Create module directory
mkdir vaultmind_forge/forge_newmodule
cd vaultmind_forge/forge_newmodule

# Create files
touch __init__.py README.md

# __init__.py template
cat > __init__.py << 'EOF'
"""
VaultMind Forge - New Module
=============================

Brief description of module purpose.
"""

__version__ = "0.1.0"
__author__ = "VaultMind Forge Contributors"

from .main_class import MainClass

__all__ = ['MainClass']
EOF

# Create README.md using template above
```

### Module Checklist

✅ **Required components:**
- `__init__.py` with version and exports
- `README.md` with complete documentation
- Main implementation file(s)
- Tests in `tests/test_forge_newmodule.py`
- Schema files (if applicable) in `config/schemas/`
- Examples in `examples/forge_newmodule/`

---

## Architecture Principles

### Ceremonial Clarity

Every operation should be treated with respect:
- Clear naming
- Complete documentation
- Proper error handling
- Comprehensive logging

### Lineage Fidelity

Track all transformations:
- SHA256 hashing for asset identity
- Complete transformation history
- Parent asset references
- Timestamp all operations

### Modular Excellence

Each module should:
- Have single, clear responsibility
- Be independently testable
- Have minimal dependencies
- Export clean public API

### Native Performance

Use appropriate language for task:
- Python: High-level logic, API layer
- C++: Performance-critical operations (validation, parsing)
- Rust: Memory-safe alternatives
- JavaScript: UI and web interfaces

---

## Questions or Need Help?

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Discord**: (To be set up) For real-time chat
- **Email**: (To be set up) For private inquiries

---

## Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Project README
- Annual contributor highlights

Thank you for contributing to VaultMind Forge!
