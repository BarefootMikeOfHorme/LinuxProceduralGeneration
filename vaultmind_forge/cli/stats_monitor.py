"""
Stats Monitor - System and GPU statistics dashboard

Monitors:
- System resources (CPU, RAM, disk)
- GPU status (CUDA, VRAM, utilization)
- Agent statistics
- Process statistics
- Generation metrics
"""

from __future__ import annotations

import time
import platform
import psutil
from pathlib import Path
from typing import Dict, Any, Optional

from .terminal_ui import TerminalUI, console
from .agent_manager import AgentManager
from .process_orchestrator import ProcessOrchestrator


class StatsMonitor:
    """
    System statistics monitor

    Tracks system resources, GPU usage, and VaultMind Forge metrics
    """

    def __init__(
        self,
        agent_manager: AgentManager,
        process_orchestrator: ProcessOrchestrator,
    ):
        self.agent_manager = agent_manager
        self.process_orchestrator = process_orchestrator

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system resource statistics"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()

        # Memory
        memory = psutil.virtual_memory()

        # Disk
        disk = psutil.disk_usage('/')

        # Python process
        process = psutil.Process()
        process_memory = process.memory_info().rss / (1024 ** 2)  # MB

        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
            },
            "memory": {
                "total_gb": memory.total / (1024 ** 3),
                "available_gb": memory.available / (1024 ** 3),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": disk.total / (1024 ** 3),
                "used_gb": disk.used / (1024 ** 3),
                "free_gb": disk.free / (1024 ** 3),
                "percent": disk.percent,
            },
            "process": {
                "memory_mb": process_memory,
                "pid": process.pid,
            },
        }

    def get_gpu_stats(self) -> Optional[Dict[str, Any]]:
        """Get GPU/CUDA statistics"""
        try:
            import torch

            if not torch.cuda.is_available():
                return None

            gpu_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()

            # Get GPU properties
            props = torch.cuda.get_device_properties(current_device)

            # Memory info
            memory_allocated = torch.cuda.memory_allocated(current_device) / (1024 ** 3)
            memory_reserved = torch.cuda.memory_reserved(current_device) / (1024 ** 3)
            memory_total = props.total_memory / (1024 ** 3)

            return {
                "available": True,
                "device_count": gpu_count,
                "current_device": current_device,
                "device_name": torch.cuda.get_device_name(current_device),
                "cuda_version": torch.version.cuda,
                "pytorch_version": torch.__version__,
                "memory": {
                    "allocated_gb": memory_allocated,
                    "reserved_gb": memory_reserved,
                    "total_gb": memory_total,
                    "free_gb": memory_total - memory_allocated,
                    "percent": (memory_allocated / memory_total) * 100,
                },
                "compute_capability": f"{props.major}.{props.minor}",
                "multiprocessor_count": props.multi_processor_count,
            }

        except ImportError:
            return None
        except Exception as e:
            return {"available": False, "error": str(e)}

    def get_nvidia_smi_stats(self) -> Optional[Dict[str, Any]]:
        """Get GPU stats from nvidia-smi"""
        try:
            import subprocess

            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw",
                 "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return None

            # Parse output
            lines = result.stdout.strip().split('\n')
            if not lines:
                return None

            # Parse first GPU
            parts = [p.strip() for p in lines[0].split(',')]
            if len(parts) < 8:
                return None

            return {
                "index": int(parts[0]),
                "name": parts[1],
                "temperature": int(parts[2]),
                "utilization_gpu": int(parts[3]),
                "utilization_memory": int(parts[4]),
                "memory_used_mb": int(parts[5]),
                "memory_total_mb": int(parts[6]),
                "power_draw_w": float(parts[7]),
            }

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None

    def display_dashboard(self) -> None:
        """Display comprehensive stats dashboard"""
        TerminalUI.clear()
        TerminalUI.header("VaultMind Forge Statistics", "System & GPU Monitoring")

        # System stats
        system_stats = self.get_system_stats()
        self._display_system_stats(system_stats)

        console.print()

        # GPU stats
        gpu_stats = self.get_gpu_stats()
        nvidia_stats = self.get_nvidia_smi_stats()
        self._display_gpu_stats(gpu_stats, nvidia_stats)

        console.print()

        # Agent stats
        agent_stats = self.agent_manager.get_stats()
        self._display_agent_stats(agent_stats)

        console.print()

        # Process stats
        process_stats = self.process_orchestrator.get_stats()
        self._display_process_stats(process_stats)

        console.print()

    def _display_system_stats(self, stats: Dict[str, Any]) -> None:
        """Display system resource statistics"""
        TerminalUI.rule("System Resources", style="cyan")

        console.print(f"[bold]Platform:[/bold] {platform.system()} {platform.release()}")
        console.print(f"[bold]Python:[/bold] {platform.python_version()}")
        console.print()

        # CPU
        cpu = stats["cpu"]
        console.print(f"[bold cyan]CPU:[/bold cyan] {cpu['count']} cores")
        console.print(f"  Utilization: {TerminalUI.display_progress_bar(int(cpu['percent']), 30)}")

        # Memory
        memory = stats["memory"]
        console.print(f"\n[bold cyan]Memory:[/bold cyan] {memory['total_gb']:.1f} GB total")
        console.print(f"  Used: {TerminalUI.display_progress_bar(int(memory['percent']), 30)}")
        console.print(f"  Available: {memory['available_gb']:.1f} GB")

        # Disk
        disk = stats["disk"]
        console.print(f"\n[bold cyan]Disk:[/bold cyan] {disk['total_gb']:.1f} GB total")
        console.print(f"  Used: {TerminalUI.display_progress_bar(int(disk['percent']), 30)}")
        console.print(f"  Free: {disk['free_gb']:.1f} GB")

        # Process
        process = stats["process"]
        console.print(f"\n[bold cyan]Process:[/bold cyan] PID {process['pid']}")
        console.print(f"  Memory: {process['memory_mb']:.1f} MB")

    def _display_gpu_stats(
        self,
        gpu_stats: Optional[Dict[str, Any]],
        nvidia_stats: Optional[Dict[str, Any]],
    ) -> None:
        """Display GPU/CUDA statistics"""
        TerminalUI.rule("GPU / CUDA", style="green")

        if not gpu_stats or not gpu_stats.get("available"):
            console.print("[dim]CUDA not available or PyTorch not installed[/dim]")
            return

        console.print(f"[bold green]GPU:[/bold green] {gpu_stats['device_name']}")
        console.print(f"  CUDA Version: {gpu_stats['cuda_version']}")
        console.print(f"  PyTorch Version: {gpu_stats['pytorch_version']}")
        console.print(f"  Compute Capability: {gpu_stats['compute_capability']}")
        console.print(f"  Multi-Processors: {gpu_stats['multiprocessor_count']}")

        # Memory
        memory = gpu_stats["memory"]
        console.print(f"\n[bold green]VRAM:[/bold green] {memory['total_gb']:.2f} GB total")
        console.print(f"  Allocated: {TerminalUI.display_progress_bar(int(memory['percent']), 30)}")
        console.print(f"  Free: {memory['free_gb']:.2f} GB")

        # nvidia-smi stats
        if nvidia_stats:
            console.print(f"\n[bold green]Real-Time (nvidia-smi):[/bold green]")
            console.print(f"  GPU Utilization: {TerminalUI.display_progress_bar(nvidia_stats['utilization_gpu'], 30)}")
            console.print(f"  Memory Utilization: {TerminalUI.display_progress_bar(nvidia_stats['utilization_memory'], 30)}")
            console.print(f"  Temperature: {nvidia_stats['temperature']}°C")
            console.print(f"  Power Draw: {nvidia_stats['power_draw_w']:.1f} W")

    def _display_agent_stats(self, stats: Dict[str, Any]) -> None:
        """Display agent statistics"""
        TerminalUI.rule("Agent Statistics", style="yellow")

        console.print(f"[bold yellow]Total Agents:[/bold yellow] {stats['total_agents']}")
        console.print(f"  Average Autonomy: {stats['avg_autonomy'] * 100:.0f}%")

        # Status breakdown
        console.print(f"\n[bold yellow]Status:[/bold yellow]")
        for status, count in stats["status_counts"].items():
            if count > 0:
                console.print(f"  {status.title()}: {count}")

        # Task stats
        if stats["total_tasks"] > 0:
            console.print(f"\n[bold yellow]Tasks:[/bold yellow] {stats['total_tasks']} completed")
            console.print(f"  Success Rate: {stats['success_rate'] * 100:.1f}%")
            if stats["total_errors"] > 0:
                console.print(f"  Errors: {stats['total_errors']}")

    def _display_process_stats(self, stats: Dict[str, Any]) -> None:
        """Display process orchestration statistics"""
        TerminalUI.rule("Process Orchestration", style="magenta")

        console.print(f"[bold magenta]Total Processes:[/bold magenta] {stats['total_processes']}")

        if stats["total_processes"] > 0:
            console.print(f"  Success Rate: {stats['success_rate'] * 100:.1f}%")
            console.print(f"  Average Duration: {stats['avg_duration']:.2f}s")

            # Status breakdown
            console.print(f"\n[bold magenta]Status:[/bold magenta]")
            for status, count in stats["status_counts"].items():
                if count > 0:
                    console.print(f"  {status.title()}: {count}")

            # Type breakdown
            console.print(f"\n[bold magenta]Types:[/bold magenta]")
            for ptype, count in stats["type_counts"].items():
                if count > 0:
                    console.print(f"  {ptype.upper()}: {count}")

    def export_stats(self) -> Dict[str, Any]:
        """Export all statistics as JSON"""
        return {
            "system": self.get_system_stats(),
            "gpu": self.get_gpu_stats(),
            "nvidia": self.get_nvidia_smi_stats(),
            "agents": self.agent_manager.get_stats(),
            "processes": self.process_orchestrator.get_stats(),
            "timestamp": time.time(),
        }
