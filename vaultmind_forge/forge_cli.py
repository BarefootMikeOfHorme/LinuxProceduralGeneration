import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from . import __version__
from .forge_validator.evaluators import MetricThresholds, ThreePassRunner
from .forge_validator.metrics import compute_metrics
from .forge_lineage.logger import LineageLogger

app = typer.Typer(add_completion=False, help="VaultMind Forge CLI")
console = Console()

@app.callback()
def main_callback():
    pass

@app.command()
def version():
    console.print(f"VaultMind Forge v{__version__}")

@app.command()
def logo(style: str = typer.Option("compact", help="Logo style: compact, simple, full")):
    """Display VaultMind Forge ASCII art logo"""
    from .forge_ascii_art import print_logo
    print_logo(console, style=style)

@app.command()
def monitor(
    refresh: float = typer.Option(1.0, help="Refresh rate in seconds"),
):
    """Launch live monitoring dashboard with real-time system stats"""
    from .forge_monitor_tui import run_monitor
    from .forge_ascii_art import print_logo

    print_logo(console, style="compact")
    console.print()
    console.print("[cyan]Starting VaultMind Forge Live Dashboard...[/cyan]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")

    run_monitor(refresh_rate=refresh)

@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Text prompt for generation"),
    output: Path = typer.Option("./output.png", help="Output file path"),
    steps: int = typer.Option(30, help="Number of denoising steps"),
    width: int = typer.Option(1024, help="Image width"),
    height: int = typer.Option(1024, help="Image height"),
    cfg_scale: float = typer.Option(7.5, help="CFG scale"),
    fui: bool = typer.Option(True, help="Use FUI styling (disable for plain output)"),
):
    """Generate an image from a text prompt using SDXL"""
    from .forge_diffusion.sdxl_generator import SDXLGenerator
    from .forge_diffusion.generator import GenerationConfig
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

    if fui:
        # FUI MODE
        console.print()
        console.rule("[bold yellow]SDXL GENERATION[/bold yellow]", style="yellow")
        console.print()

        # Generation Config Panel
        config_table = Table.grid(padding=(0, 2))
        config_table.add_column(style="dim yellow")
        config_table.add_column(style="white")

        config_table.add_row("PROMPT", prompt[:60] + "..." if len(prompt) > 60 else prompt)
        config_table.add_row("STEPS", str(steps))
        config_table.add_row("SIZE", f"{width}x{height}")
        config_table.add_row("CFG SCALE", str(cfg_scale))
        config_table.add_row("OUTPUT", str(output))

        config_panel = Panel(
            config_table,
            title="[yellow]GENERATION CONFIG[/yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print(config_panel)
        console.print()

        # Initialization
        with Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[cyan]{task.description}[/cyan]"),
            console=console
        ) as progress:
            task = progress.add_task("INITIALIZING SDXL MODEL", total=None)
            generator = SDXLGenerator()
            generator.initialize()
            progress.update(task, completed=True)

        console.print("[green]>> MODEL LOADED[/green]")
        console.print()

        # Generation
        config = GenerationConfig(
            prompt=prompt,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=cfg_scale
        )

        console.rule("[yellow]GENERATION PHASE[/yellow]", style="yellow")
        console.print()

        with Progress(
            SpinnerColumn(style="yellow"),
            TextColumn("[yellow]{task.description}[/yellow]"),
            BarColumn(complete_style="yellow", finished_style="green"),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"GENERATING IMAGE ({steps} steps)", total=steps)
            result = generator.generate(config)
            progress.update(task, completed=steps)

        result.images[0].save(output)

        console.print()
        console.print("[green]>> GENERATION COMPLETE[/green]")
        console.print()

        # Output Panel
        output_table = Table.grid(padding=(0, 2))
        output_table.add_column(style="dim green")
        output_table.add_column(style="white")

        output_table.add_row("FILE", str(output))
        output_table.add_row("SIZE", f"{width}x{height}")

        output_panel = Panel(
            output_table,
            title="[green]OUTPUT[/green]",
            border_style="green",
            padding=(1, 2)
        )
        console.print(output_panel)
        console.print()
        console.rule("[bold green]COMPLETE[/bold green]", style="green")

    else:
        # Plain output mode
        console.print(f"[cyan]Generating:[/cyan] {prompt}")
        console.print(f"[dim]Steps: {steps}, Size: {width}x{height}, CFG: {cfg_scale}[/dim]")

        with console.status("[bold green]Initializing SDXL..."):
            generator = SDXLGenerator()
            generator.initialize()

        config = GenerationConfig(
            prompt=prompt,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=cfg_scale
        )

        with console.status(f"[bold green]Generating image ({steps} steps)..."):
            result = generator.generate(config)

        result.images[0].save(output)
        console.print(f"[green]Saved:[/green] {output}")

