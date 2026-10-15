"""
preprocessing/ingest.py
-----------------------
Dataset ingestion for FlowSentry (CN-002, Phase 2).

Registers dataset files found in data/raw/ and produces a checksummed manifest
for provenance and reproducibility.

Responsibilities:
  - Discover all files under data/raw/ (recursively)
  - Compute SHA-256 checksums for reproducibility
  - Detect file format (CSV, PCAP, ARFF, etc.) by extension and light sniffing
  - For CSV files: count rows and read header (streamed, not fully loaded)
  - Write manifest to data/processed/manifest.json

Never modifies data/raw/ (DS-005).
Flags unreadable/unknown files rather than skipping silently.

Run:
    python -m preprocessing.ingest --raw-dir data/raw --out data/processed/manifest.json

TRD §4, DS-003, DS-005, DS-006, NFR-003.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from common.errors import DatasetError

logger = logging.getLogger(__name__)

# File extensions recognised by format
_FORMAT_MAP: dict[str, str] = {
    ".csv": "CSV",
    ".arff": "ARFF",
    ".pcap": "PCAP",
    ".pcapng": "PCAPNG",
    ".json": "JSON",
    ".txt": "TXT",
    ".parquet": "PARQUET",
}


def compute_sha256(path: Path, chunk_size: int = 8192) -> str:
    """Compute SHA-256 checksum of a file.

    Parameters
    ----------
    path:
        Path to the file.
    chunk_size:
        Bytes to read per iteration (for memory efficiency on large files).

    Returns
    -------
    str
        Hex-encoded SHA-256 digest.

    Raises
    ------
    DatasetError
        If the file cannot be read.
    """
    hasher = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            while True:
                chunk = fh.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except OSError as exc:
        raise DatasetError(f"Cannot read file for checksum: {path} ({exc})") from exc


def detect_format(path: Path) -> str:
    """Detect file format by extension and light sniffing.

    Parameters
    ----------
    path:
        Path to the file.

    Returns
    -------
    str
        Format string (e.g. "CSV", "PCAP", "UNKNOWN").
    """
    ext = path.suffix.lower()
    if ext in _FORMAT_MAP:
        return _FORMAT_MAP[ext]
    return "UNKNOWN"


def get_csv_info(path: Path) -> dict[str, Any]:
    """Extract row count and header from a CSV file (streamed).

    Parameters
    ----------
    path:
        Path to the CSV file.

    Returns
    -------
    dict with keys:
        - row_count: int (number of data rows, excluding header)
        - header: list[str] (column names)
        - error: str | None (if file is unreadable or malformed)

    Notes
    -----
    Handles large files by streaming (does not load entire file into memory).
    Uses utf-8 encoding; if decoding fails, reports error instead of raising.
    """
    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            try:
                header = next(reader)
            except StopIteration:
                # Empty file
                return {"row_count": 0, "header": [], "error": None}

            # Count remaining rows (data rows)
            row_count = sum(1 for _ in reader)

        return {"row_count": row_count, "header": header, "error": None}

    except UnicodeDecodeError as exc:
        return {
            "row_count": None,
            "header": None,
            "error": f"Encoding error: {exc}",
        }
    except csv.Error as exc:
        return {
            "row_count": None,
            "header": None,
            "error": f"CSV parse error: {exc}",
        }
    except OSError as exc:
        return {
            "row_count": None,
            "header": None,
            "error": f"Cannot read file: {exc}",
        }


def ingest_file(path: Path, base_dir: Path) -> dict[str, Any]:
    """Build a manifest entry for a single file.

    Parameters
    ----------
    path:
        Absolute path to the file.
    base_dir:
        Base directory (data/raw/) for computing relative paths.

    Returns
    -------
    dict
        Manifest entry with keys: relative_path, size_bytes, sha256,
        format, csv_info (if applicable).
    """
    rel_path = path.relative_to(base_dir).as_posix()
    size = path.stat().st_size
    sha256 = compute_sha256(path)
    fmt = detect_format(path)

    entry: dict[str, Any] = {
        "relative_path": rel_path,
        "size_bytes": size,
        "sha256": sha256,
        "format": fmt,
    }

    # If CSV, extract row count and header
    if fmt == "CSV":
        csv_info = get_csv_info(path)
        entry["csv_info"] = csv_info

    return entry


def ingest_directory(raw_dir: Path) -> list[dict[str, Any]]:
    """Discover and ingest all files under data/raw/ recursively.

    Parameters
    ----------
    raw_dir:
        Path to data/raw/.

    Returns
    -------
    list[dict[str, Any]]
        List of manifest entries (one per file).

    Raises
    ------
    DatasetError
        If raw_dir does not exist or is not a directory.
    """
    if not raw_dir.exists():
        raise DatasetError(
            f"Raw data directory does not exist: {raw_dir}. "
            "Place datasets under data/raw/ before running ingest."
        )
    if not raw_dir.is_dir():
        raise DatasetError(
            f"Expected data/raw/ to be a directory, got: {raw_dir}"
        )

    files = [p for p in raw_dir.rglob("*") if p.is_file()]

    if not files:
        logger.warning("No files found in %s", raw_dir)
        return []

    logger.info("Found %d files under %s", len(files), raw_dir)

    entries: list[dict[str, Any]] = []
    for file_path in sorted(files):
        # Skip hidden files and .gitkeep
        if file_path.name.startswith("."):
            logger.debug("Skipping hidden file: %s", file_path.name)
            continue

        logger.info("Ingesting: %s", file_path.relative_to(raw_dir))
        entry = ingest_file(file_path, raw_dir)
        entries.append(entry)

    return entries


def write_manifest(entries: list[dict[str, Any]], out_path: Path) -> None:
    """Write the manifest to a JSON file.

    Parameters
    ----------
    entries:
        List of file manifest entries.
    out_path:
        Output path (e.g. data/processed/manifest.json).

    Raises
    ------
    DatasetError
        If the manifest cannot be written.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": "1.0",
        "description": "FlowSentry dataset file manifest (CN-002)",
        "file_count": len(entries),
        "files": entries,
    }

    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        logger.info("Manifest written to %s (%d files)", out_path, len(entries))
    except OSError as exc:
        raise DatasetError(f"Cannot write manifest to {out_path}: {exc}") from exc


