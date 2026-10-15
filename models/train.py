"""
models/train.py
---------------
Model training orchestrator for FlowSentry (CN-006, Phase 3).

CLI interface for training and tuning models with full artifact saving.

Usage:
    python -m models.train --model decision_tree
    python -m models.train --model random_forest
    python -m models.train --model svm
    python -m models.train --model xgboost

Responsibilities:
- Load training data and preprocessing pipeline
- Build full pipeline (imputer → scaler → selector → model)
- Perform stratified K-fold cross-validation
- Save run artifacts per TRD §12
- Never touch the test set

TRD §12, FR-005, ML-001, ML-006, ML-009, ML-011, CN-006.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import platform
import sys
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
import yaml
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline

from common.config import load_config
from common.errors import ConfigError, DatasetError
from common.logging_setup import setup_logging
from common.paths import ProjectPaths
from models.decision_tree import get_decision_tree_spec, export_tree_info
from models.random_forest import get_random_forest_spec, export_feature_importances
from models.tuning import tune_model, extract_cv_results
from preprocessing.pipeline import build_preprocessor
from preprocessing.feature_selector import build_feature_selector

logger = logging.getLogger(__name__)


def load_training_data(paths: ProjectPaths) -> tuple[pd.DataFrame, pd.Series]:
    """Load training data (features + labels).
    
    Parameters
    ----------
    paths : ProjectPaths
        Path configuration from common.paths
        
    Returns
    -------
    X_train : DataFrame
        Training features
    y_train : Series
        Training labels (string class names)
        
    Notes
    -----
    Loads only the training set. Test set is never loaded here.
    This module must not import any test loader (structural leakage guard).
    """
    train_dir = paths.data_processed / 'train'
    train_path = train_dir / 'train.csv'
    
    if not train_path.exists():
        raise DatasetError(f"Training data not found: {train_path}")
    
    logger.info("Loading training data from %s", train_path)
    df = pd.read_csv(train_path)
    
    if 'target_class' not in df.columns:
        raise DatasetError("Missing 'target_class' column in training data")
    
    # Separate features and labels
    X_train = df.drop(columns=['target_class'])
    y_train = df['target_class']
    
    # Drop any remaining metadata columns (class1, flow_id, Unnamed: 0 index, etc.)
    metadata_cols = [col for col in X_train.columns if col in ['class1', 'flow_id', 'src_ip', 'dst_ip'] or col.startswith('Unnamed:')]
    if metadata_cols:
        logger.info("Dropping metadata columns: %s", metadata_cols)
        X_train = X_train.drop(columns=metadata_cols)
    
    logger.info("Loaded training data: %d samples, %d features", len(X_train), X_train.shape[1])
    logger.info("Class distribution: %s", y_train.value_counts().to_dict())
    
    return X_train, y_train


def build_full_pipeline(
    config: dict,
    model_spec,
    random_state: int,
) -> tuple[Pipeline, LabelEncoder]:
    """Build full pipeline: imputer → scaler → selector → model.
    
    Parameters
    ----------
    config : dict
        Configuration from config/default.yaml
    model_spec : ModelSpec
        Model specification
    random_state : int
        Random state for reproducibility
        
    Returns
    -------
    pipeline : Pipeline
        Full sklearn pipeline
    label_encoder : LabelEncoder
        Fitted label encoder (for later use)
        
    Notes
    -----
    Pipeline steps:
    1. Imputer: fill missing values (median)
    2. Scaler: min-max scaling to [0, 1]
    3. Selector: staged feature selection (variance → correlation → importance)
    4. Classifier: the model being trained
    
    Feature selector is fit inside CV folds, not here.
    """
    # Build preprocessing pipeline (imputer + scaler)
    prep_config = config.get('preprocessing', {})
    missing_strategy = prep_config.get('missing_strategy', 'median')
    
    preprocessor = build_preprocessor(
        imputer_strategy=missing_strategy,
        scaler_range=(0.0, 1.0),
    )
    
    # Build feature selector (will be fit in CV)
    selector_config = config.get('feature_selection', {})
    selector = build_feature_selector(
        variance_threshold=selector_config.get('variance_threshold', 0.01),
        correlation_threshold=selector_config.get('correlation_threshold', 0.95),
        importance_n_estimators=100,
        random_state=random_state,
    )
    
    # Create model estimator
    estimator = model_spec.estimator_factory()
    
    # Build full pipeline
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('selector', selector),
        ('classifier', estimator),
    ])
    
    logger.info("Built full pipeline: %s", [step for step, _ in pipeline.steps])
    
    # Create label encoder (will be fit during training)
    label_encoder = LabelEncoder()
    
    return pipeline, label_encoder


def save_run_artifacts(
    run_dir: Path,
    pipeline: Pipeline,
    label_encoder: LabelEncoder,
    search,
    cv_results_df: pd.DataFrame,
    config: dict,
    model_spec,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    train_time: float,
) -> None:
    """Save all run artifacts per TRD §12.
    
    Parameters
    ----------
    run_dir : Path
        Run directory (artifacts/runs/<run_id>/)
    pipeline : Pipeline
        Fitted pipeline
    label_encoder : LabelEncoder
        Fitted label encoder
    search : GridSearchCV
        Fitted GridSearchCV object
    cv_results_df : DataFrame
        CV results table
    config : dict
        Configuration snapshot
    model_spec : ModelSpec
        Model specification
    X_train : DataFrame
        Training features (for feature names)
    y_train : Series
        Training labels
    train_time : float
        Total training time in seconds
        
    Notes
    -----
    Artifacts saved per TRD §12:
    - config_snapshot.yaml: configuration used
    - label_mapping.sha256: hash of label mapping file
    - cv_results.csv: all CV trials
    - best_params.json: best hyperparameters
    - pipeline.joblib: fitted pipeline
    - label_encoder.joblib: fitted label encoder
    - selected_features.json: feature names after selection
    - train_info.json: metadata (seed, versions, timing, etc.)
    - metrics_cv.json: best CV scores
    - tree_info.json: (Decision Tree only) tree structure
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Saving run artifacts to %s", run_dir)
    
    # 1. Config snapshot
    with open(run_dir / 'config_snapshot.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    # 2. Label mapping hash
    label_mapping_path = Path('config/label_mapping.yaml')
    if label_mapping_path.exists():
        with open(label_mapping_path, 'rb') as f:
            mapping_hash = hashlib.sha256(f.read()).hexdigest()
        with open(run_dir / 'label_mapping.sha256', 'w') as f:
            f.write(mapping_hash)
    
    # 3. CV results
    cv_results_df.to_csv(run_dir / 'cv_results.csv', index=False)
    logger.info("Saved CV results: %d trials", len(cv_results_df))
    
    # 4. Best parameters
    best_params = search.best_params_
    with open(run_dir / 'best_params.json', 'w') as f:
        json.dump(best_params, f, indent=2)
    
    # 5. Pipeline
    joblib.dump(pipeline, run_dir / 'pipeline.joblib')
    logger.info("Saved pipeline: %s", run_dir / 'pipeline.joblib')
    
    # 6. Label encoder
    joblib.dump(label_encoder, run_dir / 'label_encoder.joblib')
    
    # 7. Selected features (after selector)
    # Get feature names that passed through the selector
    try:
        # Get feature names after preprocessing but before selector
        feature_names_in = X_train.columns.tolist()
        
        # Check if selector has get_support() method
        selector = pipeline.named_steps['selector']
        if hasattr(selector, 'get_support'):
            support = selector.get_support()
            selected_features = [name for name, keep in zip(feature_names_in, support) if keep]
        else:
            # Selector is a pipeline itself, get support from final step
            final_selector = selector.steps[-1][1]
            if hasattr(final_selector, 'get_support'):
                support = final_selector.get_support()
                selected_features = [name for name, keep in zip(feature_names_in, support) if keep]
            else:
                selected_features = feature_names_in  # All features kept
        
        selected_features_info = {
            'n_features_in': len(feature_names_in),
            'n_features_out': len(selected_features),
            'selected_features': selected_features,
        }
        
        with open(run_dir / 'selected_features.json', 'w') as f:
            json.dump(selected_features_info, f, indent=2)
        
        logger.info("Selected %d/%d features", len(selected_features), len(feature_names_in))
    
    except Exception as e:
        logger.warning("Could not extract selected features: %s", e)
        selected_features_info = {'error': str(e)}
        with open(run_dir / 'selected_features.json', 'w') as f:
            json.dump(selected_features_info, f, indent=2)
    
    # 8. Training info
    import sklearn
    import xgboost
    
    train_info = {
        'model_name': model_spec.name,
        'model_notes': model_spec.notes,
        'seed': config.get('seed', 42),
        'train_samples': len(X_train),
        'n_features': X_train.shape[1],
        'n_classes': len(label_encoder.classes_),
        'class_names': label_encoder.classes_.tolist(),
        'class_distribution': y_train.value_counts().to_dict(),
        'train_time_seconds': train_time,
        'cv_folds': config.get('cv', {}).get('folds', 5),
        'scoring': 'f1_macro',
        'sklearn_version': sklearn.__version__,
        'xgboost_version': xgboost.__version__,
        'python_version': platform.python_version(),
        'platform': platform.platform(),
        'timestamp': datetime.now().isoformat(),
    }
    
    with open(run_dir / 'train_info.json', 'w') as f:
        json.dump(train_info, f, indent=2)
    
    # 9. Best CV metrics
    metrics_cv = {
        'best_score': float(search.best_score_),
        'best_params': search.best_params_,
        'scoring': 'f1_macro',
    }
    
    with open(run_dir / 'metrics_cv.json', 'w') as f:
        json.dump(metrics_cv, f, indent=2)
    
    # 10. Model-specific artifacts
    if model_spec.name == 'decision_tree':
        try:
            tree_classifier = pipeline.named_steps['classifier']
            tree_info = export_tree_info(tree_classifier)
            
            with open(run_dir / 'tree_info.json', 'w') as f:
                json.dump(tree_info, f, indent=2)
            
            logger.info("Saved tree info: %s", tree_info)
        except Exception as e:
            logger.warning("Could not export tree info: %s", e)
    
    elif model_spec.name == 'random_forest':
        try:
            rf_classifier = pipeline.named_steps['classifier']
            
            # Get feature names after selection
            feature_names_after_selection = selected_features_info.get('selected_features', [])
            if feature_names_after_selection:
                rf_info = export_feature_importances(rf_classifier, feature_names_after_selection)
                
                with open(run_dir / 'feature_importances.json', 'w') as f:
                    json.dump(rf_info, f, indent=2)
                
                logger.info("Saved feature importances: %d features", rf_info['n_features'])
            else:
                logger.warning("Could not determine selected feature names for importance export")
        except Exception as e:
            logger.warning("Could not export feature importances: %s", e)
    
    logger.info("All artifacts saved successfully")


def main():
    """Main training orchestrator."""
    parser = argparse.ArgumentParser(
        description='Train and tune FlowSentry models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m models.train --model decision_tree
  python -m models.train --model decision_tree --config config/default.yaml
        """
    )
    
    parser.add_argument(
        '--model',
        required=True,
        choices=['decision_tree', 'random_forest', 'svm', 'xgboost'],
        help='Model to train'
    )
    parser.add_argument(
        '--config',
        default='config/default.yaml',
        help='Path to configuration file (default: config/default.yaml)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger.info("="*80)
    logger.info("FlowSentry Model Training: %s", args.model)
    logger.info("="*80)
    
    try:
        # Load config
        config = load_config(args.config)
        paths = ProjectPaths(config)
        paths.ensure_dirs()
        random_state = config.get('seed', 42)
        
        # Get model spec
        if args.model == 'decision_tree':
            model_spec = get_decision_tree_spec(random_state=random_state)
        elif args.model == 'random_forest':
            model_spec = get_random_forest_spec(random_state=random_state)
        else:
            raise ConfigError(f"Model '{args.model}' not yet implemented")
        
        logger.info("Model: %s", model_spec.name)
        logger.info("Notes: %s", model_spec.notes)
        
        # Load training data
        X_train, y_train = load_training_data(paths)
        
        # Encode labels
        label_encoder = LabelEncoder()
        y_train_encoded = label_encoder.fit_transform(y_train)
        logger.info("Encoded labels: %s", dict(zip(label_encoder.classes_, range(len(label_encoder.classes_)))))
        
        # Build pipeline
        pipeline, _ = build_full_pipeline(config, model_spec, random_state)
        
        # Tune model
        cv_config = config.get('cv', {})
        search, train_time = tune_model(
            pipeline=pipeline,
            X_train=X_train,
            y_train=y_train_encoded,
            param_grid=model_spec.param_space,
            cv_folds=cv_config.get('folds', 5),
            scoring='f1_macro',  # RID-20
            random_state=random_state,
            n_jobs=-1,
        )
        
        # Extract CV results
        cv_results_df = extract_cv_results(search)
        
        # Refit on full training set with best params
        logger.info("Refitting on full training set with best parameters...")
        best_pipeline = search.best_estimator_
        
        # Generate run ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_id = f"{model_spec.name}_{timestamp}"
        run_dir = paths.artifacts / 'runs' / run_id
        
        # Save artifacts
        save_run_artifacts(
            run_dir=run_dir,
            pipeline=best_pipeline,
            label_encoder=label_encoder,
            search=search,
            cv_results_df=cv_results_df,
            config=config,
            model_spec=model_spec,
            X_train=X_train,
            y_train=y_train,
            train_time=train_time,
        )
        
        logger.info("="*80)
        logger.info("Training complete!")
        logger.info("Run ID: %s", run_id)
        logger.info("Best CV score (macro-F1): %.4f", search.best_score_)
        logger.info("Run directory: %s", run_dir)
        logger.info("="*80)
        
        return 0
    
    except Exception as e:
        logger.exception("Training failed: %s", e)
        return 1


if __name__ == '__main__':
    sys.exit(main())
