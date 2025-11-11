"""
Agent Manager - Orchestrates VaultMind Forge specialist agents

Integrates with existing agents:
- Quality Guardian
- Prompt Refiner
- Parameter Optimizer
- Material Specialist
- Resolution Expert
"""

from __future__ import annotations

import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum

from .terminal_ui import TerminalUI, console


class AgentStatus(str, Enum):
    """Agent status states"""
    RUNNING = "running"
    PAUSED = "paused"
    IDLE = "idle"
    ERROR = "error"
    COMPLETED = "completed"


class AgentType(str, Enum):
    """Agent types"""
    QUALITY = "quality"
    PROMPT = "prompt"
    PARAMETER = "parameter"
    MATERIAL = "material"
    RESOLUTION = "resolution"
    GENERATION = "generation"
    VALIDATION = "validation"


class AgentPriority(str, Enum):
    """Agent priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Agent:
    """Agent representation"""
    id: str
    name: str
    type: AgentType
    status: AgentStatus = AgentStatus.IDLE
    priority: AgentPriority = AgentPriority.MEDIUM
    last_active: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    task_count: int = 0
    success_count: int = 0
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "last_active": self.last_active,
            "metadata": self.metadata,
            "stats": {
                "tasks": self.task_count,
                "success": self.success_count,
                "errors": self.error_count,
            },
        }


class AgentManager:
    """
    Agent management system

    Integrates with VaultMind Forge specialist agents and provides
    CLI interface for monitoring and control.
    """

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self._load_agents()

    def _load_agents(self) -> None:
        """Load VaultMind Forge specialist agents"""
        # Quality Guardian
        self.agents["quality_guardian"] = Agent(
            id="quality_guardian",
            name="Quality Guardian",
            type=AgentType.QUALITY,
            status=AgentStatus.IDLE,
            priority=AgentPriority.HIGH,
            metadata={
                "description": "Autonomous quality validation and error detection",
                "capabilities": ["artifact_detection", "composition_check", "technical_validation"],
                "autonomous_level": 0.75,
            }
        )

        # Prompt Refiner
        self.agents["prompt_refiner"] = Agent(
            id="prompt_refiner",
            name="Prompt Refiner",
            type=AgentType.PROMPT,
            status=AgentStatus.IDLE,
            priority=AgentPriority.HIGH,
            metadata={
                "description": "Autonomous prompt enhancement and optimization",
                "capabilities": ["clarity_enhancement", "specificity_boost", "negative_prompt_generation"],
                "autonomous_level": 0.85,
            }
        )

        # Parameter Optimizer
        self.agents["parameter_optimizer"] = Agent(
            id="parameter_optimizer",
            name="Parameter Optimizer",
            type=AgentType.PARAMETER,
            status=AgentStatus.IDLE,
            priority=AgentPriority.MEDIUM,
            metadata={
                "description": "Autonomous parameter selection and optimization",
                "capabilities": ["step_optimization", "cfg_tuning", "seed_management"],
                "autonomous_level": 0.70,
            }
        )

        # Material Specialist
        self.agents["material_specialist"] = Agent(
            id="material_specialist",
            name="Material Specialist",
            type=AgentType.MATERIAL,
            status=AgentStatus.IDLE,
            priority=AgentPriority.MEDIUM,
            metadata={
                "description": "Material and texture analysis expert",
                "capabilities": ["material_detection", "style_analysis", "texture_enhancement"],
                "autonomous_level": 0.75,
            }
        )

        # Resolution Expert
        self.agents["resolution_expert"] = Agent(
            id="resolution_expert",
            name="Resolution Expert",
            type=AgentType.RESOLUTION,
            status=AgentStatus.IDLE,
            priority=AgentPriority.LOW,
            metadata={
                "description": "Resolution and aspect ratio specialist",
                "capabilities": ["resolution_selection", "aspect_ratio_optimization"],
                "autonomous_level": 0.80,
            }
        )

    def list_agents(self, filter_status: Optional[AgentStatus] = None,
                   filter_type: Optional[AgentType] = None) -> List[Agent]:
        """List agents with optional filtering"""
        agents = list(self.agents.values())

        if filter_status:
            agents = [a for a in agents if a.status == filter_status]

        if filter_type:
            agents = [a for a in agents if a.type == filter_type]

        return agents

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        agent = self.get_agent(agent_id)
        if agent:
            agent.status = status
            agent.last_active = time.time()
            return True
        return False

    def show_dashboard(self, filter_status: Optional[AgentStatus] = None) -> None:
        """Display agent dashboard"""
        TerminalUI.clear()
        TerminalUI.header("Agent Management", "VaultMind Forge Specialist Agents")

        agents = self.list_agents(filter_status=filter_status)

        if not agents:
            TerminalUI.warning("No agents found")
            return

        # Create table data
        rows = []
        for agent in agents:
            rows.append([
                agent.id,
                agent.name,
                TerminalUI.format_status(agent.status.value),
                agent.type.value.upper(),
                agent.priority.value.upper(),
                TerminalUI.format_time_ago(agent.last_active),
                f"{agent.metadata.get('autonomous_level', 0) * 100:.0f}%",
            ])

        TerminalUI.table(
            title="Active Agents",
            columns=["ID", "Name", "Status", "Type", "Priority", "Last Active", "Autonomy"],
            rows=rows,
            border_color="cyan",
        )

        # Summary stats
        total = len(self.agents)
        running = len([a for a in self.agents.values() if a.status == AgentStatus.RUNNING])
        idle = len([a for a in self.agents.values() if a.status == AgentStatus.IDLE])
        paused = len([a for a in self.agents.values() if a.status == AgentStatus.PAUSED])

        console.print(f"\n[cyan]Total Agents:[/cyan] {total}")
        console.print(f"[green]Running:[/green] {running} | [dim]Idle:[/dim] {idle} | [yellow]Paused:[/yellow] {paused}\n")

    def show_agent_details(self, agent_id: str) -> None:
        """Show detailed agent information"""
        agent = self.get_agent(agent_id)

        if not agent:
            TerminalUI.error(f"Agent '{agent_id}' not found")
            return

        TerminalUI.clear()
        TerminalUI.header(agent.name, f"Agent ID: {agent.id}")

        # Basic info
        console.print(f"[bold]Status:[/bold] {TerminalUI.format_status(agent.status.value)}")
        console.print(f"[bold]Type:[/bold] {agent.type.value.upper()}")
        console.print(f"[bold]Priority:[/bold] {agent.priority.value.upper()}")
        console.print(f"[bold]Last Active:[/bold] {TerminalUI.format_time_ago(agent.last_active)}")
        console.print(f"[bold]Autonomy:[/bold] {agent.metadata.get('autonomous_level', 0) * 100:.0f}%\n")

        # Description
        console.print(f"[bold cyan]Description:[/bold cyan]")
        console.print(f"  {agent.metadata.get('description', 'N/A')}\n")

        # Capabilities
        console.print(f"[bold cyan]Capabilities:[/bold cyan]")
        capabilities = agent.metadata.get('capabilities', [])
        for cap in capabilities:
            console.print(f"  • {cap.replace('_', ' ').title()}")

        # Stats
        console.print(f"\n[bold cyan]Statistics:[/bold cyan]")
        console.print(f"  Tasks Completed: {agent.task_count}")
        console.print(f"  Success Rate: {agent.success_count}/{agent.task_count if agent.task_count > 0 else 1}")
        console.print(f"  Errors: {agent.error_count}\n")

    def manage_agent_interactive(self, agent_id: str) -> None:
        """Interactive agent management"""
        agent = self.get_agent(agent_id)

        if not agent:
            TerminalUI.error(f"Agent '{agent_id}' not found")
            return

        while True:
            self.show_agent_details(agent_id)

            actions = [
                f"{'Pause' if agent.status == AgentStatus.RUNNING else 'Resume'} Agent",
                "Restart Agent",
                "View Logs (Coming Soon)",
                "Configure Agent (Coming Soon)",
                "Back to Dashboard",
            ]

            choice = TerminalUI.choice("Select action:", actions)

            if "Back" in choice:
                break
            elif "Pause" in choice or "Resume" in choice:
                new_status = AgentStatus.PAUSED if agent.status == AgentStatus.RUNNING else AgentStatus.RUNNING
                self.update_agent_status(agent_id, new_status)
                TerminalUI.success(f"Agent {agent.name} {'paused' if new_status == AgentStatus.PAUSED else 'resumed'}")
                time.sleep(1)
            elif "Restart" in choice:
                with TerminalUI.loading(f"Restarting {agent.name}"):
                    time.sleep(1)
                    self.update_agent_status(agent_id, AgentStatus.RUNNING)
                TerminalUI.success(f"Agent {agent.name} restarted")
                time.sleep(1)
            else:
                TerminalUI.warning("Feature coming soon!")
                time.sleep(1)

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        total_tasks = sum(a.task_count for a in self.agents.values())
        total_success = sum(a.success_count for a in self.agents.values())
        total_errors = sum(a.error_count for a in self.agents.values())

        status_counts = {}
        for status in AgentStatus:
            status_counts[status.value] = len([a for a in self.agents.values() if a.status == status])

        type_counts = {}
        for agent_type in AgentType:
            type_counts[agent_type.value] = len([a for a in self.agents.values() if a.type == agent_type])

        return {
            "total_agents": len(self.agents),
            "total_tasks": total_tasks,
            "total_success": total_success,
            "total_errors": total_errors,
            "success_rate": total_success / total_tasks if total_tasks > 0 else 0,
            "status_counts": status_counts,
            "type_counts": type_counts,
            "avg_autonomy": sum(a.metadata.get("autonomous_level", 0) for a in self.agents.values()) / len(self.agents),
        }

    def export_state(self) -> Dict[str, Any]:
        """Export agent state for JSON communication"""
        return {
            "agents": [agent.to_dict() for agent in self.agents.values()],
            "stats": self.get_stats(),
            "timestamp": time.time(),
        }
