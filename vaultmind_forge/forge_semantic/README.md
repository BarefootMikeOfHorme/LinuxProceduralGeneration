# forge_semantic

Intelligent image downscaling with semantic preservation for VaultMind Forge.

## Overview

`forge_semantic` provides advanced image downrezzing (downscaling) capabilities that preserve important visual details such as edges, faces, and text. Unlike simple resizing, semantic downrezzing uses multi-pass algorithms and content-aware techniques to maintain image quality at lower resolutions.

## Key Features

- **Multi-Pass Downrezzing Ladder**: Stepwise scaling through intermediate resolutions for superior quality
- **Edge Preservation**: Detects and enhances edges to prevent blur and maintain sharpness
- **Content-Aware Scaling**: Automatically adjusts processing based on image characteristics
- **Multiple Quality Modes**: Fast, Balanced, Quality, and Adaptive modes for different use cases
- **Batch Processing**: Process multiple images efficiently with consistent settings
- **Sharpness Compensation**: Configurable post-processing to counteract downscaling blur
- **Region Protection**: Optional face and text detection for priority preservation
- **Metadata Tracking**: Detailed results including processing time and applied optimizations

## Installation

```bash
pip install pillow numpy
```

## Quick Start

```python
from vaultmind_forge.forge_semantic import SemanticDownrezzer, DownrezMode

# Create downrezzer with default settings
downrezzer = SemanticDownrezzer(
    preserve_edges=True,
    sharpness_compensation=1.1
)

# Downscale an image
result = downrezzer.downrez(
    input_path="highres.png",
    output_path="lowres.png",
    target_size=(512, 512),
    mode=DownrezMode.QUALITY
)

print(f"Processed in {result.processing_time_ms}ms")
print(f"Scale factor: {result.scale_factor}")
```

## API Reference

### SemanticDownrezzer

Main class for intelligent image downscaling.

#### Constructor Parameters

- **preserve_edges** (bool, default=True): Apply edge-preserving filters
- **preserve_faces** (bool, default=True): Detect and preserve face regions
- **preserve_text** (bool, default=False): Detect and preserve text regions
- **sharpness_compensation** (float, default=1.1): Sharpening factor (1.0=none, >1.0=sharpen)

#### Methods

##### downrez()

Downscale an image with semantic preservation.

**Parameters:**
- `input_path` (Path | str): Path to input image
- `output_path` (Path | str): Path to save downrezzed image
- `target_size` (Tuple[int, int], optional): Target (width, height) in pixels
- `scale_factor` (float, optional): Alternative to target_size (e.g., 0.5 = 50%)
- `mode` (DownrezMode, default=BALANCED): Processing mode

**Returns:** DownrezResult with metadata

##### create_downrez_ladder()

Create multiple downrezzed versions at different sizes.

**Parameters:**
- `input_path` (Path | str): Path to input image
- `output_dir` (Path | str): Directory to save versions
- `sizes` (List[Tuple[int, int]]): List of (width, height) tuples
- `naming_template` (str): Template for output filenames

**Returns:** List[DownrezResult]

### DownrezMode Enum

Processing modes with quality/speed tradeoffs:

- **FAST**: Simple Lanczos resampling (fastest)
- **BALANCED**: Multi-pass with edge preservation (recommended)
- **QUALITY**: Semantic-aware with detail preservation (best quality)
- **ADAPTIVE**: Automatically choose based on image content

### DownrezResult

Result object containing:
- `output_path`: Path to saved image
- `original_size`: Original (width, height)
- `downrezzed_size`: Final (width, height)
- `scale_factor`: Actual scale ratio applied
- `mode_used`: Processing mode that was used
- `processing_time_ms`: Processing time in milliseconds
- `preserved_regions`: List of semantic regions preserved

### Utility Functions

#### downrez_batch()

Batch process multiple images with the same settings.

```python
results = downrez_batch(
    input_paths=["img1.png", "img2.png"],
    output_dir="./output",
    target_size=(512, 512),
    mode=DownrezMode.BALANCED
)
```

## Usage Examples

### Basic Downscaling

```python
from vaultmind_forge.forge_semantic import SemanticDownrezzer

downrezzer = SemanticDownrezzer()
result = downrezzer.downrez(
    input_path="image.png",
    output_path="small.png",
    scale_factor=0.5  # 50% of original size
)
```

