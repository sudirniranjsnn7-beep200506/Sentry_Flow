# PRD — FlowSentry
**Product Requirements Document**
*FlowSentry — Machine Learning Based Network Traffic Classification Using Flow Features*

| | |
|---|---|
| Document | `PRD.md` — product authority (see `AGENTS.md` for authority order) |
| Project type | Computer Networks academic project (VIT) — Review-1 document is the primary source |
| Team (per Review-1) | Sudir Niranj R (24BDS0267), Vishal B S (24BCE2475) |
| Status | Phase 0 — Specification. **Nothing in this repository is implemented yet.** |
| Companion docs | `TRD.md` (technical authority), `AGENTS.md`, `BUILD_PLAN.md`, `TASKS.md`, `README.md` |

---

## 0. How to read this document

### 0.1 Provenance tags
Every requirement carries a provenance tag so that an assumption is never mistaken for an established requirement.

| Tag | Meaning |
|---|---|
| **[SRC]** | Stated or directly implied by the CN Review-1 document (the primary source of truth). |
| **[BRF]** | Stated in the project brief given to the documentation author (pipeline diagram, six deliverables, scope guards) but not in Review-1 itself. |
| **[REC]** | **Recommended Implementation Decision** — derived cautiously, *not* in the source. Listed in `TRD.md` Appendix A as `RID-xx`. Can be changed by the team. |
| **[UNRES]** | **Unresolved / To Be Finalized.** Listed in `TRD.md` Appendix B as `U-xx`. Work that depends on it is gated. |

### 0.2 Numerical-claims rule
Review-1's abstract states that experiments "confirm" accuracy "upwards of 95–98%". **This document does not adopt that as a result or as an acceptance threshold.** No experiment has been run for this repository. All performance figures in final reports must come from actual runs recorded in `artifacts/` (see EV-007). The 95–98% figure is treated as a *claim from the Review-1 abstract that FlowSentry's own experiments will either support or not* (U-08).

---

## 1. Product Overview

FlowSentry is a supervised machine-learning system that classifies network traffic into application categories using **flow-level statistical features only — never packet payload content**. It takes network traffic (benchmark dataset flows, offline PCAP files, and — if feasible — a live interface), groups packets into bidirectional flows by **five-tuple** (Source IP, Destination IP, Source Port, Destination Port, Protocol), extracts statistical flow features (CICFlowMeter-style: duration, inter-arrival times, byte/packet counts, TCP flag counts, etc.), and predicts an application class with a model chosen from a four-model comparison (Decision Tree, Random Forest, SVM, XGBoost).

The networking chain that the product must keep visible at every layer:

```text
Network Packets → Five-Tuple → Bidirectional Flow → Flow-Level Statistical Features → Machine Learning → Traffic Classification
```

## 2. Problem Statement

Per Review-1 **[SRC]**: port-based classification is unreliable (dynamic port allocation, P2P tunnelling, random ports); Deep Packet Inspection (DPI) is computationally expensive, raises privacy concerns, and is ineffective against end-to-end encrypted traffic (Review-1 names HTTPS, TLS 1.3, QUIC). Review-1 also states that over 85% of modern web traffic is encrypted — *this statistic is quoted from Review-1 and has not been independently verified by this project.*

FlowSentry addresses the question: **can application-type traffic classes be recovered from flow-level statistics alone, without inspecting payloads, and which of four standard classifiers does this best?**

> Review-1's problem-statement paragraph and Objectives section are partially corrupted/truncated in the supplied PDF (text cut off at the end of page 1). Objectives in §4 below are therefore reconstructed from the abstract, architecture, and module sections and are marked accordingly (U-07).

## 3. Background and Motivation

Review-1's literature gap analysis (as cited in the source; not independently verified here):

| Reference | Technique | Gap identified by Review-1 |
|---|---|---|
| Nguyen & Armitage (2008), IEEE Comm. Surveys | Survey of port-based and DPI methods | DPI fails under encryption; ports fail under obfuscation; high CPU cost |
| Lashkari et al. (2016), ICISSP | Time-based flow extraction (CICFlowMeter) on encrypted/Tor traffic | Focus on encrypted tunnels; offline batch extraction latency; no real-time streaming capability |
| Enisoglu & Rakocevic (2023), IEEE IWCMC | Trend-based statistical ML features for low-latency identification | Limited classifier scope; no ensemble tree models (XGBoost); no multi-class application categorisation |

FlowSentry's positioning relative to these gaps: (a) privacy-preserving by construction (no payload features); (b) a four-classifier comparison including XGBoost; (c) multi-class application categorisation; (d) an *attempt* at live classification, with feasibility and latency to be measured rather than assumed.

