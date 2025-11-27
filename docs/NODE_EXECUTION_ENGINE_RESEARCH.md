# Node Execution Engine Research & Implementation
**Created:** 2025-11-26
**Purpose:** Fix VaultMind Forge node data flow and make nodes actually useful

---

## Problem Statement

**Current State (backend/api.py):**
- Only 4-5 of 138 nodes work
- Connections don't properly pass data
- Only text→text connections work (hardcoded)
- No type validation
- No proper handle matching

**User Testing Results:**
- 4 SDXL generations: 3 accurate, 1 hallucinated
- Accurate = direct prompt in SDXL node
- Hallucinated = tried to use Text Input → SDXL connection (failed)

**Root Cause (api.py:148-169):**
```python
# BROKEN: Only matches node IDs, not handles
for conn in workflow.connections:
    if conn.target == node.id:
        if conn.source in node_outputs:
            # HARDCODED: Only gets "text" key
            input_text = node_outputs[conn.source].get("text", input_text)
```

**Problems:**
1. ❌ Doesn't use `conn.sourceHandle` or `conn.targetHandle`
2. ❌ Hardcodes output key names ("text", "refined_prompt")
3. ❌ No type validation (can connect image to text)
4. ❌ Sequential execution (no DAG sorting)
5. ❌ No caching/deduplication

---

## Research Findings

### 1. ComfyUI Execution Engine Pattern

