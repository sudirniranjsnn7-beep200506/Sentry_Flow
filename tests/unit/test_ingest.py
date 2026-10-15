"""
tests/unit/test_ingest.py
--------------------------
Unit tests for preprocessing/ingest.py (CN-002).

Tests cover:
  - SHA-256 checksum computation correctness
  - CSV info extraction (row count, header)
  - Format detection
  - Unknown/unreadable file handling
  - Empty directory handling
  - Manifest structure

All tests use synthetic fixtures (tmp_path).
No real datasets required.

TRD §28, NFR-006.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from common.errors import DatasetError
from preprocessing.ingest import (
    compute_sha256,
    detect_format,
    get_csv_info,
    ingest_directory,
    ingest_file,
    write_manifest,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _create_csv(path: Path, rows: list[list[str]]) -> None:
    """Write a CSV file with the given rows (first row = header)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)


def _independent_sha256(path: Path) -> str:
    """Independently compute SHA-256 for verification."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestComputeSHA256:
    """Tests for compute_sha256()."""

    def test_checksum_matches_independent_computation(self, tmp_path: Path) -> None:
        """Checksum computed by the function matches hashlib directly."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"FlowSentry test data\n")

        result = compute_sha256(test_file)
        expected = _independent_sha256(test_file)
        assert result == expected

    def test_empty_file_has_known_checksum(self, tmp_path: Path) -> None:
        """Empty file has a known SHA-256 value."""
        empty = tmp_path / "empty.txt"
        empty.write_bytes(b"")

        result = compute_sha256(empty)
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert result == expected

    def test_large_file_checksum(self, tmp_path: Path) -> None:
        """Large file (multiple chunks) computes correctly."""
        large = tmp_path / "large.bin"
        # Write 100 KB of repeating pattern
        large.write_bytes(b"x" * 100_000)

        result = compute_sha256(large)
        expected = _independent_sha256(large)
        assert result == expected

    def test_nonexistent_file_raises_dataset_error(self, tmp_path: Path) -> None:
        """Attempting to checksum a nonexistent file raises DatasetError."""
        nonexistent = tmp_path / "does_not_exist.txt"
        with pytest.raises(DatasetError, match="Cannot read file"):
            compute_sha256(nonexistent)


class TestDetectFormat:
    """Tests for detect_format()."""

    def test_csv_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "data.csv"
        path.touch()
        assert detect_format(path) == "CSV"

    def test_pcap_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "capture.pcap"
        path.touch()
        assert detect_format(path) == "PCAP"

    def test_pcapng_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "capture.pcapng"
        path.touch()
        assert detect_format(path) == "PCAPNG"

    def test_arff_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "data.arff"
        path.touch()
        assert detect_format(path) == "ARFF"

    def test_unknown_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "data.xyz"
        path.touch()
        assert detect_format(path) == "UNKNOWN"

    def test_no_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "README"
        path.touch()
        assert detect_format(path) == "UNKNOWN"

    def test_case_insensitive(self, tmp_path: Path) -> None:
        """Extension matching is case-insensitive."""
        path = tmp_path / "DATA.CSV"
        path.touch()
        assert detect_format(path) == "CSV"


