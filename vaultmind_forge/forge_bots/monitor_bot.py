"""
VaultMind Forge - Asset Monitor Bot
Watches folders for new assets and auto-submits to batch queue
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from datetime import datetime
import logging

# Add parent to path for imports

from .base_bot import BaseBot, BotConfig, BotPriority
from forge_batch import BatchProcessor, BatchJob, JobPriority

logger = logging.getLogger(__name__)


@dataclass
class FolderWatchConfig:
    """Configuration for folder watching"""
    path: Path
    pattern: str = "**/*"  # Glob pattern
    recursive: bool = True
    output_type: str = "model"
    target_engines: List[str] = field(default_factory=lambda: ["unity"])
    job_priority: JobPriority = JobPriority.NORMAL
    is_hero_asset: bool = False


class AssetMonitorBot(BaseBot):
    """
    Asset monitoring bot - watches folders and auto-submits jobs.

    Features:
    - Multiple folder watching with different configs
    - Pattern-based filtering (*.fbx, *.png, etc.)
    - Automatic job submission to batch processor
    - Duplicate detection (won't submit same file twice)
    - File modification tracking
    - Configurable per-folder settings

    Example:
        config = BotConfig(
            name="asset_monitor",
            check_interval_seconds=30.0
        )

        watch_configs = [
            FolderWatchConfig(
                path=Path("watched/models"),
                pattern="**/*.fbx",
                output_type="character",
                target_engines=["unity", "unreal"]
            ),
            FolderWatchConfig(
                path=Path("watched/textures"),
                pattern="**/*.png",
                output_type="texture",
                target_engines=["unity"]
            )
        ]

        bot = AssetMonitorBot(
            config=config,
            batch_processor=processor,
            watch_configs=watch_configs
        )
        bot.start()
    """

    def __init__(
        self,
        config: BotConfig,
        batch_processor: BatchProcessor,
        watch_configs: List[FolderWatchConfig]
    ):
        """
        Initialize asset monitor bot.

        Args:
            config: Bot configuration
            batch_processor: BatchProcessor instance
            watch_configs: List of folder watch configurations
        """
        super().__init__(config)

        self.batch_processor = batch_processor
        self.watch_configs = watch_configs

        # Track processed files
        self.processed_files: Set[Path] = set()
        self.file_timestamps: Dict[Path, float] = {}

        # Stats
        self.files_detected = 0
        self.jobs_submitted = 0
        self.duplicates_skipped = 0

        logger.info(f"Asset monitor initialized with {len(watch_configs)} watch folders")

    def execute_action(self) -> bool:
        """
        Execute monitoring cycle - check folders for new files.

        Returns:
            True if cycle completed successfully
        """
        new_files_found = False

        for watch_config in self.watch_configs:
            # Ensure folder exists
            if not watch_config.path.exists():
                logger.warning(f"Watch folder does not exist: {watch_config.path}")
                continue

            # Scan for files matching pattern
            if watch_config.recursive:
                files = list(watch_config.path.glob(watch_config.pattern))
            else:
                files = list(watch_config.path.glob(watch_config.pattern.replace("**/", "")))

            # Process each file
            for file_path in files:
                if not file_path.is_file():
                    continue

                # Check if file was already processed
                if file_path in self.processed_files:
                    # Check if file was modified
                    current_mtime = file_path.stat().st_mtime
                    previous_mtime = self.file_timestamps.get(file_path, 0)

                    if current_mtime <= previous_mtime:
                        continue  # No change, skip

                    logger.info(f"File modified, reprocessing: {file_path}")

                # Process new/modified file
                try:
                    self._process_file(file_path, watch_config)
                    new_files_found = True
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    self.create_alert('file_processing_error', f"Failed to process {file_path}: {e}", severity='medium')

        return True

    def _process_file(self, file_path: Path, config: FolderWatchConfig) -> None:
        """
        Process detected file - submit job to batch processor.

        Args:
            file_path: Path to file
            config: Watch configuration for this file
        """
        self.files_detected += 1

        # Mark as processed
        self.processed_files.add(file_path)
        self.file_timestamps[file_path] = file_path.stat().st_mtime

        # Create batch job
        job = BatchJob(
            prompt=f"Convert {file_path.stem}",  # Use filename as prompt
            output_type=config.output_type,
            target_engines=config.target_engines,
            priority=config.job_priority,
            is_hero_asset=config.is_hero_asset,
            generation_params={
                'source_file': str(file_path),
                'auto_submitted': True,
                'watch_folder': str(config.path),
            }
        )

        # Submit to batch processor
        job_id = self.batch_processor.submit_job(job)
        self.jobs_submitted += 1

        logger.info(f"Job submitted: {job_id} for file {file_path}")
        self.create_alert('job_submitted', f"Auto-submitted job {job_id} for {file_path.name}", severity='low')

    def add_watch_folder(self, config: FolderWatchConfig) -> None:
        """Add new watch folder at runtime"""
        self.watch_configs.append(config)
        logger.info(f"Added watch folder: {config.path}")

    def remove_watch_folder(self, path: Path) -> bool:
        """Remove watch folder by path"""
        original_count = len(self.watch_configs)
        self.watch_configs = [c for c in self.watch_configs if c.path != path]
        removed = len(self.watch_configs) < original_count

        if removed:
            logger.info(f"Removed watch folder: {path}")

        return removed

    def get_watch_status(self) -> Dict:
        """Get watch folder status"""
        return {
            'watch_folders': len(self.watch_configs),
            'files_detected': self.files_detected,
            'jobs_submitted': self.jobs_submitted,
            'duplicates_skipped': self.duplicates_skipped,
            'processed_files': len(self.processed_files),
            'folders': [
                {
                    'path': str(config.path),
                    'pattern': config.pattern,
                    'output_type': config.output_type,
                    'engines': config.target_engines,
                    'exists': config.path.exists(),
                }
                for config in self.watch_configs
            ]
        }

    def print_status(self) -> None:
        """Print formatted status"""
        super().print_status()

        watch_status = self.get_watch_status()

        print(f"WATCH STATUS:")
        print(f"  Watch Folders: {watch_status['watch_folders']}")
        print(f"  Files Detected: {watch_status['files_detected']}")
        print(f"  Jobs Submitted: {watch_status['jobs_submitted']}")
        print(f"  Processed Files: {watch_status['processed_files']}")
        print(f"\nFOLDERS:")

        for folder in watch_status['folders']:
            status_icon = "[OK]" if folder['exists'] else "[X]"
            print(f"  {status_icon} {folder['path']}")
            print(f"    Pattern: {folder['pattern']}")
            print(f"    Type: {folder['output_type']} -> {', '.join(folder['engines'])}")

        print()


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """CLI entry point for standalone execution"""
    import argparse

    parser = argparse.ArgumentParser(description="VaultMind Forge - Asset Monitor Bot")
    parser.add_argument('--watch', required=True, help="Folder to watch")
    parser.add_argument('--pattern', default="**/*", help="File pattern (e.g. *.fbx)")
    parser.add_argument('--output-type', default="model", help="Output type")
    parser.add_argument('--engines', default="unity", help="Target engines (comma-separated)")
    parser.add_argument('--interval', type=float, default=30.0, help="Check interval (seconds)")
    parser.add_argument('--log', help="Log file path")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create batch processor (mock for standalone)
    from forge_batch import BatchProcessor
    processor = BatchProcessor(max_workers=2)

    # Create bot config
    config = BotConfig(
        name="asset_monitor",
        check_interval_seconds=args.interval,
        log_file=Path(args.log) if args.log else None,
        priority=BotPriority.NORMAL
    )

    # Create watch config
    watch_config = FolderWatchConfig(
        path=Path(args.watch),
        pattern=args.pattern,
        output_type=args.output_type,
        target_engines=args.engines.split(','),
        job_priority=JobPriority.NORMAL
    )

    # Create and start bot
    bot = AssetMonitorBot(
        config=config,
        batch_processor=processor,
        watch_configs=[watch_config]
    )

    print(f"\nAsset Monitor Bot Started")
    print(f"Watching: {args.watch}")
    print(f"Pattern: {args.pattern}")
    print(f"Check interval: {args.interval}s")
    print(f"Press Ctrl+C to stop\n")

    try:
        bot.start(daemon=False)
        while bot.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bot...")
        bot.stop()
        print("Bot stopped")


if __name__ == '__main__':
    main()
