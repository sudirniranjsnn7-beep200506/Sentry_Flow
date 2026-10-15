"""
tests/unit/test_common.py
-------------------------
Unit tests for the common/ infrastructure package (CN-001).

Requirements covered:
  - All 10 typed exception classes exist and inherit correctly (TRD §26)
  - config.load_config() loads valid YAML and applies required-key validation
  - config.load_config() raises ConfigError on missing file, bad YAML, missing keys
  - paths.ProjectPaths resolves all directories and ensure_dirs() creates them

No real dataset, no external tools, no network access required.
All tests use only in-memory or tmp_path fixtures.

TRD §28, NFR-006.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _write_yaml(directory: Path, filename: str, data: dict) -> Path:
    """Write a dict as YAML to a temp file and return its path."""
    path = directory / filename
    path.write_text(yaml.dump(data), encoding="utf-8")
    return path


def _minimal_valid_config() -> dict:
    """Return the smallest config dict that passes load_config() validation."""
    return {
        "seed": 42,
        "paths": {
            "data_raw": "data/raw",
            "data_processed": "data/processed",
            "data_sample": "data/sample",
            "artifacts": "artifacts",
            "tmp": "artifacts/tmp",
        },
        "split": {"test_fraction": 0.2, "stratify": True, "group_column": None},
        "cv": {"folds": 5, "shuffle": True},
        "preprocessing": {
            "drop_duplicates": True,
            "missing_strategy": "median",
            "port_features": "excluded",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# common/errors.py
# ─────────────────────────────────────────────────────────────────────────────


class TestErrorHierarchy:
    """All typed exceptions must exist and inherit from FlowSentryError."""

    def test_all_exception_classes_are_importable(self) -> None:
        from common.errors import (  # noqa: F401
            CaptureError,
            ConfigError,
            DatasetError,
            ExtractionError,
            ExtractorUnavailableError,
            FlowSentryError,
            LeakageGuardError,
            LabelMappingError,
            ModelNotFoundError,
            RegistryIntegrityError,
            SchemaMismatchError,
        )

    def test_all_subclass_flowsentry_error(self) -> None:
        from common.errors import (
            CaptureError,
            ConfigError,
            DatasetError,
            ExtractionError,
            ExtractorUnavailableError,
            FlowSentryError,
            LeakageGuardError,
            LabelMappingError,
            ModelNotFoundError,
            RegistryIntegrityError,
            SchemaMismatchError,
        )

        all_classes = [
            ConfigError,
            DatasetError,
            LabelMappingError,
            SchemaMismatchError,
            ExtractorUnavailableError,
            ExtractionError,
            ModelNotFoundError,
            RegistryIntegrityError,
            CaptureError,
            LeakageGuardError,
        ]
        for cls in all_classes:
            assert issubclass(cls, FlowSentryError), (
                f"{cls.__name__} must inherit from FlowSentryError (TRD §26)"
            )

    def test_all_subclass_exception(self) -> None:
        from common.errors import FlowSentryError
        assert issubclass(FlowSentryError, Exception)

    def test_exceptions_can_be_raised_and_caught_as_base(self) -> None:
        """Each typed error can be caught as FlowSentryError (polymorphism check)."""
        from common.errors import (
            CaptureError,
            ConfigError,
            DatasetError,
            ExtractionError,
            ExtractorUnavailableError,
            FlowSentryError,
            LeakageGuardError,
            LabelMappingError,
            ModelNotFoundError,
            RegistryIntegrityError,
            SchemaMismatchError,
        )

        for cls in [
            ConfigError, DatasetError, LabelMappingError, SchemaMismatchError,
            ExtractorUnavailableError, ExtractionError, ModelNotFoundError,
            RegistryIntegrityError, CaptureError, LeakageGuardError,
        ]:
            with pytest.raises(FlowSentryError):
                raise cls("test")

    def test_exception_message_preserved(self) -> None:
        from common.errors import ConfigError
        msg = "missing required key: seed"
        exc = ConfigError(msg)
        assert str(exc) == msg

    def test_can_also_be_caught_as_exception(self) -> None:
        from common.errors import SchemaMismatchError
        with pytest.raises(Exception):
            raise SchemaMismatchError("schema mismatch")


# ─────────────────────────────────────────────────────────────────────────────
# common/config.py
# ─────────────────────────────────────────────────────────────────────────────


class TestLoadConfig:
    """Tests for common.config.load_config()."""

    def test_loads_valid_config(self, tmp_path: Path) -> None:
        """A well-formed YAML with all required keys loads without error."""
        from common.config import load_config

        cfg_path = _write_yaml(tmp_path, "config.yaml", _minimal_valid_config())
        result = load_config(cfg_path)

        assert result["seed"] == 42
        assert result["split"]["test_fraction"] == 0.2
        assert result["cv"]["folds"] == 5

    def test_default_path_loads_real_config(self) -> None:
        """load_config() with no argument loads config/default.yaml successfully."""
        from common.config import load_config

        # config/default.yaml must exist (created by CN-001)
        result = load_config()
        assert "seed" in result
        assert "paths" in result
        assert "split" in result
        assert "cv" in result
        assert "preprocessing" in result

    def test_missing_file_raises_config_error(self) -> None:
        from common.config import load_config
        from common.errors import ConfigError

        with pytest.raises(ConfigError, match="not found"):
            load_config("/nonexistent/path/does_not_exist.yaml")

    def test_invalid_yaml_raises_config_error(self, tmp_path: Path) -> None:
        from common.config import load_config
        from common.errors import ConfigError

        bad = tmp_path / "bad.yaml"
        bad.write_text("key: [unclosed_bracket\nanother: value", encoding="utf-8")
        with pytest.raises(ConfigError):
            load_config(bad)

    def test_missing_seed_raises_config_error(self, tmp_path: Path) -> None:
        from common.config import load_config
        from common.errors import ConfigError

        cfg = _minimal_valid_config()
        del cfg["seed"]
        cfg_path = _write_yaml(tmp_path, "no_seed.yaml", cfg)
        with pytest.raises(ConfigError, match="seed"):
            load_config(cfg_path)

    def test_missing_paths_raises_config_error(self, tmp_path: Path) -> None:
        from common.config import load_config
        from common.errors import ConfigError

        cfg = _minimal_valid_config()
        del cfg["paths"]
        cfg_path = _write_yaml(tmp_path, "no_paths.yaml", cfg)
        with pytest.raises(ConfigError, match="paths"):
            load_config(cfg_path)

    def test_missing_split_raises_config_error(self, tmp_path: Path) -> None:
        from common.config import load_config
        from common.errors import ConfigError

        cfg = _minimal_valid_config()
        del cfg["split"]
        cfg_path = _write_yaml(tmp_path, "no_split.yaml", cfg)
        with pytest.raises(ConfigError, match="split"):
            load_config(cfg_path)

    def test_empty_yaml_raises_config_error(self, tmp_path: Path) -> None:
        from common.config import load_config
        from common.errors import ConfigError

        empty = tmp_path / "empty.yaml"
        empty.write_text("", encoding="utf-8")
        with pytest.raises(ConfigError):
            load_config(empty)

    def test_non_mapping_yaml_raises_config_error(self, tmp_path: Path) -> None:
        from common.config import load_config
        from common.errors import ConfigError

        list_yaml = tmp_path / "list.yaml"
        list_yaml.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ConfigError):
            load_config(list_yaml)

    def test_returns_dict(self, tmp_path: Path) -> None:
        from common.config import load_config

        cfg_path = _write_yaml(tmp_path, "config.yaml", _minimal_valid_config())
        result = load_config(cfg_path)
        assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────────────────
# common/paths.py
# ─────────────────────────────────────────────────────────────────────────────


class TestProjectPaths:
    """Tests for common.paths.ProjectPaths."""

    def test_all_attributes_are_path_objects(self) -> None:
        from common.paths import ProjectPaths

        pp = ProjectPaths(_minimal_valid_config())
        for attr in [
            "repo_root", "data_raw", "data_processed", "data_sample",
            "artifacts", "runs_dir", "registry_dir", "reports_dir",
            "predictions_dir", "live_dir", "logs_dir", "tmp_dir",
            "config_dir", "docs_dir",
        ]:
            assert isinstance(getattr(pp, attr), Path), (
                f"ProjectPaths.{attr} must be a pathlib.Path"
            )

    def test_runs_dir_is_under_artifacts(self) -> None:
        from common.paths import ProjectPaths

        pp = ProjectPaths(_minimal_valid_config())
        assert pp.runs_dir.parent == pp.artifacts

    def test_registry_dir_is_under_artifacts(self) -> None:
        from common.paths import ProjectPaths

        pp = ProjectPaths(_minimal_valid_config())
        assert pp.registry_dir.parent == pp.artifacts

    def test_logs_dir_is_under_artifacts(self) -> None:
        from common.paths import ProjectPaths

        pp = ProjectPaths(_minimal_valid_config())
        assert pp.logs_dir.parent == pp.artifacts

    def test_ensure_dirs_creates_all_output_dirs(self, tmp_path: Path) -> None:
        from common.paths import ProjectPaths

        cfg = _minimal_valid_config()
        cfg["paths"]["artifacts"] = str(tmp_path / "artifacts")
        cfg["paths"]["data_processed"] = str(tmp_path / "data" / "processed")
        cfg["paths"]["data_sample"] = str(tmp_path / "data" / "sample")
        cfg["paths"]["tmp"] = str(tmp_path / "artifacts" / "tmp")

        pp = ProjectPaths(cfg)
        pp.ensure_dirs()

        for d in [
            pp.data_processed, pp.data_sample,
            pp.artifacts, pp.runs_dir, pp.registry_dir,
            pp.reports_dir, pp.predictions_dir, pp.live_dir,
            pp.logs_dir, pp.tmp_dir,
        ]:
            assert d.exists(), f"ensure_dirs() should have created: {d}"

    def test_repo_root_contains_config_dir(self) -> None:
        from common.paths import ProjectPaths

        pp = ProjectPaths(_minimal_valid_config())
        assert pp.config_dir == pp.repo_root / "config"

    def test_absolute_path_in_config_is_used_as_is(self, tmp_path: Path) -> None:
        from common.paths import ProjectPaths

        cfg = _minimal_valid_config()
        cfg["paths"]["artifacts"] = str(tmp_path / "custom_artifacts")
        pp = ProjectPaths(cfg)
        assert pp.artifacts == (tmp_path / "custom_artifacts").resolve()


# ─────────────────────────────────────────────────────────────────────────────
# common/logging_setup.py
# ─────────────────────────────────────────────────────────────────────────────


class TestLoggingSetup:
    """Tests for common.logging_setup.setup_logging()."""

    def test_setup_logging_creates_log_file(self, tmp_path: Path) -> None:
        import logging
        from common.logging_setup import setup_logging

        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)
        log_file = log_dir / "flowsentry.log"
        assert log_file.exists(), "setup_logging() must create the log file"

    def test_setup_logging_does_not_raise(self, tmp_path: Path) -> None:
        from common.logging_setup import setup_logging

        # Should not raise even with a minimal config
        setup_logging(log_dir=tmp_path / "logs")

    def test_logging_writes_messages(self, tmp_path: Path) -> None:
        import logging
        from common.logging_setup import setup_logging

        log_dir = tmp_path / "testlogs"
        setup_logging(log_dir=log_dir)
        logger = logging.getLogger("test.cn001")
        logger.info("test_message key=value")

        log_file = log_dir / "flowsentry.log"
        content = log_file.read_text(encoding="utf-8")
        assert "test_message" in content

    def test_setup_logging_with_config_level(self, tmp_path: Path) -> None:
        import logging
        from common.logging_setup import setup_logging

        cfg = {"logging": {"level": "DEBUG"}, "paths": {"artifacts": str(tmp_path)}}
        setup_logging(config=cfg, log_dir=tmp_path / "logs")
        root = logging.getLogger()
        assert root.level == logging.DEBUG
