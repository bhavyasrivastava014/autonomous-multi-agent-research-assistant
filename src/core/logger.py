"""Centralized logging using loguru."""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger

from src.core.config import settings


def setup_logger() -> Any:
    """Configure console and rotating file logs once."""

    logger.remove()
    logger.configure(extra={"request_id": "-"})

    logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        colorize=True,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | "
            "{name}:{function}:{line} | {extra[request_id]} | {message}"
        ),
    )

    logger.add(
        str(settings.log_file),
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        enqueue=False,
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
    )

    logger.add(
        str(settings.log_file.with_suffix(".json")),
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        enqueue=False,
        serialize=True,
        encoding="utf-8",
    )

    return logger


setup_logger()

__all__ = ["logger", "setup_logger"]