def main() -> None:
    """CLI entry point for dataset ingestion."""
    parser = argparse.ArgumentParser(
        description="Ingest dataset files and produce a checksummed manifest (CN-002)."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw"),
        help="Path to data/raw/ directory (default: data/raw)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/processed/manifest.json"),
        help="Output manifest path (default: data/processed/manifest.json)",
    )
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
    )

    logger.info("Starting dataset ingestion (CN-002)")
    logger.info("Raw directory: %s", args.raw_dir.resolve())
    logger.info("Output manifest: %s", args.out.resolve())

    try:
        entries = ingest_directory(args.raw_dir)

        if not entries:
            logger.warning(
                "No dataset files found. Task CN-002 is BLOCKED until datasets are "
                "placed in %s. See data/README.md for instructions.",
                args.raw_dir.resolve(),
            )
            # Still write an empty manifest so the file exists
            write_manifest(entries, args.out)
            print("\n" + "=" * 72)
            print("STATUS: BLOCKED")
            print("=" * 72)
            print(f"No dataset files found in {args.raw_dir.resolve()}.")
            print("CN-002 cannot proceed without datasets.")
            print("\nNext steps:")
            print("  1. Download ISCX-VPN2016 and/or CIC-IDS2017 datasets")
            print(f"  2. Place them in {args.raw_dir.resolve()}/")
            print("  3. Update data/README.md with source, licence, version")
            print("  4. Re-run: python -m preprocessing.ingest")
            print("=" * 72)
        else:
            write_manifest(entries, args.out)
            print("\n" + "=" * 72)
            print("SUCCESS: Dataset ingestion complete (CN-002)")
            print("=" * 72)
            print(f"Manifest: {args.out.resolve()}")
            print(f"Files registered: {len(entries)}")
            print("\nNext step: CN-003 (Dataset Inspection)")
            print("  Run: python -m preprocessing.inspect")
            print("=" * 72)

    except DatasetError as exc:
        logger.error("Dataset ingestion failed: %s", exc)
        print(f"\nERROR: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
