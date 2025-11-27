"""
VaultMind Forge - ASCII Art & FUI Branding
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


# ASCII Art Logo
VAULTMIND_LOGO = """
╔╦╗ ╦╔═╗╦ ╦╦  ╔╦╗╔╦╗╦╔╗╔╔╦╗  ╔═╗╔═╗╦═╗╔═╗╔═╗
 ║  ╠╣ ║ ║║   ║ ║║║║║║║ ║║  ╠╣ ║ ║╠╦╝║ ╦║╣
 ╩  ╩ ╚═╝╚═╝ ╩ ╩ ╩╩╝╚╝═╩╝  ╚  ╚═╝╩╚═╚═╝╚═╝
"""

VAULTMIND_LOGO_ALT = """
██╗   ██╗ █████╗ ██╗   ██╗██╗  ████████╗███╗   ███╗██╗███╗   ██╗██████╗
██║   ██║██╔══██╗██║   ██║██║  ╚══██╔══╝████╗ ████║██║████╗  ██║██╔══██╗
██║   ██║███████║██║   ██║██║     ██║   ██╔████╔██║██║██╔██╗ ██║██║  ██║
╚██╗ ██╔╝██╔══██║██║   ██║██║     ██║   ██║╚██╔╝██║██║██║╚██╗██║██║  ██║
 ╚████╔╝ ██║  ██║╚██████╔╝███████╗██║   ██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
  ╚═══╝  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝   ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝

███████╗ ██████╗ ██████╗  ██████╗ ███████╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
█████╗  ██║   ██║██████╔╝██║  ███╗█████╗
██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
"""

FORGE_COMPACT = """
▀█▀ █░█ ▄▀█ █░█ █░░ ▀█▀ █▀▄▀█ █ █▄░█ █▀▄   █▀▀ █▀█ █▀█ █▀▀ █▀▀
░█░ ▀▄▀ █▀█ █▄█ █▄▄ ░█░ █░▀░█ █ █░▀█ █▄▀   █▀░ █▄█ █▀▄ █▄█ ██▄
"""

TAGLINE = "AI-POWERED ASSET GENERATION & PROCESSING PIPELINE"


def print_logo(console: Console = None, style: str = "compact"):
    """Print VaultMind Forge logo with FUI styling"""
    if console is None:
        console = Console()

    if style == "compact":
        logo_text = Text()
        logo_text.append(FORGE_COMPACT, style="bold cyan")
        logo_text.append("\n")
        logo_text.append(TAGLINE, style="dim cyan")

        console.print(Panel(
            logo_text,
            border_style="cyan",
            padding=(1, 2)
        ))

    elif style == "full":
        logo_text = Text()
        logo_text.append(VAULTMIND_LOGO_ALT, style="bold cyan")
        logo_text.append("\n")
        logo_text.append(TAGLINE.center(70), style="dim cyan")

        console.print(Panel(
            logo_text,
            border_style="cyan",
            padding=(1, 2),
            title="[bold cyan]SYSTEM INITIALIZING[/bold cyan]"
        ))

    elif style == "simple":
        logo_text = Text()
        logo_text.append(VAULTMIND_LOGO, style="bold cyan")
        logo_text.append("\n")
        logo_text.append(TAGLINE, style="dim cyan")

        console.print(Panel(
            logo_text,
            border_style="cyan",
            padding=(1, 2)
        ))


def print_status_banner(title: str, message: str, style: str = "cyan", console: Console = None):
    """Print a status banner with FUI styling"""
    if console is None:
        console = Console()

    text = Text()
    text.append(f"{title}\n", style=f"bold {style}")
    text.append(message, style=f"dim {style}")

    console.print(Panel(
        text,
        border_style=style,
        padding=(1, 2)
    ))


def print_success_banner(message: str, console: Console = None):
    """Print success banner"""
    print_status_banner("✓ SUCCESS", message, "green", console)


def print_error_banner(message: str, console: Console = None):
    """Print error banner"""
    print_status_banner("✗ ERROR", message, "red", console)


def print_warning_banner(message: str, console: Console = None):
    """Print warning banner"""
    print_status_banner("⚠ WARNING", message, "yellow", console)


def print_info_banner(message: str, console: Console = None):
    """Print info banner"""
    print_status_banner("ℹ INFO", message, "cyan", console)


# ASCII art animations for progress
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

PULSE_FRAMES = ["◐", "◓", "◑", "◒"]

DOTS_FRAMES = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]


def get_data_flow_animation(step: int) -> str:
    """Get ASCII art for data flowing through nodes"""
    frames = [
        "○━━━○━━━○",
        "○━⚬━○━━━○",
        "○━━━⚬━━━○",
        "○━━━○━⚬━○",
        "○━━━○━━━⚬",
        "⚬━━━○━━━○",
        "○⚬━━○━━━○",
    ]
    return frames[step % len(frames)]


def print_workflow_progress(nodes: list, current_node: int, console: Console = None):
    """Print animated workflow progress"""
    if console is None:
        console = Console()

    progress_text = Text()

    for i, node in enumerate(nodes):
        if i < current_node:
            progress_text.append("✓ ", style="green")
            progress_text.append(node, style="dim green")
        elif i == current_node:
            progress_text.append("⟳ ", style="yellow")
            progress_text.append(node, style="bold yellow")
        else:
            progress_text.append("○ ", style="dim")
            progress_text.append(node, style="dim")

        if i < len(nodes) - 1:
            progress_text.append(" → ", style="dim cyan")

    console.print(progress_text)


if __name__ == "__main__":
    # Test the logos
    console = Console()

    console.print("\n[bold cyan]Compact Logo:[/bold cyan]")
    print_logo(console, "compact")

    console.print("\n[bold cyan]Simple Logo:[/bold cyan]")
    print_logo(console, "simple")

    console.print("\n[bold cyan]Full Logo:[/bold cyan]")
    print_logo(console, "full")

    console.print("\n[bold cyan]Status Banners:[/bold cyan]")
    print_success_banner("Workflow completed successfully!")
    print_error_banner("Validation failed: Missing required node")
    print_warning_banner("GPU not available, falling back to CPU")
    print_info_banner("Loading SDXL model from cache...")

    console.print("\n[bold cyan]Workflow Progress:[/bold cyan]")
    nodes = ["textInput", "promptRefiner", "sdxlGenerator", "upscaler"]
    print_workflow_progress(nodes, 2, console)

    console.print("\n[bold cyan]Data Flow Animation:[/bold cyan]")
    for i in range(7):
        console.print(get_data_flow_animation(i))
