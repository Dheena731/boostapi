"""Structured logging via Loguru."""

from __future__ import annotations

import sys

from loguru import logger

# Remove the default handler
logger.remove()

# Console output — coloured, human-readable
logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
        "<level>{message}</level>"
    ),
    level="DEBUG",
    colorize=True,
    enqueue=True,  # Thread-safe async queue
)

# Rotating file log for production
logger.add(
    "logs/boostapi.log",
    rotation="50 MB",
    retention="30 days",
    compression="gz",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} — {message}",
    level="INFO",
    enqueue=True,
    catch=True,
)

__all__ = ["logger"]
