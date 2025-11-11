"""
Agent Collaboration Network - Autonomous multi-agent orchestration

Features:
- Agent-to-agent communication
- Collaborative task solving
- Knowledge sharing between agents
- Autonomous decision making
- Consensus protocols
- Dynamic agent teaming
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from .terminal_ui import TerminalUI, console
from .agent_manager import Agent, AgentType, AgentStatus


class MessageType(str, Enum):
    """Agent message types"""
    REQUEST = "request"  # Request assistance
    RESPONSE = "response"  # Respond to request
    PROPOSAL = "proposal"  # Propose solution/action
    VOTE = "vote"  # Vote on proposal
    INFORM = "inform"  # Share information
    QUERY = "query"  # Ask question
    COMMAND = "command"  # Direct command


class MessagePriority(str, Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AgentMessage:
    """Message between agents"""
    id: str
    sender_id: str
    recipient_id: str  # or "broadcast" for all
    type: MessageType
    priority: MessagePriority
    content: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    requires_response: bool = False
    parent_message_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "type": self.type.value,
            "priority": self.priority.value,
            "content": self.content,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentProposal:
    """Proposal from agent for collaborative decision"""
    id: str
    proposer_id: str
    description: str
    action: str
    params: Dict[str, Any]
    votes_for: Set[str] = field(default_factory=set)
    votes_against: Set[str] = field(default_factory=set)
    required_votes: int = 2
    status: str = "pending"  # pending, approved, rejected
    created_at: float = field(default_factory=time.time)

    def vote(self, agent_id: str, approve: bool) -> None:
        """Cast vote"""
        if approve:
            self.votes_for.add(agent_id)
            self.votes_against.discard(agent_id)
        else:
            self.votes_against.add(agent_id)
            self.votes_for.discard(agent_id)

        # Update status
        if len(self.votes_for) >= self.required_votes:
            self.status = "approved"
        elif len(self.votes_against) >= self.required_votes:
            self.status = "rejected"


@dataclass
class CollaborativeTask:
    """Task requiring multiple agents"""
    id: str
    name: str
    description: str
    required_agents: List[AgentType]  # Types of agents needed
    assigned_agents: Dict[str, str] = field(default_factory=dict)  # type -> agent_id
    status: str = "forming"  # forming, ready, in_progress, completed
    messages: List[AgentMessage] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)


class AgentNetwork:
    """
    Multi-agent collaboration network

    Enables agents to communicate, collaborate, and make autonomous decisions
    """

    def __init__(self, agent_manager):
        self.agent_manager = agent_manager

        # Communication infrastructure
        self.message_queue: Dict[str, List[AgentMessage]] = defaultdict(list)  # agent_id -> messages
        self.broadcast_queue: List[AgentMessage] = []

        # Collaboration state
        self.proposals: Dict[str, AgentProposal] = {}
        self.collaborative_tasks: Dict[str, CollaborativeTask] = {}
        self.agent_teams: Dict[str, Set[str]] = {}  # team_name -> agent_ids

        # Knowledge base (shared between agents)
        self.shared_knowledge: Dict[str, Any] = {}

    async def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_response: bool = False,
    ) -> str:
        """Send message from one agent to another"""
        message_id = f"msg_{uuid.uuid4().hex[:8]}"

        message = AgentMessage(
            id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            type=message_type,
            priority=priority,
            content=content,
            requires_response=requires_response,
        )

        if recipient_id == "broadcast":
            self.broadcast_queue.append(message)
        else:
            self.message_queue[recipient_id].append(message)

        return message_id

    async def receive_messages(self, agent_id: str, message_type: Optional[MessageType] = None) -> List[AgentMessage]:
        """Receive messages for agent"""
        messages = []

        # Personal messages
        agent_messages = self.message_queue.get(agent_id, [])
        if message_type:
            agent_messages = [m for m in agent_messages if m.type == message_type]
        messages.extend(agent_messages)
        self.message_queue[agent_id].clear()

        # Broadcast messages
        broadcast_messages = self.broadcast_queue.copy()
        if message_type:
            broadcast_messages = [m for m in broadcast_messages if m.type == message_type]
        messages.extend(broadcast_messages)

        # Sort by priority and time
        priority_order = {
            MessagePriority.URGENT: 0,
            MessagePriority.HIGH: 1,
            MessagePriority.NORMAL: 2,
            MessagePriority.LOW: 3,
        }
        messages.sort(key=lambda m: (priority_order[m.priority], m.timestamp))

        return messages

    async def create_proposal(
        self,
        proposer_id: str,
        description: str,
        action: str,
        params: Dict[str, Any],
        required_votes: int = 2,
    ) -> str:
        """Create proposal for collaborative decision"""
        proposal_id = f"prop_{uuid.uuid4().hex[:8]}"

        proposal = AgentProposal(
            id=proposal_id,
            proposer_id=proposer_id,
            description=description,
            action=action,
            params=params,
            required_votes=required_votes,
        )

        self.proposals[proposal_id] = proposal

        # Broadcast proposal to all agents
        await self.send_message(
            sender_id=proposer_id,
            recipient_id="broadcast",
            message_type=MessageType.PROPOSAL,
            content={
                "proposal_id": proposal_id,
                "description": description,
                "action": action,
            },
            priority=MessagePriority.HIGH,
        )

        return proposal_id

    async def vote_on_proposal(self, proposal_id: str, voter_id: str, approve: bool) -> bool:
        """Vote on proposal"""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False

        proposal.vote(voter_id, approve)

        # Notify proposer of vote
        await self.send_message(
            sender_id=voter_id,
            recipient_id=proposal.proposer_id,
            message_type=MessageType.VOTE,
            content={
                "proposal_id": proposal_id,
                "approve": approve,
                "current_votes": len(proposal.votes_for),
                "required_votes": proposal.required_votes,
            },
        )

        return proposal.status != "pending"

    async def create_collaborative_task(
        self,
        name: str,
        description: str,
        required_agents: List[AgentType],
    ) -> str:
        """Create task requiring multiple agents"""
        task_id = f"ctask_{uuid.uuid4().hex[:8]}"

        task = CollaborativeTask(
            id=task_id,
            name=name,
            description=description,
            required_agents=required_agents,
        )

        self.collaborative_tasks[task_id] = task

        # Find and assign agents
        await self._assign_agents_to_task(task)

        return task_id

    async def _assign_agents_to_task(self, task: CollaborativeTask) -> None:
        """Assign agents to collaborative task"""
        for agent_type in task.required_agents:
            # Find available agent of this type
            agents = self.agent_manager.list_agents(filter_type=agent_type)
            available = [a for a in agents if a.status == AgentStatus.IDLE]

            if available:
                agent = available[0]
                task.assigned_agents[agent_type.value] = agent.id

                # Notify agent of assignment
                await self.send_message(
                    sender_id="system",
                    recipient_id=agent.id,
                    message_type=MessageType.COMMAND,
                    content={
                        "command": "join_collaborative_task",
                        "task_id": task.id,
                        "task_name": task.name,
                        "role": agent_type.value,
                    },
                    priority=MessagePriority.HIGH,
                )

                # Update agent status
                self.agent_manager.update_agent_status(agent.id, AgentStatus.RUNNING)

        # Check if team is complete
        if len(task.assigned_agents) == len(task.required_agents):
            task.status = "ready"

            # Notify all agents that team is formed
            await self._notify_team_formed(task)

    async def _notify_team_formed(self, task: CollaborativeTask) -> None:
        """Notify all agents that team is formed"""
        for agent_id in task.assigned_agents.values():
            await self.send_message(
                sender_id="system",
                recipient_id=agent_id,
                message_type=MessageType.INFORM,
                content={
                    "event": "team_formed",
                    "task_id": task.id,
                    "team_members": list(task.assigned_agents.values()),
                },
                priority=MessagePriority.HIGH,
            )

    async def execute_collaborative_task(self, task_id: str) -> Dict[str, Any]:
        """Execute collaborative task with agent coordination"""
        task = self.collaborative_tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status != "ready":
            raise ValueError(f"Task {task_id} not ready (status: {task.status})")

        task.status = "in_progress"

        # Example collaborative workflow:
        # 1. Prompt Refiner enhances prompt
        # 2. Parameter Optimizer selects parameters
        # 3. Quality Guardian validates
        # 4. Material Specialist analyzes

        results = {}

        # Each agent performs their part
        for agent_type, agent_id in task.assigned_agents.items():
            agent = self.agent_manager.get_agent(agent_id)

            # Simulate agent work
            await asyncio.sleep(0.5)

            # Agent produces result
            result = await self._execute_agent_role(agent, task)
            results[agent_type] = result

            # Agent shares result with team
            await self.send_message(
                sender_id=agent_id,
                recipient_id="broadcast",
                message_type=MessageType.INFORM,
                content={
                    "task_id": task_id,
                    "role_completed": agent_type,
                    "result": result,
                },
            )

        task.result = results
        task.status = "completed"

        # Update agents back to idle
        for agent_id in task.assigned_agents.values():
            self.agent_manager.update_agent_status(agent_id, AgentStatus.IDLE)

        return results

    async def _execute_agent_role(self, agent: Agent, task: CollaborativeTask) -> Dict[str, Any]:
        """Execute agent's role in collaborative task"""
        # This would call the actual agent logic
        # For now, return mock result

        if agent.type == AgentType.PROMPT:
            return {
                "original_prompt": "example",
                "enhanced_prompt": "detailed example with artistic style",
                "confidence": 0.95,
            }
        elif agent.type == AgentType.QUALITY:
            return {
                "quality_score": 0.92,
                "issues_found": [],
                "approved": True,
            }
        elif agent.type == AgentType.PARAMETER:
            return {
                "steps": 30,
                "guidance_scale": 7.5,
                "confidence": 0.88,
            }
        else:
            return {"status": "completed"}

    def share_knowledge(self, agent_id: str, key: str, value: Any) -> None:
        """Agent shares knowledge with network"""
        self.shared_knowledge[key] = {
            "value": value,
            "source": agent_id,
            "timestamp": time.time(),
        }

    def get_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve shared knowledge"""
        entry = self.shared_knowledge.get(key)
        return entry["value"] if entry else None

    def create_agent_team(self, team_name: str, agent_ids: List[str]) -> None:
        """Create persistent agent team"""
        self.agent_teams[team_name] = set(agent_ids)

    def visualize_network(self) -> None:
        """Visualize agent network and communication"""
        TerminalUI.clear()
        TerminalUI.header("Agent Collaboration Network", "Multi-Agent Communication & Coordination")

        # Active agents
        agents = self.agent_manager.list_agents()
        active_agents = [a for a in agents if a.status != AgentStatus.IDLE]

        console.print(f"[bold cyan]Active Agents:[/bold cyan] {len(active_agents)}/{len(agents)}\n")

        # Collaborative tasks
        console.print(f"[bold yellow]Collaborative Tasks:[/bold yellow] {len(self.collaborative_tasks)}")
        for task in self.collaborative_tasks.values():
            status_color = "green" if task.status == "completed" else "yellow"
            console.print(f"  [{status_color}]{task.name}[/{status_color}] - {task.status}")
            console.print(f"    Team: {len(task.assigned_agents)}/{len(task.required_agents)} agents assigned")

        console.print()

        # Message queue status
        total_messages = sum(len(msgs) for msgs in self.message_queue.values()) + len(self.broadcast_queue)
        console.print(f"[bold magenta]Message Queue:[/bold magenta] {total_messages} pending messages")

        # Proposals
        pending_proposals = [p for p in self.proposals.values() if p.status == "pending"]
        if pending_proposals:
            console.print(f"\n[bold blue]Active Proposals:[/bold blue] {len(pending_proposals)}")
            for prop in pending_proposals:
                console.print(f"  {prop.description}")
                console.print(f"    Votes: {len(prop.votes_for)}/{prop.required_votes}")

        # Agent teams
        if self.agent_teams:
            console.print(f"\n[bold green]Persistent Teams:[/bold green]")
            for team_name, agent_ids in self.agent_teams.items():
                console.print(f"  {team_name}: {len(agent_ids)} agents")

        console.print()

    def get_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        return {
            "total_messages": sum(len(msgs) for msgs in self.message_queue.values()),
            "broadcast_messages": len(self.broadcast_queue),
            "active_proposals": len([p for p in self.proposals.values() if p.status == "pending"]),
            "collaborative_tasks": len(self.collaborative_tasks),
            "agent_teams": len(self.agent_teams),
            "shared_knowledge_entries": len(self.shared_knowledge),
        }
