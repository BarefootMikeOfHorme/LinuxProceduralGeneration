# forge_sr

Production-grade super resolution (SR) upscaling for VaultMind Forge.

## Overview

`forge_sr` provides intelligent image upscaling using state-of-the-art super resolution models. It supports multiple ML backends (RealESRGAN, SwinIR, ESRGAN) with automatic fallback, dual-backend comparison for quality optimization, and tile-based processing for large images.

## Key Features

- **Multiple SR Backends**: RealESRGAN, SwinIR, ESRGAN with automatic detection
- **Dual SR Comparison**: Run two backends simultaneously and auto-select the best result
- **Quality Scoring**: Automatic quality assessment using sharpness metrics
- **Graceful Fallback**: Falls back to Lanczos/Bicubic if ML models unavailable
- **Tile-Based Processing**: Handle extremely large images with configurable tiling
- **Batch Processing**: Efficiently process multiple images with consistent settings
- **Flexible Scaling**: Support for 2x, 4x, and 8x upscaling factors
- **Backend Detection**: Automatically detects available ML frameworks

## Installation

### Basic Installation (PIL fallback only)

```bash
pip install pillow numpy
```

### With ML Backends

For RealESRGAN (recommended):
```bash
pip install realesrgan basicsr torch torchvision
```

For SwinIR:
```bash
pip install timm torch torchvision
```

For full support:
```bash
pip install realesrgan basicsr timm torch torchvision
```

## Quick Start

```python
from vaultmind_forge.forge_sr import SuperResolutionUpscaler, SRBackend

# Create upscaler
upscaler = SuperResolutionUpscaler(
    tile_size=512,
    tile_overlap=32,
    enable_fallback=True
)

# Upscale an image
result = upscaler.upscale(
    input_path="lowres.png",
    output_path="highres.png",
    scale_factor=4,
    backend=SRBackend.REALESRGAN
)

print(f"Upscaled from {result.original_size} to {result.upscaled_size}")
print(f"Processing time: {result.processing_time_ms}ms")
```

## API Reference

### SuperResolutionUpscaler

Main class for image super resolution.

#### Constructor Parameters

- **tile_size** (int, default=512): Tile size for processing large images
- **tile_overlap** (int, default=32): Overlap between tiles to prevent seams
- **enable_fallback** (bool, default=True): Enable fallback to Lanczos if backends unavailable

#### Methods

##### upscale()

Upscale image using specified SR backend.

**Parameters:**
- `input_path` (Path | str): Path to input image
- `output_path` (Path | str): Path to save upscaled image
- `scale_factor` (int, default=4): Upscaling factor (2, 4, or 8)
- `backend` (SRBackend, default=REALESRGAN): SR backend to use

**Returns:** SRResult with metadata

##### upscale_dual()

Run two SR backends and compare results.

**Parameters:**
- `input_path` (Path | str): Path to input image
- `output_dir` (Path | str): Directory to save both outputs
- `scale_factor` (int, default=4): Upscaling factor
- `primary_backend` (SRBackend, default=REALESRGAN): Primary SR backend
- `secondary_backend` (SRBackend, default=FALLBACK_LANCZOS): Secondary backend
- `select_best` (bool, default=True): Automatically select best result

**Returns:** DualSRComparison with both results and winner

### SRBackend Enum

Available SR backends:

- **REALESRGAN**: RealESRGAN-x4plus (high quality, balanced speed)
- **ESRGAN**: Enhanced SRGAN (classic model)
- **SWIN**: SwinIR (transformer-based, very high quality)
- **FALLBACK_LANCZOS**: Lanczos resampling (fast, no ML required)
- **FALLBACK_BICUBIC**: Bicubic interpolation (fastest, lowest quality)

### SRQuality Enum

Quality presets (future use):

- **FAST**: 2x upscale, fast models
- **BALANCED**: 2x-4x upscale, balanced quality/speed
- **QUALITY**: 4x upscale, best models
- **ULTRA**: 4x+ upscale, maximum quality

### SRResult

Result object containing:
- `output_path`: Path to saved image
- `original_size`: Original (width, height)
- `upscaled_size`: Final (width, height)
- `scale_factor`: Upscaling factor applied
- `backend_used`: Backend that was used
- `processing_time_ms`: Processing time in milliseconds
- `quality_score`: Optional quality score (0-1)

