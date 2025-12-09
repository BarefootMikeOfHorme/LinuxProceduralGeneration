"""
VaultMind Forge TUI - Terminal User Interface
Powered by Textual
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, DataTable, Log, TabbedContent, TabPane, Input
from textual.reactive import reactive
from textual import events

import psutil
import time
from datetime import datetime

class SystemMonitor(Static):
    """Widget to display system metrics"""

    cpu_usage = reactive(0.0)
    memory_usage = reactive(0.0)

    def on_mount(self) -> None:
        self.set_interval(1, self.update_metrics)

    def update_metrics(self) -> None:
        self.cpu_usage = psutil.cpu_percent()
        self.memory_usage = psutil.virtual_memory().percent

    def render(self) -> str:
        # Create a visual bar for CPU
        cpu_bar = "█" * int(self.cpu_usage / 5)
        cpu_bar += "░" * (20 - int(self.cpu_usage / 5))

        # Create a visual bar for RAM
        mem_bar = "█" * int(self.memory_usage / 5)
        mem_bar += "░" * (20 - int(self.memory_usage / 5))

        return f"""
[bold cyan]SYSTEM DIAGNOSTICS[/bold cyan]
[bold]CPU:[/bold] [{self._get_color(self.cpu_usage)}]{cpu_bar}[/] {self.cpu_usage:>5.1f}%
[bold]RAM:[/bold] [{self._get_color(self.memory_usage)}]{mem_bar}[/] {self.memory_usage:>5.1f}%
[bold]GPU:[/bold] [yellow]N/A[/yellow] (Mock)
        """

    def _get_color(self, value):
        if value < 50: return "green"
        if value < 80: return "yellow"
        return "red"

class AgentStatus(Static):
    """Widget to display agent status"""

    def render(self) -> str:
        return """
