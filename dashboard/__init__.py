"""
dashboard — read-only visualisation of FlowSentry artifacts.

Technology: Streamlit (RID-09, U-12 — confirmed at CN-018).
Reads only from artifacts/; no database; binds to 127.0.0.1 by default.

Views (DB-001…DB-008):
  1. Dataset & class distribution
  2. Four-model comparison table + chart
  3. Confusion matrix per model
  4. PCAP classification results (per-flow table, class distribution, five-tuple)
  5. Near-live monitor (if CN-017 delivered)
  6. How it works — Packets → Five-Tuple → Flow → Features → ML → Class

All displayed metrics are read from artifacts/ JSON files (never hard-coded).

Implemented at CN-018. Placeholder at CN-001. Dashboard library not yet in requirements.
TRD §2, §24.
"""
