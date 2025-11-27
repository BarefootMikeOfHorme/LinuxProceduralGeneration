# Node Editor Research & Design Recommendations

## Research Sources

### Professional Compositing Software
1. **[Nuke](https://www.foundry.com/products/nuke-family/nuke)** - Industry-standard VFX compositor
2. **Blackmagic Fusion** - Node-based VFX and motion graphics
3. **[Blender Compositor](https://www.blendernation.com/2024/03/11/blender-vs-after-effects-vs-fusion-vfx-compositor-comparison/)** - Free node-based compositing

### AI/Diffusion Workflow Editors
4. **[ComfyUI](https://stable-diffusion-art.com/comfyui/)** - Node-based Stable Diffusion GUI
5. **[Natron](https://natrongithub.github.io/)** - Free open-source compositor

### Additional Resources
- [Layer vs Node Compositing](https://www.videomaker.com/article/c3/17836-nodes-vs-layers/)
- [Blender to Nuke Pipeline](https://www.helgemaus.de/new-compositing-tutorial-series-pipeline-between-blender-nuke/)
- [ComfyUI Workflow JSON Spec](https://docs.comfy.org/specs/workflow_json)
- [Nuke .nk File Structure](https://www.andrewboyles.com/thoughts/nuke-file-structure)
- [Blender Geometry Nodes Shortcuts](https://www.oneminutevideotutorials.com/2022/05/16/blender-keyboard-shortcuts-for-working-with-nodes/)

---

## Key Findings

### 1. File Format Comparison

| Software | Format | Structure | Best For |
|----------|--------|-----------|----------|
| **ComfyUI** | JSON | Human-readable, embedded in PNG | Sharing, version control, web APIs |
| **Nuke** | .nk (TCL) | Text-based script, top-to-bottom order | Professional workflows, VCS integration |
| **Blender** | .blend (binary) | Embedded in scene file | Integrated 3D workflows |
| **Fusion** | .comp | Binary with XML metadata | Performance, complex graphs |

**Recommendation for Vaultmind Forge:**
- **Primary**: JSON (like ComfyUI) - Human-readable, web-friendly, embeddable in images
- **Alternative**: YAML for cleaner hand-editing
- **Support**: Import/export to other formats (.nk, .comp)

### 2. JSON Workflow Format (Based on ComfyUI)

```json
{
  "version": 1,
  "metadata": {
    "name": "Anime Character Workflow",
    "description": "Generate anime-style characters",
    "author": "username",
    "created": "2024-11-26",
    "tags": ["anime", "character", "sdxl"]
  },
  "config": {
    "links_ontop": true,
    "align_to_grid": 20
  },
  "nodes": {
    "1": {
      "type": "TextInputNode",
      "pos": [100, 200],
      "size": [300, 100],
      "inputs": {},
      "outputs": {"text": "warrior princess"},
      "properties": {
        "ai_mode": false,
        "enabled": true
      }
    },
    "2": {
      "type": "SDXLGeneratorNode",
      "pos": [500, 200],
      "inputs": {
        "prompt": {"node": 1, "output": "text"},
        "width": 1024,
        "height": 1024
      },
      "outputs": {"image": null, "metadata": null}
    }
  },
  "connections": [
    {
      "from": [1, "text"],
      "to": [2, "prompt"]
    }
  ]
}
```

### 3. Keyboard Shortcuts (Industry Standard)

| Action | Blender | Nuke | ComfyUI | **Vaultmind Forge** |
|--------|---------|------|---------|---------------------|
| Add Node | Shift+A | Tab | Space | **Shift+A** |
| Delete Node | X | Delete | Delete | **Del or X** |
| Duplicate | Shift+D | Ctrl+C/V | Ctrl+C/V | **Shift+D** |
| Mute Node | M | D | - | **M** |
| Search Nodes | Shift+A (type) | Tab (type) | Space (type) | **Shift+A (type)** |
| Frame Selected | F | F | - | **F** |
| Auto-arrange | - | L | Q | **Ctrl+L** |
| Toggle Preview | - | - | - | **Ctrl+P** |
| Execute Graph | - | - | - | **F5** |

**Additional Shortcuts:**
- **Ctrl+G**: Group selection
- **Ctrl+Shift+G**: Ungroup
- **Ctrl+T**: Add reroute point
- **Ctrl+D**: Disable node (keep connections)
- **Alt+Click**: View node output
- **Middle Mouse Drag**: Pan canvas
- **Scroll Wheel**: Zoom
- **Shift+A → Start typing**: Quick search

### 4. UI/UX Patterns to Borrow

#### From ComfyUI:
✅ **Embedded workflows in images**: Save workflow JSON in PNG metadata
✅ **Drag-and-drop workflow loading**: Drop PNG/JSON to load
✅ **Queue system**: Batch execute multiple variations
✅ **Progress indicators**: Real-time per-node progress
✅ **Socket colors**: Visual type system (red=image, green=text, etc.)

#### From Nuke:
✅ **"B pipe" organization**: Standardized node flow (top-to-bottom or left-to-right)
✅ **Backdrop nodes**: Visual grouping with colored backgrounds
✅ **Sticky notes**: Annotations on canvas
✅ **Version tracking**: Built-in file versioning
✅ **Precomp workflow**: Export sub-graphs as separate files

#### From Blender Geometry Nodes:
✅ **Node Wrangler addon**: Quick preview, shortcuts, cleanup
✅ **Socket tooltips**: Hover for detailed info
✅ **Named reroutes**: Label connection points
✅ **Simulation zones**: Special node groups for iterative processes
✅ **Modifier stack integration**: Nodes as part of larger pipeline

### 5. Organization Best Practices

#### Nuke's "B Pipe" Structure:
```
┌─────────┐
│ Input A │──┐
└─────────┘  │
             ├──> ┌──────┐      ┌────────┐
┌─────────┐  │    │ Merge│─────>│ Output │
│ Input B │──┘    │ (over)│     └────────┘
└─────────┘       └──────┘
```
- **A input** (foreground) from top
- **B input** (background) from bottom
- **Merge operations** flow left-to-right

#### Grid Alignment:
- Snap to grid (20px or 40px)
- Vertical alignment for parallel processing
- Horizontal flow for sequential operations

#### Color Coding:
- **Red backdrop**: Critical/final output nodes
- **Blue backdrop**: Input/reference nodes
- **Green backdrop**: Processing nodes
- **Yellow backdrop**: WIP/experimental nodes

### 6. Node Connection Types

#### Socket Types (from ComfyUI/Blender):
```python
# Visual indicators
IMAGE:     Red circle    ●
VIDEO:     Orange circle ●
MESH_3D:   Blue circle   ●
TEXT:      Green circle  ●
NUMBER:    Gray circle   ●
BOOLEAN:   White circle  ○
SIGNAL:    Yellow star   ★
ANY:       Black circle  ●
```

#### Connection Validation:
- **Type-safe**: Can't connect incompatible types
- **Auto-convert**: Smart conversions (NUMBER → TEXT)
- **Multiple outputs**: One output → many inputs
- **Feedback loops**: Detect and prevent circular dependencies

### 7. Tutorial System (Best Practices)

#### Progressive Disclosure:
1. **First launch**: Interactive tutorial (like game tutorials)
2. **Tooltips**: Always available on hover
3. **Context help**: F1 on selected node
4. **Video links**: Embedded YouTube tutorials
5. **Example workflows**: One-click load examples

#### Tutorial Flow (Inspired by game UX):
```
Step 1: "Add your first node"
        [Highlight Shift+A area]
        [Wait for user to press Shift+A]

Step 2: "Search for 'SDXL Generator'"
        [Highlight search box]
        [Auto-suggest SDXL if user types 's']

Step 3: "Click to add the node"
        [Highlight SDXL node in list]

Step 4: "Great! Now let's configure it..."
        [Show node parameters with arrows]
```

### 8. AI Integration Points

#### Where AI Can Help:
1. **Node Suggestions**: "You might want to add a Super Resolution node next"
2. **Parameter Defaults**: "For anime style, I suggest cfg_scale=7.5"
3. **Error Diagnosis**: "Quality check failed because anatomy_score < 0.7"
4. **Workflow Optimization**: "This branch is redundant, you can remove it"
5. **Template Matching**: "Your workflow looks like 'Anime Character' template"

#### AI Control Modes:
```python
# Full auto (beginner)
node.ai_mode = "full"  # AI sets all parameters

# Assisted (intermediate)
node.ai_mode = "suggest"  # AI suggests, user approves

# Manual (expert)
node.ai_mode = "off"  # User controls everything
```

---

## Recommended Architecture for Vaultmind Forge

### File Structure:
```
~/.vaultmind/
├── workflows/
│   ├── my_workflow.json
│   ├── anime_character.json
│   └── game_asset.json
├── templates/
│   ├── anime_character.json
│   ├── game_asset_pbr.json
│   └── cad_model.json
├── shortcuts.json
├── preferences.json
└── recent.json
```

### Workflow JSON Schema:
```json
{
  "$schema": "https://vaultmind.forge/schemas/workflow.v1.json",
  "version": 1,
  "metadata": {
    "name": "string",
    "description": "string",
    "author": "string",
    "created": "ISO8601",
    "modified": "ISO8601",
    "tags": ["array"],
    "difficulty": "beginner|intermediate|advanced",
    "estimated_time_minutes": "number"
  },
  "config": {
    "grid_size": 20,
    "snap_to_grid": true,
    "auto_arrange": false,
    "execution_mode": "sequential|parallel"
  },
  "nodes": {
    "node_id": {
      "type": "NodeClassName",
      "pos": [x, y],
      "size": [width, height],
      "enabled": true,
      "ai_mode": "full|suggest|off",
      "inputs": {},
      "outputs": {},
      "cache": true
    }
  },
  "connections": [
    {
      "id": "uuid",
      "from": ["node_id", "output_name"],
      "to": ["node_id", "input_name"]
    }
  ],
  "groups": [
    {
      "title": "string",
      "nodes": ["array of node IDs"],
      "color": "#RRGGBB",
      "collapsed": false
    }
  ],
  "notes": [
    {
      "text": "string",
      "pos": [x, y],
      "color": "#RRGGBB"
    }
  ]
}
```

### Node Class Interface:
```python
class BaseNode:
    # Metadata
    METADATA = NodeMetadata(
        display_name="SDXL Generator",
        category=NodeCategory.GENERATION,
        icon="🎨",
        color="#E91E63",
        shortcuts={"preview": "Ctrl+G"},
        help_url="https://docs.../sdxl"
    )

    # I/O Definitions
    INPUTS = [
        NodeInput(
            name="prompt",
            type=DataType.TEXT,
            required=True,
            tooltip="Describe your image",
            ai_default=lambda ctx: merlinv1_suggest(ctx)
        )
    ]

    OUTPUTS = [
        NodeOutput(
            name="image",
            type=DataType.IMAGE,
            tooltip="Generated image"
        )
    ]

    # Execution
    def execute(self, inputs: Dict) -> Dict:
        # Actual logic here
        result = self.run_generation(inputs)
        return {"image": result}

    # Validation
    def validate_inputs(self, inputs: Dict) -> tuple[bool, List[str]]:
        # Check inputs are valid
        return True, []

    # Help
    def get_help(self) -> Dict:
        # Return help information
        return {...}
```

---

## Implementation Phases

### Phase 1: Core Engine (Week 1-2)
- [x] BaseNode class
- [x] DataType system
- [x] JSON workflow format
- [ ] Node registry
- [ ] Graph executor (topological sort)
- [ ] Connection validation
- [ ] Error handling

### Phase 2: Essential Nodes (Week 3-4)
- [ ] TextInputNode
- [ ] SDXLGeneratorNode (forge_diffusion)
- [ ] PromptRefinerNode (forge_agents + Merlinv1)
- [ ] SuperResolutionNode (forge_sr)
- [ ] QualityValidatorNode (forge_validator)
- [ ] AssetPackagerNode (forge_packaging)
- [ ] SaveImageNode
- [ ] BranchNode (if/else)
- [ ] LoopNode (iteration)

### Phase 3: Terminal UI (Week 5-6)
- [ ] Textual-based node canvas
- [ ] Keyboard navigation
- [ ] Visual node connections
- [ ] Property panel
- [ ] Output preview
- [ ] Tutorial overlay

### Phase 4: Web UI (Week 7-8)
- [ ] React + React Flow setup
- [ ] Node palette
- [ ] Canvas with zoom/pan
- [ ] Connection drawing
- [ ] Real-time execution
- [ ] Image preview panel

### Phase 5: Templates & AI (Week 9-10)
- [ ] 5 built-in templates
- [ ] Template browser
- [ ] Merlinv1 node suggestions
- [ ] Auto-complete connections
- [ ] Smart parameter defaults
- [ ] Interactive tutorials

---

## Quick Wins to Implement First

1. **JSON Workflow Format**: Adopt ComfyUI-style JSON
   - Easy to implement
   - Human-readable
   - Web-friendly
   - Can embed in PNG metadata

2. **Essential Keyboard Shortcuts**:
   ```python
   SHORTCUTS = {
       "add_node": "Shift+A",
       "delete_node": "Del",
       "execute_graph": "F5",
       "toggle_ai": "Ctrl+A",
       "help": "F1",
   }
   ```

3. **Socket Color System**:
   ```python
   SOCKET_COLORS = {
       DataType.IMAGE: "#FF5555",    # Red
       DataType.TEXT: "#55FF55",     # Green
       DataType.NUMBER: "#888888",   # Gray
       DataType.VIDEO: "#FF8855",    # Orange
       DataType.MESH_3D: "#5555FF",  # Blue
   }
   ```

4. **Grid System**: 20px snap grid like Fusion

5. **B-Pipe Flow**: Left-to-right or top-to-bottom standard

---

## Inspiration Gallery

### ComfyUI Workflow Example:
![ComfyUI Screenshot](https://stable-diffusion-art.com/wp-content/uploads/2023/06/image-109.png)
- **Pros**: Clean, color-coded, easy to share
- **Cons**: Can get messy with complex workflows

### Nuke Node Graph:
![Nuke Screenshot](https://definitionmagazine.com/wp-content/uploads/2016/11/nuke-vfx-software.jpg)
- **Pros**: Professional, organized, robust
- **Cons**: Steep learning curve

### Blender Geometry Nodes:
- **Pros**: Integrated, powerful, well-documented
- **Cons**: Blender-specific

---

## Recommended Stack

### For Terminal UI:
- **[Textual](https://github.com/Textualize/textual)**: Modern TUI framework (Python)
- **Rich**: Terminal formatting (already used in Vaultmind Forge)
- **Blessed**: Keyboard input handling

### For Web UI:
- **React**: UI framework
- **[React Flow](https://reactflow.dev/)**: Node editor library
- **Tailwind CSS**: Styling
- **FastAPI**: Python backend API

### For Both:
- **NetworkX**: Graph algorithms (topological sort, cycle detection)
- **Pydantic**: Data validation
- **JSON Schema**: Workflow validation

---

## Next Steps

1. **Finalize workflow JSON schema** (use ComfyUI as reference)

2. **Implement graph executor** with topological sort

3. **Create 3 example nodes**:
   - TextInputNode (simple)
   - SDXLGeneratorNode (moderate)
   - PromptRefinerNode (AI integration)

4. **Build minimal Terminal UI** to test workflow

5. **Create 1 complete template** (Anime Character)

6. **Get user feedback** on workflow format and UI

---

**All research compiled from professional VFX, AI workflow, and 3D software industry leaders. Ready to implement!**

## Sources

- [Stable Diffusion Art - ComfyUI Guide](https://stable-diffusion-art.com/comfyui/)
- [ComfyUI Workflow JSON Spec](https://docs.comfy.org/specs/workflow_json)
- [Andrew Boyles - Nuke File Structure](https://www.andrewboyles.com/thoughts/nuke-file-structure)
- [Blender vs After Effects vs Fusion Comparison](https://www.blendernation.com/2024/03/11/blender-vs-after-effects-vs-fusion-vfx-compositor-comparison/)
- [Blender Geometry Nodes Manual](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/index.html)
- [CG Cookie - Geometry Nodes Cheat Sheet](https://cgcookie.com/downloads/geometry-nodes-cheat-sheet)
- [Videomaker - Nodes vs Layers](https://www.videomaker.com/article/c3/17836-nodes-vs-layers/)
