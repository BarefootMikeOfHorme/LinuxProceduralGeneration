"""
VaultMind Forge - Base Pipeline Contract
Unified interface for all pipeline implementations across the system.

This module establishes the standard contract that all pipelines must follow,
enabling consistent testing, swapping, and orchestration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class PipelineStatus(Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineResult:
    """
    Standardized result from any pipeline execution.

    All 7 pipeline implementations must return this type.
    """
    success: bool
    """Whether pipeline completed successfully"""

    outputs: Dict[str, Any]
    """Dictionary of pipeline outputs keyed by output name"""

    errors: List[str] = field(default_factory=list)
    """List of error messages (empty if success=True)"""

    execution_time_ms: float = 0.0
    """Total execution time in milliseconds"""

    execution_order: List[str] = field(default_factory=list)
    """Order in which tasks/nodes were executed (for debugging)"""

    status: PipelineStatus = PipelineStatus.COMPLETED
    """Final status of pipeline execution"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata (lineage checksums, performance metrics, etc.)"""

    started_at: Optional[datetime] = None
    """When execution started"""

    finished_at: Optional[datetime] = None
    """When execution finished"""

    def __post_init__(self):
        """Validate result consistency"""
        if self.success and self.errors:
            # If marked as success, clear errors
            self.errors = []

        if not self.success and self.status == PipelineStatus.COMPLETED:
            # If failed, update status
            self.status = PipelineStatus.FAILED

        # Calculate execution time if timestamps available
        if self.started_at and self.finished_at:
            delta = self.finished_at - self.started_at
            self.execution_time_ms = delta.total_seconds() * 1000

    def add_error(self, error: Union[str, Exception]) -> None:
        """Add an error to the result"""
        error_msg = str(error)
        if error_msg not in self.errors:
            self.errors.append(error_msg)
        self.success = False
        self.status = PipelineStatus.FAILED

    def add_output(self, name: str, data: Any) -> None:
        """Add an output to the result"""
        self.outputs[name] = data

    def get_output(self, name: str, default: Any = None) -> Any:
        """Get an output by name"""
        return self.outputs.get(name, default)


@dataclass
class ValidationResult:
    """Result from pipeline validation"""
    valid: bool
    """Whether pipeline configuration is valid"""

    errors: List[str] = field(default_factory=list)
    """List of validation errors"""

    warnings: List[str] = field(default_factory=list)
    """List of validation warnings (non-fatal)"""

    def add_error(self, error: str) -> None:
        """Add a validation error"""
        if error not in self.errors:
            self.errors.append(error)
        self.valid = False

    def add_warning(self, warning: str) -> None:
        """Add a validation warning"""
        if warning not in self.warnings:
            self.warnings.append(warning)


class BasePipeline(ABC):
    """
    Abstract base class for all VaultMind Forge pipelines.

    All pipeline implementations must inherit from this class and implement
    the required methods. This ensures consistency across:

    1. forge_executor/pipeline.py - AssetPipeline (synchronous DAG)
    2. cli/workflow_engine.py - WorkflowEngine (async DAG)
    3. forge_diffusion/agent_pipeline.py - AgentPipeline (agent-integrated)
    4. backend/core/engine.py - NodeExecutionEngine (type-safe nodes)
    5. cli/distributed_executor.py - DistributedExecutor (multi-process)
    6. cli/task_decomposer.py - TaskDecomposer (task breakdown)
    7. cli/multi_modal_pipeline.py - MultiModalPipeline (multi-modal)

    Example:
        >>> class MyPipeline(BasePipeline):
        ...     async def execute(self, input: Any) -> PipelineResult:
        ...         # Implementation
        ...         return PipelineResult(success=True, outputs={})
        ...
        ...     def validate(self) -> ValidationResult:
        ...         return ValidationResult(valid=True)
        ...
        ...     def get_execution_order(self) -> List[str]:
        ...         return ["task1", "task2"]
    """

    def __init__(self):
        """Initialize base pipeline"""
        self.result: Optional[PipelineResult] = None
        self._execution_order: List[str] = []

    @abstractmethod
    async def execute(self, input: Any) -> PipelineResult:
        """
        Execute the pipeline.

        This is the main entry point for pipeline execution. Implementations
        should:
        1. Validate input
        2. Build execution order (DAG topological sort)
        3. Execute tasks/nodes in order
        4. Collect results
        5. Return PipelineResult

        Args:
            input: Pipeline input (type varies by implementation)
                  - For AssetPipeline: generation config
                  - For NodeExecutionEngine: workflow object
                  - For WorkflowEngine: task list

        Returns:
            PipelineResult with success status, outputs, and metadata

        Raises:
            PipelineValidationError: If pipeline configuration is invalid
            PipelineExecutionError: If execution fails
        """
        pass

    @abstractmethod
    def validate(self) -> ValidationResult:
        """
        Validate pipeline configuration.

        Implementations should check:
        - All required inputs are present
        - No circular dependencies (cycles in DAG)
        - Type compatibility (for typed pipelines)
        - Required resources available

        Returns:
            ValidationResult with valid flag and any errors/warnings

        Example:
            >>> pipeline = MyPipeline()
            >>> result = pipeline.validate()
            >>> if not result.valid:
            ...     print(f"Validation failed: {result.errors}")
        """
        pass

    @abstractmethod
    def get_execution_order(self) -> List[str]:
        """
        Get the execution order of tasks/nodes.

        Returns topological sort of the pipeline DAG. Used for:
        - Debugging (show what will execute)
        - Progress tracking (show current position)
        - Parallel execution planning (identify independent tasks)

        Returns:
            List of task/node IDs in execution order

        Example:
            >>> pipeline = MyPipeline()
            >>> order = pipeline.get_execution_order()
            >>> print(f"Will execute: {' → '.join(order)}")
        """
        pass

    # Optional methods with default implementations

    def get_progress(self) -> float:
        """
        Get current execution progress (0.0 to 1.0).

        Default implementation returns 0.0 or 1.0 based on result.
        Override for more granular progress tracking.

        Returns:
            Progress fraction (0.0 = not started, 1.0 = complete)
        """
        if self.result is None:
            return 0.0
        return 1.0 if self.result.success else 0.0

    def cancel(self) -> bool:
        """
        Cancel running pipeline execution.

        Default implementation returns False (not supported).
        Override to implement cancellation.

        Returns:
            True if cancelled successfully, False otherwise
        """
        return False

    def get_result(self) -> Optional[PipelineResult]:
        """
        Get the result of the last execution.

        Returns:
            PipelineResult if executed, None otherwise
        """
        return self.result

    def clear(self) -> None:
        """
        Clear cached state for re-execution.

        Resets result and execution order. Override to clear additional state.
        """
        self.result = None
        self._execution_order = []


