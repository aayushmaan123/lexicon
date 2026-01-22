"""Structured logging configuration.

Provides consistent, structured logging across the application
suitable for production environments and legal audit requirements.
"""

import logging
import sys
from typing import Any

from lexicon.infrastructure.config.settings import AppConfig, LogLevel


def setup_logging(config: AppConfig) -> logging.Logger:
    """Configure structured logging for the application.

    Args:
        config: Application configuration

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("lexicon")

    # Set log level from config
    logger.setLevel(config.log_level.value)

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(config.log_level.value)

    # Format with structured information
    if config.environment.value == "production":
        # JSON-like format for production (easier to parse)
        formatter = logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","message":"%(message)s"}'
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"lexicon.{name}")
