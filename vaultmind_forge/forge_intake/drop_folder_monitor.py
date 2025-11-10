"""
VaultMind Forge - Drop Folder Monitor
======================================

Automated file system watcher that detects new assets and triggers processing.
Based on AssetConverterPro's architecture with enhanced capabilities.

Features:
- Real-time file system monitoring (watchdog)
- Automatic format detection and categorization
- Multi-version asset detection
- Batch processing triggers
- Metadata extraction and enhancement
- Asset repair and validation
"""

import os
import time
import json
import hashlib
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional
from collections import defaultdict
from queue import Queue, Empty

# Watchdog for file monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("[WARN] watchdog not installed. Install with: pip install watchdog")

from .multi_version_handler import MultiVersionHandler
from .unified_converter import UnifiedConverter, ConversionStatus
from .format_registry import FormatRegistry


class AssetDropHandler(FileSystemEventHandler):
    """
    Handles file system events in drop folder.
    Queues files for processing after stability check.
    """

    def __init__(self, processor_queue: Queue, stability_delay: float = 2.0):
        """
        Args:
            processor_queue: Queue for files ready to process
            stability_delay: Seconds to wait for file to stabilize
        """
        super().__init__()
        self.queue = processor_queue
        self.stability_delay = stability_delay
        self.pending_files: Dict[str, float] = {}  # filepath -> timestamp
        self.lock = threading.Lock()
        self.registry = FormatRegistry()

        # Start stability checker thread
        self.running = True
        self.checker_thread = threading.Thread(target=self._check_stability, daemon=True)
        self.checker_thread.start()

    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Check if supported format
        if not self.registry.is_supported(filepath.suffix.lower()):
            return

        print(f"[DETECT] New file: {filepath.name}")

        with self.lock:
            self.pending_files[str(filepath)] = time.time()

    def on_modified(self, event):
        """Handle file modification events (e.g., copying large files)"""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        if not self.registry.is_supported(filepath.suffix.lower()):
            return

        with self.lock:
            # Update timestamp for stability check
            self.pending_files[str(filepath)] = time.time()

    def _check_stability(self):
        """Background thread that checks file stability before queuing"""
        while self.running:
            current_time = time.time()
            stable_files = []

            with self.lock:
                for filepath, timestamp in list(self.pending_files.items()):
                    # Check if file is stable (no modifications for delay period)
                    if current_time - timestamp >= self.stability_delay:
                        # Verify file still exists and is readable
                        if Path(filepath).exists():
                            stable_files.append(filepath)
                        del self.pending_files[filepath]

            # Queue stable files for processing
            for filepath in stable_files:
                print(f"[STABLE] Ready for processing: {Path(filepath).name}")
                self.queue.put(filepath)

            time.sleep(0.5)  # Check every 500ms

    def stop(self):
        """Stop the stability checker thread"""
        self.running = False
        self.checker_thread.join(timeout=2.0)


