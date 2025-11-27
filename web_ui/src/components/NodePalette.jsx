import { useState } from 'react'
import { Search } from 'lucide-react'
import { nodeLibrary, nodeCategories } from '../lib/nodeLibrary'

export default function NodePalette() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')

  const filteredNodes = nodeLibrary.filter((node) => {
    const matchesSearch = node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         node.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || node.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div className="w-80 bg-surface border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold mb-3">Node Library</h2>
        
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-textMuted" />
          <input
            type="text"
            placeholder="Search nodes... (Shift+A)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:border-accent"
          />
        </div>

        <div className="flex flex-wrap gap-2 mt-3">
          {nodeCategories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={
                'px-3 py-1 text-xs rounded-full transition-colors ' +
                (selectedCategory === cat.id
                  ? 'bg-accent text-white'
                  : 'bg-background text-textMuted hover:bg-border')
              }
            >
              {cat.name}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {filteredNodes.map((node) => (
          <div
            key={node.type}
            draggable
            onDragStart={(e) => onDragStart(e, node.type)}
            className="p-3 bg-background border border-border rounded-lg cursor-move hover:border-accent transition-colors"
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{node.icon}</span>
              <span className="font-medium text-sm">{node.name}</span>
              {node.merlinv1Required && (
                <span className="text-xs px-1.5 py-0.5 bg-accent/20 text-accent rounded">
                  AI
                </span>
              )}
            </div>
            <p className="text-xs text-textMuted">{node.description}</p>
            <div className="text-xs text-textMuted mt-1">{node.pythonModule}</div>
          </div>
        ))}
        
        {filteredNodes.length === 0 && (
          <div className="text-center text-textMuted py-8">
            <p>No nodes found</p>
            <p className="text-xs mt-1">Try a different search or category</p>
          </div>
        )}
      </div>
    </div>
  )
}
