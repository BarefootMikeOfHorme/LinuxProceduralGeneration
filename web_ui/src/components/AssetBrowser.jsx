/**
 * VaultMind Forge - Asset Browser
 *
 * Central hub for all generated assets.
 * Similar to Unreal Engine's Content Browser or Unity's Project panel.
 */

import { useState } from 'react'
import { useEditorStore } from '../store/editorStore'
import { getDefaultEditorForAsset } from '../lib/editorRegistry'
import {
  FileImage,
  FileVideo,
  Box,
  Palette,
  FileText,
  Music,
  Search,
  Filter,
  SortAsc,
  Grid3x3,
  List,
  Star,
  Trash2
} from 'lucide-react'

const assetTypeIcons = {
  images: FileImage,
  videos: FileVideo,
  meshes: Box,
  materials: Palette,
  prompts: FileText,
  audio: Music
}

export default function AssetBrowser() {
  const {
    assets,
    selectedAssets,
    assetBrowserFilter,
    setAssetFilter,
    selectAsset,
    clearSelectedAssets,
    removeAsset,
    openAsset
  } = useEditorStore()

  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState('grid') // 'grid' | 'list'
  const [sortBy, setSortBy] = useState('date') // 'date' | 'name' | 'type'

  // Get all assets based on filter
  const getFilteredAssets = () => {
    let allAssets = []

    if (assetBrowserFilter === 'all') {
      Object.entries(assets).forEach(([type, assetList]) => {
        allAssets.push(...assetList.map(asset => ({ ...asset, assetType: type })))
      })
    } else {
      const type = assetBrowserFilter
      allAssets = (assets[type] || []).map(asset => ({ ...asset, assetType: type }))
    }

    // Apply search filter
    if (searchQuery) {
      allAssets = allAssets.filter(asset =>
        asset.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        asset.path?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Apply sorting
    if (sortBy === 'date') {
      allAssets.sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
    } else if (sortBy === 'name') {
      allAssets.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    }

    return allAssets
  }

  const filteredAssets = getFilteredAssets()

  const handleAssetDoubleClick = (asset) => {
    // Open asset in appropriate editor (editor type determined automatically)
    openAsset(asset)
  }

  const handleDeleteAsset = (asset, e) => {
    e.stopPropagation()
    if (confirm(`Delete ${asset.name}?`)) {
      removeAsset(asset.assetType, asset.id)
    }
  }

  // Asset type filter buttons
  const assetTypes = ['all', ...Object.keys(assets)]

  return (
    <div className="h-full flex flex-col bg-surface">
      {/* Header */}
      <div className="p-3 border-b border-border">
        <h2 className="text-sm font-semibold text-text mb-2">Asset Browser</h2>

        {/* Search */}
        <div className="relative mb-2">
          <Search className="w-4 h-4 absolute left-2 top-2.5 text-textMuted" />
          <input
            type="text"
            placeholder="Search assets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-2 bg-background border border-border rounded text-sm text-text placeholder-textMuted focus:outline-none focus:border-accent"
          />
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded ${
                viewMode === 'grid' ? 'bg-accent text-white' : 'bg-background text-textMuted hover:text-text'
              }`}
              title="Grid view"
            >
              <Grid3x3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded ${
                viewMode === 'list' ? 'bg-accent text-white' : 'bg-background text-textMuted hover:text-text'
              }`}
              title="List view"
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setSortBy(sortBy === 'date' ? 'name' : 'date')}
            className="p-1.5 rounded bg-background text-textMuted hover:text-text"
            title={`Sort by ${sortBy === 'date' ? 'name' : 'date'}`}
          >
            <SortAsc className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 px-2 py-2 border-b border-border overflow-x-auto">
        {assetTypes.map(type => {
          const count = type === 'all'
            ? Object.values(assets).reduce((sum, arr) => sum + arr.length, 0)
            : assets[type]?.length || 0

          return (
            <button
              key={type}
              onClick={() => setAssetFilter(type)}
              className={`px-3 py-1 rounded text-xs font-medium whitespace-nowrap transition-colors ${
                assetBrowserFilter === type
                  ? 'bg-accent text-white'
                  : 'bg-background text-textMuted hover:bg-border hover:text-text'
              }`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)} ({count})
            </button>
          )
        })}
      </div>

      {/* Asset grid/list */}
      <div className="flex-1 overflow-y-auto p-2">
        {filteredAssets.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-4">
            <div className="w-16 h-16 bg-background rounded-full flex items-center justify-center mb-3">
              <FileImage className="w-8 h-8 text-textMuted" />
            </div>
            <p className="text-sm text-textMuted mb-1">No assets yet</p>
            <p className="text-xs text-textMuted">
              Generate content in the Workflow Editor
            </p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-2 gap-2">
            {filteredAssets.map(asset => {
              const Icon = assetTypeIcons[asset.assetType] || FileImage
              const isSelected = selectedAssets.includes(asset.id)

              return (
                <div
                  key={asset.id}
                  onClick={() => selectAsset(asset.id)}
                  onDoubleClick={() => handleAssetDoubleClick(asset)}
                  className={`
                    relative group cursor-pointer rounded border-2 transition-all
                    ${isSelected
                      ? 'border-accent bg-accent/10'
                      : 'border-border hover:border-accent/50 bg-background'
                    }
                  `}
                >
                  {/* Thumbnail */}
                  <div className="aspect-square bg-background/50 rounded-t flex items-center justify-center overflow-hidden">
                    {asset.thumbnail ? (
                      <img
                        src={asset.thumbnail}
                        alt={asset.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <Icon className="w-8 h-8 text-textMuted" />
                    )}
                  </div>

                  {/* Info */}
                  <div className="p-2">
                    <p className="text-xs font-medium text-text truncate" title={asset.name}>
                      {asset.name || 'Untitled'}
                    </p>
                    <p className="text-xs text-textMuted truncate">
                      {asset.assetType}
                    </p>
                  </div>

                  {/* Actions (on hover) */}
                  <div className="absolute top-1 right-1 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => handleDeleteAsset(asset, e)}
                      className="p-1 bg-red-500 text-white rounded hover:bg-red-600"
                      title="Delete"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredAssets.map(asset => {
              const Icon = assetTypeIcons[asset.assetType] || FileImage
              const isSelected = selectedAssets.includes(asset.id)

              return (
                <div
                  key={asset.id}
                  onClick={() => selectAsset(asset.id)}
                  onDoubleClick={() => handleAssetDoubleClick(asset)}
                  className={`
                    flex items-center gap-2 p-2 rounded cursor-pointer transition-colors group
                    ${isSelected
                      ? 'bg-accent/10 border border-accent'
                      : 'bg-background hover:bg-border border border-transparent'
                    }
                  `}
                >
                  <Icon className="w-4 h-4 text-textMuted flex-shrink-0" />
                  <span className="text-sm text-text flex-1 truncate">{asset.name || 'Untitled'}</span>
                  <span className="text-xs text-textMuted">{asset.assetType}</span>
                  <button
                    onClick={(e) => handleDeleteAsset(asset, e)}
                    className="p-1 text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Delete"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      {selectedAssets.length > 0 && (
        <div className="p-2 border-t border-border bg-background/50">
          <div className="flex items-center justify-between">
            <span className="text-xs text-textMuted">
              {selectedAssets.length} selected
            </span>
            <button
              onClick={clearSelectedAssets}
              className="text-xs text-accent hover:underline"
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
