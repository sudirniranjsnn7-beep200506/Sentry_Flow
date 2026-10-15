"""
models — ML model specifications, training, tuning, and registry.

Four models (Review-1):
  decision_tree.py  — DecisionTreeClassifier (CN-006)
  random_forest.py  — RandomForestClassifier (CN-007)
  svm.py            — SVC / LinearSVC with scalability policy (CN-008, RID-06)
  xgboost_model.py  — XGBClassifier multi-class (CN-009)

Shared infrastructure:
  base.py     — ModelSpec protocol
  tuning.py   — GridSearchCV / RandomizedSearchCV wrapper
  train.py    — CLI entry point: python -m models.train --model <name>
  registry.py — file-based model registry with SHA-256 integrity (CN-012)

STRUCTURAL LEAKAGE GUARD: models/ must NEVER import evaluation/'s test loader.
This is enforced by a leakage test in tests/unit/test_no_leakage.py.

Implemented at CN-006…CN-009 (training) and CN-012 (registry). Placeholder at CN-001.
TRD §2, §12–§16, §20.
"""
