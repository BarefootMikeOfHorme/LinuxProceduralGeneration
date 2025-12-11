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
  Grid3x3,
  GitBranch,
  Zap,
  FileCode,
  TrendingUp,
  Columns
} from 'lucide-react'

export const EditorType = {
  WORKFLOW: 'workflow',
  IMAGE: 'image',
  PROMPT: 'prompt',
  MATERIAL: 'material',
  VIDEO: 'video',
  MESH: 'mesh',
  BATCH: 'batch',
  AUDIO: 'audio',
  // Pipeline-specific editors
  PIPELINE: 'pipeline',
  AUTOMATION: 'automation',
  TEMPLATE: 'template',
  PARAMETER_SWEEP: 'parameter_sweep',
  COMPARISON: 'comparison'
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
  },

  // ========================================================================
  // PIPELINE-SPECIFIC EDITORS
  // ========================================================================

  [EditorType.PIPELINE]: {
    id: EditorType.PIPELINE,
    name: 'Pipeline Editor',
    description: 'Multi-stage processing pipelines',
    icon: GitBranch,
    color: '#6366f1', // indigo
    supportedAssets: ['pipeline/json'],
    shortcuts: {
      open: 'Ctrl+Shift+L',
      save: 'Ctrl+S',
      execute: 'F6',
      addStage: 'Shift+S'
    },
    defaultWidth: '100%',
    canHaveMultiple: true,
    features: [
      'Multi-stage pipeline graph',
      'Stage dependencies',
      'Parallel execution paths',
      'Error handling & rollback',
      'Pipeline versioning',
      'Stage templates',
      'Real-time progress tracking',
      'Output caching per stage'
    ]
  },

  [EditorType.AUTOMATION]: {
    id: EditorType.AUTOMATION,
    name: 'Automation Editor',
    description: 'Event-driven workflows with triggers',
    icon: Zap,
    color: '#f97316', // orange
    supportedAssets: ['automation/json'],
    shortcuts: {
      open: 'Ctrl+Shift+U',
      save: 'Ctrl+S',
      test: 'Ctrl+T',
      addTrigger: 'Shift+T'
    },
    defaultWidth: '100%',
    canHaveMultiple: true,
    features: [
      'Event triggers (time, file, webhook)',
      'Conditional logic',
      'Action sequences',
      'Variable passing',
      'Error notifications',
      'Execution history',
      'Dry-run mode',
      'Schedule management'
    ]
  },

  [EditorType.TEMPLATE]: {
    id: EditorType.TEMPLATE,
    name: 'Template Editor',
    description: 'Reusable workflow templates',
    icon: FileCode,
    color: '#a855f7', // purple
    supportedAssets: ['template/json'],
    shortcuts: {
      open: 'Ctrl+Shift+T',
      save: 'Ctrl+S',
      instantiate: 'Ctrl+Enter',
      addParam: 'Shift+P'
    },
    defaultWidth: '100%',
    canHaveMultiple: true,
    features: [
      'Parameterized workflows',
      'Default values',
      'Type constraints',
      'Template inheritance',
      'Instant preview',
      'Template marketplace',
      'Version control',
      'Export/import'
    ]
  },

  [EditorType.PARAMETER_SWEEP]: {
    id: EditorType.PARAMETER_SWEEP,
    name: 'Parameter Sweep',
    description: 'Grid-based parameter exploration',
    icon: TrendingUp,
    color: '#0ea5e9', // sky blue
    supportedAssets: ['sweep/json'],
    shortcuts: {
      open: 'Ctrl+Shift+G',
      save: 'Ctrl+S',
      generate: 'Ctrl+Enter',
      addAxis: 'Shift+A'
    },
    defaultWidth: '100%',
    canHaveMultiple: true,
    features: [
      'Multi-dimensional parameter grids',
      'Range definitions (linear, log, custom)',
      'Combinatorial generation',
      'Priority queue',
      'Result tracking',
      'Best result highlighting',
      'Export results as dataset',
      'Resume interrupted sweeps'
    ]
  },

  [EditorType.COMPARISON]: {
    id: EditorType.COMPARISON,
    name: 'Comparison Viewer',
    description: 'Side-by-side result comparison',
    icon: Columns,
    color: '#22c55e', // green
    supportedAssets: ['*'],
    shortcuts: {
      open: 'Ctrl+Shift+C',
      nextResult: 'Right',
      prevResult: 'Left',
      favorite: 'F'
    },
    defaultWidth: '100%',
    canHaveMultiple: true,
    features: [
      '2-6 asset side-by-side view',
      'Synchronized zoom/pan',
      'Metadata diff view',
      'Rating system',
      'Export selections',
      'Diff highlighting',
      'A/B testing mode',
      'Parameter correlation'
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