@app.command()
def workflow(
    workflow_file: Path = typer.Argument(..., exists=True, readable=True, help="Workflow JSON file"),
    output_dir: Path = typer.Option("./outputs", help="Output directory"),
    fui: bool = typer.Option(True, help="Use FUI styling (disable for plain output)"),
):
    """Execute a workflow from JSON file"""
    import json
    import sys
    import time
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from backend.core.engine import NodeExecutionEngine, ValidationError, ExecutionError
    from backend.core.registry import create_default_registry
    from pydantic import BaseModel
    from typing import List, Dict, Any
    from rich.panel import Panel
    from rich.table import Table
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.text import Text
    from rich.tree import Tree

    # Define workflow models
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

    # Load workflow
    workflow_data = json.loads(workflow_file.read_text())
    workflow = WorkflowRequest(**workflow_data)

    if not fui:
        # Plain output mode
        console.print(f"[cyan]Executing workflow:[/cyan] {workflow_file}")
        console.print(f"[dim]Nodes: {len(workflow.nodes)}, Connections: {len(workflow.connections)}[/dim]")

    # Create engine
    registry = create_default_registry()
    engine = NodeExecutionEngine(registry)

    if fui:
        # FUI MODE - Holographic terminal interface
        console.print()
        console.rule("[bold cyan]VAULTMIND FORGE[/bold cyan] EXECUTION ENGINE", style="cyan")
        console.print()

        # System Info Panel
        import platform
        import psutil

        system_table = Table.grid(padding=(0, 2))
        system_table.add_column(style="dim cyan")
        system_table.add_column(style="white")

        system_table.add_row("SYSTEM", platform.system())
        system_table.add_row("CPU", f"{psutil.cpu_count()} cores @ {psutil.cpu_percent()}%")
        system_table.add_row("MEMORY", f"{psutil.virtual_memory().percent}% used")
        system_table.add_row("EXECUTORS", f"{registry.count()} registered")

        system_panel = Panel(
            system_table,
            title="[cyan]SYSTEM STATUS[/cyan]",
            border_style="cyan",
            padding=(1, 2)
        )

        # Workflow Info Panel
        workflow_table = Table.grid(padding=(0, 2))
        workflow_table.add_column(style="dim magenta")
        workflow_table.add_column(style="white")

        workflow_table.add_row("FILE", str(workflow_file.name))
        workflow_table.add_row("NODES", str(len(workflow.nodes)))
        workflow_table.add_row("CONNECTIONS", str(len(workflow.connections)))
        workflow_table.add_row("OUTPUT DIR", str(output_dir))

        workflow_panel = Panel(
            workflow_table,
            title="[magenta]WORKFLOW CONFIG[/magenta]",
            border_style="magenta",
            padding=(1, 2)
        )

        # Print top panels side by side
        from rich.columns import Columns
        console.print(Columns([system_panel, workflow_panel], equal=True))
        console.print()

    try:
        if fui:
            # Validation with FUI
            with Progress(
                SpinnerColumn(style="cyan"),
                TextColumn("[cyan]{task.description}[/cyan]"),
                console=console
            ) as progress:
                task = progress.add_task("VALIDATING WORKFLOW", total=None)
                engine.validate_workflow(workflow)
                progress.update(task, completed=True)

            console.print("[green]>> VALIDATION PASSED[/green]")
            console.print()
        else:
            with console.status("[bold green]Validating workflow..."):
                engine.validate_workflow(workflow)
            console.print("[green]Validation passed[/green]")

        if fui:
            # Execution with FUI progress
            console.rule("[yellow]EXECUTION PHASE[/yellow]", style="yellow")
            console.print()

            # Build workflow graph tree
            graph_tree = Tree("[yellow]WORKFLOW GRAPH[/yellow]")

            # Add nodes
            for node in workflow.nodes:
                node_branch = graph_tree.add(f"[cyan]{node.id}[/cyan] ({node.type})")
                # Find connections from this node
                for conn in workflow.connections:
                    if conn.source == node.id:
                        node_branch.add(f"[dim]-> {conn.target} via {conn.sourceHandle}[/dim]")

            console.print(graph_tree)
            console.print()

            with Progress(
                SpinnerColumn(style="yellow"),
                TextColumn("[yellow]{task.description}[/yellow]"),
                BarColumn(complete_style="yellow", finished_style="green"),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("EXECUTING NODES", total=len(workflow.nodes))

                # Execute workflow (this validates and sorts internally)
                results = engine.execute_workflow(workflow)

                progress.update(task, completed=len(workflow.nodes))

            console.print()
            console.print("[green]>> EXECUTION COMPLETE[/green]")
            console.print()
        else:
            with console.status("[bold green]Executing workflow..."):
                results = engine.execute_workflow(workflow)
            console.print(f"[green]Workflow completed![/green]")

        if fui:
            # Execution Order Panel
            order_text = Text()
            for i, node_id in enumerate(engine.execution_order):
                if i > 0:
                    order_text.append(" -> ", style="dim")
                order_text.append(node_id, style="cyan")

            order_panel = Panel(
                order_text,
                title="[yellow]EXECUTION ORDER[/yellow]",
                border_style="yellow",
                padding=(1, 2)
            )
            console.print(order_panel)
            console.print()

            # Results Panel
            console.rule("[green]OUTPUT RESULTS[/green]", style="green")
            console.print()

            for node_id, outputs in results.items():
                result_table = Table(show_header=True, header_style="bold green", border_style="green")
                result_table.add_column("Output", style="dim")
                result_table.add_column("Value", style="white")

                for key, value in outputs.items():
                    if isinstance(value, str) and len(value) < 100:
                        result_table.add_row(key, value)
                    elif isinstance(value, dict):
                        result_table.add_row(key, "[dim]{metadata}[/dim]")
                    else:
                        result_table.add_row(key, "[dim]<data>[/dim]")

                result_panel = Panel(
                    result_table,
                    title=f"[green]{node_id}[/green]",
                    border_style="green",
                    padding=(1, 2)
                )
                console.print(result_panel)

            console.print()
            console.rule("[bold green]WORKFLOW COMPLETE[/bold green]", style="green")
        else:
            # Plain output
            console.print(f"[dim]Execution order: {engine.execution_order}[/dim]")
            for node_id, outputs in results.items():
                console.print(f"\n[cyan]{node_id}:[/cyan]")
                for key, value in outputs.items():
                    if isinstance(value, str) and len(value) < 100:
                        console.print(f"  {key}: {value}")
                    elif isinstance(value, dict):
                        console.print(f"  {key}: {{metadata}}")
                    else:
                        console.print(f"  {key}: <data>")

    except ValidationError as e:
        if fui:
            error_panel = Panel(
                f"[red]{e}[/red]",
                title="[bold red]VALIDATION ERROR[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            console.print(error_panel)
        else:
            console.print(f"[red]Validation failed:[/red]")
            console.print(f"{e}")
        raise typer.Exit(code=1)

    except ExecutionError as e:
        if fui:
            error_panel = Panel(
                f"[red]{e}[/red]",
                title="[bold red]EXECUTION ERROR[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            console.print(error_panel)
        else:
            console.print(f"[red]Execution failed:[/red]")
            console.print(f"{e}")
        raise typer.Exit(code=1)

@app.command()
def validate(config: Path = typer.Argument(..., exists=True, readable=True)):
    import json
    from jsonschema import Draft202012Validator
    schema_path = Path(__file__).resolve().parents[1] / "config" / "schemas" / "job.schema.json"
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    instance = json.loads(Path(config).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda e: e.path)
    if errors:
        for e in errors:
            console.print(f"[red]Error:[/red] {list(e.path)} -> {e.message}")
        raise typer.Exit(code=1)
    console.print("[green]Valid configuration[/green]")

@app.command()
def evaluate(
    config: Path = typer.Argument(..., exists=True, readable=True),
    asset: Path = typer.Option(..., exists=True, readable=True, help="Path to asset (image) to evaluate"),
    color_ref: Optional[Path] = typer.Option(None, help="Optional reference image for color fidelity"),
    html_report: bool = typer.Option(False, help="Write HTML report (default off)"),
    studio: bool = typer.Option(False, help="Studio mode: more verbose diagnostics"),
    prefer_rust: bool = typer.Option(False, help="Prefer Rust backends when available"),
    prefer_cpp: bool = typer.Option(False, help="Prefer C++ backends when available"),
):
    job = json.loads(Path(config).read_text(encoding="utf-8"))
    job_id = job.get("id", "job")

    metrics, diagnostics = compute_metrics(asset, color_ref)

    base = MetricThresholds(0.50, 0.55, 0.60, 0.65, 0.60)
    buildup = MetricThresholds(0.60, 0.65, 0.70, 0.75, 0.70)
    refined = MetricThresholds(0.70, 0.75, 0.80, 0.85, 0.80)
    runner = ThreePassRunner(base, buildup, refined)

    samples = {"base": metrics, "buildup": metrics, "refined": metrics}

    reports = runner.run(samples)
    root = Path(__file__).resolve().parents[1]
    lineage = LineageLogger(root)
    written = []
    for rep in reports:
        decision = rep["decision"]
        rep_dict = {
            "job_id": job_id,
            **rep,
            "diagnostics": diagnostics if studio else {},
        }
        path = lineage.write_report(job_id, rep["pass"], decision, rep_dict)
        lineage.write_diagnostics(job_id, rep["pass"], diagnostics)
        written.append(path)

    if html_report:
        from vaultmind_forge.forge_cli.html_report import write_html_report
        html_out = write_html_report(job_id, reports, diagnostics, root / "lineage_logs" / "reports")
        console.print(f"HTML report: {html_out}")

    archive = lineage.finalize(job_id, written)
    console.print(f"Wrote {len(written)} pass reports; archive listing: {archive}")