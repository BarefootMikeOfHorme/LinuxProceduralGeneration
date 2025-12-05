import { create } from 'zustand'
import axios from 'axios'
import { nodeLibrary } from '../lib/nodeLibrary'

export const useWorkflowStore = create((set, get) => ({
  nodes: [],
  edges: [],
  isExecuting: false,
  executionProgress: 0,

  // Execution results
  executionResults: null,
  showResultsModal: false,

  // Node previews
  nodePreviews: {},

  // File browser
  currentBrowserPath: null,
  browserFiles: [],
  showFileBrowser: false,
  fileBrowserCallback: null,

  // Node library reference
  nodeLibrary: nodeLibrary,
  
  addNode: (node) => set((state) => ({
    nodes: [...state.nodes, node]
  })),
  
  updateNode: (nodeId, data) => set((state) => ({
    nodes: state.nodes.map((node) =>
      node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
    )
  })),
  
  deleteNode: (nodeId) => set((state) => ({
    nodes: state.nodes.filter((node) => node.id !== nodeId),
    edges: state.edges.filter(
      (edge) => edge.source !== nodeId && edge.target !== nodeId
    )
  })),
  
  addEdge: (edge) => set((state) => ({
    edges: [...state.edges, edge]
  })),
  
  saveWorkflow: async (name, description) => {
    const { nodes, edges } = get()
    const workflow = {
      version: 1,
      metadata: {
        name,
        description,
        created: new Date().toISOString(),
        author: 'user'
      },
      nodes: nodes.map((n) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        data: n.data
      })),
      connections: edges.map((e) => ({
        source: e.source,
        sourceHandle: e.sourceHandle,
        target: e.target,
        targetHandle: e.targetHandle
      }))
    }
    
    try {
      const response = await axios.post('/api/workflows', workflow)
      return response.data
    } catch (error) {
      console.error('Failed to save workflow:', error)
      throw error
    }
  },
  
  loadWorkflow: async (workflowId) => {
    try {
      const response = await axios.get('/api/workflows/' + workflowId)
      const workflow = response.data
      
      set({
        nodes: workflow.nodes,
        edges: workflow.connections
      })
      
      return workflow
    } catch (error) {
      console.error('Failed to load workflow:', error)
      throw error
    }
  },
  
  executeWorkflow: async () => {
    const { nodes, edges } = get()
    set({ isExecuting: true, executionProgress: 0, nodePreviews: {} })

    try {
      const response = await axios.post('/api/execute', {
        nodes: nodes.map((n) => ({
          id: n.id,
          type: n.type,
          data: n.data
        })),
        connections: edges
      })

      const executionId = response.data.execution_id

      const pollProgress = setInterval(async () => {
        try {
          const progressResponse = await axios.get('/api/execute/' + executionId + '/progress')
          const progress = progressResponse.data

          set({ executionProgress: progress.percentage })

          if (progress.status === 'completed') {
            clearInterval(pollProgress)
            set({
              isExecuting: false,
              executionProgress: 100,
              executionResults: progress.results,
              showResultsModal: true
            })

            // Update node previews if available
            if (progress.results && progress.results.previews) {
              set({ nodePreviews: progress.results.previews })
            }
          } else if (progress.status === 'failed') {
            clearInterval(pollProgress)
            set({
              isExecuting: false,
              executionResults: { error: progress.error },
              showResultsModal: true
            })
          }
        } catch (error) {
          clearInterval(pollProgress)
          set({ isExecuting: false })
          console.error('Failed to fetch progress:', error)
        }
      }, 1000)

    } catch (error) {
      set({ isExecuting: false })
      console.error('Failed to execute workflow:', error)
      alert('Failed to start workflow execution')
    }
  },

  // File browser actions
  openFileBrowser: (path, callback) => set({
    showFileBrowser: true,
    currentBrowserPath: path || null,
    fileBrowserCallback: callback
  }),

  closeFileBrowser: () => set({
    showFileBrowser: false,
    fileBrowserCallback: null
  }),

  browsePath: async (path) => {
    try {
      const response = await axios.get('/api/filesystem/browse', {
        params: { path }
      })
      set({
        currentBrowserPath: response.data.current_path,
        browserFiles: response.data.items
      })
    } catch (error) {
      console.error('Failed to browse path:', error)
      alert('Failed to browse directory')
    }
  },

  selectFile: (filePath) => {
    const { fileBrowserCallback, closeFileBrowser } = get()
    if (fileBrowserCallback) {
      fileBrowserCallback(filePath)
    }
    closeFileBrowser()
  },

  // Results actions
  showResults: (results) => set({
    executionResults: results,
    showResultsModal: true
  }),

  closeResults: () => set({ showResultsModal: false }),

  // Preview actions
  updateNodePreview: (nodeId, previewData) => set((state) => ({
    nodePreviews: {
      ...state.nodePreviews,
      [nodeId]: previewData
    }
  })),

  clearPreviews: () => set({ nodePreviews: {} })
}))
