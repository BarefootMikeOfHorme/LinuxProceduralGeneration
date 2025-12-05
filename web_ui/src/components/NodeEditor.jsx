import { useCallback } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useWorkflowStore } from '../store/workflowStore'

import SDXLGeneratorNode from './nodes/SDXLGeneratorNode'
import PromptRefinerNode from './nodes/PromptRefinerNode'
import SuperResolutionNode from './nodes/SuperResolutionNode'
import TextInputNode from './nodes/TextInputNode'
import BaseNode from './nodes/BaseNode'
import { nodeLibrary } from '../lib/nodeLibrary'

// Custom nodes with specialized UI
const nodeTypes = {
  sdxlGenerator: SDXLGeneratorNode,
  promptRefiner: PromptRefinerNode,
  superResolution: SuperResolutionNode,
  textInput: TextInputNode,
}

// Auto-register remaining nodes with BaseNode
nodeLibrary.forEach(node => {
  if (!nodeTypes[node.type]) {
    nodeTypes[node.type] = (props) => <BaseNode {...props} type={node.type} />
  }
})

const socketColors = {
  image: '#FF5555',
  text: '#55FF55',
  number: '#888888',
  video: '#FF8855',
  mesh_3d: '#5555FF',
  any: '#4A90E2',
}

export default function NodeEditor({ onNodeSelect }) {
  const { nodes: storeNodes, edges: storeEdges, addNode, updateNode, deleteNode, addEdge: addStoreEdge } = useWorkflowStore()
  
  const [nodes, setNodes, onNodesChange] = useNodesState(storeNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(storeEdges)

  const onConnect = useCallback((params) => {
    const newEdge = {
      ...params,
      type: 'smoothstep',
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed, color: '#4A90E2' },
      style: { stroke: '#4A90E2', strokeWidth: 2 },
    }
    setEdges((eds) => addEdge(newEdge, eds))
    addStoreEdge(newEdge)
  }, [setEdges, addStoreEdge])

  const onDrop = useCallback((event) => {
    event.preventDefault()
    const type = event.dataTransfer.getData('application/reactflow')
    if (!type) return

    const position = {
      x: event.clientX - 250,
      y: event.clientY - 100,
    }

    const newNode = {
      id: type + '-' + Date.now(),
      type,
      position,
      data: { label: type, aiMode: false },
    }

    setNodes((nds) => nds.concat(newNode))
    addNode(newNode)
  }, [setNodes, addNode])

  const onDragOver = useCallback((event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onNodeClick = useCallback((event, node) => {
    onNodeSelect(node)
  }, [onNodeSelect])

  return (
    <div className="flex-1 bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        snapToGrid
        snapGrid={[20, 20]}
        fitView
        attributionPosition="bottom-right"
      >
        <Background color="#2a2a2a" gap={20} variant="dots" />
        <Controls />
        <MiniMap 
          nodeColor={(node) => {
            return '#1a1a1a'
          }}
          maskColor="rgba(0, 0, 0, 0.6)"
        />
      </ReactFlow>
    </div>
  )
}
