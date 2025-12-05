"""
Maestro Agent - The Master Planner

This agent is responsible for:
1. Understanding high-level user requests
2. Decomposing them into sub-tasks
3. Delegating tasks to specialized agents (via AgentManager)
4. Synthesizing results
"""

from __future__ import annotations

import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentCapability, AgentDecision
from ..forge_ai.base_ai import AIRequest

logger = logging.getLogger(__name__)

@dataclass
class SubTask:
    """A sub-task to be executed by an agent"""
    id: str
    description: str
    assigned_agent: str  # Name of agent to handle this
    dependencies: List[str]
    status: str = "pending"
    result: Any = None

class MaestroAgent(BaseAgent):
    """
    The Orchestrator. Uses a high-level AI model to plan and coordinate.
    """

    def __init__(self, ai_backend=None, agent_manager=None):
        super().__init__(
            name="maestro",
            capabilities=[
                AgentCapability.RESOURCE_OPTIMIZATION, # Planning is a form of optimization
                AgentCapability.QUALITY_ASSESSMENT     # Assessing plan quality
            ]
        )
        self.ai = ai_backend
        self.agent_manager = agent_manager
        
    def set_ai_backend(self, backend):
        self.ai = backend
        
    def set_agent_manager(self, manager):
        self.agent_manager = manager

    def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """
        The Maestro doesn't just make a single decision; it plans and executes.
        For the BaseAgent interface, we'll return the high-level plan as the decision.
        """
        user_request = context.get("request", "")
        if not user_request:
            return AgentDecision("REJECT", 1.0, "No request provided")

        # 1. Plan
        plan = self._create_plan(user_request)
        
        # 2. Execute (simplified for this interface, normally async)
        results = self._execute_plan(plan)
        
        return AgentDecision(
            action="COMPLETE",
            confidence=0.9,
            reasoning="Plan executed successfully",
            metadata={"plan": [t.__dict__ for t in plan], "results": results}
        )

    def calculate_confidence(self, context: Dict[str, Any], proposed_action: str) -> float:
        return 0.9  # Maestro is confident!

    def _create_plan(self, request: str) -> List[SubTask]:
        """Use AI to decompose request into subtasks"""
        if not self.ai:
            logger.warning("Maestro has no AI backend! Falling back to simple logic.")
            return []

        prompt = f"""
        You are the Maestro, the master planner for the VaultMind Forge system.
        
        Available Agents:
        - resource_monitor: Checks system CPU/RAM. Use before heavy tasks.
        - texture_generator: Generates textures (simulated).
        - validator: Validates assets.
        
        User Request: "{request}"
        
        Create a JSON execution plan. Format:
        [
            {{
                "id": "step1",
                "description": "Check resources",
                "assigned_agent": "resource_monitor",
                "dependencies": []
            }},
            ...
        ]
        """
        
        try:
            response = self.ai.generate(AIRequest(prompt=prompt, temperature=0.2))
            # Extract JSON from response (naive parsing for now)
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            data = json.loads(content.strip())
            
            tasks = []
            for item in data:
                tasks.append(SubTask(
                    id=item["id"],
                    description=item["description"],
                    assigned_agent=item["assigned_agent"],
                    dependencies=item.get("dependencies", [])
                ))
            return tasks
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return []

    def _execute_plan(self, tasks: List[SubTask]) -> Dict[str, Any]:
        """Execute the plan using AgentManager"""
        results = {}
        
        # Simple sequential execution for now (topological sort would be better)
        for task in tasks:
            logger.info(f"Maestro executing task: {task.description} (Agent: {task.assigned_agent})")
            
            if not self.agent_manager:
                logger.error("No AgentManager available to execute tasks")
                task.status = "failed"
                continue
                
            try:
                # Get agent
                agent = self.agent_manager.get_agent(task.assigned_agent)
                
                # Execute
                decision = agent.make_decision({"context": task.description})
                
                task.result = decision
                task.status = "completed"
                results[task.id] = decision.to_dict()
                
            except Exception as e:
                logger.error(f"Task {task.id} failed: {e}")
                task.status = "failed"
                task.result = str(e)
                
        return results
