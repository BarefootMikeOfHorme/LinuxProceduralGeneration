"""
Agent Manager - Dynamic Lifecycle Management for Agents

Handles:
- Dynamic loading/unloading of agents
- Memory management (LRU cache)
- Integration with ModelManager
- Registry of available agents
"""

from __future__ import annotations

import logging
import time
import importlib
import threading
from typing import Dict, Any, Optional, Type, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .base_agent import BaseAgent, AgentCapability

logger = logging.getLogger(__name__)

class AgentState(str, Enum):
    """Agent lifecycle state"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    ERROR = "error"

@dataclass
class AgentConfig:
    """Configuration for a managed agent"""
    name: str
    class_path: str  # module.ClassName
    capabilities: List[AgentCapability]
    priority: int = 1
    keep_loaded: bool = False
    max_idle_seconds: float = 300.0  # 5 minutes

@dataclass
class AgentStatus:
    """Runtime status of an agent"""
    config: AgentConfig
    state: AgentState
    instance: Optional[BaseAgent] = None
    last_used: float = 0.0
    load_count: int = 0

class AgentManager:
    """
    Manages the lifecycle of agents, ensuring efficient resource usage.
    """

    def __init__(self, model_manager=None, max_loaded_agents: int = 5):
        """
        Initialize AgentManager.

        Args:
            model_manager: Optional reference to ModelManager for coordination
            max_loaded_agents: Maximum number of agents to keep in memory
        """
        self.model_manager = model_manager
        self.max_loaded_agents = max_loaded_agents
        
        self.agents: Dict[str, AgentStatus] = {}
        self._lock = threading.RLock()
        
        # Auto-unload thread could be added here similar to ModelManager
        
        logger.info(f"AgentManager initialized (max loaded: {max_loaded_agents})")

    def register_agent(self, config: AgentConfig) -> None:
        """Register an agent configuration"""
        with self._lock:
            self.agents[config.name] = AgentStatus(
                config=config,
                state=AgentState.UNLOADED
            )
            logger.info(f"Registered agent: {config.name}")

    def get_agent(self, agent_name: str) -> BaseAgent:
        """
        Get an agent instance, loading it if necessary.
        
        Args:
            agent_name: Name of the agent to retrieve
            
        Returns:
            Agent instance
        """
        with self._lock:
            if agent_name not in self.agents:
                raise ValueError(f"Agent {agent_name} not registered")
            
            status = self.agents[agent_name]
            
            # Update last used time
            status.last_used = time.time()
            
            if status.state == AgentState.LOADED and status.instance:
                return status.instance
            
            # Need to load
            return self._load_agent(agent_name)

    def _load_agent(self, agent_name: str) -> BaseAgent:
        """Internal method to load an agent"""
        status = self.agents[agent_name]
        
        # Check limits and unload if necessary
        self._enforce_limits()
        
        try:
            status.state = AgentState.LOADING
            logger.info(f"Loading agent: {agent_name}")
            
            # Parse class path
            module_name, class_name = status.config.class_path.rsplit('.', 1)
            
            # Import module
            module = importlib.import_module(module_name)
            agent_class = getattr(module, class_name)
            
            # Instantiate
            # Note: We assume a standard init signature or we'd need a factory
            instance = agent_class()
            
            # Inject dependencies if needed
            if hasattr(instance, 'set_model_manager') and self.model_manager:
                instance.set_model_manager(self.model_manager)
            
            status.instance = instance
            status.state = AgentState.LOADED
            status.load_count += 1
            status.last_used = time.time()
            
            logger.info(f"Agent {agent_name} loaded successfully")
            return instance
            
        except Exception as e:
            status.state = AgentState.ERROR
            logger.error(f"Failed to load agent {agent_name}: {e}")
            raise

    def unload_agent(self, agent_name: str) -> None:
        """Unload an agent to free resources"""
        with self._lock:
            if agent_name not in self.agents:
                return
            
            status = self.agents[agent_name]
            
            if status.state != AgentState.LOADED:
                return
            
            if status.config.keep_loaded:
                logger.debug(f"Skipping unload of {agent_name} (keep_loaded=True)")
                return

            logger.info(f"Unloading agent: {agent_name}")
            
            # Call cleanup if available
            if status.instance and hasattr(status.instance, 'cleanup'):
                try:
                    status.instance.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up agent {agent_name}: {e}")
            
            status.instance = None
            status.state = AgentState.UNLOADED

    def _enforce_limits(self) -> None:
        """Ensure we don't exceed max loaded agents"""
        loaded_agents = [
            (name, s) for name, s in self.agents.items() 
            if s.state == AgentState.LOADED and not s.config.keep_loaded
        ]
        
        if len(loaded_agents) < self.max_loaded_agents:
            return
            
        # Sort by last used (LRU)
        loaded_agents.sort(key=lambda x: x[1].last_used)
        
        # Unload least recently used until we have space
        while len(loaded_agents) >= self.max_loaded_agents:
            name, _ = loaded_agents.pop(0)
            self.unload_agent(name)

    def get_status(self) -> Dict[str, Any]:
        """Get manager status"""
        with self._lock:
            return {
                "max_loaded": self.max_loaded_agents,
                "agents": {
                    name: {
                        "state": s.state.value,
                        "load_count": s.load_count,
                        "last_used_seconds_ago": int(time.time() - s.last_used) if s.last_used > 0 else -1
                    }
                    for name, s in self.agents.items()
                }
            }
