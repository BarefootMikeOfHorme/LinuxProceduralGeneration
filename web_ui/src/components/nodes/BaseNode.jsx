import { memo, useState, useRef, useEffect } from 'react'
import { Handle, Position } from 'reactflow'
import { Sparkles, Image as ImageIcon, Video, Cube, Copy, Trash2, MoreVertical, RefreshCw, Zap } from 'lucide-react'
import { useWorkflowStore } from '../../store/workflowStore'
import { nodeLibrary, socketColors } from '../../lib/nodeLibrary'

export default memo(({ id, data, selected, type }) => {
  const { nodePreviews, deleteNode, updateNode } = useWorkflowStore()
  const [showContextMenu, setShowContextMenu] = useState(false)
  const [contextMenuPos, setContextMenuPos] = useState({ x: 0, y: 0 })
  const menuRef = useRef(null)

  // Find node configuration from library
  const nodeConfig = nodeLibrary.find(n => n.type === type)

  if (!nodeConfig) {
    return (
      <div className="px-4 py-3 bg-red-500/20 border-2 border-red-500 rounded-lg">
        <div className="text-red-500">Unknown node type: {type}</div>
      </div>
    )
  }

  const preview = nodePreviews[id]
  const hasVisualOutput = nodeConfig.outputs?.some(o =>
    ['image', 'video', 'mesh_3d'].includes(o.type)
  )
  const isMuted = data.muted || false

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowContextMenu(false)
      }
    }
    if (showContextMenu) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showContextMenu])

  // Context menu handlers
  const handleContextMenu = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setContextMenuPos({ x: e.clientX, y: e.clientY })
    setShowContextMenu(true)
  }

  const handleDuplicate = () => {
    // TODO: Implement duplicate
    console.log('Duplicate node:', id)
    setShowContextMenu(false)
  }

  const handleMuteToggle = () => {
    updateNode(id, { ...data, muted: !isMuted })
    setShowContextMenu(false)
  }

  const handleReset = () => {
    // Reset to defaults
    const defaults = {}
    nodeConfig.inputs?.forEach(input => {
      if (input.default !== undefined) {
        defaults[input.name] = input.default
      }
    })
    updateNode(id, { ...data, ...defaults })
    setShowContextMenu(false)
  }

  const handleCopyId = () => {
    navigator.clipboard.writeText(id)
    setShowContextMenu(false)
  }

  const handleDelete = () => {
    deleteNode(id)
    setShowContextMenu(false)
  }

  const handleToggleAI = () => {
    updateNode(id, { ...data, aiMode: !data.aiMode })
    setShowContextMenu(false)
  }

  // Render preview based on type
  const renderPreview = (previewData) => {
    if (!previewData) return null

    return (
      <div className="mt-2 pt-2 border-t border-border/30">
        <div className="flex flex-wrap gap-1">
          {Object.entries(previewData).map(([handle, data]) => {
            if (data.type === 'image' && data.thumbnail) {
              return (
                <div key={handle} className="relative group">
                  <img
                    src={data.thumbnail}
                    alt={handle}
                    className="w-full h-16 object-cover rounded border border-border"
                  />
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <ImageIcon className="w-4 h-4 text-white" />
                  </div>
                </div>
              )
            }

            if (data.type === 'video') {
              return (
                <div key={handle} className="w-full h-16 bg-purple-500/20 rounded border border-purple-500/30 flex items-center justify-center">
                  <Video className="w-6 h-6 text-purple-400" />
                </div>
              )
            }

            if (data.type === 'mesh') {
              return (
                <div key={handle} className="w-full h-16 bg-blue-500/20 rounded border border-blue-500/30 flex items-center justify-center">
                  <Cube className="w-6 h-6 text-blue-400" />
                </div>
              )
            }

            if (data.type === 'text' && data.text) {
              return (
                <div key={handle} className="w-full p-2 bg-background/50 rounded border border-border text-xs font-mono truncate">
                  {data.text}
                </div>
              )
            }

            if (data.type === 'number' && data.value !== undefined) {
              return (
                <div key={handle} className="w-full p-2 bg-background/50 rounded border border-border text-sm font-bold text-center">
                  {data.value}
                </div>
              )
            }

            return null
          })}
        </div>
      </div>
    )
  }

  return (
    <>
      <div
        onContextMenu={handleContextMenu}
        className={
          'px-4 py-3 rounded-xl bg-surface border-2 min-w-[260px] transition-all duration-200 ' +
          (selected ? 'border-accent shadow-xl shadow-accent/20' : 'border-border shadow-lg hover:shadow-xl') +
          (isMuted ? ' opacity-50 grayscale' : '')
        }
        style={{
          borderLeftColor: nodeConfig.color,
          borderLeftWidth: '5px',
          background: `linear-gradient(135deg, ${nodeConfig.color}08 0%, transparent 100%)`
        }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold shadow-sm"
            style={{
              backgroundColor: nodeConfig.color + '30',
              color: nodeConfig.color,
              border: `2px solid ${nodeConfig.color}50`
            }}
          >
            {nodeConfig.icon || '◉'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-bold text-sm flex items-center gap-2">
              {nodeConfig.name}
              {data.aiMode && <Sparkles className="w-3.5 h-3.5 text-accent flex-shrink-0 animate-pulse" />}
              {isMuted && <span className="text-xs px-1.5 py-0.5 bg-gray-500/20 rounded text-gray-400">MUTED</span>}
            </div>
            <div className="text-xs text-textMuted/70 truncate font-medium">
              {nodeConfig.category}
            </div>
          </div>
        </div>

        {/* Inputs */}
        {nodeConfig.inputs && nodeConfig.inputs.length > 0 && (
          <div className="space-y-2.5 mb-3">
            {nodeConfig.inputs.map((input, idx) => (
              <div key={input.name} className="flex items-center gap-2.5">
                <Handle
                  type="target"
                  position={Position.Left}
                  id={input.name}
                  style={{
                    background: input.color || socketColors[input.type] || '#888888',
                    top: 'auto',
                    transform: 'none'
                  }}
                  className="w-3.5 h-3.5 border-2 border-surface shadow-sm hover:scale-125 transition-transform"
                />
                <div className="text-xs font-medium text-textMuted">
                  {input.name}
                  {input.required && <span className="text-accent ml-1 font-bold">*</span>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Outputs */}
        {nodeConfig.outputs && nodeConfig.outputs.length > 0 && (
          <div className="space-y-2.5">
            {nodeConfig.outputs.map((output, idx) => (
              <div key={output.name} className="flex items-center justify-end gap-2.5">
                <div className="text-xs font-medium text-textMuted">{output.name}</div>
                <Handle
                  type="source"
                  position={Position.Right}
                  id={output.name}
                  style={{
                    background: output.color || socketColors[output.type] || '#888888',
                    top: 'auto',
                    transform: 'none'
                  }}
                  className="w-3.5 h-3.5 border-2 border-surface shadow-sm hover:scale-125 transition-transform"
                />
              </div>
            ))}
          </div>
        )}

        {/* Preview Window */}
        {hasVisualOutput && preview && renderPreview(preview)}
      </div>

      {/* Context Menu */}
      {showContextMenu && (
        <div
          ref={menuRef}
          className="fixed z-50 bg-surface border-2 border-border rounded-lg shadow-2xl py-2 min-w-[200px]"
          style={{ left: contextMenuPos.x, top: contextMenuPos.y }}
        >
          {nodeConfig.aiControllable && (
            <button
              onClick={handleToggleAI}
              className="w-full px-4 py-2 text-left text-sm hover:bg-accent/10 flex items-center gap-3 transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              <span>{data.aiMode ? 'Disable AI Control' : 'Enable AI Control'}</span>
            </button>
          )}

          <button
            onClick={handleMuteToggle}
            className="w-full px-4 py-2 text-left text-sm hover:bg-accent/10 flex items-center gap-3 transition-colors"
          >
            <Zap className="w-4 h-4" />
            <span>{isMuted ? 'Unmute Node' : 'Mute Node'}</span>
          </button>

          <button
            onClick={handleReset}
            className="w-full px-4 py-2 text-left text-sm hover:bg-accent/10 flex items-center gap-3 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Reset to Defaults</span>
          </button>

          <button
            onClick={handleCopyId}
            className="w-full px-4 py-2 text-left text-sm hover:bg-accent/10 flex items-center gap-3 transition-colors"
          >
            <Copy className="w-4 h-4" />
            <span>Copy Node ID</span>
          </button>

          <div className="h-px bg-border my-2" />

          <button
            onClick={handleDelete}
            className="w-full px-4 py-2 text-left text-sm hover:bg-red-500/10 text-red-500 flex items-center gap-3 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete Node</span>
          </button>
        </div>
      )}
    </>
  )
})
