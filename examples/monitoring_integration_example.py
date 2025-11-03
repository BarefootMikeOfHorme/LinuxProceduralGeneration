#!/usr/bin/env python3
"""
VaultMind Forge - Monitoring Integration Example

Shows how to integrate forge_monitor with other modules for
production monitoring of AI asset generation workflows.
"""

from pathlib import Path
import sys
import time
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "vaultmind_forge"))

from vaultmind_forge.forge_monitor import SystemMonitor, MetricsAggregator, AlertLevel
from vaultmind_forge.forge_agent import JobPlanner, OutputType, RenderStyle
from vaultmind_forge.forge_sr import SuperResolutionUpscaler, SRBackend


def alert_handler(alert):
    """Handle system alerts"""
    timestamp = alert.timestamp.strftime("%H:%M:%S")
    print(f"  ⚠️  [{timestamp}] {alert.level.value.upper()}: {alert.message}")

    if alert.level == AlertLevel.CRITICAL:
        print(f"      → Taking action: pausing generation")
        time.sleep(2)  # Simulate pause


def main():
    print("="*70)
    print("  VaultMind Forge - Monitoring Integration Demo")
    print("="*70 + "\n")

    # ========================================================================
    # Setup Monitoring with Alert Callbacks
    # ========================================================================
    print("📊 Setting up system monitoring with alerts...\n")

    monitor = SystemMonitor(
        cpu_threshold=80.0,
        memory_threshold=85.0,
        gpu_temp_threshold=80.0,
        alert_callback=alert_handler,
    )

    print("✓ Monitor initialized with thresholds:")
    print(f"  - CPU: 80%")
    print(f"  - Memory: 85%")
    print(f"  - GPU Temperature: 80°C\n")

    # ========================================================================
    # Monitor Job Planning Phase
    # ========================================================================
    print("="*70)
    print("PHASE 1: Job Planning with Resource Monitoring")
    print("="*70 + "\n")

    with monitor.track_session("job-planning"):
        planner = JobPlanner()

        # Plan multiple jobs
        jobs = []
        for i in range(5):
            job = planner.create_simple_job(
                name=f"Character Variant {i+1}",
                prompt=f"character design variation {i+1}",
                output_type=OutputType.CHARACTER_2D,
                render_style=RenderStyle.ANIME,
                width=1024,
                height=1024,
            )

            plan = planner.create_plan(job)
            jobs.append((job, plan))

            # Capture snapshot after each plan
            snapshot = monitor.capture_snapshot()

            print(f"Job {i+1}: {job.name}")
            print(f"  Est. time: {plan.estimated_time_minutes:.1f}min | "
                  f"Est. memory: {plan.estimated_memory_gb:.1f}GB")
            print(f"  Current CPU: {snapshot.cpu_percent:.1f}% | "
                  f"Memory: {snapshot.memory_percent:.1f}%\n")

            time.sleep(0.1)  # Simulate planning time

    # Get planning phase summary
    planning_summary = monitor.get_session_summary()
    print(f"\n✓ Planning phase complete:")
    print(f"  Duration: {planning_summary['duration_seconds']:.2f}s")
    print(f"  Avg CPU: {planning_summary['cpu']['avg']:.1f}%")
    print(f"  Peak memory: {planning_summary['memory']['max']:.1f}%\n")

    # ========================================================================
    # Monitor Batch Processing
    # ========================================================================
    print("="*70)
    print("PHASE 2: Batch Processing with Performance Monitoring")
    print("="*70 + "\n")

    output_dir = Path("./output/monitoring_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy images for demo
    from PIL import Image
    test_images = []
    for i in range(3):
        img_path = output_dir / f"test_image_{i}.png"
        img = Image.new('RGB', (512, 512), color=(100*i, 150, 200))
        img.save(img_path)
        test_images.append(img_path)

    print(f"Created {len(test_images)} test images for processing\n")

    # Monitor batch upscaling
    with monitor.track_session("batch-upscaling"):
        upscaler = SuperResolutionUpscaler()

        print("Starting batch upscaling...")
        print(f"{'Image':<20} {'Time (ms)':<12} {'CPU %':<10} {'Memory %':<12}")
        print("-"*60)

        for i, img_path in enumerate(test_images):
            output_path = output_dir / f"upscaled_{i}.png"

            # Capture snapshot before
            snapshot_before = monitor.capture_snapshot()

            # Upscale
            result = upscaler.upscale(
                input_path=img_path,
                output_path=output_path,
                scale_factor=2,
                backend=SRBackend.FALLBACK_LANCZOS,
            )

            # Capture snapshot after
            snapshot_after = monitor.capture_snapshot()

            print(f"{img_path.name:<20} "
                  f"{result.processing_time_ms:<12.1f} "
                  f"{snapshot_after.cpu_percent:<10.1f} "
                  f"{snapshot_after.memory_percent:<12.1f}")

            time.sleep(0.05)  # Simulate processing gap

    # Get batch processing summary
    batch_summary = monitor.get_session_summary()
    print(f"\n✓ Batch processing complete:")
    print(f"  Images processed: {len(test_images)}")
    print(f"  Total duration: {batch_summary['duration_seconds']:.2f}s")
    print(f"  Avg CPU: {batch_summary['cpu']['avg']:.1f}%")
    print(f"  Peak CPU: {batch_summary['cpu']['max']:.1f}%")
    print(f"  Avg memory: {batch_summary['memory']['avg']:.1f}%")
    print(f"  Peak memory: {batch_summary['memory']['max']:.1f}%")
    print(f"  Process memory (peak): {batch_summary['process']['memory_max_mb']:.1f} MB\n")

    # ========================================================================
    # Advanced Metrics Analysis
    # ========================================================================
    print("="*70)
    print("PHASE 3: Performance Analysis & Metrics")
    print("="*70 + "\n")

    # Generate comprehensive performance report
    report = MetricsAggregator.generate_performance_report(monitor.snapshots)

    print("📈 Performance Report\n")

    print("CPU Analysis:")
    print(f"  Mean: {report['cpu']['stats']['mean']:.1f}%")
    print(f"  Median: {report['cpu']['stats']['median']:.1f}%")
    print(f"  Std Dev: {report['cpu']['stats']['std_dev']:.1f}%")
    print(f"  95th Percentile: {report['cpu']['stats']['p95']:.1f}%")
    print(f"  99th Percentile: {report['cpu']['stats']['p99']:.1f}%")
    print(f"  Trend: {report['cpu']['trend']}")
    print(f"  Anomalies: {report['cpu']['anomaly_count']}")

    print(f"\nMemory Analysis:")
    print(f"  Mean: {report['memory']['stats']['mean']:.1f}%")
    print(f"  Median: {report['memory']['stats']['median']:.1f}%")
    print(f"  Std Dev: {report['memory']['stats']['std_dev']:.1f}%")
    print(f"  95th Percentile: {report['memory']['stats']['p95']:.1f}%")
    print(f"  Trend: {report['memory']['trend']}")
    print(f"  Anomalies: {report['memory']['anomaly_count']}")

    print(f"\nProcess Resource Usage:")
    print(f"  CPU (avg): {report['process']['cpu']['mean']:.1f}%")
    print(f"  CPU (peak): {report['process']['cpu']['max']:.1f}%")
    print(f"  Memory (avg): {report['process']['memory']['mean']:.1f} MB")
    print(f"  Memory (peak): {report['process']['memory']['max']:.1f} MB")

    if 'gpu' in report:
        print(f"\nGPU Analysis:")
        util_stats = report['gpu']['utilization']
        print(f"  Utilization (avg): {util_stats['mean']:.1f}%")
        print(f"  Utilization (peak): {util_stats['max']:.1f}%")

        if 'temperature' in report['gpu']:
            temp_stats = report['gpu']['temperature']
            print(f"  Temperature (avg): {temp_stats['mean']:.1f}°C")
            print(f"  Temperature (peak): {temp_stats['max']:.1f}°C")

    # ========================================================================
    # Export Metrics for Analysis
    # ========================================================================
    print("\n" + "="*70)
    print("PHASE 4: Exporting Metrics for External Analysis")
    print("="*70 + "\n")

    # Export to JSON
    json_path = output_dir / "monitoring_metrics.json"
    monitor.export_metrics(json_path)
    print(f"✓ Exported JSON metrics: {json_path}")

    # Export to CSV
    csv_path = output_dir / "monitoring_metrics.csv"
    MetricsAggregator.export_csv(monitor.snapshots, csv_path)
    print(f"✓ Exported CSV metrics: {csv_path}")

    print(f"\nMetrics can now be analyzed with:")
    print(f"  - Excel/LibreOffice (CSV)")
    print(f"  - Python pandas (CSV)")
    print(f"  - Monitoring tools (JSON)")
    print(f"  - Custom dashboards (JSON API)")

    # ========================================================================
    # Production Recommendations
    # ========================================================================
    print("\n" + "="*70)
    print("💡 Production Monitoring Best Practices")
    print("="*70 + "\n")

    print("Based on this session's metrics, here are recommendations:\n")

    cpu_avg = report['cpu']['stats']['mean']
    if cpu_avg > 70:
        print("  ⚠️  High average CPU usage ({:.1f}%)".format(cpu_avg))
        print("     → Consider reducing concurrent jobs")
        print("     → Enable CPU affinity for better scheduling")
    else:
        print("  ✓ CPU usage is healthy ({:.1f}%)".format(cpu_avg))

    mem_avg = report['memory']['stats']['mean']
    if mem_avg > 80:
        print(f"\n  ⚠️  High average memory usage ({mem_avg:.1f}%)")
        print("     → Consider reducing batch size")
        print("     → Enable memory monitoring alerts")
    else:
        print(f"\n  ✓ Memory usage is healthy ({mem_avg:.1f}%)")

    if report['cpu']['anomaly_count'] > 0:
        print(f"\n  📊 Detected {report['cpu']['anomaly_count']} CPU anomalies")
        print("     → Review logs for potential issues")
        print("     → Check for resource contention")

    # Current system status
    print("\n" + "="*70)
    print("Current System Status")
    print("="*70 + "\n")

    current = monitor.get_current_status()
    print(f"  Timestamp: {current['timestamp']}")
    print(f"  CPU: {current['cpu_percent']:.1f}%")
    print(f"  Memory: {current['memory_percent']:.1f}%")
    print(f"  Disk: {current['disk_percent']:.1f}%")
    print(f"  Platform: {current['platform']}")
    print(f"  Total alerts: {current['alerts_count']}")

    print("\n" + "="*70)
    print("  Monitoring Integration Demo Complete")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
