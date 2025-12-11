/**
 * VaultMind Forge - Context-Aware Properties Panel
 *
 * Shows properties relevant to the active editor.
 * Switches content based on editor type.
 */

import { useEditorStore } from '../store/editorStore'
import { useWorkflowStore } from '../store/workflowStore'
import PropertyPanelWorkflow from './PropertyPanelWorkflow'
import { Settings, Layers, Sliders } from 'lucide-react'

export default function PropertiesPanel({ editorType }) {
  const { imageEditor, promptEditor, materialEditor } = useEditorStore()
  const { selectedNodes } = useWorkflowStore()

  // Render editor-specific properties
  const renderEditorProperties = () => {
    switch (editorType) {
      case 'workflow':
        // Show workflow node properties (existing PropertyPanel logic)
        const selectedNode = selectedNodes.length === 1 ? selectedNodes[0] : null
        return <PropertyPanelWorkflow node={selectedNode} />

      case 'image':
        return (
          <div className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <Layers className="w-5 h-5 text-accent" />
              <h3 className="text-sm font-semibold">Image Editor</h3>
            </div>

            {/* Tool settings */}
            <div className="mb-4">
              <label className="block text-xs font-medium mb-2 text-textMuted">Current Tool</label>
              <div className="text-sm text-text capitalize">{imageEditor.tool}</div>
            </div>

            {/* Brush settings (if brush tool active) */}
            {(imageEditor.tool === 'brush' || imageEditor.tool === 'eraser') && (
              <>
                <div className="mb-4">
                  <label className="block text-xs font-medium mb-2 text-textMuted">
                    Brush Size: {imageEditor.brushSize}px
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={imageEditor.brushSize}
                    onChange={(e) => useEditorStore.getState().setImageEditorState({
                      brushSize: parseInt(e.target.value)
                    })}
                    className="w-full"
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-xs font-medium mb-2 text-textMuted">
                    Opacity: {imageEditor.brushOpacity}%
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={imageEditor.brushOpacity}
                    onChange={(e) => useEditorStore.getState().setImageEditorState({
                      brushOpacity: parseInt(e.target.value)
                    })}
                    className="w-full"
                  />
                </div>
              </>
            )}

            {/* Layers */}
            <div>
              <label className="block text-xs font-medium mb-2 text-textMuted">Layers</label>
              {imageEditor.layers.length === 0 ? (
                <p className="text-xs text-textMuted">No layers</p>
              ) : (
                <div className="space-y-1">
                  {imageEditor.layers.map(layer => (
                    <div
                      key={layer.id}
                      className={`p-2 rounded text-xs ${
                        layer.id === imageEditor.activeLayerId
                          ? 'bg-accent text-white'
                          : 'bg-background text-text'
                      }`}
                    >
                      {layer.name}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )

      case 'prompt':
        return (
          <div className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-5 h-5 text-accent" />
              <h3 className="text-sm font-semibold">Prompt Editor</h3>
            </div>

            {/* Style presets */}
            <div className="mb-4">
              <label className="block text-xs font-medium mb-2 text-textMuted">Style</label>
              <select
                value={promptEditor.style || ''}
                onChange={(e) => useEditorStore.getState().setPromptEditorState({
                  style: e.target.value
                })}
                className="w-full p-2 bg-background border border-border rounded text-sm"
              >
                <option value="">None</option>
                <option value="photorealistic">Photorealistic</option>
                <option value="anime">Anime</option>
                <option value="concept_art">Concept Art</option>
                <option value="game_art">Game Art</option>
              </select>
            </div>

            {/* Modifiers */}
            <div className="mb-4">
              <label className="block text-xs font-medium mb-2 text-textMuted">Modifiers</label>
              <div className="flex flex-wrap gap-1">
                {['highly detailed', '8k uhd', 'sharp focus', 'dramatic lighting'].map(modifier => (
                  <button
                    key={modifier}
                    onClick={() => {
                      const current = promptEditor.modifiers || []
                      const isActive = current.includes(modifier)
                      useEditorStore.getState().setPromptEditorState({
                        modifiers: isActive
                          ? current.filter(m => m !== modifier)
                          : [...current, modifier]
                      })
                    }}
                    className={`px-2 py-1 text-xs rounded ${
                      (promptEditor.modifiers || []).includes(modifier)
                        ? 'bg-accent text-white'
                        : 'bg-background text-text border border-border'
                    }`}
                  >
                    {modifier}
                  </button>
                ))}
              </div>
            </div>

            {/* History */}
            <div>
              <label className="block text-xs font-medium mb-2 text-textMuted">
                Recent Prompts ({promptEditor.history?.length || 0})
              </label>
            </div>
          </div>
        )

      case 'material':
        return (
          <div className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <Sliders className="w-5 h-5 text-accent" />
              <h3 className="text-sm font-semibold">Material Editor</h3>
            </div>

            {/* PBR Parameters */}
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium mb-2 text-textMuted">
                  Roughness: {materialEditor.parameters.roughness.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={materialEditor.parameters.roughness}
                  onChange={(e) => useEditorStore.getState().setMaterialEditorState({
                    parameters: {
                      ...materialEditor.parameters,
                      roughness: parseFloat(e.target.value)
                    }
                  })}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-xs font-medium mb-2 text-textMuted">
                  Metallic: {materialEditor.parameters.metallic.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={materialEditor.parameters.metallic}
                  onChange={(e) => useEditorStore.getState().setMaterialEditorState({
                    parameters: {
                      ...materialEditor.parameters,
                      metallic: parseFloat(e.target.value)
                    }
                  })}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-xs font-medium mb-2 text-textMuted">
                  Normal Strength: {materialEditor.parameters.normalStrength.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={materialEditor.parameters.normalStrength}
                  onChange={(e) => useEditorStore.getState().setMaterialEditorState({
                    parameters: {
                      ...materialEditor.parameters,
                      normalStrength: parseFloat(e.target.value)
                    }
                  })}
                  className="w-full"
                />
              </div>
            </div>

            {/* Preview mesh */}
            <div className="mt-4">
              <label className="block text-xs font-medium mb-2 text-textMuted">Preview Mesh</label>
              <div className="flex gap-2">
                {['sphere', 'cube', 'plane'].map(mesh => (
                  <button
                    key={mesh}
                    onClick={() => useEditorStore.getState().setMaterialEditorState({
                      previewMesh: mesh
                    })}
                    className={`flex-1 px-3 py-2 text-xs rounded capitalize ${
                      materialEditor.previewMesh === mesh
                        ? 'bg-accent text-white'
                        : 'bg-background text-text border border-border'
                    }`}
                  >
                    {mesh}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )

      default:
        return (
          <div className="p-4 text-center text-textMuted">
            <p className="text-sm">No properties available</p>
          </div>
        )
    }
  }

  return (
    <div className="h-full flex flex-col bg-surface overflow-y-auto">
      {renderEditorProperties()}
    </div>
  )
}
