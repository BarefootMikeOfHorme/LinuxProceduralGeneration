import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from . import __version__
from .forge_validator.evaluators import MetricThresholds, ThreePassRunner
from .forge_validator.metrics import compute_metrics
from .forge_lineage.logger import LineageLogger
from .forge_cli.html_report import write_html_report

app = typer.Typer(add_completion=False, help="VaultMind Forge CLI")
console = Console()

@app.callback()
def main_callback():
    pass

@app.command()
def version():
    console.print(f"VaultMind Forge v{__version__}")

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
        html_out = write_html_report(job_id, reports, diagnostics, root / "lineage_logs" / "reports")
        console.print(f"HTML report: {html_out}")

    archive = lineage.finalize(job_id, written)
    console.print(f"Wrote {len(written)} pass reports; archive listing: {archive}")