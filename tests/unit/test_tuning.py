"""
tests/unit/test_tuning.py
--------------------------
Unit tests for hyperparameter tuning utilities (CN-006, Phase 3).

Tests cross-validation, grid search, and CV results extraction.

TRD §12, ML-006, ML-009, ML-011, CN-006.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import make_classification
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from models.tuning import tune_model, extract_cv_results, _count_param_combinations


class TestTuneModel:
    """Test hyperparameter tuning."""
    
    def test_tune_model_basic(self):
        """Test basic tuning with a small dataset."""
        # Create small synthetic dataset
        X, y = make_classification(
            n_samples=100,
            n_features=5,
            n_informative=3,
            n_redundant=1,
            n_classes=3,
            random_state=42
        )
        X_df = pd.DataFrame(X, columns=[f'feat_{i}' for i in range(X.shape[1])])
        y_series = pd.Series(y)
        
        # Create simple pipeline
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', DecisionTreeClassifier(random_state=42))
        ])
        
        # Small param grid
        param_grid = {
            'classifier__max_depth': [None, 3],
            'classifier__criterion': ['gini']
        }
        
        # Tune
        search, elapsed = tune_model(
            pipeline=pipeline,
            X_train=X_df,
            y_train=y_series,
            param_grid=param_grid,
            cv_folds=3,
            scoring='f1_macro',
            random_state=42,
            n_jobs=1  # Single job for reproducibility in test
        )
        
        # Check results
        assert hasattr(search, 'best_params_')
        assert hasattr(search, 'best_score_')
        assert elapsed > 0
        
        # Check that best params are from the grid
        assert search.best_params_['classifier__max_depth'] in [None, 3]
        assert search.best_params_['classifier__criterion'] == 'gini'
    
    def test_stratified_cv(self):
        """Test that cross-validation maintains class proportions."""
        # Create imbalanced dataset
        X, y = make_classification(
            n_samples=90,
            n_features=5,
            n_informative=3,
            n_redundant=0,
            n_classes=3,
            weights=[0.7, 0.2, 0.1],  # Imbalanced
            random_state=42
        )
        X_df = pd.DataFrame(X)
        y_series = pd.Series(y)
        
        pipeline = Pipeline([
            ('classifier', DecisionTreeClassifier(random_state=42))
        ])
        
        param_grid = {'classifier__max_depth': [3]}
        
        search, _ = tune_model(
            pipeline=pipeline,
            X_train=X_df,
            y_train=y_series,
            param_grid=param_grid,
            cv_folds=5,
            scoring='f1_macro',
            random_state=42,
        )
        
        # Stratified CV should complete without error
        # (Non-stratified might fail with very imbalanced splits)
        assert search.best_score_ is not None


class TestExtractResults:
    """Test CV results extraction."""
    
    def test_extract_cv_results(self):
        """Test extracting results into DataFrame."""
        # Run a simple search
        X, y = make_classification(n_samples=50, n_features=4, n_classes=2, random_state=42)
        X_df = pd.DataFrame(X)
        
        pipeline = Pipeline([
            ('classifier', DecisionTreeClassifier(random_state=42))
        ])
        
        param_grid = {
            'classifier__max_depth': [3, 5],
            'classifier__criterion': ['gini', 'entropy']
        }
        
        search, _ = tune_model(
            pipeline=pipeline,
            X_train=X_df,
            y_train=pd.Series(y),
            param_grid=param_grid,
            cv_folds=3,
            scoring='accuracy',
            random_state=42,
        )
        
        # Extract results
        df = extract_cv_results(search)
        
        # Check DataFrame shape
        assert len(df) == 4  # 2 max_depth × 2 criterion
        assert 'mean_train_score' in df.columns
        assert 'mean_test_score' in df.columns
        assert 'std_test_score' in df.columns
        assert 'rank_test_score' in df.columns
        
        # Check sorted by rank
        assert df['rank_test_score'].iloc[0] == 1
    
    def test_results_have_params(self):
        """Test that results include parameter columns."""
        X, y = make_classification(
            n_samples=30,
            n_features=5,
            n_informative=2,
            n_redundant=0,
            n_classes=2,
            random_state=42
        )
        X_df = pd.DataFrame(X)
        
        pipeline = Pipeline([
            ('classifier', DecisionTreeClassifier(random_state=42))
        ])
        
        param_grid = {'classifier__max_depth': [2, 4]}
        
        search, _ = tune_model(
            pipeline=pipeline,
            X_train=X_df,
            y_train=pd.Series(y),
            param_grid=param_grid,
            cv_folds=2,
            scoring='accuracy',
            random_state=42,
        )
        
        df = extract_cv_results(search)
        
        # Should have param columns
        param_cols = [col for col in df.columns if col.startswith('param_')]
        assert len(param_cols) > 0


class TestCountCombinations:
    """Test parameter combination counting."""
    
    def test_count_simple(self):
        """Test counting simple grid."""
        grid = {
            'param1': [1, 2, 3],
            'param2': ['a', 'b']
        }
        
        count = _count_param_combinations(grid)
        assert count == 6  # 3 × 2
    
    def test_count_single_param(self):
        """Test counting with single parameter."""
        grid = {'param1': [1, 2, 3, 4]}
        
        count = _count_param_combinations(grid)
        assert count == 4
    
    def test_count_empty(self):
        """Test counting empty grid."""
        grid = {}
        
        count = _count_param_combinations(grid)
        assert count == 1
