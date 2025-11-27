export const nodeCategories = [
  { id: 'all', name: 'All' },
  { id: 'input', name: 'Input' },
  { id: 'generation', name: 'Generation' },
  { id: 'ai_agent', name: 'AI Agent' },
  { id: 'enhancement', name: 'Enhancement' },
  { id: 'validation', name: 'Validation' },
  { id: 'processing', name: 'Processing' },
  { id: 'output', name: 'Output' },
  { id: 'utility', name: 'Utility' },
]

export const socketColors = {
  image: '#FF5555',
  text: '#55FF55',
  number: '#888888',
  video: '#FF8855',
  mesh_3d: '#5555FF',
  any: '#4A90E2',
}

export const nodeLibrary = [
  {
    type: 'textInput',
    name: 'Text Input',
    description: 'Enter text manually',
    category: 'input',
    icon: 'T',
    color: '#888888',
    aiControllable: false,
    pythonModule: 'forge_input.text_input',
    inputs: [],
    outputs: [{ name: 'text', type: 'text', color: '#55FF55' }],
  },
  {
    type: 'sdxlGenerator',
    name: 'SDXL Generator',
    description: 'Generate images with Stable Diffusion XL',
    category: 'generation',
    icon: 'SD',
    color: '#E91E63',
    aiControllable: true,
    pythonModule: 'forge_diffusion.sdxl_generator',
    inputs: [
      { name: 'prompt', type: 'text', required: true, color: '#55FF55' },
      { name: 'width', type: 'number', default: 1024, color: '#888888' },
    ],
    outputs: [
      { name: 'image', type: 'image', color: '#FF5555' },
    ],
  },
  {
    type: 'promptRefiner',
    name: 'Prompt Refiner',
    description: 'Enhance prompts with Merlinv1 AI',
    category: 'ai_agent',
    icon: 'AI',
    color: '#4CAF50',
    merlinv1Required: true,
    pythonModule: 'forge_agents.prompt_refiner',
    inputs: [{ name: 'prompt', type: 'text', required: true, color: '#55FF55' }],
    outputs: [{ name: 'refined_prompt', type: 'text', color: '#55FF55' }],
  },
  {
    type: 'superResolution',
    name: 'Super Resolution',
    description: 'Upscale images with AI',
    category: 'enhancement',
    icon: 'SR',
    color: '#2196F3',
    pythonModule: 'forge_sr.super_resolution',
    inputs: [
      { name: 'image', type: 'image', required: true, color: '#FF5555' },
      { name: 'scale', type: 'number', default: 2, color: '#888888' },
    ],
    outputs: [{ name: 'upscaled_image', type: 'image', color: '#FF5555' }],
  },
]
