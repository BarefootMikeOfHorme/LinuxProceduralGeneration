# Pipeline Unification Guide

**Created**: 2025-12-04
**Status**: Task 1 of P0 Critical Fixes - COMPLETE
**Purpose**: Guide for adapting all 7 pipelines to use unified `BasePipeline` contract

---

## Executive Summary

**Completed**: ✅ Created `BasePipeline` abstract class and adapted `NodeExecutionEngine`
**Remaining**: 6 pipelines need adaptation
**Benefit**: Consistent interface enables swapping, testing, and orchestration

---

## What Was Created

### 1. Base Pipeline Contract

**File**: `backend/core/pipeline_base.py` (360 lines)

**Core Classes**:
```python
class BasePipeline(ABC):
    @abstractmethod
    async def execute(self, input: Any) -> PipelineResult

    @abstractmethod
    def validate(self) -> ValidationResult

    @abstractmethod
    def get_execution_order(self) -> List[str]
```

**Standardized Result**:
```python
@dataclass
class PipelineResult:
    success: bool
    outputs: Dict[str, Any]
    errors: List[str]
    execution_time_ms: float
    execution_order: List[str]
    status: PipelineStatus
    metadata: Dict[str, Any]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
```

**Validation Result**:
```python
@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]
```

### 2. Updated Exports

**File**: `backend/core/__init__.py`

Now exports:
- `BasePipeline` - Abstract base class
- `PipelineResult` - Standard result type
- `ValidationResult` - Validation result type
- `PipelineStatus` - Status enum
- Helper functions: `create_pipeline_result()`, `merge_pipeline_results()`
- Exception types: `PipelineValidationError`, `PipelineExecutionError`, `PipelineCancelledException`

### 3. Reference Implementation

**File**: `backend/core/engine.py` (adapted)

`NodeExecutionEngine` now inherits from `BasePipeline`:

```python
class NodeExecutionEngine(BasePipeline):
    def __init__(self, registry: NodeRegistry):
        super().__init__()  # Call BasePipeline.__init__()
        # ... existing code

    async def execute(self, input: Any) -> PipelineResult:
        # Wraps execute_workflow()
        # Returns standardized PipelineResult

    def validate(self) -> ValidationResult:
        # Returns ValidationResult instead of raising exceptions

    def get_execution_order(self) -> List[str]:
        # Returns list of node IDs in execution order
```

**Tested and verified**:
```bash
[OK] BasePipeline imports successfully
[OK] NodeExecutionEngine imports successfully
Inheritance chain: NodeExecutionEngine -> BasePipeline -> ABC -> object
Has execute() method: True
Has validate() method: True
Has get_execution_order() method: True
```

---

## How to Adapt Remaining Pipelines

### Pipelines to Adapt

1. ✅ **backend/core/engine.py** - `NodeExecutionEngine` (DONE)
2. ⏸️ **vaultmind_forge/forge_executor/pipeline.py** - `AssetPipeline`
3. ⏸️ **vaultmind_forge/cli/workflow_engine.py** - `WorkflowEngine`
4. ⏸️ **vaultmind_forge/forge_diffusion/agent_pipeline.py** - `AgentPipeline`
5. ⏸️ **vaultmind_forge/cli/distributed_executor.py** - `DistributedExecutor`
6. ⏸️ **vaultmind_forge/cli/task_decomposer.py** - `TaskDecomposer`
7. ⏸️ **vaultmind_forge/cli/multi_modal_pipeline.py** - `MultiModalPipeline`

### Adaptation Steps

#### Step 1: Import BasePipeline

```python
# At top of file
from backend.core.pipeline_base import (
    BasePipeline,
    PipelineResult,
    ValidationResult,
    create_pipeline_result,
)
```

**Note**: This will require fixing import system (Task 2) to work without `sys.path.insert()`

#### Step 2: Inherit from BasePipeline

```python
# Before:
class MyPipeline:
    def __init__(self):
        # initialization

# After:
class MyPipeline(BasePipeline):
    def __init__(self):
        super().__init__()  # REQUIRED
        # existing initialization
```

#### Step 3: Implement execute()

