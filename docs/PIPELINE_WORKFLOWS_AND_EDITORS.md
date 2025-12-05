# VaultMind Forge - Pipeline Workflows and Editor Requirements

**Date**: 2025-12-04
**Purpose**: Complete workflow analysis and editor recommendations for all pipelines

---

## Executive Summary

VaultMind Forge has 7 major pipelines for asset generation and processing. Each pipeline needs built-in viewers/editors so users can verify and adjust AI-generated content before export. This document maps complete workflows and recommends free/open-source Python libraries for building integrated editors.

**Key Finding**: Currently, all pipelines generate assets but lack built-in viewing/editing capabilities. Users have no way to verify or adjust output within VaultMind Forge.

---

## 1. FORGE_DIFFUSION (Image Generation Pipeline)

### Complete Workflow

```
INPUT → CONFIGURATION → GENERATION → VALIDATION → EDITING → EXPORT
```

### Detailed Steps

**1. Input Stage**
- Text prompts (positive/negative)
- Optional: ControlNet images (depth, canny, pose, normal maps)
- Optional: Reference images for IP-Adapter
- Configuration: resolution, steps, guidance scale, seed

**2. Processing Stage**
- A-pose canonicalization (if using ControlNet)
- Helper pass generation (depth maps, edge detection, pose extraction)
- Base SDXL generation
- Optional: Refiner pass (enhancement)
- Multi-pass generation with validation scoring

**3. Validation Stage**
- Image quality metrics (sharpness, noise, artifacts)
- Prompt adherence scoring
- Multi-pass comparison and selection
- Metadata collection

**4. Editing Needs** (CURRENTLY MISSING)
- **Image Viewer**: Quick preview of generated images
- **Comparison View**: Side-by-side comparison of multi-pass results
- **Inpainting Editor**: Fix artifacts, modify regions
- **Prompt Refinement**: Visual prompt editor with suggestions

**5. Export Stage**
- Save to organized directory structure
- Metadata embedding (prompts, seeds, parameters)
- Multiple format support (PNG, JPG, WebP)

### Recommended Editors

**Essential Editor**: Image Viewer/Comparator
- View generated images immediately after generation
- Compare multiple generations side-by-side
- Basic editing (crop, brightness, contrast)
- Inpainting for artifact removal

**Recommended Python Libraries**:
- **Pillow (PIL)**: Core image manipulation, viewing, format conversion
- **opencv-python (cv2)**: Advanced editing, inpainting, filters
- **PyQt5/PySide6**: Full-featured GUI for image editing
- **matplotlib**: Quick image display and comparison views
- **napari**: Advanced image viewer with layers and annotations
- **gradio**: Quick web-based image viewer/editor

---

## 2. FORGE_VIDEO (Video Generation Pipeline)

### Complete Workflow

```
FRAMES → VALIDATION → EDITING → STITCHING → ENCODING → EXPORT
```

### Detailed Steps

**1. Input Stage**
- Image sequence (from diffusion or other sources)
- Frame duration settings
- Transition types (cut, fade, dissolve)
- Optional: Audio track

**2. Processing Stage**
- Frame validation and sanitization
- Transition generation
- FFmpeg encoding pipeline
- Audio synchronization

**3. Validation Stage**
- Frame consistency checks
- Resolution validation
- File format verification

**4. Editing Needs** (CURRENTLY MISSING)
- **Video Player**: Preview generated videos
- **Timeline Editor**: Adjust frame durations, transitions
- **Frame Editor**: Edit individual frames before stitching
- **Audio Editor**: Trim, adjust audio tracks

**5. Export Stage**
- Multiple codec support (H264, H265, VP9, AV1)
- Quality presets (fast, balanced, quality, ultra)
- Metadata embedding

### Recommended Editors

**Essential Editors**:
1. **Video Player**: Immediate playback of generated videos
2. **Timeline Editor**: Adjust frame timing and transitions
3. **Frame Extractor**: Export/edit individual frames

**Recommended Python Libraries**:
- **opencv-python (cv2)**: Video reading, frame extraction, basic editing
- **moviepy**: High-level video editing, transitions, effects
- **PyQt5 + QMediaPlayer**: Video playback widget
- **ffmpeg-python**: Python wrapper for FFmpeg operations
- **imageio**: Simple video I/O
- **PyAV**: Pythonic bindings for FFmpeg/Libav

