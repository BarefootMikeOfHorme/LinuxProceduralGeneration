"""
VaultMind Forge - Base Agent Class
Foundation for all specialized agentic helpers
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Agent capabilities"""
    QUALITY_ASSESSMENT = "quality_assessment"
    AUTO_FIX = "auto_fix"
    PARAMETER_TUNING = "parameter_tuning"
    PROMPT_REFINEMENT = "prompt_refinement"
    MATERIAL_SUGGESTION = "material_suggestion"
    RESOURCE_OPTIMIZATION = "resource_optimization"


class EscalationReason(Enum):
    """Reasons for escalating to main AI"""
    LOW_CONFIDENCE = "low_confidence"
    SEVERE_ISSUES = "severe_issues"
    UNKNOWN_CASE = "unknown_case"
    POLICY_VIOLATION = "policy_violation"
    HUMAN_REVIEW_REQUIRED = "human_review_required"


@dataclass
class AgentDecision:
    """Result of agent decision-making"""
    action: str  # APPROVE, FIX, RETRY, REJECT, ESCALATE
    confidence: float  # 0.0-1.0
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    fixes_applied: List[str] = field(default_factory=list)
    escalation_reason: Optional[EscalationReason] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'metadata': self.metadata,
            'fixes_applied': self.fixes_applied,
            'escalation_reason': self.escalation_reason.value if self.escalation_reason else None,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class AgentMetrics:
    """Track agent performance over time"""
    total_decisions: int = 0
    decisions_by_action: Dict[str, int] = field(default_factory=dict)
    average_confidence: float = 0.0
    escalation_rate: float = 0.0
    auto_fix_success_rate: float = 0.0
    processing_time_avg_ms: float = 0.0

    # Learning metrics
    decisions_accepted: int = 0  # Not overridden by human/main AI
    decisions_overridden: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_decisions': self.total_decisions,
            'decisions_by_action': self.decisions_by_action,
            'average_confidence': round(self.average_confidence, 3),
            'escalation_rate': round(self.escalation_rate, 3),
            'auto_fix_success_rate': round(self.auto_fix_success_rate, 3),
            'processing_time_avg_ms': round(self.processing_time_avg_ms, 2),
            'accuracy': round(
                self.decisions_accepted / (self.decisions_accepted + self.decisions_overridden)
                if (self.decisions_accepted + self.decisions_overridden) > 0 else 0.0,
                3
            )
        }


