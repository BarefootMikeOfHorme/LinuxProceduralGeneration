import { useState } from 'react'
import { Bot, Trash2 } from 'lucide-react'
import { useWorkflowStore } from '../store/workflowStore'
import { nodeLibrary } from '../lib/nodeLibrary'
import FileInputField from './FileInputField'

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

  // Find node configuration from library
  const nodeConfig = nodeLibrary.find(n => n.type === node.type)

  // Render appropriate input field based on input type and name
  const renderInputField = (input) => {
    const value = properties[input.name] ?? input.default ?? ''
    const isFilePath = input.name.toLowerCase().includes('path') || input.name.toLowerCase().includes('file')

    // File path inputs use FileInputField
    if (isFilePath && input.type === 'text') {
      return (
        <div key={input.name}>
          <label className="block text-sm font-medium mb-2">
            {input.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            {input.required && <span className="text-accent ml-1">*</span>}
          </label>
          <FileInputField
            value={value}
            onChange={(val) => handlePropertyChange(input.name, val)}
            placeholder={`Select ${input.name}...`}
          />
        </div>
      )
    }

    // Number inputs
    if (input.type === 'number') {
      return (
        <div key={input.name}>
          <label className="block text-sm font-medium mb-2">
            {input.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            {input.required && <span className="text-accent ml-1">*</span>}
          </label>
          <input
            type="number"
            value={value}
            onChange={(e) => handlePropertyChange(input.name, parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:border-accent"
          />
        </div>
      )
    }

    // Text inputs - use textarea for prompts, regular input for others
    if (input.type === 'text') {
      const isLongText = input.name.toLowerCase().includes('prompt') ||
                         input.name.toLowerCase().includes('text') ||
                         input.name.toLowerCase().includes('description')

      return (
        <div key={input.name}>
          <label className="block text-sm font-medium mb-2">
            {input.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            {input.required && <span className="text-accent ml-1">*</span>}
          </label>
          {isLongText ? (
            <textarea
              value={value}
              onChange={(e) => handlePropertyChange(input.name, e.target.value)}
              placeholder={`Enter ${input.name}...`}
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm resize-none focus:outline-none focus:border-accent"
              rows={4}
            />
          ) : (
            <input
              type="text"
              value={value}
              onChange={(e) => handlePropertyChange(input.name, e.target.value)}
              placeholder={`Enter ${input.name}...`}
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:border-accent"
            />
          )}
        </div>
      )
    }

    // Fallback for any other types
    return (
      <div key={input.name}>
        <label className="block text-sm font-medium mb-2">
          {input.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          {input.required && <span className="text-accent ml-1">*</span>}
        </label>
        <input
          type="text"
          value={value}
          onChange={(e) => handlePropertyChange(input.name, e.target.value)}
          className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:border-accent"
        />
      </div>
    )
  }

  return (
    <div className="w-80 bg-surface border-l border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold mb-2">Node Properties</h2>
        <p className="text-sm text-textMuted">{nodeConfig?.name || node.type}</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* AI Control Toggle - only show if node is AI controllable */}
        {nodeConfig?.aiControllable && (
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
        )}

        {/* Dynamic property fields based on node inputs */}
        {nodeConfig?.inputs && nodeConfig.inputs.length > 0 ? (
          nodeConfig.inputs.map(input => renderInputField(input))
        ) : (
          <div className="text-sm text-textMuted text-center py-4">
            No configurable properties
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
