"""
Programmatic Agent - Base for Deterministic Logic Agents

These agents perform tasks without using LLMs, such as:
- System resource monitoring
- File management
- deterministic data processing
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentCapability, AgentDecision

logger = logging.getLogger(__name__)

class ProgrammaticAgent(BaseAgent):
    """
    Base class for agents that use deterministic logic (code) 
    rather than AI models to make decisions.
    """
    
    def __init__(self, name: str, capabilities: List[AgentCapability]):
        super().__init__(name, capabilities)
        self.learning_enabled = False  # Programmatic agents typically don't "learn" in the ML sense
        
    def calculate_confidence(self, context: Dict[str, Any], proposed_action: str) -> float:
        """
        Programmatic agents usually have 1.0 confidence if logic succeeds,
        or 0.0 if it fails/conditions aren't met.
        """
        return 1.0

    def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """
        Execute deterministic logic.
        Subclasses must implement _execute_logic(context).
        """
        try:
            return self._execute_logic(context)
        except Exception as e:
            logger.error(f"Programmatic agent {self.name} failed: {e}")
            return AgentDecision(
                action="ERROR",
                confidence=0.0,
                reasoning=f"Internal error: {str(e)}",
                metadata={"error": str(e)}
            )

    def _execute_logic(self, context: Dict[str, Any]) -> AgentDecision:
        """
        Implement the specific logic for this agent.
        Must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _execute_logic")


# Example Implementation: Resource Monitor
class ResourceMonitorAgent(ProgrammaticAgent):
    """
    Monitors system resources and recommends actions.
    """
    
    def __init__(self):
        super().__init__(
            name="resource_monitor",
            capabilities=[AgentCapability.RESOURCE_OPTIMIZATION]
        )
        
    def _execute_logic(self, context: Dict[str, Any]) -> AgentDecision:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        metadata = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3)
        }
        
        # Simple logic
        if memory.percent > 90:
            return AgentDecision(
                action="WARN",
                confidence=1.0,
                reasoning="Memory usage is critically high (>90%)",
                metadata=metadata
            )
        elif cpu_percent > 90:
             return AgentDecision(
                action="WARN",
                confidence=1.0,
                reasoning="CPU usage is critically high (>90%)",
                metadata=metadata
            )
            
        return AgentDecision(
            action="APPROVE",
            confidence=1.0,
            reasoning="System resources are within normal limits",
            metadata=metadata
        )