### DualSRComparison

Dual SR comparison result:
- `primary_result`: Result from primary backend
- `secondary_result`: Result from secondary backend
- `winner`: Best result based on quality score
- `quality_difference`: Difference between scores
- `comparison_method`: Method used for comparison

### Utility Functions

#### upscale_batch()

Batch process multiple images.

```python
results = upscale_batch(
    input_paths=["img1.png", "img2.png"],
    output_dir="./output",
    scale_factor=4,
    backend=SRBackend.REALESRGAN
)
```

## Usage Examples

### Basic Upscaling

```python
from vaultmind_forge.forge_sr import SuperResolutionUpscaler, SRBackend

upscaler = SuperResolutionUpscaler()

# 4x upscale with RealESRGAN
result = upscaler.upscale(
    input_path="photo.jpg",
    output_path="photo_4x.jpg",
    scale_factor=4,
    backend=SRBackend.REALESRGAN
)
```

### Dual Backend Comparison

```python
upscaler = SuperResolutionUpscaler()

# Compare RealESRGAN vs SwinIR
comparison = upscaler.upscale_dual(
    input_path="lowres.png",
    output_dir="./comparison",
    scale_factor=4,
    primary_backend=SRBackend.REALESRGAN,
    secondary_backend=SRBackend.SWIN,
    select_best=True
)

print(f"Winner: {comparison.winner.backend_used.value}")
print(f"Quality difference: {comparison.quality_difference}")
print(f"Winner saved at: {comparison.winner.output_path}")
```

### Fallback Mode

```python
# Automatically fallback to Lanczos if ML models unavailable
upscaler = SuperResolutionUpscaler(enable_fallback=True)

result = upscaler.upscale(
    input_path="image.png",
    output_path="upscaled.png",
    scale_factor=2,
    backend=SRBackend.REALESRGAN  # Will fallback if not available
)

print(f"Used backend: {result.backend_used.value}")
```

### Batch Processing

```python
from vaultmind_forge.forge_sr import upscale_batch, SRBackend
from pathlib import Path

# Find all images
image_files = list(Path("./input").glob("*.jpg"))

# Batch upscale
results = upscale_batch(
    input_paths=image_files,
    output_dir="./upscaled",
    scale_factor=4,
    backend=SRBackend.REALESRGAN,
    tile_size=512,
    enable_fallback=True
)

# Print summary
total_time = sum(r.processing_time_ms for r in results)
print(f"Processed {len(results)} images in {total_time:.0f}ms")
print(f"Average: {total_time/len(results):.0f}ms per image")
```

### Large Image with Tiling

```python
# Configure for very large images
upscaler = SuperResolutionUpscaler(
    tile_size=512,      # Process in 512x512 tiles
    tile_overlap=64,    # 64px overlap to prevent seams
    enable_fallback=True
)

# Process 8K image
result = upscaler.upscale(
    input_path="8k_photo.png",
    output_path="8k_upscaled.png",
    scale_factor=2,
    backend=SRBackend.REALESRGAN
)
```

### Quality Comparison Pipeline

```python
# Create comparison for quality analysis
import json

upscaler = SuperResolutionUpscaler()

comparison = upscaler.upscale_dual(
    input_path="test_image.png",
    output_dir="./quality_test",
    scale_factor=4,
    primary_backend=SRBackend.REALESRGAN,
    secondary_backend=SRBackend.FALLBACK_LANCZOS,
    select_best=True
)

# Export comparison metadata
metadata = comparison.to_dict()
with open("quality_test/comparison.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"Primary ({metadata['primary']['backend']}): {metadata['primary']['quality_score']}")
print(f"Secondary ({metadata['secondary']['backend']}): {metadata['secondary']['quality_score']}")
print(f"Winner: {metadata['winner_backend']}")
```

## Performance Considerations

### Backend Selection

- **RealESRGAN**: Best overall balance of quality and speed (recommended)
- **SwinIR**: Highest quality but slower, best for single images
- **ESRGAN**: Classic model, good quality, moderate speed
- **Lanczos**: Fast fallback, decent quality for <2x upscaling
- **Bicubic**: Fastest fallback, acceptable for small scale factors

