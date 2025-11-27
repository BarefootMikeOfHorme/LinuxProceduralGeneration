"""
VaultMind Forge - FastAPI Backend
Connects web UI to Python forge_* modules
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uuid
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

app = FastAPI(title="VaultMind Forge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

workflows_db: Dict[str, Dict] = {}
executions_db: Dict[str, Dict] = {}


class NodeData(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]


class Connection(BaseModel):
    source: str
    sourceHandle: str
    target: str
    targetHandle: str


class WorkflowRequest(BaseModel):
    nodes: List[NodeData]
    connections: List[Connection]


class WorkflowMetadata(BaseModel):
    name: str
    description: str
    created: Optional[str] = None
    author: Optional[str] = "user"


class WorkflowSaveRequest(BaseModel):
    version: int = 1
    metadata: WorkflowMetadata
    nodes: List[Dict]
    connections: List[Dict]


@app.get("/")
async def root():
    return {
        "name": "VaultMind Forge API",
        "version": "1.0.0",
        "status": "running",
    }


@app.post("/api/workflows")
async def save_workflow(workflow: WorkflowSaveRequest):
    workflow_id = str(uuid.uuid4())
    workflows_db[workflow_id] = {
        "id": workflow_id,
        **workflow.dict(),
    }
    return {"id": workflow_id, **workflow.dict()}


@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflows_db[workflow_id]


@app.get("/api/workflows")
async def list_workflows():
    return list(workflows_db.values())


@app.post("/api/execute")
async def execute_workflow(workflow: WorkflowRequest, background_tasks: BackgroundTasks):
    execution_id = str(uuid.uuid4())
    
    executions_db[execution_id] = {
        "id": execution_id,
        "status": "running",
        "percentage": 0,
        "current_node": None,
        "results": {},
        "error": None,
    }
    
    background_tasks.add_task(run_workflow_execution, execution_id, workflow)
    return {"execution_id": execution_id}


@app.get("/api/execute/{execution_id}/progress")
async def get_execution_progress(execution_id: str):
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")
    return executions_db[execution_id]


async def run_workflow_execution(execution_id: str, workflow: WorkflowRequest):
    """Execute workflow with NEW type-safe execution engine"""
    try:
        executions_db[execution_id]["status"] = "running"
        executions_db[execution_id]["percentage"] = 10

        print(f"[FORGE] Starting workflow execution: {execution_id}")
        print(f"[FORGE] Using NEW execution engine with type-safe connections")

        # Import the NEW execution engine
        from backend.core.engine import NodeExecutionEngine, ValidationError, ExecutionError
        from backend.core.registry import create_default_registry

        # Create engine with registered executors
        registry = create_default_registry()
        engine = NodeExecutionEngine(registry)

        print(f"[FORGE] Loaded {registry.count()} node executors")
        print(f"[FORGE] Validating workflow...")

        executions_db[execution_id]["percentage"] = 20

        # Execute workflow (validation + topological sort + execution)
        node_outputs = engine.execute_workflow(workflow)

        executions_db[execution_id]["percentage"] = 90

        print(f"[FORGE] [OK] Workflow completed successfully")
        print(f"[FORGE] Executed {len(engine.execution_order)} nodes in order: {engine.execution_order}")

        executions_db[execution_id]["status"] = "completed"
        executions_db[execution_id]["percentage"] = 100
        executions_db[execution_id]["results"] = {
            "message": "Workflow executed successfully with NEW engine",
            "nodes_executed": len(engine.execution_order),
            "execution_order": engine.execution_order,
            "node_outputs": node_outputs,
        }

    except ValidationError as e:
        print(f"[FORGE] [ERROR] Workflow validation failed:")
        print(f"  {e}")
        executions_db[execution_id]["status"] = "failed"
        executions_db[execution_id]["error"] = f"Validation error: {e}"

    except ExecutionError as e:
        print(f"[FORGE] [ERROR] Workflow execution failed:")
        print(f"  {e}")
        import traceback
        traceback.print_exc()
        executions_db[execution_id]["status"] = "failed"
        executions_db[execution_id]["error"] = f"Execution error: {e}"

    except Exception as e:
        print(f"[FORGE] [ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        executions_db[execution_id]["status"] = "failed"
        executions_db[execution_id]["error"] = str(e)


@app.get("/api/nodes")
async def list_available_nodes():
    return {
        "categories": ["input", "generation", "enhancement", "ai_agent", "validation", "processing", "output", "utility"],
        "nodes": [],
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "workflows_count": len(workflows_db),
        "active_executions": len([e for e in executions_db.values() if e["status"] == "running"]),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