## 4. Objectives

| ID | Objective | Prov. |
|---|---|---|
| OBJ-1 | Build a flow-based traffic classification pipeline that uses no payload inspection. | SRC |
| OBJ-2 | Train and compare Decision Tree, Random Forest, SVM, and XGBoost on benchmark-dataset flow features. | SRC |
| OBJ-3 | Evaluate with Accuracy, Precision, Recall, F1 per traffic category. | SRC |
| OBJ-4 | Classify traffic from PCAP files using the best model via the same feature pipeline. | SRC/BRF |
| OBJ-5 | Demonstrate live-interface classification if it can be implemented and verified. | SRC/BRF (optional) |
| OBJ-6 | Provide a dashboard visualising results. | BRF (optional) |
| OBJ-7 | Keep networking concepts (packets, five-tuple, flows, flags, IAT) explicit and explainable in a viva. | BRF |

## 5. Target Users

| User | Need |
|---|---|
| Project team (students) | Reproducible pipeline and honest results for Review-2/final evaluation. |
| Faculty reviewers / viva examiners | Clear networking-to-ML chain, defensible methodology, visible evidence. |
| Demo audience | See a PCAP (and optionally live traffic) get classified, with a dashboard. |

Not targeted: production network operators, ISPs, security teams (see §8).

## 6. Scope
FlowSentry is a **single-machine, Python-based, file-oriented academic prototype**. Components: capture helpers, flow extraction (via an adapter), preprocessing, feature selection, training/tuning/evaluation of four models, a file-based model registry, PCAP inference, optional near-live inference, and an optional dashboard.

## 7. In Scope
1. Dataset ingestion, inspection, label mapping, preprocessing (Review-1 Module 1).
2. Flow feature extraction via CICFlowMeter-style features through an adapter (Module 2).
3. Training + tuning (cross-validation, feature selection) of four models (Module 3).
4. Evaluation with Accuracy/Precision/Recall/F1 per class (Module 4).
5. Best-model persistence with metadata (file-based registry).
6. PCAP → flows → features → prediction.
7. Capture helpers using Tshark/Scapy; Wireshark as a manual inspection/validation tool.
8. Dashboard (optional) and demo packaging; final documentation.

## 8. Out of Scope
- Payload/DPI-based classification; decryption of any traffic.
- Intrusion detection / attack classification as a product goal (CIC-IDS2017 is named in Review-1 as a benchmark dataset; its role is U-02 — FlowSentry is not an IDS).
- Production deployment, cloud, containers/orchestration, microservices, message queues, authentication/multi-user, databases.
- Deep learning models (not in Review-1).
- Guaranteed real-time throughput on high-speed links.
- Traffic categories beyond Review-1's list (unless the team formally changes U-01).

## 9. Optional / Future Scope
- Live classification (FR-009) — *optional; delivered only if verified*.
- Dashboard (FR-010) — optional but planned.
- Native (project-written) Scapy flow extractor as a fallback if CICFlowMeter cannot be run (RID-10).
- "Uncertain/Other" class or confidence threshold for out-of-distribution traffic (RID-19).
- Encrypted-tunnel (VPN/Tor) variants, additional datasets, drift monitoring.

---

## 10. Functional Requirements

| ID | Requirement | Prov. |
|---|---|---|
| FR-001 | The system shall implement the pipeline: capture/dataset → flow generation → five-tuple grouping → feature extraction → preprocessing → feature selection → training → evaluation → best model → PCAP/live inference → classification → visualisation. | SRC/BRF |
| FR-002 | Classification shall use **flow-level statistical features only**; no payload bytes or payload-derived content shall be used as model input. | SRC |
| FR-003 | Flows shall be identified by the five-tuple and aggregated **bidirectionally** (forward/backward direction semantics documented in TRD §7). | SRC |
| FR-004 | The system shall support training from the benchmark datasets named in Review-1 (ISCX-VPN2016, CIC-IDS2017), subject to dataset usage and label-mapping decisions U-02/U-03. | SRC |
| FR-005 | The system shall train and compare exactly four classifiers: Decision Tree, Random Forest, SVM, XGBoost. | SRC |
| FR-006 | The system shall evaluate each model with Accuracy, Precision, Recall, and F1-Score across traffic categories. | SRC |
| FR-007 | The system shall select a "best model" by a documented, pre-declared criterion (TRD §19.4) and persist it in the model registry. | BRF/REC |
| FR-008 | The system shall classify flows extracted from an offline PCAP file using a registry model. | SRC/BRF |
| FR-009 | The system shall attempt live-interface classification; delivery is conditional on verification (RT-004). | SRC/BRF (optional) |
| FR-010 | The system shall provide a dashboard to visualise dataset, model comparison, and classification results. | BRF (optional) |
| FR-011 | Each pipeline stage shall be runnable from a command-line entry point with explicit arguments. | REC |
| FR-012 | Paths, seeds, thresholds, and external-tool locations shall be configuration, not hard-coded. | REC |
| FR-013 | The capture module shall record traffic to `.pcap` files using Tshark and/or Scapy. | SRC |

