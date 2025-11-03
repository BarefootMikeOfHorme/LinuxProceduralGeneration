"""
VaultMind Forge - Super Resolution Module

Dual SR runner with quality comparison and automatic backend selection.

Features:
- Multiple SR backends (RealESRGAN, SwinIR, ESRGAN)
- Dual SR comparison mode
- Quality scoring and selection
- Graceful fallback to Lanczos/Bicubic
- Batch processing support

Example:
    from vaultmind_forge.forge_sr import SuperResolutionUpscaler, SRBackend

    upscaler = SuperResolutionUpscaler()

    result = upscaler.upscale(
        input_path="lowres.png",
        output_path="highres.png",
        scale_factor=4,
        backend=SRBackend.REALESRGAN
    )
"""

from __future__ import annotations

from .upscaler import (
    SuperResolutionUpscaler,
    SRResult,
    DualSRComparison,
    SRBackend,
    SRQuality,
    upscale_batch,
)

__all__ = [
    "SuperResolutionUpscaler",
    "SRResult",
    "DualSRComparison",
    "SRBackend",
    "SRQuality",
    "upscale_batch",
]

__version__ = "1.0.0"
