"""Shared utilities: logging, YAML/JSON I/O, and path helpers."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

_CONFIGURED = False


def get_logger(name: str, level: str | None = None) -> logging.Logger:
    """Return a named logger with console handler."""
    global _CONFIGURED

    logger = logging.getLogger(name)

    if not _CONFIGURED:
        log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)
        logger.setLevel(log_level)

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


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: str | Path) -> Any:
    """Load a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSONL file (one JSON object per line)."""
    records: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_no} of {path}: {exc}"
                ) from exc
    return records


def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """Save data as a JSON file."""
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def ensure_dir(path: str | Path) -> Path:
    """Create directory (and parents) if it doesn't exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def project_root() -> Path:
    """Return the project root directory (parent of nlp_pipeline/)."""
    return Path(__file__).resolve().parent.parent