class DropFolderMonitor:
    """
    Main drop folder monitoring system with auto-processing.
    """

    def __init__(
        self,
        drop_folder: str,
        output_folder: str,
        auto_process: bool = True,
        batch_size: int = 10,
        batch_timeout: float = 30.0
    ):
        """
        Args:
            drop_folder: Folder to monitor for new assets
            output_folder: Folder for processed assets
            auto_process: Automatically process detected files
            batch_size: Process when this many files accumulated
            batch_timeout: Process after this many seconds even if batch incomplete
        """
        self.drop_folder = Path(drop_folder)
        self.output_folder = Path(output_folder)
        self.auto_process = auto_process
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout

        # Create directories
        self.drop_folder.mkdir(parents=True, exist_ok=True)
        self.output_folder.mkdir(parents=True, exist_ok=True)

        # Processing queue
        self.queue = Queue()

        # Processors
        self.mv_handler = MultiVersionHandler()
        self.converter = UnifiedConverter()

        # Observer and handler
        if not WATCHDOG_AVAILABLE:
            raise ImportError("watchdog library required. Install with: pip install watchdog")

        self.observer = Observer()
        self.event_handler = AssetDropHandler(self.queue)

        # Processing state
        self.running = False
        self.processor_thread = None
        self.batch_buffer: List[str] = []
        self.last_batch_time = time.time()

        # Statistics
        self.stats = {
            "files_detected": 0,
            "files_processed": 0,
            "files_failed": 0,
            "batches_processed": 0,
            "assets_created": 0,
        }

    def start(self):
        """Start monitoring the drop folder"""
        print(f"[*] Starting drop folder monitor")
        print(f"    Drop folder: {self.drop_folder}")
        print(f"    Output folder: {self.output_folder}")
        print(f"    Auto-process: {self.auto_process}")
        print(f"    Batch size: {self.batch_size}")
        print(f"    Batch timeout: {self.batch_timeout}s")

        self.running = True

        # Start file system observer
        self.observer.schedule(self.event_handler, str(self.drop_folder), recursive=True)
        self.observer.start()
        print(f"[+] Watching: {self.drop_folder}")

        if self.auto_process:
            # Start processing thread
            self.processor_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.processor_thread.start()
            print(f"[+] Auto-processing enabled")

    def stop(self):
        """Stop monitoring"""
        print(f"\n[*] Stopping drop folder monitor...")
        self.running = False

        # Stop observer
        self.observer.stop()
        self.observer.join()

        # Stop event handler
        self.event_handler.stop()

        # Wait for processor thread
        if self.processor_thread:
            self.processor_thread.join(timeout=5.0)

        # Process remaining files
        if self.batch_buffer:
            print(f"[*] Processing remaining {len(self.batch_buffer)} files...")
            self._process_batch(self.batch_buffer)

        print(f"[+] Stopped")
        self._print_stats()

    def _process_loop(self):
        """Background thread that processes queued files"""
        while self.running:
            try:
                # Get file from queue (with timeout)
                filepath = self.queue.get(timeout=1.0)
                self.stats["files_detected"] += 1

                # Add to batch buffer
                self.batch_buffer.append(filepath)
                print(f"[QUEUE] Added to batch: {Path(filepath).name} ({len(self.batch_buffer)}/{self.batch_size})")

                # Check if batch is ready
                batch_full = len(self.batch_buffer) >= self.batch_size
                batch_timeout = (time.time() - self.last_batch_time) >= self.batch_timeout

                if batch_full or (batch_timeout and self.batch_buffer):
                    self._process_batch(self.batch_buffer)
                    self.batch_buffer = []
                    self.last_batch_time = time.time()

            except Empty:
                # Check for timeout-based batch processing
                if self.batch_buffer and (time.time() - self.last_batch_time) >= self.batch_timeout:
                    self._process_batch(self.batch_buffer)
                    self.batch_buffer = []
                    self.last_batch_time = time.time()
                continue

    def _process_batch(self, filepaths: List[str]):
        """Process a batch of files"""
        if not filepaths:
            return

        print(f"\n[BATCH] Processing {len(filepaths)} files...")
        self.stats["batches_processed"] += 1

        # Convert to Path objects
        paths = [Path(fp) for fp in filepaths]

        # Compute hashes
        asset_id_map = {}
        for path in paths:
            try:
                asset_id = self._compute_hash(path)
                asset_id_map[path] = asset_id
            except Exception as e:
                print(f"[ERROR] Failed to hash {path.name}: {e}")
                self.stats["files_failed"] += 1

        # Group by asset name (multi-version detection)
        groups = self.mv_handler.group_asset_variants(list(asset_id_map.keys()))
        print(f"[*] Detected {len(groups)} unique assets")

        # Process each asset group
        for asset_name, variants in groups.items():
            try:
                # Get primary variant
                primary = self.mv_handler.select_primary_variant(variants)
                asset_id = asset_id_map[primary.filepath]

                print(f"[>>] {asset_name}")
                if len(variants) > 1:
                    print(f"    Multi-version: {len(variants)} formats detected")
                    for v in variants:
                        print(f"      - {v.format}")

                # Merge and convert
                result = self.mv_handler.merge_variants(variants, asset_id)

                if result.status == ConversionStatus.SUCCESS:
                    # Save outputs
                    self._save_vaf_outputs(asset_id, asset_name, result)

                    self.stats["assets_created"] += 1
                    self.stats["files_processed"] += len(variants)
                    print(f"    [+] Success! Asset created")

                    # Move processed files to archive (optional)
                    # self._archive_processed_files(variants)

                else:
                    print(f"    [ERROR] Conversion failed: {result.errors}")
                    self.stats["files_failed"] += len(variants)

            except Exception as e:
                print(f"[ERROR] Processing {asset_name}: {e}")
                self.stats["files_failed"] += 1

        print(f"[+] Batch complete\n")

    def _save_vaf_outputs(self, asset_id: str, asset_name: str, result):
        """Save VAF-Full and VAF-Catalog"""
        # Create asset directory
        asset_dir = self.output_folder / asset_name
        asset_dir.mkdir(parents=True, exist_ok=True)

        # Save VAF-Full
        vaf_full_path = asset_dir / f"{asset_id}.vaf.full.json"
        with open(vaf_full_path, 'w', encoding='utf-8') as f:
            json.dump(result.vaf_full, f, indent=2)

        # Save VAF-Catalog
        vaf_catalog_path = asset_dir / f"{asset_id}.vaf.catalog.json"
        with open(vaf_catalog_path, 'w', encoding='utf-8') as f:
            json.dump(result.vaf_catalog, f, indent=2)

        # Save lineage
        lineage_path = asset_dir / f"{asset_id}.lineage.json"
        lineage = result.vaf_full.get("lineage", {})
        with open(lineage_path, 'w', encoding='utf-8') as f:
            json.dump(lineage, f, indent=2)

    def _compute_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _print_stats(self):
        """Print processing statistics"""
        print(f"\n{'='*60}")
        print(f"DROP FOLDER MONITOR STATISTICS")
        print(f"{'='*60}")
        print(f"Files detected:    {self.stats['files_detected']}")
        print(f"Files processed:   {self.stats['files_processed']}")
        print(f"Files failed:      {self.stats['files_failed']}")
        print(f"Batches processed: {self.stats['batches_processed']}")
        print(f"Assets created:    {self.stats['assets_created']}")
        print(f"{'='*60}")

    def run_interactive(self):
        """Run in interactive mode (blocking)"""
        self.start()

        print(f"\n[*] Drop folder monitor running")
        print(f"[*] Drop files into: {self.drop_folder}")
        print(f"[*] Press Ctrl+C to stop\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n[*] Interrupt received")
            self.stop()


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Run drop folder monitor from CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="VaultMind Forge - Drop Folder Monitor")
    parser.add_argument("drop_folder", help="Folder to monitor for new assets")
    parser.add_argument("output_folder", help="Folder for processed assets")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size (default: 10)")
    parser.add_argument("--batch-timeout", type=float, default=30.0, help="Batch timeout in seconds (default: 30)")
    parser.add_argument("--no-auto", action="store_true", help="Disable auto-processing")

    args = parser.parse_args()

    monitor = DropFolderMonitor(
        drop_folder=args.drop_folder,
        output_folder=args.output_folder,
        auto_process=not args.no_auto,
        batch_size=args.batch_size,
        batch_timeout=args.batch_timeout,
    )

    monitor.run_interactive()


if __name__ == "__main__":
    main()
