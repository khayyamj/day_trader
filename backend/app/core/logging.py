"""Logging configuration for the trading application."""
import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from pythonjsonlogger import jsonlogger
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Set up application logging with file and console handlers.

    Returns:
        Configured logger instance
    """
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger("trading_app")
    logger.setLevel(log_level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console Handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Console formatter
    console_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)

    # File Handler with JSON formatting and rotation
    file_handler = TimedRotatingFileHandler(
        filename=log_dir / "trading_app.log",
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)

    # JSON formatter for structured logging
    json_format = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"}
    )
    file_handler.setFormatter(json_format)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Create global logger instance
logger = setup_logging()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name for the logger

    Returns:
        Logger instance
    """
    return logging.getLogger(f"trading_app.{name}")
