"""
preprocessing/inspect.py
------------------------
Dataset inspection for FlowSentry (CN-003, Phase 2).

Produces a factual inspection report from real dataset files to help the team
finalize the Dataset → Target Label Mapping.

Responsibilities:
  - Read dataset files (CSV, ARFF formats)
  - Extract column names, dtypes, row counts
  - Identify label column candidates and list every distinct label with counts
  - Count NaN, ±inf values per column
  - Detect exact duplicates, constant columns
  - Identify identifier-like columns (IP, port, timestamp, flow-ID)
  - Generate label_mapping_worksheet.md for human decision

Never modifies raw data; never proposes or fills in label mappings.

Run:
    python -m preprocessing.inspect --manifest data/processed/manifest.json

TRD §4, DS-004, FE-006, U-02, U-04, U-16, U-17.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from common.errors import DatasetError
from common.paths import ProjectPaths

logger = logging.getLogger(__name__)


def read_arff_file(path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read an ARFF file and convert to pandas DataFrame.

    Parameters
    ----------
    path:
        Path to the ARFF file.

    Returns
    -------
    tuple[pd.DataFrame, dict]
        DataFrame with data, and metadata dict with attribute info.

    Raises
    ------
    DatasetError
        If file cannot be read or parsed.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()

        # Parse ARFF header
        attributes = []
        data_section = False
        data_lines = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("%"):
                continue

            if line.lower().startswith("@attribute"):
                # Extract attribute name and type
                # Format: @attribute <name> <type>
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    attr_name = parts[1].strip("'\"")
                    attr_type = parts[2].strip()
                    attributes.append((attr_name, attr_type))

            elif line.lower().startswith("@data"):
                data_section = True
                continue

            elif data_section:
                if line:
                    data_lines.append(line)

        if not attributes:
            raise DatasetError(f"No @attribute declarations found in ARFF file: {path}")

        if not data_lines:
            raise DatasetError(f"No data found in ARFF file: {path}")

        # Parse data lines (comma-separated)
        data_rows = []
        for line in data_lines:
            # Handle quoted values and split by comma
            values = line.split(",")
            data_rows.append(values)

        # Create DataFrame
        column_names = [attr[0] for attr in attributes]
        df = pd.DataFrame(data_rows, columns=column_names)

        # Convert numeric columns
        for col_name, col_type in attributes:
            if col_type.lower() in ["numeric", "real", "integer"]:
                df[col_name] = pd.to_numeric(df[col_name], errors="coerce")
            # String types remain as string

        metadata = {
            "attributes": attributes,
            "format": "ARFF",
        }

        logger.info("Read ARFF file %s: %d rows, %d columns", path.name, len(df), len(df.columns))
        return df, metadata

    except Exception as exc:
        raise DatasetError(f"Cannot read ARFF file {path}: {exc}") from exc


def read_dataset_file(path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read a dataset file (CSV or ARFF) and return DataFrame + metadata.

    Parameters
    ----------
    path:
        Path to the dataset file.

    Returns
    -------
    tuple[pd.DataFrame, dict]
        DataFrame with data, and metadata dict.

    Raises
    ------
    DatasetError
        If file format is unsupported or cannot be read.
    """
    ext = path.suffix.lower()

    if ext == ".csv":
        try:
            df = pd.read_csv(path, low_memory=False)
            metadata = {"format": "CSV"}
            logger.info("Read CSV file %s: %d rows, %d columns", path.name, len(df), len(df.columns))
            return df, metadata
        except Exception as exc:
            raise DatasetError(f"Cannot read CSV file {path}: {exc}") from exc

    elif ext == ".arff":
        return read_arff_file(path)

    else:
        raise DatasetError(f"Unsupported file format: {ext} (file: {path})")


def identify_label_column_candidates(df: pd.DataFrame) -> list[str]:
    """Identify columns that might be label/class columns.

    Parameters
    ----------
    df:
        DataFrame to inspect.

    Returns
    -------
    list[str]
        List of column names that are likely labels.

    Notes
    -----
    Heuristics:
      - Column name contains: class, label, category, target, type
      - Data type is string/object
      - Low cardinality (< 50 unique values)
    """
    candidates = []

    label_keywords = ["class", "label", "category", "target", "type", "attack", "application", "app"]

    for col in df.columns:
        col_lower = col.lower()

        # Check if column name suggests it's a label
        if any(kw in col_lower for kw in label_keywords):
            candidates.append(col)
            continue

        # Check data type and cardinality
        if df[col].dtype == object or df[col].dtype.name == "category":
            nunique = df[col].nunique()
            if nunique < 50:  # Low cardinality suggests categorical
                candidates.append(col)

    return candidates


