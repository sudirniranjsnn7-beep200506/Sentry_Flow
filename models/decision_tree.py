"""
models/decision_tree.py
-----------------------
Decision Tree classifier specification for FlowSentry (CN-006, Phase 3).

Decision Tree is the interpretable baseline:
- Simple to explain in a viva
- Can export human-readable rules
- Fast to train
- Prone to overfitting without depth limits

Hyperparameters tuned:
- criterion: split quality measure (gini, entropy)
- max_depth: maximum tree depth (None = unlimited, or bounded values)
- min_samples_split: minimum samples to split an internal node
- min_samples_leaf: minimum samples in a leaf
- class_weight: handle class imbalance

TRD §13, FR-005, ML-001, CN-006.
"""

from __future__ import annotations

import logging

from sklearn.tree import DecisionTreeClassifier

from models.base import ModelSpec

logger = logging.getLogger(__name__)


def get_decision_tree_spec(random_state: int = 42) -> ModelSpec:
    """Create Decision Tree model specification.
    
    Parameters
    ----------
    random_state : int, default=42
        Random state for reproducibility
        
    Returns
    -------
    ModelSpec
        Decision Tree specification with tunable hyperparameters
        
    Notes
    -----
    Parameter names verified against scikit-learn 1.9.1 (2024-10-11):
    DecisionTreeClassifier(
        criterion='gini',         # or 'entropy', 'log_loss'
        splitter='best',
        max_depth=None,           # None = unlimited (high overfitting risk)
        min_samples_split=2,      # minimum samples to split a node
        min_samples_leaf=1,       # minimum samples in a leaf
        min_weight_fraction_leaf=0.0,
        max_features=None,
        random_state=None,
        max_leaf_nodes=None,
        min_impurity_decrease=0.0,
        class_weight=None,        # or 'balanced', or dict
        ccp_alpha=0.0,
        monotonic_cst=None
    )
    
    Search space rationale:
    - criterion: both standard splits (gini for speed, entropy for information gain)
    - max_depth: None (unconstrained) + bounded values to prevent overfitting
    - min_samples_split: control overfitting by requiring more samples to split
    - min_samples_leaf: control overfitting by requiring more samples in leaves
    - class_weight: 'balanced' to handle class imbalance (Streaming is only 4.6%)
    
    Tree export:
    After training, export tree depth, leaf count, and optionally textual rules
    for viva discussion (TRD §13).
    """
    return ModelSpec(
        name='decision_tree',
        estimator_factory=lambda: DecisionTreeClassifier(
            random_state=random_state,
            # All tunable params come from param_space below
        ),
        param_space={
            'classifier__criterion': ['gini', 'entropy'],
            'classifier__max_depth': [None, 10, 20, 30],
            'classifier__min_samples_split': [2, 5, 10],
            'classifier__min_samples_leaf': [1, 2, 4],
            'classifier__class_weight': [None, 'balanced'],
        },
        notes=(
            "Decision Tree: interpretable baseline for viva discussion. "
            "Prone to overfitting without depth limits. "
            "Export tree depth/leaf count and optionally human-readable rules. "
            "Fast to train. Good for understanding which flow features matter most."
        ),
    )


def export_tree_info(tree_classifier: DecisionTreeClassifier) -> dict[str, any]:
    """Export tree structure information after training.
    
    Parameters
    ----------
    tree_classifier : DecisionTreeClassifier
        Fitted Decision Tree classifier
        
    Returns
    -------
    dict
        Tree info including:
        - n_leaves: number of leaf nodes
        - max_depth: actual maximum depth reached
        - n_nodes: total number of nodes
        - n_features: number of features used
        
    Notes
    -----
    Call this after the pipeline is fitted to extract tree structure.
    Useful for understanding model complexity and for viva discussion.
    
    Human-readable rules can be exported via:
        from sklearn.tree import export_text
        rules = export_text(tree_classifier, feature_names=feature_names)
    """
    tree = tree_classifier.tree_
    
    info = {
        'n_leaves': int(tree.n_leaves),
        'max_depth': int(tree.max_depth),
        'n_nodes': int(tree.node_count),
        'n_features': int(tree.n_features),
    }
    
    logger.info(
        "Decision Tree structure: %d nodes, %d leaves, max depth %d, %d features",
        info['n_nodes'],
        info['n_leaves'],
        info['max_depth'],
        info['n_features'],
    )
    
    return info