## 11. ML Requirements

| ID | Requirement | Prov. |
|---|---|---|
| ML-001 | Models: Decision Tree, Random Forest, SVM, XGBoost; all multi-class supervised. | SRC |
| ML-002 | Missing values shall be handled (strategy documented and applied identically at train and inference). | SRC |
| ML-003 | Min-max scaling shall be applied; the scaler shall be **fit on training data only**. | SRC + REC |
| ML-004 | Non-informative static identifiers (IP, MAC) shall be removed from model input to prevent overfitting. | SRC |
| ML-005 | Feature selection shall be performed; method is not specified in Review-1 (RID-08). Selection shall be fit on training data only. | SRC + REC |
| ML-006 | Hyperparameter tuning shall use cross-validation, within the training set only. | SRC |
| ML-007 | A held-out test set shall be created once, frozen, and touched only for final evaluation. | SRC ("standard test splits") + REC |
| ML-008 | No data leakage: no fitting of any transformer, selector, encoder, or hyperparameter on test data; leakage tests shall exist. | REC |
| ML-009 | Preprocessing + feature selection + model shall be bundled as one persisted pipeline so inference is identical to training. | REC |
| ML-010 | Class imbalance shall be measured and, if material, handled on training data only; the test distribution shall never be altered. | REC |
| ML-011 | All randomness shall be seeded from configuration; seeds recorded with results. | REC |
| ML-012 | SVM scalability: if full-data SVM training is infeasible, any subsampling/linear variant shall be disclosed in the comparison (RID-06). | REC |

## 12. Dataset Requirements

| ID | Requirement | Prov. |
|---|---|---|
| DS-001 | Datasets named by Review-1: **ISCX-VPN2016** and **CIC-IDS2017**. Which is primary, and whether both are used, is **U-02**. | SRC / UNRES |
| DS-002 | A **Dataset → Target Label Mapping** (TRD §6) shall be completed and *approved by the team* **before any model training**. Status today: **To be finalized before model training.** | BRF / UNRES |
| DS-003 | Dataset provenance shall be recorded: source URL/citation, version, licence, file list, SHA-256 checksums. | REC |
| DS-004 | A dataset inspection report (columns, dtypes, label counts, missing/inf counts, duplicates) shall be generated from the real files — not written from memory. | REC |
| DS-005 | Raw data under `data/raw/` shall be treated as immutable; all transformations write to `data/processed/`. | REC |
| DS-006 | Large datasets shall not be committed to git; `data/README.md` documents how to obtain them. A small `data/sample/` subset is permitted only if the dataset licence allows. | REC |
| DS-007 | Rows whose original label is not mapped to a target class shall be excluded **and counted/reported**, never silently dropped. | REC |
| DS-008 | Whether dataset-provided flow CSVs or flows regenerated from dataset PCAPs are used is **U-04**; training/inference feature-schema parity is mandatory either way (FE-008). | UNRES |

## 13. Feature Requirements
Review-1 identifies four feature families (examples are as named in the source; **exact column names must be read from the actual CSV/extractor output, not from this document**).

| ID | Requirement | Prov. |
|---|---|---|
| FE-001 | **Time-based metrics:** e.g., Flow Duration, IAT statistics (e.g., mean), Active/Idle time statistics. | SRC |
| FE-002 | **Volume metrics:** e.g., Total Fwd/Bwd packets, total bytes, average packet size. | SRC |
| FE-003 | **TCP flag metrics:** e.g., SYN, ACK, FIN, PSH counts; header-length ratios. | SRC |
| FE-004 | **Directional ratios:** directional packet ratios (named in the abstract). | SRC |
| FE-005 | A canonical **feature schema** file (`config/feature_schema.yaml`) shall list model-input features, excluded identifier/metadata columns, dtypes, and group membership. | REC |
| FE-006 | Feature names/semantics shall be verified against the real data/extractor output (CN-003, CN-005, CN-013). | REC |
| FE-007 | Identifier columns (IPs, MACs, timestamps, flow IDs) shall be excluded from model input but may be retained as *metadata* for display. | SRC + REC |
| FE-008 | A schema-parity check shall fail loudly if inference-time columns differ from the training schema. | REC |
| FE-009 | Port features: whether Source Port / Destination Port enter the model is decided under RID-07 (default: excluded from model input, because port-based classification is the limitation FlowSentry addresses). | REC |
| FE-010 | Review-1's "80+ metrics" refers to CICFlowMeter output; the exact count/names depend on the verified version (U-05). | SRC / UNRES |

