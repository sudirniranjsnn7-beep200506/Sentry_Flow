"""
common/paths.py
---------------
Centralised path resolution for FlowSentry.

All code obtains paths from ``ProjectPaths`` rather than constructing
them ad-hoc, so the config's ``paths`` block is the single source of
truth and no paths are hard-coded.

Usage:
    from common.config import load_config
    from common.paths import ProjectPaths

    config = load_config()
    paths = ProjectPaths(config)
    paths.ensure_dirs()        # create output dirs that don't yet exist

TRD §25, FR-012, NFR-003.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ProjectPaths:
    """Resolved ``Path`` objects for every key project directory.

    Instantiate once from the loaded config dict; pass the instance
    around rather than re-loading config.

    Parameters
    ----------
    config:
        Config dict from ``common.config.load_config``.

    Attributes
    ----------
    repo_root : Path
        Absolute path to the repository root (parent of ``common/``).
    data_raw : Path
        ``data/raw/`` — immutable; datasets live here; never modified by code.
    data_processed : Path
        ``data/processed/`` — generated splits, manifests (git-ignored).
    data_sample : Path
        ``data/sample/`` — tiny, licence-permitting samples.
    artifacts : Path
        ``artifacts/`` — git-ignored generated outputs.
    runs_dir : Path
        ``artifacts/runs/`` — one sub-directory per training run.
    registry_dir : Path
        ``artifacts/registry/`` — model registry.
    reports_dir : Path
        ``artifacts/reports/`` — evaluation and comparison reports.
    predictions_dir : Path
        ``artifacts/predictions/`` — PCAP and live inference outputs.
    live_dir : Path
        ``artifacts/live/`` — near-live classification outputs.
    logs_dir : Path
        ``artifacts/logs/`` — rotating log files.
    tmp_dir : Path
        Temporary directory for intermediate files (e.g. extractor output).
    config_dir : Path
        ``config/`` — YAML configuration files.
    docs_dir : Path
        ``docs/`` — verification records, task reports, decisions.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.repo_root: Path = Path(__file__).resolve().parent.parent

        paths_cfg: dict[str, str] = config.get("paths", {})

        self.data_raw: Path = self._resolve(paths_cfg.get("data_raw", "data/raw"))
        self.data_processed: Path = self._resolve(
            paths_cfg.get("data_processed", "data/processed")
        )
        self.data_sample: Path = self._resolve(
            paths_cfg.get("data_sample", "data/sample")
        )
        self.artifacts: Path = self._resolve(paths_cfg.get("artifacts", "artifacts"))
        self.tmp_dir: Path = self._resolve(paths_cfg.get("tmp", "artifacts/tmp"))

        # Sub-directories within artifacts/
        self.runs_dir: Path = self.artifacts / "runs"
        self.registry_dir: Path = self.artifacts / "registry"
        self.reports_dir: Path = self.artifacts / "reports"
        self.predictions_dir: Path = self.artifacts / "predictions"
        self.live_dir: Path = self.artifacts / "live"
        self.logs_dir: Path = self.artifacts / "logs"

        # Config and docs (source-controlled; not created by ensure_dirs)
        self.config_dir: Path = self.repo_root / "config"
        self.docs_dir: Path = self.repo_root / "docs"

    def _resolve(self, relative_or_absolute: str) -> Path:
        """Return an absolute Path, resolving relative paths from repo root."""
        p = Path(relative_or_absolute)
        if p.is_absolute():
            return p
        return (self.repo_root / p).resolve()

    def ensure_dirs(self) -> None:
        """Create all output directories that do not yet exist.

        Only writable output directories are created here.
        ``data/raw/`` and ``config/`` are never created by code —
        they are placed by humans.
        """
        output_dirs = [
            self.data_processed,
            self.data_sample,
            self.artifacts,
            self.runs_dir,
            self.registry_dir,
            self.reports_dir,
            self.predictions_dir,
            self.live_dir,
            self.logs_dir,
            self.tmp_dir,
        ]
        for d in output_dirs:
            d.mkdir(parents=True, exist_ok=True)
