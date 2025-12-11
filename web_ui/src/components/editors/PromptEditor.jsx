/**
 * VaultMind Forge - Prompt Editor
 *
 * Advanced prompt crafting interface with:
 * - Template library (pre-built components)
 * - Modifier tags (dropdowns ≤4 choices - Google Imagen pattern)
 * - Three-layer architecture (style, content, quality)
 * - Token counter
 * - Negative prompts
 * - Prompt history
 * - Save as asset
 */

import { useState, useEffect, useRef } from 'react'
import { useEditorStore } from '../../store/editorStore'
import {
  Type,
  Copy,
  Save,
  History,
  Sparkles,
  Tag,
  RotateCcw,
  FileText,
  Hash,
  Plus,
  X
} from 'lucide-react'

// Prompt templates (component library pattern)
const PROMPT_TEMPLATES = {
  character: {
    name: 'Character Portrait',
    template: '{subject}, {style}, {quality}',
    placeholders: {
      subject: 'character portrait of a warrior',
      style: 'digital art, highly detailed',
      quality: '8k uhd, sharp focus'
    }
  },
  environment: {
    name: 'Environment/Scene',
    template: '{scene}, {atmosphere}, {style}, {quality}',
    placeholders: {
      scene: 'fantasy castle on a mountain',
      atmosphere: 'dramatic sunset, volumetric lighting',
      style: 'concept art, cinematic',
      quality: 'ultra detailed, 8k'
    }
  },
  product: {
    name: 'Product Render',
    template: '{product}, {presentation}, {lighting}, {quality}',
    placeholders: {
      product: 'futuristic smartphone',
      presentation: 'floating on white background',
      lighting: 'studio lighting, reflections',
      quality: 'product photography, 8k uhd'
    }
  },
  artistic: {
    name: 'Artistic Style',
    template: '{subject}, {artistic_style}, {technique}, {quality}',
    placeholders: {
      subject: 'portrait of a woman',
      artistic_style: 'oil painting, impressionist',
      technique: 'visible brushstrokes, vibrant colors',
      quality: 'masterpiece, high quality'
    }
  }
}

// Modifier categories (limited to 4 choices each - Google Imagen UX)
const MODIFIER_CATEGORIES = {
  style: {
    label: 'Style',
    options: [
      { value: 'photorealistic', label: 'Photorealistic' },
      { value: 'anime', label: 'Anime/Manga' },
      { value: 'concept_art', label: 'Concept Art' },
      { value: 'oil_painting', label: 'Oil Painting' }
    ]
  },
  quality: {
    label: 'Quality',
    options: [
      { value: '8k_uhd', label: '8K UHD' },
      { value: 'highly_detailed', label: 'Highly Detailed' },
      { value: 'masterpiece', label: 'Masterpiece' },
      { value: 'sharp_focus', label: 'Sharp Focus' }
    ]
  },
  lighting: {
    label: 'Lighting',
    options: [
      { value: 'dramatic', label: 'Dramatic Lighting' },
      { value: 'studio', label: 'Studio Lighting' },
      { value: 'natural', label: 'Natural Light' },
      { value: 'volumetric', label: 'Volumetric' }
    ]
  },
  composition: {
    label: 'Composition',
    options: [
      { value: 'portrait', label: 'Portrait' },
      { value: 'wide_angle', label: 'Wide Angle' },
      { value: 'close_up', label: 'Close-up' },
      { value: 'aerial', label: 'Aerial View' }
    ]
  }
}

