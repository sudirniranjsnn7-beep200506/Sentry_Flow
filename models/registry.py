"""
Model Registry Module

File-based model registry with integrity checks per TRD §20.
No database. Supports registering, listing, loading, and setting active models.

Registry Structure:
artifacts/registry/
├── registry.json                 # index: entries[], active_model_id
└── <model_id>/                   # e.g. decision_tree_20261014_011743
    ├── pipeline.joblib           # full fitted pipeline (+ label encoder)
    ├── metadata.json
    ├── feature_schema.json       # copy of canonical schema used
    ├── label_mapping.json        # copy + sha256
    ├── metrics.json              # test + CV metrics (from artifacts only)
    └── env.json                  # python, sklearn, xgboost, pandas versions
"""

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import joblib
import pandas as pd
import yaml

from common.config import load_config
from common.errors import ModelNotFoundError, RegistryIntegrityError
from common.paths import ProjectPaths

logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hexadecimal SHA-256 digest
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_registry_index(registry_dir: Path) -> Dict:
    """
    Load the registry index file.
    
    Args:
        registry_dir: Path to artifacts/registry/
        
    Returns:
        Dictionary with entries and active_model_id
    """
    index_path = registry_dir / "registry.json"
    
    if not index_path.exists():
        logger.info("Registry index does not exist, creating new")
        return {"entries": [], "active_model_id": None}
    
    with open(index_path, 'r') as f:
        return json.load(f)


def save_registry_index(registry_dir: Path, index: Dict):
    """
    Save the registry index file.
    
    Args:
        registry_dir: Path to artifacts/registry/
        index: Registry index dictionary
    """
    registry_dir.mkdir(parents=True, exist_ok=True)
    index_path = registry_dir / "registry.json"
    
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)
    
    logger.info(f"Registry index saved to {index_path}")


