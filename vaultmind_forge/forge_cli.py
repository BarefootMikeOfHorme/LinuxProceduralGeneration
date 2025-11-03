import typer
from pathlib import Path
from rich import print
from importlib import metadata

from .forge_agent.agent import Planner
from .forge_diffusion.generator import DiffusionGenerator, GenerationJob
from .forge_validator.validator import Validator, ValidationResult
from .forge_packaging.packager import Packager
from .forge_lineage.lineage import LineageStore

app = typer.Typer(help="VaultMind Forge CLI — orchestration & demos")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
 if ctx.invoked_subcommand is None:
 print("[bold green]VaultMind Forge[/] — run `forge --help` for commands")

@app.command("version")
def version():
 try:
 v = metadata.version("vaultmind-forge")
 print(f"[cyan]Version:[/] {v}")
 except Exception:
 print(f"[cyan]Version:[/] {__import__('vaultmind_forge').__version__} (editable)")

@app.command("status")
def status():
 root = Path(__file__).resolve().parents[1]
 modules = [p.name for p in (root / "vaultmind_forge").iterdir() if p.is_dir()]
 print("[bold]Repo root:[/]", root)
 print("[bold]Modules:[/]", ", ".join(sorted(modules)))

@app.command("run-demo")
def run_demo(output_dir: str = "demo_output"):
 """Run a minimal pipeline: plan -> generate placeholders -> validate -> package -> archive lineage"""
 out = Path(output_dir)
 out.mkdir(parents=True, exist_ok=True)
 print("[bold yellow]Starting VaultMind Forge demo pipeline[/]")

 planner = Planner()
 job = planner.plan_simple_job("demo-character", style="cel-shaded", target=(512,512))
 print("[green]Plan created:[/]", job)

 gen = DiffusionGenerator()
 assets = gen.generate(job, output_dir=out)
 print(f"[green]Generated {len(assets)} assets:[/]")
 for a in assets:
 print(" -", a)

 validator = Validator()
 results = [validator.validate_asset(a) for a in assets]
 for r in results:
 print(f"[blue]Validation:[/] {r.file} → {r.status} (score={r.score})")

 pack = Packager()
 archive_path = pack.package_assets(assets, out / "package.zip", metadata={"job": job.name})
 print("[magenta]Packaged assets to[/]", archive_path)

 lineage = LineageStore(out / "lineage")
 lineage.record_run(job=job, assets=assets, validations=results, package=str(archive_path))
 print("[bold green]Demo complete — lineage recorded.[/]")

@app.command("validate")
def validate(paths: list[str] = typer.Argument(...)):
 validator = Validator()
 for p in paths:
 r = validator.validate_asset(Path(p))
 print(f"{r.file} → {r.status} (score={r.score})")

if __name__ == "__main__":
 app()
