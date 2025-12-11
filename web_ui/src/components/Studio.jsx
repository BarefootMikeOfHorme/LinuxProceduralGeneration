/**
 * VaultMind Forge - Studio
 *
 * Main application container with multi-editor support.
 * Replaces the single-page workflow editor with a full content creation suite.
 */

import { useState, useEffect } from 'react'
import { useEditorStore } from '../store/editorStore'
import { getEditorDefinition } from '../lib/editorRegistry'
import EditorTabs from './EditorTabs'
import AssetBrowser from './AssetBrowser'
import PropertiesPanel from './PropertiesPanel'
import NodeEditor from './NodeEditor'
import ComparisonViewer from './editors/ComparisonViewer'
import PromptEditor from './editors/PromptEditor'
import ParameterSweep from './editors/ParameterSweep'
import TemplateEditor from './editors/TemplateEditor'
import PipelineEditor from './editors/PipelineEditor'
import AutomationEditor from './editors/AutomationEditor'
import MapEditor from './editors/MapEditor'
import MapMaker from './editors/MapMaker'
import { Menu, ChevronLeft, ChevronRight, Settings } from 'lucide-react'

export default function Studio() {
  const {
    activeEditorId,
    openEditors,
    assetBrowserVisible,
    propertiesPanelVisible,
    toggleAssetBrowser,
    togglePropertiesPanel
  } = useEditorStore()

  const [leftPanelWidth, setLeftPanelWidth] = useState(250)
  const [rightPanelWidth, setRightPanelWidth] = useState(300)

  // Get the currently active editor tab (asset being edited)
  const currentEditor = openEditors.find(ed => ed.id === activeEditorId)
  const editorType = currentEditor?.type || 'workflow'
  const editorDef = getEditorDefinition(editorType)

  // Render the active editor component based on asset type
  const renderActiveEditor = () => {
    switch (editorType) {
      case 'workflow':
        return <NodeEditor />

      case 'prompt':
        return <PromptEditor />

      case 'pipeline':
        return <PipelineEditor />

      case 'automation':
        return <AutomationEditor />

      case 'template':
        return <TemplateEditor />

      case 'parameter_sweep':
        return <ParameterSweep />

      case 'comparison':
        return <ComparisonViewer />

      case 'map':
        return <MapEditor />

      case 'map_maker':
        return <MapMaker />

      default:
        return (
          <div className="flex items-center justify-center h-full bg-background">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-red-500 mb-2">Unknown Editor</h2>
              <p className="text-textMuted">Editor type: {editorType}</p>
            </div>
          </div>
        )
    }
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-background text-text overflow-hidden">
      {/* Top Menu Bar */}
      <div className="h-12 bg-surface border-b border-border flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-accent rounded flex items-center justify-center">
              <span className="text-white font-bold text-sm">VM</span>
            </div>
            <h1 className="text-lg font-bold text-accent">VaultMind Forge</h1>
          </div>

          <div className="flex items-center gap-2 ml-4">
            <button
              onClick={toggleAssetBrowser}
              className={`p-2 rounded transition-colors ${
                assetBrowserVisible
                  ? 'bg-accent text-white'
                  : 'bg-background hover:bg-border text-text'
              }`}
              title="Toggle Asset Browser (Ctrl+B)"
            >
              {assetBrowserVisible ? <ChevronLeft className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>

            <button
              onClick={togglePropertiesPanel}
              className={`p-2 rounded transition-colors ${
                propertiesPanelVisible
                  ? 'bg-accent text-white'
                  : 'bg-background hover:bg-border text-text'
              }`}
              title="Toggle Properties Panel (Ctrl+P)"
            >
              {propertiesPanelVisible ? <ChevronRight className="w-4 h-4" /> : <Settings className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-textMuted">
            {editorDef?.name || 'Unknown Editor'}
          </span>
          {currentEditor?.modified && (
            <span className="text-xs text-accent">●</span>
          )}
        </div>
      </div>

      {/* Editor Tabs */}
      <EditorTabs />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Asset Browser */}
        {assetBrowserVisible && (
          <div
            className="bg-surface border-r border-border overflow-hidden flex-shrink-0"
            style={{ width: `${leftPanelWidth}px` }}
          >
            <AssetBrowser />
          </div>
        )}

        {/* Center - Active Editor */}
        <div className="flex-1 overflow-hidden bg-background">
          {renderActiveEditor()}
        </div>

        {/* Right Panel - Properties */}
        {propertiesPanelVisible && (
          <div
            className="bg-surface border-l border-border overflow-hidden flex-shrink-0"
            style={{ width: `${rightPanelWidth}px` }}
          >
            <PropertiesPanel editorType={editorType} />
          </div>
        )}
      </div>

      {/* Bottom Status Bar */}
      <div className="h-6 bg-surface border-t border-border flex items-center justify-between px-4 text-xs text-textMuted flex-shrink-0">
        <div className="flex items-center gap-4">
          <span>{openEditors.length} editor(s) open</span>
          {currentEditor?.asset && (
            <span>• {currentEditor.asset.name}</span>
          )}
        </div>

        <div className="flex items-center gap-4">
          {editorDef?.shortcuts?.save && (
            <span>Save: {editorDef.shortcuts.save}</span>
          )}
          {editorDef?.shortcuts?.execute && (
            <span>• Execute: {editorDef.shortcuts.execute}</span>
          )}
        </div>
      </div>
    </div>
  )
}
