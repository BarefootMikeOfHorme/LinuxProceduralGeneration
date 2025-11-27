# VaultMind Forge - ControlNet Implementation
**Date:** 2025-11-27
**Status:** IN PROGRESS - Phase 1 (ControlNet Integration)

---

## Overview

ControlNet adds spatial control to SDXL generation by conditioning on structural information like edges, depth maps, or pose keypoints. This enables precise control over composition, style, and character poses.

---

## ControlNet Architecture

### What is ControlNet?

ControlNet is a neural network structure that injects additional conditional controls into pre-trained diffusion models like SDXL. It works by:

1. **Preprocessing:** Converting input images to control signals (edges, depth, pose)
2. **Conditioning:** Injecting control information into UNet layers
3. **Guided Generation:** SDXL generates images matching both prompt AND structure

### Key Components

**1. Preprocessors**
- **Canny Edge Detector:** Extracts edges from reference images
- **Depth Estimator:** Generates depth maps (MiDaS, ZoeDepth)
- **Pose Detector:** Extracts human pose keypoints (OpenPose)
- **Normal Map:** Surface normal estimation
- **Scribble:** Hand-drawn sketches as guides

**2. ControlNet Models**
- **controlnet-canny-sdxl-1.0:** Edge-guided generation
- **controlnet-depth-sdxl-1.0:** Depth-guided generation
- **controlnet-openpose-sdxl-1.0:** Pose-guided generation

**3. Integration Points**
- Loads alongside SDXL base model
- Injects at UNet encoder layers
- Does not replace, only conditions

---

## Implementation Plan

### Phase 1: Core Infrastructure

#### File Structure
```
vaultmind_forge/forge_diffusion/
├── controlnet.py                 # NEW: ControlNet wrapper
├── controlnet_preprocessors.py   # NEW: Preprocessor functions
├── sdxl_generator.py            # MODIFY: Add ControlNet support
└── generator.py                 # MODIFY: Add ControlNet config

backend/executors/
├── controlnet_nodes.py          # NEW: ControlNet node executors
└── generation_nodes.py          # MODIFY: Update SDXL executor
```

#### Dependencies
```python
# Core
diffusers >= 0.25.0  # ControlNet support for SDXL
controlnet-aux       # Preprocessors

# Preprocessors
opencv-python        # Canny edge detection
timm                 # MiDaS depth estimation
transformers         # Model loading
```

---

## ControlNet Node Design

### 1. ControlNet Preprocessor Nodes

#### **Canny Edge Detector Node**
```yaml
Node: cannyPreprocessor
Inputs:
  - image: IMAGE (reference image)
  - low_threshold: NUMBER (default: 100)
  - high_threshold: NUMBER (default: 200)
Outputs:
  - control_image: IMAGE (edge map)
```

#### **Depth Estimator Node**
```yaml
Node: depthPreprocessor
Inputs:
  - image: IMAGE (reference image)
  - model: TEXT (default: "midas") # midas, zoedepth
Outputs:
  - control_image: IMAGE (depth map)
  - depth_data: ARRAY (raw depth values)
```

#### **Pose Detector Node**
```yaml
Node: posePreprocessor
Inputs:
  - image: IMAGE (reference image with person)
  - detect_hands: BOOLEAN (default: true)
  - detect_face: BOOLEAN (default: true)
Outputs:
  - control_image: IMAGE (pose keypoints visualization)
  - pose_data: JSON (keypoint coordinates)
```

---

### 2. ControlNet Loader Node

```yaml
Node: controlnetLoader
Inputs:
  - controlnet_type: TEXT (canny, depth, pose)
  - model_path: TEXT (optional, defaults to HuggingFace)
Outputs:
  - controlnet: CONTROLNET (loaded model)
```

---

### 3. ControlNet SDXL Generator Node

