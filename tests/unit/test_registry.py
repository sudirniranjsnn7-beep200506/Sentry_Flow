"""
Unit tests for model registry module.
"""

import json
import pytest
import joblib
from pathlib import Path
from models.registry import (
    compute_sha256,
    load_registry_index,
    save_registry_index,
    register_model,
    list_models,
    get_active_model_id,
    set_active_model,
    load_model
)
from common.errors import ModelNotFoundError, RegistryIntegrityError


def test_compute_sha256(tmp_path):
    """Test SHA-256 checksum computation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_sha256(test_file)
    
    # Known SHA-256 of "Hello, World!"
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert checksum == expected


def test_load_registry_index_nonexistent(tmp_path):
    """Test loading registry index when it doesn't exist."""
    registry_dir = tmp_path / "registry"
    
    index = load_registry_index(registry_dir)
    
    assert index == {"entries": [], "active_model_id": None}


def test_load_registry_index_existing(tmp_path):
    """Test loading existing registry index."""
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    
    index_data = {
        "entries": [{"model_id": "test_model", "model_name": "Test"}],
        "active_model_id": "test_model"
    }
    
    with open(registry_dir / "registry.json", 'w') as f:
        json.dump(index_data, f)
    
    index = load_registry_index(registry_dir)
    
    assert index == index_data


def test_save_registry_index(tmp_path):
    """Test saving registry index."""
    registry_dir = tmp_path / "registry"
    
    index_data = {
        "entries": [{"model_id": "test_model"}],
        "active_model_id": "test_model"
    }
    
    save_registry_index(registry_dir, index_data)
    
    assert (registry_dir / "registry.json").exists()
    
    with open(registry_dir / "registry.json", 'r') as f:
        loaded = json.load(f)
    
    assert loaded == index_data


def test_list_models_empty(tmp_path, monkeypatch):
    """Test listing models when registry is empty."""
    from common.paths import ProjectPaths
    
    # Mock ProjectPaths to use tmp_path
    class MockPaths:
        def __init__(self, config):
            self.registry_dir = tmp_path / "registry"
    
    monkeypatch.setattr("models.registry.ProjectPaths", MockPaths)
    
    models = list_models()
    
    assert models == []


def test_get_active_model_id_none(tmp_path, monkeypatch):
    """Test getting active model ID when none is set."""
    from common.paths import ProjectPaths
    
    class MockPaths:
        def __init__(self, config):
            self.registry_dir = tmp_path / "registry"
    
    monkeypatch.setattr("models.registry.ProjectPaths", MockPaths)
    
    active_id = get_active_model_id()
    
    assert active_id is None


def test_set_active_model_not_found(tmp_path, monkeypatch):
    """Test setting active model that doesn't exist."""
    from common.paths import ProjectPaths
    
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    
    # Create empty registry
    index = {"entries": [], "active_model_id": None}
    with open(registry_dir / "registry.json", 'w') as f:
        json.dump(index, f)
    
    class MockPaths:
        def __init__(self, config):
            self.registry_dir = registry_dir
    
    monkeypatch.setattr("models.registry.ProjectPaths", MockPaths)
    
    with pytest.raises(ModelNotFoundError):
        set_active_model("nonexistent_model")


def test_load_model_not_found(tmp_path, monkeypatch):
    """Test loading model that doesn't exist."""
    from common.paths import ProjectPaths
    
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    
    class MockPaths:
        def __init__(self, config):
            self.registry_dir = registry_dir
    
    monkeypatch.setattr("models.registry.ProjectPaths", MockPaths)
    
    with pytest.raises(ModelNotFoundError):
        load_model("nonexistent_model")


def test_load_model_no_active(tmp_path, monkeypatch):
    """Test loading model when no active model is set."""
    from common.paths import ProjectPaths
    
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    
    # Create registry with no active model
    index = {"entries": [], "active_model_id": None}
    with open(registry_dir / "registry.json", 'w') as f:
        json.dump(index, f)
    
    class MockPaths:
        def __init__(self, config):
            self.registry_dir = registry_dir
    
    monkeypatch.setattr("models.registry.ProjectPaths", MockPaths)
    
    with pytest.raises(ModelNotFoundError, match="No active model"):
        load_model()


