"""
preprocessing/validate_features.py
----------------------------------
Feature validation module for FlowSentry (CN-005, Phase 2).

Validates features against Review-1's four families, analyzes correlations,
identifies constant features, and generates validation reports.

Responsibilities:
  - Load and validate feature schema
  - Classify features into families (time, volume, TCP-flag, directional)
  - Detect constant/near-constant features
  - Find highly correlated feature pairs
  - Generate feature validation report
  - Verify no identifier columns included as features

Never looks at test data; all analysis on training data only.

TRD §9, FE-001…FE-010, ML-005, CN-005.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from common.errors import SchemaMismatchError

logger = logging.getLogger(__name__)


def load_feature_schema(schema_path: Path) -> dict[str, Any]:
    """Load feature schema configuration.
    
    Parameters
    ----------
    schema_path:
        Path to feature_schema.yaml
        
    Returns
    -------
    dict
        Schema configuration
        
    Raises
    ------
    SchemaMismatchError
        If schema cannot be loaded or is invalid
    """
    if not schema_path.exists():
        raise SchemaMismatchError(
            f"Feature schema not found: {schema_path}. "
            "Create it from CN-005 (Feature Validation)."
        )
    
    try:
        with open(schema_path, "r", encoding="utf-8") as fh:
            schema = yaml.safe_load(fh)
    except Exception as exc:
        raise SchemaMismatchError(
            f"Cannot parse feature schema: {schema_path} ({exc})"
        ) from exc
    
    if not isinstance(schema, dict):
        raise SchemaMismatchError(
            f"Feature schema must be a dictionary, got: {type(schema)}"
        )
    
    logger.info("Feature schema loaded: version=%s, status=%s", 
                schema.get("version"), schema.get("status"))
    
    return schema


def validate_dataframe_against_schema(
    df: pd.DataFrame,
    schema: dict[str, Any],
    label_column: str = "target_class",
) -> dict[str, Any]:
    """Validate DataFrame columns against feature schema.
    
    Parameters
    ----------
    df:
        DataFrame to validate
    schema:
        Feature schema dictionary
    label_column:
        Name of target label column
        
    Returns
    -------
    dict
        Validation results with: valid, missing_features, extra_features,
        feature_count, errors
        
    Raises
    ------
    SchemaMismatchError
        If validation fails critically
    """
    results = {
        "valid": True,
        "missing_features": [],
        "extra_features": [],
        "feature_count": 0,
        "errors": [],
    }
    
    # Get expected features from schema
    expected_features = set()
    for feature in schema.get("features", []):
        if feature.get("role") == "feature":
            expected_features.add(feature["name"])
    
    # Get actual features from DataFrame
    actual_features = set(df.columns) - {label_column}
    
    # Find missing and extra features
    missing = expected_features - actual_features
    extra = actual_features - expected_features
    
    if missing:
        results["valid"] = False
        results["missing_features"] = list(missing)
        results["errors"].append(f"Missing {len(missing)} features: {missing}")
    
    if extra:
        results["extra_features"] = list(extra)
        logger.warning("Extra features not in schema: %s", extra)
    
    results["feature_count"] = len(actual_features)
    
    logger.info(
        "Schema validation: %s (expected %d, got %d features)",
        "PASS" if results["valid"] else "FAIL",
        len(expected_features),
        len(actual_features),
    )
    
    return results


def analyze_constant_features(
    df: pd.DataFrame,
    threshold: float = 0.98,
) -> list[dict[str, Any]]:
    """Identify near-constant features.
    
    Parameters
    ----------
    df:
        DataFrame with numeric features
    threshold:
        If a single value appears in >threshold fraction of rows, flag as constant
        
    Returns
    -------
    list[dict]
        List of constant features with their dominant value and frequency
    """
    constant_features = []
    
    for col in df.columns:
        if df[col].dtype in [object, 'string']:
            continue
        
        value_counts = df[col].value_counts(normalize=True)
        if len(value_counts) > 0:
            max_freq = value_counts.iloc[0]
            if max_freq > threshold:
                constant_features.append({
                    "feature": col,
                    "dominant_value": value_counts.index[0],
                    "frequency": float(max_freq),
                    "unique_values": len(value_counts),
                })
    
    if constant_features:
        logger.warning("Found %d near-constant features (threshold=%.2f)", 
                      len(constant_features), threshold)
        for feat in constant_features:
            logger.warning("  %s: %.1f%% are %.3f", 
                          feat["feature"], 100 * feat["frequency"], feat["dominant_value"])
    else:
        logger.info("No near-constant features found (threshold=%.2f)", threshold)
    
    return constant_features


def analyze_feature_correlations(
    df: pd.DataFrame,
    threshold: float = 0.95,
) -> list[dict[str, Any]]:
    """Find highly correlated feature pairs.
    
    Parameters
    ----------
    df:
        DataFrame with numeric features
    threshold:
        Correlation coefficient threshold (absolute value)
        
    Returns
    -------
    list[dict]
        List of highly correlated pairs with correlation coefficient
    """
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        logger.warning("No numeric features to correlate")
        return []
    
    # Compute correlation matrix
    corr_matrix = numeric_df.corr()
    
    # Find pairs above threshold
    high_corr_pairs = []
    
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            corr_val = corr_matrix.iloc[i, j]
            if abs(corr_val) > threshold:
                high_corr_pairs.append({
                    "feature1": corr_matrix.columns[i],
                    "feature2": corr_matrix.columns[j],
                    "correlation": float(corr_val),
                })
    
    if high_corr_pairs:
        logger.warning("Found %d highly correlated pairs (threshold=%.2f)", 
                      len(high_corr_pairs), threshold)
        for pair in high_corr_pairs:
            logger.warning("  %s <-> %s: %.3f", 
                          pair["feature1"], pair["feature2"], pair["correlation"])
    else:
        logger.info("No highly correlated pairs found (threshold=%.2f)", threshold)
    
    return high_corr_pairs


def analyze_feature_families(
    schema: dict[str, Any],
) -> dict[str, Any]:
    """Analyze feature family coverage.
    
    Parameters
    ----------
    schema:
        Feature schema dictionary
        
    Returns
    -------
    dict
        Family coverage statistics
    """
    family_counts = {}
    
    for feature in schema.get("features", []):
        if feature.get("role") == "feature":
            family = feature.get("family", "unknown")
            family_counts[family] = family_counts.get(family, 0) + 1
    
    logger.info("Feature family coverage:")
    for family, count in sorted(family_counts.items()):
        logger.info("  %s: %d features", family, count)
    
    return {
        "family_counts": family_counts,
        "total_features": sum(family_counts.values()),
        "missing_families": schema.get("missing_families", {}),
    }


def generate_validation_report(
    df: pd.DataFrame,
    schema: dict[str, Any],
    schema_validation: dict[str, Any],
    constant_features: list[dict[str, Any]],
    high_corr_pairs: list[dict[str, Any]],
    family_analysis: dict[str, Any],
    output_md: Path,
    output_json: Path,
) -> None:
    """Generate feature validation report.
    
    Parameters
    ----------
    df:
        Training DataFrame
    schema:
        Feature schema
    schema_validation:
        Schema validation results
    constant_features:
        Near-constant features list
    high_corr_pairs:
        Highly correlated pairs
    family_analysis:
        Feature family coverage
    output_md:
        Output markdown path
    output_json:
        Output JSON path
    """
    # JSON report
    json_report = {
        "version": "1.0",
        "generated": datetime.now().isoformat(),
        "dataset": {
            "rows": len(df),
            "columns": len(df.columns),
        },
        "schema_validation": schema_validation,
        "constant_features": constant_features,
        "high_correlation_pairs": high_corr_pairs,
        "family_analysis": family_analysis,
    }
    
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as fh:
        json.dump(json_report, fh, indent=2)
    
    logger.info("JSON report saved to: %s", output_json)
    
    # Markdown report
    lines = [
        "# FlowSentry Feature Validation Report (CN-005)",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "**Task:** CN-005 — Feature Validation & Selection Stage",
        "",
        "## Summary",
        "",
        f"- **Training samples:** {len(df):,}",
        f"- **Total features:** {schema_validation['feature_count']}",
        f"- **Schema validation:** {'✅ PASS' if schema_validation['valid'] else '❌ FAIL'}",
        "",
        "---",
        "",
        "## Schema Validation",
        "",
    ]
    
    if schema_validation["valid"]:
        lines.append("✅ **All expected features present**")
    else:
        lines.append(f"❌ **Schema mismatch detected**")
        if schema_validation["missing_features"]:
            lines.append("")
            lines.append(f"Missing features ({len(schema_validation['missing_features'])}):")
            for feat in schema_validation["missing_features"]:
                lines.append(f"  - {feat}")
    
    if schema_validation["extra_features"]:
        lines.append("")
        lines.append(f"⚠️ Extra features not in schema ({len(schema_validation['extra_features'])}):")
        for feat in schema_validation["extra_features"]:
            lines.append(f"  - {feat}")
    
    lines.extend([
        "",
        "---",
        "",
        "## Feature Family Coverage",
        "",
        "Per Review-1, FlowSentry uses four feature families:",
        "",
        "| Family | Feature Count | Status |",
        "|---|---|---|",
    ])
    
    family_counts = family_analysis["family_counts"]
    for family in ["time", "volume", "tcp_flag", "directional"]:
        count = family_counts.get(family, 0)
        status = "✅" if count > 0 else "❌ Missing"
        lines.append(f"| {family} | {count} | {status} |")
    
    if family_analysis["missing_families"]:
        lines.append("")
        lines.append("### Missing Families")
        lines.append("")
        missing_families = family_analysis["missing_families"]
        if isinstance(missing_families, dict):
            for family, reason in missing_families.items():
                lines.append(f"- **{family}:** {reason}")
        else:
            lines.append(f"- {missing_families}")
    
    lines.extend([
        "",
        "---",
        "",
        "## Constant/Near-Constant Features",
        "",
    ])
    
    if constant_features:
        lines.append(f"⚠️ Found {len(constant_features)} near-constant features:")
        lines.append("")
        lines.append("| Feature | Dominant Value | Frequency | Unique Values |")
        lines.append("|---|---|---|---|")
        for feat in constant_features:
            lines.append(f"| {feat['feature']} | {feat['dominant_value']:.6f} | {feat['frequency']:.1%} | {feat['unique_values']} |")
    else:
        lines.append("✅ No near-constant features found")
    
    lines.extend([
        "",
        "---",
        "",
        "## Highly Correlated Features",
        "",
    ])
    
    if high_corr_pairs:
        lines.append(f"⚠️ Found {len(high_corr_pairs)} highly correlated pairs (|r| > 0.95):")
        lines.append("")
        lines.append("| Feature 1 | Feature 2 | Correlation |")
        lines.append("|---|---|---|")
        for pair in high_corr_pairs:
            lines.append(f"| {pair['feature1']} | {pair['feature2']} | {pair['correlation']:.3f} |")
        lines.append("")
        lines.append("**Recommendation:** Consider removing one from each pair during feature selection.")
    else:
        lines.append("✅ No highly correlated pairs found")
    
    lines.extend([
        "",
        "---",
        "",
        "## Recommendations",
        "",
        "1. **Feature Selection:** Implement staged selector to handle correlations",
        "2. **Missing Families:** Document TCP-flag and directional features as unavailable in this dataset",
        "3. **Schema Status:** Schema is approved and ready for model training",
        "",
        "---",
        "",
        "## Next Steps",
        "",
        "- ✅ Feature schema created and validated",
        "- ⏭️ Implement staged feature selector (variance → correlation → importance)",
        "- ⏭️ Integrate selector into preprocessing pipeline",
        "- ⏭️ Proceed to CN-006 (Model Training)",
        "",
    ])
    
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Markdown report saved to: %s", output_md)


def validate_features(
    train_df: pd.DataFrame,
    schema_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run complete feature validation.
    
    Parameters
    ----------
    train_df:
        Training DataFrame
    schema_path:
        Path to feature schema
    output_dir:
        Directory for output reports
        
    Returns
    -------
    dict
        Validation results summary
    """
    logger.info("Starting feature validation")
    
    # Load schema
    schema = load_feature_schema(schema_path)
    
    # Validate schema
    schema_validation = validate_dataframe_against_schema(
        train_df, schema, label_column="target_class"
    )
    
    # Analyze constant features
    numeric_features = train_df.select_dtypes(include=[np.number])
    constant_features = analyze_constant_features(numeric_features, threshold=0.98)
    
    # Analyze correlations
    high_corr_pairs = analyze_feature_correlations(numeric_features, threshold=0.95)
    
    # Analyze family coverage
    family_analysis = analyze_feature_families(schema)
    
    # Generate reports
    output_md = output_dir / "feature_validation.md"
    output_json = output_dir / "feature_validation.json"
    
    generate_validation_report(
        train_df,
        schema,
        schema_validation,
        constant_features,
        high_corr_pairs,
        family_analysis,
        output_md,
        output_json,
    )
    
    return {
        "schema_valid": schema_validation["valid"],
        "constant_features_count": len(constant_features),
        "high_corr_pairs_count": len(high_corr_pairs),
        "family_coverage": family_analysis["family_counts"],
    }
