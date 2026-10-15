"""
models/base.py
--------------
Base model specification interface for FlowSentry (CN-006, Phase 3).

Defines the contract that all models (Decision Tree, Random Forest, SVM, XGBoost)
must follow for consistent training, tuning, evaluation, and registration.

TRD §12, ML-001, ML-006, ML-009, ML-011, CN-006.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from sklearn.base import BaseEstimator


@dataclass
class ModelSpec:
    """Specification for a trainable model.
    
    Attributes
    ----------
    name : str
        Model name, must be one of: decision_tree, random_forest, svm, xgboost
        Used as CLI argument and in artifact paths
    estimator_factory : Callable[[], BaseEstimator]
        Function that returns a fresh unfitted estimator instance
        Example: lambda: DecisionTreeClassifier(random_state=42)
    param_space : dict[str, list]
        Hyperparameter search space for GridSearchCV
        Keys must match the estimator's parameter names exactly
        Example: {'max_depth': [None, 10, 20], 'criterion': ['gini', 'entropy']}
    notes : str
        Human-readable notes about this model (purpose, interpretation, caveats)
        
    Notes
    -----
    The estimator_factory allows each search trial to get a fresh model instance.
    Parameter names must be verified against the installed scikit-learn version
    before defining the search space (AGENTS.md anti-hallucination rule).
    
    All models receive integer-encoded labels and are wrapped in the same pipeline:
        imputer → scaler → selector → estimator
        
    Examples
    --------
    >>> from sklearn.tree import DecisionTreeClassifier
    >>> spec = ModelSpec(
    ...     name='decision_tree',
    ...     estimator_factory=lambda: DecisionTreeClassifier(random_state=42),
    ...     param_space={
    ...         'max_depth': [None, 10, 20, 30],
    ...         'min_samples_split': [2, 5, 10],
    ...         'criterion': ['gini', 'entropy']
    ...     },
    ...     notes='Interpretable baseline; export rules for viva discussion'
    ... )
    """
    name: str
    estimator_factory: Callable[[], BaseEstimator]
    param_space: dict[str, list[Any]]
    notes: str
    
    def __post_init__(self):
        """Validate the model specification."""
        valid_names = {'decision_tree', 'random_forest', 'svm', 'xgboost'}
        if self.name not in valid_names:
            raise ValueError(
                f"Invalid model name: {self.name}. "
                f"Must be one of {valid_names}"
            )
        
        if not callable(self.estimator_factory):
            raise TypeError("estimator_factory must be callable")
        
        if not isinstance(self.param_space, dict):
            raise TypeError("param_space must be a dict")
        
        # Verify that factory returns a BaseEstimator
        try:
            est = self.estimator_factory()
            if not isinstance(est, BaseEstimator):
                raise TypeError(
                    f"estimator_factory must return a sklearn BaseEstimator, "
                    f"got {type(est)}"
                )
        except Exception as e:
            raise ValueError(
                f"estimator_factory failed to create an estimator: {e}"
            ) from e
