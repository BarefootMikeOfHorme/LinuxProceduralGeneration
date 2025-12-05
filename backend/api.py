"""
VaultMind Forge - FastAPI Backend
Connects web UI to Python forge_* modules
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uuid
from pathlib import Path
from datetime import datetime

# Import authentication
from backend.auth import verify_api_key, get_auth_status

# Import persistence layer
from backend.persistence import get_persistence

app = FastAPI(title="VaultMind Forge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize persistence (replaces in-memory dicts)
persistence = get_persistence()


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
async def save_workflow(workflow: WorkflowSaveRequest, api_key: str = Depends(verify_api_key)):
    workflow_id = str(uuid.uuid4())
    workflow_data = {
        "id": workflow_id,
        **workflow.dict(),
    }
    await persistence.workflows.save(workflow_id, workflow_data)
    return {"id": workflow_id, **workflow.dict()}


@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str, api_key: str = Depends(verify_api_key)):
    workflow_data = await persistence.workflows.load(workflow_id)
    if workflow_data is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow_data


@app.get("/api/workflows")
async def list_workflows(api_key: str = Depends(verify_api_key)):
    return await persistence.workflows.list_all()


@app.post("/api/execute")
async def execute_workflow(workflow: WorkflowRequest, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    execution_id = str(uuid.uuid4())

    execution_data = {
        "id": execution_id,
        "status": "running",
        "percentage": 0,
        "current_node": None,
        "results": {},
        "error": None,
    }
    await persistence.executions.save(execution_id, execution_data)

    background_tasks.add_task(run_workflow_execution, execution_id, workflow)
    return {"execution_id": execution_id}


@app.get("/api/execute/{execution_id}/progress")
async def get_execution_progress(execution_id: str, api_key: str = Depends(verify_api_key)):
    execution_data = await persistence.executions.load(execution_id)
    if execution_data is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution_data


def generate_previews(node_outputs: dict) -> dict:
    """Generate preview data for visual outputs"""
    import base64
    from io import BytesIO
    from PIL import Image as PILImage
    from pathlib import Path

    previews = {}

    for node_id, outputs in node_outputs.items():
        node_previews = {}

        for handle_name, output_data in outputs.items():
            try:
                # Handle image outputs
                if isinstance(output_data, dict) and output_data.get('type') == 'image':
                    path = output_data.get('path')
                    if path and Path(path).exists():
                        # Generate thumbnail with context manager (prevents file handle leak)
                        with PILImage.open(path) as img:
                            img.thumbnail((100, 100), PILImage.Resampling.LANCZOS)

                            # Convert to base64
                            buffer = BytesIO()
                            img.save(buffer, format='PNG')
                            thumbnail_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                            node_previews[handle_name] = {
                                'type': 'image',
                                'thumbnail': f'data:image/png;base64,{thumbnail_b64}',
                                'path': path
                            }

                # Handle video outputs
                elif isinstance(output_data, dict) and output_data.get('type') == 'video':
                    path = output_data.get('path')
                    if path:
                        node_previews[handle_name] = {
                            'type': 'video',
                            'path': path
                        }

                # Handle mesh outputs
                elif isinstance(output_data, dict) and output_data.get('type') == 'mesh':
                    path = output_data.get('path')
                    if path:
                        node_previews[handle_name] = {
                            'type': 'mesh',
                            'path': path
                        }

                # Handle text outputs
                elif isinstance(output_data, str):
                    node_previews[handle_name] = {
                        'type': 'text',
                        'text': output_data[:200]  # Truncate to 200 chars
                    }

                # Handle number outputs
                elif isinstance(output_data, (int, float)):
                    node_previews[handle_name] = {
                        'type': 'number',
                        'value': output_data
                    }

            except Exception as e:
                print(f"[FORGE] Warning: Failed to generate preview for {node_id}.{handle_name}: {e}")

        if node_previews:
            previews[node_id] = node_previews

    return previews


async def run_workflow_execution(execution_id: str, workflow: WorkflowRequest):
    """Execute workflow with NEW type-safe execution engine"""
    # Helper to update execution state
    async def update_execution(updates: dict):
        execution_data = await persistence.executions.load(execution_id)
        if execution_data:
            execution_data.update(updates)
            await persistence.executions.save(execution_id, execution_data)

    try:
        await update_execution({"status": "running", "percentage": 10})

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

        await update_execution({"percentage": 20})

        # Execute workflow (validation + topological sort + execution)
        node_outputs = engine.execute_workflow(workflow)

        await update_execution({"percentage": 90})

        print(f"[FORGE] [OK] Workflow completed successfully")
        print(f"[FORGE] Executed {len(engine.execution_order)} nodes in order: {engine.execution_order}")

        # Generate previews for visual outputs
        previews = generate_previews(node_outputs)
        print(f"[FORGE] Generated previews for {len(previews)} nodes")

        await update_execution({
            "status": "completed",
            "percentage": 100,
            "results": {
                "message": "Workflow executed successfully with NEW engine",
                "nodes_executed": len(engine.execution_order),
                "execution_order": engine.execution_order,
                "node_outputs": node_outputs,
                "previews": previews,
            }
        })

    except ValidationError as e:
        print(f"[FORGE] [ERROR] Workflow validation failed:")
        print(f"  {e}")
        await update_execution({
            "status": "failed",
            "error": f"Validation error: {e}"
        })

    except ExecutionError as e:
        print(f"[FORGE] [ERROR] Workflow execution failed:")
        print(f"  {e}")
        import traceback
        traceback.print_exc()
        await update_execution({
            "status": "failed",
            "error": f"Execution error: {e}"
        })

    except Exception as e:
        print(f"[FORGE] [ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        await update_execution({
            "status": "failed",
            "error": str(e)
        })


@app.get("/api/nodes")
async def list_available_nodes():
    """Return all available nodes from the registry"""
    from backend.core.registry import create_default_registry

    registry = create_default_registry()

    # Get all node information
    nodes = []
    for node_type in registry.list_all():
        try:
            node_info = registry.get_node_info(node_type)
            nodes.append(node_info)
        except Exception as e:
            print(f"[API] Warning: Could not get info for node {node_type}: {e}")

    return {
        "categories": registry.get_categories(),
        "nodes": nodes,
    }


@app.get("/api/health")
async def health_check():
    stats = await persistence.get_stats()
    running_executions = await persistence.executions.get_by_status("running")

    return {
        "status": "healthy",
        "workflows_count": stats["workflow_count"],
        "active_executions": len(running_executions),
        "database": {
            "path": stats["database_path"],
            "size_bytes": stats["database_size_bytes"],
            "total_executions": stats["execution_count"],
        }
    }


@app.get("/api/auth/status")
async def auth_status():
    """Get authentication status (public endpoint)"""
    return get_auth_status()


@app.get("/api/filesystem/browse")
async def browse_filesystem(path: Optional[str] = None, api_key: str = Depends(verify_api_key)):
    """Browse local filesystem with security restrictions"""
    import os
    from pathlib import Path

    # Security: Whitelist allowed root directories
    home = Path.home()
    allowed_roots = [
        home,
        home / "Desktop",
        home / "Documents",
        home / "Pictures",
        home / "Downloads",
    ]

    # Default to home directory
    if path is None:
        current_path = home
    else:
        current_path = Path(path).resolve()

    # Security check: Ensure path is within allowed roots
    is_allowed = any(
        str(current_path).startswith(str(root))
        for root in allowed_roots
    )

    if not is_allowed:
        raise HTTPException(status_code=403, detail="Access to this directory is not allowed")

    if not current_path.exists() or not current_path.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    # Collect directory items
    items = []
    try:
        for item in sorted(current_path.iterdir()):
            try:
                stat = item.stat()

                # Determine item type
                if item.is_dir():
                    item_type = "directory"
                else:
                    ext = item.suffix.lower()
                    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                        item_type = "image"
                    elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                        item_type = "video"
                    elif ext in ['.obj', '.fbx', '.glb', '.gltf', '.stl']:
                        item_type = "mesh"
                    elif ext in ['.txt', '.json', '.yaml', '.yml', '.md']:
                        item_type = "text"
                    else:
                        item_type = "file"

                items.append({
                    "name": item.name,
                    "path": str(item),
                    "type": item_type,
                    "size": stat.st_size if item.is_file() else None,
                })
            except (PermissionError, OSError):
                # Skip items we can't access
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Get parent path if exists and is allowed
    parent_path = None
    if current_path != home:
        parent = current_path.parent
        if any(str(parent).startswith(str(root)) for root in allowed_roots):
            parent_path = str(parent)

    return {
        "current_path": str(current_path),
        "parent_path": parent_path,
        "items": items,
    }


@app.get("/api/filesystem/thumbnail")
async def get_thumbnail(path: str, size: int = 200, api_key: str = Depends(verify_api_key)):
    """Generate thumbnail for image file"""
    from PIL import Image
    import base64
    from io import BytesIO

    file_path = Path(path)

    # Security check
    home = Path.home()
    allowed_roots = [home, home / "Desktop", home / "Documents", home / "Pictures", home / "Downloads"]

    is_allowed = any(str(file_path.resolve()).startswith(str(root)) for root in allowed_roots)
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Access denied")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Open and resize image with context manager (prevents file handle leak)
        with Image.open(file_path) as img:
            img.thumbnail((size, size))

            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            return {
                "thumbnail": f"data:image/png;base64,{img_base64}",
                "width": img.width,
                "height": img.height,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate thumbnail: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