def register_model(
    run_id: str,
    model_name: str,
    intended_use: str = "Network traffic classification from flow-level features",
    limitations: Optional[str] = None
):
    """
    Register a trained model in the registry.
    
    Copies artifacts from runs/ and reports/ into registry/ with integrity
    checks. Per TRD §20.
    
    Args:
        run_id: Run ID from artifacts/runs/ (e.g., decision_tree_20261014_011743)
        model_name: Human-readable model name
        intended_use: Description of intended use
        limitations: Known limitations text
        
    Raises:
        ModelNotFoundError: If run artifacts not found
        RegistryIntegrityError: If required files missing
    """
    config = load_config()
    paths = ProjectPaths(config)
    
    run_dir = paths.runs_dir / run_id
    report_dir = paths.reports_dir / run_id
    
    if not run_dir.exists():
        raise ModelNotFoundError(f"Run directory not found: {run_dir}")
    
    if not report_dir.exists():
        raise ModelNotFoundError(f"Report directory not found: {report_dir}")
    
    logger.info(f"Registering model: {run_id}")
    
    # Check required files
    pipeline_path = run_dir / "pipeline.joblib"
    if not pipeline_path.exists():
        raise RegistryIntegrityError(f"Pipeline file missing: {pipeline_path}")
    
    # Create registry entry directory
    registry_dir = paths.registry_dir
    model_dir = registry_dir / run_id
    model_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Created registry directory: {model_dir}")
    
    # Copy pipeline with integrity check
    dest_pipeline = model_dir / "pipeline.joblib"
    shutil.copy2(pipeline_path, dest_pipeline)
    pipeline_sha256 = compute_sha256(dest_pipeline)
    logger.info(f"Pipeline SHA-256: {pipeline_sha256}")
    
    # Load run info
    train_info_path = run_dir / "train_info.json"
    with open(train_info_path, 'r') as f:
        train_info = json.load(f)
    
    # Load CV metrics
    cv_metrics_path = run_dir / "metrics_cv.json"
    with open(cv_metrics_path, 'r') as f:
        cv_metrics = json.load(f)
    
    # Load test metrics if available
    test_metrics = {}
    test_metrics_path = report_dir / "metrics.json"
    if test_metrics_path.exists():
        with open(test_metrics_path, 'r') as f:
            test_metrics = json.load(f)
    
    # Load timing if available
    timing = {}
    timing_path = report_dir / "timing.json"
    if timing_path.exists():
        with open(timing_path, 'r') as f:
            timing = json.load(f)
    
    # Load selected features
    features_path = run_dir / "selected_features.json"
    with open(features_path, 'r') as f:
        selected_features = json.load(f)
    
    # Extract feature list (may be under 'features' key or 'selected_features')
    feature_list = selected_features.get("features") or selected_features.get("selected_features", [])
    
    # Load label mapping hash
    mapping_hash_path = run_dir / "label_mapping.sha256"
    with open(mapping_hash_path, 'r') as f:
        label_mapping_hash = f.read().strip()
    
    # Copy feature schema
    schema_src = Path("config/feature_schema.yaml")
    schema_dest = model_dir / "feature_schema.json"
    with open(schema_src, 'r') as f:
        schema = yaml.safe_load(f)
    with open(schema_dest, 'w') as f:
        json.dump(schema, f, indent=2)
    
    # Copy label mapping
    mapping_src = Path("config/label_mapping.yaml")
    mapping_dest = model_dir / "label_mapping.json"
    with open(mapping_src, 'r') as f:
        label_mapping = yaml.safe_load(f)
    with open(mapping_dest, 'w') as f:
        json.dump(label_mapping, f, indent=2)
    
    # Build metadata
    metadata = {
        "model_id": run_id,
        "model_name": model_name,
        "run_id": run_id,
        "created_at": datetime.now().isoformat(),
        "registered_at": datetime.now().isoformat(),
        "seed": train_info.get("seed"),
        "label_mapping_hash": label_mapping_hash,
        "selected_features": feature_list,
        "n_features": len(feature_list),
        "class_names": train_info.get("class_names", []),
        "n_classes": train_info.get("n_classes"),
        "train_samples": train_info.get("train_samples"),
        "cv_folds": train_info.get("cv_folds"),
        "pipeline_sha256": pipeline_sha256,
        "selection_criterion": "cv_macro_f1",
        "intended_use": intended_use,
        "limitations": limitations or "Results specific to ISCX-VPN2016 dataset. "
                                       "Generalization requires validation on live traffic."
    }
    
    # Save metadata
    metadata_path = model_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Save metrics (combined CV + test)
    metrics = {
        "cv": cv_metrics,
        "test": test_metrics,
        "timing": timing
    }
    metrics_path = model_dir / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Save environment info
    env_info = {
        "python_version": train_info.get("python_version"),
        "sklearn_version": train_info.get("sklearn_version"),
        "xgboost_version": train_info.get("xgboost_version"),
        "pandas_version": pd.__version__,
        "platform": train_info.get("platform"),
        "timestamp": train_info.get("timestamp")
    }
    env_path = model_dir / "env.json"
    with open(env_path, 'w') as f:
        json.dump(env_info, f, indent=2)
    
    # Update registry index
    index = load_registry_index(registry_dir)
    
    # Check if already registered
    existing = [e for e in index["entries"] if e["model_id"] == run_id]
    if existing:
        logger.warning(f"Model {run_id} already registered, updating entry")
        index["entries"] = [e for e in index["entries"] if e["model_id"] != run_id]
    
    # Add new entry
    entry = {
        "model_id": run_id,
        "model_name": model_name,
        "registered_at": metadata["registered_at"],
        "cv_macro_f1": cv_metrics.get("best_score"),
        "test_accuracy": test_metrics.get("accuracy"),
        "test_macro_f1": test_metrics.get("macro", {}).get("f1"),
        "n_features": metadata["n_features"],
        "n_classes": metadata["n_classes"]
    }
    index["entries"].append(entry)
    
    # Set as active if it's the first model or if no active model set
    if index["active_model_id"] is None or len(index["entries"]) == 1:
        index["active_model_id"] = run_id
        logger.info(f"Set {run_id} as active model")
    
    save_registry_index(registry_dir, index)
    
    logger.info(f"Model {run_id} registered successfully")
    logger.info(f"Registry directory: {model_dir}")
    
    return model_dir


