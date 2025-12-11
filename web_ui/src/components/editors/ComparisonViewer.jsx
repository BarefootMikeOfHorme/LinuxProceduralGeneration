/**
 * VaultMind Forge - Comparison Viewer
 *
 * Side-by-side asset comparison with:
 * - 2-6 asset grid layout (NN/G best practice)
 * - Rating system (1-5 stars)
 * - Synchronized zoom/pan
 * - Metadata diff view
 * - Export selections
 */

import { useState, useEffect, useRef } from 'react'
import { useEditorStore } from '../../store/editorStore'
import {
  Columns,
  Grid3x3,
  ZoomIn,
  ZoomOut,
  Move,
  Star,
  Download,
  X,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Info
} from 'lucide-react'

export default function ComparisonViewer() {
  const {
    comparisonViewer,
    setComparisonViewerState,
    assets
  } = useEditorStore()

  const {
    selectedAssets,
    viewMode,
    syncZoom,
    syncPan,
    showMetadata,
    ratings
  } = comparisonViewer

  const [zoom, setZoom] = useState(1.0)
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 })
  const [activeAssetIndex, setActiveAssetIndex] = useState(0)
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })

  const containerRef = useRef(null)

  // Get selected asset objects from IDs
  const getSelectedAssetObjects = () => {
    const allAssets = []
    Object.values(assets).forEach(assetList => {
      allAssets.push(...assetList)
    })
    return selectedAssets
      .map(id => allAssets.find(a => a.id === id))
      .filter(Boolean)
      .slice(0, 6) // Limit to 6 (best practice)
  }

  const assetObjects = getSelectedAssetObjects()

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (assetObjects.length === 0) return

      if (e.key === 'ArrowLeft') {
        e.preventDefault()
        setActiveAssetIndex(prev => Math.max(0, prev - 1))
      } else if (e.key === 'ArrowRight') {
        e.preventDefault()
        setActiveAssetIndex(prev => Math.min(assetObjects.length - 1, prev + 1))
      } else if (e.key === 'f') {
        e.preventDefault()
        toggleFavorite(assetObjects[activeAssetIndex]?.id)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [assetObjects.length, activeAssetIndex])

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.25, 4.0))
  }

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.25, 0.25))
  }

  const handleResetView = () => {
    setZoom(1.0)
    setPanOffset({ x: 0, y: 0 })
  }

  const handlePanStart = (e) => {
    if (e.button !== 0) return // Only left mouse button
    setIsPanning(true)
    setPanStart({
      x: e.clientX - panOffset.x,
      y: e.clientY - panOffset.y
    })
  }

  const handlePanMove = (e) => {
    if (!isPanning) return
    setPanOffset({
      x: e.clientX - panStart.x,
      y: e.clientY - panStart.y
    })
  }

  const handlePanEnd = () => {
    setIsPanning(false)
  }

  const setRating = (assetId, rating) => {
    setComparisonViewerState({
      ratings: { ...ratings, [assetId]: rating }
    })
  }

  const toggleFavorite = (assetId) => {
    const currentRating = ratings[assetId] || 0
    setRating(assetId, currentRating === 5 ? 0 : 5)
  }

  const removeAsset = (assetId) => {
    setComparisonViewerState({
      selectedAssets: selectedAssets.filter(id => id !== assetId)
    })
  }

  const exportSelected = () => {
    // TODO: Implement export functionality
    console.log('Exporting assets:', assetObjects)
  }

  const getGridColumns = () => {
    const count = assetObjects.length
    if (count <= 2) return 2
    if (count <= 4) return 2
    return 3
  }

  const renderAssetCard = (asset, index) => {
    const isActive = index === activeAssetIndex
    const rating = ratings[asset.id] || 0

    return (
      <div
        key={asset.id}
        className={`
          relative bg-surface rounded border-2 transition-all
          ${isActive ? 'border-accent' : 'border-border'}
        `}
        onClick={() => setActiveAssetIndex(index)}
      >
        {/* Remove button */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            removeAsset(asset.id)
          }}
          className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded hover:bg-red-600 z-10"
          title="Remove from comparison"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Asset preview */}
        <div
          className="relative bg-background overflow-hidden cursor-move"
          style={{
            height: viewMode === 'grid' ? '300px' : '500px'
          }}
          onMouseDown={syncPan ? handlePanStart : undefined}
          onMouseMove={syncPan ? handlePanMove : undefined}
          onMouseUp={syncPan ? handlePanEnd : undefined}
          onMouseLeave={syncPan ? handlePanEnd : undefined}
        >
          {asset.thumbnail ? (
            <img
              src={asset.thumbnail}
              alt={asset.name}
              className="w-full h-full object-contain"
              style={{
                transform: syncZoom
                  ? `scale(${zoom}) translate(${panOffset.x / zoom}px, ${panOffset.y / zoom}px)`
                  : undefined
              }}
              draggable={false}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-textMuted">
              No preview available
            </div>
          )}
        </div>

        {/* Asset info */}
        <div className="p-3 border-t border-border">
          <p className="text-sm font-medium text-text truncate" title={asset.name}>
            {asset.name || 'Untitled'}
          </p>
          <p className="text-xs text-textMuted">{asset.assetType}</p>

          {/* Rating */}
          <div className="flex items-center gap-1 mt-2">
            {[1, 2, 3, 4, 5].map(star => (
              <button
                key={star}
                onClick={(e) => {
                  e.stopPropagation()
                  setRating(asset.id, star)
                }}
                className="transition-colors"
              >
                <Star
                  className={`w-4 h-4 ${
                    star <= rating
                      ? 'fill-yellow-500 text-yellow-500'
                      : 'text-textMuted'
                  }`}
                />
              </button>
            ))}
          </div>

          {/* Metadata */}
          {showMetadata && asset.metadata && (
            <div className="mt-2 text-xs text-textMuted space-y-1">
              {asset.metadata.resolution && (
                <div>Resolution: {asset.metadata.resolution}</div>
              )}
              {asset.metadata.format && (
                <div>Format: {asset.metadata.format}</div>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  if (assetObjects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-background">
        <div className="text-center max-w-md">
          <Columns className="w-16 h-16 text-accent mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-text mb-2">Comparison Viewer</h2>
          <p className="text-textMuted mb-4">
            Select 2-6 assets from the Asset Browser to compare them side-by-side
          </p>
          <p className="text-sm text-textMuted">
            Double-click assets while holding Ctrl to add them to comparison
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Toolbar */}
      <div className="h-12 bg-surface border-b border-border flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-text">
            Comparing {assetObjects.length} assets
          </span>

          {/* View mode toggle */}
          <div className="ml-4 flex items-center gap-1">
            <button
              onClick={() => setComparisonViewerState({ viewMode: 'grid' })}
              className={`p-1.5 rounded ${
                viewMode === 'grid'
                  ? 'bg-accent text-white'
                  : 'bg-background text-textMuted hover:text-text'
              }`}
              title="Grid view"
            >
              <Grid3x3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setComparisonViewerState({ viewMode: 'slider' })}
              className={`p-1.5 rounded ${
                viewMode === 'slider'
                  ? 'bg-accent text-white'
                  : 'bg-background text-textMuted hover:text-text'
              }`}
              title="Slider view"
            >
              <Columns className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Zoom controls */}
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded bg-background text-text hover:bg-border"
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs text-textMuted w-12 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded bg-background text-text hover:bg-border"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetView}
            className="p-1.5 rounded bg-background text-text hover:bg-border"
            title="Reset view"
          >
            <Maximize2 className="w-4 h-4" />
          </button>

          {/* Sync controls */}
          <div className="ml-2 flex items-center gap-2">
            <label className="flex items-center gap-1 text-xs text-textMuted cursor-pointer">
              <input
                type="checkbox"
                checked={syncZoom}
                onChange={(e) => setComparisonViewerState({ syncZoom: e.target.checked })}
                className="rounded"
              />
              Sync Zoom
            </label>
            <label className="flex items-center gap-1 text-xs text-textMuted cursor-pointer">
              <input
                type="checkbox"
                checked={syncPan}
                onChange={(e) => setComparisonViewerState({ syncPan: e.target.checked })}
                className="rounded"
              />
              Sync Pan
            </label>
          </div>

          {/* Export */}
          <button
            onClick={exportSelected}
            className="ml-2 px-3 py-1.5 bg-accent text-white rounded text-sm hover:bg-accent/90"
            title="Export selected assets"
          >
            <Download className="w-4 h-4 inline mr-1" />
            Export
          </button>
        </div>
      </div>

      {/* Comparison grid */}
      <div ref={containerRef} className="flex-1 overflow-auto p-4">
        {viewMode === 'grid' ? (
          <div
            className="grid gap-4 h-full"
            style={{
              gridTemplateColumns: `repeat(${getGridColumns()}, 1fr)`
            }}
          >
            {assetObjects.map((asset, index) => renderAssetCard(asset, index))}
          </div>
        ) : (
          <div className="flex gap-4 h-full">
            {assetObjects.map((asset, index) => (
              <div key={asset.id} className="flex-1">
                {renderAssetCard(asset, index)}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Navigation footer (for slider mode) */}
      {viewMode === 'slider' && assetObjects.length > 1 && (
        <div className="h-12 bg-surface border-t border-border flex items-center justify-center gap-4 flex-shrink-0">
          <button
            onClick={() => setActiveAssetIndex(prev => Math.max(0, prev - 1))}
            disabled={activeAssetIndex === 0}
            className="p-2 rounded bg-background text-text hover:bg-border disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-sm text-textMuted">
            {activeAssetIndex + 1} / {assetObjects.length}
          </span>
          <button
            onClick={() => setActiveAssetIndex(prev => Math.min(assetObjects.length - 1, prev + 1))}
            disabled={activeAssetIndex === assetObjects.length - 1}
            className="p-2 rounded bg-background text-text hover:bg-border disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}
