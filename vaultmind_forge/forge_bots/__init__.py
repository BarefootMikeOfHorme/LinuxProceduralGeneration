"""
VaultMind Forge - Bot Framework
Automated helper bots for asset pipeline management

Inspired by protocol_daemon.py and monitor_cli.py patterns
"""

from .base_bot import (
    BaseBot,
    BotStatus,
    BotPriority,
    BotConfig
)

from .monitor_bot import (
    AssetMonitorBot,
    FolderWatchConfig
)

from .qa_bot import (
    QualityAssuranceBot,
    QAConfig,
    QAReport
)

from .optimizer_bot import (
    ResourceOptimizerBot,
    OptimizerConfig
)

from .lineage_bot import (
    LineageInspectorBot,
    LineageConfig
)

from .scheduler import (
    BotScheduler,
    ScheduleConfig
)

__all__ = [
    # Base
    'BaseBot',
    'BotStatus',
    'BotPriority',
    'BotConfig',

    # Monitor Bot
    'AssetMonitorBot',
    'FolderWatchConfig',

    # QA Bot
    'QualityAssuranceBot',
    'QAConfig',
    'QAReport',

    # Optimizer Bot
    'ResourceOptimizerBot',
    'OptimizerConfig',

    # Lineage Bot
    'LineageInspectorBot',
    'LineageConfig',

    # Scheduler
    'BotScheduler',
    'ScheduleConfig',
]

__version__ = "1.0.0"
