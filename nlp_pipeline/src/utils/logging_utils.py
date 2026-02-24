"""Logging configuration."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


_CONFIGURED = False


def get_logger(name: str, level: str | None = None) -> logging.Logger:
    """Return a named logger with console + optional file handler."""
    global _CONFIGURED

    logger = logging.getLogger(name)

    if not _CONFIGURED:
        log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)
        logger.setLevel(log_level)

        # Console handler
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(log_level)
        fmt = logging.Formatter(
            "[%(asctime)s] %(name)s %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console.setFormatter(fmt)
        logger.addHandler(console)
        _CONFIGURED = True

    return logger


def add_file_handler(logger: logging.Logger, path: str | Path) -> None:
    """Add a file handler to an existing logger."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(str(p), encoding="utf-8")
    fh.setLevel(logger.level)
    fmt = logging.Formatter(
        "[%(asctime)s] %(name)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)
