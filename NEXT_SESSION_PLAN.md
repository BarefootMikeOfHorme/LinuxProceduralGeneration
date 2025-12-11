# VaultMind Forge - Next Session Action Plan

## Current State (Session End)

### ✅ Completed
1. **Security Audit** - Enterprise-grade security middleware implemented
2. **Multi-Editor Architecture** - Tab system, asset browser, properties panel built
3. **Tab System Fix** - Converted from editor-type-based to asset-based (CRITICAL FIX)
4. **Editor Type Definitions** - 13 editor types defined with full metadata

### 🏗️ VaultMind Forge Architecture (Full Picture)

**Project:** AI-powered procedural asset generation framework

**3-Layer Architecture:**
```
┌─────────────────────────────────────────────┐
│  WEB UI (React/Vite) - web_ui/              │
│  ├─ Multi-Editor Studio (NEW - just built)  │
│  ├─ Workflow Editor (ReactFlow nodes)       │
│  └─ Asset Browser, Properties Panel         │
└─────────────────┬───────────────────────────┘
                  │ HTTP
┌─────────────────▼───────────────────────────┐
│  BACKEND (FastAPI) - backend/api.py         │
│  ├─ REST API endpoints                      │
│  ├─ Workflow execution engine               │
│  └─ Node registry & orchestration           │
└─────────────────┬───────────────────────────┘
                  │ Direct calls
┌─────────────────▼───────────────────────────┐
│  PYTHON EXECUTORS (Main Orchestrators)      │
│  backend/executors/                         │
│  ├─ input_nodes.py - TextInput, NumberInput │
│  ├─ generation_nodes.py - SDXL generation   │
│  ├─ processing_nodes.py - SuperResolution   │
│  ├─ ai_nodes.py - PromptRefiner             │
│  ├─ controlnet_nodes.py                     │
│  └─ converter_pro_nodes.py                  │
└─────────────────┬───────────────────────────┘
                  │ PyO3/FFI
┌─────────────────▼───────────────────────────┐
│  NATIVE (Performance Critical)              │
│  ├─ Rust: validator (PyO3 bindings)         │
│  └─ C++: color_fidelity, geometry checks    │
└─────────────────────────────────────────────┘
```

**Node Execution Flow:**
1. User creates workflow in Web UI (ReactFlow graph)
2. Backend receives workflow JSON via /api/workflow/execute
3. Python executors run each node (SDXL, upscaling, etc.)
4. Rust/C++ called for heavy validation/processing
5. Results returned to Web UI with lineage tracking

**OLD API Layer (src/):**
- Node.js/Express wrapper around Python CLI
- Used for standalone lineage viewer
- Separate from new React web_ui/

**NEW Web UI (web_ui/):**
- React + Vite + ReactFlow
- Multi-editor studio (what we just built)
- Talks directly to FastAPI backend

### 🔧 Existing Node System (Workflow Editor)
The Workflow Editor already has a working node system with:

**Python Nodes (Backend Executors):**
- `TextInputExecutor` - Text input node
- `NumberInputExecutor` - Number input node
- `SDXLGeneratorExecutor` - SDXL image generation
- `SuperResolutionExecutor` - Image upscaling
- `PromptRefinerExecutor` - AI prompt refinement

**Node Categories:**
- Input nodes (`input_nodes.py`)
- Generation nodes (`generation_nodes.py`)
- Processing nodes (`processing_nodes.py`)
- AI nodes (`ai_nodes.py`)
- ControlNet nodes (`controlnet_nodes.py`)
- Converter Pro nodes (`converter_pro_nodes.py`)
- Additional nodes (`additional_nodes.py`)

**Rust Components:**
- Validator (`vaultmind_forge/native/rust/validator/`) - Performance-critical validation

**Web UI:**
- `NodeEditor.jsx` - Main workflow editor with ReactFlow
- `BaseNode.jsx` - Base node component
- `PropertyPanelWorkflow.jsx` - Node property editor

**Note:** The Workflow Editor is FULLY FUNCTIONAL. New editors are for different asset types (images, prompts, etc.), not replacing the workflow editor.

### 📋 Editor Types Defined (13 Total)
**Original Editors (8):**
- Workflow Editor (exists - NodeEditor component)
- Image Editor
- Prompt Editor
- Material Editor
- Video Editor
- 3D Viewer (Mesh)
- Batch Processor
- Audio Editor

**Pipeline-Specific Editors (5):**
- Pipeline Editor (multi-stage processing)
- Automation Editor (event-driven workflows)
- Template Editor (reusable workflows)
- Parameter Sweep (grid exploration)
- Comparison Viewer (side-by-side results)

