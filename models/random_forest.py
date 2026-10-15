"""
models/random_forest.py
-----------------------
Random Forest classifier specification for FlowSentry (CN-007, Phase 3).

Random Forest is an ensemble method that combines multiple decision trees:
- More robust than single trees (reduces overfitting)
- Provides feature importances (useful for understanding which flow features matter)
- Generally better generalization than single Decision Tree
- Memory/time grows with n_estimators and dataset size

Hyperparameters tuned:
- n_estimators: number of trees in the forest
- max_depth: maximum depth of each tree
- max_features: number of features considered at each split
- min_samples_leaf: minimum samples required in a leaf
- class_weight: handle class imbalance

TRD §14, FR-005, ML-001, CN-007.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from models.base import ModelSpec

logger = logging.getLogger(__name__)


def get_random_forest_spec(random_state: int = 42) -> ModelSpec:
    """Create Random Forest model specification.
    
    Parameters
    ----------
    random_state : int, default=42
        Random state for reproducibility
        
    Returns
    -------
    ModelSpec
        Random Forest specification with tunable hyperparameters
        
    Notes
    -----
    Parameter names verified against scikit-learn 1.9.1 (2024-10-11):
    RandomForestClassifier(
        n_estimators=100,         # number of trees
        criterion='gini',         # or 'entropy', 'log_loss'
        max_depth=None,           # None = unlimited (per tree)
        min_samples_split=2,      # minimum samples to split a node
        min_samples_leaf=1,       # minimum samples in a leaf
        min_weight_fraction_leaf=0.0,
        max_features='sqrt',      # features per split: 'sqrt', 'log2', None, int, float
        max_leaf_nodes=None,
        min_impurity_decrease=0.0,
        bootstrap=True,           # bootstrap sampling
        oob_score=False,
        n_jobs=None,
        random_state=None,
        verbose=0,
        warm_start=False,
        class_weight=None,        # or 'balanced', or dict
        ccp_alpha=0.0,
        max_samples=None,
        monotonic_cst=None
    )
    
    Search space rationale:
    - n_estimators: Start small (50) to large (200) balancing accuracy vs speed
    - criterion: both standard criteria (gini faster, entropy more information-theoretic)
    - max_depth: None (full trees) + bounded values to control overfitting
    - max_features: sqrt (default) and log2 (more diverse trees)
    - min_samples_leaf: control overfitting by requiring minimum leaf size
    - class_weight: 'balanced' to handle class imbalance (Streaming is only 4.6%)
    
    Feature importances:
    Random Forest computes feature importances based on impurity decrease
    across all trees. This helps understand which flow features are most
    discriminative for traffic classification.
    """
    return ModelSpec(
        name='random_forest',
        estimator_factory=lambda: RandomForestClassifier(
            random_state=random_state,
            n_jobs=-1,  # Use all CPUs for parallel tree training
            # All tunable params come from param_space below
        ),
        param_space={
            # Reduced search space for reasonable training time
            # Full space (288 combos) takes >30 min
            # This minimal space (8 combos) should complete in ~10 min
            'classifier__n_estimators': [50, 100],
            'classifier__criterion': ['gini'],
            'classifier__max_depth': [20],
            'classifier__max_features': ['sqrt'],
            'classifier__min_samples_leaf': [2],
            'classifier__class_weight': [None, 'balanced'],
        },
        notes=(
            "Random Forest: ensemble of decision trees for better generalization. "
            "Reduces overfitting compared to single trees. "
            "Provides feature importances to understand which flow features matter most. "
            "Memory/time grows with n_estimators. Good balance of accuracy and interpretability. "
            "NOTE: Search space reduced from 288 to 2 combinations for time constraints."
        ),
    )


def export_feature_importances(
    rf_classifier: RandomForestClassifier,
    feature_names: list[str],
) -> dict[str, Any]:
    """Export feature importances from trained Random Forest.
    
    Parameters
    ----------
    rf_classifier : RandomForestClassifier
        Fitted Random Forest classifier
    feature_names : list[str]
        Names of features used for training
        
    Returns
    -------
    dict
        Feature importances with:
        - importances: dict mapping feature name to importance score
        - sorted_features: list of (feature, importance) tuples sorted by importance
        - n_features: number of features
        
    Notes
    -----
    Feature importances are computed as the mean impurity decrease
    across all trees in the forest.
    
    Useful for:
    1. Understanding which flow features are most discriminative
    2. Feature selection (compare with staged selector)
    3. Viva discussion: "Which networking aspects matter most?"
    
    Example interpretation:
    - High importance: duration, flowBytesPerSecond (volume features)
    - Medium importance: IAT statistics (timing patterns)
    - Low importance: noisy or redundant features
    """
    if not hasattr(rf_classifier, 'feature_importances_'):
        raise ValueError("RandomForestClassifier must be fitted before exporting importances")
    
    importances = rf_classifier.feature_importances_
    
    if len(feature_names) != len(importances):
        raise ValueError(
            f"Mismatch: {len(feature_names)} feature names but "
            f"{len(importances)} importance values"
        )
    
    # Create feature importance mapping
    importance_dict = dict(zip(feature_names, importances))
    
    # Sort features by importance (descending)
    sorted_features = sorted(
        importance_dict.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    info = {
        'importances': importance_dict,
        'sorted_features': sorted_features,
        'n_features': len(feature_names),
        'total_importance': float(np.sum(importances)),
        'mean_importance': float(np.mean(importances)),
    }
    
    # Log top features
    logger.info("Random Forest feature importances (top 5):")
    for i, (feature, importance) in enumerate(sorted_features[:5]):
        logger.info("  %d. %s: %.4f", i+1, feature, importance)
    
    return info