export default function PromptEditor() {
  const {
    promptEditor,
    setPromptEditorState,
    openEditors,
    activeEditorId,
    markEditorModified
  } = useEditorStore()

  const [mainPrompt, setMainPrompt] = useState(promptEditor.text || '')
  const [negativePrompt, setNegativePrompt] = useState(promptEditor.negativePrompt || '')
  const [selectedModifiers, setSelectedModifiers] = useState({
    style: promptEditor.modifiers?.find(m => MODIFIER_CATEGORIES.style.options.some(o => o.value === m)) || '',
    quality: promptEditor.modifiers?.find(m => MODIFIER_CATEGORIES.quality.options.some(o => o.value === m)) || '',
    lighting: promptEditor.modifiers?.find(m => MODIFIER_CATEGORIES.lighting.options.some(o => o.value === m)) || '',
    composition: promptEditor.modifiers?.find(m => MODIFIER_CATEGORIES.composition.options.some(o => o.value === m)) || ''
  })
  const [customTags, setCustomTags] = useState([])
  const [tokenCount, setTokenCount] = useState(0)

  const mainPromptRef = useRef(null)

  // Calculate token count (rough approximation: ~1.3 tokens per word)
  useEffect(() => {
    const fullPrompt = buildFullPrompt()
    const wordCount = fullPrompt.split(/\s+/).filter(Boolean).length
    setTokenCount(Math.ceil(wordCount * 1.3))
  }, [mainPrompt, negativePrompt, selectedModifiers, customTags])

  // Mark editor as modified when prompt changes
  useEffect(() => {
    if (mainPrompt || negativePrompt || Object.values(selectedModifiers).some(Boolean) || customTags.length > 0) {
      markEditorModified(activeEditorId, true)
    }
  }, [mainPrompt, negativePrompt, selectedModifiers, customTags, activeEditorId])

  const buildFullPrompt = () => {
    const parts = []

    // Main prompt
    if (mainPrompt.trim()) {
      parts.push(mainPrompt.trim())
    }

    // Modifiers
    const modifiers = Object.values(selectedModifiers).filter(Boolean)
    if (modifiers.length > 0) {
      parts.push(modifiers.join(', '))
    }

    // Custom tags
    if (customTags.length > 0) {
      parts.push(customTags.join(', '))
    }

    return parts.join(', ')
  }

  const applyTemplate = (templateKey) => {
    const template = PROMPT_TEMPLATES[templateKey]
    if (!template) return

    // Fill template with placeholders
    let prompt = template.template
    Object.entries(template.placeholders).forEach(([key, value]) => {
      prompt = prompt.replace(`{${key}}`, value)
    })

    setMainPrompt(prompt)
  }

  const handleModifierChange = (category, value) => {
    setSelectedModifiers(prev => ({
      ...prev,
      [category]: value
    }))
  }

  const addCustomTag = () => {
    const tag = prompt('Enter custom tag:')
    if (tag && tag.trim()) {
      setCustomTags(prev => [...prev, tag.trim()])
    }
  }

  const removeCustomTag = (index) => {
    setCustomTags(prev => prev.filter((_, i) => i !== index))
  }

  const copyToClipboard = () => {
    const fullPrompt = buildFullPrompt()
    navigator.clipboard.writeText(fullPrompt)
    // TODO: Show toast notification
  }

  const savePrompt = () => {
    const fullPrompt = buildFullPrompt()
    setPromptEditorState({
      text: mainPrompt,
      negativePrompt: negativePrompt,
      modifiers: Object.values(selectedModifiers).filter(Boolean).concat(customTags),
      history: [...(promptEditor.history || []), {
        prompt: fullPrompt,
        negative: negativePrompt,
        timestamp: Date.now()
      }].slice(-20) // Keep last 20
    })

    markEditorModified(activeEditorId, false)
    // TODO: Show success notification
  }

  const clearAll = () => {
    if (confirm('Clear all fields?')) {
      setMainPrompt('')
      setNegativePrompt('')
      setSelectedModifiers({ style: '', quality: '', lighting: '', composition: '' })
      setCustomTags([])
    }
  }

  const loadFromHistory = (historyItem) => {
    setMainPrompt(historyItem.prompt)
    setNegativePrompt(historyItem.negative)
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Toolbar */}
      <div className="h-12 bg-surface border-b border-border flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Type className="w-5 h-5 text-accent" />
          <span className="text-sm font-medium text-text">Prompt Editor</span>
          <div className="ml-4 px-2 py-1 bg-background rounded border border-border">
            <Hash className="w-3 h-3 inline text-textMuted mr-1" />
            <span className="text-xs text-textMuted">{tokenCount} tokens</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={copyToClipboard}
            className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1"
            title="Copy to clipboard"
          >
            <Copy className="w-4 h-4" />
            Copy
          </button>
          <button
            onClick={savePrompt}
            className="px-3 py-1.5 bg-accent text-white rounded text-sm hover:bg-accent/90 flex items-center gap-1"
            title="Save prompt"
          >
            <Save className="w-4 h-4" />
            Save
          </button>
          <button
            onClick={clearAll}
            className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border"
            title="Clear all"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto p-6 space-y-6">
          {/* Template selector */}
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              <FileText className="w-4 h-4 inline mr-1" />
              Start from Template
            </label>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(PROMPT_TEMPLATES).map(([key, template]) => (
                <button
                  key={key}
                  onClick={() => applyTemplate(key)}
                  className="p-3 bg-surface border border-border rounded text-left hover:border-accent transition-colors"
                >
                  <div className="text-sm font-medium text-text">{template.name}</div>
                  <div className="text-xs text-textMuted mt-1 truncate">
                    {template.template}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Main prompt */}
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              Main Prompt
            </label>
            <textarea
              ref={mainPromptRef}
              value={mainPrompt}
              onChange={(e) => setMainPrompt(e.target.value)}
              placeholder="Describe what you want to generate..."
              className="w-full h-32 p-3 bg-surface border border-border rounded text-sm text-text placeholder-textMuted resize-none focus:outline-none focus:border-accent"
            />
          </div>

          {/* Modifier categories (4 choices each - Google Imagen pattern) */}
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              <Tag className="w-4 h-4 inline mr-1" />
              Style Modifiers
            </label>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(MODIFIER_CATEGORIES).map(([category, config]) => (
                <div key={category}>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    {config.label}
                  </label>
                  <select
                    value={selectedModifiers[category]}
                    onChange={(e) => handleModifierChange(category, e.target.value)}
                    className="w-full p-2 bg-surface border border-border rounded text-sm text-text"
                  >
                    <option value="">None</option>
                    {config.options.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>

          {/* Custom tags */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-text">Custom Tags</label>
              <button
                onClick={addCustomTag}
                className="px-2 py-1 bg-accent text-white rounded text-xs hover:bg-accent/90 flex items-center gap-1"
              >
                <Plus className="w-3 h-3" />
                Add Tag
              </button>
            </div>
            {customTags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {customTags.map((tag, index) => (
                  <div
                    key={index}
                    className="px-2 py-1 bg-surface border border-border rounded flex items-center gap-1"
                  >
                    <span className="text-sm text-text">{tag}</span>
                    <button
                      onClick={() => removeCustomTag(index)}
                      className="text-textMuted hover:text-red-500"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-textMuted italic">No custom tags added</div>
            )}
          </div>

          {/* Negative prompt */}
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              Negative Prompt
              <span className="text-xs text-textMuted ml-2">(what to avoid)</span>
            </label>
            <textarea
              value={negativePrompt}
              onChange={(e) => setNegativePrompt(e.target.value)}
              placeholder="ugly, blurry, low quality, distorted..."
              className="w-full h-20 p-3 bg-surface border border-border rounded text-sm text-text placeholder-textMuted resize-none focus:outline-none focus:border-accent"
            />
          </div>

          {/* Full prompt preview */}
          <div className="p-4 bg-surface border border-border rounded">
            <div className="text-xs font-medium text-textMuted mb-2">Full Prompt Preview</div>
            <div className="text-sm text-text whitespace-pre-wrap">
              {buildFullPrompt() || <span className="text-textMuted italic">Empty prompt</span>}
            </div>
            {negativePrompt && (
              <>
                <div className="text-xs font-medium text-textMuted mt-3 mb-1">Negative:</div>
                <div className="text-sm text-text">{negativePrompt}</div>
              </>
            )}
          </div>

          {/* Prompt history */}
          {promptEditor.history && promptEditor.history.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-text mb-2">
                <History className="w-4 h-4 inline mr-1" />
                Recent Prompts
              </label>
              <div className="space-y-2">
                {promptEditor.history.slice(-5).reverse().map((item, index) => (
                  <button
                    key={index}
                    onClick={() => loadFromHistory(item)}
                    className="w-full p-3 bg-surface border border-border rounded text-left hover:border-accent transition-colors"
                  >
                    <div className="text-sm text-text truncate">{item.prompt}</div>
                    <div className="text-xs text-textMuted mt-1">
                      {new Date(item.timestamp).toLocaleString()}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
