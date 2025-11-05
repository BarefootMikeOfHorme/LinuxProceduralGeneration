# VaultMind Forge - Bot Framework

Automated helper bots for intelligent asset pipeline management.

## Overview

The VaultMind Forge bot framework provides **intelligent automation helpers** that run continuously in the background, monitoring and optimizing your asset pipeline. Inspired by daemon patterns from `protocol_daemon.py` and `monitor_cli.py`.

## Architecture

```
forge_bots/
├── base_bot.py          # Base class for all bots
├── monitor_bot.py       # Asset folder monitoring
├── qa_bot.py            # Quality assurance scanner
├── optimizer_bot.py     # Resource optimization
├── lineage_bot.py       # Lineage integrity checker
└── scheduler.py         # Central bot manager
```

## Available Bots

### 1. Asset Monitor Bot

**Purpose**: Watches folders for new assets and auto-submits jobs to batch queue.

**Features**:
- Multi-folder watching with different configs
- Pattern-based filtering (`*.fbx`, `*.png`, etc.)
- Automatic job submission
- Duplicate detection
- File modification tracking

**Use Case**: Drop an FBX file into `watched/models/` → Bot automatically submits conversion job to batch processor.

**Example**:
```python
from forge_bots import BotScheduler, BotType
from forge_batch import BatchProcessor

processor = BatchProcessor(max_workers=4)
scheduler = BotScheduler(batch_processor=processor)

scheduler.deploy_bot(
    bot_type=BotType.ASSET_MONITOR,
    name="folder_watcher",
    config={
        'bot_config': {
            'check_interval_seconds': 30.0  # Check every 30 seconds
        },
        'watch_folders': [
            {
                'path': Path('watched/models'),
                'pattern': '**/*.fbx',
                'output_type': 'character',
                'target_engines': ['unity', 'unreal'],
                'job_priority': 'NORMAL'
            }
        ]
    },
    auto_start=True
)
```

### 2. Quality Assurance Bot

**Purpose**: Continuously validates asset library quality.

**Features**:
- Scheduled library scanning
- Quality metrics tracking
- Issue detection and reporting
- Optional auto-repair
- Historical trend analysis

**Use Case**: Nightly scan of asset library, create report of validation failures.

**Example**:
```python
scheduler.deploy_bot(
    bot_type=BotType.QA_BOT,
    name="qa_scanner",
    config={
        'bot_config': {
            'check_interval_seconds': 3600.0  # Every hour
        },
        'qa_config': {
            'asset_library_path': Path('output/assets'),
            'validation_patterns': ['**/*.fbx', '**/*.png'],
            'min_quality_threshold': 0.7,
            'report_path': Path('reports/qa'),
            'auto_repair': False
        }
    },
    auto_start=True
)
```

### 3. Resource Optimizer Bot

**Purpose**: Intelligently manages batch processing based on system resources.

**Features**:
- Auto-pause when system under load
- Auto-resume when resources available
- GPU temperature monitoring
- Memory pressure detection
- Configurable thresholds

**Use Case**: Pause batch processing when GPU needed for gaming, auto-resume when idle.

**Example**:
```python
scheduler.deploy_bot(
    bot_type=BotType.OPTIMIZER,
    name="resource_optimizer",
    config={
        'bot_config': {
            'check_interval_seconds': 10.0  # Check every 10 seconds
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
    priority=BotPriority.CRITICAL,
    auto_start=True
)
```

### 4. Lineage Inspector Bot

**Purpose**: Monitors asset lineage database integrity.

