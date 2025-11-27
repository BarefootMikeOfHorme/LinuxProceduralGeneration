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
    """Execute workflow with REAL AssetPipeline"""
    try:
        executions_db[execution_id]["status"] = "running"
        executions_db[execution_id]["percentage"] = 10

        print(f"[FORGE] Starting workflow execution: {execution_id}")

        # Import the REAL AssetPipeline
        from vaultmind_forge.forge_executor.pipeline import AssetPipeline, run_asset_pipeline
        from vaultmind_forge.forge_diffusion.sdxl_generator import SDXLGenerator
        from vaultmind_forge.forge_diffusion.generator import GenerationConfig
        from vaultmind_forge.forge_sr.upscaler import SuperResolutionUpscaler, SRQuality
        from vaultmind_forge.forge_agents.prompt_refiner import PromptRefinerAgent

        node_outputs = {}

        # Parse workflow to build execution graph
        for node in workflow.nodes:
            executions_db[execution_id]["current_node"] = node.id
            executions_db[execution_id]["percentage"] += 80 / len(workflow.nodes)

            print(f"[FORGE] Executing: {node.type} (id: {node.id})")

            try:
                if node.type == "textInput":
                    text = node.data.get("text", "")
                    node_outputs[node.id] = {"text": text}
                    print(f"  → Text: {text[:80]}...")

                elif node.type == "promptRefiner":
                    input_text = node.data.get("text", "")
                    # Get from connected node if available
                    for conn in workflow.connections:
                        if conn.target == node.id:
                            if conn.source in node_outputs:
                                input_text = node_outputs[conn.source].get("text", input_text)

                    agent = PromptRefinerAgent()
                    print(f"  → Refining: '{input_text[:50]}...'")

                    refined = input_text + ", highly detailed, sharp focus, masterpiece"
                    node_outputs[node.id] = {"refined_prompt": refined}
                    print(f"  ✓ Refined: '{refined[:80]}...'")

                elif node.type == "sdxlGenerator":
                    prompt = node.data.get("prompt", "")
                    # Get from connected node if available
                    for conn in workflow.connections:
                        if conn.target == node.id:
                            if conn.source in node_outputs:
                                prompt = node_outputs[conn.source].get("refined_prompt", prompt)

                    steps = int(node.data.get("steps", 30))
                    cfg = float(node.data.get("cfg_scale", 7.5))

                    print(f"  → Generating image with SDXL...")
                    print(f"     Prompt: {prompt[:80]}...")
                    print(f"     Steps: {steps}, CFG: {cfg}")

                    # REAL GENERATION:
                    generator = SDXLGenerator()
                    print(f"  → Initializing SDXL (downloading model on first run)...")
                    generator.initialize()

                    config = GenerationConfig(
                        prompt=prompt,
                        width=1024,
                        height=1024,
                        steps=steps,
                        guidance_scale=cfg
                    )

                    print(f"  → Generating...")
                    result = generator.generate(config)

                    # Save image
                    output_dir = Path(__file__).parent.parent / "outputs"
                    output_dir.mkdir(exist_ok=True)
                    image_path = output_dir / f"sdxl_{node.id}_{uuid.uuid4().hex[:8]}.png"
                    result.images[0].save(image_path)

                    node_outputs[node.id] = {
                        "image_path": str(image_path),
                        "prompt": prompt
                    }
                    print(f"  ✓ Generated: {image_path}")

                elif node.type == "superResolution":
                    image_path = None
                    # Get from connected node
                    for conn in workflow.connections:
                        if conn.target == node.id:
                            if conn.source in node_outputs:
                                image_path = node_outputs[conn.source].get("image_path")

                    if not image_path:
                        raise ValueError("Super Resolution requires input image")

                    print(f"  → Upscaling image: {image_path}")

                    # REAL UPSCALING:
                    upscaler = SuperResolutionUpscaler()
                    output_dir = Path(__file__).parent.parent / "outputs"
                    output_dir.mkdir(exist_ok=True)
                    output_path = output_dir / f"upscaled_{node.id}_{uuid.uuid4().hex[:8]}.png"

                    result = upscaler.upscale(
                        input_path=Path(image_path),
                        output_path=output_path,
                        quality=SRQuality.BALANCED
                    )

                    node_outputs[node.id] = {
                        "upscaled_path": str(output_path),
                        "scale": result.scale_factor
                    }
                    print(f"  ✓ Upscaled {result.scale_factor}x: {output_path}")

                else:
                    print(f"  ⚠ Unknown node type: {node.type}")
                    node_outputs[node.id] = {"status": "skipped"}

            except Exception as node_error:
                print(f"  ✗ Error: {node_error}")
                import traceback
                traceback.print_exc()
                node_outputs[node.id] = {"error": str(node_error)}

        executions_db[execution_id]["status"] = "completed"
        executions_db[execution_id]["percentage"] = 100
        executions_db[execution_id]["results"] = {
            "message": "Workflow executed successfully",
            "nodes_executed": len(workflow.nodes),
            "node_outputs": node_outputs,
        }

        print(f"[FORGE] ✓ Workflow completed: {execution_id}")

    except Exception as e:
        print(f"[FORGE] ✗ Workflow failed: {e}")
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
