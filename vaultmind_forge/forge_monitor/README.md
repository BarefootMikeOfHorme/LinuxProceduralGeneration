

# forge_monitor

**Production-Grade System Resource Monitoring for AI Asset Generation**

## Overview

The `forge_monitor` module provides comprehensive system resource monitoring specifically designed for AI asset generation pipelines. It tracks CPU, memory, disk, GPU usage, thermal sensors, and provides intelligent alerting for resource constraints.

## Features

### Core Monitoring
- **CPU Metrics**: Usage %, core count, frequency, temperature
- **Memory Metrics**: Total, used, available, percentage
- **Disk Metrics**: Usage, I/O rates (read/write MB/s)
- **GPU Metrics**: Utilization, memory, temperature (multi-GPU support)
- **Process Metrics**: Process-specific CPU and memory tracking

### Advanced Capabilities
- **Alert System**: Configurable thresholds with callback support
- **Session Tracking**: Context manager for monitoring specific operations
- **Historical Data**: Complete snapshot history with timestamps
- **Statistical Analysis**: Mean, median, std dev, percentiles, trend detection
- **Anomaly Detection**: Automatic outlier detection using statistical methods
- **Export Formats**: JSON and CSV export for external analysis

## Installation

The module requires `psutil` for system monitoring. GPU monitoring requires `GPUtil` (optional).

```bash
pip install psutil
pip install gputil  # Optional, for GPU monitoring
```

## Quick Start

### Basic Usage

```python
from vaultmind_forge.forge_monitor import SystemMonitor

# Create monitor with custom thresholds
monitor = SystemMonitor(
    cpu_threshold=80.0,       # Warn at 80% CPU
    memory_threshold=90.0,    # Warn at 90% memory
    gpu_temp_threshold=85.0   # Warn at 85°C GPU temp
)

# Capture single snapshot
snapshot = monitor.capture_snapshot()
print(f"CPU: {snapshot.cpu_percent}%")
print(f"Memory: {snapshot.memory_percent}%")
print(f"GPU Count: {snapshot.gpu_count}")
```

### Session Tracking

```python
# Track a specific operation
with monitor.track_session("diffusion-generation-job-123"):
    # Your asset generation code here
    generate_assets()

# Get session summary
summary = monitor.get_session_summary()
print(f"Session: {summary['session_name']}")
print(f"Duration: {summary['duration_seconds']:.2f}s")
print(f"Avg CPU: {summary['cpu']['avg']:.1f}%")
print(f"Max Memory: {summary['memory']['max']:.1f}%")
```

### Alert Callbacks

```python
def handle_alert(alert):
    print(f"⚠️  {alert.level.value.upper()}: {alert.message}")
    if alert.level == AlertLevel.CRITICAL:
        # Take action (e.g., pause generation, send notification)
        notify_admin(alert.message)

monitor = SystemMonitor(
    cpu_threshold=85.0,
    alert_callback=handle_alert
)
```

### Performance Reports

```python
from vaultmind_forge.forge_monitor import MetricsAggregator

# Run monitoring session
with monitor.track_session("batch-validation"):
    for asset in assets:
        validate(asset)
        monitor.capture_snapshot()

# Generate comprehensive report
report = MetricsAggregator.generate_performance_report(monitor.snapshots)

print(f"CPU Stats:")
print(f"  Mean: {report['cpu']['stats']['mean']:.1f}%")
print(f"  Max: {report['cpu']['stats']['max']:.1f}%")
print(f"  P95: {report['cpu']['stats']['p95']:.1f}%")
print(f"  Trend: {report['cpu']['trend']}")
```

## API Reference

### SystemMonitor

Main monitoring class for capturing system metrics.

#### Constructor

```python
SystemMonitor(
    cpu_threshold: float = 85.0,
    memory_threshold: float = 90.0,
    disk_threshold: float = 95.0,
    gpu_temp_threshold: float = 85.0,
    gpu_memory_threshold: float = 95.0,
    alert_callback: Optional[Callable[[Alert], None]] = None
)
```

