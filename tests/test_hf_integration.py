from pathlib import Path
import logging

from vaultmind_forge.forge_agents.maestro_agent import MaestroAgent
from vaultmind_forge.forge_agents.agent_manager import AgentManager
from vaultmind_forge.forge_agents.prompt_refiner import PromptRefinerAgent
from vaultmind_forge.forge_ai.base_ai import BaseAI, AIResponse, AIRequest

# Mock AI Backend for Maestro
class MockMaestroAI(BaseAI):
    def initialize(self): pass
    def is_available(self): return True
    
    def generate(self, request: AIRequest) -> AIResponse:
        # Return a plan that uses prompt_refiner
        return AIResponse(
            content='''
            ```json
            [
                {
                    "id": "step1",
                    "description": "Refine the prompt 'a cat'",
                    "assigned_agent": "prompt_refiner",
                    "dependencies": []
                }
            ]
            ```
            ''',
            backend="mock",
            model="mock",
            tokens_used=0,
            cost_estimate=0.0,
            latency_ms=0
        )

# Mock HF Backend for PromptRefiner
class MockHFBackend(BaseAI):
    def initialize(self): pass
    def is_available(self): return True

    def generate(self, request: AIRequest) -> AIResponse:
        return AIResponse(
            content="a highly detailed cat, 8k resolution, cinematic lighting",
            backend="mock_hf",
            model="mock_llama",
            tokens_used=10,
            cost_estimate=0.0,
            latency_ms=100
        )

def test_integration():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("IntegrationTest")
    
    logger.info("Setting up agents...")
    
    # Setup Agent Manager
    manager = AgentManager()
    
    # Setup Prompt Refiner with Mock HF
    refiner = PromptRefinerAgent(use_ai_refinement=True)
    refiner.ai_backend = MockHFBackend(model="mock") # Inject mock
    refiner.ai_available = True
    
    from vaultmind_forge.forge_agents.agent_manager import AgentStatus, AgentConfig, AgentState, AgentCapability

    # Register manually since we injected mock
    # We need to wrap it in AgentStatus
    config = AgentConfig(
        name="prompt_refiner",
        class_path="vaultmind_forge.forge_agents.prompt_refiner.PromptRefinerAgent",
        capabilities=[AgentCapability.PROMPT_REFINEMENT]
    )
    
    manager.agents["prompt_refiner"] = AgentStatus(
        config=config,
        state=AgentState.LOADED,
        instance=refiner
    )
    
    # Setup Maestro
    maestro = MaestroAgent(ai_backend=MockMaestroAI(model="mock"), agent_manager=manager)
    
    logger.info("Executing Maestro...")
    decision = maestro.make_decision({"request": "Make this prompt better: 'a cat'"})
    
    logger.info(f"Maestro Decision: {decision.action}")
    logger.info(f"Results: {decision.metadata['results']}")
    
    # Verify
    results = decision.metadata['results']
    if "step1" in results:
        step1_result = results["step1"]
        refined_prompt = step1_result["metadata"]["refined_prompt"]
        logger.info(f"Refined Prompt: {refined_prompt}")
        
        if "highly detailed" in refined_prompt:
            print("\nSUCCESS: Prompt was refined using Mock HF backend!")
        else:
            print("\nFAILURE: Prompt was not refined correctly.")
    else:
        print("\nFAILURE: Step 1 not executed.")

if __name__ == "__main__":
    test_integration()
