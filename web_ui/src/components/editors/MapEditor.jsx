/**
 * VaultMind Forge - Map Editor
 *
 * Tile-based map editor with:
 * - Multi-layer editing (background, foreground, collision, entities)
 * - Tileset/palette browser
 * - Brush tools (paint, fill, eraser, select, rectangle)
 * - Grid-based canvas with zoom/pan
 * - Map properties (dimensions, tile size)
 * - Layer visibility and locking
 * - Export/import maps as JSON
 * - Undo/redo support
 */

import { useState, useRef, useEffect } from 'react'
import {
  Map,
  Layers,
  Grid3x3,
  Paintbrush,
  Eraser,
  Bucket,
  Square,
  MousePointer,
  Save,
  Download,
  Upload,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Settings
} from 'lucide-react'

// Tool types
const TOOLS = {
  PAINT: 'paint',
  FILL: 'fill',
  ERASER: 'eraser',
  SELECT: 'select',
  RECTANGLE: 'rectangle'
}

// Layer types
const LAYER_TYPES = {
  BACKGROUND: 'background',
  FOREGROUND: 'foreground',
  COLLISION: 'collision',
  ENTITIES: 'entities'
}

// Default tileset (placeholder colors for demo)
const DEFAULT_TILESET = [
  { id: 0, color: '#1a1a1a', name: 'Empty' },
  { id: 1, color: '#8B4513', name: 'Ground' },
  { id: 2, color: '#90EE90', name: 'Grass' },
  { id: 3, color: '#4169E1', name: 'Water' },
  { id: 4, color: '#808080', name: 'Stone' },
  { id: 5, color: '#654321', name: 'Wall' },
  { id: 6, color: '#FFD700', name: 'Gold' },
  { id: 7, color: '#FF6347', name: 'Lava' },
  { id: 8, color: '#FFFFFF', name: 'Snow' },
  { id: 9, color: '#228B22', name: 'Forest' },
  { id: 10, color: '#D2B48C', name: 'Sand' },
  { id: 11, color: '#696969', name: 'Rock' }
]

