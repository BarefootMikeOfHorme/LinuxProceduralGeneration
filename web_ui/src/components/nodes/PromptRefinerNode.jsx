import { memo } from 'react'
import { Handle, Position } from 'reactflow'
import { Bot } from 'lucide-react'

export default memo(({ data, selected }) => {
  return (
    <div
      className={
        'px-4 py-3 shadow-lg rounded-lg bg-surface border-2 min-w-[240px] ' +
        (selected ? 'border-accent' : 'border-border')
      }
    >
      <div className="flex items-center gap-2 mb-2">
        <Bot className="w-8 h-8 p-1.5 rounded-lg bg-green-500/20 text-green-500" />
        <div className="flex-1">
          <div className="font-semibold text-sm flex items-center gap-2">
            Prompt Refiner
            <span className="text-xs px-1.5 py-0.5 bg-accent/20 text-accent rounded">
              Merlinv1
            </span>
          </div>
          <div className="text-xs text-textMuted">forge_agents</div>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Handle
            type="target"
            position={Position.Left}
            id="prompt"
            style={{ background: '#55FF55' }}
            className="w-3 h-3 border-2 border-surface"
          />
          <div className="text-xs text-textMuted">prompt</div>
        </div>

        <div className="flex items-center justify-end gap-2">
          <div className="text-xs text-textMuted">refined_prompt</div>
          <Handle
            type="source"
            position={Position.Right}
            id="refined_prompt"
            style={{ background: '#55FF55' }}
            className="w-3 h-3 border-2 border-surface"
          />
        </div>
      </div>
    </div>
  )
})