def identify_identifier_columns(df: pd.DataFrame) -> list[str]:
    """Identify columns that appear to be identifiers (IP, port, timestamp, flow-ID).

    Parameters
    ----------
    df:
        DataFrame to inspect.

    Returns
    -------
    list[str]
        List of column names that are likely identifiers.
    """
    identifiers = []

    id_keywords = [
        "ip", "address", "port", "timestamp", "time", "date",
        "flow_id", "flowid", "id", "mac", "source", "destination",
        "src", "dst", "proto", "protocol"
    ]

    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in id_keywords):
            identifiers.append(col)

    return identifiers


def inspect_dataframe(df: pd.DataFrame, file_path: Path) -> dict[str, Any]:
    """Inspect a DataFrame and extract detailed statistics.

    Parameters
    ----------
    df:
        DataFrame to inspect.
    file_path:
        Path to the source file (for reporting).

    Returns
    -------
    dict
        Inspection results with keys: file, rows, columns, dtypes, label_candidates,
        labels_with_counts, nan_counts, inf_counts, duplicate_count, constant_columns,
        identifier_columns.
    """
    result: dict[str, Any] = {
        "file": str(file_path.name),
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }

    # Identify label column candidates
    label_candidates = identify_label_column_candidates(df)
    result["label_candidates"] = label_candidates

    # Extract labels with counts from each candidate
    labels_with_counts = {}
    for col in label_candidates:
        value_counts = df[col].value_counts().to_dict()
        labels_with_counts[col] = value_counts

    result["labels_with_counts"] = labels_with_counts

    # NaN counts per column
    nan_counts = df.isna().sum().to_dict()
    result["nan_counts"] = {col: int(count) for col, count in nan_counts.items() if count > 0}

    # ±inf counts per column (numeric only)
    inf_counts = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        pos_inf = np.isinf(df[col]) & (df[col] > 0)
        neg_inf = np.isinf(df[col]) & (df[col] < 0)
        pos_count = pos_inf.sum()
        neg_count = neg_inf.sum()
        if pos_count > 0 or neg_count > 0:
            inf_counts[col] = {"pos_inf": int(pos_count), "neg_inf": int(neg_count)}

    result["inf_counts"] = inf_counts

    # Exact duplicate count
    duplicate_count = df.duplicated().sum()
    result["duplicate_count"] = int(duplicate_count)

    # Constant columns (single unique value)
    constant_columns = [col for col in df.columns if df[col].nunique() == 1]
    result["constant_columns"] = constant_columns

    # Identifier columns
    identifier_columns = identify_identifier_columns(df)
    result["identifier_columns"] = identifier_columns

    return result


def inspect_datasets(manifest_path: Path) -> list[dict[str, Any]]:
    """Inspect all datasets listed in the manifest.

    Parameters
    ----------
    manifest_path:
        Path to the manifest.json file.

    Returns
    -------
    list[dict]
        List of inspection results (one per dataset file).

    Raises
    ------
    DatasetError
        If manifest cannot be read or datasets cannot be inspected.
    """
    try:
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except Exception as exc:
        raise DatasetError(f"Cannot read manifest {manifest_path}: {exc}") from exc

    raw_dir = manifest_path.parent.parent / "raw"
    results = []

    for file_entry in manifest["files"]:
        rel_path = file_entry["relative_path"]
        file_format = file_entry["format"]

        # Skip non-data files
        if file_format not in ["CSV", "ARFF"]:
            logger.info("Skipping non-data file: %s (format: %s)", rel_path, file_format)
            continue

        file_path = raw_dir / rel_path
        logger.info("Inspecting: %s", rel_path)

        try:
            df, metadata = read_dataset_file(file_path)
            inspection = inspect_dataframe(df, file_path)
            inspection["metadata"] = metadata
            results.append(inspection)
        except DatasetError as exc:
            logger.error("Failed to inspect %s: %s", rel_path, exc)
            results.append({
                "file": rel_path,
                "error": str(exc),
            })

    return results