## 14. Traffic Classification Requirements

| ID | Requirement | Prov. |
|---|---|---|
| TC-001 | Target classes per Review-1 page 2 "Output Classes": **Web Browsing, VoIP, Streaming, File Transfer**. (The architecture figure abbreviates to "Web / VoIP / Media" — see U-01.) | SRC / UNRES |
| TC-002 | The system shall output a predicted class per flow. | SRC |
| TC-003 | Where the model supports it, a confidence/probability shall accompany the prediction. | REC |
| TC-004 | Output shall retain flow metadata (five-tuple, start time, duration) alongside the prediction for display, separate from model features. | REC |
| TC-005 | Known limitation shall be documented: traffic outside the four classes (e.g., DNS, email, chat) will be forced into one of them unless RID-19 is adopted. | REC |

## 15. PCAP Classification Requirements

| ID | Requirement | Prov. |
|---|---|---|
| PC-001 | Accept an offline `.pcap` file (and `.pcapng` if the verified extractor supports it). | SRC |
| PC-002 | Flow extraction shall go through the CICFlowMeter adapter (TRD §22); no assumed Python API. | SRC + REC |
| PC-003 | Output a per-flow predictions file (CSV/JSON) and a summary (flows per class). | REC |
| PC-004 | Invalid/empty/unsupported PCAPs shall produce clear errors, not crashes or silent empty output. | REC |
| PC-005 | Inference shall refuse to run if feature schema does not match the model's recorded schema. | REC |
| PC-006 | Input PCAPs shall not be copied/retained beyond the run unless explicitly configured. | REC |

## 16. Real-Time Classification Requirements

| ID | Requirement | Prov. |
|---|---|---|
| RT-001 | Live classification is **optional** and delivered only if verified end-to-end. | BRF |
| RT-002 | Capture via Tshark and/or Scapy on a configured interface (requires OS privileges/driver; U-13). | SRC |
| RT-003 | Recommended mechanism: **near-live chunked processing** (rolling PCAP chunks → extractor → classifier), because CICFlowMeter is described by Review-1's own gap analysis as offline/batch (RID-11). | REC |
| RT-004 | The documentation and UI shall **not** claim "real-time" until end-to-end latency has been measured and recorded; until then the term is "near-live". | REC |
| RT-005 | Live mode shall be cleanly stoppable and shall report capture permission errors clearly. | REC |
| RT-006 | Privacy defaults: capture chunks deleted after processing; optional snaplen/BPF filter; no payload persisted by default. | REC |
| RT-007 | Known limitation: flows spanning chunk boundaries are split, which may distort features. | REC |

## 17. Dashboard / Visualization Requirements (optional)

| ID | Requirement | Prov. |
|---|---|---|
| DB-001 | Show dataset class distribution (post-mapping). | BRF |
| DB-002 | Show four-model comparison table and chart from recorded evaluation artifacts. | BRF |
| DB-003 | Show confusion matrix for a selected model. | REC |
| DB-004 | Show PCAP classification results (per-flow table, class distribution). | BRF |
| DB-005 | Show live/near-live results if RT is delivered. | BRF |
| DB-006 | Show five-tuple and key flow features per classified flow (keeps the networking chain visible). | BRF |
| DB-007 | Dashboard reads from `artifacts/` files; no database; runs offline; binds to localhost by default. | REC |
| DB-008 | Dashboard shall display only values read from artifacts; no hard-coded metrics. | REC |

## 18. Evaluation Requirements