```python
async def execute(self, input: Any) -> PipelineResult:
    """Execute pipeline (BasePipeline interface)"""
    started_at = datetime.utcnow()

    try:
        # Your existing execution logic
        outputs = self._run_pipeline(input)

        # Return standardized result
        return create_pipeline_result(
            success=True,
            outputs=outputs,
            execution_order=self.get_execution_order(),
            started_at=started_at,
            finished_at=datetime.utcnow(),
        )

    except Exception as e:
        return create_pipeline_result(
            success=False,
            outputs={},
            errors=[str(e)],
            started_at=started_at,
            finished_at=datetime.utcnow(),
        )
```

#### Step 4: Implement validate()

```python
def validate(self) -> ValidationResult:
    """Validate pipeline configuration"""
    result = ValidationResult(valid=True)

    # Your validation logic
    if not self.has_required_inputs():
        result.add_error("Missing required inputs")

    if self.has_circular_dependencies():
        result.add_error("Circular dependencies detected")

    return result
```

#### Step 5: Implement get_execution_order()

```python
def get_execution_order(self) -> List[str]:
    """Get execution order of tasks"""
    # If you already have topological sort:
    return self._topological_sort()

    # Or build it:
    return self._build_execution_order()
```

---

## Pipeline-Specific Adaptation Guide

### 2. AssetPipeline (forge_executor/pipeline.py)

**Current Structure**:
```python
class AssetPipeline:
    def run_generation_pipeline(self, prompt, ...) -> PipelineResult:
        # Already returns PipelineResult!
```

**Adaptation** (EASY):
1. Inherit from `BasePipeline`
2. Rename `run_generation_pipeline()` → `async def execute()`
3. Add `validate()` method (check if ai_validator is initialized)
4. Expose `get_execution_order()` (already has `_get_execution_order()`)

**Estimated Effort**: 30 minutes

---

### 3. WorkflowEngine (cli/workflow_engine.py)

**Current Structure**:
```python
class WorkflowEngine:
    async def execute(self):
        # Already async!
```

**Adaptation** (EASY):
1. Inherit from `BasePipeline`
2. Change `execute()` signature to accept `input` parameter
3. Return `PipelineResult` instead of custom result
4. Add `validate()` method
5. Add `get_execution_order()` method

**Estimated Effort**: 45 minutes

---

### 4. AgentPipeline (forge_diffusion/agent_pipeline.py)

**Current Structure**:
```python
class AgentIntegratedPipeline:
    async def execute_with_agents(self, config) -> AgentPipelineResult:
        # Agent-enhanced execution
```

**Adaptation** (MEDIUM):
1. Inherit from `BasePipeline`
2. Rename `execute_with_agents()` → `execute()`
3. Convert `AgentPipelineResult` → `PipelineResult`
   - Map agent decisions to `metadata` field
4. Add validation (check agents are initialized)
5. Add `get_execution_order()` (stages: optimize → refine → generate → validate)

**Estimated Effort**: 1 hour

---

### 5. DistributedExecutor (cli/distributed_executor.py)

**Current Structure**:
```python
class DistributedExecutor:
    def execute_distributed(self, tasks):
        # Multi-process execution
```

**Adaptation** (MEDIUM):
1. Inherit from `BasePipeline`
2. Make `execute()` async (or use `asyncio.to_thread()` for sync code)
3. Aggregate results from workers into single `PipelineResult`
4. Use `merge_pipeline_results()` helper to combine worker results
5. Add validation (check workers available)

**Estimated Effort**: 1.5 hours

---

### 6. TaskDecomposer (cli/task_decomposer.py)

**Current Structure**:
```python
class TaskDecomposer:
    def decompose(self, task) -> List[Task]:
        # Breaks tasks into subtasks
```

**Adaptation** (EASY):
1. Inherit from `BasePipeline`
2. Add `execute()` method that:
   - Calls `decompose()`
   - Returns `PipelineResult` with subtasks as outputs
3. Add validation (check task is valid)
4. `get_execution_order()` returns list of subtask IDs

**Estimated Effort**: 30 minutes

---

### 7. MultiModalPipeline (cli/multi_modal_pipeline.py)

**Current Structure**:
```python
class MultiModalPipeline:
    def process(self, modal_type, input):
        # Handles image/video/3D/audio
```

