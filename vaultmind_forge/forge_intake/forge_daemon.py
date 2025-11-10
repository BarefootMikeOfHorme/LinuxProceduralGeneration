"""
VaultMind Forge - Background Daemon Service
============================================

Runs the asset processing system as a persistent background service/daemon.
Handles file locking, graceful shutdowns, and recovery from crashes.

Based on AssetConverterPro's bot/daemon architecture.
"""

import os
import sys
import time
import signal
import logging
import threading
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from .drop_folder_monitor import DropFolderMonitor


class ForgeDaemon:
    """
    Background daemon that runs the asset processing pipeline persistently.

    Features:
    - Graceful startup/shutdown
    - Signal handling (SIGTERM, SIGINT)
    - Crash recovery with restart
    - PID file management
    - Status reporting
    - File lock management
    """

    def __init__(
        self,
        drop_folder: str,
        output_folder: str,
        pid_file: Optional[str] = None,
        log_file: Optional[str] = None,
        status_file: Optional[str] = None,
    ):
        """
        Args:
            drop_folder: Folder to monitor
            output_folder: Output folder for processed assets
            pid_file: Path to PID file (default: ./forge_daemon.pid)
            log_file: Path to log file (default: ./forge_daemon.log)
            status_file: Path to status JSON (default: ./forge_daemon_status.json)
        """
        self.drop_folder = Path(drop_folder)
        self.output_folder = Path(output_folder)

        # Daemon files
        self.pid_file = Path(pid_file or "forge_daemon.pid")
        self.log_file = Path(log_file or "forge_daemon.log")
        self.status_file = Path(status_file or "forge_daemon_status.json")

        # Monitor instance
        self.monitor: Optional[DropFolderMonitor] = None

        # State
        self.running = False
        self.start_time: Optional[datetime] = None

        # Setup logging
        self._setup_logging()

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _setup_logging(self):
        """Configure logging to file and console"""
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("ForgeDaemon")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.stop()

    def _write_pid(self):
        """Write PID file"""
        pid = os.getpid()
        with open(self.pid_file, 'w') as f:
            f.write(str(pid))
        self.logger.info(f"PID {pid} written to {self.pid_file}")

    def _remove_pid(self):
        """Remove PID file"""
        if self.pid_file.exists():
            self.pid_file.unlink()
            self.logger.info(f"PID file removed: {self.pid_file}")

    def _check_existing_instance(self) -> bool:
        """Check if daemon is already running"""
        if not self.pid_file.exists():
            return False

        # Read PID
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process exists
            if sys.platform == "win32":
                # Windows: Use tasklist
                import subprocess
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:
                # Unix: Send signal 0
                try:
                    os.kill(pid, 0)
                    return True
                except OSError:
                    return False

        except (ValueError, FileNotFoundError):
            return False

    def _update_status(self, status: str, **kwargs):
        """Update status file"""
        status_data = {
            "status": status,
            "pid": os.getpid(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "drop_folder": str(self.drop_folder),
            "output_folder": str(self.output_folder),
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }

        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)

    def start(self):
        """Start the daemon"""
        # Check for existing instance
        if self._check_existing_instance():
            self.logger.error("Daemon is already running!")
            return False

        self.logger.info("="*60)
        self.logger.info("VaultMind Forge Daemon - Starting")
        self.logger.info("="*60)
        self.logger.info(f"Drop folder: {self.drop_folder}")
        self.logger.info(f"Output folder: {self.output_folder}")
        self.logger.info(f"PID file: {self.pid_file}")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info(f"Status file: {self.status_file}")

        # Write PID file
        self._write_pid()

        # Update status
        self.running = True
        self.start_time = datetime.now()
        self._update_status("starting")

        # Create monitor
        try:
            self.monitor = DropFolderMonitor(
                drop_folder=str(self.drop_folder),
                output_folder=str(self.output_folder),
                auto_process=True,
                batch_size=10,
                batch_timeout=30.0
            )

            # Start monitoring
            self.monitor.start()
            self._update_status("running")

            self.logger.info("="*60)
            self.logger.info("Daemon started successfully")
            self.logger.info("Monitoring for new assets...")
            self.logger.info("Press Ctrl+C or send SIGTERM to stop")
            self.logger.info("="*60)

            # Run until stopped
            self._run_loop()

        except Exception as e:
            self.logger.error(f"Daemon failed to start: {e}", exc_info=True)
            self._update_status("error", error=str(e))
            self._remove_pid()
            return False

        return True

    def _run_loop(self):
        """Main daemon loop"""
        try:
            # Periodic status updates
            last_status_update = time.time()
            status_interval = 60.0  # Update status every 60 seconds

            while self.running:
                time.sleep(1)

                # Periodic status update
                current_time = time.time()
                if current_time - last_status_update >= status_interval:
                    if self.monitor:
                        self._update_status(
                            "running",
                            stats=self.monitor.stats
                        )
                    last_status_update = current_time

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            self.stop()

    def stop(self):
        """Stop the daemon gracefully"""
        if not self.running:
            return

        self.logger.info("Stopping daemon...")
        self._update_status("stopping")

        self.running = False

        # Stop monitor
        if self.monitor:
            try:
                self.monitor.stop()
            except Exception as e:
                self.logger.error(f"Error stopping monitor: {e}")

        # Update final status
        self._update_status(
            "stopped",
            stats=self.monitor.stats if self.monitor else {}
        )

        # Remove PID file
        self._remove_pid()

        self.logger.info("Daemon stopped successfully")

    def get_status(self) -> dict:
        """Get current daemon status"""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                return json.load(f)
        return {"status": "not_running"}


