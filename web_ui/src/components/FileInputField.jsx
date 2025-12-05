import { FolderOpen } from 'lucide-react'
import { useWorkflowStore } from '../store/workflowStore'

export default function FileInputField({ value, onChange, placeholder = 'Select file...' }) {
  const openFileBrowser = useWorkflowStore(state => state.openFileBrowser)

  const handleBrowseClick = () => {
    openFileBrowser(null, (selectedPath) => {
      onChange(selectedPath)
    })
  }

  return (
    <div className="flex gap-2">
      <input
        type="text"
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="flex-1 px-3 py-2 bg-background border border-border rounded text-sm focus:outline-none focus:border-accent"
      />
      <button
        onClick={handleBrowseClick}
        className="px-3 py-2 bg-background border border-border rounded hover:bg-accent/10 hover:border-accent transition-colors"
        title="Browse files"
      >
        <FolderOpen className="w-4 h-4" />
      </button>
    </div>
  )
}
