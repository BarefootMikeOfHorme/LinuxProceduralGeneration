# VaultMind Forge - Web UI Redesign Architecture
**Version:** 2.0 (Production-Grade Node Editor)
**Created:** 2025-11-26
**Status:** Design Document - Ready for Implementation

---

## Executive Summary

This document outlines the complete redesign of VaultMind Forge's web UI from a prototype node editor to a production-grade system comparable to ComfyUI, Blender, and other professional node-based applications.

**Key Changes:**
- **Layout:** Split-panel design (70% editors top, 30% nodes bottom)
- **Nodes:** 100+ functional nodes (up from 4-5 working)
- **Previews:** Real-time embedded viewers in nodes
- **Data Flow:** Proper type-safe connections between nodes
- **Editors:** Task-specific embedded editors (image, video, 3D, text)
- **Output:** Inline preview with save/export options

---

## Reference Analysis

### ComfyUI Architecture
**Source:** [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)

**Strengths:**
- Real-time preview nodes with `--preview-method auto`
- Modular graph/nodes interface with Python backend
- Custom node system with hundreds of community extensions
- WebSocket-based progress updates
- Integrated image/video viewer with metadata
- Parameter panel for subgraph editing (V3 schema)

**Key Features to Adopt:**
- Preview nodes that show output inline
- WebSocket real-time updates during generation
- Node grouping for reusable subgraphs
- Metadata viewer for lineage tracking
- Custom node extensibility

