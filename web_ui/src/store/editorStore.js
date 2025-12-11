/**
 * VaultMind Forge - Editor Store
 *
 * Manages state for the multi-editor studio system.
 * Handles editor tabs, active editor, asset browser, and editor-specific state.
 */

import { create } from 'zustand'

export const useEditorStore = create((set, get) => ({
  // ============================================================================
  // Editor Tabs & Active Editor
  // ============================================================================

  activeEditorType: 'workflow', // 'workflow' | 'image' | 'prompt' | 'material' | 'video' | 'batch'
  openEditors: [
    { id: 'workflow-main', type: 'workflow', title: 'Workflow', asset: null }
  ],

  setActiveEditor: (editorType) => set({ activeEditorType: editorType }),

  openEditor: (editorType, asset = null, title = null) => {
    const { openEditors } = get()
    const editorId = asset ? `${editorType}-${asset.id}` : `${editorType}-${Date.now()}`

    // Check if editor already open for this asset
    const existing = openEditors.find(ed => ed.id === editorId)
    if (existing) {
      set({ activeEditorType: editorType })
      return
    }

    // Create new editor tab
    const newEditor = {
      id: editorId,
      type: editorType,
      title: title || `${editorType} Editor`,
      asset: asset,
      modified: false
    }

    set({
      openEditors: [...openEditors, newEditor],
      activeEditorType: editorType
    })
  },

  closeEditor: (editorId) => {
    const { openEditors, activeEditorType } = get()
    const closingEditor = openEditors.find(ed => ed.id === editorId)

    // Don't allow closing the last editor
    if (openEditors.length === 1) return

    // If closing active editor, switch to another
    if (closingEditor.type === activeEditorType) {
      const remainingEditors = openEditors.filter(ed => ed.id !== editorId)
      set({
        openEditors: remainingEditors,
        activeEditorType: remainingEditors[remainingEditors.length - 1].type
      })
    } else {
      set({
        openEditors: openEditors.filter(ed => ed.id !== editorId)
      })
    }
  },

  markEditorModified: (editorId, modified = true) => {
    set(state => ({
      openEditors: state.openEditors.map(ed =>
        ed.id === editorId ? { ...ed, modified } : ed
      )
    }))
  },

  // ============================================================================
  // Asset Browser
  // ============================================================================

  assets: {
    images: [],
    videos: [],
    meshes: [],
    materials: [],
    prompts: [],
    audio: []
  },

  selectedAssets: [],
  assetBrowserVisible: true,
  assetBrowserFilter: 'all', // 'all' | 'images' | 'videos' | 'meshes' | 'materials' | 'prompts'

  addAsset: (type, asset) => {
    set(state => ({
      assets: {
        ...state.assets,
        [type]: [...state.assets[type], { ...asset, id: asset.id || Date.now(), createdAt: Date.now() }]
      }
    }))
  },

  removeAsset: (type, assetId) => {
    set(state => ({
      assets: {
        ...state.assets,
        [type]: state.assets[type].filter(a => a.id !== assetId)
      }
    }))
  },

  selectAsset: (assetId) => {
    const { selectedAssets } = get()
    if (selectedAssets.includes(assetId)) {
      set({ selectedAssets: selectedAssets.filter(id => id !== assetId) })
    } else {
      set({ selectedAssets: [...selectedAssets, assetId] })
    }
  },

  clearSelectedAssets: () => set({ selectedAssets: [] }),

  toggleAssetBrowser: () => set(state => ({ assetBrowserVisible: !state.assetBrowserVisible })),

  setAssetFilter: (filter) => set({ assetBrowserFilter: filter }),

  // ============================================================================
  // Editor-Specific State
  // ============================================================================

  // Image Editor State
  imageEditor: {
    tool: 'select', // 'select' | 'crop' | 'brush' | 'eraser' | 'fill'
    layers: [],
    activeLayerId: null,
    zoom: 1.0,
    brushSize: 20,
    brushOpacity: 100,
    history: [],
    historyIndex: -1
  },

  setImageEditorState: (updates) => set(state => ({
    imageEditor: { ...state.imageEditor, ...updates }
  })),

  // Prompt Editor State
  promptEditor: {
    text: '',
    style: null,
    modifiers: [],
    negativePrompt: '',
    templates: [],
    history: []
  },

  setPromptEditorState: (updates) => set(state => ({
    promptEditor: { ...state.promptEditor, ...updates }
  })),

  // Material Editor State
  materialEditor: {
    channels: {
      baseColor: null,
      normal: null,
      roughness: null,
      metallic: null,
      height: null,
      ambientOcclusion: null
    },
    previewMesh: 'sphere', // 'sphere' | 'cube' | 'plane' | 'custom'
    lighting: 'studio',
    parameters: {
      roughness: 0.5,
      metallic: 0.0,
      normalStrength: 1.0,
      heightScale: 0.1
    }
  },

  setMaterialEditorState: (updates) => set(state => ({
    materialEditor: { ...state.materialEditor, ...updates }
  })),

  // Batch Processor State
  batchProcessor: {
    selectedAssets: [],
    operations: [],
    progress: 0,
    isProcessing: false
  },

  setBatchProcessorState: (updates) => set(state => ({
    batchProcessor: { ...state.batchProcessor, ...updates }
  })),

  // ============================================================================
  // UI State
  // ============================================================================

  propertiesPanelVisible: true,
  propertiesPanelWidth: 300,

  togglePropertiesPanel: () => set(state => ({
    propertiesPanelVisible: !state.propertiesPanelVisible
  })),

  setPropertiesPanelWidth: (width) => set({ propertiesPanelWidth: width }),

  // ============================================================================
  // Utility Functions
  // ============================================================================

  reset: () => set({
    activeEditorType: 'workflow',
    openEditors: [
      { id: 'workflow-main', type: 'workflow', title: 'Workflow', asset: null }
    ],
    selectedAssets: [],
    imageEditor: {
      tool: 'select',
      layers: [],
      activeLayerId: null,
      zoom: 1.0,
      brushSize: 20,
      brushOpacity: 100,
      history: [],
      historyIndex: -1
    },
    promptEditor: {
      text: '',
      style: null,
      modifiers: [],
      negativePrompt: '',
      templates: [],
      history: []
    }
  })
}))
