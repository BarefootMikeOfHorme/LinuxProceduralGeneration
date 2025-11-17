"""
VaultMind Forge CLI - Constants Module
Centralized constants for CLI orchestration system

L1-ACP Enhancement - Repair Priority #4
Extracted magic numbers from workflow_engine, agent_manager, etc.
"""

from __future__ import annotations

# ============================================================================
# Workflow Engine Constants
# ============================================================================

# Task execution
MAX_PARALLEL_TASKS = 4
CHECKPOINT_INTERVAL_SECONDS = 30.0
DAG_POLL_INTERVAL_SECONDS = 0.1

# Timeouts (seconds)
DEFAULT_TASK_TIMEOUT = 300
GENERATION_TASK_TIMEOUT = 300
VALIDATION_TASK_TIMEOUT = 60
ENHANCEMENT_TASK_TIMEOUT = 120

# ============================================================================
# Agent Autonomy Levels (0.0 - 1.0)
# ============================================================================

# Higher values = more autonomous decision-making
AGENT_QUALITY_GUARDIAN_AUTONOMY = 0.75
AGENT_PROMPT_REFINER_AUTONOMY = 0.85
AGENT_PARAMETER_OPTIMIZER_AUTONOMY = 0.70
AGENT_MATERIAL_SPECIALIST_AUTONOMY = 0.75
AGENT_RESOLUTION_EXPERT_AUTONOMY = 0.80

# ============================================================================
# Quality Thresholds
# ============================================================================

# Confidence thresholds for agent decisions
CONFIDENCE_THRESHOLD_AUTO_APPROVE = 0.85
CONFIDENCE_THRESHOLD_AUTO_FIX = 0.75
CONFIDENCE_THRESHOLD_FLAG_REVIEW = 0.60
CONFIDENCE_THRESHOLD_AUTO_REJECT = 0.40

# Quality Guardian specific
QUALITY_GUARDIAN_MIN_CONFIDENCE = 0.70
QUALITY_GUARDIAN_AUTO_FIX_CONFIDENCE = 0.75

# ============================================================================
# Monitoring & Stats
# ============================================================================

MONITOR_REFRESH_INTERVAL_SECONDS = 2
STATS_UPDATE_INTERVAL_SECONDS = 1
GPU_POLL_INTERVAL_SECONDS = 0.5

# ============================================================================
# Process Orchestration
# ============================================================================

PROCESS_POLL_INTERVAL_SECONDS = 0.1
PROCESS_STARTUP_TIMEOUT = 5
PROCESS_SHUTDOWN_TIMEOUT = 10

# ============================================================================
# Distributed Execution
# ============================================================================

DEFAULT_WORKER_COUNT = 4
MAX_WORKER_COUNT = 16
WORKER_HEALTH_CHECK_INTERVAL = 30
WORKER_TIMEOUT_SECONDS = 300

# Task queue
TASK_QUEUE_MAX_SIZE = 1000
TASK_BATCH_SIZE = 10
TASK_RETRY_MAX_ATTEMPTS = 3
TASK_RETRY_DELAY_SECONDS = 5

# ============================================================================
# Checkpoint Manager
# ============================================================================

CHECKPOINT_AUTO_SAVE_INTERVAL = 30.0
CHECKPOINT_MAX_HISTORY = 10
CHECKPOINT_COMPRESSION_ENABLED = True

# ============================================================================
# Network & Communication
# ============================================================================

AGENT_NETWORK_PORT_RANGE_START = 5000
AGENT_NETWORK_PORT_RANGE_END = 5999
AGENT_HEARTBEAT_INTERVAL = 10
AGENT_TIMEOUT_MULTIPLIER = 3  # timeout = heartbeat * multiplier

# ============================================================================
# Terminal UI
# ============================================================================

TERMINAL_MIN_WIDTH = 80
TERMINAL_MIN_HEIGHT = 24
LOADING_SPINNER_INTERVAL = 0.1
PROGRESS_BAR_WIDTH = 40

# ============================================================================
# File & Memory Limits
# ============================================================================

MAX_LOG_FILE_SIZE_MB = 100
MAX_CHECKPOINT_SIZE_MB = 500
MAX_MEMORY_USAGE_PERCENT = 90

# Cache sizes
RESULT_CACHE_MAX_SIZE = 1000
VALIDATION_CACHE_MAX_SIZE = 500

# ============================================================================
# Retry & Error Handling
# ============================================================================

MAX_RETRIES_DEFAULT = 3
RETRY_BACKOFF_BASE = 2  # seconds, exponential backoff
MAX_RETRY_DELAY = 60  # seconds

ERROR_REFLEX_TIER_1_TIMEOUT = 5  # Quick fixes
ERROR_REFLEX_TIER_2_TIMEOUT = 30  # Deferred fixes
ERROR_REFLEX_TIER_3_TIMEOUT = 300  # Steward review

# ============================================================================
# Version & Compatibility
# ============================================================================

CLI_VERSION = "0.1.0"
MIN_PYTHON_VERSION = (3, 10)
MIN_NODE_VERSION = (18, 0)

# ============================================================================
# Export all constants
# ============================================================================

__all__ = [
    # Workflow
    "MAX_PARALLEL_TASKS",
    "CHECKPOINT_INTERVAL_SECONDS",
    "DAG_POLL_INTERVAL_SECONDS",

    # Timeouts
    "DEFAULT_TASK_TIMEOUT",
    "GENERATION_TASK_TIMEOUT",
    "VALIDATION_TASK_TIMEOUT",
    "ENHANCEMENT_TASK_TIMEOUT",

    # Agent autonomy
    "AGENT_QUALITY_GUARDIAN_AUTONOMY",
    "AGENT_PROMPT_REFINER_AUTONOMY",
    "AGENT_PARAMETER_OPTIMIZER_AUTONOMY",
    "AGENT_MATERIAL_SPECIALIST_AUTONOMY",
    "AGENT_RESOLUTION_EXPERT_AUTONOMY",

    # Thresholds
    "CONFIDENCE_THRESHOLD_AUTO_APPROVE",
    "CONFIDENCE_THRESHOLD_AUTO_FIX",
    "CONFIDENCE_THRESHOLD_FLAG_REVIEW",
    "CONFIDENCE_THRESHOLD_AUTO_REJECT",
    "QUALITY_GUARDIAN_MIN_CONFIDENCE",
    "QUALITY_GUARDIAN_AUTO_FIX_CONFIDENCE",

    # Monitoring
    "MONITOR_REFRESH_INTERVAL_SECONDS",
    "STATS_UPDATE_INTERVAL_SECONDS",
    "GPU_POLL_INTERVAL_SECONDS",

    # Distributed
    "DEFAULT_WORKER_COUNT",
    "MAX_WORKER_COUNT",
    "WORKER_HEALTH_CHECK_INTERVAL",
    "WORKER_TIMEOUT_SECONDS",

    # Task queue
    "TASK_QUEUE_MAX_SIZE",
    "TASK_BATCH_SIZE",
    "TASK_RETRY_MAX_ATTEMPTS",
    "TASK_RETRY_DELAY_SECONDS",

    # Checkpoint
    "CHECKPOINT_AUTO_SAVE_INTERVAL",
    "CHECKPOINT_MAX_HISTORY",

    # Error handling
    "MAX_RETRIES_DEFAULT",
    "RETRY_BACKOFF_BASE",
    "MAX_RETRY_DELAY",

    # Version
    "CLI_VERSION",
    "MIN_PYTHON_VERSION",
    "MIN_NODE_VERSION",
]
