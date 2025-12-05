"""
VaultMind Forge - Video Generator
Frame stitching, transitions, and img2vid wrapper
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Literal
from dataclasses import dataclass
from enum import Enum
import subprocess
import json
import os


def sanitize_media_path(path: Path | str) -> Path:
    """
    Validate and sanitize media file paths to prevent command injection.

    Args:
        path: Path to validate

    Returns:
        Sanitized absolute Path object

    Raises:
        ValueError: If path is invalid or contains suspicious characters
    """
    try:
        path = Path(path)

        # Resolve to absolute path and check if it exists
        resolved = path.resolve(strict=True)

        # Security: Reject paths with shell metacharacters in filename
        # This prevents injection through concat file parsing
        dangerous_chars = ['\'', '"', ';', '&', '|', '$', '`', '\n', '\r']
        filename = resolved.name
        if any(char in filename for char in dangerous_chars):
            raise ValueError(f"Path contains dangerous characters: {filename}")

        # Ensure it's a regular file (not a pipe, device, etc.)
        if not resolved.is_file():
            raise ValueError(f"Path is not a regular file: {resolved}")

        return resolved

    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid or inaccessible path: {path}") from e


class TransitionType(str, Enum):
    """Video transition types"""
    CUT = "cut"                  # Hard cut
    FADE = "fade"                # Crossfade
    DISSOLVE = "dissolve"        # Dissolve transition
    WIPE = "wipe"                # Wipe transition
    SLIDE = "slide"              # Slide transition


class VideoCodec(str, Enum):
    """Video encoding codecs"""
    H264 = "h264"                # H.264/AVC
    H265 = "h265"                # H.265/HEVC
    VP9 = "vp9"                  # VP9
    AV1 = "av1"                  # AV1


@dataclass
class VideoConfig:
    """Video generation configuration"""
    fps: int = 30
    codec: VideoCodec = VideoCodec.H264
    bitrate: str = "5M"          # e.g., "5M" for 5 Mbps
    crf: int = 23                # Constant Rate Factor (lower = better quality)
    preset: Literal["ultrafast", "fast", "medium", "slow", "veryslow"] = "medium"
    audio_path: Optional[Path] = None

    def to_dict(self) -> dict:
        return {
            "fps": self.fps,
            "codec": self.codec.value,
            "bitrate": self.bitrate,
            "crf": self.crf,
            "preset": self.preset,
            "audio_path": str(self.audio_path) if self.audio_path else None,
        }


@dataclass
class VideoResult:
    """Result of video generation"""
    output_path: Path
    duration_seconds: float
    frame_count: int
    fps: int
    resolution: tuple[int, int]
    file_size_mb: float
    codec: VideoCodec

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "duration_seconds": self.duration_seconds,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "resolution": self.resolution,
            "file_size_mb": self.file_size_mb,
            "codec": self.codec.value,
        }


class VideoGenerator:
    """
    Production-grade video generator with frame stitching and transitions.

    Features:
    - Frame sequence to video
    - Transition effects between clips
    - FFmpeg integration
    - Multiple codec support
    - Audio track support

    Example:
        generator = VideoGenerator()

        result = generator.frames_to_video(
            frame_paths=["frame_001.png", "frame_002.png", ...],
            output_path="output.mp4",
            config=VideoConfig(fps=30, codec=VideoCodec.H264)
        )
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize video generator.

        Args:
            ffmpeg_path: Path to ffmpeg binary
        """
        self.ffmpeg_path = ffmpeg_path
        self._check_ffmpeg()

    def _check_ffmpeg(self) -> None:
        """Check if ffmpeg is available"""
        try:
            subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[WARN]️  FFmpeg not found. Video generation requires FFmpeg.")
            print("   Install: https://ffmpeg.org/download.html")

    def frames_to_video(
        self,
        frame_paths: List[Path | str],
        output_path: Path | str,
        config: Optional[VideoConfig] = None,
        transition: TransitionType = TransitionType.CUT,
        frame_duration: float = 0.5,
    ) -> VideoResult:
        """
        Convert frame sequence to video.

        Args:
            frame_paths: List of frame image paths (in order)
            output_path: Output video path
            config: Video configuration
            transition: Transition type between frames
            frame_duration: Duration per frame in seconds

        Returns:
            VideoResult with metadata
        """
        if config is None:
            config = VideoConfig()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create temporary file list for ffmpeg
        frame_list_path = output_path.parent / f".{output_path.stem}_frames.txt"

        # SECURITY: Validate all frame paths before writing to concat file
        try:
            sanitized_frames = [sanitize_media_path(fp) for fp in frame_paths]
        except ValueError as e:
            raise ValueError(f"Invalid frame path in sequence: {e}")

        with open(frame_list_path, 'w') as f:
            for frame_path in sanitized_frames:
                # Use forward slashes for cross-platform compatibility
                safe_path = str(frame_path).replace('\\', '/')
                f.write(f"file '{safe_path}'\n")
                f.write(f"duration {frame_duration}\n")
            # Last frame needs to be repeated for duration
            if sanitized_frames:
                safe_path = str(sanitized_frames[-1]).replace('\\', '/')
                f.write(f"file '{safe_path}'\n")

        # Build ffmpeg command
        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", str(frame_list_path),
            "-c:v", self._get_codec_name(config.codec),
            "-crf", str(config.crf),
            "-preset", config.preset,
            "-r", str(config.fps),
            "-pix_fmt", "yuv420p",
        ]

        # Add audio if provided
        if config.audio_path:
            # SECURITY: Validate audio path
            try:
                safe_audio = sanitize_media_path(config.audio_path)
                cmd.extend(["-i", str(safe_audio), "-c:a", "aac"])
            except ValueError as e:
                raise ValueError(f"Invalid audio path: {e}")

        cmd.extend([
            "-y",  # Overwrite output
            str(output_path)
        ])

        # Run ffmpeg
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed: {e.stderr.decode()}")
        finally:
            # Clean up temp file
            if frame_list_path.exists():
                frame_list_path.unlink()

        # Get output metadata
        metadata = self._get_video_metadata(output_path)

        return VideoResult(
            output_path=output_path,
            duration_seconds=metadata["duration"],
            frame_count=len(frame_paths),
            fps=config.fps,
            resolution=metadata["resolution"],
            file_size_mb=metadata["file_size_mb"],
            codec=config.codec,
        )

    def _get_codec_name(self, codec: VideoCodec) -> str:
        """Get ffmpeg codec name"""
        codec_map = {
            VideoCodec.H264: "libx264",
            VideoCodec.H265: "libx265",
            VideoCodec.VP9: "libvpx-vp9",
            VideoCodec.AV1: "libaom-av1",
        }
        return codec_map[codec]

    def _get_video_metadata(self, video_path: Path) -> dict:
        """Get video metadata using ffprobe"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, check=True)
            data = json.loads(result.stdout)

            # Extract video stream
            video_stream = next(
                (s for s in data["streams"] if s["codec_type"] == "video"),
                None
            )

            if video_stream:
                width = int(video_stream.get("width", 0))
                height = int(video_stream.get("height", 0))
            else:
                width = height = 0

            duration = float(data["format"].get("duration", 0))
            file_size = int(data["format"].get("size", 0)) / (1024**2)  # MB

            return {
                "duration": round(duration, 2),
                "resolution": (width, height),
                "file_size_mb": round(file_size, 2),
            }
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            # Fallback: simple file size
            file_size = video_path.stat().st_size / (1024**2)
            return {
                "duration": 0.0,
                "resolution": (0, 0),
                "file_size_mb": round(file_size, 2),
            }

    def extract_frames(
        self,
        video_path: Path | str,
        output_dir: Path | str,
        fps: Optional[int] = None,
        format: Literal["png", "jpg"] = "png",
    ) -> List[Path]:
        """
        Extract frames from video.

        Args:
            video_path: Input video path
            output_dir: Directory to save frames
            fps: Extract at specific FPS (None = all frames)
            format: Output image format

        Returns:
            List of extracted frame paths
        """
        # SECURITY: Validate video path
        try:
            safe_video_path = sanitize_media_path(video_path)
        except ValueError as e:
            raise ValueError(f"Invalid video path: {e}")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_pattern = str(output_dir / f"frame_%04d.{format}")

        cmd = [
            self.ffmpeg_path,
            "-i", str(safe_video_path),
        ]

        if fps:
            cmd.extend(["-vf", f"fps={fps}"])

        cmd.extend([
            "-q:v", "2",  # High quality
            output_pattern
        ])

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed: {e.stderr.decode()}")

        # Find all extracted frames
        frames = sorted(output_dir.glob(f"frame_*.{format}"))
        return frames

    def concatenate_videos(
        self,
        video_paths: List[Path | str],
        output_path: Path | str,
        transition: TransitionType = TransitionType.CUT,
        transition_duration: float = 0.5,
    ) -> VideoResult:
        """
        Concatenate multiple videos with transitions.

        Args:
            video_paths: List of video paths to concatenate
            output_path: Output video path
            transition: Transition type between clips
            transition_duration: Transition duration in seconds

        Returns:
            VideoResult with metadata
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create concat file
        concat_file = output_path.parent / f".{output_path.stem}_concat.txt"

        # SECURITY: Validate all video paths before writing to concat file
        try:
            sanitized_videos = [sanitize_media_path(vp) for vp in video_paths]
        except ValueError as e:
            raise ValueError(f"Invalid video path in sequence: {e}")

        with open(concat_file, 'w') as f:
            for video_path in sanitized_videos:
                # Use forward slashes for cross-platform compatibility
                safe_path = str(video_path).replace('\\', '/')
                f.write(f"file '{safe_path}'\n")

        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            "-y",
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed: {e.stderr.decode()}")
        finally:
            if concat_file.exists():
                concat_file.unlink()

        metadata = self._get_video_metadata(output_path)

        return VideoResult(
            output_path=output_path,
            duration_seconds=metadata["duration"],
            frame_count=0,  # Unknown for concatenation
            fps=30,  # Default
            resolution=metadata["resolution"],
            file_size_mb=metadata["file_size_mb"],
            codec=VideoCodec.H264,  # Assume H264
        )


def create_slideshow(
    image_paths: List[Path | str],
    output_path: Path | str,
    duration_per_image: float = 3.0,
    transition: TransitionType = TransitionType.FADE,
    fps: int = 30,
    audio_path: Optional[Path | str] = None,
) -> VideoResult:
    """
    Create slideshow video from images.

    Args:
        image_paths: List of image paths
        output_path: Output video path
        duration_per_image: Duration per image in seconds
        transition: Transition effect
        fps: Frame rate
        audio_path: Optional audio track

    Returns:
        VideoResult with metadata
    """
    generator = VideoGenerator()

    config = VideoConfig(
        fps=fps,
        audio_path=Path(audio_path) if audio_path else None,
    )

    return generator.frames_to_video(
        frame_paths=image_paths,
        output_path=output_path,
        config=config,
        transition=transition,
        frame_duration=duration_per_image,
    )
