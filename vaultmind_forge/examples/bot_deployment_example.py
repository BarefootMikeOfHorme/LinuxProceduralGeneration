"""
VaultMind Forge - Bot Deployment Example
Demonstrates how to deploy and manage automation bots
"""

import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from forge_batch import BatchProcessor
from forge_bots import (
    BotScheduler,
    BotType,
    BotPriority,
    ScheduleConfig
)


def example_1_asset_monitor():
    """Example 1: Deploy Asset Monitor Bot"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Asset Monitor Bot")
    print("="*80)

    # Create batch processor
    processor = BatchProcessor(max_workers=4)

    # Create scheduler
    scheduler = BotScheduler(
        config=ScheduleConfig(enable_health_monitoring=True),
        batch_processor=processor
    )

    # Deploy asset monitor
    scheduler.deploy_bot(
        bot_type=BotType.ASSET_MONITOR,
        name="folder_watcher_1",
        config={
            'bot_config': {
                'check_interval_seconds': 30.0,  # Check every 30 seconds
            },
            'watch_folders': [
                {
                    'path': Path('watched/models'),
                    'pattern': '**/*.fbx',
                    'output_type': 'character',
                    'target_engines': ['unity', 'unreal'],
                    'job_priority': 'NORMAL'
                },
                {
                    'path': Path('watched/textures'),
                    'pattern': '**/*.png',
                    'output_type': 'texture',
                    'target_engines': ['unity'],
                    'job_priority': 'LOW'
                }
            ]
        },
        priority=BotPriority.HIGH,
        auto_start=True
    )

    print("\n✓ Asset monitor deployed")
    print("  - Watching: watched/models (*.fbx)")
    print("  - Watching: watched/textures (*.png)")
    print("  - Auto-submits jobs to batch processor")

    # Run for a bit
    time.sleep(5)

    # Show status
    scheduler.print_dashboard()

    # Stop
    scheduler.stop_all()


def example_2_qa_bot():
    """Example 2: Deploy QA Bot"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Quality Assurance Bot")
    print("="*80)

    scheduler = BotScheduler()

    # Deploy QA bot
    scheduler.deploy_bot(
        bot_type=BotType.QA_BOT,
        name="qa_scanner",
        config={
            'bot_config': {
                'check_interval_seconds': 3600.0,  # Every hour
            },
            'qa_config': {
                'asset_library_path': Path('output/assets'),
                'validation_patterns': ['**/*.fbx', '**/*.png', '**/*.dds'],
                'min_quality_threshold': 0.7,
                'report_path': Path('reports/qa'),
                'auto_repair': False
            }
        },
        auto_start=True
    )

    print("\n✓ QA bot deployed")
    print("  - Scanning: output/assets")
    print("  - Check interval: 1 hour")
    print("  - Reports: reports/qa")

    time.sleep(5)
    scheduler.print_dashboard()
    scheduler.stop_all()


def example_3_optimizer_bot():
    """Example 3: Deploy Resource Optimizer Bot"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Resource Optimizer Bot")
    print("="*80)

    processor = BatchProcessor(max_workers=4)
    scheduler = BotScheduler(batch_processor=processor)

    # Deploy optimizer
    scheduler.deploy_bot(
        bot_type=BotType.OPTIMIZER,
        name="resource_optimizer",
        config={
            'bot_config': {
                'check_interval_seconds': 10.0,  # Check every 10 seconds
            },
            'optimizer_config': {
                'cpu_pause_threshold': 90.0,
                'cpu_resume_threshold': 70.0,
                'memory_pause_threshold': 90.0,
                'memory_resume_threshold': 75.0,
                'gpu_temp_pause_threshold': 85.0,
                'gpu_temp_resume_threshold': 75.0,
                'enable_auto_pause': True,
                'enable_auto_resume': True
            }
        },
        priority=BotPriority.CRITICAL,  # High priority for resource management
        auto_start=True
    )

    print("\n✓ Optimizer bot deployed")
    print("  - Auto-pauses batch processing when system is under load")
    print("  - Auto-resumes when resources available")
    print("  - Thresholds: CPU 90%, Memory 90%, GPU 85°C")

    time.sleep(5)
    scheduler.print_dashboard()
    scheduler.stop_all()


def example_4_lineage_bot():
    """Example 4: Deploy Lineage Inspector Bot"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Lineage Inspector Bot")
    print("="*80)

    scheduler = BotScheduler()

    # Deploy lineage inspector
    scheduler.deploy_bot(
        bot_type=BotType.LINEAGE_INSPECTOR,
        name="lineage_inspector",
        config={
            'bot_config': {
                'check_interval_seconds': 1800.0,  # Every 30 minutes
            },
            'lineage_config': {
                'lineage_db_path': Path('lineage'),
                'asset_library_path': Path('output/assets'),
                'check_orphans': True,
                'check_broken_chains': True,
                'check_missing_files': True
            }
        },
        auto_start=True
    )

    print("\n✓ Lineage inspector deployed")
    print("  - Monitors: lineage database integrity")
    print("  - Detects: orphans, broken chains, missing files")
    print("  - Check interval: 30 minutes")

    time.sleep(5)
    scheduler.print_dashboard()
    scheduler.stop_all()


