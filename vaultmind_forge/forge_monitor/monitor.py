"""
VaultMind Forge - System Monitor
Production-grade system resource monitoring for asset generation pipelines
"""

from __future__ import annotations

import psutil
import time
import platform
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from enum import Enum

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class SystemSnapshot:
    """Complete system resource snapshot at a point in time"""
    timestamp: datetime

    # CPU metrics
    cpu_percent: float
    cpu_count: int
    cpu_freq_current: Optional[float]
    cpu_temp: Optional[float]

    # Memory metrics
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    memory_available_gb: float

    # Disk metrics
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    disk_read_mb: float
    disk_write_mb: float

    # GPU metrics (if available)
    gpu_count: int = 0
    gpu_utilization: List[float] = field(default_factory=list)
    gpu_memory_used: List[float] = field(default_factory=list)
    gpu_memory_total: List[float] = field(default_factory=list)
    gpu_temperature: List[float] = field(default_factory=list)

    # Process metrics
    process_cpu_percent: float = 0.0
    process_memory_mb: float = 0.0
    process_threads: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu": {
                "percent": self.cpu_percent,
                "count": self.cpu_count,
                "freq_mhz": self.cpu_freq_current,
                "temp_c": self.cpu_temp,
            },
            "memory": {
                "total_gb": self.memory_total_gb,
                "used_gb": self.memory_used_gb,
                "percent": self.memory_percent,
                "available_gb": self.memory_available_gb,
            },
            "disk": {
                "total_gb": self.disk_total_gb,
                "used_gb": self.disk_used_gb,
                "percent": self.disk_percent,
                "read_mb": self.disk_read_mb,
                "write_mb": self.disk_write_mb,
            },
            "gpu": {
                "count": self.gpu_count,
                "utilization": self.gpu_utilization,
                "memory_used_mb": self.gpu_memory_used,
                "memory_total_mb": self.gpu_memory_total,
                "temperature_c": self.gpu_temperature,
            },
            "process": {
                "cpu_percent": self.process_cpu_percent,
                "memory_mb": self.process_memory_mb,
                "threads": self.process_threads,
            }
        }


@dataclass
class Alert:
    """System resource alert"""
    level: AlertLevel
    message: str
    timestamp: datetime
    metric: str
    value: float
    threshold: float

    def __str__(self) -> str:
        return f"[{self.level.value.upper()}] {self.timestamp.strftime('%H:%M:%S')} - {self.message}"


