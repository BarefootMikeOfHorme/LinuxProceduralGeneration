/**
 * VaultMind Forge - Map Maker
 *
 * Procedural map generation with:
 * - Multiple generation algorithms (Perlin noise, cellular automata, BSP, drunkard's walk)
 * - Seed-based reproducible generation
 * - Real-time parameter adjustment
 * - Preview with live regeneration
 * - Export to Map Editor format
 * - Template presets (terrain, dungeon, cave, maze)
 * - Biome distribution controls
 */

import { useState, useEffect, useRef } from 'react'
import {
  Wand2,
  RefreshCw,
  Save,
  Download,
  Copy,
  Settings,
  Layers,
  Shuffle,
  ChevronDown,
  ChevronRight
} from 'lucide-react'

// Generation algorithms
const ALGORITHMS = {
  PERLIN: 'perlin',
  CELLULAR: 'cellular',
  BSP: 'bsp',
  DRUNKARD: 'drunkard',
  MAZE: 'maze'
}

// Biome types (for terrain generation)
const BIOMES = {
  WATER: { id: 3, name: 'Water', threshold: 0.3 },
  SAND: { id: 10, name: 'Sand', threshold: 0.4 },
  GRASS: { id: 2, name: 'Grass', threshold: 0.6 },
  FOREST: { id: 9, name: 'Forest', threshold: 0.75 },
  MOUNTAIN: { id: 4, name: 'Mountain', threshold: 0.85 },
  SNOW: { id: 8, name: 'Snow', threshold: 1.0 }
}

// Template presets
const PRESETS = {
  terrain: {
    name: 'Terrain',
    algorithm: ALGORITHMS.PERLIN,
    config: {
      scale: 0.05,
      octaves: 4,
      persistence: 0.5,
      lacunarity: 2.0
    }
  },
  dungeon: {
    name: 'Dungeon (BSP)',
    algorithm: ALGORITHMS.BSP,
    config: {
      minRoomSize: 4,
      maxRoomSize: 10,
      corridorWidth: 1
    }
  },
  cave: {
    name: 'Cave',
    algorithm: ALGORITHMS.CELLULAR,
    config: {
      initialDensity: 0.45,
      iterations: 5,
      birthLimit: 4,
      deathLimit: 3
    }
  },
  maze: {
    name: 'Maze',
    algorithm: ALGORITHMS.MAZE,
    config: {
      wallThickness: 1
    }
  }
}