[bold cyan]AGENT NETWORK[/bold cyan]
[green]●[/green] [bold]Maestro[/bold]           [dim]IDLE[/dim]
[green]●[/green] [bold]Quality Guardian[/bold]  [green]WATCHING[/green]
[dim]○[/dim] [bold]Resource Monitor[/bold]  [dim]SLEEPING[/dim]
[dim]○[/dim] [bold]Prompt Refiner[/bold]    [dim]OFFLINE[/dim]
        """

class VaultMindApp(App):
    """The main TUI application"""

    CSS = """
    Screen {
        layout: vertical;
        background: #1a1b26; /* Tokyo Night Background */
    }

    /* Header Styling */
    Header {
        dock: top;
        height: 3;
        background: #16161e;
        color: #c0caf5;
        text-style: bold;
        border-bottom: solid #7aa2f7;
    }

    /* Tab Styling */
    Tabs {
        background: #1a1b26;
        color: #565f89;
        border-bottom: solid #16161e;
    }

    Tab {
        padding: 1 2;
    }

    Tab.-active {
        color: #bb9af7; /* Purple accent */
        border-bottom: solid #bb9af7;
        text-style: bold;
    }

    /* Welcome Screen */
    #welcome-container {
        align: center middle;
        height: 100%;
        padding: 2;
    }

    #logo {
        color: #e0af68; /* Yellow/Orange accent */
        margin-bottom: 2;
        text-align: center;
    }

    #welcome-text {
        color: #c0caf5;
        text-align: center;
        margin-bottom: 2;
    }

    .button-row {
        align: center middle;
        height: auto;
        margin-bottom: 1;
    }

    Button {
        margin: 0 1;
        background: #24283b;
        color: #c0caf5;
        border: none;
    }

    Button:hover {
        background: #bb9af7;
        color: #1a1b26;
    }

    Button.action-btn {
        width: 20;
    }

    Button.quit-btn {
        width: 10;
        background: #f7768e; /* Red accent */
        color: #1a1b26;
        margin-top: 2;
    }

    /* Dashboard Styling */
    .dashboard-row {
        height: 14;
        margin: 1;
    }

    SystemMonitor, AgentStatus {
        width: 50%;
        height: 100%;
        border: solid #7aa2f7;
        background: #24283b;
        margin-right: 1;
        padding: 1;
    }

    /* Terminal Styling */
    #terminal-container {
        height: 100%;
        background: #1a1b26;
        border: solid #7aa2f7;
        padding: 0 1;
    }

    #terminal-log {
        height: 1fr;
        background: #1a1b26;
        color: #c0caf5;
        border: none;
    }

    #terminal-input {
        dock: bottom;
        height: 3;
        border-top: solid #565f89;
        background: #24283b;
        color: #c0caf5;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with TabbedContent():
            with TabPane("Welcome", id="welcome"):
                with Vertical(id="welcome-container"):
                    yield Static(
                        """
 ██╗   ██╗ █████╗ ██╗   ██╗██╗  ████████╗███╗   ███╗██╗███╗   ██╗██████╗
 ██║   ██║██╔══██╗██║   ██║██║  ╚══██╔══╝████╗ ████║██║████╗  ██║██╔══██╗
 ██║   ██║███████║██║   ██║██║     ██║   ██╔████╔██║██║██╔██╗ ██║██║  ██║
 ╚██╗ ██╔╝██╔══██║██║   ██║██║     ██║   ██║╚██╔╝██║██║██║╚██╗██║██║  ██║
  ╚████╔╝ ██║  ██║╚██████╔╝███████╗██║   ██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
   ╚═══╝  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝   ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝
                        """,
                        id="logo"
                    )
                    yield Static("Welcome to VaultMind Forge Enterprise Edition", id="welcome-text")

                    with Horizontal(classes="button-row"):
                        yield Button("System Check", id="btn-sys-check", classes="action-btn")
                        yield Button("Active Agents", id="btn-agents", classes="action-btn")
                        yield Button("Update Models", id="btn-update", classes="action-btn")

                    yield Button("Quit", id="btn-quit", classes="quit-btn")

            with TabPane("Dashboard", id="dashboard"):
                yield Horizontal(
                    SystemMonitor(),
                    AgentStatus(),
                    classes="dashboard-row"
                )
                yield Log(id="activity_log", highlight=True)

            with TabPane("Processes", id="processes"):
                yield DataTable()

            with TabPane("Terminal", id="terminal"):
                with Vertical(id="terminal-container"):
                    yield Log(id="terminal-log", highlight=False)
                    yield Input(placeholder="Enter command...", id="terminal-input")

        yield Footer()

    def on_mount(self) -> None:
        self.title = "VAULTMIND FORGE"
        self.sub_title = "ENTERPRISE ORCHESTRATION"

        # Setup Log
        try:
            log = self.query_one("#activity_log", Log)
            log.write_line(f"[{datetime.now().time()}] [bold green]SYSTEM INITIALIZED[/]")
        except: pass

        # Setup Terminal
        try:
            term_log = self.query_one("#terminal-log", Log)
            term_log.write_line("[bold #7aa2f7]VaultMind Secure Shell v2.0[/]")
            term_log.write_line("[#565f89]Connected to local daemon.[/]")
            term_log.write_line("Type 'help' for available commands.\n")
        except: pass

        # Setup Process Table
        try:
            table = self.query_one(DataTable)
            table.add_columns("PID", "Name", "Status", "CPU %", "Memory %")
            self._refresh_processes()
            self.set_interval(2.0, self._refresh_processes)
        except: pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "btn-quit":
            self.exit()
        elif event.button.id == "btn-sys-check":
            self.notify("Running System Diagnostics...", title="System Check")
        elif event.button.id == "btn-agents":
            self.query_one(TabbedContent).active = "dashboard"
        elif event.button.id == "btn-update":
            self.notify("Checking for model updates...", title="Update")

    def _refresh_processes(self) -> None:
        try:
            table = self.query_one(DataTable)
            table.clear()
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
                try:
                    if proc.info['name'] in ['python.exe', 'node.exe', 'powershell.exe', 'cmd.exe', 'conhost.exe']:
                        table.add_row(
                            str(proc.info['pid']),
                            proc.info['name'],
                            proc.info['status'],
                            f"{proc.info['cpu_percent']:.1f}",
                            f"{proc.info['memory_percent']:.1f}"
                        )
                except:
                    pass
        except: pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle terminal input"""
        if event.input.id == "terminal-input":
            command = event.value.strip()
            term_log = self.query_one("#terminal-log", Log)

            # Echo command
            term_log.write_line(f"[bold #bb9af7]➜[/] {command}")

            # Clear input
            event.input.value = ""

            # Handle commands
            if command == "help":
                term_log.write_line("[#7aa2f7]Available commands:[/]")
                term_log.write_line("  [bold]help[/]    - Show this help")
                term_log.write_line("  [bold]clear[/]   - Clear terminal")
                term_log.write_line("  [bold]status[/]  - Show system status")
                term_log.write_line("  [bold]agents[/]  - List active agents")
                term_log.write_line("  [bold]exit[/]    - Exit TUI")
            elif command == "clear":
                term_log.clear()
            elif command == "status":
                cpu = psutil.cpu_percent()
                mem = psutil.virtual_memory().percent
                term_log.write_line(f"System Status: CPU [bold]{cpu}%[/] | RAM [bold]{mem}%[/]")
            elif command == "agents":
                term_log.write_line("Active Agents: [green]Maestro[/], [green]PromptRefiner[/]")
            elif command == "exit":
                self.exit()
            elif command:
                term_log.write_line(f"[red]Command not found: {command}[/]")

if __name__ == "__main__":
    app = VaultMindApp()
    app.run()