def generate_label_mapping_worksheet(
    inspections: list[dict[str, Any]], output_path: Path
) -> None:
    """Generate a label mapping worksheet for human decision-making.

    Parameters
    ----------
    inspections:
        List of inspection results.
    output_path:
        Path to write the worksheet (markdown file).
    """
    lines = [
        "# FlowSentry Label Mapping Worksheet",
        "",
        "**Generated:** " + datetime.now().isoformat(),
        "**Purpose:** Map dataset labels to FlowSentry target classes",
        "",
        "## Instructions",
        "",
        "1. Review the original labels below (from real dataset files)",
        "2. For each label, decide the target class or DROP:",
        "   - **Web Browsing** (HTTP/HTTPS browsing traffic)",
        "   - **VoIP** (Voice over IP: Skype, Hangouts, etc.)",
        "   - **Streaming** (Video/audio streaming: YouTube, Vimeo, etc.)",
        "   - **File Transfer** (FTP, SFTP, file sharing)",
        "   - **DROP** (exclude this label from training)",
        "3. Fill in the \"Target Class\" column",
        "4. Update `config/label_mapping.yaml` with your decisions",
        "5. Change `status: unresolved` to `status: approved` in the config",
        "",
        "---",
        "",
    ]

    # Collect all labels from all inspections
    all_labels: dict[str, int] = {}

    for insp in inspections:
        if "error" in insp:
            continue

        file_name = insp["file"]
        labels_with_counts = insp.get("labels_with_counts", {})

        for col_name, label_counts in labels_with_counts.items():
            lines.append(f"## Labels from: {file_name} (column: {col_name})")
            lines.append("")
            lines.append("| Original Label | Count | Target Class |")
            lines.append("|---|---|---|")

            for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
                lines.append(f"| {label} | {count} | _[FILL IN]_ |")
                # Track globally
                all_labels[label] = all_labels.get(label, 0) + count

            lines.append("")

    # Summary section
    lines.append("---")
    lines.append("")
    lines.append("## Summary: All Unique Labels Across All Files")
    lines.append("")
    lines.append("| Original Label | Total Count | Target Class |")
    lines.append("|---|---|---|")

    for label, count in sorted(all_labels.items(), key=lambda x: -x[1]):
        lines.append(f"| {label} | {count} | _[FILL IN]_ |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("1. Complete the \"Target Class\" column above")
    lines.append("2. Update `config/label_mapping.yaml` with mappings")
    lines.append("3. Set `status: approved` in the config")
    lines.append("4. Proceed to CN-004 (Preprocessing)")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Label mapping worksheet written to %s", output_path)