```yaml
Node: sdxlControlNetGenerator
Inputs:
  - prompt: TEXT
  - control_image: IMAGE (from preprocessor)
  - controlnet: CONTROLNET (from loader)
  - controlnet_scale: NUMBER (0.0-2.0, default: 1.0)
  - steps: NUMBER (default: 30)
  - width: NUMBER (default: 1024)
  - height: NUMBER (default: 1024)
  - cfg_scale: NUMBER (default: 7.5)
  - seed: NUMBER (optional)
Outputs:
  - image: IMAGE (generated with control)
  - metadata: JSON
```

---

## Workflow Examples

### Example 1: Edge-Guided Generation
```
Reference Photo → Canny Preprocessor → Edge Map
                                        ↓
Text Prompt + ControlNet Loader → SDXL ControlNet Generator → Output Image
```

**Use Case:** Maintain composition while changing style/content

---

### Example 2: Pose-Guided Character
```
Pose Reference → Pose Preprocessor → Pose Keypoints
                                      ↓
Character Prompt + ControlNet Loader → SDXL ControlNet Generator → Character in Pose
```

**Use Case:** Character consistency across poses

---

### Example 3: Depth-Guided Scene
```
3D Render/Photo → Depth Preprocessor → Depth Map
                                        ↓
Scene Prompt + ControlNet Loader → SDXL ControlNet Generator → Styled Scene
```

**Use Case:** Maintain spatial structure, change everything else

---

## Implementation Steps

### Step 1: ControlNet Wrapper Module
**File:** `vaultmind_forge/forge_diffusion/controlnet.py`

```python
from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline
from PIL import Image
import torch

class ControlNetWrapper:
    """Wrapper for ControlNet models with SDXL"""

    def __init__(self):
        self.controlnet = None
        self.controlnet_type = None

    def load_controlnet(self, controlnet_type: str, model_path: str = None):
        """Load ControlNet model"""
        # Map types to HuggingFace model IDs
        model_ids = {
            "canny": "diffusers/controlnet-canny-sdxl-1.0",
            "depth": "diffusers/controlnet-depth-sdxl-1.0",
            "pose": "thibaud/controlnet-openpose-sdxl-1.0",
        }

        model_id = model_path or model_ids.get(controlnet_type)
        self.controlnet = ControlNetModel.from_pretrained(
            model_id,
            torch_dtype=torch.float16
        )
        self.controlnet_type = controlnet_type

    def create_pipeline(self, base_model_path: str):
        """Create SDXL pipeline with ControlNet"""
        pipeline = StableDiffusionXLControlNetPipeline.from_pretrained(
            base_model_path,
            controlnet=self.controlnet,
            torch_dtype=torch.float16
        )
        return pipeline
```

---

### Step 2: Preprocessor Functions
**File:** `vaultmind_forge/forge_diffusion/controlnet_preprocessors.py`

```python
import cv2
import numpy as np
from PIL import Image

def canny_edge_detection(image: Image.Image, low: int = 100, high: int = 200):
    """Canny edge detection preprocessor"""
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, low, high)
    edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(edges_rgb)

def depth_estimation(image: Image.Image, model: str = "midas"):
    """Depth map preprocessor using MiDaS"""
    from transformers import pipeline

    depth_estimator = pipeline("depth-estimation", model=f"Intel/{model}")
    depth = depth_estimator(image)
    return depth["depth"]

def pose_detection(image: Image.Image, detect_hands: bool = True, detect_face: bool = True):
    """Pose detection preprocessor using ControlNet Aux"""
    from controlnet_aux import OpenposeDetector

    processor = OpenposeDetector.from_pretrained('lllyasviel/ControlNet')
    pose_image = processor(image, hand_and_face=detect_hands and detect_face)
    return pose_image
```

---

### Step 3: Update SDXL Generator
**File:** `vaultmind_forge/forge_diffusion/sdxl_generator.py`

Add ControlNet support to existing SDXLGenerator:

