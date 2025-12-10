"""
VaultMind Forge - FastAPI Backend
Connects web UI to Python forge_* modules
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
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

# Import rate limiting
from backend.rate_limiter import limiter, get_rate_limit
from slowapi.errors import RateLimitExceeded

# Import logging
from backend.logging_config import setup_logging, log_exception

# Import error handling
from backend.error_handling import (
    workflow_not_found_error,
    workflow_validation_error,
    workflow_execution_error,
    execution_not_found_error,
    file_not_found_error,
    file_access_denied_error,
    internal_error
)

# Import analytics and telemetry
from backend.analytics import (
    track_workflow_started,
    track_workflow_completed,
    track_workflow_failed,
    track_node_executed,
    track_node_failed,
    get_analytics_store,
    ANALYTICS_ENABLED
)
from backend.telemetry import get_telemetry_service, TELEMETRY_ENABLED

# Import security middleware
from backend.security_middleware import configure_security_middleware
import os

# Setup logger for API
logger = setup_logging("api")

app = FastAPI(title="VaultMind Forge API", version="1.0.0")

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, limiter._rate_limit_exceeded_handler)

# Configure CORS (environment-based for security)
cors_origins = os.getenv(
    "VAULTMIND_CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Configure enterprise security middleware
configure_security_middleware(app)

# Initialize persistence (replaces in-memory dicts)
persistence = get_persistence()

# Log startup
logger.info("=" * 60)
logger.info("VaultMind Forge API Starting")
logger.info(f"Authentication: {'ENABLED' if verify_api_key else 'DISABLED'}")
logger.info(f"Rate Limiting: ENABLED")
logger.info(f"Database: {persistence.db_path}")
logger.info(f"CORS Origins: {', '.join(cors_origins)}")
logger.info(f"Analytics: {'ENABLED' if ANALYTICS_ENABLED else 'DISABLED'}")
logger.info(f"Telemetry: {'ENABLED' if TELEMETRY_ENABLED else 'DISABLED'}")
logger.info("=" * 60)


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
        logger.warning(f"Workflow not found: {workflow_id}")
        raise workflow_not_found_error(workflow_id).to_http_exception()
    return workflow_data


@app.get("/api/workflows")
async def list_workflows(api_key: str = Depends(verify_api_key)):
    return await persistence.workflows.list_all()


@app.post("/api/execute")
@limiter.limit(get_rate_limit("execute_workflow"))
async def execute_workflow(request: Request, workflow: WorkflowRequest, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
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

    # Track workflow started
    track_workflow_started(
        workflow_id=execution_id,
        node_count=len(workflow.nodes),
        session_id=request.client.host if request.client else None
    )

    background_tasks.add_task(run_workflow_execution, execution_id, workflow)
    return {"execution_id": execution_id}


@app.get("/api/execute/{execution_id}/progress")
async def get_execution_progress(execution_id: str, api_key: str = Depends(verify_api_key)):
    execution_data = await persistence.executions.load(execution_id)
    if execution_data is None:
        logger.warning(f"Execution not found: {execution_id}")
        raise execution_not_found_error(execution_id).to_http_exception()
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
                logger.warning(f"Failed to generate preview for {node_id}.{handle_name}: {e}")

        if node_previews:
            previews[node_id] = node_previews

    return previews


async def run_workflow_execution(execution_id: str, workflow: WorkflowRequest):
    """Execute workflow with NEW type-safe execution engine"""
    import time
    start_time = time.time()

    # Helper to update execution state
    async def update_execution(updates: dict):
        execution_data = await persistence.executions.load(execution_id)
        if execution_data:
            execution_data.update(updates)
            await persistence.executions.save(execution_id, execution_data)

    try:
        await update_execution({"status": "running", "percentage": 10})

        logger.info(f"Starting workflow execution: {execution_id}")
        logger.debug(f"Using NEW execution engine with type-safe connections")

        # Import the NEW execution engine
        from backend.core.engine import NodeExecutionEngine, ValidationError, ExecutionError
        from backend.core.registry import create_default_registry

        # Create engine with registered executors
        registry = create_default_registry()
        engine = NodeExecutionEngine(registry)

        logger.info(f"Loaded {registry.count()} node executors")
        logger.debug(f"Validating workflow...")

        await update_execution({"percentage": 20})

        # Execute workflow (validation + topological sort + execution)
        node_outputs = engine.execute_workflow(workflow)

        await update_execution({"percentage": 90})

        logger.info(f"Workflow completed successfully")
        logger.debug(f"Executed {len(engine.execution_order)} nodes in order: {engine.execution_order}")

        # Generate previews for visual outputs
        previews = generate_previews(node_outputs)
        logger.debug(f"Generated previews for {len(previews)} nodes")

        # Calculate duration and track success
        duration_ms = (time.time() - start_time) * 1000
        track_workflow_completed(execution_id, duration_ms)

        # Track individual node executions
        for node in workflow.nodes:
            track_node_executed(
                node_id=node.id,
                node_type=node.type,
                duration_ms=0,  # Individual node timing would require engine modification
                workflow_id=execution_id
            )

        # Optional: Send telemetry (async, non-blocking)
        if TELEMETRY_ENABLED:
            import asyncio
            telemetry = get_telemetry_service()
            asyncio.create_task(
                telemetry.track_workflow_execution(
                    node_count=len(workflow.nodes),
                    duration_ms=duration_ms,
                    success=True
                )
            )

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
        logger.error(f"Workflow validation failed: {e}")
        error_detail = workflow_validation_error(str(e)).to_dict()

        # Track failure
        track_workflow_failed(execution_id, "WORKFLOW_VALIDATION_ERROR", str(e))

        await update_execution({
            "status": "failed",
            "error": error_detail
        })

    except ExecutionError as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        error_detail = workflow_execution_error(str(e)).to_dict()

        # Track failure
        track_workflow_failed(execution_id, "WORKFLOW_EXECUTION_ERROR", str(e))

        await update_execution({
            "status": "failed",
            "error": error_detail
        })

    except Exception as e:
        logger.critical(f"Unexpected error in workflow execution: {e}", exc_info=True)
        error_detail = internal_error(str(e)).to_dict()

        # Track failure
        track_workflow_failed(execution_id, "INTERNAL_ERROR", str(e))

        await update_execution({
            "status": "failed",
            "error": error_detail
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
            logger.warning(f"Could not get info for node {node_type}: {e}")

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
@limiter.limit(get_rate_limit("browse_filesystem"))
async def browse_filesystem(request: Request, path: Optional[str] = None, api_key: str = Depends(verify_api_key)):
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
        # Security: Normalize path WITHOUT following symlinks yet
        requested_path = Path(path).absolute()

        # Security: Check if path is within allowed roots BEFORE resolving
        is_allowed = False
        for root in allowed_roots:
            try:
                # Check if requested path is relative to an allowed root
                requested_path.relative_to(root)
                is_allowed = True
                break
            except ValueError:
                continue

        if not is_allowed:
            logger.warning(f"Access denied to path: {path}")
            raise file_access_denied_error(str(requested_path)).to_http_exception()

        # Now safe to resolve (follows symlinks) since we've validated
        current_path = requested_path.resolve()

        # Double-check after resolution (symlink could point outside)
        is_still_allowed = any(
            str(current_path).startswith(str(root.resolve()))
            for root in allowed_roots
        )

        if not is_still_allowed:
            logger.warning(f"Symlink target outside allowed directories: {current_path}")
            raise file_access_denied_error(str(current_path)).to_http_exception()

    # Removed old security check - now handled above

    if not current_path.exists() or not current_path.is_dir():
        logger.warning(f"Directory not found: {current_path}")
        raise file_not_found_error(str(current_path)).to_http_exception()

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
        logger.warning(f"Permission denied accessing directory: {current_path}")
        raise file_access_denied_error(str(current_path)).to_http_exception()

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
@limiter.limit(get_rate_limit("get_thumbnail"))
async def get_thumbnail(request: Request, path: str, size: int = 200, api_key: str = Depends(verify_api_key)):
    """Generate thumbnail for image file"""
    from PIL import Image
    import base64
    from io import BytesIO

    # Security: Validate path before resolving
    home = Path.home()
    allowed_roots = [home, home / "Desktop", home / "Documents", home / "Pictures", home / "Downloads"]

    # Normalize without following symlinks
    requested_file = Path(path).absolute()

    # Check if within allowed roots BEFORE resolving
    is_allowed = False
    for root in allowed_roots:
        try:
            requested_file.relative_to(root)
            is_allowed = True
            break
        except ValueError:
            continue

    if not is_allowed:
        logger.warning(f"Access denied to thumbnail path: {path}")
        raise file_access_denied_error(str(requested_file)).to_http_exception()

    # Now safe to resolve
    file_path = requested_file.resolve()

    # Double-check after symlink resolution
    is_still_allowed = any(str(file_path).startswith(str(root.resolve())) for root in allowed_roots)
    if not is_still_allowed:
        logger.warning(f"Thumbnail symlink target outside allowed directories: {file_path}")
        raise file_access_denied_error(str(file_path)).to_http_exception()

    if not file_path.exists() or not file_path.is_file():
        logger.warning(f"Thumbnail file not found: {file_path}")
        raise file_not_found_error(str(file_path)).to_http_exception()

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
        logger.error(f"Failed to generate thumbnail for {file_path}: {e}", exc_info=True)
        raise internal_error(f"Failed to generate thumbnail: {str(e)}").to_http_exception()


# ============================================================================
# Analytics Endpoints
# ============================================================================

@app.get("/api/analytics/status")
async def get_analytics_status(api_key: str = Depends(verify_api_key)):
    """Get analytics and telemetry status"""
    telemetry = get_telemetry_service()

    return {
        "analytics": {
            "enabled": ANALYTICS_ENABLED,
            "database": str(get_analytics_store().db_path) if ANALYTICS_ENABLED else None,
        },
        "telemetry": telemetry.get_telemetry_status()
    }


@app.get("/api/analytics/stats")
async def get_analytics_stats(days: int = 7, api_key: str = Depends(verify_api_key)):
    """Get workflow execution statistics"""
    if not ANALYTICS_ENABLED:
        return {"error": "Analytics is disabled"}

    analytics = get_analytics_store()
    return analytics.get_workflow_stats(days=days)


@app.get("/api/analytics/nodes")
async def get_node_analytics(limit: int = 10, api_key: str = Depends(verify_api_key)):
    """Get node usage statistics"""
    if not ANALYTICS_ENABLED:
        return {"error": "Analytics is disabled"}

    analytics = get_analytics_store()
    return {
        "nodes": analytics.get_node_usage(limit=limit)
    }


@app.get("/api/analytics/errors")
async def get_error_analytics(days: int = 7, api_key: str = Depends(verify_api_key)):
    """Get error summary"""
    if not ANALYTICS_ENABLED:
        return {"error": "Analytics is disabled"}

    analytics = get_analytics_store()
    return {
        "errors": analytics.get_error_summary(days=days)
    }


@app.post("/api/analytics/cleanup")
async def cleanup_analytics(days: int = 90, api_key: str = Depends(verify_api_key)):
    """Clean up old analytics data"""
    if not ANALYTICS_ENABLED:
        return {"error": "Analytics is disabled"}

    analytics = get_analytics_store()
    deleted_count = analytics.cleanup_old_data(days=days)

    return {
        "message": f"Cleaned up {deleted_count} old records",
        "deleted_count": deleted_count
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
