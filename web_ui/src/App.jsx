import { useState } from 'react'
import { ReactFlowProvider } from 'reactflow'
import NodeEditor from './components/NodeEditor'
import NodePalette from './components/NodePalette'
import PropertyPanel from './components/PropertyPanel'
import Toolbar from './components/Toolbar'
import FileBrowser from './components/FileBrowser'
import OutputModal from './components/OutputModal'
import useKeyboardShortcuts from './hooks/useKeyboardShortcuts'
import { useWorkflowStore } from './store/workflowStore'

function App() {
  const [showPalette, setShowPalette] = useState(true)
  const [showProperties, setShowProperties] = useState(true)
  const [selectedNode, setSelectedNode] = useState(null)
  const { executeWorkflow, saveWorkflow } = useWorkflowStore()

  useKeyboardShortcuts({
    'shift+a': () => setShowPalette(true),
    'f5': () => executeWorkflow(),
    'ctrl+s': (e) => {
      e.preventDefault()
      saveWorkflow('Untitled Workflow', 'Auto-saved workflow')
    },
    'f1': () => alert('VaultMind Forge Help\n\nShift+A: Add node\nF5: Execute\nCtrl+S: Save\nDel: Delete\nM: Mute\nCtrl+A: Toggle AI'),
    'escape': () => setSelectedNode(null),
  })

  return (
    <ReactFlowProvider>
      <div className="flex flex-col h-screen bg-background">
        <Toolbar
          showPalette={showPalette}
          setShowPalette={setShowPalette}
          showProperties={showProperties}
          setShowProperties={setShowProperties}
        />
        <div className="flex flex-1 overflow-hidden">
          {showPalette && (
            <NodePalette />
          )}
          <NodeEditor onNodeSelect={setSelectedNode} />
          {showProperties && selectedNode && (
            <PropertyPanel node={selectedNode} />
          )}
        </div>
      </div>

      {/* Modals - controlled by Zustand store */}
      <FileBrowser />
      <OutputModal />
    </ReactFlowProvider>
  )
}

export default App
