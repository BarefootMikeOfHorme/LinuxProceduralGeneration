"""
VaultMind Forge - Live Dashboard TUI
Real-time monitoring with FUI aesthetics
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import psutil
import platform

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from rich.tree import Tree
from rich.box import ROUNDED


class ForgeMonitorTUI:
    """Live dashboard for VaultMind Forge with real-time updates"""

    def __init__(self, refresh_rate: float = 1.0):
        self.console = Console()
        self.refresh_rate = refresh_rate
        self.start_time = datetime.now()
        self.workflow_count = 0
        self.output_count = 0
        self.outputs_dir = Path("outputs")

    def get_system_stats(self) -> Table:
        """Get real-time system statistics"""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="dim cyan", justify="right")
        table.add_column(style="white bold")
        table.add_column(style="dim")

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_bar = self._create_bar(cpu_percent, "cyan")
        table.add_row("CPU", f"{cpu_percent:5.1f}%", cpu_bar)

        # Memory
        mem = psutil.virtual_memory()
        mem_bar = self._create_bar(mem.percent, "magenta")
        table.add_row("MEMORY", f"{mem.percent:5.1f}%", mem_bar)

        # Disk
        disk = psutil.disk_usage('/')
        disk_bar = self._create_bar(disk.percent, "yellow")
        table.add_row("DISK", f"{disk.percent:5.1f}%", disk_bar)

        # GPU (if available)
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_bar = self._create_bar(gpu.load * 100, "green")
                table.add_row("GPU", f"{gpu.load*100:5.1f}%", gpu_bar)
                table.add_row("VRAM", f"{gpu.memoryUsed}MB / {gpu.memoryTotal}MB", "")
                table.add_row("TEMP", f"{gpu.temperature}°C", "")
        except (ImportError, Exception):
            table.add_row("GPU", "N/A", "[dim]no GPUtil[/dim]")

        # Network
        net = psutil.net_io_counters()
        table.add_row("NET ↓", f"{net.bytes_recv / 1024 / 1024:.1f} MB", "")
        table.add_row("NET ↑", f"{net.bytes_sent / 1024 / 1024:.1f} MB", "")

        return table

    def _create_bar(self, percent: float, color: str) -> str:
        """Create ASCII progress bar"""
        width = 20
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)

        # Color based on percentage
        if percent < 50:
            style = f"[{color}]{bar}[/{color}]"
        elif percent < 80:
            style = f"[yellow]{bar}[/yellow]"
        else:
            style = f"[red]{bar}[/red]"

        return style

    def get_active_workflows(self) -> Table:
        """Get currently active workflows"""
        table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        table.add_column("Workflow", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Progress", style="white")
        table.add_column("Time", style="dim")

        # TODO: Connect to backend API to get real workflows
        # For now, show placeholder
        if self.workflow_count == 0:
            table.add_row("[dim]No active workflows[/dim]", "", "", "")
        else:
            table.add_row("sdxl_generation_001", "RUNNING", "████████████░░░░░░░░ 60%", "2m 15s")
            table.add_row("upscale_batch_042", "QUEUED", "░░░░░░░░░░░░░░░░░░░░ 0%", "0s")

        return table

    def get_recent_outputs(self) -> Table:
        """Get recent generated outputs"""
        table = Table(show_header=True, header_style="bold green", border_style="green")
        table.add_column("File", style="green")
        table.add_column("Size", style="white")
        table.add_column("Time", style="dim")

        # Get actual output files
        if self.outputs_dir.exists():
            files = sorted(self.outputs_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]

            if not files:
                table.add_row("[dim]No outputs yet[/dim]", "", "")
            else:
                for f in files:
                    stat = f.stat()
                    size = stat.st_size / 1024 / 1024  # MB
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    time_ago = self._time_ago(mtime)
                    table.add_row(f.name, f"{size:.2f} MB", time_ago)
        else:
            table.add_row("[dim]outputs/ directory not found[/dim]", "", "")

        return table

    def _time_ago(self, dt: datetime) -> str:
        """Convert datetime to 'X ago' format"""
        delta = datetime.now() - dt

        if delta.seconds < 60:
            return f"{delta.seconds}s ago"
        elif delta.seconds < 3600:
            return f"{delta.seconds // 60}m ago"
        elif delta.seconds < 86400:
            return f"{delta.seconds // 3600}h ago"
        else:
            return f"{delta.days}d ago"

    def get_system_info(self) -> Table:
        """Get static system information"""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="dim cyan")
        table.add_column(style="white")

        table.add_row("PLATFORM", platform.system())
        table.add_row("PYTHON", platform.python_version())
        table.add_row("CPU COUNT", str(psutil.cpu_count()))
        table.add_row("TOTAL RAM", f"{psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")

        uptime = datetime.now() - self.start_time
        table.add_row("UPTIME", f"{uptime.seconds // 60}m {uptime.seconds % 60}s")

        return table

    def get_workflow_tree(self) -> Tree:
        """Get ASCII workflow tree visualization"""
        tree = Tree("[yellow]WORKFLOW GRAPH[/yellow]")

        # TODO: Get real workflow data from backend
        # For now, show example
        node1 = tree.add("[cyan]textInput_1[/cyan] (textInput)")
        node1.add("[dim]→ promptRefiner_1[/dim]")

        node2 = tree.add("[cyan]promptRefiner_1[/cyan] (promptRefiner)")
        node2.add("[dim]→ sdxl_1[/dim]")

        node3 = tree.add("[cyan]sdxl_1[/cyan] (sdxlGenerator)")
        node3.add("[green]✓ output: image.png[/green]")

        return tree

    def create_layout(self) -> Layout:
        """Create the main dashboard layout"""
        layout = Layout(name="root")

        # Split into header and body
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )

        # Split body into left and right
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2)
        )

        # Split left into system and info
        layout["left"].split(
            Layout(name="system", ratio=2),
            Layout(name="info", ratio=1)
        )

        # Split right into workflows and outputs
        layout["right"].split(
            Layout(name="workflows", ratio=1),
            Layout(name="outputs", ratio=1),
            Layout(name="graph", ratio=1)
        )

        return layout

    def render(self) -> Layout:
        """Render the complete dashboard"""
        layout = self.create_layout()

        # Header
        header_text = Text()
        header_text.append("╔═══════════════════════════════════════════════════════════════════╗\n", style="cyan")
        header_text.append("║ ", style="cyan")
        header_text.append("VAULTMIND FORGE", style="bold cyan")
        header_text.append(" - LIVE DASHBOARD", style="cyan")
        header_text.append(f" {datetime.now().strftime('%H:%M:%S')}", style="dim cyan")
        header_text.append(" ║\n", style="cyan")
        header_text.append("╚═══════════════════════════════════════════════════════════════════╝", style="cyan")
        layout["header"].update(Panel(header_text, border_style="cyan", padding=(0, 0)))

        # System stats
        layout["system"].update(Panel(
            self.get_system_stats(),
            title="[cyan]SYSTEM STATUS[/cyan]",
            border_style="cyan",
            padding=(1, 2)
        ))

        # System info
        layout["info"].update(Panel(
            self.get_system_info(),
            title="[cyan]SYSTEM INFO[/cyan]",
            border_style="cyan",
            padding=(1, 2)
        ))

        # Active workflows
        layout["workflows"].update(Panel(
            self.get_active_workflows(),
            title="[yellow]ACTIVE WORKFLOWS[/yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))

        # Recent outputs
        layout["outputs"].update(Panel(
            self.get_recent_outputs(),
            title="[green]RECENT OUTPUTS[/green]",
            border_style="green",
            padding=(1, 2)
        ))

        # Workflow graph
        layout["graph"].update(Panel(
            self.get_workflow_tree(),
            title="[yellow]WORKFLOW GRAPH[/yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))

        # Footer
        footer_text = Text()
        footer_text.append("Press ", style="dim")
        footer_text.append("Ctrl+C", style="bold white")
        footer_text.append(" to exit | Updates every ", style="dim")
        footer_text.append(f"{self.refresh_rate}s", style="bold white")
        footer_text.append(" | Outputs: ", style="dim")
        footer_text.append(str(self.output_count), style="bold green")

        layout["footer"].update(Panel(footer_text, border_style="dim", padding=(0, 1)))

        return layout

    def run(self):
        """Run the live dashboard"""
        try:
            with Live(self.render(), refresh_per_second=1/self.refresh_rate, console=self.console) as live:
                while True:
                    time.sleep(self.refresh_rate)

                    # Update output count
                    if self.outputs_dir.exists():
                        self.output_count = len(list(self.outputs_dir.glob("*.png")))

                    # Update display
                    live.update(self.render())

        except KeyboardInterrupt:
            self.console.print("\n[cyan]Dashboard stopped[/cyan]")


def run_monitor(refresh_rate: float = 1.0):
    """Start the live monitoring dashboard"""
    monitor = ForgeMonitorTUI(refresh_rate=refresh_rate)
    monitor.run()


if __name__ == "__main__":
    run_monitor()