---

## 3. FORGE_3D (3D Mesh Generation Pipeline)

### Complete Workflow

```
IMAGE → CANONICALIZATION → MULTIVIEW → RECONSTRUCTION → REFINEMENT → EXPORT
```

### Detailed Steps

**1. Input Stage**
- Reference image (character/object concept art)
- Configuration: A-pose conversion, semantic decomposition, refinement options

**2. Processing Stages**
- **Stage 1**: A-pose conversion (arbitrary pose → canonical pose)
- **Stage 2**: Multi-view generation (4+ viewpoints + normal maps)
- **Stage 3**: 3D reconstruction with semantic decomposition (body, clothes, hair)
- **Stage 4**: Mesh refinement and texture back-projection

**3. Validation Stage** (NEEDS IMPLEMENTATION)
- Mesh topology validation
- UV map quality checks
- Texture consistency
- Semantic segmentation verification

**4. Editing Needs** (CURRENTLY MISSING)
- **3D Viewer**: Rotate, zoom, inspect generated meshes
- **Mesh Editor**: Adjust vertices, fix topology issues
- **Material Editor**: Assign/edit PBR materials
- **UV Editor**: Adjust texture mapping
- **Multi-component View**: View body/clothes/hair separately

**5. Export Stage**
- Multiple format support (OBJ, FBX, GLB, USD)
- Semantic components export (separate meshes)
- Texture map export

### Recommended Editors

**Essential Editors**:
1. **3D Viewer**: Interactive mesh inspection
2. **Component Viewer**: View semantic parts (body, clothes, hair)
3. **Material Inspector**: Preview PBR materials

**Recommended Python Libraries**:
- **trimesh**: Mesh loading, manipulation, analysis
- **Open3D**: 3D visualization, editing, processing
- **PyVista**: 3D visualization and mesh analysis
- **PyMeshLab**: Interface to MeshLab operations
- **PyQt5 + PyOpenGL**: Custom 3D viewers
- **pythreejs**: 3D visualization in Jupyter notebooks
- **vispy**: High-performance 3D visualization

---

## 4. FORGE_PROCEDURAL (Procedural Generation Pipeline)

### Complete Workflow

```
CONFIG → NOISE GENERATION → PROCESSING → VALIDATION → EDITING → EXPORT
```

### Detailed Steps

**1. Input Stage**
- Preset selection (clouds, marble, wood, mountains, etc.)
- Or custom parameters (noise type, octaves, scale, frequency)
- Size, seed, variation count

**2. Processing Stage**
- Rust-powered noise generation (25x faster than Python)
- FBM heightmap generation
- Texture synthesis
- Variation generation with reproducible seeds

**3. Validation Stage**
- Pattern quality checks
- Seamless tiling verification
- Statistical analysis

**4. Editing Needs** (CURRENTLY MISSING)
- **Texture Preview**: Real-time preview with parameter adjustment
- **Heightmap Visualizer**: 3D preview of terrain heightmaps
- **Tiling Tester**: Verify seamless tiling
- **Parameter Editor**: Visual sliders for all noise parameters
- **Batch Viewer**: Compare multiple variations

**5. Export Stage**
- Auto-organized directory structure (158 endpoints)
- Multiple formats (PNG, TGA, EXR for heightmaps)
- 16-bit heightmaps for precision

### Recommended Editors

**Essential Editors**:
1. **Real-time Preview**: Live parameter adjustment with instant feedback
2. **Heightmap 3D Viewer**: Terrain preview
3. **Tiling Tester**: Verify seamless patterns

**Recommended Python Libraries**:
- **Pillow (PIL)**: Image display and manipulation
- **matplotlib**: 2D texture preview, heightmap visualization
- **PyQt5/PySide6**: Parameter sliders, real-time preview
- **napari**: Multi-layer texture viewer
- **vispy**: 3D heightmap visualization
- **imgui**: Immediate mode GUI for parameter tweaking

---

## 5. FORGE_SR (Super Resolution Upscaling Pipeline)

### Complete Workflow

