"""
common/logging_setup.py
-----------------------
Logging configuration for FlowSentry.

Sets up a console handler and a rotating file handler writing to
``artifacts/logs/flowsentry.log`` (path taken from config or a
sensible default).

Call ``setup_logging()`` once at the start of each CLI entry point,
before any other module is used.

TRD §27, NFR-009.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Any


def setup_logging(
    config: dict[str, Any] | None = None,
    log_dir: str | Path | None = None,
) -> None:
    """Configure console and rotating-file logging for FlowSentry.

    Parameters
    ----------
    config:
        FlowSentry config dict (from ``common.config.load_config``).
        Uses ``config["logging"]["level"]`` and ``config["paths"]["artifacts"]``
        to determine log level and log directory.
    log_dir:
        Direct override for the log directory.  Takes precedence over
        config if supplied.

    Notes
    -----
    - Log messages use structured key=value format for easy grep.
    - Rotating file handler: max 10 MB per file, 5 backup files.
    - Calling this function more than once replaces all existing handlers
      (safe for CLI entry points, avoids duplicate messages).
    - Packet/payload content is never logged (NFR-007).
      Five-tuples are logged only at DEBUG level (TRD §27).
    """
    # ── Determine log level ──────────────────────────────────────────────
    level_name: str = "INFO"
    if config:
        level_name = config.get("logging", {}).get("level", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)

    # ── Determine log directory ──────────────────────────────────────────
    if log_dir is None:
        if config:
            artifacts_dir = config.get("paths", {}).get("artifacts", "artifacts")
        else:
            artifacts_dir = "artifacts"
        log_dir = Path(artifacts_dir) / "logs"
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "flowsentry.log"

    # ── Format ───────────────────────────────────────────────────────────
    fmt = "%(asctime)s level=%(levelname)s logger=%(name)s %(message)s"
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S")

    # ── Root logger ───────────────────────────────────────────────────────
    root = logging.getLogger()
    root.setLevel(level)
    # Remove existing handlers to avoid duplicates on repeated calls.
    root.handlers.clear()

    # ── Console handler ───────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # ── Rotating file handler ─────────────────────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    logging.getLogger(__name__).debug(
        "logging initialised level=%s log_file=%s", level_name, log_file
    )
