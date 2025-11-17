"""
VaultMind Forge - Production Logging System
Comprehensive logging with file rotation, syslog, structured output, and error tracking

L1-ACP Enhancement - Repair Priority #3
Replaces console.print() with production-grade logging while preserving Rich terminal UI
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
import traceback
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from vaultmind_forge.config import get_config

config = get_config()


# ============================================================================
# Structured Log Entry
# ============================================================================

@dataclass
class LogEntry:
    """Structured log entry for JSON logging"""
    timestamp: str
    level: str
    logger: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    process: Optional[int] = None
    thread: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


# ============================================================================
# Custom Formatters
# ============================================================================

class StructuredFormatter(logging.Formatter):
    """JSON structured logging formatter for machine parsing"""

    def format(self, record: logging.LogRecord) -> str:
        entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line=record.lineno,
            process=record.process,
            thread=record.threadName,
        )

        # Add exception info if present
        if record.exc_info:
            entry.error = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, 'extra'):
            entry.extra = record.extra

        return entry.to_json()


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter with timestamps"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level_colored = f"{color}{record.levelname:8s}{reset}"

        # Format: 2025-11-17 12:34:56 [INFO    ] module.function:123 - Message
        return f"{timestamp} [{level_colored}] {record.name}:{record.lineno} - {record.getMessage()}"


# ============================================================================
# Error Aggregator
# ============================================================================

class ErrorAggregator:
    """Aggregate and track errors for debugging"""

    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.errors: list[Dict[str, Any]] = []
        self.error_counts: Dict[str, int] = {}

    def add_error(self, record: logging.LogRecord):
        """Add error to aggregator"""
        error_key = f"{record.module}:{record.funcName}:{record.levelname}"

        error_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        if record.exc_info:
            error_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }

        self.errors.append(error_entry)
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Limit size
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]

    def get_summary(self) -> Dict[str, Any]:
        """Get error summary"""
        return {
            "total_errors": len(self.errors),
            "error_counts": self.error_counts,
            "recent_errors": self.errors[-10:] if self.errors else []
        }

    def save_to_file(self, path: Path):
        """Save error log to file"""
        with open(path, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": self.get_summary(),
                "all_errors": self.errors
            }, f, indent=2)


# Global error aggregator
_error_aggregator = ErrorAggregator()


# ============================================================================
# Custom Handler with Error Aggregation
# ============================================================================

class AggregatingHandler(logging.Handler):
    """Handler that aggregates errors for debugging"""

    def emit(self, record: logging.LogRecord):
        if record.levelno >= logging.ERROR:
            _error_aggregator.add_error(record)


# ============================================================================
# Logger Setup
# ============================================================================

def setup_logging(
    name: str = "vaultmind_forge",
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    enable_syslog: bool = False,
    enable_console: bool = True,
    enable_json: bool = False,
) -> logging.Logger:
    """
    Setup comprehensive logging for VaultMind Forge

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (enables file logging with rotation)
        enable_syslog: Enable syslog handler
        enable_console: Enable console output
        enable_json: Use JSON structured logging in file

    Returns:
        Configured logger instance
    """
    # Get logger
    logger = logging.getLogger(name)

    # Clear existing handlers
    logger.handlers.clear()

    # Set level from config or parameter
    log_level = level or config.logging.log_level
    logger.setLevel(getattr(logging, log_level.upper()))

    # ========================================================================
    # Console Handler (colored, human-readable)
    # ========================================================================
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Console gets INFO+
        console_handler.setFormatter(ColoredConsoleFormatter())
        logger.addHandler(console_handler)

    # ========================================================================
    # File Handler (rotating, structured or text)
    # ========================================================================
    if log_file or config.logging.log_to_file:
        file_path = log_file or config.logging.log_file_path

        if file_path:
            # Ensure directory exists
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Rotating file handler (100MB max, 5 backups)
            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=100 * 1024 * 1024,  # 100MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)  # File gets everything

            # Choose formatter
            if enable_json:
                file_handler.setFormatter(StructuredFormatter())
            else:
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s [%(levelname)-8s] %(name)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                ))

            logger.addHandler(file_handler)

    # ========================================================================
    # Syslog Handler (Unix/Windows)
    # ========================================================================
    if enable_syslog or config.logging.log_to_syslog:
        try:
            syslog_address = config.logging.syslog_address

            # Handle Windows vs Unix
            if sys.platform == 'win32':
                # Windows: use UDP to localhost
                syslog_address = ('localhost', 514)

            syslog_handler = logging.handlers.SysLogHandler(address=syslog_address)
            syslog_handler.setLevel(logging.WARNING)  # Syslog gets WARNING+
            syslog_handler.setFormatter(logging.Formatter(
                '%(name)s[%(process)d]: %(levelname)s - %(message)s'
            ))
            logger.addHandler(syslog_handler)
        except Exception as e:
            # Non-fatal if syslog unavailable
            print(f"Warning: Could not enable syslog: {e}")

    # ========================================================================
    # Error Aggregation Handler
    # ========================================================================
    aggregating_handler = AggregatingHandler()
    aggregating_handler.setLevel(logging.ERROR)
    logger.addHandler(aggregating_handler)

    # Don't propagate to root logger
    logger.propagate = False

    return logger


# ============================================================================
# Convenience Functions
# ============================================================================

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with VaultMind Forge configuration

    Args:
        name: Module name (use __name__)

    Returns:
        Configured logger
    """
    return logging.getLogger(f"vaultmind_forge.{name}")


def get_error_summary() -> Dict[str, Any]:
    """Get aggregated error summary"""
    return _error_aggregator.get_summary()


def save_error_log(path: Optional[Path] = None):
    """Save error log to file"""
    if path is None:
        path = config.paths.output_dir / f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    path.parent.mkdir(parents=True, exist_ok=True)
    _error_aggregator.save_to_file(path)
    return path


def configure_root_logger():
    """Configure the root vaultmind_forge logger"""
    return setup_logging(
        name="vaultmind_forge",
        log_file=config.logging.log_file_path if config.logging.log_to_file else None,
        enable_syslog=config.logging.log_to_syslog,
        enable_console=True,
        enable_json=False,  # Human-readable for file
    )


# ============================================================================
# Initialize on import
# ============================================================================

# Setup root logger on module import
_root_logger = configure_root_logger()


__all__ = [
    "setup_logging",
    "get_logger",
    "get_error_summary",
    "save_error_log",
    "configure_root_logger",
    "LogEntry",
    "StructuredFormatter",
    "ColoredConsoleFormatter",
]
