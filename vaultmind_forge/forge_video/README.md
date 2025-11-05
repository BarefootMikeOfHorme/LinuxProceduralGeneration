# forge_video

Professional video generation and frame stitching for VaultMind Forge.

## Overview

`forge_video` provides comprehensive video generation capabilities including frame-to-video conversion, video concatenation, frame extraction, and slideshow creation. Built on top of FFmpeg, it offers production-grade encoding with multiple codec options and transition effects.

## Key Features

- **Frame Sequence to Video**: Convert image sequences to video with configurable FPS
- **Video Concatenation**: Merge multiple video clips with smooth transitions
- **Frame Extraction**: Extract frames from existing videos at any framerate
- **Multiple Codecs**: H.264, H.265, VP9, and AV1 support
- **Transition Effects**: Cut, fade, dissolve, wipe, and slide transitions
- **Audio Track Support**: Add audio to generated videos
- **Slideshow Creation**: Create slideshows from image collections
- **Quality Control**: Configurable bitrate, CRF, and encoding presets
- **FFmpeg Integration**: Leverages FFmpeg for professional-grade encoding

## Installation

### Requirements

FFmpeg must be installed and available in your system PATH.

**Install FFmpeg:**
- **Windows**: Download from https://ffmpeg.org/download.html or use `choco install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg` or `sudo yum install ffmpeg`

### Python Installation

```bash
pip install python>=3.10
```

No additional Python dependencies required.

## Quick Start

```python
from vaultmind_forge.forge_video import VideoGenerator, VideoConfig, VideoCodec
from pathlib import Path

# Initialize generator
generator = VideoGenerator()

# Get frame sequence
frames = sorted(Path("./frames").glob("*.png"))

# Create video
result = generator.frames_to_video(
    frame_paths=frames,
    output_path="output.mp4",
    config=VideoConfig(
        fps=30,
        codec=VideoCodec.H264,
        preset="medium"
    )
)

print(f"Created video: {result.output_path}")
print(f"Duration: {result.duration_seconds}s")
print(f"File size: {result.file_size_mb}MB")
```

## API Reference

### VideoGenerator

Main class for video generation and processing.

#### Constructor

```python
VideoGenerator(ffmpeg_path: str = "ffmpeg")
```

**Parameters:**
- `ffmpeg_path`: Path to ffmpeg binary (default: "ffmpeg" from PATH)

#### Methods

##### frames_to_video()

Convert image sequence to video.

**Parameters:**
- `frame_paths` (List[Path | str]): Ordered list of frame image paths
- `output_path` (Path | str): Output video file path
- `config` (VideoConfig, optional): Video encoding configuration
- `transition` (TransitionType, default=CUT): Transition effect between frames
- `frame_duration` (float, default=0.5): Duration per frame in seconds

**Returns:** VideoResult with metadata

##### extract_frames()

Extract frames from a video file.

**Parameters:**
- `video_path` (Path | str): Input video file path
- `output_dir` (Path | str): Directory to save extracted frames
- `fps` (int, optional): Extract at specific FPS (None = all frames)
- `format` (Literal["png", "jpg"], default="png"): Output image format

**Returns:** List[Path] of extracted frame paths

##### concatenate_videos()

Concatenate multiple video clips.

**Parameters:**
- `video_paths` (List[Path | str]): List of video paths to concatenate
- `output_path` (Path | str): Output video path
- `transition` (TransitionType, default=CUT): Transition between clips
- `transition_duration` (float, default=0.5): Transition duration in seconds

**Returns:** VideoResult with metadata

### VideoConfig

Video encoding configuration.

**Attributes:**
- `fps` (int, default=30): Frames per second
- `codec` (VideoCodec, default=H264): Video codec
- `bitrate` (str, default="5M"): Target bitrate (e.g., "5M" = 5 Mbps)
- `crf` (int, default=23): Constant Rate Factor (0-51, lower = better quality)
- `preset` (str, default="medium"): Encoding preset (ultrafast, fast, medium, slow, veryslow)
- `audio_path` (Path, optional): Path to audio track

### VideoCodec Enum

Supported video codecs:

