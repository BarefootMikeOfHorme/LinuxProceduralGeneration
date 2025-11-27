import { useEffect } from 'react'

export default function useKeyboardShortcuts(shortcuts) {
  useEffect(() => {
    const handleKeyDown = (event) => {
      const keys = []
      
      if (event.ctrlKey || event.metaKey) keys.push('ctrl')
      if (event.shiftKey) keys.push('shift')
      if (event.altKey) keys.push('alt')
      
      keys.push(event.key.toLowerCase())
      
      const shortcut = keys.join('+')
      
      if (shortcuts[shortcut]) {
        shortcuts[shortcut](event)
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [shortcuts])
}

export const defaultShortcuts = {
  'shift+a': 'Add Node',
  'f5': 'Execute Workflow',
  'ctrl+s': 'Save Workflow',
  'ctrl+o': 'Open Workflow',
  'ctrl+a': 'Toggle AI Mode',
  'f1': 'Help',
  'delete': 'Delete Selected',
  'm': 'Mute Node',
  'ctrl+d': 'Duplicate',
  'ctrl+z': 'Undo',
  'escape': 'Deselect All',
}
