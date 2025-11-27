# Vaultmind Forge - Node System Architecture

## Overview

The node system transforms Vaultmind Forge's **138 Python/Rust/C++ modules** into an enterprise-grade visual workflow editor. Every `forge_*` module becomes a drag-and-drop node with:

✅ **Smart Help System**: Contextual tooltips, tutorials, keyboard shortcuts
✅ **AI Control**: Merlinv1 can configure nodes automatically or assist user
✅ **Type Safety**: Strongly-typed connections between nodes
✅ **Enterprise Templates**: Pre-built workflows for common tasks
✅ **Live Preview**: See results as you build
✅ **Lineage Tracking**: Every execution tracked and archivable

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    UI LAYER (Future)                     │
│  Web UI (React + React Flow) | Terminal UI (Textual)    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   NODE GRAPH ENGINE                      │
│  • Execution (topological sort)                          │
│  • Validation (type checking)                            │
│  • Caching (avoid recomputation)                         │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    NODE LIBRARY                          │
│  138 modules wrapped as nodes:                           │
│  • forge_diffusion → SDXL Generator Node                 │
│  • forge_sr → Super Resolution Node                      │
│  • forge_ai → Merlinv1 Agent Node                        │
│  • forge_3d → Mesh Generator Node                        │
│  • ... and 134 more                                      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│               NATIVE MODULES (Py/Rust/C++)               │
│  Actual computation happens here                         │
└─────────────────────────────────────────────────────────┘
```

---

## Current Codebase Analysis

**From `analyze_codebase.py`:**

| Module Category | Files | Purpose | Node Type |
|-----------------|-------|---------|-----------|
| forge_ai | 14 PY | AI backends (Merlinv1, Claude, GPT) | AI Agent Nodes |
| forge_diffusion | 7 PY | Image generation (SDXL, etc.) | Generation Nodes |
| forge_agents | 9 PY | Specialized AI agents | AI Agent Nodes |
| forge_sr | 2 PY | Super-resolution | Enhancement Nodes |
| forge_video | 2 PY | Video generation | Generation Nodes |
| forge_3d | 2 PY | 3D mesh generation | Generation Nodes |
| forge_validator | 7 PY | Quality validation | Validation Nodes |
| forge_converter | 13 PY | Format conversion | Processing Nodes |
| forge_procedural | 5 PY | Procedural generation | Generation Nodes |
| forge_batch | 4 PY | Batch processing | Utility Nodes |
| **native/rust** | **7 RS** | High-speed validators | Validation Nodes |
| **native/cpp** | **3 C++** | System-level control | Validation Nodes |

**Total: 138 modules = 138 potential node types!**

---

## Node Types by Category

### 1. Input Nodes
Connect external data to the graph:
- **Text Input**: Manual prompt entry
- **Image Loader**: Load reference images
- **Style Profile Selector**: Choose from style library
- **Batch Input**: Process multiple items
- **Drop Folder Monitor** (`forge_intake`): Auto-detect new files

### 2. Generation Nodes
Create new content:
- **SDXL Generator** (`forge_diffusion`): Text-to-image
- **Video Generator** (`forge_video`): Image-to-video
- **3D Mesh Generator** (`forge_3d`): Text/image-to-3D
- **Procedural Generator** (`forge_procedural`): Noise-based generation
- **Billboard Generator**: Procedural backgrounds

### 3. Enhancement Nodes
Improve existing content:
- **Super Resolution** (`forge_sr`): Upscale images
- **Semantic Downrez** (`forge_semantic`): Smart resize
- **Color Correction**: Palette enforcement
- **Refiner**: Detail enhancement

### 4. AI Agent Nodes (🚀 This is where Merlinv1 shines!)
- **Prompt Refiner** (`forge_agents`): Enhance prompts with Merlinv1
- **Parameter Optimizer**: Find best settings
- **Material Suggester**: PBR material recommendations
- **Quality Guardian**: AI-powered quality assessment
- **Merlinv1 Planner** (`forge_ai`): Job orchestration

### 5. Validation Nodes
Quality control:
- **Quality Validator** (`forge_validator` + Rust/C++): Multi-metric checks
- **Anatomy Validator**: Character anatomy checks
- **PBR Validator**: Material validation
- **Drift Detector**: Consistency checks

### 6. Processing Nodes
Transform data:
- **Format Converter** (`forge_converter`): FBX, USD, DDS, etc.
- **Asset Packager** (`forge_packaging`): Bundle for export
- **Batch Processor** (`forge_batch`): Process queues

### 7. Output Nodes
Save results:
- **Save Image**: Write to disk
- **Export to Unreal**: UE5-ready assets
- **Export to Unity**: Unity packages
- **Lineage Archive** (`forge_lineage`): Archive with metadata

### 8. Utility Nodes
Control flow:
- **Branch**: Conditional execution
- **Loop**: Iterate over collections
- **Cache**: Store intermediate results
- **Monitor** (`forge_monitor`): System metrics

---

## Node Definition Example

Every module becomes a node by extending `BaseNode`:

```python
from forge_nodes import BaseNode, NodeInput, NodeOutput, NodeMetadata

