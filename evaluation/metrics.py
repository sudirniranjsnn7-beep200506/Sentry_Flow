"""
evaluation/metrics.py
---------------------
Evaluation metrics for FlowSentry (CN-010, Phase 4).

Compute all required metrics for model evaluation on the test set.
Metrics are computed exactly once per model and saved to artifacts.

TRD §18, FR-006, EV-001-006, CN-010.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

logger = logging.getLogger(__name__)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: list[str],
) -> dict[str, Any]:
    """Compute all evaluation metrics.
    
    Parameters
    ----------
    y_true : array-like
        True labels (integer-encoded)
    y_pred : array-like
        Predicted labels (integer-encoded)
    class_names : list[str]
        Class names in label-encoded order
        
    Returns
    -------
    dict
        Dictionary containing all metrics:
        - accuracy: overall accuracy
        - per_class: dict with precision/recall/F1 per class
        - macro: macro-averaged metrics
        - weighted: weighted-averaged metrics
        - confusion_matrix: confusion matrix as list
        - class_names: class names for reference
        
    Notes
    -----
    All metrics follow sklearn conventions.
    Per-class metrics are indexed by class name.
    
    TRD §18: Required metrics:
    - Accuracy
    - Precision/Recall/F1 per class
    - Macro and weighted averages
    - Confusion matrix
    """
    # Accuracy
    accuracy = float(accuracy_score(y_true, y_pred))
    
    # Per-class metrics
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        average=None,
        zero_division=0,
    )
    
    per_class = {}
    for i, class_name in enumerate(class_names):
        per_class[class_name] = {
            'precision': float(precision[i]),
            'recall': float(recall[i]),
            'f1': float(f1[i]),
            'support': int(support[i]),
        }
    
    # Macro averages
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average='macro',
        zero_division=0,
    )
    
    # Weighted averages
    weighted_precision, weighted_recall, weighted_f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average='weighted',
        zero_division=0,
    )
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
    metrics = {
        'accuracy': accuracy,
        'per_class': per_class,
        'macro': {
            'precision': float(macro_precision),
            'recall': float(macro_recall),
            'f1': float(macro_f1),
        },
        'weighted': {
            'precision': float(weighted_precision),
            'recall': float(weighted_recall),
            'f1': float(weighted_f1),
        },
        'confusion_matrix': cm.tolist(),
        'class_names': class_names,
        'n_samples': len(y_true),
    }
    
    logger.info("Computed metrics: accuracy=%.4f, macro_f1=%.4f, weighted_f1=%.4f",
                accuracy, macro_f1, weighted_f1)
    
    return metrics


def measure_inference_time(
    pipeline,
    X_test: pd.DataFrame,
    n_runs: int = 3,
) -> dict[str, float]:
    """Measure per-flow inference time.
    
    Parameters
    ----------
    pipeline :
        Fitted pipeline
    X_test : DataFrame
        Test features
    n_runs : int, default=3
        Number of timing runs for averaging
        
    Returns
    -------
    dict
        Timing statistics:
        - mean_time_per_flow_ms: mean time per flow in milliseconds
        - total_time_s: total time for all test samples
        - n_flows: number of test flows
        - n_runs: number of timing runs
        
    Notes
    -----
    Measures wall-clock time for prediction on the full test set.
    Averages over multiple runs for stability.
    """
    times = []
    n_flows = len(X_test)
    
    for _ in range(n_runs):
        start = time.perf_counter()
        _ = pipeline.predict(X_test)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    mean_total_time = np.mean(times)
    mean_per_flow = (mean_total_time / n_flows) * 1000  # Convert to ms
    
    timing = {
        'mean_time_per_flow_ms': float(mean_per_flow),
        'total_time_s': float(mean_total_time),
        'n_flows': n_flows,
        'n_runs': n_runs,
    }
    
    logger.info("Inference timing: %.3f ms per flow (%.2f s total for %d flows)",
                mean_per_flow, mean_total_time, n_flows)
    
    return timing


def format_classification_report(
    metrics: dict[str, Any]
) -> str:
    """Format metrics as a human-readable classification report.
    
    Parameters
    ----------
    metrics : dict
        Metrics dictionary from compute_metrics()
        
    Returns
    -------
    str
        Formatted classification report string
    """
    lines = []
    lines.append("Classification Report")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Accuracy: {metrics['accuracy']:.4f}")
    lines.append("")
    lines.append(f"{'Class':<20} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'Support':>10}")
    lines.append("-" * 60)
    
    for class_name, class_metrics in metrics['per_class'].items():
        lines.append(
            f"{class_name:<20} "
            f"{class_metrics['precision']:>10.4f} "
            f"{class_metrics['recall']:>10.4f} "
            f"{class_metrics['f1']:>10.4f} "
            f"{class_metrics['support']:>10d}"
        )
    
    lines.append("")
    lines.append(f"{'Macro Avg':<20} "
                 f"{metrics['macro']['precision']:>10.4f} "
                 f"{metrics['macro']['recall']:>10.4f} "
                 f"{metrics['macro']['f1']:>10.4f} "
                 f"{metrics['n_samples']:>10d}")
    
    lines.append(f"{'Weighted Avg':<20} "
                 f"{metrics['weighted']['precision']:>10.4f} "
                 f"{metrics['weighted']['recall']:>10.4f} "
                 f"{metrics['weighted']['f1']:>10.4f} "
                 f"{metrics['n_samples']:>10d}")
    
    return "\n".join(lines)
