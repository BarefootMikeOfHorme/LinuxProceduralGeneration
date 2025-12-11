/**
 * VaultMind Forge - Parameter Sweep Editor
 *
 * Grid-based parameter exploration with:
 * - Multi-dimensional parameter grids (W&B/TensorBoard pattern)
 * - Range definitions (linear, log, custom)
 * - Parallel coordinates visualization
 * - Heatmap view for 2D parameter spaces
 * - Best result highlighting
 * - Resume interrupted sweeps
 */

import { useState, useEffect } from 'react'
import { useEditorStore } from '../../store/editorStore'
import {
  TrendingUp,
  Play,
  Pause,
  RotateCcw,
  Plus,
  Trash2,
  Grid3x3,
  BarChart3,
  Download,
  Star,
  Settings,
  Info
} from 'lucide-react'

// Range type definitions
const RANGE_TYPES = {
  LINEAR: 'linear',
  LOGARITHMIC: 'logarithmic',
  CUSTOM: 'custom'
}

export default function ParameterSweep() {
  const {
    parameterSweep,
    setParameterSweepState,
    activeEditorId,
    markEditorModified
  } = useEditorStore()

  const {
    axes,
    combinations,
    results,
    status,
    currentIndex,
    bestResult
  } = parameterSweep

  const [viewMode, setViewMode] = useState('grid') // 'grid' | 'heatmap' | 'parallel'
  const [selectedAxis, setSelectedAxis] = useState(null)

  // Mark as modified when axes change
  useEffect(() => {
    if (axes.length > 0) {
      markEditorModified(activeEditorId, true)
    }
  }, [axes, activeEditorId])

  // Generate combinations when axes change
  useEffect(() => {
    if (axes.length > 0) {
      const combos = generateCombinations(axes)
      setParameterSweepState({ combinations: combos })
    }
  }, [axes])

  const generateCombinations = (paramAxes) => {
    if (paramAxes.length === 0) return []

    // Generate all combinations of parameter values
    const combinations = []

    const generate = (index, current) => {
      if (index === paramAxes.length) {
        combinations.push({ ...current })
        return
      }

      const axis = paramAxes[index]
      axis.values.forEach(value => {
        generate(index + 1, { ...current, [axis.name]: value })
      })
    }

    generate(0, {})
    return combinations.map((combo, idx) => ({
      id: idx,
      parameters: combo,
      status: 'pending',
      result: null
    }))
  }

  const generateRangeValues = (min, max, step, rangeType) => {
    const values = []

    if (rangeType === RANGE_TYPES.LINEAR) {
      for (let i = min; i <= max; i += step) {
        values.push(parseFloat(i.toFixed(4)))
      }
    } else if (rangeType === RANGE_TYPES.LOGARITHMIC) {
      const logMin = Math.log10(min)
      const logMax = Math.log10(max)
      const logStep = (logMax - logMin) / step
      for (let i = 0; i <= step; i++) {
        values.push(parseFloat(Math.pow(10, logMin + i * logStep).toFixed(4)))
      }
    }

    return values
  }

  const addAxis = () => {
    const name = prompt('Parameter name:')
    if (!name) return

    const newAxis = {
      id: Date.now(),
      name: name.trim(),
      min: 0,
      max: 1,
      step: 0.1,
      rangeType: RANGE_TYPES.LINEAR,
      values: [0, 0.5, 1]
    }

    setParameterSweepState({
      axes: [...axes, newAxis]
    })
  }

  const removeAxis = (axisId) => {
    setParameterSweepState({
      axes: axes.filter(a => a.id !== axisId)
    })
  }

  const updateAxis = (axisId, updates) => {
    setParameterSweepState({
      axes: axes.map(axis => {
        if (axis.id !== axisId) return axis

        const updated = { ...axis, ...updates }

        // Regenerate values if range params changed
        if ('min' in updates || 'max' in updates || 'step' in updates || 'rangeType' in updates) {
          updated.values = generateRangeValues(
            updated.min,
            updated.max,
            updated.step,
            updated.rangeType
          )
        }

        return updated
      })
    })
  }

  const startSweep = () => {
    if (combinations.length === 0) {
      alert('Please add at least one parameter axis')
      return
    }

    setParameterSweepState({
      status: 'running',
      currentIndex: 0
    })

    // TODO: Integrate with workflow execution engine
    // For now, simulate sweep
    simulateSweep()
  }

  const pauseSweep = () => {
    setParameterSweepState({ status: 'paused' })
  }

  const resetSweep = () => {
    if (!confirm('Reset all results?')) return

    setParameterSweepState({
      status: 'idle',
      currentIndex: 0,
      results: [],
      bestResult: null,
      combinations: combinations.map(c => ({ ...c, status: 'pending', result: null }))
    })
  }

  const simulateSweep = () => {
    // Simulate running sweep (replace with actual workflow execution)
    let index = currentIndex

    const interval = setInterval(() => {
      const state = useEditorStore.getState().parameterSweep

      if (state.status !== 'running' || index >= combinations.length) {
        clearInterval(interval)
        setParameterSweepState({ status: 'completed' })
        return
      }

      // Simulate result (random score)
      const score = Math.random()
      const result = {
        combinationId: combinations[index].id,
        score: score,
        metrics: {
          accuracy: score,
          loss: 1 - score
        }
      }

      const newResults = [...state.results, result]
      const newBest = !state.bestResult || score > state.bestResult.score
        ? result
        : state.bestResult

      setParameterSweepState({
        results: newResults,
        currentIndex: index + 1,
        bestResult: newBest,
        combinations: state.combinations.map(c =>
          c.id === combinations[index].id
            ? { ...c, status: 'completed', result }
            : c
        )
      })

      index++
    }, 500) // Simulate 500ms per combination
  }

  const exportResults = () => {
    const csv = [
      // Header
      [...axes.map(a => a.name), 'score'].join(','),
      // Results
      ...results.map(r => {
        const combo = combinations.find(c => c.id === r.combinationId)
        const values = axes.map(a => combo.parameters[a.name])
        return [...values, r.score].join(',')
      })
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'sweep_results.csv'
    a.click()
  }

  const renderAxisEditor = (axis) => (
    <div key={axis.id} className="p-4 bg-surface border border-border rounded">
      <div className="flex items-center justify-between mb-3">
        <div className="font-medium text-text">{axis.name}</div>
        <button
          onClick={() => removeAxis(axis.id)}
          className="p-1 text-red-500 hover:bg-red-500/10 rounded"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-textMuted mb-1">Min</label>
          <input
            type="number"
            value={axis.min}
            onChange={(e) => updateAxis(axis.id, { min: parseFloat(e.target.value) })}
            className="w-full p-2 bg-background border border-border rounded text-sm"
            step="0.1"
          />
        </div>
        <div>
          <label className="block text-xs text-textMuted mb-1">Max</label>
          <input
            type="number"
            value={axis.max}
            onChange={(e) => updateAxis(axis.id, { max: parseFloat(e.target.value) })}
            className="w-full p-2 bg-background border border-border rounded text-sm"
            step="0.1"
          />
        </div>
        <div>
          <label className="block text-xs text-textMuted mb-1">Step</label>
          <input
            type="number"
            value={axis.step}
            onChange={(e) => updateAxis(axis.id, { step: parseFloat(e.target.value) })}
            className="w-full p-2 bg-background border border-border rounded text-sm"
            step="0.01"
          />
        </div>
        <div>
          <label className="block text-xs text-textMuted mb-1">Range Type</label>
          <select
            value={axis.rangeType}
            onChange={(e) => updateAxis(axis.id, { rangeType: e.target.value })}
            className="w-full p-2 bg-background border border-border rounded text-sm"
          >
            <option value={RANGE_TYPES.LINEAR}>Linear</option>
            <option value={RANGE_TYPES.LOGARITHMIC}>Logarithmic</option>
          </select>
        </div>
      </div>

      <div className="mt-2 text-xs text-textMuted">
        {axis.values.length} values: [{axis.values.slice(0, 3).join(', ')}
        {axis.values.length > 3 ? '...' : ''}]
      </div>
    </div>
  )

  const renderGridView = () => (
    <div className="space-y-2">
      {combinations.map(combo => {
        const result = results.find(r => r.combinationId === combo.id)
        const isBest = bestResult?.combinationId === combo.id

        return (
          <div
            key={combo.id}
            className={`p-3 rounded flex items-center justify-between ${
              isBest
                ? 'bg-accent/10 border-2 border-accent'
                : 'bg-surface border border-border'
            }`}
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 text-sm">
                {Object.entries(combo.parameters).map(([key, value]) => (
                  <span key={key} className="text-text">
                    <span className="text-textMuted">{key}:</span> {value}
                  </span>
                ))}
                {isBest && <Star className="w-4 h-4 text-accent fill-accent" />}
              </div>
            </div>
            <div className="flex items-center gap-3">
              {result && (
                <div className="text-sm">
                  <span className="text-textMuted">Score:</span>{' '}
                  <span className="font-bold text-accent">{result.score.toFixed(4)}</span>
                </div>
              )}
              <div
                className={`px-2 py-1 rounded text-xs ${
                  combo.status === 'completed'
                    ? 'bg-green-500/20 text-green-500'
                    : combo.status === 'running'
                    ? 'bg-blue-500/20 text-blue-500'
                    : 'bg-gray-500/20 text-gray-500'
                }`}
              >
                {combo.status}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )

  const renderHeatmapView = () => {
    if (axes.length !== 2) {
      return (
        <div className="flex items-center justify-center h-64 text-textMuted">
          Heatmap requires exactly 2 parameter axes
        </div>
      )
    }

    // Create 2D heatmap grid
    const xAxis = axes[0]
    const yAxis = axes[1]

    return (
      <div className="p-4">
        <div className="mb-4 text-sm text-textMuted">
          Heatmap: {xAxis.name} (X) vs {yAxis.name} (Y)
        </div>
        <div className="overflow-auto">
          <table className="border-collapse">
            <thead>
              <tr>
                <th className="p-2 border border-border bg-surface"></th>
                {xAxis.values.map(xVal => (
                  <th key={xVal} className="p-2 border border-border bg-surface text-xs">
                    {xVal.toFixed(2)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {yAxis.values.map(yVal => (
                <tr key={yVal}>
                  <td className="p-2 border border-border bg-surface text-xs font-medium">
                    {yVal.toFixed(2)}
                  </td>
                  {xAxis.values.map(xVal => {
                    const combo = combinations.find(
                      c =>
                        c.parameters[xAxis.name] === xVal &&
                        c.parameters[yAxis.name] === yVal
                    )
                    const result = combo ? results.find(r => r.combinationId === combo.id) : null
                    const score = result?.score || 0

                    return (
                      <td
                        key={`${xVal}-${yVal}`}
                        className="p-2 border border-border w-16 h-16"
                        style={{
                          backgroundColor: result
                            ? `rgba(59, 130, 246, ${score})`
                            : 'transparent'
                        }}
                      >
                        {result && (
                          <div className="text-xs text-center text-white font-medium">
                            {score.toFixed(2)}
                          </div>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Toolbar */}
      <div className="h-12 bg-surface border-b border-border flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-accent" />
          <span className="text-sm font-medium text-text">Parameter Sweep</span>
          <div className="ml-4 px-2 py-1 bg-background rounded border border-border">
            <span className="text-xs text-textMuted">
              {combinations.length} combinations
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {status === 'idle' && (
            <button
              onClick={startSweep}
              disabled={combinations.length === 0}
              className="px-3 py-1.5 bg-accent text-white rounded text-sm hover:bg-accent/90 flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-4 h-4" />
              Start Sweep
            </button>
          )}
          {status === 'running' && (
            <button
              onClick={pauseSweep}
              className="px-3 py-1.5 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600 flex items-center gap-1"
            >
              <Pause className="w-4 h-4" />
              Pause
            </button>
          )}
          {status === 'paused' && (
            <button
              onClick={startSweep}
              className="px-3 py-1.5 bg-accent text-white rounded text-sm hover:bg-accent/90 flex items-center gap-1"
            >
              <Play className="w-4 h-4" />
              Resume
            </button>
          )}
          {results.length > 0 && (
            <>
              <button
                onClick={resetSweep}
                className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1"
              >
                <RotateCcw className="w-4 h-4" />
                Reset
              </button>
              <button
                onClick={exportResults}
                className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
            </>
          )}
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left panel - Axis configuration */}
        <div className="w-96 bg-surface border-r border-border overflow-auto flex-shrink-0">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-text">Parameter Axes</h3>
              <button
                onClick={addAxis}
                className="px-2 py-1 bg-accent text-white rounded text-xs hover:bg-accent/90 flex items-center gap-1"
              >
                <Plus className="w-3 h-3" />
                Add Axis
              </button>
            </div>

            {axes.length === 0 ? (
              <div className="text-center text-textMuted py-8">
                <Settings className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No parameter axes defined</p>
                <p className="text-xs mt-1">Click "Add Axis" to get started</p>
              </div>
            ) : (
              <div className="space-y-3">{axes.map(renderAxisEditor)}</div>
            )}
          </div>
        </div>

        {/* Right panel - Results */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* View mode selector */}
          <div className="h-12 bg-surface border-b border-border flex items-center px-4 gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1.5 rounded text-sm flex items-center gap-1 ${
                viewMode === 'grid'
                  ? 'bg-accent text-white'
                  : 'bg-background text-text hover:bg-border'
              }`}
            >
              <Grid3x3 className="w-4 h-4" />
              Grid
            </button>
            <button
              onClick={() => setViewMode('heatmap')}
              className={`px-3 py-1.5 rounded text-sm flex items-center gap-1 ${
                viewMode === 'heatmap'
                  ? 'bg-accent text-white'
                  : 'bg-background text-text hover:bg-border'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              Heatmap
            </button>

            {status === 'running' && (
              <div className="ml-auto flex items-center gap-2 text-sm text-textMuted">
                <div className="animate-pulse">Running...</div>
                <div className="font-medium text-accent">
                  {currentIndex} / {combinations.length}
                </div>
              </div>
            )}
          </div>

          {/* Results view */}
          <div className="flex-1 overflow-auto p-4">
            {combinations.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-textMuted">
                  <TrendingUp className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg mb-2">No parameter sweep configured</p>
                  <p className="text-sm">Add parameter axes to generate combinations</p>
                </div>
              </div>
            ) : viewMode === 'grid' ? (
              renderGridView()
            ) : viewMode === 'heatmap' ? (
              renderHeatmapView()
            ) : null}
          </div>
        </div>
      </div>

      {/* Status bar */}
      {bestResult && (
        <div className="h-10 bg-accent/10 border-t border-accent flex items-center px-4 flex-shrink-0">
          <Star className="w-4 h-4 text-accent mr-2" />
          <span className="text-sm text-text">
            Best result: Score <span className="font-bold">{bestResult.score.toFixed(4)}</span>
          </span>
        </div>
      )}
    </div>
  )
}
