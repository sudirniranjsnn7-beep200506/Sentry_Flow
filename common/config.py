"""
common/config.py
----------------
Configuration loader for FlowSentry.

Loads a YAML config file (default: config/default.yaml) and applies
a curated set of FLOWSENTRY_* environment-variable overrides.
Exposes a single ``load_config(path)`` function returning a plain dict.

Any missing required key raises ConfigError immediately so downstream
code never silently operates on bad configuration.

Usage:
    from common.config import load_config
    config = load_config()          # uses config/default.yaml
    config = load_config("path/to/custom.yaml")

TRD §25, FR-012, NFR-003.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from common.errors import ConfigError

logger = logging.getLogger(__name__)

# Required top-level keys that every config must contain.
_REQUIRED_KEYS: tuple[str, ...] = ("seed", "paths", "split", "cv", "preprocessing")

# Environment-variable → nested key-path in config dict.
# Only a curated list is supported; no wild-card injection.
_ENV_OVERRIDES: dict[str, tuple[str, ...]] = {
    "FLOWSENTRY_DATA_DIR": ("paths", "data_raw"),
    "FLOWSENTRY_ARTIFACTS_DIR": ("paths", "artifacts"),
    "CICFLOWMETER_PATH": ("cicflowmeter", "command_template"),
    "CAPTURE_INTERFACE": ("capture", "interface"),
}


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load and return the FlowSentry configuration dictionary.

    Parameters
    ----------
    path:
        Path to a YAML config file.  Defaults to ``config/default.yaml``
        relative to the repository root (the directory two levels above
        this file: ``common/../`` = repo root).

    Returns
    -------
    dict[str, Any]
        Merged configuration with environment-variable overrides applied.

    Raises
    ------
    ConfigError
        If the file cannot be read, is not valid YAML, or is missing
        required top-level keys.
    """
    if path is None:
        # Resolve relative to repository root (parent of common/)
        repo_root = Path(__file__).resolve().parent.parent
        path = repo_root / "config" / "default.yaml"
    else:
        path = Path(path)

    if not path.exists():
        raise ConfigError(
            f"Configuration file not found: {path}. "
            "Ensure config/default.yaml exists at the repository root."
        )

    try:
        with open(path, "r", encoding="utf-8") as fh:
            config: dict[str, Any] = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse YAML config at {path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Cannot read config file {path}: {exc}") from exc

    if not isinstance(config, dict):
        raise ConfigError(
            f"Config file {path} must be a YAML mapping at the top level; "
            f"got {type(config).__name__}."
        )

    config = _apply_env_overrides(config)
    _validate_required_keys(config, path)

    logger.debug("config loaded path=%s", path)
    return config


def _apply_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    """Apply FLOWSENTRY_* environment-variable overrides to config dict.

    Parameters
    ----------
    config:
        Config dict to modify in place.

    Returns
    -------
    dict[str, Any]
        The same dict with overrides applied.
    """
    for env_var, key_path in _ENV_OVERRIDES.items():
        value = os.environ.get(env_var)
        if value:
            _set_nested(config, key_path, value)
            logger.debug("config override env_var=%s key_path=%s", env_var, key_path)
    return config


def _set_nested(d: dict[str, Any], key_path: tuple[str, ...], value: Any) -> None:
    """Set a value at a nested key path, creating intermediate dicts if needed."""
    for key in key_path[:-1]:
        d = d.setdefault(key, {})
    d[key_path[-1]] = value


def _validate_required_keys(config: dict[str, Any], path: Path) -> None:
    """Raise ConfigError if any required top-level key is absent."""
    missing = [k for k in _REQUIRED_KEYS if k not in config]
    if missing:
        raise ConfigError(
            f"Config file {path} is missing required keys: {missing}. "
            "Check config/default.yaml against TRD §25."
        )
