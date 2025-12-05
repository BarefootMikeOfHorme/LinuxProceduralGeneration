import { useState } from 'react'
import { useWorkflowStore } from '../store/workflowStore'
import { X, CheckCircle, XCircle, Image as ImageIcon, Video, Cube, Copy, Download, Info } from 'lucide-react'

export default function OutputModal() {
  const { showResultsModal, executionResults, closeResults } = useWorkflowStore()
  const [activeTab, setActiveTab] = useState('outputs')
  const [copiedPath, setCopiedPath] = useState(null)

  if (!showResultsModal || !executionResults) return null

  const hasError = executionResults.error
  const previews = executionResults.previews || {}
  const executionOrder = executionResults.execution_order || []
  const nodesExecuted = executionResults.nodes_executed || 0

  const handleCopyPath = (path) => {
    navigator.clipboard.writeText(path)
    setCopiedPath(path)
    setTimeout(() => setCopiedPath(null), 2000)
  }

  const handleDownload = (path) => {
    // Create download link
    const link = document.createElement('a')
    link.href = path
    link.download = path.split('/').pop() || path.split('\\').pop()
    link.click()
  }

  const renderPreview = (nodeId, handleName, previewData) => {
    if (previewData.type === 'image' && previewData.thumbnail) {
      return (
        <div className="flex flex-col gap-2">
          <img
            src={previewData.thumbnail}
            alt={handleName}
            className="w-full max-w-md rounded border border-border"
          />
          <div className="flex gap-2">
            {previewData.path && (
              <>
                <button
                  onClick={() => handleCopyPath(previewData.path)}
                  className="flex items-center gap-1 px-3 py-1 text-xs bg-background border border-border rounded hover:bg-accent/10 hover:border-accent"
                >
                  {copiedPath === previewData.path ? (
                    <>
                      <CheckCircle className="w-3 h-3 text-green-500" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      Copy Path
                    </>
                  )}
                </button>
                <button
                  onClick={() => handleDownload(previewData.path)}
                  className="flex items-center gap-1 px-3 py-1 text-xs bg-background border border-border rounded hover:bg-accent/10 hover:border-accent"
                >
                  <Download className="w-3 h-3" />
                  Download
                </button>
              </>
            )}
          </div>
        </div>
      )
    }

    if (previewData.type === 'video' && previewData.path) {
      return (
        <div className="flex items-center gap-3 p-4 bg-purple-500/10 border border-purple-500/30 rounded">
          <Video className="w-8 h-8 text-purple-400" />
          <div className="flex-1">
            <div className="text-sm font-medium">Video Output</div>
            <div className="text-xs text-textMuted truncate">{previewData.path}</div>
          </div>
          <button
            onClick={() => handleCopyPath(previewData.path)}
            className="px-3 py-1 text-xs bg-background border border-border rounded hover:bg-accent/10"
          >
            <Copy className="w-3 h-3" />
          </button>
        </div>
      )
    }

    if (previewData.type === 'mesh' && previewData.path) {
      return (
        <div className="flex items-center gap-3 p-4 bg-blue-500/10 border border-blue-500/30 rounded">
          <Cube className="w-8 h-8 text-blue-400" />
          <div className="flex-1">
            <div className="text-sm font-medium">3D Mesh Output</div>
            <div className="text-xs text-textMuted truncate">{previewData.path}</div>
          </div>
          <button
            onClick={() => handleCopyPath(previewData.path)}
            className="px-3 py-1 text-xs bg-background border border-border rounded hover:bg-accent/10"
          >
            <Copy className="w-3 h-3" />
          </button>
        </div>
      )
    }

    if (previewData.type === 'text' && previewData.text) {
      return (
        <div className="p-3 bg-background/50 rounded border border-border font-mono text-sm">
          {previewData.text}
        </div>
      )
    }

    if (previewData.type === 'number' && previewData.value !== undefined) {
      return (
        <div className="p-3 bg-background/50 rounded border border-border text-center font-bold text-lg">
          {previewData.value}
        </div>
      )
    }

    return null
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-surface border-2 border-border rounded-lg w-[900px] max-h-[80vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-3">
            {hasError ? (
              <>
                <XCircle className="w-6 h-6 text-red-500" />
                <h2 className="font-semibold text-lg">Execution Failed</h2>
              </>
            ) : (
              <>
                <CheckCircle className="w-6 h-6 text-green-500" />
                <h2 className="font-semibold text-lg">Execution Complete</h2>
              </>
            )}
          </div>
          <button
            onClick={closeResults}
            className="p-1 hover:bg-background rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        {!hasError && (
          <div className="flex gap-4 px-4 pt-3 border-b border-border">
            <button
              onClick={() => setActiveTab('outputs')}
              className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'outputs'
                  ? 'border-accent text-accent'
                  : 'border-transparent text-textMuted hover:text-text'
              }`}
            >
              Outputs
            </button>
            <button
              onClick={() => setActiveTab('details')}
              className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'details'
                  ? 'border-accent text-accent'
                  : 'border-transparent text-textMuted hover:text-text'
              }`}
            >
              Details
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {hasError ? (
            <div className="flex flex-col items-center justify-center h-full gap-4">
              <XCircle className="w-16 h-16 text-red-500" />
              <div className="text-center">
                <div className="font-semibold text-lg mb-2">Workflow Execution Failed</div>
                <div className="text-sm text-textMuted max-w-md">
                  {executionResults.error || 'Unknown error occurred'}
                </div>
              </div>
            </div>
          ) : activeTab === 'outputs' ? (
            <div className="space-y-6">
              {Object.keys(previews).length === 0 ? (
                <div className="text-center text-textMuted py-8">
                  No visual outputs to display
                </div>
              ) : (
                Object.entries(previews).map(([nodeId, nodeOutputs]) => (
                  <div key={nodeId} className="border border-border rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Info className="w-4 h-4 text-accent" />
                      <div className="font-medium text-sm">{nodeId}</div>
                    </div>
                    <div className="space-y-4">
                      {Object.entries(nodeOutputs).map(([handle, previewData]) => (
                        <div key={handle}>
                          <div className="text-xs text-textMuted mb-2 uppercase tracking-wide">
                            {handle}
                          </div>
                          {renderPreview(nodeId, handle, previewData)}
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Execution Order */}
              <div>
                <h3 className="font-semibold mb-2">Execution Order</h3>
                <div className="flex flex-wrap gap-2">
                  {executionOrder.map((nodeId, idx) => (
                    <div
                      key={idx}
                      className="px-3 py-1 bg-accent/10 border border-accent/30 rounded-full text-sm"
                    >
                      <span className="font-bold text-accent">{idx + 1}.</span> {nodeId}
                    </div>
                  ))}
                </div>
              </div>

              {/* Statistics */}
              <div>
                <h3 className="font-semibold mb-2">Statistics</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-background/50 rounded border border-border">
                    <div className="text-2xl font-bold text-accent">{nodesExecuted}</div>
                    <div className="text-xs text-textMuted">Nodes Executed</div>
                  </div>
                  <div className="p-3 bg-background/50 rounded border border-border">
                    <div className="text-2xl font-bold text-accent">{Object.keys(previews).length}</div>
                    <div className="text-xs text-textMuted">Outputs Generated</div>
                  </div>
                </div>
              </div>

              {/* Message */}
              {executionResults.message && (
                <div>
                  <h3 className="font-semibold mb-2">Status</h3>
                  <div className="p-3 bg-green-500/10 border border-green-500/30 rounded text-sm">
                    {executionResults.message}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-border flex justify-end">
          <button
            onClick={closeResults}
            className="px-4 py-2 bg-accent text-white rounded hover:bg-accent/90 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
