"""
preprocessing/feature_selector.py
----------------------------------
Staged feature selection for FlowSentry (CN-005, Phase 2).

Implements the staged feature selector per RID-08:
  Stage 1: Variance threshold - Remove low-variance features
  Stage 2: Correlation filter - Remove highly correlated features
  Stage 3: Model-based importance - Select top-k features by importance

Selector must fit only inside training folds (never on test data).

TRD §9, ML-005, ML-009, RID-08, CN-005.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel, VarianceThreshold

logger = logging.getLogger(__name__)


class CorrelationFilter(BaseEstimator, TransformerMixin):
    """Remove one feature from each highly correlated pair.
    
    Parameters
    ----------
    threshold : float, default=0.95
        Correlation coefficient threshold (absolute value).
        If |correlation| > threshold, remove one of the pair.
        
    Notes
    -----
    For each highly correlated pair, removes the feature that appears
    second in the column order (arbitrary but deterministic).
    
    Fits only on training data to determine which features to remove.
    """
    
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.features_to_remove_: list[str] | None = None
        self.feature_names_in_: np.ndarray | None = None
        
    def fit(self, X, y=None):
        """Identify features to remove based on correlation.
        
        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data
        y : array-like of shape (n_samples,), optional
            Target values (not used, for compatibility)
            
        Returns
        -------
        self
            Fitted transformer
        """
        # Convert to DataFrame for easier handling
        if isinstance(X, pd.DataFrame):
            df = X
            self.feature_names_in_ = np.array(df.columns)
        else:
            df = pd.DataFrame(X)
            self.feature_names_in_ = np.array([f"feature_{i}" for i in range(X.shape[1])])
            df.columns = self.feature_names_in_
        
        # Compute correlation matrix
        corr_matrix = df.corr().abs()
        
        # Find features to remove
        to_remove = set()
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                if corr_matrix.iloc[i, j] > self.threshold:
                    # Remove the second feature in the pair
                    feature_name = corr_matrix.columns[j]
                    to_remove.add(feature_name)
        
        self.features_to_remove_ = list(to_remove)
        
        if self.features_to_remove_:
            logger.info(
                "CorrelationFilter: Removing %d features with |r| > %.2f",
                len(self.features_to_remove_),
                self.threshold,
            )
            for feat in self.features_to_remove_:
                logger.info("  - %s", feat)
        else:
            logger.info(
                "CorrelationFilter: No features to remove (threshold=%.2f)",
                self.threshold,
            )
        
        return self
    
    def transform(self, X):
        """Remove highly correlated features.
        
        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to transform
            
        Returns
        -------
        X_transformed : array-like of shape (n_samples, n_features_new)
            Data with correlated features removed
        """
        if self.features_to_remove_ is None:
            raise ValueError("CorrelationFilter must be fitted before transform")
        
        if isinstance(X, pd.DataFrame):
            return X.drop(columns=self.features_to_remove_, errors='ignore')
        else:
            # For numpy arrays, need to map feature names to indices
            if self.feature_names_in_ is None:
                return X  # Can't filter without feature names
            
            indices_to_keep = [
                i for i, name in enumerate(self.feature_names_in_)
                if name not in self.features_to_remove_
            ]
            return X[:, indices_to_keep]
    
    def get_feature_names_out(self, input_features=None):
        """Get feature names after transformation.
        
        Parameters
        ----------
        input_features : array-like of str, optional
            Input feature names
            
        Returns
        -------
        feature_names_out : ndarray of str
            Output feature names
        """
        if input_features is None:
            input_features = self.feature_names_in_
        
        if self.features_to_remove_ is None:
            return np.array(input_features)
        
        return np.array([
            name for name in input_features
            if name not in self.features_to_remove_
        ])


def build_staged_selector(
    variance_threshold: float = 0.01,
    correlation_threshold: float = 0.95,
    importance_threshold: str | float = "mean",
    max_features: int | None = None,
    random_state: int = 42,
) -> list[tuple[str, BaseEstimator]]:
    """Build staged feature selector pipeline steps.
    
    Parameters
    ----------
    variance_threshold : float, default=0.01
        Features with variance below this are removed
    correlation_threshold : float, default=0.95
        Feature pairs with |correlation| above this have one removed
    importance_threshold : str or float, default="mean"
        Threshold for SelectFromModel:
        - "mean": keep features with importance >= mean
        - "median": keep features with importance >= median
        - float: keep features with importance >= threshold
    max_features : int or None, default=None
        Maximum number of features to keep (None = no limit)
    random_state : int, default=42
        Random seed for reproducibility
        
    Returns
    -------
    list of (name, transformer) tuples
        Pipeline steps for feature selection
        
    Notes
    -----
    Stage 1: VarianceThreshold - Remove constant/near-constant features
    Stage 2: CorrelationFilter - Remove highly correlated features  
    Stage 3: SelectFromModel - Keep top features by importance
    
    All stages fit only on training data, never on test data.
    """
    steps = []
    
    # Stage 1: Variance threshold
    steps.append((
        "variance_filter",
        VarianceThreshold(threshold=variance_threshold)
    ))
    
    # Stage 2: Correlation filter
    steps.append((
        "correlation_filter",
        CorrelationFilter(threshold=correlation_threshold)
    ))
    
    # Stage 3: Model-based importance
    # Use RandomForestClassifier to compute feature importances
    estimator = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=random_state,
        n_jobs=-1,
    )
    
    steps.append((
        "importance_selector",
        SelectFromModel(
            estimator=estimator,
            threshold=importance_threshold,
            max_features=max_features,
        )
    ))
    
    logger.info(
        "Built staged selector: variance(%.3f) → correlation(%.2f) → importance(%s)",
        variance_threshold,
        correlation_threshold,
        importance_threshold,
    )
    
    return steps


def build_feature_selector(
    variance_threshold: float = 0.01,
    correlation_threshold: float = 0.95,
    importance_n_estimators: int = 100,
    random_state: int = 42,
):
    """Build feature selector as a sklearn Pipeline.
    
    Parameters
    ----------
    variance_threshold : float, default=0.01
        Features with variance below this are removed
    correlation_threshold : float, default=0.95
        Feature pairs with |correlation| above this have one removed
    importance_n_estimators : int, default=100
        Number of trees in RandomForest for importance ranking
    random_state : int, default=42
        Random seed for reproducibility
        
    Returns
    -------
    Pipeline
        Feature selection pipeline
        
    Notes
    -----
    Convenience function that wraps build_staged_selector() and returns
    a Pipeline object for use in the full model pipeline.
    
    IMPORTANT: Set memory=None to prevent sklearn from exposing
    internal estimator parameters in GridSearchCV.
    """
    from sklearn.pipeline import Pipeline
    
    steps = build_staged_selector(
        variance_threshold=variance_threshold,
        correlation_threshold=correlation_threshold,
        importance_threshold="mean",
        max_features=None,
        random_state=random_state,
    )
    
    # memory=None prevents GridSearchCV from searching nested estimator params
    return Pipeline(steps, memory=None)


def get_selected_features(selector_pipeline, feature_names: list[str]) -> list[str]:
    """Get list of features selected by the pipeline.
    
    Parameters
    ----------
    selector_pipeline : Pipeline
        Fitted feature selection pipeline
    feature_names : list of str
        Original feature names
        
    Returns
    -------
    list of str
        Names of selected features
    """
    # Get support mask from the final transformer
    final_transformer = selector_pipeline.steps[-1][1]
    
    if hasattr(final_transformer, 'get_support'):
        support = final_transformer.get_support()
        
        # Need to track features through each stage
        current_features = feature_names
        
        for name, transformer in selector_pipeline.steps:
            if hasattr(transformer, 'get_support'):
                support_mask = transformer.get_support()
                current_features = [
                    feat for feat, keep in zip(current_features, support_mask) if keep
                ]
            elif hasattr(transformer, 'get_feature_names_out'):
                current_features = list(transformer.get_feature_names_out(current_features))
        
        return current_features
    
    return feature_names  # Fallback if can't determine