class PipelineValidationError(Exception):
    """Raised when pipeline validation fails"""
    pass


class PipelineExecutionError(Exception):
    """Raised when pipeline execution fails"""
    pass


class PipelineCancelledException(Exception):
    """Raised when pipeline is cancelled during execution"""
    pass


# Utility functions for pipeline management

def create_pipeline_result(
    success: bool,
    outputs: Optional[Dict[str, Any]] = None,
    errors: Optional[List[str]] = None,
    **kwargs
) -> PipelineResult:
    """
    Convenience function to create PipelineResult.

    Args:
        success: Whether execution succeeded
        outputs: Dictionary of outputs (default: empty dict)
        errors: List of error messages (default: empty list)
        **kwargs: Additional fields (execution_time_ms, metadata, etc.)

    Returns:
        PipelineResult instance

    Example:
        >>> result = create_pipeline_result(
        ...     success=True,
        ...     outputs={"image": image_path},
        ...     execution_time_ms=1500.0
        ... )
    """
    return PipelineResult(
        success=success,
        outputs=outputs or {},
        errors=errors or [],
        **kwargs
    )


def merge_pipeline_results(results: List[PipelineResult]) -> PipelineResult:
    """
    Merge multiple pipeline results into one.

    Useful for parallel pipeline execution or multi-stage pipelines.

    Args:
        results: List of PipelineResult objects to merge

    Returns:
        Combined PipelineResult

    Example:
        >>> r1 = create_pipeline_result(success=True, outputs={"a": 1})
        >>> r2 = create_pipeline_result(success=True, outputs={"b": 2})
        >>> merged = merge_pipeline_results([r1, r2])
        >>> merged.outputs
        {'a': 1, 'b': 2}
    """
    if not results:
        return create_pipeline_result(success=True)

    # Merge outputs
    merged_outputs = {}
    for result in results:
        merged_outputs.update(result.outputs)

    # Merge errors
    merged_errors = []
    for result in results:
        merged_errors.extend(result.errors)

    # Merge execution order
    merged_order = []
    for result in results:
        merged_order.extend(result.execution_order)

    # Merge metadata
    merged_metadata = {}
    for result in results:
        merged_metadata.update(result.metadata)

    # Calculate total execution time
    total_time = sum(r.execution_time_ms for r in results)

    # Success if all succeeded
    success = all(r.success for r in results)

    # Get earliest start and latest finish
    start_times = [r.started_at for r in results if r.started_at]
    finish_times = [r.finished_at for r in results if r.finished_at]

    return PipelineResult(
        success=success,
        outputs=merged_outputs,
        errors=merged_errors,
        execution_time_ms=total_time,
        execution_order=merged_order,
        metadata=merged_metadata,
        started_at=min(start_times) if start_times else None,
        finished_at=max(finish_times) if finish_times else None
    )


__all__ = [
    "BasePipeline",
    "PipelineResult",
    "ValidationResult",
    "PipelineStatus",
    "PipelineValidationError",
    "PipelineExecutionError",
    "PipelineCancelledException",
    "create_pipeline_result",
    "merge_pipeline_results",
]
