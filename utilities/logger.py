"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Logger Utility
============================================================
Provides a centralized, colored, multi-handler logging
system that writes to both console and rotating log files.
============================================================
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
import colorlog
from config.config import LOG_LEVEL, LOG_FILE, LOG_DIR


# ── ANSI Color Map for Log Levels ───────────────────────────
LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

# ── Log Formats ─────────────────────────────────────────────
CONSOLE_FORMAT = "%(log_color)s%(asctime)s [%(levelname)8s]%(reset)s %(name)s:%(lineno)d - %(message)s"
FILE_FORMAT = "%(asctime)s [%(levelname)8s] %(name)s:%(filename)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ── Max log file size: 10 MB, keep 5 backups ────────────────
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# ── Registry of created loggers (avoid duplicate handlers) ──
_logger_registry: dict[str, logging.Logger] = {}


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get or create a named logger with console + file handlers.
    
    DESIGN PATTERN: Factory pattern with registry to ensure
    each module gets its own logger but handlers aren't duplicated.
    
    Args:
        name: Logger name (usually __name__ of the calling module)
        level: Override log level (defaults to config LOG_LEVEL)
    
    Returns:
        logging.Logger: Configured logger instance
    
    Usage:
        from utilities.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Test started")
        logger.error("Test failed: %s", error_msg)
    """
    # Return existing logger if already created
    if name in _logger_registry:
        return _logger_registry[name]

    logger = logging.getLogger(name)

    # Prevent adding duplicate handlers if logger already exists in logging module
    if logger.handlers:
        _logger_registry[name] = logger
        return logger

    # Set logging level
    log_level = getattr(logging, (level or LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(log_level)

    # ── Console Handler (colored output) ────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    colored_formatter = colorlog.ColoredFormatter(
        fmt=CONSOLE_FORMAT,
        datefmt=DATE_FORMAT,
        log_colors=LOG_COLORS,
    )
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)

    # ── Rotating File Handler ───────────────────────────────
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # Always write DEBUG to file
    file_formatter = logging.Formatter(fmt=FILE_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Prevent propagation to root logger (avoids duplicate logs)
    logger.propagate = False

    _logger_registry[name] = logger
    return logger


def get_test_logger(test_name: str) -> logging.Logger:
    """
    Get a logger specifically for a test case with test-specific log file.
    
    Args:
        test_name: Name of the test (used for log file naming)
    
    Returns:
        logging.Logger: Test-specific logger
    """
    test_log_dir = LOG_DIR / "test_logs"
    test_log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(f"test.{test_name}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Test-specific file handler
    test_log_file = test_log_dir / f"{test_name}.log"
    handler = RotatingFileHandler(
        filename=test_log_file,
        maxBytes=MAX_BYTES,
        backupCount=2,
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(fmt=FILE_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(handler)
    logger.propagate = True  # Also log to parent (general log file)

    return logger


# ── Module-level framework logger ───────────────────────────
framework_logger = get_logger("framework")