---

## Next Session: Implementation Priority

### Phase 1: High-Value Editors (Build These First)

#### 1. **Comparison Viewer** (PRIORITY 1)
**Why First:** Immediate value for reviewing/comparing generation results
**Files to Create:**
- `web_ui/src/components/editors/ComparisonViewer.jsx`
- `web_ui/src/components/editors/ComparisonGrid.jsx`
- `web_ui/src/components/editors/ComparisonControls.jsx`

**Features to Implement:**
- [ ] Grid layout (2-6 assets side-by-side)
- [ ] Asset selection from asset browser
- [ ] Synchronized zoom/pan toggle
- [ ] Rating system (1-5 stars)
- [ ] Metadata panel showing parameters
- [ ] Export selected assets
- [ ] Keyboard shortcuts (Left/Right for navigation)

**Estimated Complexity:** Medium (UI-heavy, no backend needed initially)

---

#### 2. **Prompt Editor** (PRIORITY 2)
**Why Second:** Core to the generation workflow, high usage
**Files to Create:**
- `web_ui/src/components/editors/PromptEditor.jsx`
- `web_ui/src/components/editors/PromptTemplates.jsx`
- `web_ui/src/components/editors/PromptModifiers.jsx`
- `web_ui/src/components/editors/PromptHistory.jsx`

**Features to Implement:**
- [ ] Rich text editor with syntax highlighting
- [ ] Template library (dropdown selector)
- [ ] Modifier tags (drag-and-drop or quick-add)
- [ ] Negative prompt section
- [ ] Token counter (show approximate token usage)
- [ ] Prompt history (last 20 prompts)
- [ ] Save prompt as asset
- [ ] Copy to clipboard

**Estimated Complexity:** Medium-High (needs template system)

---

#### 3. **Parameter Sweep** (PRIORITY 3)
**Why Third:** Enables systematic experimentation and optimization
**Files to Create:**
- `web_ui/src/components/editors/ParameterSweep.jsx`
- `web_ui/src/components/editors/AxisEditor.jsx`
- `web_ui/src/components/editors/SweepResults.jsx`
- `backend/routes/sweep.py` (API for sweep execution)

**Features to Implement:**
- [ ] Axis configuration (parameter name, min, max, step)
- [ ] Range type selector (linear, logarithmic, custom)
- [ ] Preview grid showing all combinations
- [ ] Execute sweep (send to workflow queue)
- [ ] Progress tracking
- [ ] Results grid with thumbnails
- [ ] Best result highlighting
- [ ] Export results as dataset

**Estimated Complexity:** High (requires backend integration)

---

#### 4. **Template Editor** (PRIORITY 4)
**Why Fourth:** Enables workflow reuse and sharing
**Files to Create:**
- `web_ui/src/components/editors/TemplateEditor.jsx`
- `web_ui/src/components/editors/ParameterDefiner.jsx`
- `web_ui/src/components/editors/TemplatePreview.jsx`
- `backend/routes/templates.py` (CRUD for templates)

**Features to Implement:**
- [ ] Load base workflow
- [ ] Define parameters (name, type, default, constraints)
- [ ] Parameter UI (text, number, slider, dropdown)
- [ ] Live preview of template with current values
- [ ] Save template to library
- [ ] Instantiate template (create new workflow from template)
- [ ] Template marketplace (list, search, import)

**Estimated Complexity:** High (workflow parameterization is complex)

---

### Phase 2: Pipeline Editors

#### 5. **Pipeline Editor**
**Files to Create:**
- `web_ui/src/components/editors/PipelineEditor.jsx`
- Use ReactFlow for stage graph (already have it)

**Features:**
- [ ] Stage graph (nodes = stages, edges = dependencies)
- [ ] Stage configuration (workflow, inputs, outputs)
- [ ] Execution mode (sequential, parallel)
- [ ] Error handling options
- [ ] Execute pipeline
- [ ] Progress visualization

**Estimated Complexity:** High (multi-stage execution)

---

#### 6. **Automation Editor**
**Files to Create:**
- `web_ui/src/components/editors/AutomationEditor.jsx`
- `backend/automation/scheduler.py`

**Features:**
- [ ] Trigger definition (time-based, file-watch, webhook)
- [ ] Condition builder (if/then logic)
- [ ] Action sequence builder
- [ ] Enable/disable toggle
- [ ] Execution history viewer
- [ ] Test/dry-run mode

**Estimated Complexity:** Very High (requires backend scheduler)

---

### Phase 3: Content Editors