```python
def generate_with_controlnet(self, config: GenerationConfig, control_image: Image.Image, controlnet_scale: float = 1.0):
    """Generate image with ControlNet guidance"""

    result = self.pipeline(
        prompt=config.prompt,
        negative_prompt=config.negative_prompt,
        image=control_image,  # Control image
        num_inference_steps=config.steps,
        guidance_scale=config.guidance_scale,
        width=config.width,
        height=config.height,
        controlnet_conditioning_scale=controlnet_scale,
    )

    return result
```

---

### Step 4: Backend Executors
**File:** `backend/executors/controlnet_nodes.py`

Implement node executors for:
- CannyPreprocessorExecutor
- DepthPreprocessorExecutor
- PosePreprocessorExecutor
- ControlNetLoaderExecutor
- SDXLControlNetGeneratorExecutor

---

## Testing Strategy

### Test 1: Canny Edge Control
1. Load reference portrait photo
2. Run Canny preprocessor
3. Generate with prompt: "oil painting of a person"
4. Verify: Output matches edge structure

### Test 2: Pose Control
1. Load pose reference (person standing)
2. Run Pose preprocessor
3. Generate with prompt: "cyberpunk warrior in armor"
4. Verify: Character matches pose exactly

### Test 3: Depth Control
1. Load scene with depth variation
2. Run Depth preprocessor
3. Generate with prompt: "fantasy landscape"
4. Verify: Depth structure preserved

---

## Performance Considerations

### Memory Usage
- ControlNet model: ~1.5GB VRAM
- SDXL base: ~6GB VRAM
- **Total:** ~7.5GB VRAM minimum

### Speed
- Preprocessing: 0.5-2 seconds
- Generation with ControlNet: +10-20% slower than base SDXL
- **Total:** ~30-60 seconds per image (30 steps, GPU)

### Optimizations
- Cache preprocessor models
- Batch preprocessing when possible
- Use fp16 for all models
- Enable xformers memory attention

---

## Workflow Integration

### CLI Command
```bash
# Generate with Canny control
forge generate "oil painting portrait" \
  --control-image photo.jpg \
  --control-type canny \
  --control-scale 1.0 \
  --steps 30
```

### Node Workflow
```json
{
  "nodes": [
    {"id": "1", "type": "imageInput", "data": {"path": "photo.jpg"}},
    {"id": "2", "type": "cannyPreprocessor", "data": {"low": 100, "high": 200}},
    {"id": "3", "type": "controlnetLoader", "data": {"type": "canny"}},
    {"id": "4", "type": "textInput", "data": {"text": "oil painting"}},
    {"id": "5", "type": "sdxlControlNetGenerator", "data": {"steps": 30}}
  ],
  "connections": [
    {"source": "1", "sourceHandle": "image", "target": "2", "targetHandle": "image"},
    {"source": "2", "sourceHandle": "control_image", "target": "5", "targetHandle": "control_image"},
    {"source": "3", "sourceHandle": "controlnet", "target": "5", "targetHandle": "controlnet"},
    {"source": "4", "sourceHandle": "text", "target": "5", "targetHandle": "prompt"}
  ]
}
```

---

## Documentation Deliverables

1. **User Guide:** How to use ControlNet nodes
2. **Tutorial:** Step-by-step workflows with examples
3. **API Reference:** Node specifications and parameters
4. **Troubleshooting:** Common issues and solutions

---

## Success Criteria

✅ Canny edge detection working
✅ Depth estimation working
✅ Pose detection working
✅ ControlNet models loading correctly
✅ SDXL + ControlNet generation working
✅ Node executors functional
✅ Workflow examples tested
✅ Documentation complete

---

## Next Steps After ControlNet

After completing ControlNet integration, move to:
- **Option 3:** Web UI FUI (holographic interface)
- **Option 2:** AI Agents/Merlinv1 integration

---

**Status:** Research complete, ready to implement
**Estimated Implementation Time:** 2-3 hours
**Expected Output:** 5 new node types, full ControlNet support

---

**END OF CONTROLNET IMPLEMENTATION PLAN**
