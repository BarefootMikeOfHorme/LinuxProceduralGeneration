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
  // Each tab represents an ASSET being edited, not an editor type
  // The editor type is determined by the asset type

  activeEditorId: 'workflow-main', // ID of active tab
  openEditors: [
    {
      id: 'workflow-main',
      type: 'workflow',
      title: 'Untitled Workflow',
      asset: null, // null for new/unsaved assets
      modified: false,
      icon: 'workflow'
    }
  ],

  setActiveEditor: (editorId) => set({ activeEditorId: editorId }),

  openAsset: (asset) => {
    const { openEditors } = get()
    const editorId = `asset-${asset.id}`

    // Check if this asset is already open
    const existing = openEditors.find(ed => ed.id === editorId)
    if (existing) {
      set({ activeEditorId: editorId })
      return
    }

    // Determine editor type from asset type
    let editorType = 'workflow'
    if (asset.assetType === 'images') editorType = 'image'
    else if (asset.assetType === 'videos') editorType = 'video'
    else if (asset.assetType === 'meshes') editorType = 'mesh'
    else if (asset.assetType === 'materials') editorType = 'material'
    else if (asset.assetType === 'prompts') editorType = 'prompt'
    else if (asset.assetType === 'audio') editorType = 'audio'

    // Create new tab for this asset
    const newEditor = {
      id: editorId,
      type: editorType,
      title: asset.name || 'Untitled',
      asset: asset,
      modified: false,
      icon: editorType
    }

    set({
      openEditors: [...openEditors, newEditor],
      activeEditorId: editorId
    })
  },

  openNewAsset: (assetType) => {
    const { openEditors } = get()
    const editorId = `new-${assetType}-${Date.now()}`

    // Determine editor type
    let editorType = assetType
    let title = `Untitled ${assetType}`

    const newEditor = {
      id: editorId,
      type: editorType,
      title: title,
      asset: null, // New asset not yet saved
      modified: true, // New assets are always "modified"
      icon: editorType
    }

    set({
      openEditors: [...openEditors, newEditor],
      activeEditorId: editorId
    })
  },

  closeEditor: (editorId) => {
    const { openEditors, activeEditorId } = get()
    const closingEditor = openEditors.find(ed => ed.id === editorId)

    // Don't allow closing the last editor
    if (openEditors.length === 1) return

    // Check if modified and warn user
    if (closingEditor?.modified) {
      // TODO: Show confirmation dialog
      // For now, just close it
    }

    // If closing active editor, switch to another
    if (editorId === activeEditorId) {
      const remainingEditors = openEditors.filter(ed => ed.id !== editorId)
      set({
        openEditors: remainingEditors,
        activeEditorId: remainingEditors[remainingEditors.length - 1].id
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
    activeEditorId: 'workflow-main',
    openEditors: [
      { id: 'workflow-main', type: 'workflow', title: 'Untitled Workflow', asset: null, modified: false }
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
