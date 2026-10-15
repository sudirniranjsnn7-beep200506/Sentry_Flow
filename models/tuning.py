"""
models/tuning.py
----------------
Hyperparameter tuning utilities for FlowSentry (CN-006, Phase 3).

Cross-validation and grid search functions that respect the ML rules:
- Fit only on training data (never test)
- Stratified K-fold CV inside training set
- Macro-F1 scoring (RID-20)
- Full pipeline (imputer → scaler → selector → model)
- All CV trials saved for analysis

TRD §12, ML-006, ML-009, ML-011, RID-20, CN-006.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


def tune_model(
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    param_grid: dict[str, list[Any]],
    cv_folds: int = 5,
    scoring: str = "f1_macro",
    random_state: int | None = 42,
    n_jobs: int = -1,
) -> tuple[GridSearchCV, float]:
    """Tune hyperparameters via stratified K-fold cross-validation.
    
    Parameters
    ----------
    pipeline : Pipeline
        sklearn Pipeline with preprocessing + model steps
        Final step is the estimator to tune
    X_train : DataFrame
        Training features (already split from test)
    y_train : Series
        Training labels (integer-encoded)
    param_grid : dict
        Hyperparameter search space
        Keys should be prefixed with final estimator step name
        Example: {'estimator__max_depth': [None, 10, 20]}
    cv_folds : int, default=5
        Number of cross-validation folds
    scoring : str, default='f1_macro'
        Scoring metric for model selection (RID-20)
        Options: 'f1_macro', 'f1_weighted', 'accuracy', 'precision_macro', etc.
    random_state : int or None, default=42
        Random state for reproducibility
    n_jobs : int, default=-1
        Number of parallel jobs (-1 = all CPUs)
        
    Returns
    -------
    search : GridSearchCV
        Fitted GridSearchCV object with all CV results
    elapsed : float
        Wall-clock time in seconds
        
    Notes
    -----
    Cross-validation is ONLY on training data. The test set is never seen.
    
    Stratified K-fold ensures each fold has proportional class representation.
    This is critical for imbalanced classes (Streaming is only 4.6%).
    
    All preprocessing steps (imputer, scaler, selector) are fit inside each CV fold
    to prevent data leakage.
    
    The pipeline's final step is the estimator to tune. Parameter names must
    be prefixed with the step name, e.g., 'classifier__max_depth'.
    """
    logger.info(
        "Starting hyperparameter tuning: %d folds, scoring=%s, %d parameter combinations",
        cv_folds,
        scoring,
        _count_param_combinations(param_grid),
    )
    logger.info("Training samples: %d", len(X_train))
    
    # Create stratified K-fold splitter
    cv_splitter = StratifiedKFold(
        n_splits=cv_folds,
        shuffle=True,
        random_state=random_state,
    )
    
    # Create grid search
    search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        cv=cv_splitter,
        scoring=scoring,
        n_jobs=n_jobs,
        verbose=1,
        return_train_score=True,
        error_score='raise',  # fail loudly on errors
    )
    
    # Run search
    logger.info("Fitting GridSearchCV...")
    start_time = time.time()
    
    search.fit(X_train, y_train)
    
    elapsed = time.time() - start_time
    
    logger.info("Tuning complete in %.2f seconds", elapsed)
    logger.info("Best score (CV %s): %.4f", scoring, search.best_score_)
    logger.info("Best parameters: %s", search.best_params_)
    
    return search, elapsed


def extract_cv_results(search: GridSearchCV) -> pd.DataFrame:
    """Extract CV results from GridSearchCV into a DataFrame.
    
    Parameters
    ----------
    search : GridSearchCV
        Fitted GridSearchCV object
        
    Returns
    -------
    DataFrame
        CV results with columns:
        - params: parameter combination
        - mean_train_score, std_train_score
        - mean_test_score, std_test_score
        - rank_test_score
        - mean_fit_time, std_fit_time
        
    Notes
    -----
    'test' scores are actually CV fold validation scores (not the held-out test set).
    The held-out test set is never accessed during training/tuning.
    """
    df = pd.DataFrame(search.cv_results_)
    
    # Select key columns
    columns_to_keep = [
        'params',
        'mean_train_score',
        'std_train_score',
        'mean_test_score',
        'std_test_score',
        'rank_test_score',
        'mean_fit_time',
        'std_fit_time',
    ]
    
    # Add all param columns
    param_cols = [col for col in df.columns if col.startswith('param_')]
    columns_to_keep = param_cols + columns_to_keep
    
    df = df[columns_to_keep].copy()
    
    # Sort by rank
    df = df.sort_values('rank_test_score')
    
    return df


def _count_param_combinations(param_grid: dict[str, list[Any]]) -> int:
    """Count total parameter combinations in a grid."""
    count = 1
    for values in param_grid.values():
        count *= len(values)
    return count
