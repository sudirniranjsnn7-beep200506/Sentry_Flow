"""
preprocessing/split.py
----------------------
Train/test splitting module for FlowSentry (CN-004, Phase 2).

Creates frozen, stratified train/test splits with reproducibility guarantees.

Responsibilities:
  - Stratified split by target class (maintain class distribution)
  - Seed from config for reproducibility
  - Write train/test datasets to disk
  - Generate split manifest with row IDs and checksums
  - Assert disjointness (no overlap between train/test)
  - Verify two runs with same seed produce identical splits

Never resamples test set; never fits on test; never leaks information.

TRD §8, ML-002, ML-003, ML-007, DS-007, U-09.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from common.errors import DatasetError

logger = logging.getLogger(__name__)


def compute_dataframe_hash(df: pd.DataFrame) -> str:
    """Compute SHA-256 hash of DataFrame contents for reproducibility verification.
    
    Parameters
    ----------
    df:
        DataFrame to hash
        
    Returns
    -------
    str
        Hex-encoded SHA-256 digest
    """
    # Hash the values as bytes
    content = pd.util.hash_pandas_object(df, index=True).values
    hasher = hashlib.sha256()
    hasher.update(content.tobytes())
    return hasher.hexdigest()


def create_train_test_split(
    df: pd.DataFrame,
    test_fraction: float = 0.2,
    stratify_column: str = "target_class",
    random_seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create stratified train/test split.
    
    Parameters
    ----------
    df:
        Input DataFrame (already cleaned, with target_class column)
    test_fraction:
        Fraction of data for test set (default: 0.2 = 20%)
    stratify_column:
        Column to stratify by (default: "target_class")
    random_seed:
        Random seed for reproducibility
        
    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        - Training DataFrame
        - Test DataFrame
        
    Raises
    ------
    DatasetError
        If stratify column not found or split fails
    """
    if stratify_column not in df.columns:
        raise DatasetError(
            f"Stratify column '{stratify_column}' not found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )
    
    logger.info(
        "Creating train/test split: test_fraction=%.2f, seed=%d, stratify=%s",
        test_fraction,
        random_seed,
        stratify_column,
    )
    
    # Log class distribution before split
    class_counts = df[stratify_column].value_counts()
    logger.info("Class distribution (total %d rows):", len(df))
    for cls, count in class_counts.items():
        logger.info("  %s: %d (%.1f%%)", cls, count, 100 * count / len(df))
    
    # Perform stratified split
    train_df, test_df = train_test_split(
        df,
        test_size=test_fraction,
        random_state=random_seed,
        stratify=df[stratify_column],
    )
    
    logger.info("Split complete: %d train, %d test", len(train_df), len(test_df))
    
    # Log class distribution after split
    train_counts = train_df[stratify_column].value_counts()
    test_counts = test_df[stratify_column].value_counts()
    
    logger.info("Train set class distribution:")
    for cls, count in train_counts.items():
        logger.info("  %s: %d (%.1f%%)", cls, count, 100 * count / len(train_df))
    
    logger.info("Test set class distribution:")
    for cls, count in test_counts.items():
        logger.info("  %s: %d (%.1f%%)", cls, count, 100 * count / len(test_df))
    
    return train_df, test_df


def assert_disjoint(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """Assert that train and test sets have no overlapping rows.
    
    Parameters
    ----------
    train_df:
        Training DataFrame
    test_df:
        Test DataFrame
        
    Raises
    ------
    DatasetError
        If there is any overlap between train and test
    """
    train_indices = set(train_df.index)
    test_indices = set(test_df.index)
    
    overlap = train_indices & test_indices
    
    if overlap:
        raise DatasetError(
            f"Train/test split has {len(overlap)} overlapping row indices! "
            f"This indicates a data leakage error. Train and test must be disjoint."
        )
    
    logger.info("Disjointness verified: no overlap between train and test indices")


def save_split_datasets(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: Path,
    manifest_path: Path,
    config: dict[str, Any],
) -> None:
    """Save train/test datasets and generate split manifest.
    
    Parameters
    ----------
    train_df:
        Training DataFrame
    test_df:
        Test DataFrame
    output_dir:
        Directory to save train/test subdirectories
    manifest_path:
        Path to save split manifest JSON
    config:
        Configuration dict with split parameters
        
    Raises
    ------
    DatasetError
        If save fails
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    train_dir = output_dir / "train"
    test_dir = output_dir / "test"
    
    train_dir.mkdir(exist_ok=True)
    test_dir.mkdir(exist_ok=True)
    
    # Save datasets as CSV
    train_path = train_dir / "train.csv"
    test_path = test_dir / "test.csv"
    
    try:
        train_df.to_csv(train_path, index=True)
        test_df.to_csv(test_path, index=True)
        
        logger.info("Saved train set to: %s", train_path)
        logger.info("Saved test set to: %s", test_path)
        
    except Exception as exc:
        raise DatasetError(f"Failed to save datasets: {exc}") from exc
    
    # Compute hashes
    train_hash = compute_dataframe_hash(train_df)
    test_hash = compute_dataframe_hash(test_df)
    
    # Create manifest
    manifest = {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "config": config,
        "train": {
            "path": str(train_path.relative_to(output_dir.parent)),
            "rows": len(train_df),
            "columns": len(train_df.columns),
            "sha256": train_hash,
            "row_indices": list(train_df.index),
        },
        "test": {
            "path": str(test_path.relative_to(output_dir.parent)),
            "rows": len(test_df),
            "columns": len(test_df.columns),
            "sha256": test_hash,
            "row_indices": list(test_df.index),
        },
    }
    
    # Save manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        
        logger.info("Saved split manifest to: %s", manifest_path)
        
    except Exception as exc:
        raise DatasetError(f"Failed to save manifest: {exc}") from exc


def load_split_dataset(split_dir: Path, split_name: str = "train") -> pd.DataFrame:
    """Load a train or test split from disk.
    
    Parameters
    ----------
    split_dir:
        Directory containing split subdirectories (e.g., data/processed/)
    split_name:
        "train" or "test"
        
    Returns
    -------
    pd.DataFrame
        Loaded DataFrame
        
    Raises
    ------
    DatasetError
        If split cannot be loaded
    """
    split_path = split_dir / split_name / f"{split_name}.csv"
    
    if not split_path.exists():
        raise DatasetError(
            f"Split not found: {split_path}. "
            f"Run preprocessing to create train/test splits first."
        )
    
    try:
        df = pd.read_csv(split_path, index_col=0)
        logger.info("Loaded %s split: %d rows, %d columns", split_name, len(df), len(df.columns))
        return df
        
    except Exception as exc:
        raise DatasetError(f"Failed to load {split_name} split: {exc}") from exc