#### 7. **Image Editor**
**Complexity:** Very High (layer system, non-destructive editing)
**Consider:** Use existing library (e.g., Fabric.js, Konva) or integrate external tool

#### 8. **Material Editor**
**Complexity:** High (PBR preview requires WebGL/Three.js)

#### 9. **Video Editor**
**Complexity:** Very High (timeline, encoding)

#### 10. **3D Viewer**
**Complexity:** Medium-High (Three.js integration)

#### 11. **Batch Processor**
**Complexity:** Medium (UI for bulk operations)

---

## Implementation Strategy

### Step-by-Step Approach
1. **Create editor component** in `web_ui/src/components/editors/`
2. **Update Studio.jsx** to import and render the new component
3. **Test opening the editor** via asset browser or new tab button
4. **Implement core features** incrementally
5. **Connect to backend APIs** (if needed)
6. **Update PropertiesPanel.jsx** with editor-specific properties
7. **Test keyboard shortcuts**
8. **Commit when functional**

### File Organization
```
web_ui/src/components/editors/
├── ComparisonViewer.jsx         (Phase 1.1)
├── PromptEditor.jsx              (Phase 1.2)
├── ParameterSweep.jsx            (Phase 1.3)
├── TemplateEditor.jsx            (Phase 1.4)
├── PipelineEditor.jsx            (Phase 2.1)
├── AutomationEditor.jsx          (Phase 2.2)
├── ImageEditor.jsx               (Phase 3)
├── MaterialEditor.jsx            (Phase 3)
├── VideoEditor.jsx               (Phase 3)
├── MeshViewer.jsx                (Phase 3)
└── BatchProcessor.jsx            (Phase 3)
```

---

## Backend Work Needed

### API Endpoints to Create
1. **Templates API** (`/api/templates`)
   - GET /api/templates (list all)
   - POST /api/templates (create)
   - GET /api/templates/:id (get one)
   - PUT /api/templates/:id (update)
   - DELETE /api/templates/:id (delete)
   - POST /api/templates/:id/instantiate (create workflow from template)

2. **Sweep API** (`/api/sweeps`)
   - POST /api/sweeps (create and execute sweep)
   - GET /api/sweeps/:id (get sweep status)
   - GET /api/sweeps/:id/results (get results)
   - DELETE /api/sweeps/:id (cancel sweep)

3. **Automation API** (`/api/automations`)
   - CRUD operations similar to templates
   - POST /api/automations/:id/enable
   - POST /api/automations/:id/disable
   - POST /api/automations/:id/test (dry run)

---

## Quick Wins for Next Session

### Option A: Start with Comparison Viewer (Recommended)
- **Time:** 1-2 hours
- **Value:** Immediate usability improvement
- **Complexity:** Medium (no backend needed)
- **User Impact:** High (see results side-by-side)

### Option B: Start with Prompt Editor
- **Time:** 2-3 hours
- **Value:** High for workflow improvement
- **Complexity:** Medium-High
- **User Impact:** Very High (core feature)

### Option C: Build Multiple Simple Features
- Basic Comparison Viewer (1 hour)
- Basic Prompt Editor (1 hour)
- Then polish both

---

## Testing Checklist (Per Editor)

- [ ] Can open editor via asset browser double-click
- [ ] Can create new asset with editor type
- [ ] Tab shows asset name correctly
- [ ] Modified indicator works
- [ ] Keyboard shortcuts work
- [ ] Properties panel shows correct properties
- [ ] Can save asset
- [ ] Can close tab (with unsaved warning if modified)
- [ ] State persists when switching tabs

---

## Notes for Next Session

### Architecture is SOLID
- Tab system is asset-based (correct pattern)
- Editor registry is comprehensive
- State management is in place
- Just need to build the actual editor UIs

### Start Simple, Iterate
- Don't over-engineer on first pass
- Get basic functionality working first
- Polish and add features incrementally
- User feedback will guide priorities

### Key Files to Remember
- `editorRegistry.js` - All editor metadata
- `editorStore.js` - All editor state
- `Studio.jsx` - Main render logic
- `PropertiesPanel.jsx` - Context-aware properties

---

## Questions to Ask User Next Session

1. Which editor provides the most value to implement first?
2. Are there specific features for Comparison Viewer that are must-haves?
3. Should we integrate existing image editing libraries or build custom?
4. What's the priority: more basic editors or fewer polished editors?
5. Any specific pipeline workflows we should optimize for?

---

## Git Status
- **Last Commit:** feat: Add 5 pipeline-specific editor types for automated workflows
- **Branch:** master
- **Clean Working Directory:** Yes
- **Ready for:** Implementation phase

---

**END OF PLAN**