- **H264**: H.264/AVC (most compatible, good quality)
- **H265**: H.265/HEVC (better compression, requires modern players)
- **VP9**: Google VP9 (royalty-free, great for web)
- **AV1**: AV1 (next-gen, best compression, slower encoding)

### TransitionType Enum

Transition effects:

- **CUT**: Hard cut (instant transition)
- **FADE**: Crossfade (smooth blend)
- **DISSOLVE**: Dissolve effect
- **WIPE**: Wipe transition
- **SLIDE**: Slide transition

*Note: Advanced transitions are placeholders - currently only CUT is fully implemented*

### VideoResult

Result object from video generation.

**Attributes:**
- `output_path` (Path): Path to generated video
- `duration_seconds` (float): Video duration
- `frame_count` (int): Number of frames
- `fps` (int): Frames per second
- `resolution` (tuple[int, int]): (width, height)
- `file_size_mb` (float): File size in megabytes
- `codec` (VideoCodec): Codec used

### Utility Functions

#### create_slideshow()

Quick slideshow creation from images.

```python
result = create_slideshow(
    image_paths=["img1.jpg", "img2.jpg"],
    output_path="slideshow.mp4",
    duration_per_image=3.0,
    transition=TransitionType.FADE,
    fps=30,
    audio_path="music.mp3"
)
```

## Usage Examples

### Basic Frame-to-Video Conversion

```python
from vaultmind_forge.forge_video import VideoGenerator, VideoConfig
from pathlib import Path

generator = VideoGenerator()

# Collect frames
frames = sorted(Path("renders").glob("frame_*.png"))

# Convert to video
result = generator.frames_to_video(
    frame_paths=frames,
    output_path="animation.mp4",
    config=VideoConfig(fps=24, preset="slow")
)
```

### High-Quality Encoding with H.265

```python
from vaultmind_forge.forge_video import VideoGenerator, VideoConfig, VideoCodec

generator = VideoGenerator()

config = VideoConfig(
    fps=60,
    codec=VideoCodec.H265,
    crf=18,  # Higher quality (lower CRF)
    preset="slow",  # Better compression
    bitrate="10M"
)

result = generator.frames_to_video(
    frame_paths=frames,
    output_path="high_quality.mp4",
    config=config
)
```

### Creating a Slideshow with Audio

```python
from vaultmind_forge.forge_video import create_slideshow, TransitionType
from pathlib import Path

images = sorted(Path("photos").glob("*.jpg"))

result = create_slideshow(
    image_paths=images,
    output_path="memories.mp4",
    duration_per_image=4.0,  # 4 seconds per image
    transition=TransitionType.FADE,
    fps=30,
    audio_path="soundtrack.mp3"
)

print(f"Slideshow created: {result.file_size_mb}MB")
```

### Extracting Frames from Video

```python
generator = VideoGenerator()

# Extract all frames
frames = generator.extract_frames(
    video_path="input_video.mp4",
    output_dir="extracted_frames",
    format="png"
)

print(f"Extracted {len(frames)} frames")

# Extract at specific FPS (e.g., 1 frame per second)
frames_1fps = generator.extract_frames(
    video_path="input_video.mp4",
    output_dir="thumbnails",
    fps=1,
    format="jpg"
)
```

### Concatenating Multiple Videos

```python
generator = VideoGenerator()

clips = [
    "intro.mp4",
    "main_content.mp4",
    "outro.mp4"
]

result = generator.concatenate_videos(
    video_paths=clips,
    output_path="final_video.mp4",
    transition=TransitionType.FADE,
    transition_duration=1.0
)
```

### Rendering Pipeline: Upscale → Video