def example_5_full_deployment():
    """Example 5: Full Bot Deployment"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Full Bot Deployment")
    print("="*80)
    print("Deploying complete automation suite...\n")

    # Create batch processor
    processor = BatchProcessor(max_workers=4)

    # Create scheduler with full config
    scheduler = BotScheduler(
        config=ScheduleConfig(
            enable_health_monitoring=True,
            health_check_interval=60.0,
            enable_metrics_export=True,
            metrics_export_interval=300.0,
            metrics_export_path=Path('metrics'),
            enable_auto_restart=True,
            max_restart_attempts=3
        ),
        batch_processor=processor
    )

    # Deploy asset monitor
    scheduler.deploy_bot(
        bot_type=BotType.ASSET_MONITOR,
        name="asset_monitor",
        config={
            'bot_config': {'check_interval_seconds': 30.0},
            'watch_folders': [
                {
                    'path': Path('watched/models'),
                    'pattern': '**/*.fbx',
                    'output_type': 'character',
                    'target_engines': ['unity', 'unreal']
                }
            ]
        },
        priority=BotPriority.HIGH
    )

    # Deploy QA bot
    scheduler.deploy_bot(
        bot_type=BotType.QA_BOT,
        name="qa_bot",
        config={
            'bot_config': {'check_interval_seconds': 3600.0},
            'qa_config': {
                'asset_library_path': Path('output/assets'),
                'report_path': Path('reports/qa')
            }
        },
        priority=BotPriority.NORMAL
    )

    # Deploy optimizer
    scheduler.deploy_bot(
        bot_type=BotType.OPTIMIZER,
        name="optimizer",
        config={
            'bot_config': {'check_interval_seconds': 10.0},
            'optimizer_config': {
                'cpu_pause_threshold': 90.0,
                'memory_pause_threshold': 90.0
            }
        },
        priority=BotPriority.CRITICAL
    )

    # Deploy lineage inspector
    scheduler.deploy_bot(
        bot_type=BotType.LINEAGE_INSPECTOR,
        name="lineage_inspector",
        config={
            'bot_config': {'check_interval_seconds': 1800.0},
            'lineage_config': {
                'lineage_db_path': Path('lineage'),
                'asset_library_path': Path('output/assets')
            }
        },
        priority=BotPriority.LOW
    )

    print("✓ All bots deployed!\n")

    # Start all bots
    scheduler.start_all()
    print("✓ All bots started\n")

    # Run for a bit
    print("Running for 15 seconds...\n")
    for i in range(3):
        time.sleep(5)
        print(f"[{(i+1)*5}s] Running...")

    # Show dashboard
    scheduler.print_dashboard()

    # Run health check
    print("\nRunning health check...")
    health = scheduler.run_health_check()
    print("Health Status:")
    for bot_name, status in health.items():
        print(f"  {bot_name}: {status}")

    # Export metrics
    print("\nExporting metrics...")
    scheduler.export_metrics()

    # Save configuration
    print("Saving configuration...")
    scheduler.save_configuration(Path('bot_config.json'))

    # Stop all
    print("\nStopping all bots...")
    scheduler.stop_all()

    print("\n✓ Example complete!")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("VAULTMIND FORGE - BOT DEPLOYMENT EXAMPLES")
    print("="*80)

    # Run examples
    # example_1_asset_monitor()
    # example_2_qa_bot()
    # example_3_optimizer_bot()
    # example_4_lineage_bot()
    example_5_full_deployment()

    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETE")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
