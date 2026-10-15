"""
evaluation/test_loader.py
-------------------------
Test set loader with access control for FlowSentry (CN-010, Phase 4).

The test set may ONLY be loaded by evaluation code for final evaluation.
This module implements the structural leakage guard.

TRD §12, ML-008, AGENTS.md ML rules, CN-010.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from common.errors import DatasetError, LeakageGuardError
from common.paths import ProjectPaths

logger = logging.getLogger(__name__)

# Track test set access for audit log
_test_set_access_log = []


def load_test_set(
    paths: ProjectPaths,
    purpose: str = "final_evaluation",
) -> tuple[pd.DataFrame, pd.Series]:
    """Load the frozen test set for final evaluation.
    
    Parameters
    ----------
    paths : ProjectPaths
        Project paths configuration
    purpose : str, default="final_evaluation"
        Purpose of loading (for audit log)
        Must be "final_evaluation" - any other value raises error
        
    Returns
    -------
    X_test : DataFrame
        Test features
    y_test : Series
        Test labels (string class names)
        
    Raises
    ------
    LeakageGuardError
        If purpose is not "final_evaluation" (prevents accidental access)
    DatasetError
        If test set file not found
        
    Notes
    -----
    STRUCTURAL LEAKAGE GUARD:
    - Only evaluation/ may call this function
    - Test set is loaded exactly once per model for final evaluation
    - Every access is logged for audit trail
    - Test set is NEVER used for:
      * Hyperparameter tuning
      * Feature selection
      * Model selection
      * Any training decisions
    
    The test set was created in CN-004 and has been frozen since then.
    It has never been touched by any training or preprocessing code.
    """
    # Guard: only allow final evaluation
    if purpose != "final_evaluation":
        raise LeakageGuardError(
            f"Test set access denied: purpose='{purpose}' is not 'final_evaluation'. "
            "The test set may ONLY be loaded for final evaluation, never for "
            "training, tuning, feature selection, or model selection."
        )
    
    # Audit log
    import inspect
    caller_frame = inspect.stack()[1]
    caller_info = f"{caller_frame.filename}:{caller_frame.lineno} in {caller_frame.function}"
    
    _test_set_access_log.append({
        'purpose': purpose,
        'caller': caller_info,
    })
    
    logger.warning(
        "TEST SET ACCESS: purpose='%s', caller=%s, access_count=%d",
        purpose,
        caller_info,
        len(_test_set_access_log)
    )
    
    # Load test set
    test_dir = paths.data_processed / 'test'
    test_path = test_dir / 'test.csv'
    
    if not test_path.exists():
        raise DatasetError(f"Test set not found: {test_path}")
    
    logger.info("Loading test set from %s", test_path)
    df = pd.read_csv(test_path)
    
    if 'target_class' not in df.columns:
        raise DatasetError("Missing 'target_class' column in test set")
    
    # Separate features and labels
    X_test = df.drop(columns=['target_class'])
    y_test = df['target_class']
    
    # Drop metadata columns (same as training)
    metadata_cols = [
        col for col in X_test.columns
        if col in ['class1', 'flow_id', 'src_ip', 'dst_ip']
        or col.startswith('Unnamed:')
    ]
    if metadata_cols:
        logger.info("Dropping metadata columns: %s", metadata_cols)
        X_test = X_test.drop(columns=metadata_cols)
    
    logger.info("Loaded test set: %d samples, %d features", len(X_test), X_test.shape[1])
    logger.info("Test set class distribution: %s", y_test.value_counts().to_dict())
    
    return X_test, y_test


def get_test_access_log() -> list[dict]:
    """Get the test set access audit log.
    
    Returns
    -------
    list of dict
        Access log entries with purpose and caller information
        
    Notes
    -----
    Used for verification that test set was only accessed appropriately.
    Each model should have exactly one access for final evaluation.
    """
    return _test_set_access_log.copy()