**Parameters:**
- `cpu_threshold`: CPU usage % to trigger warning
- `memory_threshold`: Memory usage % to trigger warning
- `disk_threshold`: Disk usage % to trigger warning
- `gpu_temp_threshold`: GPU temperature °C to trigger warning
- `gpu_memory_threshold`: GPU memory usage % to trigger warning
- `alert_callback`: Optional callback function for alerts

#### Methods

**`capture_snapshot() -> SystemSnapshot`**

Capture current system state snapshot with all metrics.

**`start_session(session_name: str) -> None`**

Start a monitoring session with a name.

**`stop_session() -> Dict[str, Any]`**

Stop current session and return summary statistics.

**`track_session(session_name: str) -> ContextManager`**

Context manager for tracking a session.

```python
with monitor.track_session("job-123"):
    # Monitored code
    pass
```

**`get_session_summary() -> Dict[str, Any]`**

Get statistical summary of current session.

**`get_current_status() -> Dict[str, Any]`**

Get current system status snapshot.

**`export_metrics(output_path: Path) -> None`**

Export all snapshots and alerts to JSON file.

### SystemSnapshot

Data class representing a complete system snapshot at a point in time.

**Attributes:**
- `timestamp`: Capture time
- `cpu_percent`: CPU usage %
- `cpu_count`: Number of CPU cores
- `cpu_freq_current`: Current CPU frequency (MHz)
- `cpu_temp`: CPU temperature °C (if available)
- `memory_total_gb`: Total memory GB
- `memory_used_gb`: Used memory GB
- `memory_percent`: Memory usage %
- `memory_available_gb`: Available memory GB
- `disk_total_gb`: Total disk space GB
- `disk_used_gb`: Used disk space GB
- `disk_percent`: Disk usage %
- `disk_read_mb`: Disk read rate MB/s
- `disk_write_mb`: Disk write rate MB/s
- `gpu_count`: Number of GPUs
- `gpu_utilization`: List of GPU utilization % per GPU
- `gpu_memory_used`: List of GPU memory used MB per GPU
- `gpu_memory_total`: List of GPU memory total MB per GPU
- `gpu_temperature`: List of GPU temperature °C per GPU
- `process_cpu_percent`: Process-specific CPU usage %
- `process_memory_mb`: Process-specific memory usage MB
- `process_threads`: Number of threads in process

**Methods:**
- `to_dict() -> Dict[str, Any]`: Convert snapshot to dictionary

### Alert

Data class representing a system resource alert.

**Attributes:**
- `level`: AlertLevel (INFO, WARNING, CRITICAL)
- `message`: Alert message
- `timestamp`: Alert time
- `metric`: Metric name that triggered alert
- `value`: Current metric value
- `threshold`: Threshold that was exceeded

### MetricsAggregator

Statistical analysis and aggregation utilities.

#### Static Methods

**`compute_stats(values: List[float], metric_name: str) -> MetricStats`**

Compute comprehensive statistics (mean, median, std dev, percentiles).

**`detect_anomalies(values: List[float], threshold_std_dev: float = 3.0) -> List[int]`**

Detect anomalies using standard deviation method. Returns indices of anomalous values.

**`detect_trend(values: List[float]) -> str`**

Detect trend in metric values. Returns: "increasing", "decreasing", or "stable".

**`generate_performance_report(snapshots: List[SystemSnapshot]) -> Dict[str, Any]`**

Generate comprehensive performance report with all statistics.

**`export_csv(snapshots: List[SystemSnapshot], output_path: Path) -> None`**

Export snapshots to CSV for external analysis.

### MetricStats

Statistical summary of a metric.

**Attributes:**
- `metric_name`: Name of metric
- `count`: Number of samples
- `mean`: Mean value
- `median`: Median value
- `std_dev`: Standard deviation
- `min_value`: Minimum value
- `max_value`: Maximum value
- `percentile_95`: 95th percentile
- `percentile_99`: 99th percentile

## Integration Examples

### With Diffusion Generator