```python
from vaultmind_forge.forge_sr import SuperResolutionUpscaler, SRBackend
from vaultmind_forge.forge_video import VideoGenerator, VideoConfig, VideoCodec
from pathlib import Path

# Step 1: Upscale frames
upscaler = SuperResolutionUpscaler()
low_res_frames = sorted(Path("frames_sd").glob("*.png"))

upscaled_dir = Path("frames_hd")
upscaled_dir.mkdir(exist_ok=True)

for frame in low_res_frames:
    upscaler.upscale(
        input_path=frame,
        output_path=upscaled_dir / frame.name,
        scale_factor=2,
        backend=SRBackend.REALESRGAN
    )

# Step 2: Create video from upscaled frames
generator = VideoGenerator()
upscaled_frames = sorted(upscaled_dir.glob("*.png"))

result = generator.frames_to_video(
    frame_paths=upscaled_frames,
    output_path="hd_video.mp4",
    config=VideoConfig(fps=30, codec=VideoCodec.H265)
)
```

### Time-lapse Creation

```python
generator = VideoGenerator()

# Capture frames over time
timelapse_frames = sorted(Path("timelapse").glob("capture_*.jpg"))

# Create fast time-lapse (e.g., 1 hour → 10 seconds)
result = generator.frames_to_video(
    frame_paths=timelapse_frames,
    output_path="timelapse.mp4",
    config=VideoConfig(
        fps=60,  # Smooth playback
        codec=VideoCodec.H264,
        preset="fast"
    ),
    frame_duration=0.016  # ~60fps effective
)
```

### Batch Video Processing

```python
generator = VideoGenerator()
input_videos = Path("raw_footage").glob("*.mp4")

# Extract frames from multiple videos
for video in input_videos:
    output_dir = Path("processed") / video.stem
    frames = generator.extract_frames(
        video_path=video,
        output_dir=output_dir,
        fps=10  # Sample at 10fps
    )
    print(f"Processed {video.name}: {len(frames)} frames")
```

### Custom Encoding Settings

```python
generator = VideoGenerator()

# Ultra-high quality for archival
archive_config = VideoConfig(
    fps=24,
    codec=VideoCodec.H265,
    crf=0,  # Lossless
    preset="veryslow",  # Maximum compression
)

# Fast encoding for preview
preview_config = VideoConfig(
    fps=24,
    codec=VideoCodec.H264,
    crf=28,  # Lower quality
    preset="ultrafast",
)

# Web-optimized
web_config = VideoConfig(
    fps=30,
    codec=VideoCodec.VP9,
    crf=31,
    preset="medium",
    bitrate="2M"  # Lower bitrate for streaming
)
```

## FFmpeg Configuration

### CRF (Constant Rate Factor) Guidelines

- **0**: Lossless (huge files)
- **17-18**: Visually lossless (very high quality)
- **23**: Default (good quality)
- **28**: Medium quality (smaller files)
- **51**: Worst quality (smallest files)

### Preset Guidelines

- **ultrafast**: Fastest encoding, largest files
- **fast**: Quick encoding, good for preview
- **medium**: Balanced (default)
- **slow**: Better compression, takes longer
- **veryslow**: Best compression, very slow

### Bitrate Guidelines

Resolution-based recommendations:
- **480p**: 1.5-2.5 Mbps
- **720p**: 3-5 Mbps
- **1080p**: 5-8 Mbps
- **4K**: 25-45 Mbps

## Performance Considerations

### Encoding Speed

Typical encoding speeds (relative to real-time):
- **H.264 (ultrafast)**: 5-10x faster
- **H.264 (medium)**: 1-3x faster
- **H.264 (veryslow)**: 0.5-1x speed
- **H.265**: 2-5x slower than H.264
- **AV1**: 10-50x slower than H.264

### Hardware Acceleration

For GPU encoding, modify FFmpeg path:
```python
# NVIDIA NVENC
generator = VideoGenerator()
# Use custom config with hardware codec
```

*Note: Hardware acceleration requires custom FFmpeg configuration*

### Memory Usage

Frame extraction memory usage:
- Depends on resolution and frame count
- ~4-8MB RAM per HD frame in memory
- Use batch processing for very long videos

## Technical Details

### FFmpeg Command Generation

The module builds FFmpeg commands like:
```bash
ffmpeg -f concat -safe 0 -i frames.txt \
  -c:v libx264 -crf 23 -preset medium \
  -r 30 -pix_fmt yuv420p \
  -y output.mp4
```

### Metadata Extraction

Uses `ffprobe` to extract:
- Video duration
- Resolution (width × height)
- File size
- Stream information

