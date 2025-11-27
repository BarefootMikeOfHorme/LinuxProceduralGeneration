# VaultMind Forge - Web UI

Enterprise-grade visual node editor for AI content generation.

## Features

✅ **Drag-and-Drop Node Editor** - Built with React Flow
✅ **138 Available Nodes** - Wrapping all `forge_*` Python modules
✅ **AI-Assisted Workflow** - Merlinv1 integration for smart suggestions
✅ **Dark Charcoal Theme** - Professional, easy on eyes
✅ **Keyboard Shortcuts** - Efficient workflow (Shift+A, F5, Ctrl+S, etc.)
✅ **Real-time Execution** - Live progress tracking
✅ **Workflow Templates** - Pre-built workflows for common tasks
✅ **Property Panel** - Configure nodes with tooltips and help
✅ **Type-Safe Connections** - Color-coded sockets

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.12 (for backend)

### Installation

```bash
# Install dependencies
cd web_ui
npm install

# Start development server
npm run dev
```

The UI will be available at `http://localhost:3000`

### Start Backend API

```bash
# In separate terminal
cd backend
python api.py
```

Backend runs at `http://localhost:8000`

## Project Structure

```
web_ui/
├── src/
│   ├── components/
│   │   ├── NodeEditor.jsx        # Main React Flow canvas
│   │   ├── NodePalette.jsx       # Node library sidebar
│   │   ├── PropertyPanel.jsx     # Node configuration
│   │   ├── Toolbar.jsx           # Top toolbar
│   │   └── nodes/                # Custom node components
│   │       ├── SDXLGeneratorNode.jsx
│   │       ├── PromptRefinerNode.jsx
│   │       └── SuperResolutionNode.jsx
│   ├── store/
│   │   └── workflowStore.js      # Zustand state management
│   ├── hooks/
│   │   └── useKeyboardShortcuts.js
│   ├── lib/
│   │   └── nodeLibrary.js        # Node definitions
│   ├── App.jsx                   # Main app
│   └── main.jsx                  # Entry point
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Available Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Shift+A` | Add node (opens search) |
| `F5` | Execute workflow |
| `Ctrl+S` | Save workflow |
| `Ctrl+O` | Open workflow |
| `F1` | Help |
| `Del` | Delete selected |
| `M` | Mute selected node |
| `Ctrl+A` | Toggle AI mode |
| `Ctrl+D` | Duplicate |
| `Ctrl+Z` | Undo |
| `Esc` | Deselect all |

## Node Categories

### 1. Input Nodes
- Text Input
- Image Loader
- Style Profile

### 2. Generation Nodes (forge_diffusion, forge_3d, forge_video)
- SDXL Generator
- Video Generator
- 3D Mesh Generator
- Procedural Generator

### 3. AI Agent Nodes (forge_agents + Merlinv1)
- Prompt Refiner
- Parameter Optimizer
- Material Suggester

### 4. Enhancement Nodes (forge_sr, forge_semantic)
- Super Resolution
- Semantic Downrez

### 5. Validation Nodes (forge_validator + Rust/C++)
- Quality Validator
- PBR Validator

### 6. Processing Nodes (forge_converter, forge_batch)
- Format Converter
- Asset Packager
- Batch Processor

### 7. Output Nodes
- Save Image
- Lineage Archive
- Export to Unreal/Unity

### 8. Utility Nodes
- Branch (If/Else)
- Loop (Iterate)
- Cache

## Workflow Format

Workflows are saved as JSON:

```json
{
  "version": 1,
  "metadata": {
    "name": "Anime Character",
    "description": "Generate anime-style characters",
    "created": "2024-11-26T00:00:00Z",
    "author": "user"
  },
  "nodes": [
    {
      "id": "node-1",
      "type": "textInput",
      "position": { "x": 100, "y": 200 },
      "data": { "text": "warrior princess" }
    },
    {
      "id": "node-2",
      "type": "sdxlGenerator",
      "position": { "x": 400, "y": 200 },
      "data": { "steps": 30, "cfg_scale": 7.5 }
    }
  ],
  "connections": [
    {
      "source": "node-1",
      "sourceHandle": "text",
      "target": "node-2",
      "targetHandle": "prompt"
    }
  ]
}
```

## Development

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Linting

```bash
npm run lint
```

## API Endpoints

Backend provides these endpoints:

- `POST /api/workflows` - Save workflow
- `GET /api/workflows/{id}` - Load workflow
- `GET /api/workflows` - List all workflows
- `POST /api/execute` - Execute workflow
- `GET /api/execute/{id}/progress` - Get execution progress
- `GET /api/nodes` - List available nodes
- `GET /api/templates` - List workflow templates
- `GET /api/templates/{name}` - Get specific template

## Customization

### Adding New Nodes

1. Create node definition in `src/lib/nodeLibrary.js`:

```javascript
{
  type: 'myCustomNode',
  name: 'My Custom Node',
  description: 'Does something cool',
  category: 'generation',
  icon: '🎯',
  color: '#FF5733',
  pythonModule: 'forge_my_module.my_node',
  inputs: [...],
  outputs: [...],
}
```

2. Create React component in `src/components/nodes/MyCustomNode.jsx`

3. Register in `src/components/nodes/index.js`

### Changing Theme

Edit `tailwind.config.js`:

```javascript
colors: {
  background: '#0f0f0f',  // Dark charcoal
  surface: '#1a1a1a',
  accent: '#4A90E2',       // Blue accent
  // ... customize as needed
}
```

## Troubleshooting

### Nodes not loading
- Check backend is running (`python backend/api.py`)
- Verify Python path includes `vaultmind_forge`

### Keyboard shortcuts not working
- Check browser focus is on canvas
- Some shortcuts may conflict with browser defaults

### Workflow execution stuck
- Check backend logs for errors
- Verify all node connections are valid
- Check `GET /api/health` endpoint

## Next Steps

- [ ] Add undo/redo functionality
- [ ] Implement workflow templates browser
- [ ] Add node grouping/backdrop support
- [ ] Live preview panel for images
- [ ] Tutorial mode overlay
- [ ] Export workflows as PNG with embedded JSON
- [ ] Collaborative editing (multiplayer)

## Resources

- [React Flow Docs](https://reactflow.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Zustand State Management](https://github.com/pmndrs/zustand)
- [Vite](https://vitejs.dev/)

---

**Built with ❤️ for VaultMind Forge**