```python
from vaultmind_forge.forge_monitor import SystemMonitor
from vaultmind_forge.forge_diffusion import DiffusionGenerator

monitor = SystemMonitor(gpu_temp_threshold=85.0)
generator = DiffusionGenerator()

with monitor.track_session("diffusion-batch-generation"):
    for i in range(10):
        # Capture metrics before generation
        snapshot = monitor.capture_snapshot()

        # Check if resources are healthy
        if snapshot.memory_percent > 90:
            print("Warning: High memory usage, pausing generation")
            time.sleep(5)

        # Generate asset
        result = generator.generate(job, output_dir)

    # Get session summary
    summary = monitor.get_session_summary()
    print(f"Generated 10 assets in {summary['duration_seconds']:.1f}s")
    print(f"Peak GPU temp: {max(summary['gpu']['temperature_avg'])}°C")
```

### With Validator

```python
from vaultmind_forge.forge_monitor import SystemMonitor, MetricsAggregator
from vaultmind_forge.forge_validator import AssetValidator

monitor = SystemMonitor()
validator = AssetValidator()

with monitor.track_session("batch-validation"):
    for asset_path in asset_paths:
        result = validator.validate(asset_path)
        monitor.capture_snapshot()

# Generate performance report
report = MetricsAggregator.generate_performance_report(monitor.snapshots)

# Export to CSV for analysis
from pathlib import Path
MetricsAggregator.export_csv(monitor.snapshots, Path("metrics.csv"))
```

### Continuous Monitoring

```python
import time
from threading import Thread

monitor = SystemMonitor()

def continuous_monitor(interval_seconds=5):
    """Background monitoring thread"""
    while True:
        snapshot = monitor.capture_snapshot()
        if snapshot.cpu_percent > 90:
            print(f"High CPU: {snapshot.cpu_percent}%")
        time.sleep(interval_seconds)

# Start background monitoring
monitor_thread = Thread(target=continuous_monitor, daemon=True)
monitor_thread.start()

# Your main application code
run_asset_generation_pipeline()
```

## Export Formats

### JSON Export

```python
from pathlib import Path

monitor.export_metrics(Path("system_metrics.json"))
```

**Format:**
```json
{
  "monitor_config": {
    "cpu_threshold": 85.0,
    "memory_threshold": 90.0
  },
  "snapshots": [
    {
      "timestamp": "2025-11-03T...",
      "cpu": { "percent": 45.2, "count": 16 },
      "memory": { "used_gb": 12.5, "percent": 78.1 },
      "gpu": { "count": 1, "utilization": [67.0] }
    }
  ],
  "alerts": [
    {
      "level": "warning",
      "message": "High CPU usage: 87.3%",
      "timestamp": "2025-11-03T..."
    }
  ]
}
```

### CSV Export

```python
from vaultmind_forge.forge_monitor import MetricsAggregator

MetricsAggregator.export_csv(monitor.snapshots, Path("metrics.csv"))
```

**Columns:** timestamp, cpu_percent, memory_percent, disk_percent, process_cpu_percent, process_memory_mb, gpu_0_util, gpu_0_temp, gpu_0_mem_used, ...

## Performance Considerations

- **Snapshot Overhead**: ~10-20ms per capture (depends on system)
- **GPU Monitoring**: Adds ~5-10ms if GPUtil is available
- **Memory Usage**: ~1KB per snapshot (10,000 snapshots ≈ 10MB)
- **Recommended Interval**: Capture every 1-5 seconds for asset generation

## Platform Support

- **Windows**: ✅ Full support (CPU, memory, disk, GPU, thermal sensors)
- **Linux**: ✅ Full support (CPU, memory, disk, GPU, thermal sensors)
- **macOS**: ✅ Full support (GPU support via Metal/PyTorch)

**Note:** Thermal sensor availability varies by hardware and OS. The monitor gracefully handles missing sensors.

## Best Practices

1. **Set Appropriate Thresholds**: Adjust based on your hardware and workload
2. **Use Session Tracking**: Wrap operations with `track_session()` for clean summaries
3. **Handle Alerts**: Implement alert callbacks to take action on resource constraints
4. **Export Data**: Regularly export metrics for long-term analysis
5. **Monitor Trends**: Use `MetricsAggregator` to detect performance degradation
6. **Background Monitoring**: Run continuous monitoring in production pipelines

## Status

**Version:** 1.0.0
**Status:** Production-Ready
**Last Updated:** 2025-11-03

---

**Part of VaultMind Forge** - AI-powered asset generation with complete lineage tracking
