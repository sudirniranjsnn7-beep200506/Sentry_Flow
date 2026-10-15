"""
preprocessing/label_mapping.py
-------------------------------
Label mapping module for FlowSentry (CN-004, Phase 2).

Applies the approved dataset → target label mapping from config/label_mapping.yaml.
Enforces G-LABEL gate: raises LabelMappingError unless status == "approved".

Responsibilities:
  - Load and validate label mapping configuration
  - Verify status is "approved" (G-LABEL gate enforcement)
  - Map original dataset labels to target classes
  - Drop rows with labels mapped to "DROP"
  - Report unmapped labels as errors (never silently drop)
  - Record per-class counts and dropped-label counts
  - Compute and store SHA-256 hash of the mapping config

Never invents mappings; never proceeds if status ≠ "approved".

TRD §6, DS-002, G-LABEL gate, ML-002.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from common.errors import LabelMappingError

logger = logging.getLogger(__name__)


def compute_yaml_hash(yaml_path: Path) -> str:
    """Compute SHA-256 hash of the label mapping YAML file.
    
    Parameters
    ----------
    yaml_path:
        Path to label_mapping.yaml
        
    Returns
    -------
    str
        Hex-encoded SHA-256 digest
    """
    with open(yaml_path, "rb") as fh:
        content = fh.read()
    return hashlib.sha256(content).hexdigest()


def load_label_mapping_config(config_path: Path) -> dict[str, Any]:
    """Load and validate label mapping configuration.
    
    Parameters
    ----------
    config_path:
        Path to label_mapping.yaml
        
    Returns
    -------
    dict
        Configuration dictionary
        
    Raises
    ------
    LabelMappingError
        If config cannot be read, is invalid, or status is not "approved"
    """
    if not config_path.exists():
        raise LabelMappingError(
            f"Label mapping config not found: {config_path}. "
            "Create it from the template and complete G-LABEL gate."
        )
    
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh)
    except Exception as exc:
        raise LabelMappingError(
            f"Cannot parse label mapping config: {config_path} ({exc})"
        ) from exc
    
    # Validate structure
    if not isinstance(config, dict):
        raise LabelMappingError(
            f"Label mapping config must be a dictionary, got: {type(config)}"
        )
    
    # Check required keys
    required_keys = ["status", "target_classes", "datasets"]
    for key in required_keys:
        if key not in config:
            raise LabelMappingError(
                f"Label mapping config missing required key: '{key}'"
            )
    
    # G-LABEL GATE ENFORCEMENT
    status = config.get("status")
    if status != "approved":
        raise LabelMappingError(
            f"Label mapping status is '{status}', must be 'approved'. "
            f"G-LABEL gate blocks training until the team approves the mapping "
            f"in {config_path}. Change 'status: unresolved' to 'status: approved' "
            f"after completing the label worksheet."
        )
    
    # Validate target_classes is a list
    if not isinstance(config["target_classes"], list):
        raise LabelMappingError(
            "target_classes must be a list of class names"
        )
    
    if not config["target_classes"]:
        raise LabelMappingError(
            "target_classes list is empty. Provide at least one target class."
        )
    
    logger.info(
        "Label mapping config loaded: status=%s, target_classes=%s",
        status,
        config["target_classes"],
    )
    
    return config


def apply_label_mapping(
    df: pd.DataFrame,
    dataset_name: str,
    config: dict[str, Any],
    label_column: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Apply label mapping to a DataFrame.
    
    Parameters
    ----------
    df:
        DataFrame with original labels
    dataset_name:
        Name of the dataset (e.g., "ISCX-VPN2016")
    config:
        Label mapping configuration (from load_label_mapping_config)
    label_column:
        Name of the label column. If None, auto-detected from config.
        
    Returns
    -------
    tuple[pd.DataFrame, dict]
        - DataFrame with mapped labels and dropped rows removed
        - Metadata dict with: original_count, mapped_count, dropped_count,
          dropped_labels, class_counts, unmapped_labels
          
    Raises
    ------
    LabelMappingError
        If dataset not in config, label column not found, or unmapped labels exist
    """
    # Get dataset config
    dataset_config = config.get("datasets", {}).get(dataset_name)
    if not dataset_config:
        raise LabelMappingError(
            f"Dataset '{dataset_name}' not found in label mapping config. "
            f"Available datasets: {list(config.get('datasets', {}).keys())}"
        )
    
    # Determine label column
    if label_column is None:
        label_column = dataset_config.get("label_column")
    
    if not label_column:
        raise LabelMappingError(
            f"Label column not specified for dataset '{dataset_name}'. "
            f"Set 'label_column' in config or pass explicitly."
        )
    
    if label_column not in df.columns:
        raise LabelMappingError(
            f"Label column '{label_column}' not found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )
    
    # Get mapping
    mapping = dataset_config.get("mapping", {})
    if not mapping:
        raise LabelMappingError(
            f"No label mapping defined for dataset '{dataset_name}'. "
            f"Complete the mapping in label_mapping.yaml."
        )
    
    original_count = len(df)
    logger.info(
        "Applying label mapping to %d rows from dataset '%s'",
        original_count,
        dataset_name,
    )
    
    # Check for unmapped labels (ERROR - never silently drop)
    unique_labels = df[label_column].unique()
    unmapped_labels = [
        label for label in unique_labels if label not in mapping
    ]
    
    if unmapped_labels:
        raise LabelMappingError(
            f"Unmapped labels found in dataset '{dataset_name}': {unmapped_labels}. "
            f"Every label must be mapped to a target class or 'DROP'. "
            f"Update {label_column} mapping in label_mapping.yaml."
        )
    
    # Apply mapping
    df = df.copy()
    df["_original_label"] = df[label_column]
    df["target_class"] = df[label_column].map(mapping)
    
    # Separate DROP rows
    drop_mask = df["target_class"] == "DROP"
    dropped_df = df[drop_mask].copy()
    df_mapped = df[~drop_mask].copy()
    
    # Count dropped labels
    dropped_labels = dropped_df["_original_label"].value_counts().to_dict()
    dropped_count = len(dropped_df)
    
    # Remove temporary column from final output
    df_mapped = df_mapped.drop(columns=["_original_label"])
    
    # Count per-class distribution
    class_counts = df_mapped["target_class"].value_counts().to_dict()
    
    mapped_count = len(df_mapped)
    
    logger.info(
        "Label mapping complete: %d → %d kept, %d dropped (%d unique labels dropped)",
        original_count,
        mapped_count,
        dropped_count,
        len(dropped_labels),
    )
    
    for target_class, count in sorted(class_counts.items()):
        logger.info("  Class '%s': %d samples", target_class, count)
    
    if dropped_labels:
        logger.info("Dropped labels:")
        for label, count in sorted(dropped_labels.items(), key=lambda x: -x[1]):
            logger.info("  '%s': %d samples", label, count)
    
    metadata = {
        "original_count": original_count,
        "mapped_count": mapped_count,
        "dropped_count": dropped_count,
        "dropped_labels": dropped_labels,
        "class_counts": class_counts,
        "unmapped_labels": [],  # Empty if we got here (would have raised)
        "label_column": label_column,
    }
    
    return df_mapped, metadata


def get_mapping_hash(config_path: Path) -> str:
    """Get SHA-256 hash of the label mapping config for reproducibility.
    
    Parameters
    ----------
    config_path:
        Path to label_mapping.yaml
        
    Returns
    -------
    str
        Hex-encoded SHA-256 digest
    """
    return compute_yaml_hash(config_path)
