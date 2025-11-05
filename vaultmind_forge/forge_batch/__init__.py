"""
VaultMind Forge - Batch Processing Module

Multi-asset job queue with priority scheduling and parallel execution.
"""

from .job_queue import (
    JobQueue,
    BatchJob,
    JobPriority,
    JobStatus
)

from .resource_manager import (
    ResourceManager,
    ResourceRequirements,
    GPUStatus,
    SystemResources
)

from .batch_processor import (
    BatchProcessor,
    WorkerStatus,
    BatchProgress
)

__all__ = [
    # Job Queue
    'JobQueue',
    'BatchJob',
    'JobPriority',
    'JobStatus',

    # Resource Manager
    'ResourceManager',
    'ResourceRequirements',
    'GPUStatus',
    'SystemResources',

    # Batch Processor
    'BatchProcessor',
    'WorkerStatus',
    'BatchProgress'
]

__version__ = "1.0.0"
