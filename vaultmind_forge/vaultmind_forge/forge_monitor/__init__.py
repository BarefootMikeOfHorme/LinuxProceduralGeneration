"""
VaultMind Forge - System Monitor Module

Production-grade system resource monitoring for asset generation pipelines.

Features:
- Real-time CPU, memory, disk, GPU monitoring
- Thermal sensor tracking
- Alert system for resource constraints
- Historical metrics storage and analysis
- Process-specific monitoring
- Statistical analysis and trend detection
- Export to JSON/CSV for external analysis

Example:
    from vaultmind_forge.forge_monitor import SystemMonitor, MetricsAggregator

    # Basic monitoring
    monitor = SystemMonitor(cpu_threshold=80.0, memory_threshold=90.0)

    with monitor.track_session("diffusion-job-123"):
        # Your asset generation code here
        snapshot = monitor.capture_snapshot()
        print(f"CPU: {snapshot.cpu_percent}%")

    # Get session summary
    summary = monitor.get_session_summary()
    print(f"Average CPU: {summary['cpu']['avg']:.1f}%")

    # Generate performance report
    report = MetricsAggregator.generate_performance_report(monitor.snapshots)
"""

from __future__ import annotations

from .monitor import (
    SystemMonitor,
    SystemSnapshot,
    Alert,
    AlertLevel,
)

from .metrics import (
    MetricsAggregator,
    MetricStats,
)

__all__ = [
    # Core monitoring
    "SystemMonitor",
    "SystemSnapshot",
    "Alert",
    "AlertLevel",
    # Metrics analysis
    "MetricsAggregator",
    "MetricStats",
]

__version__ = "1.0.0"
