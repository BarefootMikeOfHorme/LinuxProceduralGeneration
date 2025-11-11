"""
Process Orchestrator - Multi-language process management

Spawns and manages:
- Python scripts (AI/ML operations)
- Rust binaries (performance-critical tasks)
- C++ executables (legacy/optimized code)
- Node.js scripts (async orchestration)
"""

from __future__ import annotations

import subprocess
import json
import time
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue

from .terminal_ui import TerminalUI, console


class ProcessType(str, Enum):
    """Process types"""
    PYTHON = "python"
    RUST = "rust"
    CPP = "cpp"
    NODEJS = "nodejs"
    BASH = "bash"


class ProcessStatus(str, Enum):
    """Process status states"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"


@dataclass
class ProcessResult:
    """Result from process execution"""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ManagedProcess:
    """Managed process representation"""
    id: str
    name: str
    type: ProcessType
    command: List[str]
    status: ProcessStatus
    pid: Optional[int] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    result: Optional[ProcessResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def duration(self) -> float:
        """Get process duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "pid": self.pid,
            "duration": self.duration(),
            "metadata": self.metadata,
        }


class ProcessOrchestrator:
    """
    Multi-language process orchestration

    Manages subprocess execution for Python, Rust, C++, and Node.js
    with output streaming, error handling, and JSON-based communication.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.processes: Dict[str, ManagedProcess] = {}
        self.output_queue: Queue = Queue()

    def execute_python(
        self,
        script_path: Path,
        args: Optional[List[str]] = None,
        venv_path: Optional[Path] = None,
        capture_output: bool = True,
        timeout: Optional[float] = None,
    ) -> ProcessResult:
        """Execute Python script"""
        # Determine Python executable
        if venv_path:
            if venv_path.name == ".venv312":
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                python_exe = venv_path / "bin" / "python"
        else:
            python_exe = Path("python")

        command = [str(python_exe), str(script_path)]
        if args:
            command.extend(args)

        return self._execute_process(
            name=script_path.stem,
            process_type=ProcessType.PYTHON,
            command=command,
            capture_output=capture_output,
            timeout=timeout,
        )

    def execute_rust(
        self,
        binary_path: Path,
        args: Optional[List[str]] = None,
        capture_output: bool = True,
        timeout: Optional[float] = None,
    ) -> ProcessResult:
        """Execute Rust binary"""
        command = [str(binary_path)]
        if args:
            command.extend(args)

        return self._execute_process(
            name=binary_path.stem,
            process_type=ProcessType.RUST,
            command=command,
            capture_output=capture_output,
            timeout=timeout,
        )

    def execute_cpp(
        self,
        binary_path: Path,
        args: Optional[List[str]] = None,
        capture_output: bool = True,
        timeout: Optional[float] = None,
    ) -> ProcessResult:
        """Execute C++ binary"""
        command = [str(binary_path)]
        if args:
            command.extend(args)

        return self._execute_process(
            name=binary_path.stem,
            process_type=ProcessType.CPP,
            command=command,
            capture_output=capture_output,
            timeout=timeout,
        )

    def execute_nodejs(
        self,
        script_path: Path,
        args: Optional[List[str]] = None,
        capture_output: bool = True,
        timeout: Optional[float] = None,
    ) -> ProcessResult:
        """Execute Node.js script"""
        command = ["node", str(script_path)]
        if args:
            command.extend(args)

        return self._execute_process(
            name=script_path.stem,
            process_type=ProcessType.NODEJS,
            command=command,
            capture_output=capture_output,
            timeout=timeout,
        )

    def _execute_process(
        self,
        name: str,
        process_type: ProcessType,
        command: List[str],
        capture_output: bool = True,
        timeout: Optional[float] = None,
        cwd: Optional[Path] = None,
    ) -> ProcessResult:
        """Execute subprocess and return result"""
        start_time = time.time()

        # Create managed process
        process_id = f"{process_type.value}_{int(start_time * 1000)}"
        managed_proc = ManagedProcess(
            id=process_id,
            name=name,
            type=process_type,
            command=command,
            status=ProcessStatus.RUNNING,
        )
        self.processes[process_id] = managed_proc

        try:
            # Execute process
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=cwd or self.project_root,
            )

            # Create result
            duration = time.time() - start_time
            proc_result = ProcessResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout if capture_output else "",
                stderr=result.stderr if capture_output else "",
                duration=duration,
            )

            # Update managed process
            managed_proc.status = ProcessStatus.COMPLETED if proc_result.success else ProcessStatus.FAILED
            managed_proc.end_time = time.time()
            managed_proc.result = proc_result

            return proc_result

        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            managed_proc.status = ProcessStatus.KILLED
            managed_proc.end_time = time.time()

            return ProcessResult(
                success=False,
                exit_code=-1,
                stdout=e.stdout if hasattr(e, 'stdout') else "",
                stderr=f"Process timeout after {timeout}s",
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            managed_proc.status = ProcessStatus.FAILED
            managed_proc.end_time = time.time()

            return ProcessResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=duration,
            )

    def execute_with_json_io(
        self,
        process_type: ProcessType,
        executable: Path,
        input_data: Dict[str, Any],
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute process with JSON input/output

        Useful for structured communication between Python and Rust/C++/Node.js
        """
        # Write input to temp JSON file
        input_file = self.project_root / f"input_{int(time.time() * 1000)}.json"
        output_file = self.project_root / f"output_{int(time.time() * 1000)}.json"

        try:
            # Write input
            with open(input_file, 'w') as f:
                json.dump(input_data, f)

            # Execute
            if process_type == ProcessType.PYTHON:
                result = self.execute_python(executable, [str(input_file), str(output_file)], timeout=timeout)
            elif process_type == ProcessType.RUST:
                result = self.execute_rust(executable, [str(input_file), str(output_file)], timeout=timeout)
            elif process_type == ProcessType.CPP:
                result = self.execute_cpp(executable, [str(input_file), str(output_file)], timeout=timeout)
            elif process_type == ProcessType.NODEJS:
                result = self.execute_nodejs(executable, [str(input_file), str(output_file)], timeout=timeout)
            else:
                raise ValueError(f"Unsupported process type: {process_type}")

            # Read output
            if result.success and output_file.exists():
                with open(output_file, 'r') as f:
                    output_data = json.load(f)
                return output_data
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "exit_code": result.exit_code,
                }

        finally:
            # Cleanup
            if input_file.exists():
                input_file.unlink()
            if output_file.exists():
                output_file.unlink()

    def list_processes(self, filter_status: Optional[ProcessStatus] = None) -> List[ManagedProcess]:
        """List managed processes"""
        processes = list(self.processes.values())

        if filter_status:
            processes = [p for p in processes if p.status == filter_status]

        return processes

    def get_process(self, process_id: str) -> Optional[ManagedProcess]:
        """Get process by ID"""
        return self.processes.get(process_id)

    def show_process_dashboard(self) -> None:
        """Display process dashboard"""
        TerminalUI.clear()
        TerminalUI.header("Process Orchestrator", "Multi-Language Process Management")

        processes = list(self.processes.values())

        if not processes:
            TerminalUI.info("No processes executed yet")
            return

        # Create table
        rows = []
        for proc in processes[-20:]:  # Last 20 processes
            rows.append([
                proc.id[:12],
                proc.name,
                proc.type.value.upper(),
                TerminalUI.format_status(proc.status.value),
                f"{proc.duration():.2f}s",
                proc.result.exit_code if proc.result else "N/A",
            ])

        TerminalUI.table(
            title="Recent Processes",
            columns=["ID", "Name", "Type", "Status", "Duration", "Exit Code"],
            rows=rows,
            border_color="magenta",
        )

        # Summary
        total = len(processes)
        completed = len([p for p in processes if p.status == ProcessStatus.COMPLETED])
        failed = len([p for p in processes if p.status == ProcessStatus.FAILED])
        running = len([p for p in processes if p.status == ProcessStatus.RUNNING])

        console.print(f"\n[cyan]Total Processes:[/cyan] {total}")
        console.print(f"[green]Completed:[/green] {completed} | [red]Failed:[/red] {failed} | [yellow]Running:[/yellow] {running}\n")

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        processes = list(self.processes.values())
        total = len(processes)

        status_counts = {}
        for status in ProcessStatus:
            status_counts[status.value] = len([p for p in processes if p.status == status])

        type_counts = {}
        for ptype in ProcessType:
            type_counts[ptype.value] = len([p for p in processes if p.type == ptype])

        completed = [p for p in processes if p.status == ProcessStatus.COMPLETED]
        avg_duration = sum(p.duration() for p in completed) / len(completed) if completed else 0

        return {
            "total_processes": total,
            "status_counts": status_counts,
            "type_counts": type_counts,
            "avg_duration": avg_duration,
            "success_rate": status_counts.get("completed", 0) / total if total > 0 else 0,
        }

    def export_state(self) -> Dict[str, Any]:
        """Export orchestrator state"""
        return {
            "processes": [p.to_dict() for p in self.processes.values()],
            "stats": self.get_stats(),
            "timestamp": time.time(),
        }