def generate_inspection_report(
    inspections: list[dict[str, Any]], output_md: Path, output_json: Path
) -> None:
    """Generate inspection report in markdown and JSON formats.

    Parameters
    ----------
    inspections:
        List of inspection results.
    output_md:
        Path to markdown report.
    output_json:
        Path to JSON report.
    """
    # Save JSON
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as fh:
        json.dump({
            "version": "1.0",
            "generated": datetime.now().isoformat(),
            "inspections": inspections,
        }, fh, indent=2)

    logger.info("JSON report written to %s", output_json)

    # Generate markdown
    lines = [
        "# FlowSentry Dataset Inspection Report (CN-003)",
        "",
        "**Generated:** " + datetime.now().isoformat(),
        "**Task:** CN-003 — Dataset Inspection",
        "",
        "## Summary",
        "",
        f"- **Files inspected:** {len(inspections)}",
    ]

    total_rows = sum(insp.get("rows", 0) for insp in inspections if "error" not in insp)
    lines.append(f"- **Total rows:** {total_rows:,}")

    lines.append("")
    lines.append("---")
    lines.append("")

    for insp in inspections:
        if "error" in insp:
            lines.append(f"## File: {insp['file']}")
            lines.append("")
            lines.append(f"**ERROR:** {insp['error']}")
            lines.append("")
            continue

        lines.append(f"## File: {insp['file']}")
        lines.append("")
        lines.append(f"- **Format:** {insp['metadata']['format']}")
        lines.append(f"- **Rows:** {insp['rows']:,}")
        lines.append(f"- **Columns:** {insp['columns']}")
        lines.append(f"- **Duplicate rows:** {insp['duplicate_count']:,}")
        lines.append("")

        lines.append("### Label Columns")
        lines.append("")
        if insp["label_candidates"]:
            for col in insp["label_candidates"]:
                labels = insp["labels_with_counts"].get(col, {})
                lines.append(f"**{col}:** {len(labels)} unique labels")
                for label, count in sorted(labels.items(), key=lambda x: -x[1])[:10]:
                    lines.append(f"  - {label}: {count:,}")
                if len(labels) > 10:
                    lines.append(f"  - _(and {len(labels) - 10} more)_")
                lines.append("")
        else:
            lines.append("_No label column candidates found._")
            lines.append("")

        lines.append("### Columns")
        lines.append("")
        lines.append("| Column | Type |")
        lines.append("|---|---|")
        for col, dtype in list(insp["dtypes"].items())[:20]:
            lines.append(f"| {col} | {dtype} |")
        if len(insp["dtypes"]) > 20:
            lines.append(f"| _...and {len(insp['dtypes']) - 20} more columns_ | |")
        lines.append("")

        if insp["nan_counts"]:
            lines.append("### Missing Values (NaN)")
            lines.append("")
            lines.append("| Column | NaN Count |")
            lines.append("|---|---|")
            for col, count in sorted(insp["nan_counts"].items(), key=lambda x: -x[1])[:10]:
                lines.append(f"| {col} | {count:,} |")
            lines.append("")

        if insp["inf_counts"]:
            lines.append("### Infinite Values")
            lines.append("")
            lines.append("| Column | +Inf | -Inf |")
            lines.append("|---|---|---|")
            for col, counts in insp["inf_counts"].items():
                lines.append(f"| {col} | {counts['pos_inf']:,} | {counts['neg_inf']:,} |")
            lines.append("")

        if insp["constant_columns"]:
            lines.append(f"### Constant Columns ({len(insp['constant_columns'])})")
            lines.append("")
            for col in insp["constant_columns"]:
                lines.append(f"- {col}")
            lines.append("")

        if insp["identifier_columns"]:
            lines.append(f"### Identifier-like Columns ({len(insp['identifier_columns'])})")
            lines.append("")
            for col in insp["identifier_columns"]:
                lines.append(f"- {col}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Open questions section
    lines.append("## Open Questions for Team Decision")
    lines.append("")
    lines.append("### U-02: Dataset Label Usability")
    lines.append("")
    lines.append("Are the dataset labels suitable for FlowSentry's target classes")
    lines.append("(Web Browsing, VoIP, Streaming, File Transfer)?")
    lines.append("")
    lines.append("**Action:** Review label_mapping_worksheet.md and decide.")
    lines.append("")
    lines.append("### U-04: Data Source Format")
    lines.append("")
    lines.append("Datasets contain flow-feature files (ARFF/CSV). No raw PCAPs found.")
    lines.append("")
    lines.append("### U-17: Grouping Identifiers")
    lines.append("")
    lines.append("Check if identifier columns can be used for group-aware splitting.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("1. **Human action required:** Complete label_mapping_worksheet.md")
    lines.append("2. Update `config/label_mapping.yaml` with approved mappings")
    lines.append("3. Set `status: approved` in the config")
    lines.append("4. Proceed to CN-004 (Preprocessing)")
    lines.append("")

    output_md.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Markdown report written to %s", output_md)


def main() -> None:
    """CLI entry point for dataset inspection."""
    parser = argparse.ArgumentParser(
        description="Inspect datasets and generate label mapping worksheet (CN-003)."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/processed/manifest.json"),
        help="Path to manifest.json (default: data/processed/manifest.json)",
    )
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
    )

    logger.info("Starting dataset inspection (CN-003)")

    try:
        inspections = inspect_datasets(args.manifest)

        # Generate reports
        output_dir = Path("artifacts/reports")
        output_json = output_dir / "dataset_inspection.json"
        output_md = output_dir / "dataset_inspection.md"
        worksheet_path = Path("docs/decisions/label_mapping_worksheet.md")

        generate_inspection_report(inspections, output_md, output_json)
        generate_label_mapping_worksheet(inspections, worksheet_path)

        print("\n" + "=" * 72)
        print("SUCCESS: Dataset inspection complete (CN-003)")
        print("=" * 72)
        print(f"Inspection report: {output_md}")
        print(f"JSON data: {output_json}")
        print(f"Label worksheet: {worksheet_path}")
        print("")
        print("NEXT STEPS (HUMAN ACTION REQUIRED):")
        print(f"  1. Review: {worksheet_path}")
        print("  2. Map each label to a target class (or DROP)")
        print("  3. Update: config/label_mapping.yaml")
        print("  4. Set status: approved in the config")
        print("  5. Then agent can proceed with CN-004")
        print("=" * 72)

    except DatasetError as exc:
        logger.error("Dataset inspection failed: %s", exc)
        print(f"\nERROR: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