**Adaptation** (MEDIUM):
1. Inherit from `BasePipeline`
2. Rename `process()` → `execute()`
3. Return `PipelineResult` with modal outputs
4. Add validation (check modal_type supported)
5. `get_execution_order()` returns processing stages

**Estimated Effort**: 1 hour

---

## Benefits of Unification

### 1. Consistent Testing

```python
def test_any_pipeline(pipeline: BasePipeline, test_input):
    # Works with ANY pipeline!
    result = await pipeline.execute(test_input)
    assert result.success
    assert result.execution_time_ms > 0
```

### 2. Pipeline Swapping

```python
# Easy to swap implementations
pipeline = NodeExecutionEngine(registry)  # OR
pipeline = WorkflowEngine()               # OR
pipeline = AgentIntegratedPipeline()      # OR
# ... any pipeline!

result = await pipeline.execute(input)
```

### 3. Unified Orchestration

```python
class PipelineOrchestrator:
    def __init__(self, pipelines: List[BasePipeline]):
        self.pipelines = pipelines

    async def execute_all(self, input):
        results = []
        for pipeline in self.pipelines:
            result = await pipeline.execute(input)
            results.append(result)

        return merge_pipeline_results(results)
```

### 4. Progress Tracking

```python
pipeline = AssetPipeline()
execution_order = pipeline.get_execution_order()

print(f"Will execute: {' → '.join(execution_order)}")

result = await pipeline.execute(config)

print(f"Executed: {' → '.join(result.execution_order)}")
print(f"Time: {result.execution_time_ms}ms")
```

---

## Migration Priority

Based on usage and impact:

### High Priority (Do Next)
1. **AssetPipeline** - Used in production workflows
2. **WorkflowEngine** - Used by CLI and API
3. **AgentPipeline** - Critical for AI-enhanced generation

### Medium Priority
4. **DistributedExecutor** - Performance optimization
5. **MultiModalPipeline** - Multi-format support

### Low Priority
6. **TaskDecomposer** - Internal tool
7. Any undiscovered pipelines

---

## Testing Checklist

After adapting each pipeline, verify:

- ✅ Import works: `from [module] import [Pipeline]`
- ✅ Inheritance works: `isinstance(pipeline, BasePipeline)`
- ✅ All methods exist: `execute()`, `validate()`, `get_execution_order()`
- ✅ Execute returns `PipelineResult`
- ✅ Validate returns `ValidationResult`
- ✅ Execution order returns `List[str]`
- ✅ Legacy methods still work (for backwards compatibility)

**Test Script**:
```python
from backend.core import BasePipeline

def test_pipeline_contract(pipeline_class, test_input):
    # Create instance
    pipeline = pipeline_class()

    # Check inheritance
    assert isinstance(pipeline, BasePipeline)

    # Check methods exist
    assert hasattr(pipeline, 'execute')
    assert hasattr(pipeline, 'validate')
    assert hasattr(pipeline, 'get_execution_order')

    # Test validation
    validation = pipeline.validate()
    assert isinstance(validation, ValidationResult)

    # Test execution
    result = await pipeline.execute(test_input)
    assert isinstance(result, PipelineResult)
    assert isinstance(result.success, bool)
    assert isinstance(result.outputs, dict)
    assert isinstance(result.errors, list)

    print(f"✅ {pipeline_class.__name__} passes contract test")
```

---

## Next Steps

1. ✅ **Task 1 Complete**: BasePipeline contract created and tested
2. 🔄 **Task 2 In Progress**: Fix import system (removes `sys.path.insert()` hacks)
3. ⏸️ **Task 3 Pending**: Add persistence layer
4. ⏸️ **Task 4 Pending**: Integrate NativeBridge

**After Task 2 is complete**, we can adapt the remaining 6 pipelines without import issues.

---

## Summary

**Created**:
- `backend/core/pipeline_base.py` - Base contract (360 lines)
- Updated `backend/core/__init__.py` - Exports base classes
- Adapted `backend/core/engine.py` - Reference implementation

**Status**: ✅ COMPLETE
**Tested**: ✅ All imports and inheritance working
**Next**: Fix import system (Task 2)

**Total Effort for Remaining Pipelines**: ~5-6 hours (all 6 pipelines)

---

**Date Completed**: 2025-12-04
**Agent Recommendation**: This was the highest ROI task - foundation for all future improvements