### Create Multiple Sizes (Responsive Images)

```python
downrezzer = SemanticDownrezzer()

results = downrezzer.create_downrez_ladder(
    input_path="original.png",
    output_dir="./thumbnails",
    sizes=[
        (1920, 1080),  # Full HD
        (1280, 720),   # HD
        (640, 480),    # SD
        (320, 240),    # Thumbnail
    ]
)

for result in results:
    print(f"{result.downrezzed_size}: {result.processing_time_ms}ms")
```

### Adaptive Mode with Face Preservation

```python
downrezzer = SemanticDownrezzer(
    preserve_edges=True,
    preserve_faces=True,
    sharpness_compensation=1.2
)

result = downrezzer.downrez(
    input_path="portrait.jpg",
    output_path="portrait_small.jpg",
    target_size=(512, 512),
    mode=DownrezMode.ADAPTIVE
)
```

### Batch Processing

```python
from vaultmind_forge.forge_semantic import downrez_batch, DownrezMode
from pathlib import Path

image_files = list(Path("./images").glob("*.png"))

results = downrez_batch(
    input_paths=image_files,
    output_dir="./output",
    scale_factor=0.5,
    mode=DownrezMode.QUALITY,
    preserve_edges=True,
    sharpness_compensation=1.15
)

print(f"Processed {len(results)} images")
```

### Custom Pipeline Integration

```python
# Process and get metadata for tracking
result = downrezzer.downrez(
    input_path="input.png",
    output_path="output.png",
    target_size=(768, 768),
    mode=DownrezMode.QUALITY
)

# Export metadata
metadata = result.to_dict()
print(f"Original: {metadata['original_size']}")
print(f"Downrezzed: {metadata['downrezzed_size']}")
print(f"Preserved: {metadata['preserved_regions']}")
```

## Performance Considerations

### Mode Selection Guidelines

- **FAST**: Use for scale factors > 0.75 or when speed is critical
- **BALANCED**: Default for most use cases, good quality/speed ratio
- **QUALITY**: Use for large images (>1MP) or critical visual content
- **ADAPTIVE**: Let the system choose based on image characteristics

### Multi-Pass Ladder

The multi-pass approach processes images through intermediate sizes (e.g., 1024→768→512 instead of 1024→512 directly). This preserves more detail but takes longer.

### Memory Usage

Processing is done in-memory. Large images or batch operations may require significant RAM. Consider processing in smaller batches if memory is constrained.

## Technical Details

### Algorithms

1. **Lanczos Resampling**: Base resampling algorithm with 3-lobe filter
2. **Multi-Pass Downrezzing**: Stepwise scaling at 50% intervals
3. **Edge Detection**: PIL FIND_EDGES filter with selective blending
4. **Sharpness Enhancement**: Unsharp mask with configurable radius

### Semantic Regions

The module supports preservation priorities for:
- **FACE**: Facial features (future: ML-based detection)
- **EYES**: Eye regions within faces
- **TEXT**: Readable text content
- **EDGES**: High-contrast boundaries
- **BACKGROUND**: Lower-priority regions

## Integration with VaultMind Forge

This module integrates with the broader VaultMind Forge ecosystem:

- **forge_diffusion**: Prepare training images at multiple resolutions
- **forge_sr**: Generate ground truth low-res images for super-resolution
- **forge_video**: Create efficient video thumbnails and previews
- **forge_packaging**: Optimize assets for distribution

## Limitations

- Face and text detection are currently simplified placeholders
- Edge preservation uses basic filter approach (could be enhanced with ML)
- No GPU acceleration (CPU-only PIL processing)
- Limited to common image formats supported by PIL

## Future Enhancements

- ML-based semantic segmentation for face/text detection
- GPU acceleration via PyTorch or CUDA
- Perceptual quality metrics (SSIM, LPIPS) for adaptive mode
- Support for HDR and wide-gamut color spaces
- Incremental processing for extremely large images

## Contributing

When contributing to forge_semantic, ensure:
1. All new features include docstrings and examples
2. Performance benchmarks for new algorithms
3. Test coverage for edge cases (very small/large images, unusual aspect ratios)
4. Compatibility with PIL image modes (RGB, RGBA, L, etc.)

## License

Part of the VaultMind Forge project. See main repository for license details.