class SDXLGeneratorNode(BaseNode):
    # Metadata (help, shortcuts, etc.)
    METADATA = NodeMetadata(
        display_name="SDXL Generator",
        description="Generate images with SDXL",
        category=NodeCategory.GENERATION,
        help_text="...",
        shortcuts={"generate": "Ctrl+G"},
        ai_controllable=True,  # AI can control this!
    )

    # Define inputs with validation & help
    INPUTS = [
        NodeInput(
            name="prompt",
            data_type=DataType.TEXT,
            required=True,
            tooltip="Describe your image in detail",
            help_url="https://docs.../prompting",
        ),
        # ... more inputs
    ]

    # Define outputs
    OUTPUTS = [
        NodeOutput(
            name="image",
            data_type=DataType.IMAGE,
            description="Generated image",
        ),
    ]

    # Actual execution logic
    def execute(self, inputs):
        from ...forge_diffusion import SDXLGenerator
        generator = SDXLGenerator()
        result = generator.generate(**inputs)
        return {"image": result}
```

**That's it!** The module is now a visual node.

---

## Workflow Templates

Pre-built, enterprise-grade workflows with tutorials:

### Template: Anime Character

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Text Input   │────>│ Prompt       │────>│ SDXL         │
│              │     │ Refiner      │     │ Generator    │
│              │     │ (Merlinv1)   │     │ [anime]      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                                                  v
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Asset        │<────│ Quality      │<────│ Super        │
│ Packager     │     │ Validator    │     │ Resolution   │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Tutorial Steps:**
1. Enter character description
2. Merlinv1 refines prompt automatically
3. SDXL generates anime-style art
4. SR upscales to high-res
5. Validator checks quality
6. Packager creates asset bundle with lineage

**Estimated time**: 3 minutes

### Template: Game Asset (PBR)

Complex multi-stage workflow:
1. Concept art generation
2. 3D mesh from 2D reference
3. PBR texture generation (albedo, normal, roughness, metallic)
4. Material validation (Rust/C++ validators)
5. Export to Unreal/Unity

**Estimated time**: 10 minutes

---

## AI Control System

Nodes can operate in two modes:

### 1. AI Mode (Default)
- Merlinv1 suggests optimal parameters
- Auto-connects compatible nodes
- Provides real-time hints
- Adapts based on previous results

```python
# AI suggests prompt refinement
refined = merlinv1_node.get_ai_suggestion(
    "prompt",
    context={"previous_output": prev_image}
)
```

### 2. User Override Mode
- User takes full control
- AI suggestions still available as hints
- Shortcuts for quick edits

```python
# User manually sets all parameters
node.disable_ai_mode()
node.input_values["prompt"] = "my custom prompt"
```

**Switch anytime**: Press `Ctrl+A` to toggle AI assist on/off

---

## Keyboard Shortcuts (Built Dynamically)

Shortcuts are built as you use nodes:

| Action | Shortcut | Scope |
|--------|----------|-------|
| Execute graph | `F5` | Global |
| Stop execution | `Esc` | Global |
| Toggle AI mode | `Ctrl+A` | Current node |
| Quick preview | `Ctrl+G` | Generator nodes |
| Edit prompt | `Ctrl+E` | Text nodes |
| Open help | `F1` | Current node |
| Save workflow | `Ctrl+S` | Global |
| Load template | `Ctrl+O` | Global |

**Custom shortcuts** saved per-user in `~/.vaultmind/shortcuts.json`

---

## Help System

Every node has multi-level help:

### Level 1: Tooltips
Hover over input → see tooltip instantly

### Level 2: Help Panel
Press `F1` → detailed help with:
- Input/output descriptions
- Parameter ranges and tips
- Common mistakes
- Related nodes

### Level 3: Tutorials
Interactive step-by-step guides:
- Highlights relevant nodes
- Shows example values
- Validates your progress
- Links to video tutorials

### Level 4: AI Assistance
Ask Merlinv1:
- "How do I improve image quality?"
- "What parameters should I use for anime style?"
- "Why did validation fail?"

---

## Type System

Connections are type-safe:

```python
class DataType(Enum):
    IMAGE = "image"      # PIL Image, numpy array
    VIDEO = "video"      # Video frames or path
    MESH_3D = "mesh_3d"  # 3D mesh (trimesh)
    TEXT = "text"        # String
    NUMBER = "number"    # Int/float
    PROMPT = "prompt"    # Structured prompt
    STYLE = "style"      # Style profile
    BATCH = "batch"      # List of items
    ANY = "any"          # Wildcard