| ID | Requirement | Prov. |
|---|---|---|
| EV-001 | Report Accuracy, Precision, Recall, F1-Score. | SRC |
| EV-002 | Report per traffic category plus macro and weighted aggregates. | SRC + REC |
| EV-003 | Report a confusion matrix per model. | REC |
| EV-004 | The model-comparison table shall be generated programmatically from run artifacts. | REC |
| EV-005 | The test set is used only for final evaluation; model/feature/hyperparameter choice uses cross-validation/validation only. | REC |
| EV-006 | Additionally record training time, per-flow inference time, model size (relevant to Review-1's "speed" aim). | REC |
| EV-007 | **No performance number may appear in any document unless produced by a recorded run.** | REC |
| EV-008 | Because dataset-trained models classifying *own* PCAPs have no ground truth, include a small controlled sanity check (captures of known applications, labelled by the team) and describe it as qualitative. | REC |
| EV-009 | Report cross-dataset/split caveats (e.g., session/capture-level leakage risk, U-17). | REC |

## 19. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-001 | **Explainability:** every component must be explainable at viva level; networking concepts visible in code names, docs, and dashboard. |
| NFR-002 | **Simplicity:** minimal dependencies; each added dependency justified in the task report; no over-engineering (see AGENTS.md). |
| NFR-003 | **Reproducibility:** fixed seeds, recorded configs, dataset checksums, library versions, git commit in registry metadata. |
| NFR-004 | **Portability:** runs on the team's target OS (Windows and/or Linux — U-13); OS-specific steps (Npcap, privileges) documented. |
| NFR-005 | **Performance:** measured and reported, never promised a priori; no throughput target is set by Review-1. |
| NFR-006 | **Testability:** automated tests (pytest) for each module; tests that need CICFlowMeter/privileges are explicitly marked and reported as skipped when unavailable — *skipped ≠ passed*. |
| NFR-007 | **Privacy:** payload never used; captured data treated as sensitive; IPs excluded from features and optionally masked in the UI. |
| NFR-008 | **Offline capable:** no cloud/API calls required at runtime. |
| NFR-009 | **Maintainability:** typed, documented functions; structured logging; clear error classes. |

## 20. Constraints
- University project; limited time and compute (laptops).
- Stack fixed by Review-1: Python, Pandas, scikit-learn, XGBoost, Wireshark, Tshark, Scapy, CICFlowMeter. Additional libraries (e.g., joblib, PyYAML, matplotlib, a dashboard library, pytest) are **[REC]** and must be justified.
- Datasets are large third-party files with their own licences; they cannot be assumed present.
- Wireshark is a GUI tool: used for manual inspection/validation, not as a pipeline dependency (Tshark is the scriptable counterpart).
- CICFlowMeter's availability, version and interface are unverified (U-05).

## 21. Limitations (to be stated honestly in the final report)
1. Flow statistics cannot distinguish applications that behave statistically alike; confusion is expected between some classes.
2. Benchmark datasets reflect specific capture environments; generalisation to arbitrary networks is **not** established.
3. Mapping dataset labels to four classes may merge heterogeneous behaviours (U-03).
4. Near-live processing adds latency and splits boundary-spanning flows (RT-007).
5. Out-of-distribution traffic is forced into a known class (TC-005).
6. Results from Review-1's abstract (95–98%) are unverified claims until FlowSentry's own experiments exist.

## 22. Acceptance Criteria
No numerical accuracy threshold is imposed (none is defined by Review-1; U-15). Acceptance is about **verified delivery and honest reporting**.

| ID | Criterion | Verified by |
|---|---|---|
| AC-001 | The Dataset → Target Label Mapping is marked *approved* and every training run records its hash. | CN-004 report |
| AC-002 | A dataset inspection report exists, generated from real files. | CN-003 |
| AC-003 | Preprocessing is fit on training data only; leakage tests pass. | CN-004/005 tests |
| AC-004 | All four models are trained, tuned (CV), and evaluated on the same frozen split. | CN-006…CN-010 |
| AC-005 | Accuracy, Precision, Recall, F1 (per class + aggregates) and confusion matrices are generated programmatically. | CN-010/011 |
| AC-006 | A comparison report names the best model by the pre-declared criterion, with limitations. | CN-011 |
| AC-007 | The best model is stored in the registry with schema, metrics, seeds, checksums. | CN-012 |
| AC-008 | CICFlowMeter version/interface/output format is documented from actual verification, and the adapter works on at least one real PCAP — **or** the fallback decision (RID-10) is formally taken. | CN-013/014 |
| AC-009 | A real PCAP is classified end-to-end, producing per-flow predictions. | CN-015 |
| AC-010 | *If claimed:* live/near-live classification works on a real interface with measured latency recorded; otherwise documented as not delivered. | CN-016/017 |
| AC-011 | *If delivered:* the dashboard shows comparison, PCAP results, and (if available) live results from artifacts only. | CN-018 |
| AC-012 | Integration and end-to-end test reports exist with exact commands and results; skipped tests are listed as skipped. | CN-019/020 |
| AC-013 | A viva-ready demo package and final documentation exist; every stated number traces to an artifact. | CN-021/022 |