### Tile Size Guidelines

- **256**: Very large images (>16K), GPU memory constrained
- **512**: Default, good balance for most images
- **1024**: High-end GPUs, faster processing for large images
- **No tiling**: Small images (<2K pixels) don't need tiling

### Memory Usage

Approximate VRAM requirements (4x upscale):
- **512x512 tile**: ~2GB VRAM
- **1024x1024 tile**: ~4GB VRAM
- **Full image**: Width × Height × 4 × bytes_per_pixel

### Speed Optimization

1. Use lower scale factors when possible (2x is ~4x faster than 4x)
2. Enable fallback mode to avoid failures
3. Batch processing amortizes model loading overhead
4. Consider Lanczos for near-real-time applications

## Technical Details

### Quality Scoring

The `_compute_quality_score()` method uses Laplacian variance (sharpness metric):
1. Convert image to grayscale
2. Apply Laplacian filter to detect edges
3. Compute variance of filter response
4. Normalize to [0, 1] range

Higher scores indicate sharper, more detailed images.

### Dual SR Workflow

1. Load input image
2. Run primary backend (e.g., RealESRGAN)
3. Run secondary backend (e.g., Lanczos)
4. Compute quality scores for both
5. Select winner based on higher score
6. Return comparison with both results

### Tile-Based Processing

For large images:
1. Divide image into overlapping tiles
2. Process each tile with SR model
3. Blend overlapping regions to prevent seams
4. Merge tiles back into full image

*Note: Current implementation is placeholder - full tiling logic pending*

### Backend Detection

On initialization, checks for:
- `realesrgan` package → enables REALESRGAN backend
- `basicsr` package → enables ESRGAN backend
- `timm` package → enables SwinIR backend
- PIL always available → enables fallback backends

## Integration with VaultMind Forge

This module integrates with:

- **forge_semantic**: Upscale after semantic downrezzing for quality testing
- **forge_diffusion**: Generate high-res images from diffusion outputs
- **forge_video**: Upscale video frames for HD/4K output
- **forge_validator**: Quality metrics for SR validation
- **forge_packaging**: Prepare assets at multiple resolutions

## Current Limitations

- **Model inference is placeholder**: Current implementation uses Lanczos fallback
- **No actual tiling logic**: Tile parameters accepted but not yet implemented
- **Basic quality metric**: Simple sharpness score, not perceptual quality
- **CPU-only**: No GPU acceleration implemented yet
- **Limited format support**: Only PIL-supported formats

## Production Roadmap

### Phase 1: Model Integration
- [ ] Integrate RealESRGAN inference
- [ ] Add SwinIR model support
- [ ] Implement ESRGAN backend
- [ ] Add model weight management

### Phase 2: Performance
- [ ] Implement tile-based processing
- [ ] Add GPU acceleration
- [ ] Optimize memory usage
- [ ] Multi-threading for batch processing

### Phase 3: Quality
- [ ] Advanced quality metrics (LPIPS, SSIM)
- [ ] Perceptual quality scoring
- [ ] Face-aware upscaling
- [ ] Text preservation

### Phase 4: Features
- [ ] Video frame upscaling
- [ ] Real-time mode for streams
- [ ] Custom model training
- [ ] Progressive upscaling

## Model Resources

### RealESRGAN
- GitHub: https://github.com/xinntao/Real-ESRGAN
- Models: RealESRGAN-x4plus, RealESRGAN_x4plus_anime
- Best for: Photos, general content

### SwinIR
- GitHub: https://github.com/JingyunLiang/SwinIR
- Models: Multiple variants (classical, lightweight, real-world)
- Best for: Maximum quality, fine details

### ESRGAN
- GitHub: https://github.com/xinntao/BasicSR
- Models: ESRGAN, ESRGAN-DF2K
- Best for: Classic SR tasks, balanced quality

## Contributing

When contributing to forge_sr, ensure:
1. Model integrations include proper attribution and licensing
2. Performance benchmarks for new backends
3. Memory profiling for large images
4. Quality comparisons against existing backends
5. Documentation of model requirements and installation

## License

Part of the VaultMind Forge project. See main repository for license details.

**Note**: ML models (RealESRGAN, SwinIR, ESRGAN) have their own licenses - review before commercial use.