"""
VaultMind Forge - Resource Optimizer Bot
Intelligently manages batch processing resources
"""

from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from .base_bot import BaseBot, BotConfig, BotPriority
from forge_batch import BatchProcessor

logger = logging.getLogger(__name__)


@dataclass
class OptimizerConfig:
    """Resource optimizer configuration"""
    cpu_pause_threshold: float = 90.0       # Pause if CPU > 90%
    cpu_resume_threshold: float = 70.0      # Resume if CPU < 70%
    memory_pause_threshold: float = 90.0    # Pause if RAM > 90%
    memory_resume_threshold: float = 75.0   # Resume if RAM < 75%
    gpu_temp_pause_threshold: float = 85.0  # Pause if GPU > 85°C
    gpu_temp_resume_threshold: float = 75.0 # Resume if GPU < 75°C
    enable_auto_pause: bool = True          # Enable automatic pausing
    enable_auto_resume: bool = True         # Enable automatic resuming


class ResourceOptimizerBot(BaseBot):
    """
    Resource optimizer bot - manages batch processor based on system resources.

    Features:
    - Auto-pause batch processing when system is under load
    - Auto-resume when resources available
    - GPU temperature monitoring
    - Memory pressure detection
    - Configurable thresholds

    Example:
        config = BotConfig(
            name="resource_optimizer",
            check_interval_seconds=10.0  # Check every 10 seconds
        )

        optimizer_config = OptimizerConfig(
            cpu_pause_threshold=90.0,
            memory_pause_threshold=90.0,
            enable_auto_pause=True
        )

        bot = ResourceOptimizerBot(
            config=config,
            batch_processor=processor,
            optimizer_config=optimizer_config
        )
        bot.start()
    """

    def __init__(
        self,
        config: BotConfig,
        batch_processor: BatchProcessor,
        optimizer_config: Optional[OptimizerConfig] = None
    ):
        """
        Initialize resource optimizer bot.

        Args:
            config: Bot configuration
            batch_processor: BatchProcessor to manage
            optimizer_config: Optimizer configuration
        """
        super().__init__(config)

        self.batch_processor = batch_processor
        self.optimizer_config = optimizer_config or OptimizerConfig()

        # State tracking
        self.is_paused = False
        self.pause_reason: Optional[str] = None

        # Stats
        self.total_pauses = 0
        self.total_resumes = 0

        logger.info("Resource optimizer initialized")

    def execute_action(self) -> bool:
        """
        Execute optimization cycle - check resources and manage processor.

        Returns:
            True if cycle completed successfully
        """
        # Get system resources
        resources = self.batch_processor.resource_manager.get_system_resources()

        # Check if we should pause
        if self.optimizer_config.enable_auto_pause and not self.is_paused:
            pause_reason = self._check_should_pause(resources)
            if pause_reason:
                self._pause_processor(pause_reason)

        # Check if we should resume
        if self.optimizer_config.enable_auto_resume and self.is_paused:
            if self._check_should_resume(resources):
                self._resume_processor()

        return True

    def _check_should_pause(self, resources) -> Optional[str]:
        """
        Check if processor should be paused.

        Returns:
            Pause reason if should pause, None otherwise
        """
        # Check CPU
        if resources.cpu_percent > self.optimizer_config.cpu_pause_threshold:
            return f"CPU usage high: {resources.cpu_percent:.1f}%"

        # Check memory
        if resources.ram_percent > self.optimizer_config.memory_pause_threshold:
            return f"Memory usage high: {resources.ram_percent:.1f}%"

        # Check GPU temperature
        for gpu in resources.gpus:
            if gpu.temperature_celsius and gpu.temperature_celsius > self.optimizer_config.gpu_temp_pause_threshold:
                return f"GPU {gpu.gpu_id} temperature high: {gpu.temperature_celsius}°C"

        return None

    def _check_should_resume(self, resources) -> bool:
        """
        Check if processor should be resumed.

        Returns:
            True if should resume
        """
        # All thresholds must be below resume threshold
        if resources.cpu_percent > self.optimizer_config.cpu_resume_threshold:
            return False

        if resources.ram_percent > self.optimizer_config.memory_resume_threshold:
            return False

        # Check all GPUs
        for gpu in resources.gpus:
            if gpu.temperature_celsius and gpu.temperature_celsius > self.optimizer_config.gpu_temp_resume_threshold:
                return False

        return True

    def _pause_processor(self, reason: str) -> None:
        """
        Pause batch processor.

        Args:
            reason: Reason for pausing
        """
        logger.warning(f"Pausing batch processor: {reason}")

        # Pause processor (batch processor doesn't have native pause, so we track state)
        # In a real implementation, you'd implement pause/resume in BatchProcessor
        self.is_paused = True
        self.pause_reason = reason
        self.total_pauses += 1

        self.create_alert('processor_paused', reason, severity='medium')

    def _resume_processor(self) -> None:
        """Resume batch processor"""
        logger.info("Resuming batch processor")

        self.is_paused = False
        self.pause_reason = None
        self.total_resumes += 1

        self.create_alert('processor_resumed', "Resources available", severity='low')

    def get_optimizer_status(self) -> dict:
        """Get optimizer status"""
        return {
            'is_paused': self.is_paused,
            'pause_reason': self.pause_reason,
            'total_pauses': self.total_pauses,
            'total_resumes': self.total_resumes,
            'thresholds': {
                'cpu_pause': self.optimizer_config.cpu_pause_threshold,
                'cpu_resume': self.optimizer_config.cpu_resume_threshold,
                'memory_pause': self.optimizer_config.memory_pause_threshold,
                'memory_resume': self.optimizer_config.memory_resume_threshold,
                'gpu_temp_pause': self.optimizer_config.gpu_temp_pause_threshold,
                'gpu_temp_resume': self.optimizer_config.gpu_temp_resume_threshold,
            }
        }

    def print_status(self) -> None:
        """Print formatted status"""
        super().print_status()

        optimizer_status = self.get_optimizer_status()

        print(f"OPTIMIZER STATUS:")
        print(f"  Paused: {optimizer_status['is_paused']}")
        if optimizer_status['pause_reason']:
            print(f"  Reason: {optimizer_status['pause_reason']}")
        print(f"  Total Pauses: {optimizer_status['total_pauses']}")
        print(f"  Total Resumes: {optimizer_status['total_resumes']}")
        print(f"\nTHRESHOLDS:")
        thresholds = optimizer_status['thresholds']
        print(f"  CPU: {thresholds['cpu_pause']:.0f}% (pause) / {thresholds['cpu_resume']:.0f}% (resume)")
        print(f"  Memory: {thresholds['memory_pause']:.0f}% (pause) / {thresholds['memory_resume']:.0f}% (resume)")
        print(f"  GPU Temp: {thresholds['gpu_temp_pause']:.0f}°C (pause) / {thresholds['gpu_temp_resume']:.0f}°C (resume)")
        print()
