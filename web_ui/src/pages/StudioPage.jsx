/**
 * VaultMind Forge - Studio Page
 *
 * New multi-editor studio interface.
 * Replaces the old single-page workflow editor.
 */

import React from 'react'
import { ReactFlowProvider } from 'reactflow'
import Studio from '../components/Studio'
import FileBrowser from '../components/FileBrowser'
import OutputModal from '../components/OutputModal'
import ExecutionPanel from '../components/ExecutionPanel'
import useKeyboardShortcuts from '../hooks/useKeyboardShortcuts'
import { useWorkflowStore } from '../store/workflowStore'
import { useEditorStore } from '../store/editorStore'
import { showHelpDialog } from '../utils/notifications'

const StudioPage = () => {
  const { executeWorkflow, saveWorkflow } = useWorkflowStore()
  const { toggleAssetBrowser, togglePropertiesPanel, activeEditorId, openEditors } = useEditorStore()

  // Derive the current editor type from the active editor
  const currentEditor = openEditors.find(ed => ed.id === activeEditorId)
  const editorType = currentEditor?.type || 'workflow'

  useKeyboardShortcuts({
    // Global shortcuts
    'ctrl+b': (e) => {
      e.preventDefault()
      toggleAssetBrowser()
    },
    'ctrl+p': (e) => {
      e.preventDefault()
      togglePropertiesPanel()
    },
    'f1': () => showHelpDialog('VaultMind Forge Studio Shortcuts', [
      { key: 'Ctrl+B', action: 'Toggle Asset Browser' },
      { key: 'Ctrl+P', action: 'Toggle Properties Panel' },
      { key: 'Ctrl+T', action: 'New Editor Tab' },
      { key: 'Ctrl+W', action: 'Close Current Tab' },
      { key: 'F1', action: 'Show this help' },
      { key: '---', action: '---' },
      { key: 'Workflow Editor:', action: '' },
      { key: 'F5', action: 'Execute workflow' },
      { key: 'Ctrl+S', action: 'Save workflow' },
      { key: 'Shift+A', action: 'Add node' },
      { key: 'Del', action: 'Delete selected' },
    ]),

    // Workflow editor specific (only when workflow editor is active)
    ...(editorType === 'workflow' && {
      'f5': () => executeWorkflow(),
      'ctrl+s': (e) => {
        e.preventDefault()
        saveWorkflow('Untitled Workflow', 'Auto-saved workflow')
      },
    })
  })

  return (
    <ReactFlowProvider>
      <div className="h-full w-full">
        <Studio />

        {/* Global modals and panels */}
        <FileBrowser />
        <OutputModal />
        <ExecutionPanel />
      </div>
    </ReactFlowProvider>
  )
}

export default StudioPage
