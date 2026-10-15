"""
preprocessing/preprocess.py
---------------------------
Main preprocessing orchestration script for FlowSentry (CN-004, Phase 2).

Orchestrates the complete preprocessing pipeline:
  1. Load raw datasets
  2. Apply label mapping (G-LABEL enforced)
  3. Clean data (remove duplicates, handle inf/NaN)
  4. Create train/test split (stratified)
  5. Build and fit preprocessing pipeline on training data only
  6. Save processed datasets and pipeline

Run:
    python -m preprocessing.preprocess

TRD §4-8, CN-004.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from common.config import load_config
from common.errors import DatasetError
from common.paths import ProjectPaths
from preprocessing.cleaning import clean_dataset
from preprocessing.inspect import read_dataset_file
from preprocessing.label_mapping import (
    apply_label_mapping,
    get_mapping_hash,
    load_label_mapping_config,
)
from preprocessing.pipeline import build_preprocessor, get_pipeline_params
from preprocessing.split import (
    assert_disjoint,
    create_train_test_split,
    save_split_datasets,
)

logger = logging.getLogger(__name__)


def load_datasets_from_manifest(
    manifest_path: Path,
    dataset_filter: str | None = None,
) -> list[tuple[str, pd.DataFrame]]:
    """Load all dataset files from the manifest.
    
    Parameters
    ----------
    manifest_path:
        Path to manifest.json
    dataset_filter:
        Optional: only load files containing this string (e.g., "ScenarioB")
        
    Returns
    -------
    list[tuple[str, pd.DataFrame]]
        List of (filename, dataframe) tuples
    """
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    
    raw_dir = manifest_path.parent.parent / "raw"
    datasets = []
    
    for file_entry in manifest["files"]:
        rel_path = file_entry["relative_path"]
        file_format = file_entry["format"]
        
        # Skip non-data files
        if file_format not in ["CSV", "ARFF"]:
            logger.debug("Skipping non-data file: %s", rel_path)
            continue
        
        # Apply filter if specified
        if dataset_filter and dataset_filter not in rel_path:
            logger.debug("Skipping file (filter): %s", rel_path)
            continue
        
        file_path = raw_dir / rel_path
        logger.info("Loading: %s", rel_path)
        
        df, _ = read_dataset_file(file_path)
        datasets.append((rel_path, df))
    
    logger.info("Loaded %d dataset files", len(datasets))
    return datasets


def main() -> None:
    """Main preprocessing orchestration."""
    parser = argparse.ArgumentParser(
        description="FlowSentry preprocessing pipeline (CN-004)"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/processed/manifest.json"),
        help="Path to dataset manifest",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/default.yaml"),
        help="Path to main config file",
    )
    parser.add_argument(
        "--label-config",
        type=Path,
        default=Path("config/label_mapping.yaml"),
        help="Path to label mapping config",
    )
    parser.add_argument(
        "--filter",
        type=str,
        default="ScenarioB",
        help="Only process files containing this string (default: ScenarioB)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed"),
        help="Output directory for processed datasets",
    )
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
    )
    
    logger.info("=" * 72)
    logger.info("FlowSentry Preprocessing Pipeline (CN-004)")
    logger.info("=" * 72)
    logger.info("Started: %s", datetime.now().isoformat())
    
    try:
        # Load configurations
        config = load_config(args.config)
        paths = ProjectPaths(config)
        paths.ensure_dirs()
        
        label_config = load_label_mapping_config(args.label_config)
        mapping_hash = get_mapping_hash(args.label_config)
        
        logger.info("Configuration loaded")
        logger.info("  Random seed: %d", config["seed"])
        logger.info("  Test fraction: %.2f", config["split"]["test_fraction"])
        logger.info("  Stratify: %s", config["split"]["stratify"])
        logger.info("  Label mapping hash: %s", mapping_hash[:16] + "...")
        
        # Load datasets
        logger.info("")
        logger.info("Step 1: Loading datasets")
        logger.info("-" * 72)
        
        datasets = load_datasets_from_manifest(args.manifest, args.filter)
        
        if not datasets:
            raise DatasetError(
                f"No datasets found matching filter '{args.filter}'. "
                f"Check manifest: {args.manifest}"
            )
        
        # Concatenate all datasets
        logger.info("Concatenating %d dataset files...", len(datasets))
        all_dfs = [df for _, df in datasets]
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        logger.info("Combined dataset: %d rows, %d columns", len(combined_df), len(combined_df.columns))
        
        # Apply label mapping
        logger.info("")
        logger.info("Step 2: Applying label mapping")
        logger.info("-" * 72)
        
        mapped_df, mapping_metadata = apply_label_mapping(
            combined_df,
            dataset_name="ISCX-VPN2016",
            config=label_config,
        )
        
        # Clean data
        logger.info("")
        logger.info("Step 3: Cleaning data")
        logger.info("-" * 72)
        
        cleaned_df, cleaning_metadata = clean_dataset(
            mapped_df,
            label_column="target_class",
            remove_metadata=True,
        )
        
        # Create train/test split
        logger.info("")
        logger.info("Step 4: Creating train/test split")
        logger.info("-" * 72)
        
        train_df, test_df = create_train_test_split(
            cleaned_df,
            test_fraction=config["split"]["test_fraction"],
            stratify_column="target_class",
            random_seed=config["seed"],
        )
        
        # Verify disjointness
        assert_disjoint(train_df, test_df)
        
        # Save datasets
        logger.info("")
        logger.info("Step 5: Saving train/test datasets")
        logger.info("-" * 72)
        
        split_config = {
            "test_fraction": config["split"]["test_fraction"],
            "stratify": config["split"]["stratify"],
            "random_seed": config["seed"],
            "label_mapping_hash": mapping_hash,
        }
        
        save_split_datasets(
            train_df,
            test_df,
            args.output,
            args.output / "split_manifest.json",
            split_config,
        )
        
        # Build and fit preprocessing pipeline
        logger.info("")
        logger.info("Step 6: Building preprocessing pipeline")
        logger.info("-" * 72)
        
        pipeline = build_preprocessor(
            imputer_strategy=config["preprocessing"]["missing_strategy"],
        )
        
        # Separate features and labels, select only numeric columns
        X_train = train_df.drop(columns=["target_class"])
        
        # Convert all columns to numeric (ARFF parser may have kept some as strings)
        for col in X_train.columns:
            X_train[col] = pd.to_numeric(X_train[col], errors='coerce')
        
        y_train = train_df["target_class"]
        
        logger.info("Fitting pipeline on training data (%d samples, %d features)...", len(X_train), len(X_train.columns))
        pipeline.fit(X_train)
        
        # Save pipeline
        pipeline_path = args.output / "preprocessing_pipeline.joblib"
        joblib.dump(pipeline, pipeline_path)
        logger.info("Saved preprocessing pipeline to: %s", pipeline_path)
        
        # Extract and log fitted parameters
        pipeline_params = get_pipeline_params(pipeline)
        logger.info("Pipeline fitted parameters:")
        for step_name, params in pipeline_params.items():
            logger.info("  %s: %d parameters", step_name, len(params))
        
        # Generate summary report
        logger.info("")
        logger.info("Step 7: Generating summary report")
        logger.info("-" * 72)
        
        summary = {
            "version": "1.0",
            "completed": datetime.now().isoformat(),
            "config": {
                "random_seed": config["seed"],
                "test_fraction": config["split"]["test_fraction"],
                "imputer_strategy": config["preprocessing"]["missing_strategy"],
            },
            "label_mapping": {
                "hash": mapping_hash,
                "original_count": mapping_metadata["original_count"],
                "mapped_count": mapping_metadata["mapped_count"],
                "dropped_count": mapping_metadata["dropped_count"],
                "class_counts": mapping_metadata["class_counts"],
            },
            "cleaning": {
                "duplicate_count": cleaning_metadata["duplicate_count"],
                "final_count": cleaning_metadata["final_count"],
            },
            "split": {
                "train_rows": len(train_df),
                "test_rows": len(test_df),
                "train_classes": train_df["target_class"].value_counts().to_dict(),
                "test_classes": test_df["target_class"].value_counts().to_dict(),
            },
            "pipeline": {
                "fitted_params": pipeline_params,
            },
        }
        
        summary_path = args.output / "preprocessing_summary.json"
        with open(summary_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
        
        logger.info("Saved summary to: %s", summary_path)
        
        # Print final summary
        logger.info("")
        logger.info("=" * 72)
        logger.info("SUCCESS: Preprocessing complete (CN-004)")
        logger.info("=" * 72)
        logger.info("Train set: %d samples", len(train_df))
        logger.info("Test set: %d samples", len(test_df))
        logger.info("Features: %d", len(X_train.columns))
        logger.info("Classes: %d", len(mapping_metadata["class_counts"]))
        logger.info("")
        logger.info("Output files:")
        logger.info("  - %s/train/train.csv", args.output)
        logger.info("  - %s/test/test.csv", args.output)
        logger.info("  - %s/split_manifest.json", args.output)
        logger.info("  - %s/preprocessing_pipeline.joblib", args.output)
        logger.info("  - %s/preprocessing_summary.json", args.output)
        logger.info("")
        logger.info("Next step: CN-005 (Feature Validation)")
        logger.info("=" * 72)
        
    except Exception as exc:
        logger.error("Preprocessing failed: %s", exc, exc_info=True)
        print(f"\nERROR: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
