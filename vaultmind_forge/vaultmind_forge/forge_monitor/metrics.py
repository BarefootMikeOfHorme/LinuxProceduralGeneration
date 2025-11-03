"""
VaultMind Forge - Metrics Aggregation
Advanced metrics analysis and aggregation for monitoring data
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import statistics


@dataclass
class MetricStats:
    """Statistical summary of a metric over time"""
    metric_name: str
    count: int
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_95: float
    percentile_99: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric_name,
            "count": self.count,
            "mean": self.mean,
            "median": self.median,
            "std_dev": self.std_dev,
            "min": self.min_value,
            "max": self.max_value,
            "p95": self.percentile_95,
            "p99": self.percentile_99,
        }


class MetricsAggregator:
    """
    Advanced metrics aggregation and analysis.

    Features:
    - Statistical summaries (mean, median, std dev, percentiles)
    - Time-windowed analysis
    - Trend detection
    - Anomaly detection
    - Performance profiling
    """

    @staticmethod
    def compute_stats(values: List[float], metric_name: str) -> MetricStats:
        """
        Compute comprehensive statistics for a metric.

        Args:
            values: List of metric values
            metric_name: Name of the metric

        Returns:
            MetricStats with all statistical measures
        """
        if not values:
            return MetricStats(
                metric_name=metric_name,
                count=0,
                mean=0.0,
                median=0.0,
                std_dev=0.0,
                min_value=0.0,
                max_value=0.0,
                percentile_95=0.0,
                percentile_99=0.0,
            )

        sorted_values = sorted(values)
        count = len(values)

        return MetricStats(
            metric_name=metric_name,
            count=count,
            mean=statistics.mean(values),
            median=statistics.median(values),
            std_dev=statistics.stdev(values) if count > 1 else 0.0,
            min_value=min(values),
            max_value=max(values),
            percentile_95=sorted_values[int(count * 0.95)] if count > 0 else 0.0,
            percentile_99=sorted_values[int(count * 0.99)] if count > 0 else 0.0,
        )

    @staticmethod
    def detect_anomalies(
        values: List[float],
        threshold_std_dev: float = 3.0
    ) -> List[int]:
        """
        Detect anomalies using standard deviation method.

        Args:
            values: List of metric values
            threshold_std_dev: Number of standard deviations for anomaly threshold

        Returns:
            List of indices where anomalies were detected
        """
        if len(values) < 3:
            return []

        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)

        if std_dev == 0:
            return []

        anomalies = []
        for i, value in enumerate(values):
            z_score = abs((value - mean) / std_dev)
            if z_score > threshold_std_dev:
                anomalies.append(i)

        return anomalies

    @staticmethod
    def detect_trend(values: List[float]) -> str:
        """
        Detect trend in metric values (increasing, decreasing, stable).

        Args:
            values: List of metric values

        Returns:
            Trend description: "increasing", "decreasing", or "stable"
        """
        if len(values) < 3:
            return "stable"

        # Calculate linear regression slope
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        # Determine trend based on slope
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"

    @staticmethod
    def time_window_stats(
        snapshots: List[Any],
        metric_extractor: callable,
        window_minutes: int = 5
    ) -> List[MetricStats]:
        """
        Compute statistics over time windows.

        Args:
            snapshots: List of SystemSnapshot objects
            metric_extractor: Function to extract metric value from snapshot
            window_minutes: Window size in minutes

        Returns:
            List of MetricStats, one per time window
        """
        if not snapshots:
            return []

        window_stats = []
        window_size = timedelta(minutes=window_minutes)

        # Sort snapshots by timestamp
        sorted_snapshots = sorted(snapshots, key=lambda s: s.timestamp)

        # Group into windows
        current_window = []
        window_start = sorted_snapshots[0].timestamp

        for snapshot in sorted_snapshots:
            if snapshot.timestamp - window_start <= window_size:
                current_window.append(metric_extractor(snapshot))
            else:
                # Process current window
                if current_window:
                    stats = MetricsAggregator.compute_stats(
                        current_window,
                        f"window_{window_start.isoformat()}"
                    )
                    window_stats.append(stats)

                # Start new window
                current_window = [metric_extractor(snapshot)]
                window_start = snapshot.timestamp

        # Process final window
        if current_window:
            stats = MetricsAggregator.compute_stats(
                current_window,
                f"window_{window_start.isoformat()}"
            )
            window_stats.append(stats)

        return window_stats

    @staticmethod
    def generate_performance_report(snapshots: List[Any]) -> Dict[str, Any]:
        """
        Generate comprehensive performance report from snapshots.

        Args:
            snapshots: List of SystemSnapshot objects

        Returns:
            Dictionary with performance report
        """
        if not snapshots:
            return {"error": "No snapshots provided"}

        # Extract metrics
        cpu_values = [s.cpu_percent for s in snapshots]
        memory_values = [s.memory_percent for s in snapshots]
        process_cpu = [s.process_cpu_percent for s in snapshots]
        process_mem = [s.process_memory_mb for s in snapshots]

        # Compute stats
        cpu_stats = MetricsAggregator.compute_stats(cpu_values, "cpu_percent")
        memory_stats = MetricsAggregator.compute_stats(memory_values, "memory_percent")
        process_cpu_stats = MetricsAggregator.compute_stats(process_cpu, "process_cpu_percent")
        process_mem_stats = MetricsAggregator.compute_stats(process_mem, "process_memory_mb")

        # Detect anomalies
        cpu_anomalies = MetricsAggregator.detect_anomalies(cpu_values)
        memory_anomalies = MetricsAggregator.detect_anomalies(memory_values)

        # Detect trends
        cpu_trend = MetricsAggregator.detect_trend(cpu_values)
        memory_trend = MetricsAggregator.detect_trend(memory_values)

        # Time span
        duration = (snapshots[-1].timestamp - snapshots[0].timestamp).total_seconds()

        report = {
            "summary": {
                "snapshot_count": len(snapshots),
                "duration_seconds": duration,
                "start_time": snapshots[0].timestamp.isoformat(),
                "end_time": snapshots[-1].timestamp.isoformat(),
            },
            "cpu": {
                "stats": cpu_stats.to_dict(),
                "trend": cpu_trend,
                "anomaly_count": len(cpu_anomalies),
            },
            "memory": {
                "stats": memory_stats.to_dict(),
                "trend": memory_trend,
                "anomaly_count": len(memory_anomalies),
            },
            "process": {
                "cpu": process_cpu_stats.to_dict(),
                "memory": process_mem_stats.to_dict(),
            },
        }

        # GPU stats if available
        if snapshots[0].gpu_count > 0:
            gpu_util_values = []
            gpu_temp_values = []

            for snapshot in snapshots:
                if snapshot.gpu_utilization:
                    gpu_util_values.extend(snapshot.gpu_utilization)
                if snapshot.gpu_temperature:
                    gpu_temp_values.extend(snapshot.gpu_temperature)

            if gpu_util_values:
                report["gpu"] = {
                    "utilization": MetricsAggregator.compute_stats(
                        gpu_util_values,
                        "gpu_utilization"
                    ).to_dict(),
                }

            if gpu_temp_values:
                report["gpu"]["temperature"] = MetricsAggregator.compute_stats(
                    gpu_temp_values,
                    "gpu_temperature"
                ).to_dict()

        return report

    @staticmethod
    def export_csv(snapshots: List[Any], output_path: Path) -> None:
        """
        Export snapshots to CSV file for external analysis.

        Args:
            snapshots: List of SystemSnapshot objects
            output_path: Path to output CSV file
        """
        import csv

        if not snapshots:
            return

        # Determine columns
        headers = [
            "timestamp",
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "process_cpu_percent",
            "process_memory_mb",
        ]

        # Add GPU columns if present
        if snapshots[0].gpu_count > 0:
            for i in range(snapshots[0].gpu_count):
                headers.extend([
                    f"gpu_{i}_util",
                    f"gpu_{i}_temp",
                    f"gpu_{i}_mem_used",
                ])

        with output_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for snapshot in snapshots:
                row = {
                    "timestamp": snapshot.timestamp.isoformat(),
                    "cpu_percent": snapshot.cpu_percent,
                    "memory_percent": snapshot.memory_percent,
                    "disk_percent": snapshot.disk_percent,
                    "process_cpu_percent": snapshot.process_cpu_percent,
                    "process_memory_mb": snapshot.process_memory_mb,
                }

                # Add GPU data
                for i in range(snapshot.gpu_count):
                    if i < len(snapshot.gpu_utilization):
                        row[f"gpu_{i}_util"] = snapshot.gpu_utilization[i]
                    if i < len(snapshot.gpu_temperature):
                        row[f"gpu_{i}_temp"] = snapshot.gpu_temperature[i]
                    if i < len(snapshot.gpu_memory_used):
                        row[f"gpu_{i}_mem_used"] = snapshot.gpu_memory_used[i]

                writer.writerow(row)
