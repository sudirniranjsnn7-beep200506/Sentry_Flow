# FlowSentry (React)
**Machine Learning Based Network Traffic Classification Using Flow Features**

FlowSentry is a high-performance React application for network traffic classification using flow-level statistical features without inspecting packet payloads. It preserves the full business logic, 4-model evaluation, Cisco Packet Tracer topology, offline PCAP flow extraction, and model registry from the original Review-1 specification.

## Core Features

1. **Cisco Packet Tracer Network Topology (CN-023)**
   - Interactive network diagram representing Client Network (10.0.0.0/24), Switch SW1 (2960-24TT), Router R1 (2911 Gateway), and Server Farm (10.0.1.0/24).
   - Router capture interface (`Gi0/1`) traffic extraction and live packet traversal animation.
   - Traffic simulation for Web Browsing (HTTP GET), VoIP (SIP/RTP), Streaming (RTSP/HLS), and File Transfer (FTP RETR).

2. **Offline PCAP Flow Classifier (CN-014 / CN-015)**
   - Bidirectional 5-tuple aggregation with schema parity gate check against canonical `feature_schema.yaml`.
   - Pre-loaded PCAP captures: `mixed_enterprise.pcap`, `web_browsing.pcap`, `voip.pcap`, `streaming.pcap`, and `file_transfer.pcap`.
   - Interactive flow inspector with multi-class probability breakdown and viva-ready decision tree explainability rules.

3. **Near-Live Stream Classification (CN-016 / CN-017)**
   - Rolling 1-second chunk ingestion with measured latency tracking (0.0071 ms/flow).
   - Real-time traffic volume breakdown and live streaming flow event log.

4. **Model Benchmarks & Review-1 Verification (CN-010 / CN-011)**
   - Comparative evaluation across Decision Tree (production active), Random Forest, XGBoost, and SVM.
   - Validated Review-1 abstract claim: 95–98% claimed vs 96.70% test accuracy confirmed.
   - Interactive confusion matrix and per-class precision, recall, and F1 metrics.

5. **Model Registry & Governance (CN-012)**
   - Active Model: `decision_tree_20261014_011743` with SHA-256 integrity verification (`ad7336732e0c...`).
   - 9 selected features retained out of 21 canonical features.
   - Approved ISCX-VPN2016 Scenario B label mapping table (`config/label_mapping.yaml`).

## Development

- Start development server: `npm run dev` (runs on `http://0.0.0.0:3000`)
- Build for production: `npm run build`
