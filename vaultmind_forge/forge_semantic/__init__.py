"""
VaultMind Forge - Semantic Module

Intelligent image downscaling with semantic preservation.

Features:
- Multi-pass downrezzing ladder for quality
- Edge and detail preservation
- Content-aware adaptive scaling
- Batch processing support
- Sharpness compensation

Example:
    from vaultmind_forge.forge_semantic import SemanticDownrezzer, DownrezMode

    downrezzer = SemanticDownrezzer(preserve_edges=True)

    result = downrezzer.downrez(
        input_path="highres.png",
        output_path="lowres.png",
        target_size=(512, 512),
        mode=DownrezMode.QUALITY
    )
"""

from __future__ import annotations

from .downrez import (
    SemanticDownrezzer,
    DownrezResult,
    DownrezMode,
    SemanticRegion,
    downrez_batch,
)

__all__ = [
    "SemanticDownrezzer",
    "DownrezResult",
    "DownrezMode",
    "SemanticRegion",
    "downrez_batch",
]

__version__ = "1.0.0"
