/**
 * VaultMind Forge - Template Editor
 *
 * Create reusable workflow templates with:
 * - ReactFlow-based workflow designer
 * - Parameter definition UI (template variables)
 * - Template metadata (name, description, tags, category)
 * - Parameter validation rules
 * - Template preview and instantiation
 * - Export/import templates
 */

import { useState, useCallback, useRef } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  MarkerType
} from 'reactflow'
import 'reactflow/dist/style.css'
import {
  FileText,
  Plus,
  Save,
  Download,
  Upload,
  Play,
  Settings,
  Tag,
  X,
  Copy,
  Edit3,
  Trash2,
  Sliders
} from 'lucide-react'

// Parameter types for template variables
const PARAMETER_TYPES = {
  STRING: 'string',
  NUMBER: 'number',
  BOOLEAN: 'boolean',
  SELECT: 'select',
  FILE: 'file',
  COLOR: 'color'
}

// Template categories
const TEMPLATE_CATEGORIES = [
  'Image Generation',
  'Image Processing',
  'Text Processing',
  'Batch Operations',
  'AI/ML',
  'Utilities',
  'Custom'
]

// Default node types that can be used in templates
const NODE_TYPES_LIBRARY = [
  { type: 'input_text', label: 'Text Input', category: 'Input' },
  { type: 'input_number', label: 'Number Input', category: 'Input' },
  { type: 'input_image', label: 'Image Input', category: 'Input' },
  { type: 'sdxl_generate', label: 'SDXL Generate', category: 'Generation' },
  { type: 'super_resolution', label: 'Super Resolution', category: 'Processing' },
  { type: 'image_filter', label: 'Image Filter', category: 'Processing' },
  { type: 'prompt_refiner', label: 'Prompt Refiner', category: 'AI' },
  { type: 'output_image', label: 'Image Output', category: 'Output' },
  { type: 'output_text', label: 'Text Output', category: 'Output' }
]

