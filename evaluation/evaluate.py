"""
evaluation/evaluate.py
----------------------
Model evaluation on test set for FlowSentry (CN-010, Phase 4).

Evaluates trained models on the frozen test set exactly once per model.
Produces all required metrics and artifacts.

Usage:
    python -m evaluation.evaluate --run-id decision_tree_20261014_011743

TRD §18, FR-006, EV-001-006, CN-010.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common.config import load_config
from common.errors import DatasetError
from common.logging_setup import setup_logging
from common.paths import ProjectPaths
from evaluation.metrics import compute_metrics, measure_inference_time, format_classification_report
from evaluation.test_loader import load_test_set

logger = logging.getLogger(__name__)


def load_run_artifacts(run_dir: Path) -> tuple:
    """Load artifacts from a training run.
    
    Parameters
    ----------
    run_dir : Path
        Run directory path
        
    Returns
    -------
    pipeline :
        Fitted pipeline
    label_encoder :
        Fitted label encoder
    train_info : dict
        Training information
        
    Raises
    ------
    FileNotFoundError
        If required artifacts are missing
    """
    pipeline_path = run_dir / 'pipeline.joblib'
    encoder_path = run_dir / 'label_encoder.joblib'
    info_path = run_dir / 'train_info.json'
    
    if not pipeline_path.exists():
        raise FileNotFoundError(f"Pipeline not found: {pipeline_path}")
    if not encoder_path.exists():
        raise FileNotFoundError(f"Label encoder not found: {encoder_path}")
    if not info_path.exists():
        raise FileNotFoundError(f"Train info not found: {info_path}")
    
    logger.info("Loading pipeline from %s", pipeline_path)
    pipeline = joblib.load(pipeline_path)
    
    logger.info("Loading label encoder from %s", encoder_path)
    label_encoder = joblib.load(encoder_path)
    
    with open(info_path) as f:
        train_info = json.load(f)
    
    return pipeline, label_encoder, train_info


def save_evaluation_artifacts(
    eval_dir: Path,
    metrics: dict,
    timing: dict,
    train_info: dict,
    run_id: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: list[str],
) -> None:
    """Save all evaluation artifacts.
    
    Parameters
    ----------
    eval_dir : Path
        Evaluation directory
    metrics : dict
        Computed metrics
    timing : dict
        Timing information
    train_info : dict
        Training information from run
    run_id : str
        Run ID being evaluated
    y_true : array
        True labels
    y_pred : array
        Predicted labels
    class_names : list
        Class names
    """
    eval_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Metrics JSON
    metrics_file = eval_dir / 'metrics.json'
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info("Saved metrics to %s", metrics_file)
    
    # 2. Timing JSON
    timing_file = eval_dir / 'timing.json'
    with open(timing_file, 'w') as f:
        json.dump(timing, f, indent=2)
    logger.info("Saved timing to %s", timing_file)
    
    # 3. Summary JSON (combines everything)
    summary = {
        'run_id': run_id,
        'model_name': train_info.get('model_name'),
        'evaluated_at': datetime.now().isoformat(),
        'metrics': metrics,
        'timing': timing,
        'train_time_seconds': train_info.get('train_time_seconds'),
        'train_samples': train_info.get('train_samples'),
        'test_samples': metrics.get('n_samples'),
    }
    
    summary_file = eval_dir / 'summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info("Saved summary to %s", summary_file)
    
    # 4. Classification report (human-readable)
    report_text = format_classification_report(metrics)
    report_file = eval_dir / 'classification_report.txt'
    with open(report_file, 'w') as f:
        f.write(report_text)
    logger.info("Saved classification report to %s", report_file)
    
    # 5. Confusion matrix plot
    cm = np.array(metrics['confusion_matrix'])
    
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm, cmap='Blues', interpolation='nearest')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Count', rotation=270, labelpad=20)
    
    # Add labels
    ax.set_xticks(np.arange(len(class_names)))
    ax.set_yticks(np.arange(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha='right')
    ax.set_yticklabels(class_names)
    
    # Add text annotations
    thresh = cm.max() / 2
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            ax.text(j, i, format(cm[i, j], 'd'),
                   ha="center", va="center",
                   color="white" if cm[i, j] > thresh else "black")
    
    ax.set_title(f'Confusion Matrix - {train_info.get("model_name", run_id)}')
    ax.set_ylabel('True Label')
    ax.set_xlabel('Predicted Label')
    plt.tight_layout()
    
    cm_file = eval_dir / 'confusion_matrix.png'
    plt.savefig(cm_file, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info("Saved confusion matrix plot to %s", cm_file)
    
    # 6. Per-class metrics CSV
    per_class_df = pd.DataFrame(metrics['per_class']).T
    per_class_df.index.name = 'class'
    per_class_file = eval_dir / 'per_class_metrics.csv'
    per_class_df.to_csv(per_class_file)
    logger.info("Saved per-class metrics to %s", per_class_file)


def main():
    """Main evaluation entry point."""
    parser = argparse.ArgumentParser(
        description='Evaluate trained model on test set',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m evaluation.evaluate --run-id decision_tree_20261014_011743
        """
    )
    
    parser.add_argument(
        '--run-id',
        required=True,
        help='Run ID to evaluate (directory name in artifacts/runs/)'
    )
    parser.add_argument(
        '--config',
        default='config/default.yaml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger.info("="*80)
    logger.info("FlowSentry Model Evaluation: %s", args.run_id)
    logger.info("="*80)
    
    try:
        # Load config and paths
        config = load_config(args.config)
        paths = ProjectPaths(config)
        paths.ensure_dirs()
        
        # Load run artifacts
        run_dir = paths.artifacts / 'runs' / args.run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run directory not found: {run_dir}")
        
        pipeline, label_encoder, train_info = load_run_artifacts(run_dir)
        
        logger.info("Model: %s", train_info.get('model_name'))
        logger.info("Training samples: %d", train_info.get('train_samples'))
        logger.info("Training time: %.2f seconds", train_info.get('train_time_seconds', 0))
        
        # Load test set (with audit logging)
        logger.info("Loading test set for final evaluation...")
        X_test, y_test = load_test_set(paths, purpose="final_evaluation")
        
        # Encode test labels
        y_test_encoded = label_encoder.transform(y_test)
        class_names = label_encoder.classes_.tolist()
        
        logger.info("Predicting on test set...")
        y_pred_encoded = pipeline.predict(X_test)
        
        # Compute metrics
        logger.info("Computing evaluation metrics...")
        metrics = compute_metrics(y_test_encoded, y_pred_encoded, class_names)
        
        # Measure inference time
        logger.info("Measuring inference time...")
        timing = measure_inference_time(pipeline, X_test)
        
        # Save artifacts
        eval_dir = paths.reports_dir / args.run_id
        logger.info("Saving evaluation artifacts to %s", eval_dir)
        
        save_evaluation_artifacts(
            eval_dir=eval_dir,
            metrics=metrics,
            timing=timing,
            train_info=train_info,
            run_id=args.run_id,
            y_true=y_test_encoded,
            y_pred=y_pred_encoded,
            class_names=class_names,
        )
        
        # Print summary
        logger.info("="*80)
        logger.info("Evaluation Complete!")
        logger.info("="*80)
        logger.info("Run ID: %s", args.run_id)
        logger.info("Model: %s", train_info.get('model_name'))
        logger.info("")
        logger.info("Test Set Results:")
        logger.info("  Accuracy:    %.4f", metrics['accuracy'])
        logger.info("  Macro F1:    %.4f", metrics['macro']['f1'])
        logger.info("  Weighted F1: %.4f", metrics['weighted']['f1'])
        logger.info("")
        logger.info("Inference Time:")
        logger.info("  Per flow:    %.3f ms", timing['mean_time_per_flow_ms'])
        logger.info("")
        logger.info("Artifacts saved to: %s", eval_dir)
        logger.info("="*80)
        
        return 0
    
    except Exception as e:
        logger.exception("Evaluation failed: %s", e)
        return 1


if __name__ == '__main__':
    sys.exit(main())
