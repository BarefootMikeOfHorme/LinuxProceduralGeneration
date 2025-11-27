import SDXLGeneratorNode from './SDXLGeneratorNode'
import PromptRefinerNode from './PromptRefinerNode'
import SuperResolutionNode from './SuperResolutionNode'
import TextInputNode from './TextInputNode'

// Map node types to React components
export const nodeTypes = {
  sdxlGenerator: SDXLGeneratorNode,
  promptRefiner: PromptRefinerNode,
  superResolution: SuperResolutionNode,
  textInput: TextInputNode,
  // Add more as we create them
}

export {
  SDXLGeneratorNode,
  PromptRefinerNode,
  SuperResolutionNode,
  TextInputNode,
}
