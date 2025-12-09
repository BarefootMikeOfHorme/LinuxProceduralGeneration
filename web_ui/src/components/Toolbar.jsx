import { Play, Save, FolderOpen, Layers, Settings, HelpCircle, Loader2 } from 'lucide-react'
import { useWorkflowStore } from '../store/workflowStore'
import { notifySuccess, notifyInfo } from '../utils/notifications'

export default function Toolbar({ showPalette, setShowPalette, showProperties, setShowProperties }) {
  const { saveWorkflow, executeWorkflow, isExecuting, executionProgress } = useWorkflowStore()

  const handleSave = async () => {
    const name = prompt('Workflow name:', 'Untitled Workflow')
    if (name) {
      await saveWorkflow(name, 'Created with VaultMind Forge')
      notifySuccess(`Workflow "${name}" saved successfully!`)
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
            'px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 relative overflow-hidden ' +
            (isExecuting
              ? 'bg-blue-600 text-white cursor-not-allowed'
              : 'bg-accent hover:bg-accent/80 text-white')
          }
        >
          {/* Progress background */}
          {isExecuting && (
            <div
              className="absolute inset-0 bg-blue-700 transition-all duration-300"
              style={{ width: `${executionProgress}%` }}
            />
          )}

          {/* Content */}
          <div className="relative flex items-center gap-2">
            {isExecuting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {isExecuting ? `Executing ${Math.round(executionProgress)}%` : 'Execute (F5)'}
          </div>
        </button>

        <div className="w-px h-8 bg-border mx-2" />

        <button
          onClick={() => notifyInfo('VaultMind Forge v1.0 - Node-based AI content generation. Press F1 for keyboard shortcuts.', { duration: 5000 })}
          className="p-2 bg-background hover:bg-border rounded-lg transition-colors"
        >
          <HelpCircle className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
