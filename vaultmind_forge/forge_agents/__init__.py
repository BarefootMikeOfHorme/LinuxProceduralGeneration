"""
VaultMind Forge - Specialized Agentic Helpers
Autonomous micro-decision agents for asset pipeline tasks

These agents handle specific subtasks without requiring main AI consultation,
significantly improving iteration speed and reducing costs.
"""

from .base_agent import (
    BaseAgent,
    AgentDecision,
    AgentCapability,
    EscalationReason,
)

from .quality_guardian import (
    QualityGuardianAgent,
    QualityIssue,
    QualityDecision,
    AutoFixType,
    QualityReport,
)

from .style_profiles import (
    StyleProfile,
    ParameterRange,
    ALL_PROFILES,
    get_profile,
)

from .style_profile_manager import (
    StyleProfileManager,
    create_style_aware_pipeline,
    quick_style_detection,
    get_recommended_params,
)

from .prompt_refiner import (
    PromptRefinerAgent,
    PromptRefinement,
)

__all__ = [
    # Base
    'BaseAgent',
    'AgentDecision',
    'AgentCapability',
    'EscalationReason',

    # Quality Guardian
    'QualityGuardianAgent',
    'QualityIssue',
    'QualityDecision',
    'AutoFixType',
    'QualityReport',

    # Style Profiles
    'StyleProfile',
    'ParameterRange',
    'ALL_PROFILES',
    'get_profile',
    'StyleProfileManager',
    'create_style_aware_pipeline',
    'quick_style_detection',
    'get_recommended_params',

    # Prompt Refiner
    'PromptRefinerAgent',
    'PromptRefinement',
]

__version__ = "1.0.0"
