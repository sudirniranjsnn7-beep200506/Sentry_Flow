"""
preprocessing/cleaning.py
-------------------------
Data cleaning module for FlowSentry (CN-004, Phase 2).

Deterministic data cleaning operations before train/test split.

Responsibilities:
  - Replace ±inf with NaN
  - Remove exact duplicate rows
  - Separate metadata/identifier columns from feature columns
  - Apply port-feature policy per RID-07
  - Log row counts at each step (never silently drop)

Never modifies raw data; never resamples; never fits anything.

TRD §7, DS-005, DS-007, ML-004, RID-07.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Identifier-like column patterns (will be kept as metadata, not features)
IDENTIFIER_PATTERNS = [
    "ip", "address", "port", "mac",
    "timestamp", "time", "date",
    "flow_id", "flowid", "id",
    "source", "destination", "src", "dst",
]


def replace_inf_with_nan(df: pd.DataFrame) -> pd.DataFrame:
    """Replace ±inf with NaN in numeric columns.
    
    Parameters
    ----------
    df:
        Input DataFrame
        
    Returns
    -------
    pd.DataFrame
        DataFrame with inf replaced by NaN
    """
    df = df.copy()
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    inf_counts = {}
    for col in numeric_cols:
        pos_inf_count = np.isinf(df[col]) & (df[col] > 0)
        neg_inf_count = np.isinf(df[col]) & (df[col] < 0)
        
        pos_count = pos_inf_count.sum()
        neg_count = neg_inf_count.sum()
        
        if pos_count > 0 or neg_count > 0:
            inf_counts[col] = {"pos_inf": int(pos_count), "neg_inf": int(neg_count)}
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
    
    if inf_counts:
        logger.info("Replaced ±inf with NaN:")
        for col, counts in inf_counts.items():
            logger.info(
                "  %s: +inf=%d, -inf=%d",
                col,
                counts["pos_inf"],
                counts["neg_inf"],
            )
    else:
        logger.info("No ±inf values found")
    
    return df


def remove_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove exact duplicate rows.
    
    Parameters
    ----------
    df:
        Input DataFrame
        
    Returns
    -------
    tuple[pd.DataFrame, int]
        - DataFrame with duplicates removed
        - Count of duplicates removed
    """
    original_count = len(df)
    df_dedup = df.drop_duplicates()
    duplicate_count = original_count - len(df_dedup)
    
    if duplicate_count > 0:
        logger.info(
            "Removed %d exact duplicate rows (%.2f%%)",
            duplicate_count,
            100 * duplicate_count / original_count,
        )
    else:
        logger.info("No exact duplicates found")
    
    return df_dedup, duplicate_count


def separate_metadata_features(
    df: pd.DataFrame,
    label_column: str = "target_class",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate metadata/identifier columns from feature columns.
    
    Parameters
    ----------
    df:
        Input DataFrame with all columns
    label_column:
        Name of the target label column
        
    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        - Features DataFrame (numeric columns for modeling)
        - Metadata DataFrame (identifiers, timestamps, etc.)
        
    Notes
    -----
    Identifier-like columns (IP, port, timestamp, flow ID) are moved to metadata.
    The label column is kept with features.
    Per RID-07: port numbers are excluded from model inputs by default.
    """
    # Identify metadata columns
    metadata_cols = []
    
    for col in df.columns:
        if col == label_column:
            continue  # Keep label with features
        
        col_lower = col.lower()
        
        # Check if column name matches identifier patterns
        is_identifier = any(pattern in col_lower for pattern in IDENTIFIER_PATTERNS)
        
        if is_identifier:
            metadata_cols.append(col)
    
    if metadata_cols:
        logger.info("Identified %d metadata columns:", len(metadata_cols))
        for col in metadata_cols:
            logger.info("  - %s", col)
        
        metadata_df = df[metadata_cols].copy()
        feature_cols = [col for col in df.columns if col not in metadata_cols]
        features_df = df[feature_cols].copy()
    else:
        logger.info("No metadata columns identified; all columns are features")
        features_df = df.copy()
        metadata_df = pd.DataFrame(index=df.index)
    
    logger.info(
        "Separated: %d feature columns, %d metadata columns",
        len(features_df.columns),
        len(metadata_df.columns),
    )
    
    return features_df, metadata_df


def clean_dataset(
    df: pd.DataFrame,
    label_column: str = "target_class",
    remove_metadata: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Apply all cleaning operations to a dataset.
    
    Parameters
    ----------
    df:
        Input DataFrame
    label_column:
        Name of the target label column
    remove_metadata:
        If True, separate and return only features (not metadata)
        
    Returns
    -------
    tuple[pd.DataFrame, dict]
        - Cleaned DataFrame (features only if remove_metadata=True)
        - Metadata dict with: original_count, inf_replaced_count, duplicate_count,
          final_count, metadata_columns, feature_columns
    """
    original_count = len(df)
    logger.info("Starting data cleaning: %d rows", original_count)
    
    # Step 1: Replace ±inf with NaN
    df = replace_inf_with_nan(df)
    
    # Step 2: Remove exact duplicates
    df, duplicate_count = remove_duplicates(df)
    
    # Step 3: Separate metadata and features
    if remove_metadata:
        df, metadata_df = separate_metadata_features(df, label_column)
        metadata_columns = list(metadata_df.columns)
    else:
        metadata_columns = []
    
    feature_columns = [col for col in df.columns if col != label_column]
    
    final_count = len(df)
    
    logger.info(
        "Cleaning complete: %d → %d rows (removed %d duplicates)",
        original_count,
        final_count,
        duplicate_count,
    )
    
    metadata = {
        "original_count": original_count,
        "duplicate_count": duplicate_count,
        "final_count": final_count,
        "metadata_columns": metadata_columns,
        "feature_columns": feature_columns,
        "label_column": label_column,
    }
    
    return df, metadata
