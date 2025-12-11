/**
 * VaultMind Forge - Editor Registry
 *
 * Central registry for all editor types in the studio.
 * Defines editor metadata, icons, supported asset types, and components.
 */

import {
  FileImage,
  FileVideo,
  Box,
  Palette,
  Type,
  Layers,
  Workflow,
  Grid3x3
} from 'lucide-react'

export const EditorType = {
  WORKFLOW: 'workflow',
  IMAGE: 'image',
  PROMPT: 'prompt',
  MATERIAL: 'material',
  VIDEO: 'video',
  MESH: 'mesh',
  BATCH: 'batch',
  AUDIO: 'audio'
}

export const editorDefinitions = {
  [EditorType.WORKFLOW]: {
    id: EditorType.WORKFLOW,
    name: 'Workflow Editor',
    description: 'Node-based visual workflow creation',
    icon: Workflow,
    color: '#3b82f6', // blue
    supportedAssets: [],
    shortcuts: {
      open: 'Ctrl+Shift+W',
      execute: 'F5',
      save: 'Ctrl+S'
    },
    defaultWidth: '100%',
    canHaveMultiple: false,
    features: [
      'Node graph editing',
      'Type-safe connections',
      'Real-time execution',
      'Workflow versioning'
    ]
  },

  [EditorType.IMAGE]: {
    id: EditorType.IMAGE,
    name: 'Image Editor',
    description: 'Non-destructive image editing with layers',
    icon: FileImage,
    color: '#ec4899', // pink
    supportedAssets: ['image/png', 'image/jpeg', 'image/webp'],
    shortcuts: {
      open: 'Ctrl+Shift+I',
      save: 'Ctrl+S',
      undo: 'Ctrl+Z',
      redo: 'Ctrl+Y'
    },
    defaultWidth: '100%',
    canHaveMultiple: true,
    features: [
      'Layer system',
      'Adjustment layers',
      'Smart filters',
      'Crop, rotate, resize',
      'Inpainting/outpainting',
      'Export presets'
    ]
  },

  [EditorType.PROMPT]: {
    id: EditorType.PROMPT,
    name: 'Prompt Editor',
    description: 'Advanced prompt crafting and refinement',
    icon: Type,
    color: '#10b981', // green
    supportedAssets: ['text/plain', 'application/json'],
    shortcuts: {
      open: 'Ctrl+Shift+P',
      save: 'Ctrl+S',
      refine: 'Ctrl+R'
    },
    defaultWidth: '100%',
    canHaveMultiple: true,
    features: [
      'Template library',
      'Modifier tags',
      'Negative prompts',
      'Token counting',
      'Style presets',
      'Prompt history',
      'AI refinement'
    ]
  },

  [EditorType.MATERIAL]: {
    id: EditorType.MATERIAL,
    name: 'Material Editor',
    description: 'PBR material creation and editing',
    icon: Palette,
    color: '#f59e0b', // amber
    supportedAssets: ['material/pbr', 'image/png'],
    shortcuts: {
      open: 'Ctrl+Shift+M',
      save: 'Ctrl+S',
      preview: 'Space'
    },
    defaultWidth: '100%',
    canHaveMultiple: true,
    features: [
      'PBR channel editing',
      'Real-time preview',
      'Multiple lighting presets',
      'Preview meshes (sphere, cube, plane)',
      'Export to Unity/Unreal',
      'Substance Designer integration'
    ]
  },

  [EditorType.VIDEO]: {
    id: EditorType.VIDEO,
    name: 'Video Editor',
    description: 'Timeline-based video editing',
    icon: FileVideo,
    color: '#8b5cf6', // purple
    supportedAssets: ['video/mp4', 'video/webm'],
    shortcuts: {
      open: 'Ctrl+Shift+V',
      save: 'Ctrl+S',
      play: 'Space',
      split: 'S'
    },
    defaultWidth: '100%',
    canHaveMultiple: true,
    features: [
      'Timeline editing',
      'Transition effects',
      'Audio sync',
      'Frame-by-frame preview',
      'Render queue',
      'Export presets'
    ]
  },

  [EditorType.MESH]: {
    id: EditorType.MESH,
    name: '3D Viewer',
    description: '3D mesh inspection and basic editing',
    icon: Box,
    color: '#06b6d4', // cyan
    supportedAssets: ['model/gltf+json', 'model/obj', 'model/fbx'],
    shortcuts: {
      open: 'Ctrl+Shift+3',
      rotate: 'R',
      pan: 'Middle Mouse',
      zoom: 'Scroll'
    },
    defaultWidth: '100%',
    canHaveMultiple: true,
    features: [
      '3D viewport',
      'Material preview',
      'Wireframe mode',
      'UV unwrapping view',
      'Export options',
      'Modifier stack display'
    ]
  },

  [EditorType.BATCH]: {
    id: EditorType.BATCH,
    name: 'Batch Processor',
    description: 'Multi-asset batch operations',
    icon: Grid3x3,
    color: '#ef4444', // red
    supportedAssets: ['*'],
    shortcuts: {
      open: 'Ctrl+Shift+B',
      selectAll: 'Ctrl+A',
      process: 'Ctrl+Enter'
    },
    defaultWidth: '100%',
    canHaveMultiple: false,
    features: [
      'Grid view of assets',
      'Tag and categorize',
      'Bulk operations',
      'Filter and search',
      'Export sets',
      'Quality sorting'
    ]
  },

  [EditorType.AUDIO]: {
    id: EditorType.AUDIO,
    name: 'Audio Editor',
    description: 'Audio waveform editing',
    icon: Layers,
    color: '#14b8a6', // teal
    supportedAssets: ['audio/wav', 'audio/mp3', 'audio/ogg'],
    shortcuts: {
      open: 'Ctrl+Shift+A',
      save: 'Ctrl+S',
      play: 'Space',
      cut: 'C'
    },
    defaultWidth: '100%',
    canHaveMultiple: true,
    features: [
      'Waveform display',
      'Cut, copy, paste',
      'Effects (reverb, EQ)',
      'Fade in/out',
      'Normalization',
      'Export formats'
    ]
  }
}

/**
 * Get editor definition by type
 */
export function getEditorDefinition(editorType) {
  return editorDefinitions[editorType]
}

/**
 * Get all editor types
 */
export function getAllEditorTypes() {
  return Object.keys(editorDefinitions)
}

/**
 * Get editors that support a specific asset type
 */
export function getEditorsForAsset(assetType) {
  return Object.values(editorDefinitions).filter(editor =>
    editor.supportedAssets.includes(assetType) || editor.supportedAssets.includes('*')
  )
}

/**
 * Get default editor for asset type
 */
export function getDefaultEditorForAsset(assetType) {
  if (assetType.startsWith('image/')) return EditorType.IMAGE
  if (assetType.startsWith('video/')) return EditorType.VIDEO
  if (assetType.startsWith('audio/')) return EditorType.AUDIO
  if (assetType.startsWith('model/')) return EditorType.MESH
  if (assetType.startsWith('material/')) return EditorType.MATERIAL
  if (assetType.startsWith('text/')) return EditorType.PROMPT

  return null
}

export default editorDefinitions
