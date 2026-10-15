"""
inference — model inference for PCAP files and near-live traffic.

  predictor.py       — load a registry pipeline; schema-parity check; predict()
  pcap_classifier.py — PCAP → FlowExtractor → normaliser → predictor → predictions.csv
  live_classifier.py — chunk loop → FlowExtractor → normaliser → predictor → predictions.jsonl

Networking chain at inference:
  PCAP / capture chunk
      ↓ CICFlowMeter adapter (external subprocess)
      ↓ flow CSV
      ↓ Feature Normaliser (alias map + unit conversion)
      ↓ schema-parity check (SchemaMismatchError if mismatch)
      ↓ registry pipeline.predict()
      ↓ Traffic Classification (Web Browsing | VoIP | Streaming | File Transfer)

Implemented at CN-015 (PCAP) and CN-017 (near-live). Placeholder at CN-001.
TRD §2, §21, §23.
"""