```
LOWRES INPUT → DUAL SR → QUALITY SCORING → SELECTION → EXPORT
```

### Detailed Steps

**1. Input Stage**
- Low-resolution image
- Scale factor (2x, 4x, 8x)
- Backend selection (ESRGAN, SwinIR, RealESRGAN, or fallback)

**2. Processing Stage**
- Tile-based processing for large images
- Dual backend comparison mode
- Model inference or fallback (Bicubic/Lanczos)

**3. Validation Stage**
- Quality scoring (sharpness metrics)
- LPIPS/SSIM comparison (if available)
- Automatic best selection

**4. Editing Needs** (CURRENTLY MISSING)
- **Comparison Viewer**: Before/after side-by-side
- **Zoom Inspector**: Pixel-level comparison
- **Dual Result Viewer**: Compare two SR backends
- **Quality Metrics Dashboard**: Visual quality scores
- **Touch-up Editor**: Fix remaining artifacts

**5. Export Stage**
- High-quality output (quality=95)
- Metadata with processing info
- Batch processing support

### Recommended Editors

**Essential Editors**:
1. **Before/After Viewer**: Interactive comparison slider
2. **Zoom Inspector**: 100%/200%/400% comparison
3. **Dual Backend Comparator**: Compare ESRGAN vs SwinIR

**Recommended Python Libraries**:
- **Pillow (PIL)**: Image loading, basic editing
- **opencv-python (cv2)**: Advanced image processing
- **matplotlib**: Side-by-side comparison plots
- **PyQt5/PySide6**: Interactive before/after slider
- **napari**: Multi-layer image comparison
- **gradio**: Web-based comparison interface

---

## 6. FORGE_SEMANTIC (Semantic Downscaling Pipeline)

### Complete Workflow

```
HIGHRES INPUT → SEMANTIC ANALYSIS → MULTI-PASS DOWNSCALING → SHARPENING → EXPORT
```

### Detailed Steps

**1. Input Stage**
- High-resolution image
- Target size or scale factor
- Mode selection (fast, balanced, quality, adaptive)
- Preservation options (edges, faces, text)

**2. Processing Stage**
- Content analysis (auto-mode selection)
- Multi-pass ladder downscaling (50% steps)
- Edge preservation filtering
- Sharpness compensation

**3. Validation Stage**
- Detail preservation metrics
- Edge quality checks
- Semantic region validation

**4. Editing Needs** (CURRENTLY MISSING)
- **Comparison Viewer**: Compare downscaling modes
- **Region Selector**: Mark areas to preserve
- **Detail Inspector**: Verify edge/face preservation
- **Ladder Visualizer**: Show multi-pass progression
- **Sharpness Adjuster**: Fine-tune sharpening

**5. Export Stage**
- Downscaling ladder creation (multiple sizes)
- High-quality output with optimization
- Metadata preservation

### Recommended Editors

**Essential Editors**:
1. **Mode Comparator**: Compare fast/balanced/quality/adaptive
2. **Region Marker**: Highlight areas to preserve
3. **Multi-resolution Viewer**: View all ladder sizes

**Recommended Python Libraries**:
- **Pillow (PIL)**: Core image operations
- **opencv-python (cv2)**: Edge detection, face detection
- **matplotlib**: Comparison visualizations
- **PyQt5/PySide6**: Region selection tools
- **napari**: Multi-resolution viewer
- **scikit-image**: Advanced image processing metrics

---

## 7. FORGE_CONVERTER (Format Conversion Pipeline)

### Complete Workflow

```
SOURCE ASSET → TYPE DETECTION → ENGINE-SPECIFIC CONVERSION → OPTIMIZATION → VALIDATION → EXPORT
```

### Detailed Steps

**1. Input Stage**
- Source asset (3D model, texture, animation, audio)
- Target engine (Unity, Unreal, Godot, Web, Blender)
- Conversion profile (quality, balanced, optimized)
- Options (LODs, compression, optimization)

**2. Processing Stage**
- Asset type detection (by extension)
- Engine-specific conversion rules
- LOD generation (3-5 levels)
- Texture compression (BC1, BC7, etc.)
- Mesh decimation (conservative, moderate, aggressive)