// Tileset (matching MapEditor)
const TILESET = [
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

export default function MapMaker() {
  // Map configuration
  const [mapWidth, setMapWidth] = useState(64)
  const [mapHeight, setMapHeight] = useState(48)
  const [seed, setSeed] = useState(Math.floor(Math.random() * 1000000))

  // Generation settings
  const [algorithm, setAlgorithm] = useState(ALGORITHMS.PERLIN)
  const [config, setConfig] = useState(PRESETS.terrain.config)

  // Generated map data
  const [mapData, setMapData] = useState([])
  const [isGenerating, setIsGenerating] = useState(false)

  // UI state
  const [showConfig, setShowConfig] = useState(true)
  const [zoom, setZoom] = useState(1.0)

  const canvasRef = useRef(null)

  // Simple hash function for seeded random
  const seededRandom = (seed, x, y) => {
    const hash = Math.sin(seed + x * 12.9898 + y * 78.233) * 43758.5453123
    return hash - Math.floor(hash)
  }

  // Perlin-like noise (simplified)
  const generatePerlinNoise = (width, height, seed, config) => {
    const { scale, octaves, persistence, lacunarity } = config
    const map = Array(height).fill(null).map(() => Array(width).fill(0))

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        let value = 0
        let amplitude = 1
        let frequency = scale

        for (let octave = 0; octave < octaves; octave++) {
          const sampleX = x * frequency
          const sampleY = y * frequency
          const noise = seededRandom(seed + octave, Math.floor(sampleX), Math.floor(sampleY))
          value += noise * amplitude

          amplitude *= persistence
          frequency *= lacunarity
        }

        // Normalize to 0-1
        value = Math.max(0, Math.min(1, value / 2))

        // Map to biome
        let tileId = 0
        for (const biome of Object.values(BIOMES)) {
          if (value <= biome.threshold) {
            tileId = biome.id
            break
          }
        }

        map[y][x] = tileId
      }
    }

    return map
  }

  // Cellular automata (cave generation)
  const generateCellularAutomata = (width, height, seed, config) => {
    const { initialDensity, iterations, birthLimit, deathLimit } = config
    let map = Array(height).fill(null).map(() => Array(width).fill(0))

    // Initialize with random walls
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        map[y][x] = seededRandom(seed, x, y) < initialDensity ? 5 : 0 // 5 = wall
      }
    }

    // Run cellular automata iterations
    for (let i = 0; i < iterations; i++) {
      const newMap = map.map(row => [...row])

      for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
          // Count alive neighbors
          let aliveNeighbors = 0
          for (let dy = -1; dy <= 1; dy++) {
            for (let dx = -1; dx <= 1; dx++) {
              if (dx === 0 && dy === 0) continue
              if (map[y + dy][x + dx] === 5) aliveNeighbors++
            }
          }

          // Apply rules
          if (map[y][x] === 5) {
            newMap[y][x] = aliveNeighbors < deathLimit ? 0 : 5
          } else {
            newMap[y][x] = aliveNeighbors > birthLimit ? 5 : 0
          }
        }
      }

      map = newMap
    }

    return map
  }

  // BSP (Binary Space Partitioning) for dungeons
  const generateBSP = (width, height, seed, config) => {
    const { minRoomSize, maxRoomSize, corridorWidth } = config
    const map = Array(height).fill(null).map(() => Array(width).fill(5)) // Fill with walls

    const rooms = []

    // Simple BSP implementation
    const splitRegion = (x, y, w, h, depth = 0) => {
      if (depth > 4 || w < minRoomSize * 2 || h < minRoomSize * 2) {
        // Create room
        const roomW = Math.floor(seededRandom(seed, x, y) * (maxRoomSize - minRoomSize) + minRoomSize)
        const roomH = Math.floor(seededRandom(seed, y, x) * (maxRoomSize - minRoomSize) + minRoomSize)
        const roomX = x + Math.floor(seededRandom(seed, x + 100, y) * (w - roomW))
        const roomY = y + Math.floor(seededRandom(seed, x, y + 100) * (h - roomH))

        rooms.push({ x: roomX, y: roomY, w: roomW, h: roomH })

        // Carve room
        for (let ry = roomY; ry < roomY + roomH && ry < height; ry++) {
          for (let rx = roomX; rx < roomX + roomW && rx < width; rx++) {
            map[ry][rx] = 1 // 1 = ground
          }
        }
        return
      }

      // Split horizontally or vertically
      if (seededRandom(seed, x, y) > 0.5) {
        const splitX = x + Math.floor(w / 2)
        splitRegion(x, y, splitX - x, h, depth + 1)
        splitRegion(splitX, y, w - (splitX - x), h, depth + 1)
      } else {
        const splitY = y + Math.floor(h / 2)
        splitRegion(x, y, w, splitY - y, depth + 1)
        splitRegion(x, splitY, w, h - (splitY - y), depth + 1)
      }
    }

    splitRegion(0, 0, width, height)

    // Connect rooms with corridors
    for (let i = 0; i < rooms.length - 1; i++) {
      const room1 = rooms[i]
      const room2 = rooms[i + 1]
      const cx1 = Math.floor(room1.x + room1.w / 2)
      const cy1 = Math.floor(room1.y + room1.h / 2)
      const cx2 = Math.floor(room2.x + room2.w / 2)
      const cy2 = Math.floor(room2.y + room2.h / 2)

      // Horizontal corridor
      for (let x = Math.min(cx1, cx2); x <= Math.max(cx1, cx2) && x < width; x++) {
        for (let w = 0; w < corridorWidth && cy1 + w < height; w++) {
          map[cy1 + w][x] = 1
        }
      }

      // Vertical corridor
      for (let y = Math.min(cy1, cy2); y <= Math.max(cy1, cy2) && y < height; y++) {
        for (let w = 0; w < corridorWidth && cx2 + w < width; w++) {
          map[y][cx2 + w] = 1
        }
      }
    }

    return map
  }

  // Drunkard's walk
  const generateDrunkardWalk = (width, height, seed) => {
    const map = Array(height).fill(null).map(() => Array(width).fill(5)) // Fill with walls
    const targetFloors = Math.floor(width * height * 0.4) // 40% floor coverage

    let x = Math.floor(width / 2)
    let y = Math.floor(height / 2)
    let floorsCarved = 0

    while (floorsCarved < targetFloors) {
      // Carve floor
      if (x >= 0 && x < width && y >= 0 && y < height) {
        if (map[y][x] === 5) {
          map[y][x] = 1
          floorsCarved++
        }
      }

      // Random walk
      const dir = Math.floor(seededRandom(seed, x, y + floorsCarved) * 4)
      if (dir === 0) x++
      else if (dir === 1) x--
      else if (dir === 2) y++
      else y--

      // Clamp to bounds
      x = Math.max(1, Math.min(width - 2, x))
      y = Math.max(1, Math.min(height - 2, y))
    }

    return map
  }

  // Maze generation (recursive backtracking)
  const generateMaze = (width, height, seed) => {
    // Ensure odd dimensions for maze
    const w = width % 2 === 0 ? width - 1 : width
    const h = height % 2 === 0 ? height - 1 : height
    const map = Array(h).fill(null).map(() => Array(w).fill(5)) // Fill with walls

    const stack = []
    const visited = new Set()
    const startX = 1
    const startY = 1

    stack.push([startX, startY])
    visited.add(`${startX},${startY}`)
    map[startY][startX] = 1

    const directions = [[0, -2], [2, 0], [0, 2], [-2, 0]]

    while (stack.length > 0) {
      const [cx, cy] = stack[stack.length - 1]

      // Shuffle directions using seed
      const shuffled = [...directions].sort(() =>
        seededRandom(seed, cx + stack.length, cy) - 0.5
      )

      let moved = false
      for (const [dx, dy] of shuffled) {
        const nx = cx + dx
        const ny = cy + dy

        if (nx >= 1 && nx < w - 1 && ny >= 1 && ny < h - 1 && !visited.has(`${nx},${ny}`)) {
          // Carve path
          map[cy + dy / 2][cx + dx / 2] = 1
          map[ny][nx] = 1

          visited.add(`${nx},${ny}`)
          stack.push([nx, ny])
          moved = true
          break
        }
      }

      if (!moved) {
        stack.pop()
      }
    }

    return map
  }

  // Generate map based on algorithm
  const generateMap = () => {
    setIsGenerating(true)

    setTimeout(() => {
      let newMap

      switch (algorithm) {
        case ALGORITHMS.PERLIN:
          newMap = generatePerlinNoise(mapWidth, mapHeight, seed, config)
          break
        case ALGORITHMS.CELLULAR:
          newMap = generateCellularAutomata(mapWidth, mapHeight, seed, config)
          break
        case ALGORITHMS.BSP:
          newMap = generateBSP(mapWidth, mapHeight, seed, config)
          break
        case ALGORITHMS.DRUNKARD:
          newMap = generateDrunkardWalk(mapWidth, mapHeight, seed)
          break
        case ALGORITHMS.MAZE:
          newMap = generateMaze(mapWidth, mapHeight, seed)
          break
        default:
          newMap = Array(mapHeight).fill(null).map(() => Array(mapWidth).fill(0))
      }

      setMapData(newMap)
      setIsGenerating(false)
    }, 100)
  }

  // Auto-generate on mount and when settings change
  useEffect(() => {
    generateMap()
  }, [seed, algorithm, mapWidth, mapHeight])

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || mapData.length === 0) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const tileSize = 12

    // Clear canvas
    ctx.fillStyle = '#1a1a1a'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    ctx.save()
    ctx.scale(zoom, zoom)

    // Draw map
    mapData.forEach((row, y) => {
      row.forEach((tileId, x) => {
        const tile = TILESET.find(t => t.id === tileId)
        if (!tile) return

        ctx.fillStyle = tile.color
        ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize)
      })
    })

    ctx.restore()
  }, [mapData, zoom])

  // Apply preset
  const applyPreset = (presetKey) => {
    const preset = PRESETS[presetKey]
    setAlgorithm(preset.algorithm)
    setConfig(preset.config)
  }

  // Export to Map Editor format
  const exportToMapEditor = () => {
    const exportData = {
      name: `Generated Map (${algorithm})`,
      width: mapWidth,
      height: mapHeight,
      tileSize: 32,
      tileset: TILESET,
      layers: [
        {
          id: 'layer_generated',
          name: 'Generated Layer',
          type: 'background',
          visible: true,
          locked: false,
          data: mapData
        }
      ]
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `generated_map_${seed}.map.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Random seed
  const randomizeSeed = () => {
    setSeed(Math.floor(Math.random() * 1000000))
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Toolbar */}
      <div className="h-12 bg-surface border-b border-border flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Wand2 className="w-5 h-5 text-accent" />
          <span className="text-sm font-medium text-text">Map Maker</span>
          <span className="text-xs text-textMuted px-2 py-1 bg-background rounded">
            {mapWidth} × {mapHeight}
          </span>
          <span className="text-xs text-textMuted px-2 py-1 bg-background rounded">
            Seed: {seed}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={randomizeSeed}
            className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1"
            title="Random seed"
          >
            <Shuffle className="w-4 h-4" />
            New Seed
          </button>

          <button
            onClick={generateMap}
            disabled={isGenerating}
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
            title="Regenerate map"
          >
            <RefreshCw className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
            Generate
          </button>

          <button
            onClick={() => navigator.clipboard.writeText(seed.toString())}
            className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1"
            title="Copy seed"
          >
            <Copy className="w-4 h-4" />
          </button>

          <div className="h-6 w-px bg-border" />

          <button
            onClick={exportToMapEditor}
            className="px-3 py-1.5 bg-accent text-white rounded text-sm hover:bg-accent/90 flex items-center gap-1"
            title="Export to Map Editor"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Configuration */}
        <div className="w-80 bg-surface border-r border-border overflow-y-auto flex-shrink-0">
          <div className="p-4 space-y-6">
            {/* Presets */}
            <div>
              <h3 className="text-sm font-semibold text-text mb-3">Presets</h3>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(PRESETS).map(([key, preset]) => (
                  <button
                    key={key}
                    onClick={() => applyPreset(key)}
                    className="p-2 bg-background border border-border rounded text-sm text-text hover:border-accent transition-colors"
                  >
                    {preset.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Map Settings */}
            <div>
              <h3 className="text-sm font-semibold text-text mb-3">Map Settings</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Width
                  </label>
                  <input
                    type="number"
                    value={mapWidth}
                    onChange={(e) => setMapWidth(parseInt(e.target.value) || 32)}
                    min="16"
                    max="128"
                    className="w-full p-2 bg-background border border-border rounded text-sm text-text"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Height
                  </label>
                  <input
                    type="number"
                    value={mapHeight}
                    onChange={(e) => setMapHeight(parseInt(e.target.value) || 24)}
                    min="16"
                    max="128"
                    className="w-full p-2 bg-background border border-border rounded text-sm text-text"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-textMuted mb-1">
                    Seed
                  </label>
                  <input
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(parseInt(e.target.value) || 0)}
                    className="w-full p-2 bg-background border border-border rounded text-sm text-text font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Algorithm */}
            <div>
              <h3 className="text-sm font-semibold text-text mb-3">Algorithm</h3>
              <select
                value={algorithm}
                onChange={(e) => setAlgorithm(e.target.value)}
                className="w-full p-2 bg-background border border-border rounded text-sm text-text"
              >
                <option value={ALGORITHMS.PERLIN}>Perlin Noise (Terrain)</option>
                <option value={ALGORITHMS.CELLULAR}>Cellular Automata (Caves)</option>
                <option value={ALGORITHMS.BSP}>BSP (Dungeon Rooms)</option>
                <option value={ALGORITHMS.DRUNKARD}>Drunkard's Walk (Caves)</option>
                <option value={ALGORITHMS.MAZE}>Maze (Recursive Backtracking)</option>
              </select>
            </div>

            {/* Algorithm-specific config */}
            {algorithm === ALGORITHMS.PERLIN && (
              <div>
                <h3 className="text-sm font-semibold text-text mb-3">Perlin Settings</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-textMuted mb-1">
                      Scale: {config.scale?.toFixed(3)}
                    </label>
                    <input
                      type="range"
                      min="0.01"
                      max="0.2"
                      step="0.01"
                      value={config.scale || 0.05}
                      onChange={(e) => setConfig({ ...config, scale: parseFloat(e.target.value) })}
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-textMuted mb-1">
                      Octaves: {config.octaves}
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="8"
                      step="1"
                      value={config.octaves || 4}
                      onChange={(e) => setConfig({ ...config, octaves: parseInt(e.target.value) })}
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-textMuted mb-1">
                      Persistence: {config.persistence?.toFixed(2)}
                    </label>
                    <input
                      type="range"
                      min="0.1"
                      max="0.9"
                      step="0.1"
                      value={config.persistence || 0.5}
                      onChange={(e) => setConfig({ ...config, persistence: parseFloat(e.target.value) })}
                      className="w-full"
                    />
                  </div>
                </div>
              </div>
            )}

            {algorithm === ALGORITHMS.CELLULAR && (
              <div>
                <h3 className="text-sm font-semibold text-text mb-3">Cellular Automata</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-textMuted mb-1">
                      Initial Density: {config.initialDensity?.toFixed(2)}
                    </label>
                    <input
                      type="range"
                      min="0.3"
                      max="0.6"
                      step="0.05"
                      value={config.initialDensity || 0.45}
                      onChange={(e) => setConfig({ ...config, initialDensity: parseFloat(e.target.value) })}
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-textMuted mb-1">
                      Iterations: {config.iterations}
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      step="1"
                      value={config.iterations || 5}
                      onChange={(e) => setConfig({ ...config, iterations: parseInt(e.target.value) })}
                      className="w-full"
                    />
                  </div>
                </div>
              </div>
            )}

            {algorithm === ALGORITHMS.BSP && (
              <div>
                <h3 className="text-sm font-semibold text-text mb-3">BSP Settings</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-textMuted mb-1">
                      Min Room Size: {config.minRoomSize}
                    </label>
                    <input
                      type="range"
                      min="3"
                      max="8"
                      step="1"
                      value={config.minRoomSize || 4}
                      onChange={(e) => setConfig({ ...config, minRoomSize: parseInt(e.target.value) })}
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-textMuted mb-1">
                      Max Room Size: {config.maxRoomSize}
                    </label>
                    <input
                      type="range"
                      min="6"
                      max="16"
                      step="1"
                      value={config.maxRoomSize || 10}
                      onChange={(e) => setConfig({ ...config, maxRoomSize: parseInt(e.target.value) })}
                      className="w-full"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Center - Preview Canvas */}
        <div className="flex-1 overflow-hidden bg-background flex items-center justify-center p-8">
          <canvas
            ref={canvasRef}
            width={1200}
            height={800}
            className="border border-border rounded shadow-lg"
          />
        </div>
      </div>
    </div>
  )
}