class TestGetCSVInfo:
    """Tests for get_csv_info()."""

    def test_csv_with_header_and_rows(self, tmp_path: Path) -> None:
        """CSV with header and data rows returns correct counts."""
        csv_path = tmp_path / "test.csv"
        _create_csv(csv_path, [
            ["col1", "col2", "col3"],
            ["a", "b", "c"],
            ["d", "e", "f"],
        ])

        info = get_csv_info(csv_path)
        assert info["error"] is None
        assert info["row_count"] == 2
        assert info["header"] == ["col1", "col2", "col3"]

    def test_empty_csv(self, tmp_path: Path) -> None:
        """Empty CSV (no rows) returns zero count and empty header."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("", encoding="utf-8")

        info = get_csv_info(empty_csv)
        assert info["error"] is None
        assert info["row_count"] == 0
        assert info["header"] == []

    def test_csv_with_header_only(self, tmp_path: Path) -> None:
        """CSV with only a header row has row_count = 0."""
        csv_path = tmp_path / "header_only.csv"
        _create_csv(csv_path, [["col1", "col2"]])

        info = get_csv_info(csv_path)
        assert info["error"] is None
        assert info["row_count"] == 0
        assert info["header"] == ["col1", "col2"]

    def test_csv_with_many_rows(self, tmp_path: Path) -> None:
        """CSV with many rows counts correctly without loading into memory."""
        csv_path = tmp_path / "large.csv"
        rows = [["idx", "value"]] + [[str(i), f"val_{i}"] for i in range(1000)]
        _create_csv(csv_path, rows)

        info = get_csv_info(csv_path)
        assert info["error"] is None
        assert info["row_count"] == 1000

    def test_nonexistent_csv_reports_error(self, tmp_path: Path) -> None:
        """Nonexistent file returns error field populated."""
        nonexistent = tmp_path / "missing.csv"
        info = get_csv_info(nonexistent)
        assert info["error"] is not None
        assert "Cannot read file" in info["error"]


class TestIngestFile:
    """Tests for ingest_file()."""

    def test_csv_file_entry_structure(self, tmp_path: Path) -> None:
        """CSV file entry has all required fields."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        csv_path = raw_dir / "dataset.csv"
        _create_csv(csv_path, [["col1"], ["row1"], ["row2"]])

        entry = ingest_file(csv_path, raw_dir)

        assert "relative_path" in entry
        assert entry["relative_path"] == "dataset.csv"
        assert "size_bytes" in entry
        assert entry["size_bytes"] > 0
        assert "sha256" in entry
        assert len(entry["sha256"]) == 64  # SHA-256 hex digest length
        assert entry["format"] == "CSV"
        assert "csv_info" in entry
        assert entry["csv_info"]["row_count"] == 2

    def test_pcap_file_entry(self, tmp_path: Path) -> None:
        """PCAP file entry does not have csv_info."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        pcap_path = raw_dir / "capture.pcap"
        pcap_path.write_bytes(b"fake pcap data")

        entry = ingest_file(pcap_path, raw_dir)

        assert entry["format"] == "PCAP"
        assert "csv_info" not in entry

    def test_relative_path_in_subdirectory(self, tmp_path: Path) -> None:
        """File in a subdirectory has correct relative_path."""
        raw_dir = tmp_path / "raw"
        subdir = raw_dir / "subdir" / "nested"
        subdir.mkdir(parents=True)
        file_path = subdir / "data.csv"
        _create_csv(file_path, [["col1"]])

        entry = ingest_file(file_path, raw_dir)
        assert entry["relative_path"] == "subdir/nested/data.csv"


class TestIngestDirectory:
    """Tests for ingest_directory()."""

    def test_nonexistent_directory_raises_dataset_error(self, tmp_path: Path) -> None:
        """Nonexistent data/raw/ directory raises DatasetError."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(DatasetError, match="does not exist"):
            ingest_directory(nonexistent)

    def test_empty_directory_returns_empty_list(self, tmp_path: Path) -> None:
        """Empty data/raw/ directory returns empty list (no error)."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        entries = ingest_directory(empty_dir)
        assert entries == []

    def test_directory_with_multiple_files(self, tmp_path: Path) -> None:
        """Directory with multiple files returns all entries."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        _create_csv(raw_dir / "file1.csv", [["col1"]])
        _create_csv(raw_dir / "file2.csv", [["col2"]])
        (raw_dir / "capture.pcap").write_bytes(b"pcap")

        entries = ingest_directory(raw_dir)
        assert len(entries) == 3

        rel_paths = {e["relative_path"] for e in entries}
        assert rel_paths == {"file1.csv", "file2.csv", "capture.pcap"}

    def test_hidden_files_are_skipped(self, tmp_path: Path) -> None:
        """Hidden files (starting with .) are skipped."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        _create_csv(raw_dir / "visible.csv", [["col1"]])
        (raw_dir / ".gitkeep").write_text("")
        (raw_dir / ".hidden").write_text("")

        entries = ingest_directory(raw_dir)
        assert len(entries) == 1
        assert entries[0]["relative_path"] == "visible.csv"

    def test_recursive_discovery(self, tmp_path: Path) -> None:
        """Files in subdirectories are discovered recursively."""
        raw_dir = tmp_path / "raw"
        (raw_dir / "subdir").mkdir(parents=True)
        _create_csv(raw_dir / "top.csv", [["col1"]])
        _create_csv(raw_dir / "subdir" / "nested.csv", [["col2"]])

        entries = ingest_directory(raw_dir)
        assert len(entries) == 2

        rel_paths = {e["relative_path"] for e in entries}
        assert rel_paths == {"top.csv", "subdir/nested.csv"}


class TestWriteManifest:
    """Tests for write_manifest()."""

    def test_manifest_structure(self, tmp_path: Path) -> None:
        """Written manifest has correct structure."""
        entries = [
            {"relative_path": "file1.csv", "size_bytes": 100, "sha256": "abc123", "format": "CSV"},
            {"relative_path": "file2.pcap", "size_bytes": 200, "sha256": "def456", "format": "PCAP"},
        ]
        out_path = tmp_path / "manifest.json"

        write_manifest(entries, out_path)

        assert out_path.exists()
        import json
        with open(out_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)

        assert manifest["version"] == "1.0"
        assert manifest["file_count"] == 2
        assert manifest["files"] == entries

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        """write_manifest creates parent directories if they don't exist."""
        out_path = tmp_path / "nested" / "dir" / "manifest.json"
        write_manifest([], out_path)

        assert out_path.exists()
        assert out_path.parent.exists()

    def test_empty_entries_list(self, tmp_path: Path) -> None:
        """Empty entries list writes a valid manifest with file_count=0."""
        out_path = tmp_path / "manifest.json"
        write_manifest([], out_path)

        import json
        with open(out_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)

        assert manifest["file_count"] == 0
        assert manifest["files"] == []