# =============================================================================
# Daemon Control Functions
# =============================================================================

def start_daemon(drop_folder: str, output_folder: str, **kwargs):
    """Start the daemon"""
    daemon = ForgeDaemon(drop_folder, output_folder, **kwargs)
    daemon.start()


def stop_daemon(pid_file: str = "forge_daemon.pid"):
    """Stop a running daemon"""
    pid_file = Path(pid_file)

    if not pid_file.exists():
        print("No daemon running (PID file not found)")
        return

    # Read PID
    with open(pid_file, 'r') as f:
        pid = int(f.read().strip())

    print(f"Stopping daemon (PID: {pid})...")

    # Send SIGTERM
    if sys.platform == "win32":
        import subprocess
        subprocess.run(["taskkill", "/PID", str(pid), "/F"])
    else:
        os.kill(pid, signal.SIGTERM)

    # Wait for shutdown
    time.sleep(2)

    if pid_file.exists():
        print("Daemon did not stop gracefully, removing PID file")
        pid_file.unlink()
    else:
        print("Daemon stopped successfully")


def status_daemon(status_file: str = "forge_daemon_status.json"):
    """Get daemon status"""
    status_file = Path(status_file)

    if not status_file.exists():
        print("Status: NOT RUNNING")
        return

    with open(status_file, 'r') as f:
        status = json.load(f)

    print("="*60)
    print("VaultMind Forge Daemon Status")
    print("="*60)
    print(f"Status: {status.get('status', 'unknown').upper()}")
    print(f"PID: {status.get('pid', 'N/A')}")
    print(f"Start Time: {status.get('start_time', 'N/A')}")
    print(f"Uptime: {status.get('uptime_seconds', 0):.0f} seconds")
    print(f"Drop Folder: {status.get('drop_folder', 'N/A')}")
    print(f"Output Folder: {status.get('output_folder', 'N/A')}")

    if 'stats' in status:
        stats = status['stats']
        print("\nStatistics:")
        print(f"  Files detected: {stats.get('files_detected', 0)}")
        print(f"  Files processed: {stats.get('files_processed', 0)}")
        print(f"  Files failed: {stats.get('files_failed', 0)}")
        print(f"  Batches processed: {stats.get('batches_processed', 0)}")
        print(f"  Assets created: {stats.get('assets_created', 0)}")

    print("="*60)


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """CLI for daemon control"""
    import argparse

    parser = argparse.ArgumentParser(description="VaultMind Forge - Daemon Control")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the daemon")
    start_parser.add_argument("drop_folder", help="Folder to monitor")
    start_parser.add_argument("output_folder", help="Output folder for processed assets")
    start_parser.add_argument("--pid-file", help="Path to PID file")
    start_parser.add_argument("--log-file", help="Path to log file")
    start_parser.add_argument("--status-file", help="Path to status file")

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the daemon")
    stop_parser.add_argument("--pid-file", default="forge_daemon.pid", help="Path to PID file")

    # Status command
    status_parser = subparsers.add_parser("status", help="Get daemon status")
    status_parser.add_argument("--status-file", default="forge_daemon_status.json", help="Path to status file")

    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart the daemon")
    restart_parser.add_argument("drop_folder", help="Folder to monitor")
    restart_parser.add_argument("output_folder", help="Output folder for processed assets")

    args = parser.parse_args()

    if args.command == "start":
        kwargs = {}
        if args.pid_file:
            kwargs['pid_file'] = args.pid_file
        if args.log_file:
            kwargs['log_file'] = args.log_file
        if args.status_file:
            kwargs['status_file'] = args.status_file

        start_daemon(args.drop_folder, args.output_folder, **kwargs)

    elif args.command == "stop":
        stop_daemon(args.pid_file)

    elif args.command == "status":
        status_daemon(args.status_file)

    elif args.command == "restart":
        print("Stopping existing daemon...")
        stop_daemon()
        time.sleep(2)
        print("Starting daemon...")
        start_daemon(args.drop_folder, args.output_folder)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