**3. Validation Stage**
- Format compatibility checks
- File size comparison
- Optimization verification

**4. Editing Needs** (CURRENTLY MISSING)
- **Asset Previewer**: View source/converted assets
- **Material Editor**: Adjust material conversion
- **LOD Inspector**: Preview all LOD levels
- **Texture Compressor**: Visual compression settings
- **Batch Converter UI**: Drag-drop conversion interface

**5. Export Stage**
- Engine-specific directory structure
- Batch conversion support
- Project-wide conversion
- Compression ratio reporting

### Recommended Editors

**Essential Editors**:
1. **Asset Previewer**: Before/after conversion comparison
2. **LOD Inspector**: View all generated LOD levels
3. **Batch Converter UI**: Visual batch conversion

**Recommended Python Libraries**:
- **trimesh**: 3D model viewing and manipulation
- **Pillow (PIL)**: Texture preview and editing
- **PyQt5/PySide6**: Full conversion GUI
- **Open3D**: 3D asset visualization
- **PyVista**: Mesh inspection and visualization
- **Assimp**: Asset import library for format conversion

---

## INTEGRATION POINTS WITH EXISTING MODULES

### Forge Validator Integration

All pipelines should integrate with `forge_validator` for:
- Quality metrics scoring
- AI-based validation
- Asset verification
- Pass/fail determination

**Integration Pattern**:
```python
from vaultmind_forge.forge_validator import compute_metrics

# After generation
metrics, diagnostics = compute_metrics(asset_path)

# Display metrics in editor
editor.show_quality_metrics(metrics)

# Allow user to accept or regenerate
if user_accepts:
    export_asset()
else:
    regenerate_with_adjustments()
```

### Forge Lineage Integration

Track asset provenance:
- Source files
- Processing steps
- Parameters used
- Validation results
- User edits

**Integration Pattern**:
```python
from vaultmind_forge.forge_lineage import LineageLogger

logger = LineageLogger()
logger.log_job_start(job_id, config)
logger.log_asset_created(job_id, asset_path, metadata)

# Track user edits in editor
logger.log_edit(job_id, edit_type="inpaint", region=bbox)

logger.log_job_complete(job_id)
```

### Forge Versioning Integration

Version control for:
- Generated assets
- Edited versions
- Parameter variations
- Best selections

**Integration Pattern**:
```python
from vaultmind_forge.forge_versioning import VersionControl

vc = VersionControl()

# Save each variation
for i, variant in enumerate(variants):
    vc.save_version(variant, f"generation_{i}", metadata)

# Save user-edited version
vc.save_version(edited_asset, "user_final", metadata)
```

---

## RECOMMENDED EDITOR ARCHITECTURE

### Unified Editor Framework

**Goal**: Single unified interface for all asset types

```python
from vaultmind_forge.forge_editors import UnifiedAssetViewer

# Automatic type detection
viewer = UnifiedAssetViewer()
viewer.open_asset("path/to/asset.png")  # Opens image viewer
viewer.open_asset("path/to/video.mp4")  # Opens video player
viewer.open_asset("path/to/mesh.obj")   # Opens 3D viewer
viewer.show()
```

### Core Editor Components

**1. Base Viewer Class**
```python
class AssetViewer:
    def open(self, asset_path): ...
    def show(self): ...
    def close(self): ...
    def export(self, output_path, format): ...
    def get_metadata(self): ...
```

**2. Image Viewer (Pillow + PyQt5)**
```python
class ImageViewer(AssetViewer):
    - View images
    - Zoom, pan
    - Basic adjustments (brightness, contrast, saturation)
    - Crop, rotate
    - Inpainting
    - Side-by-side comparison
```

**3. Video Player (opencv + PyQt5)**
```python
class VideoPlayer(AssetViewer):
    - Play/pause video
    - Scrub timeline
    - Extract frames
    - Trim, cut
    - Add transitions
```

**4. 3D Viewer (Open3D or PyVista)**
```python
class MeshViewer(AssetViewer):
    - Rotate, zoom, pan
    - Wireframe/solid/textured modes
    - View semantic components
    - Material preview
    - LOD switcher
```