def list_models() -> List[Dict]:
    """
    List all registered models.
    
    Returns:
        List of model entries from registry index
    """
    config = load_config()
    paths = ProjectPaths(config)
    
    index = load_registry_index(paths.registry_dir)
    return index.get("entries", [])


def get_active_model_id() -> Optional[str]:
    """
    Get the currently active model ID.
    
    Returns:
        Active model ID, or None if no active model
    """
    config = load_config()
    paths = ProjectPaths(config)
    
    index = load_registry_index(paths.registry_dir)
    return index.get("active_model_id")


def set_active_model(model_id: str):
    """
    Set a model as the active model.
    
    Args:
        model_id: Model ID to set as active
        
    Raises:
        ModelNotFoundError: If model not in registry
    """
    config = load_config()
    paths = ProjectPaths(config)
    
    index = load_registry_index(paths.registry_dir)
    
    # Verify model exists
    model_ids = [e["model_id"] for e in index["entries"]]
    if model_id not in model_ids:
        raise ModelNotFoundError(
            f"Model {model_id} not found in registry. "
            f"Available: {model_ids}"
        )
    
    index["active_model_id"] = model_id
    save_registry_index(paths.registry_dir, index)
    
    logger.info(f"Set {model_id} as active model")


def load_model(model_id: Optional[str] = None, verify_checksum: bool = True) -> tuple:
    """
    Load a model from the registry.
    
    Args:
        model_id: Model ID to load, or None to load active model
        verify_checksum: If True, verify pipeline SHA-256
        
    Returns:
        Tuple of (pipeline, metadata, feature_schema, label_encoder)
        
    Raises:
        ModelNotFoundError: If model not found
        RegistryIntegrityError: If checksum verification fails
    """
    config = load_config()
    paths = ProjectPaths(config)
    
    # Resolve model ID
    if model_id is None:
        model_id = get_active_model_id()
        if model_id is None:
            raise ModelNotFoundError("No active model set in registry")
        logger.info(f"Loading active model: {model_id}")
    else:
        logger.info(f"Loading model: {model_id}")
    
    model_dir = paths.registry_dir / model_id
    
    if not model_dir.exists():
        raise ModelNotFoundError(f"Model directory not found: {model_dir}")
    
    # Load metadata
    metadata_path = model_dir / "metadata.json"
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Verify pipeline integrity
    pipeline_path = model_dir / "pipeline.joblib"
    
    if verify_checksum:
        current_sha256 = compute_sha256(pipeline_path)
        expected_sha256 = metadata.get("pipeline_sha256")
        
        if current_sha256 != expected_sha256:
            raise RegistryIntegrityError(
                f"Pipeline checksum mismatch for {model_id}. "
                f"Expected: {expected_sha256}, Got: {current_sha256}. "
                f"Pipeline file may have been modified or corrupted."
            )
        logger.debug(f"Pipeline checksum verified: {current_sha256}")
    
    # Load pipeline
    try:
        pipeline = joblib.load(pipeline_path)
        logger.info(f"Pipeline loaded from {pipeline_path}")
    except Exception as e:
        raise RegistryIntegrityError(
            f"Failed to load pipeline for {model_id}: {e}"
        )
    
    # Load feature schema
    schema_path = model_dir / "feature_schema.json"
    with open(schema_path, 'r') as f:
        feature_schema = json.load(f)
    
    # Load label encoder if exists
    label_encoder_path = model_dir.parent.parent / "runs" / model_id / "label_encoder.joblib"
    label_encoder = None
    if label_encoder_path.exists():
        try:
            label_encoder = joblib.load(label_encoder_path)
            logger.info("Label encoder loaded")
        except Exception as e:
            logger.warning(f"Failed to load label encoder: {e}")
    
    # Check library versions
    env_path = model_dir / "env.json"
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_info = json.load(f)
        
        import sklearn
        current_sklearn = sklearn.__version__
        trained_sklearn = env_info.get("sklearn_version")
        
        if current_sklearn != trained_sklearn:
            logger.warning(
                f"Library version mismatch: Model trained with scikit-learn {trained_sklearn}, "
                f"but current version is {current_sklearn}. "
                f"Predictions may differ."
            )
    
    return pipeline, metadata, feature_schema, label_encoder


