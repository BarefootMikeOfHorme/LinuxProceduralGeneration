"""
VaultMind Forge - Base Bot
Foundation for all automation bots
"""

from __future__ import annotations

import time
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import json

logger = logging.getLogger(__name__)


class BotStatus(Enum):
    """Bot operational status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class BotPriority(Enum):
    """Bot execution priority"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class BotConfig:
    """Base bot configuration"""
    name: str
    enabled: bool = True
    check_interval_seconds: float = 60.0
    log_file: Optional[Path] = None
    enable_logging: bool = True
    max_retries: int = 3
    alert_callback: Optional[Callable] = None
    priority: BotPriority = BotPriority.NORMAL


@dataclass
class BotMetrics:
    """Bot performance metrics"""
    uptime_start: datetime = field(default_factory=datetime.now)
    total_cycles: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    total_alerts: int = 0
    last_action_time: Optional[datetime] = None
    average_cycle_duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'uptime_hours': (datetime.now() - self.uptime_start).total_seconds() / 3600,
            'total_cycles': self.total_cycles,
            'successful_actions': self.successful_actions,
            'failed_actions': self.failed_actions,
            'total_alerts': self.total_alerts,
            'last_action': self.last_action_time.isoformat() if self.last_action_time else None,
            'avg_cycle_duration': self.average_cycle_duration,
        }