**5. Procedural Preview (matplotlib + vispy)**
```python
class ProceduralPreview(AssetViewer):
    - Real-time parameter sliders
    - Instant texture preview
    - 3D heightmap view
    - Tiling tester
    - Variation browser
```

### Comparison Tools

**Side-by-Side Comparator**:
```python
class ComparisonView:
    def set_images(self, left, right):
        """Set two images for comparison"""

    def set_slider_mode(self, enabled):
        """Enable interactive slider"""

    def show_difference(self):
        """Show pixel difference heatmap"""

    def show_metrics(self):
        """Display quality metrics for both"""
```

**Multi-variant Browser**:
```python
class VariantBrowser:
    def load_variants(self, paths):
        """Load multiple variants"""

    def display_grid(self):
        """Grid view of all variants"""

    def select_best(self):
        """Highlight highest-quality variant"""

    def compare_selected(self):
        """Compare user-selected variants"""
```

### Editing Tools

**Inpainting Editor**:
```python
class InpaintingEditor:
    def set_mask_tool(self, brush_size):
        """Brush for marking regions"""

    def inpaint_region(self, algorithm="telea"):
        """Fill masked region"""

    def undo/redo(self): ...
```

**Parameter Editor**:
```python
class ParameterEditor:
    def add_slider(self, name, min, max, default):
        """Add parameter slider"""

    def set_realtime_preview(self, enabled):
        """Update preview as sliders move"""

    def get_parameters(self):
        """Get current parameter values"""
```

---

## FREE/OPEN-SOURCE LIBRARY RECOMMENDATIONS

### Essential Core Libraries (MUST HAVE)

**Image Processing**:
- **Pillow (PIL)**: Image I/O, basic editing, format conversion
  - License: PIL License (permissive)
  - Size: ~8MB
  - Features: Open, save, resize, crop, rotate, filters

**Computer Vision**:
- **opencv-python (cv2)**: Advanced editing, inpainting, filters, video
  - License: Apache 2.0
  - Size: ~90MB (headless: ~40MB)
  - Features: Inpainting, video processing, filters, transformations

**Numerical Computing**:
- **numpy**: Numerical operations, array manipulation
  - License: BSD
  - Size: ~20MB
  - Features: Fast array operations, math functions

### GUI Framework (RECOMMENDED)

**Desktop GUI**:
- **PyQt5/PySide6**: Professional cross-platform GUI
  - License: GPL/LGPL (PyQt5), LGPL (PySide6)
  - Size: ~100MB
  - Features: Full widget set, multimedia, OpenGL, threading
  - **Recommendation**: PySide6 (LGPL is more permissive)

**Alternative (Lightweight)**:
- **tkinter**: Built-in Python GUI (no install needed)
  - License: Python License
  - Size: Included with Python
  - Features: Basic widgets, simple layouts

### Visualization Libraries (ESSENTIAL)

**2D Plotting**:
- **matplotlib**: Plotting, image display, comparisons
  - License: PSF-based
  - Size: ~40MB
  - Features: Plots, image display, subplots, interactive

**Advanced Image Viewing**:
- **napari**: Multi-dimensional image viewer with layers
  - License: BSD-3
  - Size: ~20MB
  - Features: Layers, annotations, n-dimensional, plugins
  - **Use case**: Multi-layer image comparison, annotations

### 3D Processing Libraries (FOR 3D PIPELINES)

**Mesh Manipulation**:
- **trimesh**: Mesh loading, manipulation, analysis
  - License: MIT
  - Size: ~5MB
  - Features: Load/save meshes, boolean operations, repair

**3D Visualization**:
- **Open3D**: 3D data processing and visualization
  - License: MIT
  - Size: ~150MB
  - Features: Point clouds, meshes, rendering, editing
  - **Recommended for**: 3D viewer, mesh editor

**Alternative (Lighter)**:
- **PyVista**: VTK-based 3D visualization
  - License: MIT
  - Size: ~70MB (with VTK)
  - Features: 3D plotting, mesh operations, interactive

**Advanced (Optional)**:
- **PyMeshLab**: MeshLab Python bindings
  - License: GPL
  - Size: ~200MB
  - Features: All MeshLab filters and operations

### Video Processing Libraries (FOR VIDEO PIPELINES)

