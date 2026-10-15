"""
preprocessing/pipeline.py
-------------------------
Preprocessing pipeline builder for FlowSentry (CN-004, Phase 2).

Builds sklearn pipelines for data preprocessing that can be fit on training data
and applied consistently to test/inference data.

Responsibilities:
  - Build preprocessing pipeline (imputer + scaler)
  - Impute missing values (median strategy)
  - Scale features to [0, 1] range (MinMaxScaler)
  - Document pipeline parameters
  - Ensure fit only on training data (never on test)

Feature selector will be added in CN-005.

TRD §7, ML-005, ML-008, ML-010, NFR-003.
"""

from __future__ import annotations

import logging
from typing import Any

from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)


def build_preprocessor(
    imputer_strategy: str = "median",
    scaler_range: tuple[float, float] = (0.0, 1.0),
) -> Pipeline:
    """Build preprocessing pipeline with imputer and scaler.
    
    Parameters
    ----------
    imputer_strategy:
        Strategy for SimpleImputer (default: "median")
        Options: "mean", "median", "most_frequent", "constant"
    scaler_range:
        Feature range for MinMaxScaler (default: (0, 1))
        
    Returns
    -------
    Pipeline
        sklearn Pipeline with: imputer → scaler
        
    Notes
    -----
    Pipeline steps:
      1. SimpleImputer: Replace NaN with median (or other strategy)
         - fit() computes medians from training data only
         - transform() applies those medians to any data
         
      2. MinMaxScaler: Scale features to [0, 1]
         - fit() computes min/max from training data only  
         - transform() applies X_scaled = (X - min) / (max - min)
         
    The pipeline must be fit on training data only.
    It is then applied to test data during evaluation and to new data during inference.
    
    Feature selector will be added in CN-005 as a third step.
    """
    steps = [
        ("imputer", SimpleImputer(strategy=imputer_strategy)),
        ("scaler", MinMaxScaler(feature_range=scaler_range)),
    ]
    
    pipeline = Pipeline(steps)
    
    logger.info(
        "Built preprocessing pipeline: imputer(strategy=%s) → scaler(range=%s)",
        imputer_strategy,
        scaler_range,
    )
    
    return pipeline


def get_pipeline_params(pipeline: Pipeline) -> dict[str, Any]:
    """Extract fitted parameters from a preprocessing pipeline.
    
    Parameters
    ----------
    pipeline:
        Fitted sklearn Pipeline
        
    Returns
    -------
    dict
        Dictionary with fitted parameters from each step
        
    Notes
    -----
    For verification and debugging purposes.
    Returns medians from imputer, min/max from scaler, etc.
    """
    params = {}
    
    for step_name, step in pipeline.steps:
        step_params = {}
        
        if step_name == "imputer" and hasattr(step, "statistics_"):
            step_params["statistics"] = step.statistics_.tolist()
        
        if step_name == "scaler" and hasattr(step, "data_min_"):
            step_params["data_min"] = step.data_min_.tolist()
            step_params["data_max"] = step.data_max_.tolist()
            step_params["scale"] = step.scale_.tolist()
        
        params[step_name] = step_params
    
    return params
