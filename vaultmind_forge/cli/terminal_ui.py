"""
Terminal UI Components - Rich-based beautiful terminal interface

Mirrors the Node.js CLI aesthetic with Python's Rich library.
"""

from __future__ import annotations

import time
from typing import Callable, Optional, Any
from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.box import ROUNDED, HEAVY, DOUBLE
from rich.align import Align

console = Console()


class TerminalUI:
    """Beautiful terminal UI components using Rich"""

    @staticmethod
    def header(title: str, subtitle: str = "") -> None:
        """Display a header panel"""
        content = f"[bold white]{title}[/bold white]"
        if subtitle:
            content += f"\n[dim]{subtitle}[/dim]"

        panel = Panel(
            content,
            border_style="blue",
            box=ROUNDED,
            padding=(1, 2),
        )
        console.print(panel)
        console.print()

    @staticmethod
    def success(message: str) -> None:
        """Display success message"""
        console.print(f"[bold green on black] ✓ {message} [/bold green on black]")

    @staticmethod
    def error(message: str) -> None:
        """Display error message"""
        console.print(f"[bold red on black] ✗ {message} [/bold red on black]")

    @staticmethod
    def warning(message: str) -> None:
        """Display warning message"""
        console.print(f"[bold yellow on black] ⚠ {message} [/bold yellow on black]")

    @staticmethod
    def info(message: str) -> None:
        """Display info message"""
        console.print(f"[cyan] ℹ {message}[/cyan]")

    @staticmethod
    @contextmanager
    def loading(message: str):
        """Context manager for loading spinner"""
        with console.status(f"[bold cyan]{message}...", spinner="dots"):
            try:
                yield
            except Exception as e:
                TerminalUI.error(str(e))
                raise

    @staticmethod
    def progress_bar(total: int, description: str = "Progress"):
        """Create a progress bar"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        )

    @staticmethod
    def table(title: str, columns: list[str], rows: list[list[Any]],
              border_color: str = "blue") -> None:
        """Display a formatted table"""
        table = Table(title=title, border_style=border_color, box=ROUNDED)

        for col in columns:
            table.add_column(col, style="cyan", no_wrap=False)

        for row in rows:
            table.add_row(*[str(cell) for cell in row])

        console.print(table)

    @staticmethod
    def panel(content: str, title: str = "", border_color: str = "blue") -> None:
        """Display a panel"""
        panel = Panel(
            content,
            title=title,
            border_style=border_color,
            box=ROUNDED,
            padding=(1, 2),
        )
        console.print(panel)

    @staticmethod
    def rule(title: str = "", style: str = "blue") -> None:
        """Display a horizontal rule"""
        console.rule(f"[bold {style}]{title}[/bold {style}]")

    @staticmethod
    def clear() -> None:
        """Clear the console"""
        console.clear()

    @staticmethod
    def print(text: str, style: str = "") -> None:
        """Print text with optional style"""
        if style:
            console.print(f"[{style}]{text}[/{style}]")
        else:
            console.print(text)

    @staticmethod
    def prompt(message: str, default: str = "") -> str:
        """Prompt for user input"""
        from rich.prompt import Prompt
        return Prompt.ask(f"[cyan]{message}[/cyan]", default=default)

    @staticmethod
    def confirm(message: str, default: bool = True) -> bool:
        """Prompt for confirmation"""
        from rich.prompt import Confirm
        return Confirm.ask(f"[yellow]{message}[/yellow]", default=default)

    @staticmethod
    def choice(message: str, choices: list[str]) -> str:
        """Prompt for choice from list"""
        from rich.prompt import Prompt

        console.print(f"\n[cyan]{message}[/cyan]")
        for i, choice in enumerate(choices, 1):
            console.print(f"  {i}. {choice}")

        while True:
            answer = Prompt.ask("\n[cyan]Select option[/cyan]", default="1")
            try:
                idx = int(answer) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
            except ValueError:
                pass
            console.print("[red]Invalid choice, try again[/red]")

    @staticmethod
    def format_status(status: str) -> str:
        """Format status with color"""
        status_map = {
            "running": "[green]RUNNING[/green]",
            "paused": "[yellow]PAUSED[/yellow]",
            "idle": "[dim]IDLE[/dim]",
            "error": "[red]ERROR[/red]",
            "completed": "[green]COMPLETED[/green]",
            "queued": "[dim]QUEUED[/dim]",
            "in_progress": "[yellow]IN PROGRESS[/yellow]",
        }
        return status_map.get(status.lower(), status.upper())

    @staticmethod
    def format_time_ago(timestamp: float) -> str:
        """Format timestamp as 'time ago'"""
        diff = time.time() - timestamp

        if diff < 60:
            return f"{int(diff)}s ago"
        elif diff < 3600:
            return f"{int(diff / 60)}m ago"
        elif diff < 86400:
            return f"{int(diff / 3600)}h ago"
        else:
            return f"{int(diff / 86400)}d ago"

    @staticmethod
    def display_progress_bar(percent: int, width: int = 20) -> str:
        """Create a text-based progress bar"""
        filled = int((percent / 100) * width)
        empty = width - filled

        bar = "[green]" + "█" * filled + "[/green]"
        bar += "[dim]" + "░" * empty + "[/dim]"
        bar += f" {percent}%"

        return bar

    @staticmethod
    def wait_for_key(message: str = "Press Enter to continue") -> None:
        """Wait for user to press Enter"""
        from rich.prompt import Prompt
        Prompt.ask(f"\n[dim]{message}[/dim]", default="", show_default=False)


class CommandHistory:
    """Command history manager"""

    def __init__(self):
        self.history: list[str] = []
        self.pointer: int = -1

    def add(self, command: str) -> None:
        """Add command to history"""
        self.history.append(command)
        self.pointer = len(self.history)

    def previous(self) -> str:
        """Get previous command"""
        if self.pointer > 0:
            self.pointer -= 1
        return self.history[self.pointer] if self.pointer < len(self.history) else ""

    def next(self) -> str:
        """Get next command"""
        if self.pointer < len(self.history) - 1:
            self.pointer += 1
        return self.history[self.pointer] if self.pointer < len(self.history) else ""

    def last(self, n: int = 1) -> list[str]:
        """Get last n commands"""
        return self.history[-n:] if n <= len(self.history) else self.history

    def all(self) -> list[str]:
        """Get all commands"""
        return self.history.copy()


# Global command history
command_history = CommandHistory()