class BaseBot(ABC):
    """
    Base class for all VaultMind Forge bots.

    Features:
    - Threaded execution with daemon mode
    - Health monitoring and metrics
    - Alert system
    - Pause/resume capability
    - Configurable retry logic
    - Comprehensive logging

    Example:
        class MyBot(BaseBot):
            def execute_action(self) -> bool:
                # Do bot work
                return True

        bot = MyBot(BotConfig(name="my_bot"))
        bot.start()
    """

    def __init__(self, config: BotConfig):
        """
        Initialize base bot.

        Args:
            config: Bot configuration
        """
        self.config = config
        self.status = BotStatus.IDLE
        self.running = False
        self.paused = False

        # Metrics
        self.metrics = BotMetrics()

        # Threading
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()

        # Alerts
        self.alerts: List[Dict[str, Any]] = []
        self.max_alerts = 100

        # Setup logging
        if self.config.enable_logging:
            self._setup_logging()

        logger.info(f"Bot initialized: {self.config.name}")

    def _setup_logging(self) -> None:
        """Setup bot-specific logging"""
        if self.config.log_file:
            handler = logging.FileHandler(self.config.log_file)
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(handler)

    # ========================================================================
    # Core Bot Lifecycle
    # ========================================================================

    @abstractmethod
    def execute_action(self) -> bool:
        """
        Execute bot's primary action (must be implemented by subclass).

        Returns:
            True if action successful, False otherwise
        """
        pass

    def before_cycle(self) -> None:
        """Hook called before each cycle (optional override)"""
        pass

    def after_cycle(self, success: bool) -> None:
        """Hook called after each cycle (optional override)"""
        pass

    def _run_cycle(self) -> None:
        """Run single bot cycle"""
        cycle_start = time.time()

        try:
            # Check if paused
            if self.paused:
                self._pause_event.wait()

            # Pre-cycle hook
            self.before_cycle()

            # Execute main action with retry logic
            success = False
            for attempt in range(self.config.max_retries):
                try:
                    success = self.execute_action()
                    if success:
                        self.metrics.successful_actions += 1
                        break
                except Exception as e:
                    logger.error(f"Bot action failed (attempt {attempt + 1}/{self.config.max_retries}): {e}")
                    if attempt == self.config.max_retries - 1:
                        self.metrics.failed_actions += 1
                        self.create_alert('execution_failed', f"Action failed after {self.config.max_retries} attempts: {e}", severity='high')
                    time.sleep(1.0)  # Brief delay before retry

            # Post-cycle hook
            self.after_cycle(success)

            # Update metrics
            self.metrics.total_cycles += 1
            self.metrics.last_action_time = datetime.now()

            cycle_duration = time.time() - cycle_start
            # Update rolling average
            self.metrics.average_cycle_duration = (
                (self.metrics.average_cycle_duration * (self.metrics.total_cycles - 1) + cycle_duration)
                / self.metrics.total_cycles
            )

        except Exception as e:
            logger.error(f"Cycle error: {e}", exc_info=True)
            self.status = BotStatus.ERROR
            self.create_alert('cycle_error', f"Cycle error: {e}", severity='critical')

    def _run_loop(self) -> None:
        """Main bot execution loop"""
        self.status = BotStatus.RUNNING
        logger.info(f"Bot started: {self.config.name}")

        while not self._stop_event.is_set():
            self._run_cycle()
            time.sleep(self.config.check_interval_seconds)

        self.status = BotStatus.STOPPED
        logger.info(f"Bot stopped: {self.config.name}")

    # ========================================================================
    # Bot Control
    # ========================================================================

    def start(self, daemon: bool = True) -> None:
        """
        Start bot execution.

        Args:
            daemon: Run as daemon thread
        """
        if self.running:
            logger.warning("Bot already running")
            return

        if not self.config.enabled:
            logger.warning("Bot is disabled")
            return

        self.running = True
        self._stop_event.clear()
        self._pause_event.set()  # Not paused initially

        self._thread = threading.Thread(target=self._run_loop, daemon=daemon)
        self._thread.start()

        logger.info(f"Bot started: {self.config.name} (daemon={daemon})")

    def stop(self, wait: bool = True) -> None:
        """
        Stop bot execution.

        Args:
            wait: Wait for bot to finish current cycle
        """
        if not self.running:
            return

        self.running = False
        self._stop_event.set()
        self._pause_event.set()  # Unpause if paused

        if wait and self._thread:
            self._thread.join(timeout=10.0)

        logger.info(f"Bot stopped: {self.config.name}")

    def pause(self) -> None:
        """Pause bot execution"""
        if self.paused:
            return

        self.paused = True
        self._pause_event.clear()
        self.status = BotStatus.PAUSED
        logger.info(f"Bot paused: {self.config.name}")

    def resume(self) -> None:
        """Resume bot execution"""
        if not self.paused:
            return

        self.paused = False
        self._pause_event.set()
        self.status = BotStatus.RUNNING
        logger.info(f"Bot resumed: {self.config.name}")

    # ========================================================================
    # Alert System
    # ========================================================================

    def create_alert(self, alert_type: str, message: str, severity: str = 'medium') -> None:
        """
        Create alert.

        Args:
            alert_type: Alert type
            message: Alert message
            severity: Severity (low, medium, high, critical)
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'bot': self.config.name,
            'type': alert_type,
            'severity': severity,
            'message': message,
        }

        self.alerts.append(alert)
        self.metrics.total_alerts += 1

        # Keep alerts within limit
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]

        logger.warning(f"ALERT [{severity.upper()}] {alert_type}: {message}")

        # Trigger callback
        if self.config.alert_callback:
            try:
                self.config.alert_callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def clear_alerts(self) -> int:
        """Clear all alerts"""
        count = len(self.alerts)
        self.alerts = []
        return count

    # ========================================================================
    # Status and Metrics
    # ========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get bot status"""
        return {
            'name': self.config.name,
            'status': self.status.value,
            'enabled': self.config.enabled,
            'running': self.running,
            'paused': self.paused,
            'priority': self.config.priority.value,
            'check_interval': self.config.check_interval_seconds,
            'active_alerts': len(self.alerts),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get bot metrics"""
        return self.metrics.to_dict()

    def print_status(self) -> None:
        """Print formatted status"""
        status = self.get_status()
        metrics = self.get_metrics()

        print(f"\n{'='*60}")
        print(f"BOT STATUS: {self.config.name}")
        print(f"{'='*60}")
        print(f"Status: {status['status'].upper()}")
        print(f"Enabled: {status['enabled']}")
        print(f"Priority: {status['priority']}")
        print(f"Alerts: {status['active_alerts']}")
        print(f"\nMETRICS:")
        print(f"  Uptime: {metrics['uptime_hours']:.2f} hours")
        print(f"  Cycles: {metrics['total_cycles']}")
        print(f"  Successful: {metrics['successful_actions']}")
        print(f"  Failed: {metrics['failed_actions']}")
        print(f"  Avg Duration: {metrics['avg_cycle_duration']:.3f}s")
        print(f"{'='*60}\n")

    def export_metrics(self, output_path: Path) -> None:
        """Export metrics to JSON"""
        data = {
            'bot': self.config.name,
            'status': self.get_status(),
            'metrics': self.get_metrics(),
            'alerts': self.alerts,
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Metrics exported to {output_path}")
