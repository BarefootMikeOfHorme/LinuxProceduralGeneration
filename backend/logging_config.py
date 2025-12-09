"""
VaultMind Forge - Centralized Logging Configuration
Production-grade logging with rotation, structured output, and multiple handlers
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import os
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability in development
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        return super().format(record)


def setup_logging(
    component: str = "vaultmind",
    log_level: Optional[str] = None,
    log_dir: Optional[Path] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    Setup logging for a component with both file and console handlers.

    Args:
        component: Component name (e.g., "api", "cli", "tui", "workflow")
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ./logs)
        log_to_file: Enable file logging
        log_to_console: Enable console logging

    Returns:
        Configured logger instance
    """

    # Get log level from environment or parameter
    if log_level is None:
        log_level = os.getenv("VAULTMIND_LOG_LEVEL", "INFO").upper()

    # Validate log level
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Get or create logger
    logger = logging.getLogger(f"vaultmind.{component}")
    logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # Setup file handler with rotation
    if log_to_file:
        if log_dir is None:
            # Default: ./logs directory
            log_dir = Path(__file__).parent.parent / "logs"

        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Main log file with rotation (10MB max, keep 5 backups)
        log_file = log_dir / f"{component}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Error log file (errors only)
        error_log_file = log_dir / f"{component}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)

    # Setup console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # Prevent propagation to root logger (avoids duplicate logs)
    logger.propagate = False

    logger.info(f"Logging initialized for {component} at {log_level} level")

    return logger


def setup_uvicorn_logging(log_dir: Optional[Path] = None):
    """
    Configure Uvicorn logging to use our logging system.
    Call this before starting the FastAPI server.

    Args:
        log_dir: Directory for log files (default: ./logs)
    """

    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure uvicorn access log
    access_log = log_dir / "access.log"

    uvicorn_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "access": {
                "format": '%(asctime)s | %(levelname)-8s | %(client_addr)s | "%(request_line)s" %(status_code)s',
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout"
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "access",
                "filename": str(access_log),
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5
            }
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"],
                "level": "INFO"
            },
            "uvicorn.access": {
                "handlers": ["access_file", "default"],
                "level": "INFO",
                "propagate": False
            }
        }
    }

    return uvicorn_config


def get_logger(component: str) -> logging.Logger:
    """
    Get or create a logger for a component.
    This is a convenience function for components that need logging.

    Args:
        component: Component name

    Returns:
        Logger instance
    """
    logger_name = f"vaultmind.{component}"
    logger = logging.getLogger(logger_name)

    # If logger not configured yet, set it up
    if not logger.handlers:
        return setup_logging(component)

    return logger


def log_exception(logger: logging.Logger, exc: Exception, context: str = ""):
    """
    Log an exception with full traceback and context.

    Args:
        logger: Logger instance
        exc: Exception to log
        context: Additional context message
    """
    if context:
        logger.error(f"{context}: {type(exc).__name__}: {exc}", exc_info=True)
    else:
        logger.error(f"{type(exc).__name__}: {exc}", exc_info=True)


# Create default logger for backward compatibility
default_logger = setup_logging("vaultmind")


__all__ = [
    "setup_logging",
    "setup_uvicorn_logging",
    "get_logger",
    "log_exception",
    "default_logger",
]