**Source:** [ComfyUI execution.py](https://github.com/comfyanonymous/ComfyUI/blob/master/execution.py)

**Key Concepts:**

**Recursive Execution with Output Cache:**
```python
def recursive_execute(
    server, prompt, outputs, current_item,
    extra_data, executed, prompt_id,
    outputs_ui, object_storage
):
    unique_id = current_item

    # Check if already executed (cached)
    if unique_id in outputs:
        return (True, None, None)

    # Get node inputs
    inputs = prompt[unique_id]['inputs']

    # For each input that's a connection [node_id, output_index]
    for input_name, input_data in inputs.items():
        if isinstance(input_data, list):  # Connection format
            input_unique_id = input_data[0]
            output_index = input_data[1] if len(input_data) > 1 else 0

            # Recursively execute upstream node if not cached
            if input_unique_id not in outputs:
                recursive_execute(...)

            # Get cached output
            obj = outputs[input_unique_id][output_index]

    # Execute current node
    output_data, output_ui = get_output_data(obj, prompt[unique_id])

    # Cache results
    outputs[unique_id] = output_data

    return (True, None, None)
```

**Key Insights:**
- Uses `outputs` dict as cache (key = node ID)
- Connections are `[node_id, output_index]` format
- Recursive execution ensures dependencies resolve first
- Output format: `outputs[node_id][output_slot_index]`

**Connection Format:**
```python
# Input format in prompt:
{
  "node_123": {
    "inputs": {
      "prompt": ["node_100", 0],  # [source_node_id, output_slot]
      "negative_prompt": ["node_101", 0],
      "steps": 30  # Direct value (not connection)
    }
  }
}

# Output format:
outputs = {
  "node_100": ["refined prompt text"],  # Single output
  "node_123": [<PIL.Image>, metadata]   # Multiple outputs
}
```

**Advantages:**
- ✅ Simple and efficient
- ✅ Automatic caching prevents re-execution
- ✅ Works with any data type
- ✅ Supports multiple outputs per node

**Disadvantages:**
- ⚠️ No explicit type validation
- ⚠️ Relies on numeric indices (not named handles)

---

### 2. DAG Topological Sort Pattern

**Sources:**
- [Python graphlib](https://docs.python.org/3/library/graphlib.html)
- [IPython DAG Dependencies](https://ipython-books.github.io/143-resolving-dependencies-in-a-directed-acyclic-graph-with-a-topological-sort/)
- [NetworkX DAGs](https://networkx.org/nx-guides/content/algorithms/dag/index.html)

**What is a DAG?**
Directed Acyclic Graph - nodes with directed edges, no cycles. Perfect for workflow execution.

**Topological Sort:**
Orders nodes so that for every edge A → B, node A comes before B in the list.

**Python Implementation (Built-in graphlib):**
```python
from graphlib import TopologicalSorter

# Build dependency graph
ts = TopologicalSorter()

for node in nodes:
    dependencies = []
    for conn in connections:
        if conn.target == node.id:
            dependencies.append(conn.source)

    ts.add(node.id, *dependencies)

# Get execution order
execution_order = list(ts.static_order())
# Result: ['node_1', 'node_2', 'node_3', ...]
```

**Example Workflow:**
```
Text Input (node_1)
    ↓
Prompt Refiner (node_2)
    ↓
SDXL Generator (node_3)
    ↓
Super Resolution (node_4)
```

**Execution Order:** `[node_1, node_2, node_3, node_4]`

**Advantages:**
- ✅ Guarantees correct execution order
- ✅ Built-in cycle detection (raises error if cycles exist)
- ✅ Efficient O(V + E) complexity
- ✅ Standard library (Python 3.9+)

**Disadvantages:**
- ⚠️ Doesn't support parallel execution of independent branches
- ⚠️ Requires Python 3.9+ (we're on 3.10+, so fine)

---

### 3. Type-Safe Connection Validation

**Sources:**
- [ExecutionGraph](https://github.com/gabyx/ExecutionGraph) - C++ graph execution with type safety
- [Graph Engine](https://graph.docs.tokens.studio/docs/concepts/nodes) - JSON Schema typing

**ExecutionGraph Pattern (C++):**
```cpp
// Each output socket has a type
template<typename T>
class OutputSocket {
    T data;
    SocketType type;  // e.g., DOUBLE, INT, IMAGE, etc.
};

// Can only connect if types match
bool canConnect(OutputSocket& out, InputSocket& in) {
    return out.type == in.type || in.type == ANY;
}
```

**Graph Engine Pattern (JSON Schema):**
```javascript
// Node definition with typed inputs/outputs
{
  type: 'sdxlGenerator',
  inputs: [
    { name: 'prompt', type: 'string', required: true },
    { name: 'negative', type: 'string', required: false },
    { name: 'steps', type: 'number', required: false }
  ],
  outputs: [
    { name: 'image', type: 'image' },
    { name: 'metadata', type: 'object' }
  ]
}

// Validation before connection
function validateConnection(sourceNode, sourceHandle, targetNode, targetHandle) {
  const sourceOutput = sourceNode.outputs.find(o => o.name === sourceHandle)
  const targetInput = targetNode.inputs.find(i => i.name === targetHandle)

  if (!sourceOutput || !targetInput) return false

  // Type compatibility check
  return sourceOutput.type === targetInput.type ||
         targetInput.type === 'any'
}
```

**VaultMind Forge Type System (Proposed):**
```python
from enum import Enum

class DataType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    MESH = "mesh"
    MASK = "mask"
    LATENT = "latent"
    MODEL = "model"
    NUMBER = "number"
    DICT = "dict"
    ANY = "any"

# Compatibility matrix
COMPATIBLE_TYPES = {
    DataType.TEXT: [DataType.TEXT, DataType.ANY],
    DataType.IMAGE: [DataType.IMAGE, DataType.ANY],
    DataType.MASK: [DataType.MASK, DataType.IMAGE, DataType.ANY],  # Mask can connect to image
    DataType.NUMBER: [DataType.NUMBER, DataType.ANY],
    # ... etc
}

def can_connect(source_type: DataType, target_type: DataType) -> bool:
    return target_type in COMPATIBLE_TYPES.get(source_type, [])
```

**Advantages:**
- ✅ Prevents invalid connections at design time
- ✅ Clear error messages ("Cannot connect IMAGE to TEXT")
- ✅ Extensible type system
- ✅ Some types can auto-convert (mask → image)

---

## Current Implementation Analysis

**File:** `backend/api.py` (Lines 118-263)

### Issue 1: No Handle Matching

**Current Code (Lines 151-154):**
```python
for conn in workflow.connections:
    if conn.target == node.id:
        if conn.source in node_outputs:
            input_text = node_outputs[conn.source].get("text", input_text)
```

**Problem:**
- Only checks if connection targets this node
- Doesn't check which input handle is being connected
- Assumes all inputs are called "text"

**What Should Happen:**
```python
for conn in workflow.connections:
    if conn.target == node.id and conn.targetHandle == "text":
        if conn.source in node_outputs:
            input_text = node_outputs[conn.source][conn.sourceHandle]
```

### Issue 2: Hardcoded Output Keys

**Current Code (Lines 145-146, 159-160, 200-203):**
```python
# Text Input
node_outputs[node.id] = {"text": text}

# Prompt Refiner
node_outputs[node.id] = {"refined_prompt": refined}

# SDXL Generator
node_outputs[node.id] = {"image_path": str(image_path), "prompt": prompt}
```

**Problem:**
- Each node type uses different key names
- Connection code hardcodes expected keys
- Won't work if nodes change output names

**What Should Happen:**
```python
# Standardized output format keyed by handle name
node_outputs[node.id] = {
    "text": text  # Output handle name → data
}

node_outputs[node.id] = {
    "refined_prompt": refined
}

node_outputs[node.id] = {
    "image": image_path,
    "metadata": {"prompt": prompt, ...}
}
```

### Issue 3: Sequential Execution (No DAG)

**Current Code (Line 136):**
```python
for node in workflow.nodes:
    # Execute in order received from frontend
```

**Problem:**
- Assumes frontend sends nodes in correct order
- Will fail if nodes are out of order
- No dependency resolution

**Example Failure:**
```
Frontend sends: [SDXL Generator, Text Input, Prompt Refiner]
Execution tries: SDXL → Text → Prompt (WRONG ORDER)
Result: SDXL can't find Text Input output (not executed yet)
```

**What Should Happen:**
```python
# Build dependency graph
execution_order = topological_sort(workflow.nodes, workflow.connections)
# Result: [Text Input, Prompt Refiner, SDXL Generator]

for node_id in execution_order:
    node = find_node_by_id(node_id)
    execute_node(node, ...)
```

### Issue 4: No Type Validation

**Current Code:**
- No validation at all
- Can connect anything to anything
- Runtime errors when types don't match

**Example Failure:**
```
User connects: Image Output → Text Input
Runtime error: Can't convert PIL.Image to string
```

**What Should Happen:**
```python
# Before allowing connection (frontend validation)
def validate_connection(conn, nodes):
    source_node = find_node(conn.source)
    target_node = find_node(conn.target)

    source_output = source_node.get_output_handle(conn.sourceHandle)
    target_input = target_node.get_input_handle(conn.targetHandle)

    if not can_connect(source_output.type, target_input.type):
        raise ValidationError(
            f"Cannot connect {source_output.type} to {target_input.type}"
        )
```

---

## Proposed Solution

### Architecture: Hybrid Approach

Combine the best of ComfyUI (output caching) + DAG (execution order) + Type validation:

```python
class NodeExecutionEngine:
    def __init__(self):
        self.node_outputs = {}  # Cache: {node_id: {handle: data}}
        self.node_registry = {}  # {node_type: NodeExecutor}

    def execute_workflow(self, workflow):
        # 1. Validate connections (type-safe)
        self.validate_all_connections(workflow)

        # 2. Build execution order (topological sort)
        execution_order = self.build_execution_order(workflow)

        # 3. Execute nodes in order
        for node_id in execution_order:
            node = self.find_node(workflow, node_id)
            self.execute_node(node, workflow)

        # 4. Return final outputs
        return self.node_outputs

    def execute_node(self, node, workflow):
        # Get node executor
        executor = self.node_registry[node.type]

        # Build inputs from connections + node data
        inputs = self.build_node_inputs(node, workflow)

        # Execute
        outputs = executor.execute(inputs)

        # Cache outputs by handle name
        self.node_outputs[node.id] = outputs

    def build_node_inputs(self, node, workflow):
        inputs = {}

        # Start with node's own data
        inputs.update(node.data)

        # Override with connected inputs (handle-based)
        for conn in workflow.connections:
            if conn.target == node.id:
                # Get upstream node's output
                source_output = self.node_outputs[conn.source]

                # Match handles: sourceHandle → targetHandle
                if conn.sourceHandle in source_output:
                    inputs[conn.targetHandle] = source_output[conn.sourceHandle]

        return inputs
```

### Node Executor Pattern

Each node type has a dedicated executor class:

```python
class NodeExecutor(ABC):
    @property
    @abstractmethod
    def node_type(self) -> str:
        pass

    @property
    @abstractmethod
    def input_spec(self) -> List[InputSpec]:
        pass

    @property
    @abstractmethod
    def output_spec(self) -> List[OutputSpec]:
        pass

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        pass

class InputSpec:
    name: str
    type: DataType
    required: bool = True
    default: Any = None

class OutputSpec:
    name: str
    type: DataType

# Example: SDXL Generator Executor
class SDXLGeneratorExecutor(NodeExecutor):
    node_type = "sdxlGenerator"

    input_spec = [
        InputSpec(name="prompt", type=DataType.TEXT, required=True),
        InputSpec(name="negative", type=DataType.TEXT, required=False, default=""),
        InputSpec(name="steps", type=DataType.NUMBER, required=False, default=30),
        InputSpec(name="cfg_scale", type=DataType.NUMBER, required=False, default=7.5),
    ]

    output_spec = [
        OutputSpec(name="image", type=DataType.IMAGE),
        OutputSpec(name="metadata", type=DataType.DICT),
    ]

    def execute(self, inputs):
        from vaultmind_forge.forge_diffusion.sdxl_generator import SDXLGenerator
        from vaultmind_forge.forge_diffusion.generator import GenerationConfig

        generator = SDXLGenerator()
        generator.initialize()

        config = GenerationConfig(
            prompt=inputs["prompt"],
            negative_prompt=inputs.get("negative", ""),
            width=1024,
            height=1024,
            steps=int(inputs.get("steps", 30)),
            guidance_scale=float(inputs.get("cfg_scale", 7.5))
        )

        result = generator.generate(config)

        # Save image
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        image_path = output_dir / f"sdxl_{uuid.uuid4().hex[:8]}.png"
        result.images[0].save(image_path)

        # Return outputs keyed by handle name
        return {
            "image": str(image_path),
            "metadata": {
                "prompt": inputs["prompt"],
                "steps": config.steps,
                "cfg_scale": config.guidance_scale,
                "resolution": "1024x1024",
            }
        }
```

### Topological Sort Implementation

```python
from graphlib import TopologicalSorter

def build_execution_order(self, workflow):
    """Build execution order using topological sort"""
    ts = TopologicalSorter()

    # Add all nodes with their dependencies
    for node in workflow.nodes:
        dependencies = []

        # Find all nodes that this node depends on
        for conn in workflow.connections:
            if conn.target == node.id:
                dependencies.append(conn.source)

        ts.add(node.id, *dependencies)

    # Get static order (list of node IDs)
    try:
        return list(ts.static_order())
    except CycleError:
        raise ValueError("Workflow contains cycles (circular dependencies)")
```

### Type Validation

```python
def validate_all_connections(self, workflow):
    """Validate all connections are type-safe"""
    errors = []

    for conn in workflow.connections:
        source_node = self.find_node(workflow, conn.source)
        target_node = self.find_node(workflow, conn.target)

        source_executor = self.node_registry[source_node.type]
        target_executor = self.node_registry[target_node.type]

        # Find output spec for source handle
        source_output = next(
            (o for o in source_executor.output_spec if o.name == conn.sourceHandle),
            None
        )

        # Find input spec for target handle
        target_input = next(
            (i for i in target_executor.input_spec if i.name == conn.targetHandle),
            None
        )

        if not source_output:
            errors.append(f"Node {conn.source} has no output '{conn.sourceHandle}'")

        if not target_input:
            errors.append(f"Node {conn.target} has no input '{conn.targetHandle}'")

        if source_output and target_input:
            if not can_connect(source_output.type, target_input.type):
                errors.append(
                    f"Type mismatch: Cannot connect {source_output.type.value} "
                    f"to {target_input.type.value} "
                    f"({conn.source}.{conn.sourceHandle} → {conn.target}.{conn.targetHandle})"
                )

    if errors:
        raise ValidationError("Workflow validation failed:\n" + "\n".join(errors))
```

---

## Implementation Plan

### Phase 1: Core Engine (Priority P0)

**Files to Create:**
1. `backend/core/engine.py` - Main NodeExecutionEngine class
2. `backend/core/types.py` - DataType enum, type compatibility
3. `backend/core/base_executor.py` - NodeExecutor base class, InputSpec, OutputSpec
4. `backend/core/registry.py` - Node executor registry

**Estimated Time:** 2-3 hours

### Phase 2: Node Executors (Priority P0)

**Files to Create:**
1. `backend/executors/input_nodes.py` - TextInput, FileLoader, etc.
2. `backend/executors/generation_nodes.py` - SDXLGenerator, etc.
3. `backend/executors/processing_nodes.py` - SuperResolution, etc.
4. `backend/executors/ai_nodes.py` - PromptRefiner, etc.

**Start with 10 core nodes:**
- TextInput
- NumberInput
- SDXLGenerator
- SuperResolution
- PromptRefiner
- ImageSaver
- Preview
- PreviewAndPass
- Switch
- Note

**Estimated Time:** 4-5 hours

### Phase 3: Update Backend API (Priority P0)

**Files to Modify:**
1. `backend/api.py` - Replace run_workflow_execution() with new engine

**Changes:**
```python
from backend.core.engine import NodeExecutionEngine
from backend.core.registry import create_default_registry

# Initialize engine once at startup
engine = NodeExecutionEngine(registry=create_default_registry())

async def run_workflow_execution(execution_id: str, workflow: WorkflowRequest):
    try:
        # Use new engine
        results = engine.execute_workflow(workflow)

        executions_db[execution_id]["status"] = "completed"
        executions_db[execution_id]["results"] = results

    except ValidationError as e:
        executions_db[execution_id]["status"] = "failed"
        executions_db[execution_id]["error"] = f"Validation failed: {e}"
    except Exception as e:
        executions_db[execution_id]["status"] = "failed"
        executions_db[execution_id]["error"] = str(e)
```

**Estimated Time:** 1-2 hours

### Phase 4: Testing (Priority P0)

**Test Workflows:**
1. Text Input → SDXL Generator
2. Text Input → Prompt Refiner → SDXL Generator
3. Text Input → Prompt Refiner → SDXL Generator → Super Resolution
4. Invalid connection (Image → Text) - should fail validation
5. Cyclic workflow - should fail

**Estimated Time:** 2-3 hours

**Total Phase 1-4:** 10-13 hours

### Phase 5: Expand Node Library (Priority P1)

Add remaining 108 nodes in batches:
- Batch 1: Image processing (20 nodes) - 6 hours
- Batch 2: Advanced generation (15 nodes) - 5 hours
- Batch 3: Video processing (8 nodes) - 4 hours
- Batch 4: 3D processing (10 nodes) - 5 hours
- Batch 5: Validation & utilities (20 nodes) - 6 hours
- Batch 6: Batch & automation (6 nodes) - 3 hours

**Total Phase 5:** 29 hours

**Grand Total:** 39-42 hours for complete 118-node system

---

## Success Criteria

### Functional Requirements
- ✅ All connections pass data correctly (no more hallucinations)
- ✅ Type validation prevents invalid connections
- ✅ Execution order automatically determined (topological sort)
- ✅ Support all data types (text, image, video, mesh, mask, etc.)
- ✅ Metadata propagates through workflow
- ✅ Clear error messages when validation fails

### Performance Requirements
- ⚡ Execution overhead < 100ms per node
- ⚡ Topological sort < 10ms for 100-node graph
- ⚡ Type validation < 5ms per connection
- ⚡ Memory: O(N) where N = number of nodes

### Testing Requirements
- 🧪 Unit tests for each node executor
- 🧪 Integration tests for common workflows
- 🧪 Validation tests for type errors
- 🧪 Cycle detection tests

---

## File Structure

```
backend/
├── api.py                    # FastAPI endpoints (modified)
├── core/
│   ├── __init__.py
│   ├── engine.py            # NodeExecutionEngine (NEW)
│   ├── types.py             # DataType, compatibility (NEW)
│   ├── base_executor.py     # NodeExecutor base (NEW)
│   └── registry.py          # Executor registry (NEW)
├── executors/
│   ├── __init__.py
│   ├── input_nodes.py       # Input node executors (NEW)
│   ├── generation_nodes.py  # SDXL, etc. (NEW)
│   ├── processing_nodes.py  # SR, filters, etc. (NEW)
│   ├── ai_nodes.py          # Prompt refiner, etc. (NEW)
│   ├── video_nodes.py       # Video processing (NEW)
│   ├── mesh_nodes.py        # 3D processing (NEW)
│   ├── validation_nodes.py  # Validators (NEW)
│   └── utility_nodes.py     # Preview, switch, etc. (NEW)
└── tests/
    ├── test_engine.py       # Engine tests (NEW)
    ├── test_executors.py    # Executor tests (NEW)
    └── test_workflows.py    # E2E workflow tests (NEW)
```

---

## References

**ComfyUI Execution:**
- [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI execution.py](https://github.com/comfyanonymous/ComfyUI/blob/master/execution.py)
- [ComfyUI Nodes Documentation](https://docs.comfy.org/development/core-concepts/nodes)

**DAG & Topological Sort:**
- [Python graphlib](https://docs.python.org/3/library/graphlib.html)
- [IPython DAG Tutorial](https://ipython-books.github.io/143-resolving-dependencies-in-a-directed-acyclic-graph-with-a-topological-sort/)
- [NetworkX DAG Guide](https://networkx.org/nx-guides/content/algorithms/dag/index.html)

**Type-Safe Graph Execution:**
- [ExecutionGraph (C++)](https://github.com/gabyx/ExecutionGraph)
- [Graph Engine Typing](https://graph.docs.tokens.studio/docs/concepts/nodes)

---

**Status:** ✅ Research Complete
**Next Step:** Begin Phase 1 implementation (core engine)
**Estimated Total Time:** 39-42 hours for 118 nodes

---

**END OF RESEARCH DOCUMENT**
