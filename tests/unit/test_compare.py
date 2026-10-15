"""
Unit tests for model comparison module.
"""

import json
import pytest
import pandas as pd
from pathlib import Path
from evaluation.compare import (
    load_model_artifacts,
    build_comparison_table,
    find_evaluated_models
)


@pytest.fixture
def mock_report_dir(tmp_path):
    """Create mock evaluation report directory."""
    report_dir = tmp_path / "test_run_001"
    report_dir.mkdir()
    
    # Create summary.json
    summary = {
        "run_id": "test_run_001",
        "model_name": "test_model",
        "evaluated_at": "2026-10-14T00:00:00",
        "metrics": {
            "accuracy": 0.95,
            "per_class": {
                "Class A": {"precision": 0.94, "recall": 0.96, "f1": 0.95, "support": 100},
                "Class B": {"precision": 0.96, "recall": 0.94, "f1": 0.95, "support": 100}
            },
            "macro": {"precision": 0.95, "recall": 0.95, "f1": 0.95},
            "weighted": {"precision": 0.95, "recall": 0.95, "f1": 0.95},
            "confusion_matrix": [[96, 4], [6, 94]],
            "class_names": ["Class A", "Class B"],
            "n_samples": 200
        },
        "timing": {
            "mean_time_per_flow_ms": 0.01,
            "total_time_s": 0.002,
            "n_flows": 200,
            "n_runs": 3
        },
        "train_time_seconds": 10.5,
        "train_samples": 800,
        "test_samples": 200
    }
    
    with open(report_dir / "summary.json", 'w') as f:
        json.dump(summary, f)
    
    return report_dir


def test_load_model_artifacts_success(mock_report_dir):
    """Test loading artifacts from valid report directory."""
    data = load_model_artifacts(mock_report_dir)
    
    assert data is not None
    assert data['run_id'] == 'test_run_001'
    assert data['model_name'] == 'test_model'
    assert data['metrics']['accuracy'] == 0.95
    assert data['timing']['mean_time_per_flow_ms'] == 0.01


def test_load_model_artifacts_missing_dir(tmp_path):
    """Test handling of missing report directory."""
    nonexistent = tmp_path / "nonexistent"
    data = load_model_artifacts(nonexistent)
    
    assert data is None


def test_load_model_artifacts_missing_summary(tmp_path):
    """Test handling of missing summary.json."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    data = load_model_artifacts(empty_dir)
    
    assert data is None


def test_build_comparison_table_single_model(mock_report_dir):
    """Test building comparison table with one model."""
    data = load_model_artifacts(mock_report_dir)
    model_data = {"test_run_001": data}
    
    df = build_comparison_table(model_data)
    
    assert len(df) == 1
    assert df.iloc[0]['model_name'] == 'test_model'
    assert df.iloc[0]['test_accuracy'] == 0.95
    assert df.iloc[0]['test_macro_f1'] == 0.95
    assert df.iloc[0]['inference_time_ms'] == 0.01
    assert 'f1_class_a' in df.columns
    assert 'f1_class_b' in df.columns


def test_build_comparison_table_empty():
    """Test building comparison table with no valid data."""
    model_data = {"test_run": None}
    
    df = build_comparison_table(model_data)
    
    assert len(df) == 0


def test_find_evaluated_models(mock_report_dir):
    """Test finding evaluated models in reports directory."""
    reports_dir = mock_report_dir.parent
    
    run_ids = find_evaluated_models(reports_dir)
    
    assert len(run_ids) == 1
    assert "test_run_001" in run_ids


def test_find_evaluated_models_empty(tmp_path):
    """Test finding models in empty directory."""
    empty_dir = tmp_path / "empty_reports"
    empty_dir.mkdir()
    
    run_ids = find_evaluated_models(empty_dir)
    
    assert len(run_ids) == 0


def test_find_evaluated_models_nonexistent(tmp_path):
    """Test finding models in nonexistent directory."""
    nonexistent = tmp_path / "nonexistent"
    
    run_ids = find_evaluated_models(nonexistent)
    
    assert len(run_ids) == 0


def test_comparison_table_columns():
    """Test that comparison table has all expected columns."""
    # Mock data with all fields
    model_data = {
        "run1": {
            "run_id": "run1",
            "model_name": "model1",
            "cv_score": 0.94,
            "metrics": {
                "accuracy": 0.95,
                "per_class": {
                    "ClassA": {"precision": 0.95, "recall": 0.95, "f1": 0.95, "support": 50}
                },
                "macro": {"precision": 0.95, "recall": 0.95, "f1": 0.95},
                "weighted": {"precision": 0.95, "recall": 0.95, "f1": 0.95}
            },
            "timing": {"mean_time_per_flow_ms": 0.01},
            "train_time_seconds": 100.0,
            "model_size_mb": 5.0,
            "train_samples": 1000,
            "test_samples": 200
        }
    }
    
    df = build_comparison_table(model_data)
    
    expected_cols = [
        'run_id', 'model_name', 'cv_macro_f1', 'test_accuracy',
        'test_macro_f1', 'inference_time_ms', 'train_time_s',
        'model_size_mb', 'train_samples', 'test_samples'
    ]
    
    for col in expected_cols:
        assert col in df.columns


def test_comparison_table_sorted_by_cv_f1():
    """Test that comparison table is sorted by CV macro F1."""
    model_data = {
        "run1": {
            "run_id": "run1",
            "model_name": "model1",
            "cv_score": 0.90,
            "metrics": {"accuracy": 0.91, "macro": {"f1": 0.90}, "weighted": {"f1": 0.90}},
            "timing": {"mean_time_per_flow_ms": 0.01},
            "train_time_seconds": 100.0,
            "train_samples": 1000,
            "test_samples": 200
        },
        "run2": {
            "run_id": "run2",
            "model_name": "model2",
            "cv_score": 0.95,
            "metrics": {"accuracy": 0.96, "macro": {"f1": 0.95}, "weighted": {"f1": 0.95}},
            "timing": {"mean_time_per_flow_ms": 0.01},
            "train_time_seconds": 100.0,
            "train_samples": 1000,
            "test_samples": 200
        }
    }
    
    df = build_comparison_table(model_data)
    
    # Should be sorted descending by cv_macro_f1
    assert df.iloc[0]['model_name'] == 'model2'
    assert df.iloc[1]['model_name'] == 'model1'
    assert df.iloc[0]['cv_macro_f1'] > df.iloc[1]['cv_macro_f1']