```

**Invalid connections rejected**:
- Can't connect TEXT to IMAGE
- But can connect IMAGE to ANY

**Auto-conversion** when sensible:
- NUMBER → TEXT (str(num))
- IMAGE → BATCH ([image])

---

## Execution Engine

Graph executes in topological order:

```python
from forge_nodes import NodeGraph, GraphExecutor

# Build graph
graph = NodeGraph()
graph.add_node(text_input)
graph.add_node(sdxl_generator)
graph.connect(text_input, "text", sdxl_generator, "prompt")

# Execute
executor = GraphExecutor(graph)
result = executor.execute()

# Result includes:
# - Output values
# - Execution time per node
# - Lineage metadata
# - Cached intermediate results
```

**Features:**
- **Topological sort**: Executes in dependency order
- **Caching**: Reuse unchanged node outputs
- **Parallel execution**: Independent nodes run concurrently
- **Error recovery**: Continues after non-critical failures
- **Progress tracking**: Real-time execution updates

---

## Visual Editor (Future)

Two options being considered:

### Option A: Web UI (React + React Flow)
**Pros:**
- Rich visual editing
- Cross-platform (runs in browser)
- Easy deployment
- Great ecosystem

**Cons:**
- Requires web server
- Harder to integrate with local files

### Option B: Terminal UI (Textual + Rich)
**Pros:**
- Native CLI integration
- Works over SSH
- Lightweight
- Matches Vaultmind Forge aesthetic

**Cons:**
- More limited visually
- Steeper learning curve

**Current plan**: Build both! Web UI for designers, Terminal UI for power users.

---

## Implementation Roadmap

### Phase 1: Core (Current)
- ✅ BaseNode class with input/output/metadata
- ✅ DataType system
- ✅ Node validation
- ✅ AI control modes
- ✅ Help system
- ✅ Workflow templates
- ⏳ Node registry
- ⏳ Graph executor

### Phase 2: Node Library (Next)
- ⏳ Wrap 10 key modules as nodes:
  - SDXL Generator
  - Super Resolution
  - Merlinv1 Prompt Refiner
  - Quality Validator
  - Asset Packager
  - Etc.
- ⏳ Auto-generate nodes from Python introspection
- ⏳ Rust/C++ node bindings (FFI)

### Phase 3: Templates & Tutorials
- ⏳ 5 built-in templates:
  - Anime Character
  - Game Asset (PBR)
  - CAD Model
  - Storyboard
  - Video Cinematic
- ⏳ Interactive tutorial system
- ⏳ Example assets

### Phase 4: Visual Editor
- ⏳ Terminal UI prototype (Textual)
- ⏳ Web UI prototype (React)
- ⏳ Keyboard shortcuts system
- ⏳ Live preview panels
- ⏳ Asset browser

### Phase 5: AI Integration
- ⏳ Merlinv1 node suggestions
- ⏳ Auto-complete connections
- ⏳ Smart defaults from context
- ⏳ Conversational editing ("make it more anime")

---

## Next Steps

1. **Test the foundation**: Run `python analyze_codebase.py` to see module breakdown

2. **Explore base node**: Read `forge_nodes/base_node.py` for architecture

3. **Try example node**: See `forge_nodes/nodes/sdxl_node.py` for SDXL wrapper

4. **Workflow templates**: Check `forge_nodes/workflow_template.py` for pre-built workflows

5. **Research inspiration**: Look at:
   - ComfyUI (Stable Diffusion node editor)
   - Blender Geometry Nodes
   - Unreal Engine Blueprints
   - Houdini's procedural network

6. **Decide on UI**: Web (React Flow) vs Terminal (Textual)?

7. **Start wrapping modules**: Pick 5 key `forge_*` modules to convert to nodes

---

## Questions for User

1. **UI Preference**: Web-based or terminal-based editor? (Or both?)

2. **Priority Modules**: Which 5 modules should we wrap as nodes first?
   - forge_diffusion (SDXL)?
   - forge_ai (Merlinv1)?
   - forge_sr (upscaling)?
   - forge_3d (mesh gen)?
   - forge_agents (prompt refiner)?

3. **Template Focus**: What workflows are most important?
   - Anime/manga?
   - Game assets?
   - CAD models?
   - Video/animation?

4. **Keyboard Shortcuts**: Any specific shortcuts you want?

5. **Merlinv1 Role**: How should Merlinv1 integrate?
   - Prompt refinement?
   - Parameter suggestions?
   - Workflow planning?
   - All of the above?

---

## Technical Notes

**Performance:**
- Nodes cached by default (avoid re-execution)
- Parallel execution for independent branches
- Lazy loading of heavy modules
- GPU sharing across nodes

**Storage:**
- Workflows saved as JSON
- Templates in `forge_nodes/templates/`
- User workflows in `~/.vaultmind/workflows/`
- Lineage archives linked to graph execution

**Extensibility:**
- New nodes: Just extend `BaseNode`
- New data types: Add to `DataType` enum
- New templates: Create `WorkflowTemplate` instance
- Custom validators: Override `validate_inputs()`

---

## Inspiration & Resources

**Similar Systems:**
- **ComfyUI**: Node-based SD workflow (our closest inspiration)
- **Blender Geometry Nodes**: Procedural 3D modeling
- **Unreal Blueprints**: Visual scripting for games
- **Houdini**: Procedural VFX network
- **TouchDesigner**: Real-time visual programming

**Libraries:**
- **React Flow**: Web-based node editor
- **Textual**: Terminal UI framework (Python)
- **Rich**: Terminal formatting
- **NetworkX**: Graph algorithms

**Design Principles:**
- **Discoverability**: Easy to find nodes
- **Predictability**: Clear input/output behavior
- **Forgivability**: Easy to undo/redo
- **Efficiency**: Keyboard-first workflow
- **Learnability**: Progressive disclosure (beginner → advanced)

---

**The node system transforms Vaultmind Forge from a collection of modules into a unified, visual, AI-assisted content creation platform. 🚀**
