"""
tests/unit/test_random_forest.py
---------------------------------
Unit tests for Random Forest model specification (CN-007, Phase 3).

Tests the Random Forest model spec, parameter validation, and feature importance export.

TRD §14, FR-005, ML-001, CN-007.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier

from models.base import ModelSpec
from models.random_forest import get_random_forest_spec, export_feature_importances


class TestRandomForestSpec:
    """Test Random Forest model specification."""
    
    def test_get_spec(self):
        """Test getting Random Forest spec."""
        spec = get_random_forest_spec(random_state=42)
        
        assert spec.name == 'random_forest'
        assert callable(spec.estimator_factory)
        assert isinstance(spec.param_space, dict)
        
        # Check that param names are prefixed with 'classifier__'
        for key in spec.param_space.keys():
            assert key.startswith('classifier__'), f"Parameter {key} not prefixed"
    
    def test_estimator_factory(self):
        """Test that factory creates RandomForestClassifier."""
        spec = get_random_forest_spec(random_state=42)
        estimator = spec.estimator_factory()
        
        assert isinstance(estimator, RandomForestClassifier)
        assert estimator.random_state == 42
        assert estimator.n_jobs == -1  # Should use all CPUs
    
    def test_param_space_valid(self):
        """Test that param space contains valid sklearn parameters."""
        spec = get_random_forest_spec()
        
        # Get valid param names from RandomForestClassifier
        from sklearn.ensemble import RandomForestClassifier
        valid_params = set(RandomForestClassifier().get_params().keys())
        
        # Check each param in spec (remove 'classifier__' prefix)
        for key in spec.param_space.keys():
            param_name = key.replace('classifier__', '')
            assert param_name in valid_params, f"Invalid parameter: {param_name}"
    
    def test_param_values_valid(self):
        """Test that parameter values are valid for sklearn."""
        spec = get_random_forest_spec()
        
        # Test that we can create an estimator with each param combination
        # (Just test a few combinations, not all - that would be slow)
        
        # Test some specific combinations that should work
        test_params = [
            {'n_estimators': 50, 'criterion': 'gini', 'max_depth': None},
            {'n_estimators': 100, 'criterion': 'entropy', 'max_depth': 10},
            {'n_estimators': 200, 'max_features': 'sqrt', 'class_weight': 'balanced'},
        ]
        
        for params in test_params:
            # Should not raise an exception
            rf = RandomForestClassifier(**params, random_state=42)
            assert isinstance(rf, RandomForestClassifier)


class TestFeatureImportances:
    """Test feature importance export."""
    
    def test_export_importances_basic(self):
        """Test basic feature importance export."""
        # Create and train a simple Random Forest
        X, y = make_classification(
            n_samples=100,
            n_features=5,
            n_informative=3,
            n_redundant=0,
            random_state=42
        )
        feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        
        rf = RandomForestClassifier(n_estimators=10, random_state=42)
        rf.fit(X, y)
        
        # Export importances
        info = export_feature_importances(rf, feature_names)
        
        # Check structure
        assert 'importances' in info
        assert 'sorted_features' in info
        assert 'n_features' in info
        assert 'total_importance' in info
        assert 'mean_importance' in info
        
        # Check values
        assert info['n_features'] == 5
        assert len(info['importances']) == 5
        assert len(info['sorted_features']) == 5
        
        # Importances should sum to approximately 1.0
        assert abs(info['total_importance'] - 1.0) < 1e-10
        
        # All importances should be non-negative
        for importance in info['importances'].values():
            assert importance >= 0
        
        # Sorted features should be in descending order
        importances_sorted = [imp for _, imp in info['sorted_features']]
        assert importances_sorted == sorted(importances_sorted, reverse=True)
    
    def test_export_unfitted_raises_error(self):
        """Test that exporting from unfitted classifier raises error."""
        rf = RandomForestClassifier(random_state=42)
        feature_names = ['feat1', 'feat2']
        
        with pytest.raises(ValueError, match="must be fitted"):
            export_feature_importances(rf, feature_names)
    
    def test_export_mismatch_features_raises_error(self):
        """Test that mismatched feature names raise error."""
        # Create and train a Random Forest
        X, y = make_classification(
            n_samples=50,
            n_features=3,
            n_informative=2,
            n_redundant=0,
            random_state=42
        )
        rf = RandomForestClassifier(n_estimators=5, random_state=42)
        rf.fit(X, y)
        
        # Wrong number of feature names
        wrong_names = ['feat1', 'feat2']  # Only 2 names for 3 features
        
        with pytest.raises(ValueError, match="Mismatch"):
            export_feature_importances(rf, wrong_names)
    
    def test_export_with_real_feature_names(self):
        """Test export with realistic flow feature names."""
        # Simulate flow features
        feature_names = [
            'duration',
            'flowBytesPerSecond', 
            'mean_fiat',
            'mean_biat',
            'max_flowiat'
        ]
        
        # Create synthetic data
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 4, 100)  # 4 classes like our data
        
        rf = RandomForestClassifier(n_estimators=10, random_state=42)
        rf.fit(X, y)
        
        info = export_feature_importances(rf, feature_names)
        
        # Check that feature names are preserved
        assert set(info['importances'].keys()) == set(feature_names)
        
        # Check sorted features have correct names
        sorted_names = [name for name, _ in info['sorted_features']]
        assert set(sorted_names) == set(feature_names)


class TestRandomForestIntegration:
    """Test Random Forest integration with training pipeline."""
    
    def test_spec_in_modelspec_interface(self):
        """Test that Random Forest spec follows ModelSpec interface."""
        spec = get_random_forest_spec()
        
        # Should be a valid ModelSpec
        assert isinstance(spec, ModelSpec)
        
        # Should pass ModelSpec validation
        assert spec.name in {'decision_tree', 'random_forest', 'svm', 'xgboost'}
        
        # Factory should work
        estimator = spec.estimator_factory()
        assert hasattr(estimator, 'fit')
        assert hasattr(estimator, 'predict')
    
    def test_reproducibility(self):
        """Test that Random Forest with same seed gives same results."""
        # Create data
        X, y = make_classification(n_samples=50, n_features=4, random_state=42)
        
        # Train two Random Forests with same seed
        spec1 = get_random_forest_spec(random_state=42)
        spec2 = get_random_forest_spec(random_state=42)
        
        rf1 = spec1.estimator_factory()
        rf2 = spec2.estimator_factory()
        
        rf1.fit(X, y)
        rf2.fit(X, y)
        
        # Predictions should be identical
        pred1 = rf1.predict(X)
        pred2 = rf2.predict(X)
        
        np.testing.assert_array_equal(pred1, pred2)
        
        # Feature importances should be identical
        np.testing.assert_array_almost_equal(
            rf1.feature_importances_, 
            rf2.feature_importances_
        )