class BaseAgent(ABC):
    """
    Base class for all specialized agentic helpers.

    Key principles:
    - Make autonomous decisions for specific domain
    - Calculate confidence scores
    - Escalate when uncertain
    - Learn from experience
    - Track performance metrics
    """

    def __init__(self, name: str, capabilities: List[AgentCapability]):
        """
        Initialize base agent.

        Args:
            name: Agent name
            capabilities: List of agent capabilities
        """
        self.name = name
        self.capabilities = capabilities
        self.metrics = AgentMetrics()
        self.decision_history: List[AgentDecision] = []
        self.max_history = 1000

        # Configuration
        self.confidence_threshold = 0.7  # Escalate if below this
        self.learning_enabled = True
        self.metrics_path: Optional[Path] = None

        logger.info(f"Agent initialized: {name} with capabilities: {[c.value for c in capabilities]}")

    @abstractmethod
    def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """
        Make autonomous decision for given context.

        Args:
            context: Decision context (varies by agent type)

        Returns:
            AgentDecision with action, confidence, reasoning
        """
        pass

    @abstractmethod
    def calculate_confidence(self, context: Dict[str, Any], proposed_action: str) -> float:
        """
        Calculate confidence score for proposed action.

        Args:
            context: Decision context
            proposed_action: Proposed action

        Returns:
            Confidence score 0.0-1.0
        """
        pass

    def should_escalate(self, decision: AgentDecision) -> bool:
        """
        Determine if decision should be escalated to main AI.

        Args:
            decision: Agent decision

        Returns:
            True if should escalate
        """
        # Always escalate if confidence too low
        if decision.confidence < self.confidence_threshold:
            decision.escalation_reason = EscalationReason.LOW_CONFIDENCE
            return True

        # Escalate if decision is to escalate
        if decision.action == "ESCALATE":
            return True

        return False

    def record_decision(self, decision: AgentDecision) -> None:
        """
        Record decision in history and update metrics.

        Args:
            decision: Decision to record
        """
        # Add to history
        self.decision_history.append(decision)
        if len(self.decision_history) > self.max_history:
            self.decision_history = self.decision_history[-self.max_history:]

        # Update metrics
        self.metrics.total_decisions += 1

        # Count by action type
        if decision.action not in self.metrics.decisions_by_action:
            self.metrics.decisions_by_action[decision.action] = 0
        self.metrics.decisions_by_action[decision.action] += 1

        # Update average confidence (rolling average)
        self.metrics.average_confidence = (
            (self.metrics.average_confidence * (self.metrics.total_decisions - 1) + decision.confidence)
            / self.metrics.total_decisions
        )

        # Update escalation rate
        escalations = self.metrics.decisions_by_action.get("ESCALATE", 0)
        self.metrics.escalation_rate = escalations / self.metrics.total_decisions

        logger.debug(f"Agent {self.name} decision recorded: {decision.action} (confidence={decision.confidence:.3f})")

    def learn_from_feedback(self, decision_id: int, was_correct: bool, corrected_action: Optional[str] = None) -> None:
        """
        Learn from human/main AI feedback on decision.

        Args:
            decision_id: Index in decision history
            was_correct: Whether agent decision was correct
            corrected_action: What the correct action should have been
        """
        if not self.learning_enabled:
            return

        if was_correct:
            self.metrics.decisions_accepted += 1
        else:
            self.metrics.decisions_overridden += 1

            if corrected_action:
                logger.info(f"Agent {self.name} learned: {self.decision_history[decision_id].action} -> {corrected_action}")

                # Store for future training
                self._store_correction(decision_id, corrected_action)

    def _store_correction(self, decision_id: int, corrected_action: str) -> None:
        """Store correction for future ML training"""
        # Override in subclass to implement learning
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.

        Returns:
            Metrics dictionary
        """
        return self.metrics.to_dict()

    def save_metrics(self, path: Optional[Path] = None) -> None:
        """
        Save metrics to file.

        Args:
            path: Path to save metrics (optional, uses self.metrics_path if not provided)
        """
        save_path = path or self.metrics_path
        if not save_path:
            return

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w') as f:
            json.dump({
                'agent_name': self.name,
                'capabilities': [c.value for c in self.capabilities],
                'metrics': self.get_metrics(),
                'recent_decisions': [d.to_dict() for d in self.decision_history[-10:]],
            }, f, indent=2)

        logger.info(f"Agent {self.name} metrics saved to {save_path}")

    def load_metrics(self, path: Optional[Path] = None) -> None:
        """Load metrics from file"""
        load_path = path or self.metrics_path
        if not load_path or not load_path.exists():
            return

        with open(load_path, 'r') as f:
            data = json.load(f)

        # Restore metrics
        metrics_data = data.get('metrics', {})
        self.metrics.total_decisions = metrics_data.get('total_decisions', 0)
        self.metrics.average_confidence = metrics_data.get('average_confidence', 0.0)
        # ... restore other metrics

        logger.info(f"Agent {self.name} metrics loaded from {load_path}")

    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.metrics = AgentMetrics()
        self.decision_history = []
        logger.info(f"Agent {self.name} metrics reset")

    def get_status(self) -> Dict[str, Any]:
        """Get agent status summary"""
        return {
            'name': self.name,
            'capabilities': [c.value for c in self.capabilities],
            'metrics': self.get_metrics(),
            'confidence_threshold': self.confidence_threshold,
            'learning_enabled': self.learning_enabled,
            'decision_history_size': len(self.decision_history),
        }