def main():
    """CLI for registry operations."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Model registry operations"
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register a model')
    register_parser.add_argument('--run-id', required=True, help='Run ID from artifacts/runs/')
    register_parser.add_argument('--model-name', required=True, help='Human-readable model name')
    register_parser.add_argument('--intended-use', default="Network traffic classification from flow-level features")
    register_parser.add_argument('--limitations', help='Known limitations text')
    
    # List command
    subparsers.add_parser('list', help='List registered models')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show active model')
    
    # Set-active command
    set_parser = subparsers.add_parser('set-active', help='Set active model')
    set_parser.add_argument('--model-id', required=True, help='Model ID to set as active')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify model integrity')
    verify_parser.add_argument('--model-id', help='Model ID to verify (default: active)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.command == 'register':
        model_dir = register_model(
            run_id=args.run_id,
            model_name=args.model_name,
            intended_use=args.intended_use,
            limitations=args.limitations
        )
        print(f"\n✅ Model registered successfully")
        print(f"Model ID: {args.run_id}")
        print(f"Registry directory: {model_dir}")
        
    elif args.command == 'list':
        models = list_models()
        active_id = get_active_model_id()
        
        print("\n" + "="*70)
        print("REGISTERED MODELS")
        print("="*70)
        
        if not models:
            print("\nNo models registered yet.")
        else:
            for model in models:
                is_active = " [ACTIVE]" if model["model_id"] == active_id else ""
                print(f"\nModel: {model['model_name']}{is_active}")
                print(f"  ID: {model['model_id']}")
                print(f"  Registered: {model['registered_at']}")
                if model.get('cv_macro_f1'):
                    print(f"  CV Macro F1: {model['cv_macro_f1']:.4f}")
                if model.get('test_macro_f1'):
                    print(f"  Test Macro F1: {model['test_macro_f1']:.4f}")
                if model.get('test_accuracy'):
                    print(f"  Test Accuracy: {model['test_accuracy']:.4f}")
                print(f"  Features: {model.get('n_features')}")
                print(f"  Classes: {model.get('n_classes')}")
        print()
        
    elif args.command == 'show':
        active_id = get_active_model_id()
        
        if active_id is None:
            print("\n⚠️ No active model set")
        else:
            print(f"\n✅ Active model: {active_id}")
            
            # Load and show details
            try:
                _, metadata, _, _ = load_model(active_id, verify_checksum=False)
                print(f"\nModel Name: {metadata['model_name']}")
                print(f"Features: {metadata['n_features']}")
                print(f"Classes: {metadata['n_classes']}")
                print(f"Class Names: {', '.join(metadata['class_names'])}")
                print(f"Intended Use: {metadata['intended_use']}")
            except Exception as e:
                print(f"⚠️ Could not load model details: {e}")
        print()
        
    elif args.command == 'set-active':
        set_active_model(args.model_id)
        print(f"\n✅ Set {args.model_id} as active model\n")
        
    elif args.command == 'verify':
        model_id = args.model_id
        
        try:
            pipeline, metadata, schema, encoder = load_model(model_id, verify_checksum=True)
            print(f"\n✅ Model integrity verified: {metadata['model_id']}")
            print(f"SHA-256: {metadata['pipeline_sha256']}")
            print(f"Features: {metadata['n_features']}")
            print(f"Classes: {metadata['n_classes']}")
            print()
        except Exception as e:
            print(f"\n❌ Verification failed: {e}\n")
            exit(1)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
