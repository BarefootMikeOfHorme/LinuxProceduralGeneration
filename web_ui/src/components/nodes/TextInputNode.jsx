import { memo } from 'react'
import { Handle, Position } from 'reactflow'

export default memo(({ data, selected }) => {
  return (
    <div
      className={
        'px-4 py-3 shadow-lg rounded-lg bg-surface border-2 min-w-[200px] ' +
        (selected ? 'border-accent' : 'border-border')
      }
    >
      <div className="flex items-center gap-2 mb-2">
        <div className="w-8 h-8 rounded-lg bg-gray-500/20 flex items-center justify-center text-lg">
          📝
        </div>
        <div className="flex-1">
          <div className="font-semibold text-sm">Text Input</div>
          <div className="text-xs text-textMuted">Input</div>
        </div>
      </div>

      <div className="flex items-center justify-end gap-2">
        <div className="text-xs text-textMuted">text</div>
        <Handle
          type="source"
          position={Position.Right}
          id="text"
          style={{ background: '#55FF55' }}
          className="w-3 h-3 border-2 border-surface"
        />
      </div>
    </div>
  )
})
