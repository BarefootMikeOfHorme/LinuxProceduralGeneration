/**
 * VaultMind Forge - Editor Tabs
 *
 * Tab bar for switching between open editors.
 * Similar to VS Code, Photoshop, or browser tabs.
 */

import { useEditorStore } from '../store/editorStore'
import { getEditorDefinition } from '../lib/editorRegistry'
import { X, Plus } from 'lucide-react'

export default function EditorTabs() {
  const {
    activeEditorType,
    openEditors,
    setActiveEditor,
    closeEditor,
    openEditor
  } = useEditorStore()

  const handleNewEditor = () => {
    // Show editor type picker (for now, just cycle through types)
    const types = ['workflow', 'image', 'prompt', 'material', 'video', 'batch']
    const currentIndex = types.indexOf(activeEditorType)
    const nextType = types[(currentIndex + 1) % types.length]
    openEditor(nextType)
  }

  return (
    <div className="h-10 bg-surface border-b border-border flex items-center overflow-x-auto flex-shrink-0">
      <div className="flex items-center h-full">
        {openEditors.map((editor) => {
          const editorDef = getEditorDefinition(editor.type)
          const Icon = editorDef?.icon
          const isActive = editor.type === activeEditorType

          return (
            <div
              key={editor.id}
              className={`
                h-full px-4 flex items-center gap-2 border-r border-border cursor-pointer
                transition-colors relative group
                ${isActive
                  ? 'bg-background text-text'
                  : 'bg-surface text-textMuted hover:bg-background/50'
                }
              `}
              onClick={() => setActiveEditor(editor.type)}
            >
              {/* Active indicator */}
              {isActive && (
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-accent" />
              )}

              {/* Editor icon */}
              {Icon && (
                <Icon
                  className="w-4 h-4"
                  style={{ color: isActive ? editorDef.color : undefined }}
                />
              )}

              {/* Editor title */}
              <span className="text-sm font-medium whitespace-nowrap">
                {editor.title}
              </span>

              {/* Modified indicator */}
              {editor.modified && (
                <span className="text-accent text-xs">●</span>
              )}

              {/* Close button */}
              {openEditors.length > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    closeEditor(editor.id)
                  }}
                  className="ml-2 p-0.5 rounded hover:bg-border opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          )
        })}

        {/* New editor button */}
        <button
          onClick={handleNewEditor}
          className="h-full px-3 flex items-center gap-2 hover:bg-background/50 transition-colors border-r border-border"
          title="Open new editor (Ctrl+T)"
        >
          <Plus className="w-4 h-4 text-textMuted" />
        </button>
      </div>
    </div>
  )
}
