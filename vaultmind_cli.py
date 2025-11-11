#!/usr/bin/env python3
"""
VaultMind Forge CLI - Multi-Language AI Orchestration System

Python-based CLI that orchestrates:
- Python AI/ML operations (SDXL, agents, validation)
- Rust performance layers (terrain, mesh, physics)
- C++ optimized modules
- Node.js async orchestration

Beautiful terminal interface with comprehensive agent and process management.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import click
from rich.console import Console

from vaultmind_forge.cli.terminal_ui import TerminalUI, command_history
from vaultmind_forge.cli.agent_manager import AgentManager, AgentStatus
from vaultmind_forge.cli.process_orchestrator import ProcessOrchestrator
from vaultmind_forge.cli.stats_monitor import StatsMonitor

console = Console()

# Global context
class CLIContext:
    """CLI context holding managers"""
    def __init__(self):
        self.agent_manager = AgentManager()
        self.process_orchestrator = ProcessOrchestrator(project_root=PROJECT_ROOT)
        self.stats_monitor = StatsMonitor(self.agent_manager, self.process_orchestrator)


@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def cli(ctx):
    """
    VaultMind Forge - AI-Powered Procedural Generation Orchestrator

    Multi-language orchestration for Python AI/ML, Rust performance,
    C++ optimization, and Node.js async operations.
    """
    ctx.ensure_object(dict)
    if 'context' not in ctx.obj:
        ctx.obj['context'] = CLIContext()


@cli.command()
@click.option('--status', '-s', type=click.Choice(['running', 'paused', 'idle', 'error']),
              help="Filter agents by status")
@click.pass_context
def agents(ctx, status):
    """
    Manage and monitor AI agents

    View agent status, manage lifecycle, and monitor performance.
    """
    cli_ctx: CLIContext = ctx.obj['context']

    filter_status = AgentStatus(status) if status else None
    cli_ctx.agent_manager.show_dashboard(filter_status)

    TerminalUI.wait_for_key()


@cli.command()
@click.argument('agent_id')
@click.pass_context
def agent(ctx, agent_id):
    """
    Manage specific agent

    Detailed agent information and management interface.
    """
    cli_ctx: CLIContext = ctx.obj['context']
    cli_ctx.agent_manager.manage_agent_interactive(agent_id)


@cli.command()
@click.pass_context
def processes(ctx):
    """
    View process orchestration dashboard

    Monitor Python, Rust, C++, and Node.js process execution.
    """
    cli_ctx: CLIContext = ctx.obj['context']
    cli_ctx.process_orchestrator.show_process_dashboard()

    TerminalUI.wait_for_key()


@cli.command()
@click.pass_context
def stats(ctx):
    """
    System statistics dashboard

    CPU, RAM, GPU, agents, processes, and generation metrics.
    """
    cli_ctx: CLIContext = ctx.obj['context']
    cli_ctx.stats_monitor.display_dashboard()

    TerminalUI.wait_for_key()


@cli.command()
@click.argument('prompt', nargs=-1, required=True)
@click.option('--width', '-w', default=1024, help="Image width")
@click.option('--height', '-h', default=1024, help="Image height")
@click.option('--steps', '-s', default=30, help="Inference steps")
@click.option('--batch', '-b', default=1, help="Batch size")
@click.option('--output', '-o', default=None, help="Output directory")
@click.pass_context
def generate(ctx, prompt, width, height, steps, batch, output):
    """
    Generate images with SDXL

    Uses CUDA-accelerated SDXL generation with agent enhancement.

    Example:
        vaultmind generate a futuristic cityscape at sunset --width 1024 --height 1024
    """
    cli_ctx: CLIContext = ctx.obj['context']

    prompt_text = ' '.join(prompt)

    TerminalUI.header("SDXL Generation", f"Prompt: {prompt_text[:50]}...")

    console.print(f"[cyan]Width:[/cyan] {width}x{height}")
    console.print(f"[cyan]Steps:[/cyan] {steps}")
    console.print(f"[cyan]Batch:[/cyan] {batch}")
    console.print()

    # Execute Python SDXL generation script
    script_path = PROJECT_ROOT / "examples" / "generate_sdxl.py"

    with TerminalUI.loading("Generating with SDXL"):
        # Note: We'll create this script to wrap SDXL generation
        args = [
            "--prompt", prompt_text,
            "--width", str(width),
            "--height", str(height),
            "--steps", str(steps),
            "--batch", str(batch),
        ]

        if output:
            args.extend(["--output", output])

        # Execute via process orchestrator
        result = cli_ctx.process_orchestrator.execute_python(
            script_path=script_path,
            args=args,
            venv_path=PROJECT_ROOT / ".venv312",
            timeout=300,
        )

    if result.success:
        TerminalUI.success(f"Generation completed in {result.duration:.2f}s")
        console.print(result.stdout)
    else:
        TerminalUI.error("Generation failed")
        console.print(f"[red]{result.stderr}[/red]")


@cli.command()
@click.option('--watch', '-w', is_flag=True, help="Watch mode (refresh every 2s)")
@click.pass_context
def monitor(ctx, watch):
    """
    Real-time monitoring dashboard

    Live view of system, GPU, agents, and processes.
    """
    cli_ctx: CLIContext = ctx.obj['context']

    try:
        while True:
            cli_ctx.stats_monitor.display_dashboard()

            if not watch:
                TerminalUI.wait_for_key()
                break

            console.print("\n[dim]Press Ctrl+C to exit...[/dim]")
            time.sleep(2)

    except KeyboardInterrupt:
        TerminalUI.info("Monitoring stopped")


@cli.command()
@click.argument('language', type=click.Choice(['python', 'rust', 'cpp', 'nodejs']))
@click.argument('script_path', type=click.Path(exists=True))
@click.argument('args', nargs=-1)
@click.pass_context
def run(ctx, language, script_path, args):
    """
    Execute script/binary in any language

    Run Python scripts, Rust binaries, C++ executables, or Node.js scripts.

    Example:
        vaultmind run python scripts/test.py --arg1 value1
        vaultmind run rust ./target/release/terrain_gen input.json
    """
    cli_ctx: CLIContext = ctx.obj['context']

    TerminalUI.header(f"{language.upper()} Execution", script_path)

    script = Path(script_path)

    with TerminalUI.loading(f"Executing {script.name}"):
        if language == 'python':
            result = cli_ctx.process_orchestrator.execute_python(
                script_path=script,
                args=list(args) if args else None,
                venv_path=PROJECT_ROOT / ".venv312",
            )
        elif language == 'rust':
            result = cli_ctx.process_orchestrator.execute_rust(
                binary_path=script,
                args=list(args) if args else None,
            )
        elif language == 'cpp':
            result = cli_ctx.process_orchestrator.execute_cpp(
                binary_path=script,
                args=list(args) if args else None,
            )
        elif language == 'nodejs':
            result = cli_ctx.process_orchestrator.execute_nodejs(
                script_path=script,
                args=list(args) if args else None,
            )

    if result.success:
        TerminalUI.success(f"Execution completed in {result.duration:.2f}s")
        if result.stdout:
            console.print("\n[bold cyan]Output:[/bold cyan]")
            console.print(result.stdout)
    else:
        TerminalUI.error(f"Execution failed (exit code: {result.exit_code})")
        if result.stderr:
            console.print("\n[bold red]Error:[/bold red]")
            console.print(result.stderr)


@cli.command()
@click.pass_context
def interactive(ctx):
    """
    Start interactive shell

    REPL-style interface for VaultMind Forge commands.
    """
    cli_ctx: CLIContext = ctx.obj['context']

    TerminalUI.clear()
    TerminalUI.header("VaultMind Forge", "Interactive Mode")

    console.print("[dim]Type 'help' for commands, 'exit' to quit[/dim]\n")

    while True:
        try:
            command = TerminalUI.prompt(">")

            if not command.strip():
                continue

            command_history.add(command)

            parts = command.strip().split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            if cmd in ['exit', 'quit', 'q']:
                TerminalUI.info("Goodbye!")
                break

            elif cmd == 'help':
                _print_help()

            elif cmd == 'agents':
                cli_ctx.agent_manager.show_dashboard()
                TerminalUI.wait_for_key()

            elif cmd == 'processes':
                cli_ctx.process_orchestrator.show_process_dashboard()
                TerminalUI.wait_for_key()

            elif cmd == 'stats':
                cli_ctx.stats_monitor.display_dashboard()
                TerminalUI.wait_for_key()

            elif cmd == 'clear':
                TerminalUI.clear()

            else:
                TerminalUI.error(f"Unknown command: {cmd}")
                console.print("[dim]Type 'help' for available commands[/dim]\n")

        except KeyboardInterrupt:
            console.print()
            if TerminalUI.confirm("Exit interactive mode?"):
                break

        except Exception as e:
            TerminalUI.error(str(e))


def _print_help():
    """Print interactive mode help"""
    TerminalUI.clear()
    TerminalUI.header("VaultMind Forge Commands", "Interactive Mode Help")

    console.print("[bold cyan]Agent Management:[/bold cyan]")
    console.print("  agents          - List all agents")
    console.print("  agent <id>      - Manage specific agent")

    console.print("\n[bold cyan]Process Management:[/bold cyan]")
    console.print("  processes       - View process dashboard")
    console.print("  run <lang> <script> - Execute script")

    console.print("\n[bold cyan]Generation:[/bold cyan]")
    console.print("  generate <prompt> - Generate image with SDXL")

    console.print("\n[bold cyan]Monitoring:[/bold cyan]")
    console.print("  stats           - System statistics")
    console.print("  monitor         - Real-time monitoring")

    console.print("\n[bold cyan]General:[/bold cyan]")
    console.print("  help            - Show this help")
    console.print("  clear           - Clear screen")
    console.print("  exit            - Exit interactive mode\n")


def main():
    """Main entry point"""
    try:
        # Show banner if no command provided
        if len(sys.argv) == 1:
            TerminalUI.header(
                "VaultMind Forge CLI",
                "Multi-Language AI Orchestration System v0.1.0"
            )
            console.print("[dim]Type 'vaultmind --help' for commands[/dim]")
            console.print("[dim]Type 'vaultmind interactive' for interactive mode[/dim]\n")

        cli(obj={})

    except KeyboardInterrupt:
        console.print("\n")
        TerminalUI.info("Interrupted by user")
        sys.exit(0)

    except Exception as e:
        TerminalUI.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
