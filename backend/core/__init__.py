"""
VaultMind Forge - Core Execution Engine
Type-safe node execution with DAG topological sorting and unified pipeline interface
"""

from .types import DataType, can_connect
from .base_executor import NodeExecutor, InputSpec, OutputSpec
from .engine import NodeExecutionEngine
from .registry import NodeRegistry, create_default_registry
from .pipeline_base import (
    BasePipeline,
    PipelineResult,
    ValidationResult,
    PipelineStatus,
    PipelineValidationError,
    PipelineExecutionError,
    PipelineCancelledException,
    create_pipeline_result,
    merge_pipeline_results,
)

__all__ = [
    'DataType',
    'can_connect',
    'NodeExecutor',
    'InputSpec',
    'OutputSpec',
    'NodeExecutionEngine',
    'NodeRegistry',
    'create_default_registry',
    # Pipeline base classes
    'BasePipeline',
    'PipelineResult',
    'ValidationResult',
    'PipelineStatus',
    'PipelineValidationError',
    'PipelineExecutionError',
    'PipelineCancelledException',
    'create_pipeline_result',
    'merge_pipeline_results',
]
