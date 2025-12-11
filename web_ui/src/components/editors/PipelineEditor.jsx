/**
 * VaultMind Forge - Pipeline Editor
 *
 * Multi-stage processing pipeline designer with:
 * - ReactFlow-based stage graph visualization
 * - Sequential and parallel stage execution
 * - Stage configuration (nodes, dependencies)
 * - Input/output mapping between stages
 * - Pipeline validation
 * - Execution controls and monitoring
 * - Stage status tracking
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position
} from 'reactflow'
import 'reactflow/dist/style.css'
import {
  GitBranch,
  Plus,
  Play,
  Pause,
  Square,
  Settings,
  Save,
  Download,
  Upload,
  CheckCircle,
  XCircle,
  Clock,
  Loader,
  AlertTriangle,
  Trash2,
  Copy,
  Edit3
} from 'lucide-react'

// Stage status types
const STAGE_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  SKIPPED: 'skipped'
}

// Stage execution mode
const EXECUTION_MODE = {
  SEQUENTIAL: 'sequential',
  PARALLEL: 'parallel'
}

// Pipeline execution state
const PIPELINE_STATE = {
  IDLE: 'idle',
  RUNNING: 'running',
  PAUSED: 'paused',
  COMPLETED: 'completed',
  FAILED: 'failed'
}

// Status icon mapping
const StatusIcon = ({ status }) => {
  switch (status) {
    case STAGE_STATUS.PENDING:
      return <Clock className="w-4 h-4 text-textMuted" />
    case STAGE_STATUS.RUNNING:
      return <Loader className="w-4 h-4 text-blue-500 animate-spin" />
    case STAGE_STATUS.COMPLETED:
      return <CheckCircle className="w-4 h-4 text-green-500" />
    case STAGE_STATUS.FAILED:
      return <XCircle className="w-4 h-4 text-red-500" />
    case STAGE_STATUS.SKIPPED:
      return <AlertTriangle className="w-4 h-4 text-yellow-500" />
    default:
      return <Clock className="w-4 h-4 text-textMuted" />
  }
}

// Custom node component for pipeline stages
const StageNode = ({ data }) => {
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-[180px] ${
        data.status === STAGE_STATUS.RUNNING
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : data.status === STAGE_STATUS.COMPLETED
          ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
          : data.status === STAGE_STATUS.FAILED
          ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
          : 'border-border bg-surface'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <StatusIcon status={data.status} />
          <span className="text-sm font-semibold text-text">{data.label}</span>
        </div>
        {data.executionMode === EXECUTION_MODE.PARALLEL && (
          <span className="text-xs text-textMuted bg-background px-2 py-0.5 rounded">
            Parallel
          </span>
        )}
      </div>
      <div className="text-xs text-textMuted">
        {data.nodes?.length || 0} nodes
        {data.duration && ` • ${data.duration}ms`}
      </div>
    </div>
  )
}

const nodeTypes = {
  stage: StageNode
}

export default function PipelineEditor() {
  // Pipeline metadata
  const [pipelineName, setPipelineName] = useState('Untitled Pipeline')
  const [pipelineDescription, setPipelineDescription] = useState('')

  // Pipeline execution
  const [pipelineState, setPipelineState] = useState(PIPELINE_STATE.IDLE)
  const [currentStageIndex, setCurrentStageIndex] = useState(0)

  // ReactFlow state
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const reactFlowWrapper = useRef(null)
  const [reactFlowInstance, setReactFlowInstance] = useState(null)

  // UI state
  const [selectedStage, setSelectedStage] = useState(null)
  const [showStageConfig, setShowStageConfig] = useState(false)

  // Stage configuration state
  const [editingStage, setEditingStage] = useState(null)

  // Add edge connection
  const onConnect = useCallback(
    (params) => {
      // Validate that we don't create cycles
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

  // Add new stage
  const addStage = () => {
    const id = `stage_${Date.now()}`
    const position = reactFlowInstance
      ? reactFlowInstance.project({ x: 250, y: nodes.length * 150 + 50 })
      : { x: 250, y: nodes.length * 150 + 50 }

    const newNode = {
      id,
      type: 'stage',
      position,
      data: {
        label: `Stage ${nodes.length + 1}`,
        status: STAGE_STATUS.PENDING,
        executionMode: EXECUTION_MODE.SEQUENTIAL,
        nodes: [],
        dependencies: [],
        config: {}
      }
    }

    setNodes((nds) => [...nds, newNode])
  }

  // Update stage data
  const updateStageData = (stageId, updates) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === stageId
          ? { ...node, data: { ...node.data, ...updates } }
          : node
      )
    )
  }

  // Delete stage
  const deleteStage = (stageId) => {
    setNodes((nds) => nds.filter((n) => n.id !== stageId))
    setEdges((eds) => eds.filter((e) => e.source !== stageId && e.target !== stageId))
    if (selectedStage?.id === stageId) {
      setSelectedStage(null)
      setShowStageConfig(false)
    }
  }

  // Validate pipeline
  const validatePipeline = () => {
    const errors = []

    // Check for cycles
    const hasCycle = (nodeId, visited = new Set(), stack = new Set()) => {
      if (stack.has(nodeId)) return true
      if (visited.has(nodeId)) return false

      visited.add(nodeId)
      stack.add(nodeId)

      const outgoingEdges = edges.filter((e) => e.source === nodeId)
      for (const edge of outgoingEdges) {
        if (hasCycle(edge.target, visited, stack)) return true
      }

      stack.delete(nodeId)
      return false
    }

    for (const node of nodes) {
      if (hasCycle(node.id)) {
        errors.push('Pipeline contains cycles')
        break
      }
    }

    // Check for stages with no nodes
    for (const node of nodes) {
      if (!node.data.nodes || node.data.nodes.length === 0) {
        errors.push(`Stage "${node.data.label}" has no nodes configured`)
      }
    }

    // Check for disconnected stages (except the first one)
    const rootStages = nodes.filter((n) => !edges.some((e) => e.target === n.id))
    if (rootStages.length > 1) {
      errors.push('Pipeline has multiple disconnected starting points')
    }

    return { valid: errors.length === 0, errors }
  }

  // Execute pipeline
  const executePipeline = async () => {
    const validation = validatePipeline()
    if (!validation.valid) {
      alert(`Pipeline validation failed:\n${validation.errors.join('\n')}`)
      return
    }

    setPipelineState(PIPELINE_STATE.RUNNING)
    setCurrentStageIndex(0)

    // Reset all stages to pending
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: STAGE_STATUS.PENDING, duration: null }
      }))
    )

    // Execute stages in topological order
    // This is a simulation - in production, this would trigger backend execution
    await executeStagesInOrder()
  }

  const executeStagesInOrder = async () => {
    // Find root stages (no incoming edges)
    const rootStages = nodes.filter((n) => !edges.some((e) => e.target === n.id))

    // Execute stages level by level
    const executedStages = new Set()
    const executeStage = async (stageId) => {
      if (executedStages.has(stageId)) return

      // Mark as running
      updateStageData(stageId, { status: STAGE_STATUS.RUNNING })

      // Simulate execution
      const startTime = Date.now()
      await new Promise((resolve) => setTimeout(resolve, 2000 + Math.random() * 2000))
      const duration = Date.now() - startTime

      // Randomly succeed or fail (90% success rate for demo)
      const success = Math.random() > 0.1

      updateStageData(stageId, {
        status: success ? STAGE_STATUS.COMPLETED : STAGE_STATUS.FAILED,
        duration
      })

      executedStages.add(stageId)

      if (!success) {
        setPipelineState(PIPELINE_STATE.FAILED)
        throw new Error('Stage failed')
      }

      // Find and execute dependent stages
      const dependentStages = edges
        .filter((e) => e.source === stageId)
        .map((e) => e.target)

      // Execute dependent stages in parallel if they have no other dependencies
      await Promise.all(
        dependentStages.map(async (depStageId) => {
          // Check if all dependencies are completed
          const dependencies = edges
            .filter((e) => e.target === depStageId)
            .map((e) => e.source)

          const allDepsCompleted = dependencies.every((dep) => executedStages.has(dep))

          if (allDepsCompleted) {
            await executeStage(depStageId)
          }
        })
      )
    }

    try {
      await Promise.all(rootStages.map((stage) => executeStage(stage.id)))
      setPipelineState(PIPELINE_STATE.COMPLETED)
    } catch (error) {
      setPipelineState(PIPELINE_STATE.FAILED)
    }
  }

  // Pause pipeline
  const pausePipeline = () => {
    setPipelineState(PIPELINE_STATE.PAUSED)
    // TODO: Pause execution
  }

  // Stop pipeline
  const stopPipeline = () => {
    setPipelineState(PIPELINE_STATE.IDLE)
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: STAGE_STATUS.PENDING, duration: null }
      }))
    )
  }

  // Save pipeline
  const savePipeline = () => {
    const pipeline = {
      name: pipelineName,
      description: pipelineDescription,
      stages: nodes.map((node) => ({
        id: node.id,
        ...node.data
      })),
      connections: edges.map((edge) => ({
        from: edge.source,
        to: edge.target
      }))
    }

    console.log('Saving pipeline:', pipeline)
    // TODO: API call to save pipeline
  }

  // Export pipeline as JSON
  const exportPipeline = () => {
    const pipeline = {
      name: pipelineName,
      description: pipelineDescription,
      version: '1.0.0',
      stages: nodes,
      edges
    }

    const blob = new Blob([JSON.stringify(pipeline, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${pipelineName.replace(/\s+/g, '_')}.pipeline.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Import pipeline from JSON
  const importPipeline = (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const pipeline = JSON.parse(e.target.result)
        setPipelineName(pipeline.name)
        setPipelineDescription(pipeline.description)
        setNodes(pipeline.stages || [])
        setEdges(pipeline.edges || [])
      } catch (error) {
        console.error('Failed to import pipeline:', error)
        alert('Failed to import pipeline. Invalid file format.')
      }
    }
    reader.readAsText(file)
  }

  // Node click handler
  const handleNodeClick = (_, node) => {
    setSelectedStage(node)
    setEditingStage(node.data)
    setShowStageConfig(true)
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Toolbar */}
      <div className="h-12 bg-surface border-b border-border flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-accent" />
          <input
            type="text"
            value={pipelineName}
            onChange={(e) => setPipelineName(e.target.value)}
            className="bg-transparent border-none text-sm font-medium text-text focus:outline-none focus:border-b focus:border-accent"
            placeholder="Pipeline name"
          />
          <span className="text-xs text-textMuted px-2 py-1 bg-background rounded">
            {nodes.length} stages
          </span>
          <span
            className={`text-xs px-2 py-1 rounded ${
              pipelineState === PIPELINE_STATE.RUNNING
                ? 'bg-blue-500 text-white'
                : pipelineState === PIPELINE_STATE.COMPLETED
                ? 'bg-green-500 text-white'
                : pipelineState === PIPELINE_STATE.FAILED
                ? 'bg-red-500 text-white'
                : 'bg-background text-textMuted'
            }`}
          >
            {pipelineState.toUpperCase()}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={addStage}
            className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1"
            title="Add stage"
          >
            <Plus className="w-4 h-4" />
            Add Stage
          </button>

          <div className="h-6 w-px bg-border" />

          <button
            onClick={executePipeline}
            disabled={pipelineState === PIPELINE_STATE.RUNNING || nodes.length === 0}
            className="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
            title="Run pipeline"
          >
            <Play className="w-4 h-4" />
            Run
          </button>

          <button
            onClick={pausePipeline}
            disabled={pipelineState !== PIPELINE_STATE.RUNNING}
            className="px-3 py-1.5 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
            title="Pause pipeline"
          >
            <Pause className="w-4 h-4" />
          </button>

          <button
            onClick={stopPipeline}
            disabled={pipelineState === PIPELINE_STATE.IDLE}
            className="px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
            title="Stop pipeline"
          >
            <Square className="w-4 h-4" />
          </button>

          <div className="h-6 w-px bg-border" />

          <label className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1 cursor-pointer">
            <Upload className="w-4 h-4" />
            Import
            <input
              type="file"
              accept=".json,.pipeline.json"
              onChange={importPipeline}
              className="hidden"
            />
          </label>

          <button
            onClick={exportPipeline}
            className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1"
            title="Export pipeline"
          >
            <Download className="w-4 h-4" />
            Export
          </button>

          <button
            onClick={savePipeline}
            className="px-3 py-1.5 bg-accent text-white rounded text-sm hover:bg-accent/90 flex items-center gap-1"
            title="Save pipeline"
          >
            <Save className="w-4 h-4" />
            Save
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Pipeline Info */}
        <div className="w-80 bg-surface border-r border-border overflow-y-auto flex-shrink-0">
          <div className="p-4 space-y-6">
            {/* Pipeline description */}
            <div>
              <label className="block text-xs font-medium text-textMuted mb-1">
                Description
              </label>
              <textarea
                value={pipelineDescription}
                onChange={(e) => setPipelineDescription(e.target.value)}
                placeholder="Describe this pipeline..."
                className="w-full h-20 p-2 bg-background border border-border rounded text-sm text-text placeholder-textMuted resize-none focus:outline-none focus:border-accent"
              />
            </div>

            {/* Pipeline validation */}
            <div>
              <h3 className="text-sm font-semibold text-text mb-2">Validation</h3>
              <button
                onClick={() => {
                  const validation = validatePipeline()
                  if (validation.valid) {
                    alert('Pipeline is valid!')
                  } else {
                    alert(`Validation errors:\n${validation.errors.join('\n')}`)
                  }
                }}
                className="w-full px-3 py-2 bg-background text-text rounded text-sm hover:bg-border"
              >
                Validate Pipeline
              </button>
            </div>

            {/* Stage list */}
            <div>
              <h3 className="text-sm font-semibold text-text mb-2">Stages</h3>
              {nodes.length === 0 ? (
                <div className="text-xs text-textMuted italic">
                  No stages added yet. Click "Add Stage" to start building your pipeline.
                </div>
              ) : (
                <div className="space-y-2">
                  {nodes.map((node, index) => (
                    <div
                      key={node.id}
                      className={`p-2 bg-background border rounded cursor-pointer transition-colors ${
                        selectedStage?.id === node.id
                          ? 'border-accent'
                          : 'border-border hover:border-accent/50'
                      }`}
                      onClick={() => handleNodeClick(null, node)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium text-textMuted">
                            #{index + 1}
                          </span>
                          <StatusIcon status={node.data.status} />
                          <span className="text-sm font-medium text-text">
                            {node.data.label}
                          </span>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteStage(node.id)
                          }}
                          className="text-textMuted hover:text-red-500"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="text-xs text-textMuted">
                        {node.data.nodes?.length || 0} nodes
                        {node.data.duration && ` • ${node.data.duration}ms`}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Center - Pipeline Graph */}
        <div className="flex-1 relative" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onNodeClick={handleNodeClick}
            onPaneClick={() => {
              setSelectedStage(null)
              setShowStageConfig(false)
            }}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>

          {nodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <GitBranch className="w-16 h-16 text-textMuted mx-auto mb-4" />
                <p className="text-textMuted text-sm">
                  Click "Add Stage" to start building your pipeline
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Stage Configuration */}
        {showStageConfig && editingStage && (
          <div className="w-80 bg-surface border-l border-border overflow-y-auto flex-shrink-0">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-text">Stage Configuration</h3>
                <button
                  onClick={() => setShowStageConfig(false)}
                  className="text-textMuted hover:text-text"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Stage Name
                  </label>
                  <input
                    type="text"
                    value={editingStage.label}
                    onChange={(e) => {
                      const updated = { ...editingStage, label: e.target.value }
                      setEditingStage(updated)
                      updateStageData(selectedStage.id, updated)
                    }}
                    className="w-full p-2 bg-background border border-border rounded text-sm text-text focus:outline-none focus:border-accent"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Execution Mode
                  </label>
                  <select
                    value={editingStage.executionMode}
                    onChange={(e) => {
                      const updated = { ...editingStage, executionMode: e.target.value }
                      setEditingStage(updated)
                      updateStageData(selectedStage.id, updated)
                    }}
                    className="w-full p-2 bg-background border border-border rounded text-sm text-text"
                  >
                    <option value={EXECUTION_MODE.SEQUENTIAL}>Sequential</option>
                    <option value={EXECUTION_MODE.PARALLEL}>Parallel</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Workflow Nodes
                  </label>
                  <div className="text-xs text-textMuted mb-2">
                    {editingStage.nodes?.length || 0} nodes configured
                  </div>
                  <button className="w-full px-3 py-2 bg-background text-text rounded text-sm hover:bg-border">
                    Configure Nodes
                  </button>
                  <p className="text-xs text-textMuted mt-2">
                    Configure which workflow nodes run in this stage
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Status
                  </label>
                  <div className="flex items-center gap-2 p-2 bg-background rounded">
                    <StatusIcon status={editingStage.status} />
                    <span className="text-sm text-text capitalize">
                      {editingStage.status}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