def test_checksum_mismatch_detection(tmp_path, monkeypatch):
    """Test that checksum mismatch is detected."""
    from common.paths import ProjectPaths
    
    registry_dir = tmp_path / "registry"
    model_dir = registry_dir / "test_model"
    model_dir.mkdir(parents=True)
    
    # Create fake pipeline
    pipeline_path = model_dir / "pipeline.joblib"
    pipeline_path.write_text("fake pipeline")
    
    # Create metadata with wrong checksum
    metadata = {
        "model_id": "test_model",
        "pipeline_sha256": "wrong_checksum_000000000000000000000000000000000000000000000000000000000000"
    }
    
    with open(model_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f)
    
    # Create minimal schema
    with open(model_dir / "feature_schema.json", 'w') as f:
        json.dump({"features": []}, f)
    
    class MockPaths:
        def __init__(self, config):
            self.registry_dir = registry_dir
    
    monkeypatch.setattr("models.registry.ProjectPaths", MockPaths)
    
    with pytest.raises(RegistryIntegrityError, match="checksum mismatch"):
        load_model("test_model", verify_checksum=True)


def test_checksum_verification_can_be_skipped(tmp_path, monkeypatch):
    """Test that checksum verification can be disabled."""
    from common.paths import ProjectPaths
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.pipeline import Pipeline
    
    registry_dir = tmp_path / "registry"
    model_dir = registry_dir / "test_model"
    model_dir.mkdir(parents=True)
    
    # Create real pipeline
    pipeline = Pipeline([('clf', DecisionTreeClassifier())])
    pipeline_path = model_dir / "pipeline.joblib"
    joblib.dump(pipeline, pipeline_path)
    
    # Create metadata with wrong checksum
    metadata = {
        "model_id": "test_model",
        "pipeline_sha256": "intentionally_wrong",
        "selected_features": ["feature1", "feature2"],
        "class_names": ["A", "B"]
    }
    
    with open(model_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f)
    
    # Create minimal schema
    with open(model_dir / "feature_schema.json", 'w') as f:
        json.dump({"features": []}, f)
    
    class MockPaths:
        def __init__(self, config):
            self.registry_dir = registry_dir
    
    monkeypatch.setattr("models.registry.ProjectPaths", MockPaths)
    
    # Should not raise with verify_checksum=False
    loaded_pipeline, loaded_metadata, schema, encoder = load_model("test_model", verify_checksum=False)
    
    assert loaded_pipeline is not None
    assert loaded_metadata["model_id"] == "test_model"


def test_round_trip_predictions(tmp_path, monkeypatch):
    """Test that registered model produces consistent predictions."""
    from common.paths import ProjectPaths
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    import numpy as np
    
    registry_dir = tmp_path / "registry"
    model_dir = registry_dir / "test_model"
    model_dir.mkdir(parents=True)
    
    # Create and fit a pipeline
    np.random.seed(42)
    X_train = np.random.rand(100, 3)
    y_train = np.random.randint(0, 2, 100)
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', DecisionTreeClassifier(random_state=42, max_depth=3))
    ])
    pipeline.fit(X_train, y_train)
    
    # Get predictions before saving
    X_test = np.random.rand(10, 3)
    predictions_before = pipeline.predict(X_test)
    
    # Save pipeline
    pipeline_path = model_dir / "pipeline.joblib"
    joblib.dump(pipeline, pipeline_path)
    
    # Create metadata
    metadata = {
        "model_id": "test_model",
        "pipeline_sha256": compute_sha256(pipeline_path),
        "selected_features": ["f1", "f2", "f3"],
        "class_names": ["A", "B"]
    }
    
    with open(model_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f)
    
    # Create schema
    with open(model_dir / "feature_schema.json", 'w') as f:
        json.dump({"features": ["f1", "f2", "f3"]}, f)
    
    class MockPaths:
        def __init__(self, config):
            self.registry_dir = registry_dir
    
    monkeypatch.setattr("models.registry.ProjectPaths", MockPaths)
    
    # Load and predict
    loaded_pipeline, _, _, _ = load_model("test_model", verify_checksum=True)
    predictions_after = loaded_pipeline.predict(X_test)
    
    # Predictions should be identical
    np.testing.assert_array_equal(predictions_before, predictions_after)


def test_register_model_missing_run(tmp_path, monkeypatch):
    """Test registering model with missing run directory."""
    from common.paths import ProjectPaths
    
    class MockPaths:
        def __init__(self, config):
            self.runs_dir = tmp_path / "runs"
            self.reports_dir = tmp_path / "reports"
            self.registry_dir = tmp_path / "registry"
    
    monkeypatch.setattr("models.registry.ProjectPaths", MockPaths)
    
    with pytest.raises(ModelNotFoundError, match="Run directory not found"):
        register_model("nonexistent_run", "Test Model")