**High-Level Video Editing**:
- **moviepy**: Video editing, transitions, effects
  - License: MIT
  - Size: ~10MB (requires ffmpeg)
  - Features: Cuts, transitions, effects, audio

**Alternative (Simpler)**:
- **imageio**: Simple video I/O
  - License: BSD-2
  - Size: ~5MB
  - Features: Read/write video frames

**Low-Level (Advanced)**:
- **PyAV**: FFmpeg Python bindings
  - License: BSD
  - Size: ~30MB
  - Features: Full FFmpeg access, codecs, streams

### Web-Based Editors (ALTERNATIVE APPROACH)

**Quick Prototyping**:
- **gradio**: Web-based interfaces for ML models
  - License: Apache 2.0
  - Size: ~10MB
  - Features: Quick UI, auto-sharing, interactive
  - **Use case**: Rapid prototyping of editors

**Dashboard Apps**:
- **streamlit**: Interactive data apps
  - License: Apache 2.0
  - Size: ~30MB
  - Features: Widgets, caching, deployment
  - **Use case**: Comparison dashboards, batch processing UI

**Advanced (Plotly-based)**:
- **dash**: Interactive dashboards
  - License: MIT
  - Size: ~40MB
  - Features: Advanced visualization, callbacks
  - **Use case**: Production-grade web editors

---

## IMPLEMENTATION PRIORITY

### Phase 1: Essential Viewers (Immediate)
1. **Image Viewer** (Pillow + PyQt5)
   - View generated images
   - Side-by-side comparison
   - Basic zoom/pan
   - Export with metadata

2. **3D Viewer** (Open3D)
   - View generated meshes
   - Rotate, zoom, pan
   - View semantic components
   - Export to engine formats

### Phase 2: Comparison Tools (Short Term)
1. **Multi-variant Comparator**
   - Grid view of variants
   - Quality metrics display
   - Select best

2. **Before/After Viewer**
   - Interactive slider
   - Zoom inspector
   - Metrics dashboard

### Phase 3: Editing Tools (Medium Term)
1. **Inpainting Editor**
   - Brush tool
   - Fill algorithms
   - Undo/redo

2. **Parameter Editors**
   - Real-time sliders
   - Preset system
   - Save/load configurations

### Phase 4: Advanced Features (Long Term)
1. **Video Timeline Editor**
2. **Batch Processing UI**
3. **Material Editor**
4. **UV Editor**

---

## INTEGRATION WITH WEB UI

### Option 1: Hybrid Approach
- Desktop editors for heavy work (PyQt5-based)
- Web UI editors for remote access (gradio-based)
- Share same backend API

### Option 2: Web-First Approach
- All editors in React web UI
- Use Three.js for 3D viewer
- Canvas API for image editing
- Video.js for video playback

### Recommendation
**Hybrid approach** for best of both worlds:
- Desktop: High-performance, full-featured editors
- Web: Lightweight preview, remote access, sharing

---

## LIBRARY SIZE SUMMARY

**Minimal Installation** (~150MB):
- Pillow (8MB)
- numpy (20MB)
- opencv-python-headless (40MB)
- PyQt5 (100MB) or PySide6 (100MB)

**Standard Installation** (~300MB):
- Minimal +
- matplotlib (40MB)
- trimesh (5MB)
- Open3D (150MB)

**Full Installation** (~500MB):
- Standard +
- moviepy (10MB + ffmpeg)
- napari (20MB)
- PyVista (70MB)
- gradio (10MB)

---

## NEXT STEPS

1. **Create `forge_editors/` module** with:
   - Base viewer classes
   - Image viewer (Pillow + PyQt5)
   - 3D viewer (Open3D)
   - Unified asset viewer

2. **Integrate with pipelines**:
   - Auto-show results in viewer after generation
   - Pass metadata to viewer
   - Export from viewer to pipeline output

3. **Add to Web UI**:
   - Embed viewers in node results
   - Click to open full editor
   - Save edits back to workflow

4. **Documentation**:
   - Editor user guide
   - API documentation
   - Integration examples

---

**Status**: Research complete, implementation pending
**Priority**: Phase 1 (Essential Viewers) - High priority
**Dependencies**: PyQt5/PySide6, Pillow, numpy, opencv-python, Open3D
