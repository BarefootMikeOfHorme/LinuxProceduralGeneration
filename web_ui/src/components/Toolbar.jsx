import { Play, Save, FolderOpen, Layers, Settings, HelpCircle } from 'lucide-react'
import { useWorkflowStore } from '../store/workflowStore'

export default function Toolbar({ showPalette, setShowPalette, showProperties, setShowProperties }) {
  const { saveWorkflow, executeWorkflow, isExecuting } = useWorkflowStore()

  const handleSave = async () => {
    const name = prompt('Workflow name:', 'Untitled Workflow')
    if (name) {
      await saveWorkflow(name, 'Created with VaultMind Forge')
      alert('Workflow saved!')
    }
  }

  const handleExecute = () => {
    executeWorkflow()
  }

  return (
    <div className="h-14 bg-surface border-b border-border flex items-center justify-between px-4">
      <div className="flex items-center gap-2">
        <h1 className="text-xl font-bold text-accent">VaultMind Forge</h1>
        <span className="text-xs text-textMuted">Visual Node Editor</span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowPalette(!showPalette)}
          className="px-3 py-2 bg-background hover:bg-border text-sm rounded-lg transition-colors flex items-center gap-2"
        >
          <Layers className="w-4 h-4" />
          Nodes
        </button>

        <button
          onClick={() => setShowProperties(!showProperties)}
          className="px-3 py-2 bg-background hover:bg-border text-sm rounded-lg transition-colors flex items-center gap-2"
        >
          <Settings className="w-4 h-4" />
          Properties
        </button>

        <div className="w-px h-8 bg-border mx-2" />

        <button
          onClick={handleSave}
          className="px-3 py-2 bg-background hover:bg-border text-sm rounded-lg transition-colors flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          Save
        </button>

        <button
          onClick={handleExecute}
          disabled={isExecuting}
          className={
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ' +
            (isExecuting
              ? 'bg-border text-textMuted cursor-not-allowed'
              : 'bg-accent hover:bg-accent/80 text-white')
          }
        >
          <Play className="w-4 h-4" />
          {isExecuting ? 'Executing...' : 'Execute (F5)'}
        </button>

        <div className="w-px h-8 bg-border mx-2" />

        <button
          onClick={() => alert('VaultMind Forge v1.0\n\nNode-based AI content generation\n\nPress F1 for keyboard shortcuts')}
          className="p-2 bg-background hover:bg-border rounded-lg transition-colors"
        >
          <HelpCircle className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
