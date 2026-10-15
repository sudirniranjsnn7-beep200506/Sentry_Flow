"""
preprocessing — dataset ingestion, inspection, label mapping, cleaning, splitting.

Pipeline:
  ingest.py        — checksum manifest from data/raw/
  inspect.py       — dataset inspection report and label worksheet
  label_mapping.py — apply approved config/label_mapping.yaml
  cleaning.py      — deterministic cleaning (identifiers, inf→NaN, dedup, ports)
  split.py         — frozen stratified train/test split
  pipeline.py      — sklearn Pipeline builder (imputer + MinMaxScaler)
  validate_features.py — feature schema validation and selector

Networking concept: flow-level statistical features are the model input;
IP/MAC/port identifiers are metadata only (never model input).

Implemented at CN-002…CN-005. Placeholder at CN-001.
TRD §2, §4, §10, §11.
"""
