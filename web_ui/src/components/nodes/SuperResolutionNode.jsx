import { memo } from 'react'
import { Handle, Position } from 'reactflow'

export default memo(({ data, selected }) => {
  return (
    <div
      className={
        'px-4 py-3 shadow-lg rounded-lg bg-surface border-2 min-w-[240px] ' +
        (selected ? 'border-accent' : 'border-border')
      }
    >
      <div className="flex items-center gap-2 mb-2">
        <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-lg">
          📐
        </div>
        <div className="flex-1">
          <div className="font-semibold text-sm">Super Resolution</div>
          <div className="text-xs text-textMuted">forge_sr</div>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Handle
            type="target"
            position={Position.Left}
            id="image"
            style={{ background: '#FF5555' }}
            className="w-3 h-3 border-2 border-surface"
          />
          <div className="text-xs text-textMuted">image</div>
        </div>

        <div className="flex items-center justify-end gap-2">
          <div className="text-xs text-textMuted">upscaled_image</div>
          <Handle
            type="source"
            position={Position.Right}
            id="upscaled_image"
            style={{ background: '#FF5555' }}
            className="w-3 h-3 border-2 border-surface"
          />
        </div>
      </div>
    </div>
  )
})