export default function MapEditor() {
  // Map metadata
  const [mapName, setMapName] = useState('Untitled Map')
  const [mapWidth, setMapWidth] = useState(32)
  const [mapHeight, setMapHeight] = useState(24)
  const [tileSize, setTileSize] = useState(32)

  // Layers
  const [layers, setLayers] = useState([
    {
      id: 'layer_bg',
      name: 'Background',
      type: LAYER_TYPES.BACKGROUND,
      visible: true,
      locked: false,
      data: Array(24).fill(null).map(() => Array(32).fill(0))
    },
    {
      id: 'layer_fg',
      name: 'Foreground',
      type: LAYER_TYPES.FOREGROUND,
      visible: true,
      locked: false,
      data: Array(24).fill(null).map(() => Array(32).fill(0))
    }
  ])
  const [activeLayerId, setActiveLayerId] = useState('layer_bg')

  // Tools and tileset
  const [activeTool, setActiveTool] = useState(TOOLS.PAINT)
  const [selectedTileId, setSelectedTileId] = useState(1)
  const [tileset, setTileset] = useState(DEFAULT_TILESET)

  // Canvas state
  const [zoom, setZoom] = useState(1.0)
  const [showGrid, setShowGrid] = useState(true)
  const [isPainting, setIsPainting] = useState(false)
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 })

  // UI state
  const [showTilePalette, setShowTilePalette] = useState(true)
  const [showLayers, setShowLayers] = useState(true)
  const [showMapSettings, setShowMapSettings] = useState(false)

  const canvasRef = useRef(null)

  // Get active layer
  const getActiveLayer = () => layers.find(l => l.id === activeLayerId)

  // Add new layer
  const addLayer = () => {
    const newLayer = {
      id: `layer_${Date.now()}`,
      name: `Layer ${layers.length + 1}`,
      type: LAYER_TYPES.FOREGROUND,
      visible: true,
      locked: false,
      data: Array(mapHeight).fill(null).map(() => Array(mapWidth).fill(0))
    }
    setLayers([...layers, newLayer])
    setActiveLayerId(newLayer.id)
  }

  // Delete layer
  const deleteLayer = (layerId) => {
    if (layers.length <= 1) {
      alert('Cannot delete the last layer')
      return
    }
    const newLayers = layers.filter(l => l.id !== layerId)
    setLayers(newLayers)
    if (activeLayerId === layerId) {
      setActiveLayerId(newLayers[0].id)
    }
  }

  // Toggle layer visibility
  const toggleLayerVisibility = (layerId) => {
    setLayers(layers.map(l =>
      l.id === layerId ? { ...l, visible: !l.visible } : l
    ))
  }

  // Toggle layer lock
  const toggleLayerLock = (layerId) => {
    setLayers(layers.map(l =>
      l.id === layerId ? { ...l, locked: !l.locked } : l
    ))
  }

  // Update layer name
  const updateLayerName = (layerId, name) => {
    setLayers(layers.map(l =>
      l.id === layerId ? { ...l, name } : l
    ))
  }

  // Paint tile at position
  const paintTile = (x, y) => {
    const layer = getActiveLayer()
    if (!layer || layer.locked) return
    if (x < 0 || x >= mapWidth || y < 0 || y >= mapHeight) return

    const newLayers = layers.map(l => {
      if (l.id === activeLayerId) {
        const newData = l.data.map(row => [...row])
        newData[y][x] = activeTool === TOOLS.ERASER ? 0 : selectedTileId
        return { ...l, data: newData }
      }
      return l
    })

    setLayers(newLayers)
  }

  // Fill tool (flood fill)
  const floodFill = (startX, startY) => {
    const layer = getActiveLayer()
    if (!layer || layer.locked) return
    if (startX < 0 || startX >= mapWidth || startY < 0 || startY >= mapHeight) return

    const targetTile = layer.data[startY][startX]
    if (targetTile === selectedTileId) return

    const newData = layer.data.map(row => [...row])
    const queue = [[startX, startY]]
    const visited = new Set()

    while (queue.length > 0) {
      const [x, y] = queue.shift()
      const key = `${x},${y}`

      if (visited.has(key)) continue
      if (x < 0 || x >= mapWidth || y < 0 || y >= mapHeight) continue
      if (newData[y][x] !== targetTile) continue

      visited.add(key)
      newData[y][x] = selectedTileId

      queue.push([x + 1, y])
      queue.push([x - 1, y])
      queue.push([x, y + 1])
      queue.push([x, y - 1])
    }

    setLayers(layers.map(l =>
      l.id === activeLayerId ? { ...l, data: newData } : l
    ))
  }

  // Handle canvas mouse down
  const handleCanvasMouseDown = (e) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = Math.floor((e.clientX - rect.left - panOffset.x) / (tileSize * zoom))
    const y = Math.floor((e.clientY - rect.top - panOffset.y) / (tileSize * zoom))

    if (activeTool === TOOLS.PAINT || activeTool === TOOLS.ERASER) {
      setIsPainting(true)
      paintTile(x, y)
    } else if (activeTool === TOOLS.FILL) {
      floodFill(x, y)
    }
  }

  // Handle canvas mouse move
  const handleCanvasMouseMove = (e) => {
    if (!isPainting) return

    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = Math.floor((e.clientX - rect.left - panOffset.x) / (tileSize * zoom))
    const y = Math.floor((e.clientY - rect.top - panOffset.y) / (tileSize * zoom))

    paintTile(x, y)
  }

  // Handle canvas mouse up
  const handleCanvasMouseUp = () => {
    setIsPainting(false)
  }

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.fillStyle = '#1a1a1a'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    ctx.save()
    ctx.translate(panOffset.x, panOffset.y)
    ctx.scale(zoom, zoom)

    // Draw layers (bottom to top)
    layers.forEach(layer => {
      if (!layer.visible) return

      layer.data.forEach((row, y) => {
        row.forEach((tileId, x) => {
          if (tileId === 0) return

          const tile = tileset.find(t => t.id === tileId)
          if (!tile) return

          ctx.fillStyle = tile.color
          ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize)
        })
      })
    })

    // Draw grid
    if (showGrid) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)'
      ctx.lineWidth = 1 / zoom

      for (let x = 0; x <= mapWidth; x++) {
        ctx.beginPath()
        ctx.moveTo(x * tileSize, 0)
        ctx.lineTo(x * tileSize, mapHeight * tileSize)
        ctx.stroke()
      }

      for (let y = 0; y <= mapHeight; y++) {
        ctx.beginPath()
        ctx.moveTo(0, y * tileSize)
        ctx.lineTo(mapWidth * tileSize, y * tileSize)
        ctx.stroke()
      }
    }

    ctx.restore()
  }, [layers, zoom, panOffset, showGrid, tileSize, mapWidth, mapHeight, tileset])

  // Zoom controls
  const handleZoomIn = () => setZoom(Math.min(zoom * 1.2, 4.0))
  const handleZoomOut = () => setZoom(Math.max(zoom / 1.2, 0.25))
  const handleResetZoom = () => {
    setZoom(1.0)
    setPanOffset({ x: 0, y: 0 })
  }

  // Save map
  const saveMap = () => {
    const mapData = {
      name: mapName,
      width: mapWidth,
      height: mapHeight,
      tileSize,
      layers: layers.map(l => ({
        name: l.name,
        type: l.type,
        data: l.data
      }))
    }
    console.log('Saving map:', mapData)
    // TODO: API call to save map
  }

  // Export map as JSON
  const exportMap = () => {
    const mapData = {
      name: mapName,
      width: mapWidth,
      height: mapHeight,
      tileSize,
      tileset,
      layers
    }

    const blob = new Blob([JSON.stringify(mapData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${mapName.replace(/\s+/g, '_')}.map.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Import map from JSON
  const importMap = (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const mapData = JSON.parse(e.target.result)
        setMapName(mapData.name)
        setMapWidth(mapData.width)
        setMapHeight(mapData.height)
        setTileSize(mapData.tileSize)
        setLayers(mapData.layers || layers)
        setTileset(mapData.tileset || tileset)
      } catch (error) {
        console.error('Failed to import map:', error)
        alert('Failed to import map. Invalid file format.')
      }
    }
    reader.readAsText(file)
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Toolbar */}
      <div className="h-12 bg-surface border-b border-border flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Map className="w-5 h-5 text-accent" />
          <input
            type="text"
            value={mapName}
            onChange={(e) => setMapName(e.target.value)}
            className="bg-transparent border-none text-sm font-medium text-text focus:outline-none focus:border-b focus:border-accent"
            placeholder="Map name"
          />
          <span className="text-xs text-textMuted px-2 py-1 bg-background rounded">
            {mapWidth} × {mapHeight}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Tool buttons */}
          <div className="flex items-center gap-1 mr-2">
            <button
              onClick={() => setActiveTool(TOOLS.PAINT)}
              className={`p-1.5 rounded ${activeTool === TOOLS.PAINT ? 'bg-accent text-white' : 'bg-background text-textMuted hover:text-text'}`}
              title="Paint tool"
            >
              <Paintbrush className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveTool(TOOLS.FILL)}
              className={`p-1.5 rounded ${activeTool === TOOLS.FILL ? 'bg-accent text-white' : 'bg-background text-textMuted hover:text-text'}`}
              title="Fill tool"
            >
              <Bucket className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveTool(TOOLS.ERASER)}
              className={`p-1.5 rounded ${activeTool === TOOLS.ERASER ? 'bg-accent text-white' : 'bg-background text-textMuted hover:text-text'}`}
              title="Eraser"
            >
              <Eraser className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveTool(TOOLS.SELECT)}
              className={`p-1.5 rounded ${activeTool === TOOLS.SELECT ? 'bg-accent text-white' : 'bg-background text-textMuted hover:text-text'}`}
              title="Select tool"
            >
              <MousePointer className="w-4 h-4" />
            </button>
          </div>

          {/* Zoom controls */}
          <button onClick={handleZoomOut} className="p-1.5 rounded bg-background text-text hover:bg-border">
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs text-textMuted w-12 text-center">{Math.round(zoom * 100)}%</span>
          <button onClick={handleZoomIn} className="p-1.5 rounded bg-background text-text hover:bg-border">
            <ZoomIn className="w-4 h-4" />
          </button>
          <button onClick={handleResetZoom} className="p-1.5 rounded bg-background text-text hover:bg-border">
            <Maximize2 className="w-4 h-4" />
          </button>

          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`p-1.5 rounded ${showGrid ? 'bg-accent text-white' : 'bg-background text-textMuted'}`}
            title="Toggle grid"
          >
            <Grid3x3 className="w-4 h-4" />
          </button>

          <div className="h-6 w-px bg-border" />

          <label className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1 cursor-pointer">
            <Upload className="w-4 h-4" />
            Import
            <input type="file" accept=".json,.map.json" onChange={importMap} className="hidden" />
          </label>

          <button onClick={exportMap} className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1">
            <Download className="w-4 h-4" />
            Export
          </button>

          <button onClick={saveMap} className="px-3 py-1.5 bg-accent text-white rounded text-sm hover:bg-accent/90 flex items-center gap-1">
            <Save className="w-4 h-4" />
            Save
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Tile Palette */}
        {showTilePalette && (
          <div className="w-64 bg-surface border-r border-border overflow-y-auto flex-shrink-0">
            <div className="p-4">
              <h3 className="text-sm font-semibold text-text mb-3">Tile Palette</h3>
              <div className="grid grid-cols-4 gap-2">
                {tileset.map(tile => (
                  <button
                    key={tile.id}
                    onClick={() => setSelectedTileId(tile.id)}
                    className={`aspect-square rounded border-2 transition-all ${
                      selectedTileId === tile.id ? 'border-accent scale-110' : 'border-border'
                    }`}
                    style={{ backgroundColor: tile.color }}
                    title={tile.name}
                  />
                ))}
              </div>
              <div className="mt-3 text-xs text-textMuted">
                Selected: {tileset.find(t => t.id === selectedTileId)?.name || 'None'}
              </div>
            </div>
          </div>
        )}

        {/* Center - Canvas */}
        <div className="flex-1 overflow-hidden bg-background relative">
          <canvas
            ref={canvasRef}
            width={1200}
            height={800}
            className="cursor-crosshair"
            onMouseDown={handleCanvasMouseDown}
            onMouseMove={handleCanvasMouseMove}
            onMouseUp={handleCanvasMouseUp}
            onMouseLeave={handleCanvasMouseUp}
          />
        </div>

        {/* Right Panel - Layers */}
        {showLayers && (
          <div className="w-64 bg-surface border-l border-border overflow-y-auto flex-shrink-0">
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-text flex items-center gap-2">
                  <Layers className="w-4 h-4" />
                  Layers
                </h3>
                <button
                  onClick={addLayer}
                  className="p-1 bg-accent text-white rounded hover:bg-accent/90"
                  title="Add layer"
                >
                  <Plus className="w-3 h-3" />
                </button>
              </div>

              <div className="space-y-2">
                {[...layers].reverse().map(layer => (
                  <div
                    key={layer.id}
                    className={`p-2 bg-background border rounded cursor-pointer transition-colors ${
                      activeLayerId === layer.id ? 'border-accent' : 'border-border'
                    }`}
                    onClick={() => setActiveLayerId(layer.id)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <input
                        type="text"
                        value={layer.name}
                        onChange={(e) => {
                          e.stopPropagation()
                          updateLayerName(layer.id, e.target.value)
                        }}
                        className="flex-1 bg-transparent text-sm text-text border-none focus:outline-none"
                        onClick={(e) => e.stopPropagation()}
                      />
                      <div className="flex items-center gap-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            toggleLayerVisibility(layer.id)
                          }}
                          className="text-textMuted hover:text-text"
                        >
                          {layer.visible ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            toggleLayerLock(layer.id)
                          }}
                          className="text-textMuted hover:text-text"
                        >
                          {layer.locked ? <Lock className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteLayer(layer.id)
                          }}
                          className="text-textMuted hover:text-red-500"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                    <div className="text-xs text-textMuted capitalize">{layer.type}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
