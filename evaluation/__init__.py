"""
evaluation — model evaluation, comparison, and reporting.

  metrics.py  — metric computation (Accuracy, Precision, Recall, F1, confusion matrix)
  evaluate.py — load_test_set() and per-model evaluation on the frozen test set
  compare.py  — four-model comparison table and best-model selection
  report.py   — programmatic report generation (CSV, JSON, PNG)

IMPORTANT: load_test_set() is the ONLY place test data is loaded.
No other package may import this function (LeakageGuardError if violated).
Test set is touched exactly once per model in a final evaluation run.

Implemented at CN-010…CN-011. Placeholder at CN-001.
TRD §2, §19.
"""