**Features**:
- Orphan detection (assets without parents)
- Broken chain detection (missing parent references)
- Missing file detection (lineage exists but file doesn't)
- Integrity reporting

**Use Case**: Weekly report of orphaned assets or broken genealogy chains.

**Example**:
```python
scheduler.deploy_bot(
    bot_type=BotType.LINEAGE_INSPECTOR,
    name="lineage_inspector",
    config={
        'bot_config': {
            'check_interval_seconds': 1800.0  # Every 30 minutes
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
```

## Bot Manager (Scheduler)

The `BotScheduler` is the central orchestration system for all bots.

**Features**:
- Deploy multiple bot types
- Monitor bot health
- Automatic failure recovery
- Centralized metrics
- Alert aggregation
- Configuration management

### Quick Start

```python
from forge_bots import BotScheduler, BotType, ScheduleConfig
from forge_batch import BatchProcessor

# Create batch processor
processor = BatchProcessor(max_workers=4)

# Create scheduler
scheduler = BotScheduler(
    config=ScheduleConfig(
        enable_health_monitoring=True,
        enable_metrics_export=True,
        metrics_export_path=Path('metrics'),
        enable_auto_restart=True
    ),
    batch_processor=processor
)

# Deploy bots
scheduler.deploy_bot(BotType.ASSET_MONITOR, name="monitor", config={...})
scheduler.deploy_bot(BotType.QA_BOT, name="qa", config={...})
scheduler.deploy_bot(BotType.OPTIMIZER, name="optimizer", config={...})
scheduler.deploy_bot(BotType.LINEAGE_INSPECTOR, name="lineage", config={...})

# Start all bots
scheduler.start_all()

# Monitor
scheduler.print_dashboard()

# Stop all
scheduler.stop_all()
```

### Bot Control

```python
# Start/stop individual bots
scheduler.start_bot("monitor")
scheduler.stop_bot("monitor")

# Pause/resume
scheduler.pause_bot("optimizer")
scheduler.resume_bot("optimizer")

# Remove bot
scheduler.remove_bot("old_bot")

# Health check
health = scheduler.run_health_check()

# Export metrics
scheduler.export_metrics()

# Save/load configuration
scheduler.save_configuration(Path('config.json'))
scheduler.load_configuration(Path('config.json'))
```

## Base Bot Class

All bots inherit from `BaseBot`, which provides:

### Core Features
- **Threaded execution** with daemon mode
- **Health monitoring** and metrics
- **Alert system** for notifications
- **Pause/resume** capability
- **Configurable retry logic**
- **Comprehensive logging**

### Creating Custom Bots

```python
from forge_bots import BaseBot, BotConfig

class MyCustomBot(BaseBot):
    def __init__(self, config: BotConfig, my_params):
        super().__init__(config)
        self.my_params = my_params

    def execute_action(self) -> bool:
        """Main bot action (called each cycle)"""
        # Do bot work here
        print(f"Running cycle with {self.my_params}")

        # Create alerts if needed
        if some_condition:
            self.create_alert('issue_detected', 'Found problem', severity='high')

        return True

    def before_cycle(self) -> None:
        """Optional: Called before each cycle"""
        pass

    def after_cycle(self, success: bool) -> None:
        """Optional: Called after each cycle"""
        pass

# Use custom bot
config = BotConfig(name="my_bot", check_interval_seconds=60.0)
bot = MyCustomBot(config, my_params="test")
bot.start()
```

## Bot Priorities

Bots can be assigned priorities to influence scheduling:

- `BotPriority.CRITICAL` (20): Resource optimizer, system critical
- `BotPriority.HIGH` (10): Asset monitor, time-sensitive
- `BotPriority.NORMAL` (5): QA bot, regular maintenance
- `BotPriority.LOW` (1): Lineage inspector, background tasks

## Alert System

Bots generate alerts that propagate to the scheduler:

```python
# Bot generates alert
self.create_alert(
    alert_type='high_load',
    message='CPU usage exceeds threshold',
    severity='medium'  # low, medium, high, critical
)

# Scheduler aggregates alerts
scheduler.alerts  # List of all alerts from all bots

# Configure alert callback
def alert_handler(alert):
    print(f"[{alert['severity']}] {alert['bot']}: {alert['message']}")

config = ScheduleConfig(alert_callback=alert_handler)
scheduler = BotScheduler(config=config)
```

## Metrics and Monitoring

### Bot Metrics

Each bot tracks:
- Uptime
- Total cycles
- Successful/failed actions
- Total alerts
- Average cycle duration

```python
metrics = bot.get_metrics()
print(f"Uptime: {metrics['uptime_hours']:.2f} hours")
print(f"Success rate: {metrics['successful_actions']}/{metrics['total_cycles']}")
```

### Aggregate Metrics

Scheduler provides aggregate view:

```python
metrics = scheduler.get_aggregate_metrics()
print(f"Total bots: {metrics['total_bots']}")
print(f"Active bots: {metrics['active_bots']}")
print(f"Total successful actions: {metrics['total_successful_actions']}")
```

### Dashboard

```python
scheduler.print_dashboard()
```

Output:
```
================================================================================
VAULTMIND FORGE - BOT MANAGER DASHBOARD
================================================================================
Uptime: 2.5 hours
Bots: 4/4 active
Alerts: 3 active

BOT STATUS----------------------------------------------------------------------
  ✓ asset_monitor                RUNNING       Priority: HIGH
  ✓ qa_scanner                   RUNNING       Priority: NORMAL
  ✓ optimizer                    RUNNING       Priority: CRITICAL
  ✓ lineage_inspector            RUNNING       Priority: LOW

PERFORMANCE---------------------------------------------------------------------
  Total Cycles: 1523
  Successful Actions: 1498
  Failed Actions: 25

RECENT ALERTS-------------------------------------------------------------------
  [MEDIUM] optimizer: CPU usage high: 91.2%
  [LOW] asset_monitor: Auto-submitted job abc123
  [HIGH] qa_bot: Found 5 failed assets in scan
================================================================================
```

## Configuration Files

Save/load bot configurations:

```python
# Save
scheduler.save_configuration(Path('bot_config.json'))

# Produces:
{
  "scheduler_config": {
    "enable_health_monitoring": true,
    "health_check_interval": 60.0,
    "enable_auto_restart": true,
    "max_restart_attempts": 3
  },
  "bots": {
    "asset_monitor": {
      "type": "asset_monitor",
      "status": {"running": true, "enabled": true},
      "config": {"check_interval_seconds": 30.0, "priority": 10}
    },
    ...
  }
}
```

## Standalone Bot Execution

Each bot can run standalone:

```bash
# Asset monitor
python -m forge_bots.monitor_bot --watch watched/models --pattern "**/*.fbx" --engines unity,unreal

# QA bot (implement CLI as needed)
# Optimizer bot (implement CLI as needed)
# Lineage bot (implement CLI as needed)
```

## Integration with VaultMind Forge

The bot framework integrates seamlessly with the rest of VaultMind Forge:

### With Batch Processor

```python
from forge_batch import BatchProcessor
from forge_bots import BotScheduler, BotType

processor = BatchProcessor(max_workers=4)
scheduler = BotScheduler(batch_processor=processor)

# Asset monitor submits jobs to processor
scheduler.deploy_bot(BotType.ASSET_MONITOR, ...)

# Optimizer manages processor resources
scheduler.deploy_bot(BotType.OPTIMIZER, ...)
```

### With Validator

```python
# QA bot uses forge_validator
from forge_validator import Validator

class QualityAssuranceBot(BaseBot):
    def __init__(self, config, qa_config):
        super().__init__(config)
        self.validator = Validator(threshold=qa_config.min_quality_threshold)

    def _validate_asset(self, file_path):
        return self.validator.validate_asset(file_path)
```

### With Lineage Tracker

```python
# Lineage bot uses forge_lineage
from forge_lineage import LineageTracker

class LineageInspectorBot(BaseBot):
    def __init__(self, config, lineage_config):
        super().__init__(config)
        self.tracker = LineageTracker(lineage_config.lineage_db_path)

    def _check_orphans(self):
        # Use tracker to find orphans
        pass
```

## Performance Considerations

- **Check intervals**: Set appropriate intervals for each bot type
  - Asset monitor: 30-60 seconds
  - QA bot: 1-24 hours
  - Optimizer: 5-10 seconds
  - Lineage inspector: 30-60 minutes

- **Resource usage**: Bots run in separate threads, minimal overhead

- **Daemon mode**: Bots run as daemon threads by default (stop when main thread exits)

## Examples

See `examples/bot_deployment_example.py` for comprehensive examples:
1. Asset Monitor Bot
2. QA Bot
3. Optimizer Bot
4. Lineage Inspector Bot
5. Full Deployment (all bots together)

## Troubleshooting

### Bot not starting
- Check `bot.config.enabled` is True
- Verify required dependencies (e.g., BatchProcessor for optimizer)

### Bot in ERROR state
- Check logs: `bot.config.log_file`
- Enable auto-restart: `ScheduleConfig(enable_auto_restart=True)`

### High CPU usage
- Increase `check_interval_seconds`
- Reduce number of active bots

### Alerts not appearing
- Verify alert callback: `config.alert_callback`
- Check alert list: `scheduler.alerts`

## Future Enhancements

Potential bot additions:
- **Format Migration Bot**: Bulk-convert legacy assets to modern formats
- **Batch Job Optimizer Bot**: Analyze job history, suggest better parameters
- **Asset Tagging Bot**: Auto-tag assets based on content analysis
- **Dependency Resolver Bot**: Analyze dependencies, optimize batch job order

## License

Part of VaultMind Forge asset pipeline system.