export default function TemplateEditor() {
  // Template metadata
  const [templateName, setTemplateName] = useState('Untitled Template')
  const [templateDescription, setTemplateDescription] = useState('')
  const [templateCategory, setTemplateCategory] = useState(TEMPLATE_CATEGORIES[0])
  const [templateTags, setTemplateTags] = useState([])
  const [newTag, setNewTag] = useState('')

  // Template parameters (variables that users can fill when instantiating)
  const [parameters, setParameters] = useState([])
  const [editingParameter, setEditingParameter] = useState(null)
  const [showParameterEditor, setShowParameterEditor] = useState(false)

  // ReactFlow state
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const reactFlowWrapper = useRef(null)
  const [reactFlowInstance, setReactFlowInstance] = useState(null)

  // UI state
  const [showNodeLibrary, setShowNodeLibrary] = useState(false)
  const [selectedNode, setSelectedNode] = useState(null)

  // Add edge connection
  const onConnect = useCallback(
    (params) => {
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            type: 'smoothstep',
            animated: true,
            markerEnd: { type: MarkerType.ArrowClosed }
          },
          eds
        )
      )
    },
    [setEdges]
  )

  // Add node from library
  const addNodeToCanvas = (nodeType) => {
    const id = `node_${Date.now()}`
    const position = reactFlowInstance
      ? reactFlowInstance.project({ x: 250, y: 250 })
      : { x: 250, y: 250 }

    const newNode = {
      id,
      type: 'default',
      position,
      data: {
        label: nodeType.label,
        nodeType: nodeType.type
      }
    }

    setNodes((nds) => [...nds, newNode])
    setShowNodeLibrary(false)
  }

  // Parameter CRUD operations
  const addParameter = () => {
    const newParam = {
      id: `param_${Date.now()}`,
      name: 'new_parameter',
      label: 'New Parameter',
      type: PARAMETER_TYPES.STRING,
      defaultValue: '',
      required: false,
      description: '',
      validation: null
    }
    setParameters([...parameters, newParam])
    setEditingParameter(newParam)
    setShowParameterEditor(true)
  }

  const updateParameter = (paramId, updates) => {
    setParameters(parameters.map(p => p.id === paramId ? { ...p, ...updates } : p))
  }

  const deleteParameter = (paramId) => {
    setParameters(parameters.filter(p => p.id !== paramId))
    if (editingParameter?.id === paramId) {
      setEditingParameter(null)
      setShowParameterEditor(false)
    }
  }

  // Tag management
  const addTag = () => {
    if (newTag.trim() && !templateTags.includes(newTag.trim())) {
      setTemplateTags([...templateTags, newTag.trim()])
      setNewTag('')
    }
  }

  const removeTag = (tag) => {
    setTemplateTags(templateTags.filter(t => t !== tag))
  }

  // Save template
  const saveTemplate = () => {
    const template = {
      metadata: {
        name: templateName,
        description: templateDescription,
        category: templateCategory,
        tags: templateTags,
        version: '1.0.0',
        createdAt: Date.now(),
        modifiedAt: Date.now()
      },
      parameters,
      workflow: {
        nodes,
        edges
      }
    }

    console.log('Saving template:', template)
    // TODO: API call to save template
  }

  // Export template as JSON
  const exportTemplate = () => {
    const template = {
      metadata: {
        name: templateName,
        description: templateDescription,
        category: templateCategory,
        tags: templateTags,
        version: '1.0.0'
      },
      parameters,
      workflow: { nodes, edges }
    }

    const blob = new Blob([JSON.stringify(template, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${templateName.replace(/\s+/g, '_')}.template.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Import template from JSON
  const importTemplate = (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const template = JSON.parse(e.target.result)
        setTemplateName(template.metadata.name)
        setTemplateDescription(template.metadata.description)
        setTemplateCategory(template.metadata.category)
        setTemplateTags(template.metadata.tags || [])
        setParameters(template.parameters || [])
        setNodes(template.workflow.nodes || [])
        setEdges(template.workflow.edges || [])
      } catch (error) {
        console.error('Failed to import template:', error)
        alert('Failed to import template. Invalid file format.')
      }
    }
    reader.readAsText(file)
  }

  // Instantiate template (create new workflow from template)
  const instantiateTemplate = () => {
    console.log('Instantiating template with parameters:', parameters)
    // TODO: Show parameter input dialog and create new workflow
    alert('Template instantiation not yet implemented. This will create a new workflow from this template.')
  }

  // Delete selected node
  const deleteSelectedNode = () => {
    if (selectedNode) {
      setNodes((nds) => nds.filter(n => n.id !== selectedNode.id))
      setEdges((eds) => eds.filter(e => e.source !== selectedNode.id && e.target !== selectedNode.id))
      setSelectedNode(null)
    }
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Toolbar */}
      <div className="h-12 bg-surface border-b border-border flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-accent" />
          <input
            type="text"
            value={templateName}
            onChange={(e) => setTemplateName(e.target.value)}
            className="bg-transparent border-none text-sm font-medium text-text focus:outline-none focus:border-b focus:border-accent"
            placeholder="Template name"
          />
          <span className="text-xs text-textMuted px-2 py-1 bg-background rounded">
            {parameters.length} parameters
          </span>
          <span className="text-xs text-textMuted px-2 py-1 bg-background rounded">
            {nodes.length} nodes
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowNodeLibrary(!showNodeLibrary)}
            className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1"
            title="Add node"
          >
            <Plus className="w-4 h-4" />
            Add Node
          </button>

          <label className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1 cursor-pointer">
            <Upload className="w-4 h-4" />
            Import
            <input
              type="file"
              accept=".json,.template.json"
              onChange={importTemplate}
              className="hidden"
            />
          </label>

          <button
            onClick={exportTemplate}
            className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1"
            title="Export template"
          >
            <Download className="w-4 h-4" />
            Export
          </button>

          <button
            onClick={saveTemplate}
            className="px-3 py-1.5 bg-accent text-white rounded text-sm hover:bg-accent/90 flex items-center gap-1"
            title="Save template"
          >
            <Save className="w-4 h-4" />
            Save
          </button>

          <button
            onClick={instantiateTemplate}
            className="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700 flex items-center gap-1"
            title="Create workflow from template"
          >
            <Play className="w-4 h-4" />
            Use Template
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Template Settings & Parameters */}
        <div className="w-80 bg-surface border-r border-border overflow-y-auto flex-shrink-0">
          <div className="p-4 space-y-6">
            {/* Template Metadata */}
            <div>
              <h3 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Template Settings
              </h3>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Description
                  </label>
                  <textarea
                    value={templateDescription}
                    onChange={(e) => setTemplateDescription(e.target.value)}
                    placeholder="Describe what this template does..."
                    className="w-full h-20 p-2 bg-background border border-border rounded text-sm text-text placeholder-textMuted resize-none focus:outline-none focus:border-accent"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Category
                  </label>
                  <select
                    value={templateCategory}
                    onChange={(e) => setTemplateCategory(e.target.value)}
                    className="w-full p-2 bg-background border border-border rounded text-sm text-text"
                  >
                    {TEMPLATE_CATEGORIES.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1 flex items-center gap-1">
                    <Tag className="w-3 h-3" />
                    Tags
                  </label>
                  <div className="flex gap-1 mb-2">
                    <input
                      type="text"
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && addTag()}
                      placeholder="Add tag..."
                      className="flex-1 p-2 bg-background border border-border rounded text-sm text-text placeholder-textMuted focus:outline-none focus:border-accent"
                    />
                    <button
                      onClick={addTag}
                      className="px-2 bg-accent text-white rounded hover:bg-accent/90"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                  {templateTags.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {templateTags.map(tag => (
                        <div
                          key={tag}
                          className="px-2 py-1 bg-background border border-border rounded flex items-center gap-1 text-xs"
                        >
                          <span className="text-text">{tag}</span>
                          <button
                            onClick={() => removeTag(tag)}
                            className="text-textMuted hover:text-red-500"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-textMuted italic">No tags</div>
                  )}
                </div>
              </div>
            </div>

            {/* Template Parameters */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-text flex items-center gap-2">
                  <Sliders className="w-4 h-4" />
                  Parameters
                </h3>
                <button
                  onClick={addParameter}
                  className="px-2 py-1 bg-accent text-white rounded text-xs hover:bg-accent/90 flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" />
                  Add
                </button>
              </div>

              {parameters.length === 0 ? (
                <div className="text-xs text-textMuted italic">
                  No parameters defined. Add parameters to make this template reusable.
                </div>
              ) : (
                <div className="space-y-2">
                  {parameters.map(param => (
                    <div
                      key={param.id}
                      className={`p-2 bg-background border rounded cursor-pointer transition-colors ${
                        editingParameter?.id === param.id
                          ? 'border-accent'
                          : 'border-border hover:border-accent/50'
                      }`}
                      onClick={() => {
                        setEditingParameter(param)
                        setShowParameterEditor(true)
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="text-sm font-medium text-text">{param.label}</div>
                          <div className="text-xs text-textMuted font-mono">{param.name}</div>
                          <div className="text-xs text-textMuted mt-1">
                            Type: {param.type}
                            {param.required && <span className="text-red-500 ml-1">*</span>}
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteParameter(param.id)
                          }}
                          className="text-textMuted hover:text-red-500"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Center - Workflow Canvas */}
        <div className="flex-1 relative" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onNodeClick={(_, node) => setSelectedNode(node)}
            onPaneClick={() => setSelectedNode(null)}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>

          {/* Node Library Popup */}
          {showNodeLibrary && (
            <div className="absolute top-4 left-4 w-64 bg-surface border border-border rounded shadow-lg z-10">
              <div className="p-3 border-b border-border flex items-center justify-between">
                <h4 className="text-sm font-semibold text-text">Node Library</h4>
                <button
                  onClick={() => setShowNodeLibrary(false)}
                  className="text-textMuted hover:text-text"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="max-h-96 overflow-y-auto">
                {Object.entries(
                  NODE_TYPES_LIBRARY.reduce((acc, node) => {
                    if (!acc[node.category]) acc[node.category] = []
                    acc[node.category].push(node)
                    return acc
                  }, {})
                ).map(([category, categoryNodes]) => (
                  <div key={category} className="p-2">
                    <div className="text-xs font-medium text-textMuted mb-1 px-2">
                      {category}
                    </div>
                    {categoryNodes.map(node => (
                      <button
                        key={node.type}
                        onClick={() => addNodeToCanvas(node)}
                        className="w-full text-left px-3 py-2 text-sm text-text hover:bg-background rounded transition-colors"
                      >
                        {node.label}
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Selected Node Actions */}
          {selectedNode && (
            <div className="absolute bottom-4 right-4 bg-surface border border-border rounded shadow-lg p-2 flex gap-2">
              <button
                onClick={deleteSelectedNode}
                className="px-3 py-2 bg-red-500 text-white rounded text-sm hover:bg-red-600 flex items-center gap-1"
              >
                <Trash2 className="w-4 h-4" />
                Delete Node
              </button>
            </div>
          )}
        </div>

        {/* Right Panel - Parameter Editor */}
        {showParameterEditor && editingParameter && (
          <div className="w-80 bg-surface border-l border-border overflow-y-auto flex-shrink-0">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-text">Edit Parameter</h3>
                <button
                  onClick={() => setShowParameterEditor(false)}
                  className="text-textMuted hover:text-text"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Label
                  </label>
                  <input
                    type="text"
                    value={editingParameter.label}
                    onChange={(e) => updateParameter(editingParameter.id, { label: e.target.value })}
                    className="w-full p-2 bg-background border border-border rounded text-sm text-text focus:outline-none focus:border-accent"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Variable Name (code)
                  </label>
                  <input
                    type="text"
                    value={editingParameter.name}
                    onChange={(e) => updateParameter(editingParameter.id, { name: e.target.value })}
                    className="w-full p-2 bg-background border border-border rounded text-sm text-text font-mono focus:outline-none focus:border-accent"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Type
                  </label>
                  <select
                    value={editingParameter.type}
                    onChange={(e) => updateParameter(editingParameter.id, { type: e.target.value })}
                    className="w-full p-2 bg-background border border-border rounded text-sm text-text"
                  >
                    {Object.entries(PARAMETER_TYPES).map(([key, value]) => (
                      <option key={value} value={value}>
                        {key.charAt(0) + key.slice(1).toLowerCase()}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Default Value
                  </label>
                  <input
                    type="text"
                    value={editingParameter.defaultValue}
                    onChange={(e) => updateParameter(editingParameter.id, { defaultValue: e.target.value })}
                    className="w-full p-2 bg-background border border-border rounded text-sm text-text focus:outline-none focus:border-accent"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Description
                  </label>
                  <textarea
                    value={editingParameter.description}
                    onChange={(e) => updateParameter(editingParameter.id, { description: e.target.value })}
                    className="w-full h-20 p-2 bg-background border border-border rounded text-sm text-text resize-none focus:outline-none focus:border-accent"
                    placeholder="Describe this parameter..."
                  />
                </div>

                <div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={editingParameter.required}
                      onChange={(e) => updateParameter(editingParameter.id, { required: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-sm text-text">Required</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
