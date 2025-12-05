"""
VaultMind Forge - Bot Scheduler & Manager
Central orchestration for all automation bots

Inspired by protocol_daemon.py patterns
"""

from __future__ import annotations

import sys
import time
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type
from datetime import datetime
from enum import Enum
import logging

# Add parent to path

from .base_bot import BaseBot, BotConfig, BotStatus, BotPriority
from .monitor_bot import AssetMonitorBot, FolderWatchConfig
from .qa_bot import QualityAssuranceBot, QAConfig
from .optimizer_bot import ResourceOptimizerBot, OptimizerConfig
from .lineage_bot import LineageInspectorBot, LineageConfig

logger = logging.getLogger(__name__)


class BotType(Enum):
    """Available bot types"""
    ASSET_MONITOR = "asset_monitor"
    QA_BOT = "qa_bot"
    OPTIMIZER = "optimizer"
    LINEAGE_INSPECTOR = "lineage_inspector"


@dataclass
class ScheduleConfig:
    """Bot scheduler configuration"""
    enable_health_monitoring: bool = True
    health_check_interval: float = 60.0  # Check every minute
    enable_metrics_export: bool = True
    metrics_export_interval: float = 300.0  # Export every 5 minutes
    metrics_export_path: Optional[Path] = None
    enable_auto_restart: bool = True  # Restart failed bots
    max_restart_attempts: int = 3
    alert_callback: Optional[callable] = None