### Temporary Files

Creates temporary files during processing:
- `.{name}_frames.txt`: Frame list for concat
- `.{name}_concat.txt`: Video list for concatenation

These are automatically cleaned up after processing.

## Integration with VaultMind Forge

This module integrates with:

- **forge_sr**: Upscale frames before video generation
- **forge_semantic**: Downrez video frames for previews
- **forge_diffusion**: Generate video from diffusion model outputs
- **forge_lineage**: Track video generation provenance
- **forge_packaging**: Package videos for distribution
- **forge_versioning**: Version control for video assets

## Current Limitations

- **Transition effects**: Only CUT is fully implemented (FADE/etc are placeholders)
- **Hardware acceleration**: Not yet integrated
- **Real-time encoding**: No streaming support
- **Advanced filters**: Limited to basic FFmpeg operations
- **Subtitle support**: Not implemented
- **Multi-audio tracks**: Single audio track only

## Future Enhancements

### Phase 1: Advanced Transitions
- [ ] Implement crossfade transition
- [ ] Add dissolve effects
- [ ] Wipe and slide animations
- [ ] Custom transition curves

### Phase 2: Effects & Filters
- [ ] Color grading filters
- [ ] Stabilization
- [ ] Speed ramping (slow-mo/time-lapse)
- [ ] Text overlays

### Phase 3: Performance
- [ ] Hardware-accelerated encoding (NVENC, QuickSync, VideoToolbox)
- [ ] Multi-threaded frame processing
- [ ] Streaming output support
- [ ] Progress callbacks

### Phase 4: Advanced Features
- [ ] Multi-track audio mixing
- [ ] Subtitle support
- [ ] Scene detection
- [ ] Smart frame interpolation

## Codec Comparison

| Codec | Quality | Compression | Speed | Compatibility | Use Case |
|-------|---------|-------------|-------|---------------|----------|
| H.264 | Good | Medium | Fast | Universal | General purpose |
| H.265 | Excellent | High | Slow | Modern devices | 4K, archival |
| VP9 | Excellent | High | Medium | Web browsers | Web video |
| AV1 | Excellent | Very high | Very slow | Cutting-edge | Future-proof |

## Best Practices

### Frame Naming

Use consistent frame naming:
```
frame_0001.png
frame_0002.png
frame_0003.png
...
```

### Quality Settings

For different use cases:

**Archive/Master Copy:**
```python
VideoConfig(codec=VideoCodec.H265, crf=18, preset="veryslow")
```

**YouTube/Web:**
```python
VideoConfig(codec=VideoCodec.H264, crf=23, preset="medium", bitrate="8M")
```

**Preview/Draft:**
```python
VideoConfig(codec=VideoCodec.H264, crf=28, preset="ultrafast")
```

### Audio Sync

Ensure audio duration matches video:
- Use audio editing to trim/extend before adding
- FFmpeg will truncate longer audio automatically
- Add silence padding if audio is too short

## Troubleshooting

### "FFmpeg not found" Error

1. Install FFmpeg: https://ffmpeg.org/download.html
2. Add FFmpeg to system PATH
3. Or specify full path: `VideoGenerator(ffmpeg_path="/path/to/ffmpeg")`

### Quality Issues

- Lower CRF for better quality (try 18-20)
- Use slower preset (medium → slow → veryslow)
- Increase bitrate
- Switch to H.265 for better compression

### Large File Sizes

- Increase CRF (try 26-28)
- Use faster preset
- Lower bitrate
- Use H.265 or VP9 for better compression

### Playback Compatibility

- Stick to H.264 for maximum compatibility
- Use `yuv420p` pixel format (default)
- Test on target devices

## Contributing

When contributing to forge_video, ensure:
1. FFmpeg command compatibility across platforms
2. Proper cleanup of temporary files
3. Error handling for FFmpeg failures
4. Test with various codecs and settings
5. Documentation of new transition effects

## License

Part of the VaultMind Forge project. See main repository for license details.

**Note**: FFmpeg is licensed under LGPL/GPL. Review licensing if distributing as binary.