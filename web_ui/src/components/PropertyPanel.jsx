import { useState } from 'react'
import { Bot, Trash2 } from 'lucide-react'
import { useWorkflowStore } from '../store/workflowStore'

export default function PropertyPanel({ node }) {
  const { updateNode, deleteNode } = useWorkflowStore()
  const [aiMode, setAiMode] = useState(node?.data?.aiMode || false)
  const [properties, setProperties] = useState(node?.data || {})

  const handleAIModeToggle = () => {
    const newAiMode = !aiMode
    setAiMode(newAiMode)
    updateNode(node.id, { ...node.data, aiMode: newAiMode })
  }

  const handlePropertyChange = (key, value) => {
    const newProperties = { ...properties, [key]: value }
    setProperties(newProperties)
    updateNode(node.id, newProperties)
  }

  const handleDelete = () => {
    deleteNode(node.id)
  }

  if (!node) return null

  return (
    <div className="w-80 bg-surface border-l border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold mb-2">Node Properties</h2>
        <p className="text-sm text-textMuted">{node.type}</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="flex items-center justify-between p-3 bg-background rounded-lg">
          <div className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-accent" />
            <span className="text-sm font-medium">AI Control</span>
          </div>
          <button
            onClick={handleAIModeToggle}
            className={
              'px-3 py-1 rounded text-xs font-medium transition-colors ' +
              (aiMode
                ? 'bg-accent text-white'
                : 'bg-border text-textMuted')
            }
          >
            {aiMode ? 'ON' : 'OFF'}
          </button>
        </div>

        {node.type === 'sdxlGenerator' && (
          <>
            <div>
              <label className="block text-sm font-medium mb-2">Prompt</label>
              <textarea
                value={properties.prompt || ''}
                onChange={(e) => handlePropertyChange('prompt', e.target.value)}
                placeholder="Enter your prompt..."
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm resize-none focus:outline-none focus:border-accent"
                rows={4}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Steps</label>
              <input
                type="number"
                value={properties.steps || 30}
                onChange={(e) => handlePropertyChange('steps', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:border-accent"
                min={1}
                max={150}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">CFG Scale</label>
              <input
                type="number"
                value={properties.cfg_scale || 7.5}
                onChange={(e) => handlePropertyChange('cfg_scale', parseFloat(e.target.value))}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:border-accent"
                step={0.5}
                min={1}
                max={20}
              />
            </div>
          </>
        )}

        {node.type === 'textInput' && (
          <div>
            <label className="block text-sm font-medium mb-2">Text</label>
            <textarea
              value={properties.text || ''}
              onChange={(e) => handlePropertyChange('text', e.target.value)}
              placeholder="Enter text..."
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm resize-none focus:outline-none focus:border-accent"
              rows={6}
            />
          </div>
        )}
      </div>

      <div className="p-4 border-t border-border space-y-2">
        <button
          onClick={handleDelete}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-error hover:bg-error/80 text-white rounded-lg transition-colors"
        >
          <Trash2 className="w-4 h-4" />
          Delete Node
        </button>
      </div>
    </div>
  )
}