class BotScheduler:
    """
    Bot Scheduler - Central manager for all automation bots.

    Features:
    - Deploy multiple bot types
    - Monitor bot health
    - Automatic failure recovery
    - Centralized metrics
    - Alert aggregation
    - Configuration management

    Example:
        scheduler = BotScheduler(
            config=ScheduleConfig(enable_health_monitoring=True)
        )

        # Deploy asset monitor
        scheduler.deploy_bot(
            BotType.ASSET_MONITOR,
            name="folder_watcher",
            config={
                'watch_folders': [
                    {'path': 'watched/models', 'pattern': '**.fbx'}
                ]
            }
        )

        # Deploy QA bot
        scheduler.deploy_bot(
            BotType.QA_BOT,
            name="qa_scanner",
            config={'asset_library_path': 'output/assets'}
        )

        # Start all bots
        scheduler.start_all()

        # Monitor
        scheduler.print_dashboard()
    """

    def __init__(
        self,
        config: Optional[ScheduleConfig] = None,
        batch_processor: Optional['BatchProcessor'] = None
    ):
        """
        Initialize bot scheduler.

        Args:
            config: Scheduler configuration
            batch_processor: BatchProcessor instance (for bots that need it)
        """
        self.config = config or ScheduleConfig()
        self.batch_processor = batch_processor

        # Bot registry
        self.bots: Dict[str, BaseBot] = {}
        self.bot_types: Dict[str, BotType] = {}
        self.restart_counts: Dict[str, int] = {}

        # Metrics
        self.start_time = datetime.now()
        self.last_health_check = datetime.now()
        self.last_metrics_export = datetime.now()

        # Alerts
        self.alerts: List[Dict] = []
        self.max_alerts = 500

        logger.info("Bot scheduler initialized")

    # ========================================================================
    # Bot Deployment
    # ========================================================================

    def deploy_bot(
        self,
        bot_type: BotType,
        name: str,
        config: Dict,
        priority: BotPriority = BotPriority.NORMAL,
        auto_start: bool = False
    ) -> str:
        """
        Deploy a bot.

        Args:
            bot_type: Type of bot to deploy
            name: Unique bot name
            config: Bot-specific configuration
            priority: Bot priority
            auto_start: Start bot immediately

        Returns:
            Bot name
        """
        if name in self.bots:
            raise ValueError(f"Bot with name '{name}' already exists")

        # Create bot config
        bot_config = BotConfig(
            name=name,
            priority=priority,
            alert_callback=self._handle_bot_alert,
            **config.get('bot_config', {})
        )

        # Create bot based on type
        bot = self._create_bot(bot_type, bot_config, config)

        # Register bot
        self.bots[name] = bot
        self.bot_types[name] = bot_type
        self.restart_counts[name] = 0

        logger.info(f"Bot deployed: {name} ({bot_type.value})")

        if auto_start:
            bot.start()

        return name

    def _create_bot(
        self,
        bot_type: BotType,
        bot_config: BotConfig,
        config: Dict
    ) -> BaseBot:
        """
        Create bot instance.

        Args:
            bot_type: Bot type
            bot_config: Bot configuration
            config: Type-specific configuration

        Returns:
            Bot instance
        """
        if bot_type == BotType.ASSET_MONITOR:
            if not self.batch_processor:
                raise ValueError("Asset monitor requires batch_processor")

            watch_configs = [
                FolderWatchConfig(**wc) for wc in config.get('watch_folders', [])
            ]

            return AssetMonitorBot(
                config=bot_config,
                batch_processor=self.batch_processor,
                watch_configs=watch_configs
            )

        elif bot_type == BotType.QA_BOT:
            qa_config = QAConfig(**config.get('qa_config', {}))
            return QualityAssuranceBot(bot_config, qa_config)

        elif bot_type == BotType.OPTIMIZER:
            if not self.batch_processor:
                raise ValueError("Optimizer requires batch_processor")

            optimizer_config = OptimizerConfig(**config.get('optimizer_config', {}))
            return ResourceOptimizerBot(bot_config, self.batch_processor, optimizer_config)

        elif bot_type == BotType.LINEAGE_INSPECTOR:
            lineage_config = LineageConfig(**config.get('lineage_config', {}))
            return LineageInspectorBot(bot_config, lineage_config)

        else:
            raise ValueError(f"Unknown bot type: {bot_type}")

    # ========================================================================
    # Bot Control
    # ========================================================================

    def start_all(self) -> None:
        """Start all bots"""
        for name, bot in self.bots.items():
            if not bot.running and bot.config.enabled:
                bot.start()
                logger.info(f"Started bot: {name}")

    def stop_all(self, wait: bool = True) -> None:
        """Stop all bots"""
        for name, bot in self.bots.items():
            if bot.running:
                bot.stop(wait=wait)
                logger.info(f"Stopped bot: {name}")

    def start_bot(self, name: str) -> bool:
        """Start specific bot"""
        if name not in self.bots:
            return False

        bot = self.bots[name]
        if not bot.running and bot.config.enabled:
            bot.start()
            logger.info(f"Started bot: {name}")
            return True

        return False

    def stop_bot(self, name: str, wait: bool = True) -> bool:
        """Stop specific bot"""
        if name not in self.bots:
            return False

        bot = self.bots[name]
        if bot.running:
            bot.stop(wait=wait)
            logger.info(f"Stopped bot: {name}")
            return True

        return False

    def pause_bot(self, name: str) -> bool:
        """Pause specific bot"""
        if name not in self.bots:
            return False

        self.bots[name].pause()
        return True

    def resume_bot(self, name: str) -> bool:
        """Resume specific bot"""
        if name not in self.bots:
            return False

        self.bots[name].resume()
        return True

    def remove_bot(self, name: str) -> bool:
        """Remove bot"""
        if name not in self.bots:
            return False

        bot = self.bots[name]
        if bot.running:
            bot.stop()

        del self.bots[name]
        del self.bot_types[name]
        del self.restart_counts[name]

        logger.info(f"Removed bot: {name}")
        return True

    # ========================================================================
    # Health Monitoring
    # ========================================================================

    def _handle_bot_alert(self, alert: Dict) -> None:
        """Handle alert from bot"""
        self.alerts.append(alert)

        # Keep alerts within limit
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]

        # Trigger scheduler callback
        if self.config.alert_callback:
            try:
                self.config.alert_callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def run_health_check(self) -> Dict[str, str]:
        """
        Run health check on all bots.

        Returns:
            Dict mapping bot name to health status
        """
        health_status = {}

        for name, bot in self.bots.items():
            status = bot.status

            if status == BotStatus.ERROR:
                health_status[name] = 'error'

                # Attempt restart if enabled
                if self.config.enable_auto_restart:
                    if self.restart_counts[name] < self.config.max_restart_attempts:
                        logger.warning(f"Attempting to restart bot: {name}")
                        bot.stop(wait=False)
                        time.sleep(1.0)
                        bot.start()
                        self.restart_counts[name] += 1
                    else:
                        logger.error(f"Bot {name} exceeded restart attempts")
                        health_status[name] = 'failed'

            elif status == BotStatus.STOPPED:
                health_status[name] = 'stopped'
            elif status == BotStatus.PAUSED:
                health_status[name] = 'paused'
            elif status == BotStatus.RUNNING:
                health_status[name] = 'healthy'
            else:
                health_status[name] = 'idle'

        self.last_health_check = datetime.now()
        return health_status

    # ========================================================================
    # Metrics and Reporting
    # ========================================================================

    def get_aggregate_metrics(self) -> Dict:
        """Get aggregate metrics from all bots"""
        uptime = (datetime.now() - self.start_time).total_seconds() / 3600

        total_cycles = 0
        total_successful = 0
        total_failed = 0
        total_alerts = 0

        bot_metrics = {}

        for name, bot in self.bots.items():
            metrics = bot.get_metrics()
            bot_metrics[name] = metrics

            total_cycles += metrics.get('total_cycles', 0)
            total_successful += metrics.get('successful_actions', 0)
            total_failed += metrics.get('failed_actions', 0)
            total_alerts += metrics.get('total_alerts', 0)

        return {
            'uptime_hours': uptime,
            'total_bots': len(self.bots),
            'active_bots': sum(1 for b in self.bots.values() if b.running),
            'total_cycles': total_cycles,
            'total_successful_actions': total_successful,
            'total_failed_actions': total_failed,
            'total_alerts': total_alerts,
            'active_alerts': len(self.alerts),
            'bot_metrics': bot_metrics,
        }

    def export_metrics(self) -> None:
        """Export metrics to file"""
        if not self.config.metrics_export_path:
            return

        metrics = self.get_aggregate_metrics()
        metrics['timestamp'] = datetime.now().isoformat()

        # Add bot statuses
        metrics['bot_statuses'] = {
            name: bot.get_status() for name, bot in self.bots.items()
        }

        # Export
        output_file = self.config.metrics_export_path / f"bot_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Metrics exported: {output_file}")
        self.last_metrics_export = datetime.now()

    def print_dashboard(self) -> None:
        """Print comprehensive bot dashboard"""
        metrics = self.get_aggregate_metrics()
        health = self.run_health_check()

        print(f"\n{'='*80}")
        print(f"VAULTMIND FORGE - BOT MANAGER DASHBOARD")
        print(f"{'='*80}")
        print(f"Uptime: {metrics['uptime_hours']:.2f} hours")
        print(f"Bots: {metrics['active_bots']}/{metrics['total_bots']} active")
        print(f"Alerts: {metrics['active_alerts']} active")

        print(f"\n{'BOT STATUS':-^80}")
        for name, bot in self.bots.items():
            status = bot.status.value.upper()
            health_icon = "[OK]" if health[name] == 'healthy' else ("[WARN]" if health[name] in ['paused', 'idle'] else "[X]")
            priority = bot.config.priority.name
            print(f"  {health_icon} {name:<30} {status:<12} Priority: {priority}")

        print(f"\n{'PERFORMANCE':-^80}")
        print(f"  Total Cycles: {metrics['total_cycles']}")
        print(f"  Successful Actions: {metrics['total_successful_actions']}")
        print(f"  Failed Actions: {metrics['total_failed_actions']}")

        if metrics['active_alerts'] > 0:
            print(f"\n{'RECENT ALERTS':-^80}")
            for alert in self.alerts[-5:]:
                severity = alert['severity'].upper()
                bot_name = alert['bot']
                message = alert['message']
                print(f"  [{severity}] {bot_name}: {message}")

        print(f"{'='*80}\n")

    # ========================================================================
    # Configuration Management
    # ========================================================================

    def save_configuration(self, output_path: Path) -> None:
        """Save current bot configuration"""
        config_data = {
            'scheduler_config': {
                'enable_health_monitoring': self.config.enable_health_monitoring,
                'health_check_interval': self.config.health_check_interval,
                'enable_metrics_export': self.config.enable_metrics_export,
                'metrics_export_interval': self.config.metrics_export_interval,
                'enable_auto_restart': self.config.enable_auto_restart,
                'max_restart_attempts': self.config.max_restart_attempts,
            },
            'bots': {}
        }

        # Save bot configurations
        for name, bot in self.bots.items():
            config_data['bots'][name] = {
                'type': self.bot_types[name].value,
                'status': bot.get_status(),
                'config': {
                    'enabled': bot.config.enabled,
                    'check_interval_seconds': bot.config.check_interval_seconds,
                    'priority': bot.config.priority.value,
                }
            }

        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"Configuration saved: {output_path}")

    def load_configuration(self, config_path: Path) -> None:
        """Load bot configuration"""
        with open(config_path, 'r') as f:
            config_data = json.load(f)

        logger.info(f"Configuration loaded: {config_path}")
        # Note: Actual bot deployment would need to be done manually
        # as we can't serialize all bot-specific configs easily