### Blender Node Editor
**Source:** [Blender Node Workflows](https://spin.atomicobject.com/blender-node-based-workflows/)

**Strengths:**
- Geometry nodes + Shader editor split architecture
- Embedded 3D viewport shows real-time results
- Group nodes hide complexity
- Attribute-based data transfer between systems
- Modifier stack integration (high-level interface)

**Key Features to Adopt:**
- Split-panel layout (viewport + nodes)
- Group nodes for complex operations
- Real-time preview in main viewport
- Attribute/metadata propagation
- Hierarchical node organization

### React Flow / Professional Node UIs
**Source:** [React Flow](https://reactflow.dev), [Awesome Node-Based UIs](https://github.com/xyflow/awesome-node-based-uis)

**Strengths:**
- Highly customizable React components
- Built-in edge validation and connection rules
- Minimap, zoom, pan controls
- Custom node rendering with embedded content
- Group nodes and hierarchical layouts

**Key Features to Adopt:**
- React Flow as base library (already using)
- Custom node components with embedded viewers
- Connection validation (type-safe edges)
- Minimap for large graphs
- Spatial organization patterns

### Stable Diffusion Node Systems
**Source:** [IP-Adapter Guide](https://stable-diffusion-art.com/ip-adapter/), [ControlNet Guide](https://stable-diffusion-art.com/controlnet/)

**Critical Nodes Identified:**
- IP-Adapter nodes (image prompting)
- ControlNet nodes (pose, depth, canny, etc.)
- LoRA loader nodes
- VAE encode/decode nodes
- Sampler/scheduler nodes
- Latent upscaling nodes
- Image conditioning nodes

---

## New UI Layout Design

### Split-Panel Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  TOOLBAR: File | Edit | View | Node | Help          [⚙️ ⚡ 🔍] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│               PRIMARY EDITOR AREA (70%)                       │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                       │    │
│  │  [Image Viewer] [Video Player] [3D Viewer] [Text]   │    │
│  │                                                       │    │
│  │  • Auto-switches based on selected node output       │    │
│  │  • Pan, zoom, compare, histogram tools               │    │
│  │  • Metadata overlay (resolution, format, lineage)    │    │
│  │  • Save/export buttons inline                        │    │
│  │                                                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
├───────────────────────────────────────────────────────────── │
│                                                               │
│                   NODE GRAPH AREA (30%)                       │
│                                                               │
│  [Minimap]                                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  🔵 Input ──→ 🟢 Generator ──→ 🟡 Processor ──→ 🔴 Output│
│  │                                                       │    │
│  │  • Zoomable (scroll wheel)                           │    │
│  │  • Pannable (click-drag)                             │    │
│  │  • Inline previews (thumbnail in nodes)              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
    [Status Bar: Ready | Last: SDXL_output.png | 2048x2048]
```

### Panel Resizing
- Drag divider to adjust editor/nodes ratio
- Collapse nodes panel to full editor view
- Collapse editor panel to full graph view
- Save layout preferences per-user

### Responsive Behavior
- **Large screens (>1920px):** Default 70/30 split
- **Medium screens (1280-1920px):** Default 60/40 split
- **Small screens (<1280px):** Tabbed interface (Editor tab | Nodes tab)

---

## Comprehensive Node Library (100+ Nodes)

### Category 1: Input Nodes (12 nodes)

| Node Name | Inputs | Outputs | Purpose |
|-----------|--------|---------|---------|
| Text Input | - | text | Manual text entry |
| File Loader | file_path | image/video/3d | Load from disk |
| Image Capture | device_id | image | Webcam/screen capture |
| Batch Loader | directory, pattern | image[] | Load multiple files |
| Random Seed | - | seed | Randomized seed |
| Fixed Seed | value | seed | Reproducible seed |
| Slider (Int) | min, max, step | int | Integer parameter |
| Slider (Float) | min, max, step | float | Float parameter |
| Dropdown | options[] | selection | Choice selector |
| Color Picker | - | color | RGB/HSV color |
| JSON Input | json_text | dict | Structured data |
| Metadata Reader | image/asset | metadata | Extract lineage |

### Category 2: Image Generation (24 nodes)

| Node Name | Inputs | Outputs | Purpose |
|-----------|--------|---------|---------|
| SDXL Generator | prompt, negative, seed, steps, cfg | image | Base SDXL generation |
| SDXL Turbo | prompt, seed, steps | image | Fast 1-4 step generation |
| SDXL Refiner | image, prompt, steps | image | Refinement pass |
| SDXL Lightning | prompt, seed | image | Ultra-fast generation |
| ControlNet Canny | image, prompt, strength | image | Edge-guided generation |
| ControlNet Depth | image, prompt, strength | image | Depth-guided generation |
| ControlNet Pose | image, prompt, strength | image | Pose-guided generation |
| ControlNet Scribble | image, prompt, strength | image | Scribble-guided generation |
| ControlNet Normal | image, prompt, strength | image | Normal map-guided |
| ControlNet Tile | image, prompt, strength | image | Tiled upscale |
| IP-Adapter | image_prompt, text_prompt, weight | image | Image prompting |
| IP-Adapter FaceID | face_image, prompt, weight | image | Face identity transfer |
| IP-Adapter Plus | image_prompt, text_prompt, detail | image | High-detail IP-Adapter |
| LoRA Loader | lora_name, strength | lora_model | Load LoRA weights |
| LoRA Stack | lora_models[], weights[] | combined_lora | Combine multiple LoRAs |
| VAE Encode | image | latent | Image → latent space |
| VAE Decode | latent | image | Latent → image |
| Sampler | latent, model, steps, cfg | latent | Custom sampler |
| Scheduler | sampler_type, steps | schedule | Noise schedule |
| Latent Upscale | latent, scale_factor | latent | Upscale in latent |
| Inpaint | image, mask, prompt | image | Region-specific gen |
| Outpaint | image, direction, prompt | image | Extend canvas |
| Img2Img | image, prompt, strength | image | Image variation |
| Batch Generator | prompt, count, seed_offset | image[] | Multi-generation |

### Category 3: Image Processing (28 nodes)

| Node Name | Inputs | Outputs | Purpose |
|-----------|--------|---------|---------|
| Super Resolution | image, scale, model | image | AI upscaling (forge_sr) |
| Resize | image, width, height, method | image | Standard resize |
| Crop | image, x, y, width, height | image | Crop region |
| Smart Crop | image, target_size, focus | image | AI-guided crop |
| Rotate | image, degrees | image | Rotation |
| Flip | image, direction | image | Horizontal/vertical flip |
| Blur | image, radius, method | image | Gaussian/box/motion blur |
| Sharpen | image, amount | image | Sharpening |
| Denoise | image, strength | image | Noise reduction |
| Color Correct | image, brightness, contrast, saturation | image | Color adjustments |
| HSV Adjust | image, hue, saturation, value | image | HSV manipulation |
| Curves | image, curve_points | image | Tone curves |
| Levels | image, black_point, white_point, gamma | image | Levels adjustment |
| Threshold | image, value, method | image | Binary threshold |
| Edge Detect | image, method | image | Canny/Sobel/Prewitt |
| Gradient | image, direction | image | Gradient extraction |
| Histogram | image | histogram_data | Histogram analysis |
| Normalize | image | image | Auto-normalize |
| Clamp | image, min, max | image | Clamp values |
| Blend | image1, image2, mode, opacity | image | Layer blending |
| Alpha Composite | foreground, background, mask | image | Alpha compositing |
| Mask Blur | mask, radius | mask | Soften mask edges |
| Mask Expand | mask, pixels | mask | Dilate mask |
| Mask Shrink | mask, pixels | mask | Erode mask |
| Mask Invert | mask | mask | Invert mask |
| Background Remove | image | image, mask | Remove background |
| Segmentation | image, model | mask[] | Semantic segmentation |
| Depth Estimation | image, model | depth_map | Estimate depth |

### Category 4: Prompt & Text (10 nodes)

| Node Name | Inputs | Outputs | Purpose |
|-----------|--------|---------|---------|
| Prompt Refiner | text | text | AI prompt enhancement (Merlinv1) |
| Prompt Combiner | prompt1, prompt2, separator | text | Concatenate prompts |
| Prompt Switch | prompt1, prompt2, condition | text | Conditional prompt |
| Negative Prompt | text | text | Negative prompt wrapper |
| Style Preset | style_name | text | Load style presets |
| Token Counter | text, model | token_count | Count tokens |
| Wildcard | template, wildcards | text | Random substitution |
| Text Replace | text, find, replace | text | String replacement |
| Text Template | template, variables | text | Template rendering |
| Regex Match | text, pattern | matches[] | Pattern matching |

### Category 5: Video Processing (8 nodes)

| Node Name | Inputs | Outputs | Purpose |
|-----------|--------|---------|---------|
| Video Loader | file_path | video, fps, frames | Load video |
| Video Saver | frames, fps, codec | file_path | Save video |
| Frame Extract | video, frame_number | image | Extract single frame |
| Frame Sequence | video | image[] | All frames |
| Frame Interpolation | frames[], target_fps | frames[] | AI interpolation |
| Video Upscale | video, scale, model | video | Upscale video |
| Video Stabilize | video | video | Stabilization |
| Video Effects | video, effect_type, params | video | Apply effects |

### Category 6: 3D Processing (10 nodes)

| Node Name | Inputs | Outputs | Purpose |
|-----------|--------|---------|---------|
| 3D Loader | file_path | mesh | Load glTF/FBX/OBJ |
| 3D Saver | mesh, format | file_path | Save 3D model |
| Mesh Generator | prompt, params | mesh | AI mesh generation |
| UV Unwrap | mesh | mesh, uv_map | Generate UVs |
| Material Apply | mesh, material | mesh | Apply material |
| Texture Baker | mesh, material | texture_maps | Bake textures |
| Normal Map | mesh | normal_map | Generate normal map |
| AO Baker | mesh | ao_map | Ambient occlusion |
| Mesh Decimate | mesh, target_poly_count | mesh | Reduce polygons |
| Mesh Smooth | mesh, iterations | mesh | Smooth geometry |

### Category 7: Validation & QA (8 nodes)

| Node Name | Inputs | Outputs | Purpose |
|-----------|--------|---------|---------|
| Image Validator | image | validation_report | Check quality (forge_validator) |
| Resolution Check | image, min_res, max_res | pass/fail | Resolution validation |
| Format Validator | file, expected_format | pass/fail | Format check |
| Checksum | asset | sha256_hash | Generate checksum |
| Lineage Validator | asset | lineage_report | Verify provenance |
| Duplicate Detector | image, threshold | is_duplicate | Check for duplicates |
| NSFW Filter | image | is_safe, score | Content filtering |
| Quality Score | image, model | score | AI quality scoring |

### Category 8: Utilities (12 nodes)

| Node Name | Inputs | Outputs | Purpose |
|-----------|--------|---------|---------|
| Preview | any | - | Display in editor (no passthrough) |
| Preview + Pass | any | any | Display + passthrough |
| Switch | input1, input2, condition | output | Conditional routing |
| Branch | input, condition | output1, output2 | Split execution |
| Merge | input[] | output | Combine streams |
| Reroute | input | output | Clean graph layout |
| Note | - | - | Documentation node |
| Group Input | - | outputs[] | Subgraph input |
| Group Output | inputs[] | - | Subgraph output |
| Variable Set | name, value | - | Store variable |
| Variable Get | name | value | Retrieve variable |
| Logger | any | any | Console logging |

### Category 9: Batch & Automation (6 nodes)

| Node Name | Inputs | Outputs | Purpose |
|-----------|--------|---------|---------|
| Batch Processor | inputs[], operation | outputs[] | Process array |
| For Each | array, subgraph | results[] | Loop execution |
| Range | start, end, step | int[] | Generate range |
| Collect | stream | array | Accumulate results |
| Filter | array, condition | filtered[] | Filter by condition |
| Sort | array, key | sorted[] | Sort results |

**Total Nodes:** 118 (exceeds 100+ requirement)

---

## Embedded Editor Specifications

### Image Viewer (Primary Editor)

**Features:**
- Pan (click-drag or arrow keys)
- Zoom (scroll wheel, 10%-1000%)
- Fit to window / 100% / fill screen modes
- A/B comparison slider (before/after)
- Histogram overlay (RGB + luminosity)
- Pixel inspector (hover shows RGB, position)
- Metadata panel (resolution, format, seed, prompt)
- Grid overlay (rule of thirds, golden ratio)
- Zoom navigator (minimap)

**Toolbar:**
```
[🔍+ 🔍-] [100%] [Fit] [Fill] [A|B] [📊 Histogram] [ℹ️ Metadata] [💾 Save] [📤 Export]
```

**Keyboard Shortcuts:**
- `Space + Drag` - Pan
- `+/-` - Zoom in/out
- `0` - Fit to window
- `1` - 100% zoom
- `H` - Toggle histogram
- `I` - Toggle metadata
- `S` - Save
- `E` - Export menu

### Video Player (Secondary Editor)

**Features:**
- Timeline scrubbing
- Play/pause/stop controls
- Frame-by-frame stepping (← →)
- Speed control (0.25x - 2x)
- Loop toggle
- Audio waveform display
- Frame number overlay
- Timestamp display
- Export frame as image

**Toolbar:**
```
[⏮️ ⏪ ▶️ ⏸️ ⏩ ⏭️] [🔁 Loop] [⚡ 1x] [🔊] [📸 Export Frame] [💾 Save]
```

**Timeline:**
```
┌────────────────────────────────────────────────────────┐
│ ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁ (Audio waveform)                      │
├────────────────────────────────────────────────────────┤
│ ━━━━━━━━━●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ 00:00:05 / 00:00:30                                    │
└────────────────────────────────────────────────────────┘
```

### 3D Viewer (Tertiary Editor)

**Features:**
- Orbit camera (click-drag)
- Pan camera (Shift + drag)
- Zoom camera (scroll wheel)
- Wireframe/shaded/textured modes
- Material preview
- Lighting controls (3-point light setup)
- Grid floor
- Axis gizmo
- Poly count display
- Export glTF/FBX/OBJ

**Toolbar:**
```
[🔄 Orbit] [↔️ Pan] [🔍 Zoom] [🔲 Wireframe] [🎨 Material] [💡 Lights] [💾 Save]
```

**Viewport Controls:**
- `Left Click + Drag` - Orbit
- `Shift + Drag` - Pan
- `Scroll` - Zoom
- `F` - Frame object
- `W` - Wireframe toggle
- `M` - Material preview toggle

### Text Editor (Quaternary Editor)

**Features:**
- Syntax highlighting (JSON, Python, YAML)
- Line numbers
- Auto-indent
- Find/replace
- Undo/redo (Ctrl+Z / Ctrl+Shift+Z)
- Word wrap toggle
- Copy/paste
- Export to file

**Toolbar:**
```
[📋 Copy] [📄 Paste] [🔍 Find] [💾 Save] [📤 Export] [↩️ Wrap]
```

**Use Cases:**
- Editing prompts from Prompt Refiner
- Viewing JSON metadata
- Editing batch configs
- Viewing validation reports

---

## Data Flow Architecture

### Type System

**Core Data Types:**
```typescript
type DataType =
  | 'text'           // String data
  | 'image'          // PIL.Image or base64
  | 'video'          // Video file path or stream
  | 'mesh'           // 3D model data
  | 'mask'           // Binary/grayscale mask
  | 'latent'         // Latent tensor
  | 'model'          // Model weights (LoRA, etc.)
  | 'seed'           // Integer seed
  | 'int'            // Integer
  | 'float'          // Float
  | 'array'          // Array of any type
  | 'dict'           // Dictionary/object
  | 'metadata'       // Lineage metadata
  | 'any'            // Accepts any type
```

**Connection Rules:**
```typescript
const compatibleTypes = {
  'text': ['text', 'any'],
  'image': ['image', 'any'],
  'video': ['video', 'any'],
  'mesh': ['mesh', 'any'],
  'mask': ['mask', 'image', 'any'],
  'latent': ['latent', 'any'],
  // ... etc
}

function canConnect(sourceType: DataType, targetType: DataType): boolean {
  return targetType === 'any' || compatibleTypes[sourceType]?.includes(targetType)
}
```

### Execution Flow

**DAG-Based Execution:**
1. User presses F5 (execute workflow)
2. Frontend validates graph (no cycles, all required inputs connected)
3. Frontend performs topological sort to determine execution order
4. Frontend sends workflow to backend via WebSocket
5. Backend executes nodes in order:
   - Load node inputs from previous node outputs
   - Execute node's Python function
   - Store node output in execution context
   - Send progress update via WebSocket
   - Send preview image/data via WebSocket (if Preview node)
6. Backend sends final results
7. Frontend updates editor with final output

**WebSocket Protocol:**
```typescript
// Frontend → Backend
{
  type: 'execute_workflow',
  workflow: {
    nodes: [...],
    connections: [...]
  }
}

// Backend → Frontend (progress)
{
  type: 'progress',
  node_id: 'node_123',
  status: 'running',
  progress: 0.45,
  message: 'Generating image (step 18/40)'
}

// Backend → Frontend (preview)
{
  type: 'preview',
  node_id: 'node_123',
  data_type: 'image',
  data: 'data:image/png;base64,...',
  metadata: { resolution: '2048x2048', ... }
}

// Backend → Frontend (complete)
{
  type: 'complete',
  outputs: {
    'node_123': { image: 'data:image/png;base64,...' },
    'node_456': { text: 'refined prompt...' }
  }
}
```

### Backend Execution Engine (backend/api.py)

**Current Issues (MUST FIX):**
- Only handles text→text connections
- Doesn't propagate images, masks, latents
- No type checking on connections

**Required Changes:**
```python
# NEW: Proper type-safe connection handling
def execute_node(node: Node, workflow: Workflow, node_outputs: dict) -> dict:
    """Execute a single node with proper data flow"""

    # 1. Initialize inputs from node defaults
    inputs = node.data.copy()

    # 2. Override with connected inputs (TYPE-SAFE)
    for conn in workflow.connections:
        if conn.target == node.id:
            source_node_output = node_outputs.get(conn.source, {})

            # Match by output handle name → input handle name
            source_value = source_node_output.get(conn.sourceHandle)

            if source_value is not None:
                # Type validation
                source_type = conn.sourceType  # From connection metadata
                target_type = conn.targetType

                if can_connect(source_type, target_type):
                    inputs[conn.targetHandle] = source_value
                else:
                    raise TypeError(f"Cannot connect {source_type} to {target_type}")

    # 3. Execute node's Python function
    if node.type == "sdxlGenerator":
        result = execute_sdxl_generator(inputs)
        return {
            'image': result.image_base64,
            'metadata': result.metadata
        }
    elif node.type == "superResolution":
        result = execute_super_resolution(inputs)
        return {
            'image': result.image_base64,
            'metadata': result.metadata
        }
    # ... etc for all 118 node types

    return {}
```

**Metadata Propagation:**
```python
# Every node output includes metadata
{
  'image': 'data:image/png;base64,...',
  'metadata': {
    'node_id': 'node_123',
    'node_type': 'sdxlGenerator',
    'timestamp': '2025-11-26T10:30:00Z',
    'resolution': '2048x2048',
    'format': 'PNG',
    'sha256': 'abc123...',
    'lineage': {
      'parent_nodes': ['node_100', 'node_101'],
      'prompt': 'a beautiful landscape',
      'seed': 42,
      'model': 'sdxl_base_1.0',
      'loras': ['style_lora_v1'],
      'controlnets': []
    }
  }
}
```

---

## Frontend Architecture (React + Zustand)

### State Management (Zustand)

**Store Structure:**
```typescript
interface WorkflowStore {
  // Graph state
  nodes: Node[]
  edges: Edge[]

  // Execution state
  isExecuting: boolean
  executionProgress: Map<string, number>
  nodeOutputs: Map<string, any>

  // Editor state
  selectedEditor: 'image' | 'video' | '3d' | 'text'
  editorContent: any
  editorMetadata: any

  // Layout state
  editorHeight: number  // % of screen (default 70%)
  nodesHeight: number   // % of screen (default 30%)

  // Actions
  addNode: (node: Node) => void
  deleteNode: (id: string) => void
  addEdge: (edge: Edge) => void
  deleteEdge: (id: string) => void
  executeWorkflow: () => void
  updateNodeOutput: (nodeId: string, output: any) => void
  setEditorContent: (content: any, metadata: any) => void
  resizeLayout: (editorHeight: number) => void
}
```

### Component Hierarchy

```
<App>
  <Toolbar>
    <FileMenu />
    <EditMenu />
    <ViewMenu />
    <NodeMenu />
    <HelpMenu />
  </Toolbar>

  <SplitPanel orientation="vertical" initialRatio={70}>
    <EditorPanel>
      {selectedEditor === 'image' && <ImageViewer />}
      {selectedEditor === 'video' && <VideoPlayer />}
      {selectedEditor === '3d' && <ThreeDViewer />}
      {selectedEditor === 'text' && <TextEditor />}
    </EditorPanel>

    <NodePanel>
      <Minimap />
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={customNodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
      >
        <Background />
        <Controls />
      </ReactFlow>
    </NodePanel>
  </SplitPanel>

  <StatusBar>
    {executionStatus} | {lastOutput} | {outputResolution}
  </StatusBar>
</App>
```

### Custom Node Component (with inline preview)

```tsx
function CustomNode({ data, id }: NodeProps) {
  const nodeOutput = useWorkflowStore(state => state.nodeOutputs.get(id))
  const isExecuting = useWorkflowStore(state =>
    state.executionProgress.has(id)
  )
  const progress = useWorkflowStore(state =>
    state.executionProgress.get(id) || 0
  )

  return (
    <div className="custom-node">
      {/* Node header */}
      <div className="node-header">
        <span className="node-icon">{data.icon}</span>
        <span className="node-name">{data.name}</span>
      </div>

      {/* Input handles */}
      <div className="node-inputs">
        {data.inputs?.map(input => (
          <Handle
            key={input.name}
            type="target"
            position={Position.Left}
            id={input.name}
            style={{ background: input.color }}
          />
        ))}
      </div>

      {/* Node content (params or preview) */}
      <div className="node-content">
        {isExecuting && (
          <ProgressBar progress={progress} />
        )}

        {nodeOutput?.image && (
          <img
            src={nodeOutput.image}
            alt="Preview"
            className="node-preview-thumbnail"
            onClick={() => openInEditor(nodeOutput)}
          />
        )}

        {!nodeOutput && data.params && (
          <NodeParams params={data.params} nodeId={id} />
        )}
      </div>

      {/* Output handles */}
      <div className="node-outputs">
        {data.outputs?.map(output => (
          <Handle
            key={output.name}
            type="source"
            position={Position.Right}
            id={output.name}
            style={{ background: output.color }}
          />
        ))}
      </div>
    </div>
  )
}
```

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1)
**Priority:** P0 (Must have)

- [ ] Implement split-panel layout (ResizablePanel component)
- [ ] Add embedded Image Viewer with zoom/pan
- [ ] Implement WebSocket connection for real-time updates
- [ ] Fix backend data flow (type-safe connection handling)
- [ ] Add inline preview thumbnails in nodes
- [ ] Implement execution progress indicators

**Deliverable:** Basic split-panel UI with working image preview

### Phase 2: Core Nodes (Week 2-3)
**Priority:** P0 (Must have)

- [ ] Implement all 24 Image Generation nodes
- [ ] Implement all 28 Image Processing nodes
- [ ] Implement 10 Prompt & Text nodes
- [ ] Implement 12 Input nodes
- [ ] Add type-safe edge validation
- [ ] Add Preview nodes with editor integration

**Deliverable:** 84 working nodes with proper data flow

### Phase 3: Advanced Features (Week 4)
**Priority:** P1 (Should have)

- [ ] Add Video Player editor
- [ ] Add 3D Viewer editor (Three.js)
- [ ] Add Text Editor
- [ ] Implement all 8 Video Processing nodes
- [ ] Implement all 10 3D Processing nodes
- [ ] Add auto-layout algorithms

**Deliverable:** Multi-format editor support (image/video/3D/text)

### Phase 4: Validation & Utilities (Week 5)
**Priority:** P1 (Should have)

- [ ] Implement all 8 Validation & QA nodes
- [ ] Implement all 12 Utility nodes
- [ ] Add Node Groups (subgraphs)
- [ ] Add metadata viewer panel
- [ ] Add lineage tracking display

**Deliverable:** 118 total nodes, validation system

### Phase 5: Batch & Automation (Week 6)
**Priority:** P2 (Nice to have)

- [ ] Implement all 6 Batch & Automation nodes
- [ ] Add batch execution queue
- [ ] Add saved workflow templates
- [ ] Add workflow sharing/export

**Deliverable:** Complete automation features

### Phase 6: Polish & Optimization (Week 7)
**Priority:** P2 (Nice to have)

- [ ] Performance optimization (virtualized nodes)
- [ ] Keyboard shortcuts
- [ ] Undo/redo for graph edits
- [ ] Dark/light theme
- [ ] Accessibility (ARIA labels)
- [ ] User documentation

**Deliverable:** Production-ready UI

---

## Technical Stack

### Frontend
- **Framework:** React 18 + TypeScript
- **Node Editor:** React Flow 11.x
- **State Management:** Zustand
- **Image Viewer:** Custom component with canvas API
- **Video Player:** Custom component with HTML5 video
- **3D Viewer:** Three.js + React Three Fiber
- **Text Editor:** Monaco Editor (VS Code editor)
- **HTTP Client:** Axios
- **WebSocket:** Native WebSocket API
- **Styling:** TailwindCSS + CSS Modules

### Backend
- **Framework:** FastAPI (Python 3.10+)
- **WebSocket:** FastAPI WebSocket support
- **Image Processing:** PIL (Pillow)
- **SDXL Generation:** Diffusers library
- **Super Resolution:** forge_sr module
- **Validation:** forge_validator module
- **Lineage:** forge_lineage module
- **Async Execution:** asyncio

### Development Tools
- **Build:** Vite
- **Linting:** ESLint + Prettier
- **Testing:** Jest + React Testing Library
- **Type Checking:** TypeScript strict mode
- **API Testing:** Pytest + httpx

---

## Performance Considerations

### Frontend Optimization

1. **Node Virtualization:**
   - Only render nodes in viewport
   - Use React Flow's built-in virtualization
   - Lazy-load node thumbnails

2. **Edge Rendering:**
   - Simplify edges outside viewport
   - Use canvas for edge rendering (faster than SVG)
   - Batch edge updates

3. **Image Handling:**
   - Lazy-load full-resolution images
   - Use progressive JPEGs for previews
   - Cache decoded images in memory
   - WebP format for thumbnails

4. **State Updates:**
   - Debounce node parameter changes
   - Batch state updates with Zustand
   - Memoize expensive components

### Backend Optimization

1. **Execution Engine:**
   - Parallel execution of independent nodes
   - Thread pool for CPU-bound tasks
   - GPU batch processing for SDXL

2. **WebSocket Updates:**
   - Throttle progress updates (max 10/sec)
   - Compress preview images (JPEG quality 80%)
   - Send diffs instead of full state

3. **Caching:**
   - Cache loaded models (SDXL, LoRA, etc.)
   - Cache intermediate node outputs
   - Redis for distributed caching (future)

4. **Memory Management:**
   - Clear node outputs after workflow complete
   - Stream large files instead of loading to memory
   - Garbage collect after each execution

---

## Security Considerations

1. **Input Validation:**
   - Sanitize all file paths (prevent directory traversal)
   - Validate image dimensions (prevent memory bombs)
   - Limit prompt length (prevent token overflow)

2. **Resource Limits:**
   - Max workflow size: 500 nodes
   - Max execution time: 10 minutes
   - Max output size: 100MB per node
   - Max concurrent executions: 5

3. **Content Safety:**
   - NSFW filter on all generated images
   - Prompt filtering (hate speech, violence)
   - User-configurable safety settings

4. **Authentication (Future):**
   - JWT-based authentication
   - API rate limiting
   - User workspace isolation

---

## Testing Strategy

### Unit Tests
- Each node type has dedicated test
- Test type validation on connections
- Test metadata propagation
- Test error handling

### Integration Tests
- Test complete workflows (end-to-end)
- Test WebSocket communication
- Test file I/O operations
- Test concurrent executions

### Performance Tests
- Benchmark node execution times
- Test with 100+ node graphs
- Memory leak detection
- Load testing (10 concurrent users)

### User Acceptance Tests
- Test all 118 nodes manually
- Verify editor functionality
- Test on multiple screen sizes
- Cross-browser testing (Chrome, Firefox, Safari)

---

## Success Metrics

### Functionality
- ✅ All 118 nodes implemented and tested
- ✅ Proper data flow between all node types
- ✅ Real-time preview in all 4 editors
- ✅ Inline thumbnails in nodes
- ✅ Metadata/lineage tracking working

### Performance
- ⚡ Node execution < 100ms overhead
- ⚡ WebSocket latency < 50ms
- ⚡ Editor rendering 60 FPS
- ⚡ Graph with 100 nodes renders smoothly

### User Experience
- 🎨 Split-panel layout responsive
- 🎨 No hunting for outputs (inline preview)
- 🎨 Keyboard shortcuts working
- 🎨 Intuitive node connections

---

## Comparison to Current UI

| Feature | Current UI | Redesigned UI |
|---------|------------|---------------|
| **Layout** | Full-screen nodes only | Split: 70% editor, 30% nodes |
| **Working Nodes** | 4-5 nodes | 118 nodes |
| **Data Flow** | Broken (text-only) | Type-safe all types |
| **Output Preview** | Hunt in outputs/ folder | Inline thumbnails + editor |
| **Editors** | None | Image/Video/3D/Text |
| **Real-time Updates** | None | WebSocket progress |
| **Metadata** | Not visible | Full lineage viewer |
| **Node Groups** | No | Yes (subgraphs) |
| **Batch Processing** | No | Yes (6 batch nodes) |
| **Validation** | No | Yes (8 QA nodes) |

**Improvement:** ~2000% increase in functionality and usability

---

## Known Limitations & Future Work

### Current Limitations
1. Single-user only (no collaboration)
2. No workflow versioning
3. No cloud storage integration
4. Limited to local GPU

### Future Enhancements (Post-V2)
1. **Multi-user Collaboration:**
   - Real-time collaborative editing
   - User cursors and selections
   - Conflict resolution

2. **Cloud Integration:**
   - RunPod / Vast.ai GPU offloading
   - Cloud storage (S3, GCS)
   - Workflow marketplace

3. **Advanced Features:**
   - Custom node creation UI
   - Visual scripting (loops, conditionals)
   - A/B testing workflows
   - Automated optimization

4. **Mobile Support:**
   - Responsive design for tablets
   - Touch-optimized controls
   - Mobile preview app

---

## Documentation Requirements

### User Documentation
- [ ] Quick start guide (5 min tutorial)
- [ ] Complete node reference (all 118 nodes)
- [ ] Video tutorials (YouTube series)
- [ ] Example workflows (10+ templates)
- [ ] FAQ / troubleshooting

### Developer Documentation
- [ ] Architecture overview (this document)
- [ ] API reference (backend endpoints)
- [ ] Custom node development guide
- [ ] Contributing guidelines
- [ ] Code style guide

---

## References & Sources

1. [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI) - Primary reference for node-based SDXL UI
2. [ComfyUI Web Viewer](https://github.com/VrchStudio/comfyui-web-viewer) - Real-time preview integration
3. [Blender Node Workflows](https://spin.atomicobject.com/blender-node-based-workflows/) - Split-panel layout inspiration
4. [React Flow](https://reactflow.dev) - Node editor library documentation
5. [Awesome Node-Based UIs](https://github.com/xyflow/awesome-node-based-uis) - Design patterns collection
6. [IP-Adapter Guide](https://stable-diffusion-art.com/ip-adapter/) - Image prompting nodes
7. [ControlNet Guide](https://stable-diffusion-art.com/controlnet/) - ControlNet integration
8. [Blender Geometry Nodes Design](https://developer.blender.org/T74967) - Node architecture patterns

---

**Document Status:** ✅ Complete - Ready for Implementation
**Next Step:** Begin Phase 1 implementation (split-panel layout + WebSocket)
**Estimated Timeline:** 6-7 weeks to production-ready V2.0

---

**END OF ARCHITECTURE DOCUMENT**