class SystemMonitor:
    """
    Production-grade system resource monitor for asset generation pipelines.

    Features:
    - Real-time CPU, memory, disk, GPU monitoring
    - Thermal sensor tracking
    - Alert system for resource constraints
    - Historical metrics storage
    - Process-specific monitoring
    - Configurable thresholds

    Example:
        monitor = SystemMonitor(
            cpu_threshold=80.0,
            memory_threshold=90.0,
            gpu_temp_threshold=85.0
        )

        with monitor.track_session("diffusion-job-123"):
            # Run asset generation
            pass

        summary = monitor.get_session_summary()
    """

    def __init__(
        self,
        cpu_threshold: float = 85.0,
        memory_threshold: float = 90.0,
        disk_threshold: float = 95.0,
        gpu_temp_threshold: float = 85.0,
        gpu_memory_threshold: float = 95.0,
        alert_callback: Optional[Callable[[Alert], None]] = None,
    ):
        """
        Initialize system monitor with thresholds.

        Args:
            cpu_threshold: CPU usage % to trigger warning (default: 85%)
            memory_threshold: Memory usage % to trigger warning (default: 90%)
            disk_threshold: Disk usage % to trigger warning (default: 95%)
            gpu_temp_threshold: GPU temperature °C to trigger warning (default: 85°C)
            gpu_memory_threshold: GPU memory usage % to trigger warning (default: 95%)
            alert_callback: Optional callback function for alerts
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.gpu_temp_threshold = gpu_temp_threshold
        self.gpu_memory_threshold = gpu_memory_threshold
        self.alert_callback = alert_callback

        # Historical data
        self.snapshots: List[SystemSnapshot] = []
        self.alerts: List[Alert] = []

        # Session tracking
        self.session_active = False
        self.session_name: Optional[str] = None
        self.session_start: Optional[datetime] = None
        self.session_snapshots: List[SystemSnapshot] = []

        # Process handle
        self.process = psutil.Process()

        # Initial disk I/O counters
        self._last_disk_io = psutil.disk_io_counters()
        self._last_disk_time = time.time()

    def capture_snapshot(self) -> SystemSnapshot:
        """
        Capture current system state snapshot.

        Returns:
            SystemSnapshot with all current metrics
        """
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        cpu_freq_current = cpu_freq.current if cpu_freq else None

        # CPU temperature (if available)
        cpu_temp = self._get_cpu_temperature()

        # Memory metrics
        mem = psutil.virtual_memory()
        memory_total_gb = mem.total / (1024**3)
        memory_used_gb = mem.used / (1024**3)
        memory_percent = mem.percent
        memory_available_gb = mem.available / (1024**3)

        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_total_gb = disk.total / (1024**3)
        disk_used_gb = disk.used / (1024**3)
        disk_percent = disk.percent

        # Disk I/O rates
        disk_read_mb, disk_write_mb = self._get_disk_io_rates()

        # GPU metrics
        gpu_count = 0
        gpu_utilization = []
        gpu_memory_used = []
        gpu_memory_total = []
        gpu_temperature = []

        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                gpu_count = len(gpus)
                for gpu in gpus:
                    gpu_utilization.append(gpu.load * 100)
                    gpu_memory_used.append(gpu.memoryUsed)
                    gpu_memory_total.append(gpu.memoryTotal)
                    gpu_temperature.append(gpu.temperature)
            except Exception:
                pass  # GPU monitoring not critical

        # Process-specific metrics
        process_cpu_percent = self.process.cpu_percent(interval=0.1)
        process_memory_mb = self.process.memory_info().rss / (1024**2)
        process_threads = self.process.num_threads()

        snapshot = SystemSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            cpu_freq_current=cpu_freq_current,
            cpu_temp=cpu_temp,
            memory_total_gb=memory_total_gb,
            memory_used_gb=memory_used_gb,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_total_gb=disk_total_gb,
            disk_used_gb=disk_used_gb,
            disk_percent=disk_percent,
            disk_read_mb=disk_read_mb,
            disk_write_mb=disk_write_mb,
            gpu_count=gpu_count,
            gpu_utilization=gpu_utilization,
            gpu_memory_used=gpu_memory_used,
            gpu_memory_total=gpu_memory_total,
            gpu_temperature=gpu_temperature,
            process_cpu_percent=process_cpu_percent,
            process_memory_mb=process_memory_mb,
            process_threads=process_threads,
        )

        # Check thresholds and generate alerts
        self._check_thresholds(snapshot)

        # Store snapshot
        self.snapshots.append(snapshot)
        if self.session_active:
            self.session_snapshots.append(snapshot)

        return snapshot

    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature if available"""
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Try common sensor names
                    for name in ["coretemp", "cpu_thermal", "k10temp", "zenpower"]:
                        if name in temps:
                            entries = temps[name]
                            if entries:
                                # Return average of all cores
                                return sum(e.current for e in entries) / len(entries)
        except Exception:
            pass
        return None

    def _get_disk_io_rates(self) -> tuple[float, float]:
        """Calculate disk I/O rates in MB/s"""
        current_io = psutil.disk_io_counters()
        current_time = time.time()

        if self._last_disk_io and self._last_disk_time:
            time_delta = current_time - self._last_disk_time
            if time_delta > 0:
                read_mb = (current_io.read_bytes - self._last_disk_io.read_bytes) / (1024**2) / time_delta
                write_mb = (current_io.write_bytes - self._last_disk_io.write_bytes) / (1024**2) / time_delta
            else:
                read_mb = write_mb = 0.0
        else:
            read_mb = write_mb = 0.0

        self._last_disk_io = current_io
        self._last_disk_time = current_time

        return read_mb, write_mb

    def _check_thresholds(self, snapshot: SystemSnapshot) -> None:
        """Check snapshot against thresholds and generate alerts"""
        alerts = []

        # CPU check
        if snapshot.cpu_percent > self.cpu_threshold:
            alerts.append(Alert(
                level=AlertLevel.WARNING if snapshot.cpu_percent < 95 else AlertLevel.CRITICAL,
                message=f"High CPU usage: {snapshot.cpu_percent:.1f}%",
                timestamp=snapshot.timestamp,
                metric="cpu_percent",
                value=snapshot.cpu_percent,
                threshold=self.cpu_threshold,
            ))

        # Memory check
        if snapshot.memory_percent > self.memory_threshold:
            alerts.append(Alert(
                level=AlertLevel.WARNING if snapshot.memory_percent < 95 else AlertLevel.CRITICAL,
                message=f"High memory usage: {snapshot.memory_percent:.1f}%",
                timestamp=snapshot.timestamp,
                metric="memory_percent",
                value=snapshot.memory_percent,
                threshold=self.memory_threshold,
            ))

        # Disk check
        if snapshot.disk_percent > self.disk_threshold:
            alerts.append(Alert(
                level=AlertLevel.CRITICAL,
                message=f"Low disk space: {snapshot.disk_percent:.1f}% used",
                timestamp=snapshot.timestamp,
                metric="disk_percent",
                value=snapshot.disk_percent,
                threshold=self.disk_threshold,
            ))

        # GPU temperature check
        for i, temp in enumerate(snapshot.gpu_temperature):
            if temp > self.gpu_temp_threshold:
                alerts.append(Alert(
                    level=AlertLevel.WARNING if temp < 90 else AlertLevel.CRITICAL,
                    message=f"High GPU {i} temperature: {temp:.1f}°C",
                    timestamp=snapshot.timestamp,
                    metric=f"gpu_{i}_temp",
                    value=temp,
                    threshold=self.gpu_temp_threshold,
                ))

        # GPU memory check
        for i, (used, total) in enumerate(zip(snapshot.gpu_memory_used, snapshot.gpu_memory_total)):
            if total > 0:
                percent = (used / total) * 100
                if percent > self.gpu_memory_threshold:
                    alerts.append(Alert(
                        level=AlertLevel.WARNING,
                        message=f"High GPU {i} memory: {percent:.1f}%",
                        timestamp=snapshot.timestamp,
                        metric=f"gpu_{i}_memory_percent",
                        value=percent,
                        threshold=self.gpu_memory_threshold,
                    ))

        # Store and trigger callbacks
        for alert in alerts:
            self.alerts.append(alert)
            if self.alert_callback:
                self.alert_callback(alert)

    def start_session(self, session_name: str) -> None:
        """Start a monitoring session"""
        self.session_active = True
        self.session_name = session_name
        self.session_start = datetime.now()
        self.session_snapshots = []

    def stop_session(self) -> Dict[str, Any]:
        """Stop monitoring session and return summary"""
        if not self.session_active:
            return {}

        summary = self.get_session_summary()

        self.session_active = False
        self.session_name = None
        self.session_start = None
        self.session_snapshots = []

        return summary

    def track_session(self, session_name: str):
        """Context manager for tracking a session"""
        class SessionTracker:
            def __init__(self, monitor: SystemMonitor, name: str):
                self.monitor = monitor
                self.name = name

            def __enter__(self):
                self.monitor.start_session(self.name)
                return self.monitor

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.monitor.stop_session()

        return SessionTracker(self, session_name)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary statistics for current session"""
        if not self.session_snapshots:
            return {}

        cpu_values = [s.cpu_percent for s in self.session_snapshots]
        memory_values = [s.memory_percent for s in self.session_snapshots]
        process_cpu = [s.process_cpu_percent for s in self.session_snapshots]
        process_mem = [s.process_memory_mb for s in self.session_snapshots]

        duration = (self.session_snapshots[-1].timestamp - self.session_snapshots[0].timestamp).total_seconds()

        summary = {
            "session_name": self.session_name,
            "duration_seconds": duration,
            "snapshot_count": len(self.session_snapshots),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
            },
            "process": {
                "cpu_avg": sum(process_cpu) / len(process_cpu),
                "cpu_max": max(process_cpu),
                "memory_avg_mb": sum(process_mem) / len(process_mem),
                "memory_max_mb": max(process_mem),
            },
            "alerts": [
                {"level": a.level.value, "message": a.message, "timestamp": a.timestamp.isoformat()}
                for a in self.alerts
                if self.session_start and a.timestamp >= self.session_start
            ],
        }

        # GPU summary if available
        if self.session_snapshots[0].gpu_count > 0:
            gpu_util = [s.gpu_utilization for s in self.session_snapshots if s.gpu_utilization]
            gpu_temp = [s.gpu_temperature for s in self.session_snapshots if s.gpu_temperature]

            if gpu_util:
                summary["gpu"] = {
                    "count": self.session_snapshots[0].gpu_count,
                    "utilization_avg": [
                        sum(u[i] for u in gpu_util) / len(gpu_util)
                        for i in range(len(gpu_util[0]))
                    ],
                    "temperature_avg": [
                        sum(t[i] for t in gpu_temp) / len(gpu_temp)
                        for i in range(len(gpu_temp[0]))
                    ] if gpu_temp else [],
                }

        return summary

    def get_current_status(self) -> Dict[str, Any]:
        """Get current system status summary"""
        snapshot = self.capture_snapshot()
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "cpu_percent": snapshot.cpu_percent,
            "memory_percent": snapshot.memory_percent,
            "disk_percent": snapshot.disk_percent,
            "gpu_count": snapshot.gpu_count,
            "alerts_count": len(self.alerts),
            "platform": platform.platform(),
        }

    def export_metrics(self, output_path: Path) -> None:
        """Export all snapshots to JSON file"""
        import json

        data = {
            "monitor_config": {
                "cpu_threshold": self.cpu_threshold,
                "memory_threshold": self.memory_threshold,
                "disk_threshold": self.disk_threshold,
                "gpu_temp_threshold": self.gpu_temp_threshold,
            },
            "snapshots": [s.to_dict() for s in self.snapshots],
            "alerts": [
                {
                    "level": a.level.value,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat(),
                    "metric": a.metric,
                    "value": a.value,
                    "threshold": a.threshold,
                }
                for a in self.alerts
            ],
        }

        output_path.write_text(json.dumps(data, indent=2))
