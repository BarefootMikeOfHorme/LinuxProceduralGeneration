import { useEffect, useState } from 'react'
import { useWorkflowStore } from '../store/workflowStore'
import {  Folder, Image, Video, Cube, File, Home, ArrowLeft, X, FolderOpen } from 'lucide-react'

export default function FileBrowser() {
  const {
    showFileBrowser,
    currentBrowserPath,
    browserFiles,
    closeFileBrowser,
    browsePath,
    selectFile
  } = useWorkflowStore()

  const [parentPath, setParentPath] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (showFileBrowser && !currentBrowserPath) {
      // Load home directory on open
      handleBrowse(null)
    }
  }, [showFileBrowser])

  const handleBrowse = async (path) => {
    setLoading(true)
    try {
      await browsePath(path)
      // Extract parent path from response
      const response = await fetch(`/api/filesystem/browse${path ? `?path=${encodeURIComponent(path)}` : ''}`)
      const data = await response.json()
      setParentPath(data.parent_path)
    } catch (error) {
      console.error('Browse error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleItemClick = (item) => {
    if (item.type === 'directory') {
      handleBrowse(item.path)
    }
  }

  const handleItemRightClick = (e, item) => {
    e.preventDefault()
    if (item.type !== 'directory') {
      selectFile(item.path)
    }
  }

  const getIcon = (type) => {
    switch (type) {
      case 'directory':
        return <Folder className="w-5 h-5 text-yellow-500" />
      case 'image':
        return <Image className="w-5 h-5 text-blue-500" />
      case 'video':
        return <Video className="w-5 h-5 text-purple-500" />
      case 'mesh':
        return <Cube className="w-5 h-5 text-green-500" />
      default:
        return <File className="w-5 h-5 text-gray-500" />
    }
  }

  const formatSize = (bytes) => {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  }

  if (!showFileBrowser) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-surface border-2 border-border rounded-lg w-[800px] h-[600px] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <FolderOpen className="w-5 h-5" />
            <h2 className="font-semibold">Browse Files</h2>
          </div>
          <button
            onClick={closeFileBrowser}
            className="p-1 hover:bg-background rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex items-center gap-2 p-3 border-b border-border bg-background/30">
          <button
            onClick={() => handleBrowse(null)}
            className="p-2 hover:bg-background rounded flex items-center gap-1 text-sm"
            title="Home"
          >
            <Home className="w-4 h-4" />
          </button>
          {parentPath && (
            <button
              onClick={() => handleBrowse(parentPath)}
              className="p-2 hover:bg-background rounded flex items-center gap-1 text-sm"
              title="Parent directory"
            >
              <ArrowLeft className="w-4 h-4" />
              Up
            </button>
          )}
          <div className="flex-1 text-sm text-textMuted truncate px-2">
            {currentBrowserPath || 'Home'}
          </div>
        </div>

        {/* File List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center h-full text-textMuted">
              Loading...
            </div>
          ) : browserFiles.length === 0 ? (
            <div className="flex items-center justify-center h-full text-textMuted">
              Empty directory
            </div>
          ) : (
            <div className="divide-y divide-border/30">
              {browserFiles.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-3 p-3 hover:bg-background/50 cursor-pointer group"
                  onClick={() => handleItemClick(item)}
                  onContextMenu={(e) => handleItemRightClick(e, item)}
                  title={item.type === 'directory' ? 'Click to open' : 'Right-click to select'}
                >
                  {getIcon(item.type)}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm truncate">{item.name}</div>
                    {item.size && (
                      <div className="text-xs text-textMuted">{formatSize(item.size)}</div>
                    )}
                  </div>
                  {item.type !== 'directory' && (
                    <div className="text-xs text-accent opacity-0 group-hover:opacity-100 transition-opacity">
                      Right-click to select
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-border bg-background/30 text-xs text-textMuted">
          <strong>Tip:</strong> Click folders to navigate, right-click files to select
        </div>
      </div>
    </div>
  )
}
