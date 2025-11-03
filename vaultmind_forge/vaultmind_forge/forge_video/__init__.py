"""
VaultMind Forge - Video Module

Frame stitching, transitions, and video generation with FFmpeg.

Features:
- Frame sequence to video conversion
- Video concatenation with transitions
- Frame extraction from video
- Multiple codec support (H.264, H.265, VP9, AV1)
- Audio track support
- Slideshow creation

Example:
    from vaultmind_forge.forge_video import VideoGenerator, VideoConfig, VideoCodec

    generator = VideoGenerator()

    result = generator.frames_to_video(
        frame_paths=["frame_001.png", "frame_002.png"],
        output_path="output.mp4",
        config=VideoConfig(fps=30, codec=VideoCodec.H264)
    )
"""

from __future__ import annotations

from .generator import (
    VideoGenerator,
    VideoConfig,
    VideoResult,
    TransitionType,
    VideoCodec,
    create_slideshow,
)

__all__ = [
    "VideoGenerator",
    "VideoConfig",
    "VideoResult",
    "TransitionType",
    "VideoCodec",
    "create_slideshow",
]

__version__ = "1.0.0"
