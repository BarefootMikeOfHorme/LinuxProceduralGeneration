import pytest
import time
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from vaultmind_forge.forge_agents.agent_manager import AgentManager, AgentConfig, AgentState
from vaultmind_forge.forge_agents.base_agent import AgentCapability

# Mock agent class for testing
class MockAgent:
    def __init__(self):
        self.cleanup_called = False
        
    def cleanup(self):
        self.cleanup_called = True

def test_agent_registration():
    manager = AgentManager()
    config = AgentConfig(
        name="test_agent",
        class_path="vaultmind_forge.forge_agents.programmatic_agent.ResourceMonitorAgent",
        capabilities=[AgentCapability.RESOURCE_OPTIMIZATION]
    )
    manager.register_agent(config)
    assert "test_agent" in manager.agents
    assert manager.agents["test_agent"].state == AgentState.UNLOADED

def test_agent_loading():
    manager = AgentManager()
    config = AgentConfig(
        name="resource_monitor",
        class_path="vaultmind_forge.forge_agents.programmatic_agent.ResourceMonitorAgent",
        capabilities=[AgentCapability.RESOURCE_OPTIMIZATION]
    )
    manager.register_agent(config)
    
    agent = manager.get_agent("resource_monitor")
    assert agent is not None
    assert manager.agents["resource_monitor"].state == AgentState.LOADED
    assert manager.agents["resource_monitor"].load_count == 1

def test_lru_eviction():
    # Set max loaded to 1 to force eviction
    manager = AgentManager(max_loaded_agents=1)
    
    # Register two agents
    config1 = AgentConfig(
        name="agent1",
        class_path="vaultmind_forge.forge_agents.programmatic_agent.ResourceMonitorAgent",
        capabilities=[]
    )
    config2 = AgentConfig(
        name="agent2",
        class_path="vaultmind_forge.forge_agents.programmatic_agent.ResourceMonitorAgent",
        capabilities=[]
    )
    
    manager.register_agent(config1)
    manager.register_agent(config2)
    
    # Load agent 1
    manager.get_agent("agent1")
    assert manager.agents["agent1"].state == AgentState.LOADED
    
    # Load agent 2 - should evict agent 1
    manager.get_agent("agent2")
    
    assert manager.agents["agent2"].state == AgentState.LOADED
    assert manager.agents["agent1"].state == AgentState.UNLOADED

if __name__ == "__main__":
    # Manual run
    try:
        test_agent_registration()
        test_agent_loading()
        test_lru_eviction()
        print("✅ All AgentManager tests passed")
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
