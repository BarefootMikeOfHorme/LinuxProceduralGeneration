import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from vaultmind_forge.forge_agents.maestro_agent import MaestroAgent, SubTask
from vaultmind_forge.forge_ai.base_ai import AIResponse

def test_maestro_planning():
    # Mock AI backend
    mock_ai = MagicMock()
    mock_ai.generate.return_value = AIResponse(
        content='''
        ```json
        [
            {
                "id": "step1",
                "description": "Check system resources",
                "assigned_agent": "resource_monitor",
                "dependencies": []
            }
        ]
        ```
        ''',
        backend="mock",
        model="mock-model",
        tokens_used=10,
        cost_estimate=0.0,
        latency_ms=10.0
    )
    
    maestro = MaestroAgent(ai_backend=mock_ai)
    
    # Test planning
    plan = maestro._create_plan("Check resources")
    
    assert len(plan) == 1
    assert plan[0].id == "step1"
    assert plan[0].assigned_agent == "resource_monitor"
    assert plan[0].description == "Check system resources"

def test_maestro_execution():
    # Mock AgentManager
    mock_manager = MagicMock()
    mock_agent = MagicMock()
    mock_decision = MagicMock()
    mock_decision.to_dict.return_value = {"action": "APPROVE"}
    mock_agent.make_decision.return_value = mock_decision
    mock_manager.get_agent.return_value = mock_agent
    
    maestro = MaestroAgent(agent_manager=mock_manager)
    
    # Create manual plan
    tasks = [
        SubTask(id="t1", description="test", assigned_agent="test_agent", dependencies=[])
    ]
    
    # Execute
    results = maestro._execute_plan(tasks)
    
    assert "t1" in results
    assert results["t1"]["action"] == "APPROVE"
    mock_manager.get_agent.assert_called_with("test_agent")
    mock_agent.make_decision.assert_called()

if __name__ == "__main__":
    try:
        test_maestro_planning()
        test_maestro_execution()
        print("✅ All MaestroAgent tests passed")
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
