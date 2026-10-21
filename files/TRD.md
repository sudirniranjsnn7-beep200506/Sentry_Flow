# TRD — FlowSentry
**Technical Requirements & Design Document** (companion to `PRD.md`)

| | |
|---|---|
| Authority | Technical authority. If `TRD.md` conflicts with `PRD.md` on *what* is required, `PRD.md` wins; on *how*, `TRD.md` wins. Conflicts are reported, never silently resolved (see `AGENTS.md`). |
| Status | Design only. **No code exists.** Nothing here has been executed or verified against real data, real tools, or a real network. |
| Tags | `[SRC]` from CN Review-1 · `[BRF]` project brief · `[REC]` Recommended Implementation Decision (`RID-xx`, Appendix A) · `[UNRES]` Unresolved (`U-xx`, Appendix B) |
| Verification markers | `VERIFY:` marks any command, flag, API, column name, or file format that **must be confirmed against the real installed tool/dataset before use**. |

---

## 1. System Architecture

### 1.1 Overall pipeline `[SRC][BRF]`
```text
Network Traffic (dataset flows | PCAP | live interface)
        ↓
Flow Generation                 (packets → bidirectional flows)
        ↓
Five-Tuple Flow Grouping        (SrcIP, DstIP, SrcPort, DstPort, Protocol)
        ↓
Flow Feature Extraction         (time / volume / TCP-flag / directional-ratio features)
        ↓
Preprocessing                   (identifier removal, missing values, min-max scaling)
        ↓
Feature Selection
        ↓
ML Model Training               (DT, RF, SVM, XGBoost; tuning via cross-validation)
        ↓
Model Evaluation                (Accuracy, Precision, Recall, F1; held-out test set)
        ↓
Best Model → Model Registry
        ↓
PCAP / Live Traffic Inference
        ↓
Traffic Classification          (Web Browsing | VoIP | Streaming | File Transfer — U-01)
        ↓
Visualization / Dashboard
```

### 1.2 Two operating modes
| Mode | Flow source | Purpose |
|---|---|---|
| **Training mode** | Dataset flow CSVs *or* dataset PCAPs run through the extractor (U-04) | Build, tune, evaluate, register a model |
| **Inference mode** | User PCAP (offline) or capture chunks (near-live) run through the **same** extractor and **same** persisted pipeline | Classify traffic |

The architectural invariant (**feature parity**): the feature vector the model sees at inference must be produced by the same definitions, units, column names, and transformations as at training (FE-008, ML-009).

### 1.3 Style
Single-machine, file-based, CLI-driven Python. No database, no server beyond the optional local dashboard, no message queue, no cloud. Components exchange data through files in `data/` and `artifacts/` and through plain Python function calls.

## 2. Component Architecture

| Component | Package | Responsibility | Networking concept it keeps visible |
|---|---|---|---|
| Common | `common/` | config loading, paths, logging, error classes, schema helpers | — |
| Capture | `capture/` | Tshark/Scapy capture to `.pcap`; chunk rotation | packets, interfaces, BPF filters |
| Flow | `flow/` | extractor interface, CICFlowMeter adapter, optional native fallback, feature normalizer | five-tuple, bidirectional flows, timeouts |
| Preprocessing | `preprocessing/` | ingestion, inspection, label mapping, cleaning, splitting, pipeline construction, feature validation | flow features, identifiers |
| Models | `models/` | the four model specs, training, tuning, registry | — |
| Evaluation | `evaluation/` | metrics, test-set evaluation, comparison, reports | per-class traffic categories |
| Inference | `inference/` | predictor, PCAP classifier, live classifier | PCAP → flows → class |
| Dashboard | `dashboard/` | read-only visualisation of artifacts | five-tuple, flow features |
| Scripts | `scripts/` | thin helper CLIs (e.g., environment verification) | — |
| Tests | `tests/` | unit/integration/e2e tests | — |

```text
capture/ ──pcap──▶ flow/ ──flow CSV──▶ flow/normalizer ──canonical features──▶ inference/predictor ──▶ results files ──▶ dashboard/
dataset ──▶ preprocessing/ ──train/test──▶ models/ ──pipeline──▶ evaluation/ ──▶ models/registry ──▶ inference/predictor
```
Dependency rule: `dashboard` and `inference` may import `common`, `flow`, `models.registry`; **nothing imports `dashboard`**; `models` never imports `evaluation` test-set loaders (structural leakage guard, §19.2).

## 3. Repository Structure `[REC RID-01]`
Modified from the proposed layout: added `common/`, `config/`, `artifacts/`, `docs/`; separated *code* (`models/`) from *outputs* (`artifacts/`).

```text
flowsentry/
├── PRD.md  TRD.md  AGENTS.md  README.md  BUILD_PLAN.md  TASKS.md
├── requirements.txt            # pinned after CN-001 verification
├── .env.example  .gitignore
│
├── config/
│   ├── default.yaml            # paths, seeds, split, CV, thresholds
│   ├── models.yaml             # per-model hyperparameter search spaces
│   ├── feature_schema.yaml     # canonical features, groups, aliases, excluded columns (CN-005)
│   └── label_mapping.yaml      # Dataset → Target label mapping (status: unresolved until approved)
├── common/                     # config.py logging_setup.py errors.py paths.py
├── data/
│   ├── raw/                    # immutable, git-ignored (DS-005/006)
│   ├── processed/              # train/test splits, manifests (git-ignored)
│   ├── sample/                 # tiny, licence-permitting or clearly synthetic
│   └── README.md               # how to obtain datasets, checksums, licences
├── capture/                    # tshark_capture.py scapy_capture.py chunk_manager.py
├── flow/                       # extractor_base.py cicflowmeter_adapter.py native_extractor.py(fallback) normalizer.py
├── preprocessing/              # ingest.py inspect.py label_mapping.py cleaning.py split.py pipeline.py validate_features.py
├── models/                     # base.py decision_tree.py random_forest.py svm.py xgboost_model.py tuning.py train.py registry.py
├── evaluation/                 # metrics.py evaluate.py compare.py report.py
├── inference/                  # predictor.py pcap_classifier.py live_classifier.py
├── dashboard/                  # app.py loaders.py views/
├── scripts/                    # verify_environment.py verify_cicflowmeter.py
├── tests/                      # unit/ integration/ e2e/ fixtures/ conftest.py
├── artifacts/                  # git-ignored: runs/ registry/ reports/ predictions/ live/ logs/
└── docs/                       # verification/ (tool/dataset verification records), task_reports/, decisions/
```
Run everything from the repository root (`python -m package.module`). Packaging (`pyproject.toml`) is optional and only added if imports demand it.

## 4. Data Pipeline

| Stage | Input | Output | Owner task |
|---|---|---|---|
| Ingest | `data/raw/<dataset>/…` | `data/processed/manifest.json` (files, SHA-256, sizes, row counts) | CN-002 |
| Inspect | raw flow files | `artifacts/reports/dataset_inspection.{md,json}` | CN-003 |
| Map labels | raw + `config/label_mapping.yaml` | mapped table + unmapped-label report | CN-004 |
| Clean | mapped table | cleaned table (identifiers dropped, inf→NaN, dedupe) | CN-004 |
| Split | cleaned table | `train` and frozen `test` (row-ID manifest) | CN-004 |
| Validate features | train | `config/feature_schema.yaml` + validation report | CN-005 |
| Train/tune | train only | run directory with pipeline + CV results | CN-006…009 |
| Evaluate | test (once) + run | metrics, confusion matrices | CN-010 |
| Compare | metrics | comparison table + best-model decision | CN-011 |
| Register | best run | registry entry | CN-012 |
| Infer | PCAP/chunks | predictions files | CN-015/017 |

Intermediate tables are CSV by default (transparent, inspectable); Parquet only if size forces it, with the dependency justified `[REC RID-14]`.

## 5. Dataset Handling

### 5.1 Datasets `[SRC]`
ISCX-VPN2016 and CIC-IDS2017 are named in Review-1 as "standard benchmark datasets for evaluating encrypted & application traffic". **Everything below about their contents must be verified from the actual files** — do not rely on memory or on this document.

### 5.2 Handling rules
1. Datasets are downloaded manually by the team (licence/terms checked — U-14); the repo stores no dataset. `data/README.md` records source URL/citation, date, version, licence, file list, SHA-256.
2. `data/raw/` is read-only by convention; code never writes there (DS-005).
3. CN-003 inspects the real files and records: file formats (CSV/ARFF/PCAP), column names and counts, dtypes, label column(s) and every distinct original label with counts, missing/±inf counts, duplicate counts, per-file label distribution, whether capture/session identifiers exist.
4. Whether to train from dataset-provided flow CSVs or from flows regenerated from dataset PCAPs is **U-04**. Trade-off:
   - *Dataset CSVs:* faster, but the feature set/units/names may differ from what the live CICFlowMeter version produces → inference mismatch risk.
   - *Regenerate from PCAP with the chosen extractor:* guarantees parity, but is slow/storage-heavy and requires PCAP access and labels per capture.
   - **Decision gate at CN-003/CN-013:** the canonical feature set must be a subset computable by the *inference-time* extractor with verified identical semantics.
5. Whether a dataset is usable for the four target classes at all depends on §6. In particular, a dataset organised around attack/benign intrusion labels may not contain application-category labels; this is a **risk to be checked at CN-003**, not an assumption (U-02).

## 6. Dataset → Target Label Mapping `[BRF][UNRES]`

> **Status: To be finalized before model training.** Review-1 names two datasets and four target classes but gives **no mapping** between them. This section defines the structure, the process and the gate; it deliberately contains **no invented mappings**.

### 6.1 Target classes (U-01)
| Source | Classes |
|---|---|
| Review-1 p.2 "Output Classes" | Web Browsing, VoIP, Streaming, File Transfer |
| Review-1 p.2 architecture figure | "Web / VoIP / Media" (abbreviated; 3 labels) |
| FlowSentry working assumption | The four-class list. **Whether "Media" = "Streaming" and whether the figure is simply abbreviated is to be confirmed by the team (U-01).** |

### 6.2 Mapping register
| Source dataset | Original label(s) | FlowSentry target class | Mapping status | Required transformation | Unresolved issues | Verification required |
|---|---|---|---|---|---|---|
| ISCX-VPN2016 | *To be extracted from the real files at CN-003* | *To be decided by team* | UNRESOLVED | Explicit `original → target` or `DROP` entries in `config/label_mapping.yaml` | Whether VPN and non-VPN variants map to the same target class (U-16); whether labels derive from file names vs. a label column | Print distinct labels with counts; team review of every entry; row counts before/after |
| CIC-IDS2017 | *To be extracted from the real files at CN-003* | *To be decided by team* | UNRESOLVED | As above | Whether this dataset contains any application-category labels usable for the four targets, or only intrusion-type labels (U-02) | Same; if no valid mapping exists, document the dataset's role (or exclusion) explicitly |
| Combined use | — | — | UNRESOLVED | Union only after per-dataset mapping is approved | Domain shift between datasets; feature-schema parity between them (U-04) | Report per-dataset results separately before any pooling |

### 6.3 Mapping file contract (`config/label_mapping.yaml`) — template only
```yaml
status: unresolved            # unresolved | draft | approved   (training refuses unless "approved")
approved_by: null             # team member names, filled by humans
approved_on: null
target_classes: []            # to be finalized before model training (U-01)
datasets:
  ISCX-VPN2016:
    label_column: null        # VERIFY from real files at CN-003
    mapping: {}               # original_label: target_class | DROP   (no entries invented)
  CIC-IDS2017:
    label_column: null
    mapping: {}
```

### 6.4 Rules
1. `preprocessing/label_mapping.py` refuses to run (raises `LabelMappingError`) unless `status: approved`.
2. Every original label found in the data must be either mapped or explicitly `DROP`; an **unlisted label is an error**, not silently dropped (DS-007).
3. The SHA-256 of the mapping file is stored in every run and registry entry (AC-001).
4. After mapping, a per-class count table is produced; a class below a minimum sample count (threshold decided by the team, not assumed) triggers a documented decision (merge, drop, or collect more data).
5. Agents must **never** propose or guess entries to "make it work"; they may list candidate decisions for human approval, clearly labelled as candidates.

## 7. Five-Tuple Flow Model `[SRC]`

### 7.1 Definitions
- **Five-tuple:** (Source IP, Destination IP, Source Port, Destination Port, Protocol).
- **Flow:** the set of packets sharing a five-tuple within the extractor's timeout rules.
- **Bidirectional flow:** packets of the *reverse* five-tuple (src/dst swapped) are assigned to the same flow. The **forward** direction is conventionally the direction of the first packet observed (the initiator); the reverse is **backward**. *VERIFY the exact convention for the chosen extractor version.*

### 7.2 Why this matters to classification
Payload is not used. What remains observable per flow is *how* endpoints exchange packets: sizes, directions, timing, flag usage. VoIP tends toward small, regular packets; bulk transfer toward large packets/sustained volume; streaming toward asymmetric sustained flow; web browsing toward short bursty request/response exchanges. *(These are textbook intuitions to motivate the features — not claims about the datasets; actual separability is an experimental result.)*

### 7.3 Flow termination (extractor-defined — `VERIFY`)
TCP: FIN/RST handling; all protocols: inactivity (flow) timeout and possibly maximum flow duration. Timeout values are extractor parameters; their defaults must be read from the installed version's documentation/source and recorded in `docs/verification/cicflowmeter.md` — **no default value is assumed here**. Active/Idle statistics depend on an idle-threshold parameter likewise.

### 7.4 Scope of protocols
TCP and UDP flows are the expected focus (Protocol field in five-tuple). Handling of ICMP/other protocols and fragments is U-11; default behaviour: log and exclude from classification, reporting the excluded count.

## 8. Flow Generation

| Path | Mechanism | Notes |
|---|---|---|
| Dataset-provided flows | read flow CSVs (U-04) | no generation step |
| Dataset PCAP | PCAP → extractor adapter → flow CSV | parity guaranteed with inference |
| User PCAP | PCAP → extractor adapter → flow CSV | CN-014/015 |
| Live | rolling capture chunks → extractor adapter → flow CSV | CN-016/017 |

All generation passes through `flow.extractor_base.FlowExtractor` (§22). The extractor returns a flow CSV; the **normalizer** (§9.3) turns it into the canonical feature table.

## 9. Feature Extraction `[SRC]`

### 9.1 Feature groups (names from Review-1; exact columns `VERIFY`)
| Group | Review-1 examples | Notes |
|---|---|---|
| Time-based | Flow Duration, IAT mean (and other IAT stats), Active & Idle time stats | units (µs vs s) must be verified |
| Volume | Total Fwd/Bwd packets, total bytes, average packet size | forward/backward semantics per §7.1 |
| TCP flag | SYN, ACK, FIN, PSH counts, header-length ratios | meaningless for UDP (expect zeros) — note |
| Directional ratios | directional packet ratios (abstract) | may be derived by the normalizer if not emitted directly; if derived, document the formula |

Review-1 states CICFlowMeter yields "80+" metrics; the real count/names are determined at CN-003 (dataset) and CN-013 (extractor) `[UNRES U-05]`.

### 9.2 Metadata vs features
Columns are partitioned in `config/feature_schema.yaml`:
- `features:` model inputs (numeric).
- `metadata:` Flow ID, five-tuple, timestamps — retained for display/audit, **never** model input (ML-004, FE-007).
- `label:` target column (training only).
- `excluded:` everything else, with a reason (constant, leakage-prone, identifier, unverifiable).

### 9.3 Feature normalizer (`flow/normalizer.py`)
Input: raw extractor CSV (or dataset CSV). Steps:
1. Header normalisation (trim whitespace; case rules *only if verified necessary*).
2. Alias mapping `raw_name → canonical_name` from the schema.
3. Unit/semantic conversion where verified to differ.
4. Derive missing derived features (documented formulas) if any.
5. Assert required canonical features exist (else `SchemaMismatchError` listing missing/extra columns).
6. Return canonical features + metadata separately.

### 9.4 Parity verification (CN-013/014)
If dataset PCAPs are available: run the extractor on one, compare resulting feature distributions/definitions against the dataset-provided CSV for the same traffic. Differences are documented; features that disagree in semantics/units are **excluded or converted**, not ignored.

## 10. Feature Preprocessing `[SRC][REC]`

### 10.1 Deterministic cleaning (safe before splitting — learns nothing from data)
1. Apply label mapping (§6).
2. Drop `metadata`/identifier columns from model input (IP, MAC, IDs, timestamps).
3. Replace ±inf with NaN (and count them).
4. Remove **exact duplicate rows** *before* splitting (prevents the same row landing in both splits); record counts `[RID-04]`.
5. Port policy `[RID-07]`: Source Port and Destination Port are **excluded from model input by default**, because Review-1's motivation is that ports are unreliable and a port feature would let the model recreate port-based classification. An ablation including Destination Port may be run and *reported separately* if the team wants.

### 10.2 Learned transformations (inside the persisted pipeline, fit on training data only)
1. **Missing-value strategy:** Review-1 says "handles missing values" without a method. Recommended: median imputation fit on train; rows/columns with excessive missingness handled by a documented threshold decided at CN-003. `[RID-03]`
2. **Min-max scaling** `[SRC]`: `MinMaxScaler` fit on train; test/inference values outside the training range are clipped or flagged per documented policy (decision at CN-004; default: allow, no clipping, log count out-of-range).
3. Order: `imputer → scaler → feature selector → classifier`, one scikit-learn `Pipeline` object `[RID-03]`.

Tree-based models do not need scaling, but one uniform pipeline is used for all four models so that the comparison isolates the classifier, and so that Review-1's min-max step is satisfied once, identically.

### 10.3 Class labels
Target classes are string labels in the mapping; models receive integer-encoded labels via a `LabelEncoder` fitted on training labels and stored in the registry (XGBoost requires integer classes).

## 11. Feature Selection `[SRC][REC RID-08]`
Review-1 requires feature selection "to optimize speed and accuracy" but gives no method (U-10). Recommended staged approach, all **fit inside training folds**:
1. Drop constant / near-zero-variance features.
2. Drop one of each highly-correlated pair (threshold in config).
3. Rank by a model-based importance (e.g., Random Forest importance) and keep top-*k* (*k* tuned by CV or fixed in config).

Outputs: ordered selected-feature list per run, stored with the pipeline and in registry metadata (documented transformation, AGENTS.md ML rules). A comparison "all features vs selected" is recommended for the final report (the viva will ask).

## 12. ML Training Architecture `[SRC]`

```text
train split ──▶ build_pipeline(model_spec) ──▶ tuning (CV on train) ──▶ refit on full train ──▶ run artifacts
                         ▲
        config/models.yaml (search spaces) + config/default.yaml (seed, CV)
```
- `models/base.py` defines `ModelSpec(name, estimator_factory, param_space, notes)`.
- `models/train.py`: `python -m models.train --model {decision_tree|random_forest|svm|xgboost} --config config/default.yaml`.
- **Structural leakage guard:** training code receives only the *training* table; the loader for the test table lives in `evaluation/` and is never imported by `models/` (checked by a test).
- Run directory `artifacts/runs/<run_id>/`: `config_snapshot.yaml`, `label_mapping.sha256`, `cv_results.csv`, `best_params.json`, `pipeline.joblib`, `selected_features.json`, `train_info.json` (seed, durations, library versions, git commit, dataset manifest hash), `metrics_cv.json`.

## 13. Decision Tree
- scikit-learn `DecisionTreeClassifier` (`VERIFY` installed version/parameters).
- Tunable: split criterion, max depth, min samples split/leaf, class weighting (names per installed API).
- Value to the project: interpretable; export human-readable rules / depth for viva discussion; strong baseline.
- Risk: overfitting with unlimited depth — depth/leaf limits in the search space.

## 14. Random Forest
- scikit-learn `RandomForestClassifier`.
- Tunable: number of trees, max depth, max features, min samples leaf, class weighting.
- Outputs feature importances (also useful for §11 and explaining *which networking features matter*).
- Cost: memory/time grow with trees and dataset size; budget limit in config.

## 15. SVM `[REC RID-06]`
- scikit-learn `SVC` (kernel methods) — scale-sensitive (the pipeline's min-max scaling is required, not optional).
- Tunable: kernel, `C`, `gamma`, class weighting.
- **Scalability risk:** kernel SVM training time grows super-linearly with samples; flow datasets can be very large. Recommended policy: tune on a **stratified training subsample** (fraction in config), and/or evaluate `LinearSVC` as a documented variant. *Whatever is done must be disclosed in the comparison* (ML-012). The test set is never subsampled.
- Probability outputs are expensive (`probability=True` adds internal CV); default off; use decision-function margins as a confidence proxy only if documented.

## 16. XGBoost
- `xgboost.XGBClassifier`, multi-class (`multi:softprob`-style objective — `VERIFY` against installed version).
- Tunable: number of estimators, max depth, learning rate, subsample ratios, regularisation.
- `VERIFY`: XGBoost's scikit-learn-wrapper API has changed across versions (e.g., where early stopping is configured); consult the installed version and record it. Do not copy parameter names from memory.
- Labels must be integers (§10.3); class imbalance via sample weights computed on training data.
- Early stopping, if used, needs a validation split carved **from training data only**.

## 17. Hyperparameter Tuning `[SRC]`
- Method: `GridSearchCV` for small spaces, `RandomizedSearchCV` for larger ones (config chooses; budget `n_iter` in config).
- Scoring: macro-F1 (robust to imbalance) `[RID-20]`; accuracy and weighted-F1 also recorded.
- The **full pipeline** (imputer → scaler → selector → model) is what is cross-validated, so scaling/selection are re-fit per fold (no leakage through preprocessing).
- All trials saved to `cv_results.csv`. Search spaces live in `config/models.yaml`; initial values are starting points, not validated optima.

## 18. Cross-Validation `[SRC][REC RID-05, RID-21]`
- `StratifiedKFold` (shuffle with config seed); default 5 folds (U-09).
- If the dataset exposes capture/session/file identifiers, use **group-aware** CV and splitting so flows from one capture session cannot appear on both sides (U-17). Rationale: consecutive flows from the same capture session are highly correlated; random flow-level splitting can inflate scores. CN-003 must report whether such identifiers exist.
- Cross-validation happens **only within the training set**.

## 19. Model Evaluation `[SRC]`

### 19.1 Metrics
Accuracy; Precision, Recall, F1 **per class**; macro and weighted averages; confusion matrix; plus training time, per-flow inference time, model size `[RID-15]`.

### 19.2 Protocol
1. Test set created once at CN-004 (stratified; ratio in config — U-09), stored with a row-ID manifest and a hash.
2. Test data is loaded only through `evaluation.load_test_set(purpose="final_evaluation")`, which writes an audit-log line.
3. Models are evaluated on test exactly once per final run; if re-evaluated after any change, that fact is logged, and the repeated-peeking caveat is stated in the report.
4. Model/feature/hyperparameter decisions use CV results only.

### 19.3 Outputs
`artifacts/reports/<run_id>/metrics.json`, `classification_report.csv`, `confusion_matrix.csv/.png`; `artifacts/reports/comparison.{csv,md,png}` (generated, never hand-typed).

### 19.4 Best-model selection criterion `[REC RID-20]`
Declared **before** evaluation: highest macro-F1 in cross-validation; ties broken by simpler/faster model. The test-set results are then reported *for the chosen and all models* but not used to pick. (If the team prefers selecting on test, that must be disclosed — not recommended.)

### 19.5 Reporting rules
Every number in a report links to its artifact file; limitations from PRD §21 are reproduced; Review-1's 95–98% claim is neither assumed nor targeted (U-08).

## 20. Model Registry `[REC RID-16]`
File-based, no database.
```text
artifacts/registry/
├── registry.json                 # index: entries[], active_model_id
└── <model_id>/                   # e.g. <model_name>_<timestamp>_<short-hash>
    ├── pipeline.joblib           # full fitted pipeline (+ label encoder)
    ├── metadata.json
    ├── feature_schema.json       # copy of canonical schema used
    ├── label_mapping.json        # copy + sha256
    ├── metrics.json              # test + CV metrics (from artifacts only)
    └── env.json                  # python, sklearn, xgboost, pandas versions, git commit
```
`metadata.json` fields: model name, run id, created time, seed, dataset manifest hash, label-mapping hash, split manifest hash, selected features, class list, artifact SHA-256, selection criterion, intended-use and limitations text.
Rules: loading verifies SHA-256 and warns on library-version mismatch; `joblib` (pickle) files are loaded **only from the local trusted registry**, never from uploads; inference refuses to run if the incoming schema ≠ `feature_schema.json` (FE-008).

## 21. PCAP Inference `[SRC][BRF]`
```text
PCAP → [validate file] → FlowExtractor (CICFlowMeter adapter) → flow CSV
     → Feature Normalizer → schema-parity check → registry pipeline.predict (+ confidence if available)
     → predictions.csv/json + summary.json
```
- CLI: `python -m inference.pcap_classifier --pcap <file> --model-id <id|active> --out artifacts/predictions/<name>/`.
- Output columns: flow metadata (five-tuple, start time, duration), predicted class, confidence (if available).
- Summary: flows per class, excluded-flow counts and reasons, model id, extractor version, run time.
- Errors: missing/corrupt/empty PCAP, extractor unavailable, zero flows, schema mismatch → typed errors with actionable messages (§26).
- Temp files in a configured temp dir; deleted unless `keep_intermediate: true` (PC-006).

## 22. CICFlowMeter Integration `[SRC][UNRES U-05]`

**Never assume a Python API exists.** Review-1 lists CICFlowMeter as "(Java / Python)" without specifying which implementation, version, or interface; several implementations/ports exist, and their command-line interfaces and CSV outputs may differ. Therefore:

```text
PCAP → CICFlowMeter (external process) → Flow CSV → Feature Normalizer → ML Pipeline → Prediction
```

### 22.1 Adapter interface
```python
class FlowExtractor(Protocol):        # flow/extractor_base.py (design sketch, not implementation)
    name: str
    def verify_available(self) -> ExtractorInfo: ...         # version, path, raises ExtractorUnavailableError
    def extract(self, pcap_path: Path, out_dir: Path) -> Path: ...  # returns flow CSV path
```
`CICFlowMeterAdapter` invokes the tool as an **external process** (`subprocess` with an argument list — never `shell=True`), using a command template stored in config (`cicflowmeter.command_template`, placeholders for input/output paths). The template is **empty until CN-013 verifies it**.

### 22.2 Verification protocol (CN-013) — record in `docs/verification/cicflowmeter.md`
Which implementation and where obtained; version; language/runtime (e.g., Java version if Java); OS; install steps actually performed; the exact command that worked; output file naming; **CSV header (verbatim) and column count**; sample row; unit conventions; flow/activity timeout parameters and defaults; handling of non-TCP/UDP; `.pcap` vs `.pcapng` support; behaviour on empty/corrupt PCAP; run time on a sample PCAP.

### 22.3 Contingency `[REC RID-10]`
If no CICFlowMeter implementation can be installed/run on the team's machines: implement a **project-native Scapy extractor** (`flow/native_extractor.py`) producing a *documented subset* of the same feature families; training must then use features produced by that same extractor (dataset PCAPs required). Adopting this fallback is a **team decision recorded in `docs/decisions/`** (it changes scope and weakens "uses CICFlowMeter" from Review-1), not an agent decision.

## 23. Live Traffic Classification `[SRC][BRF][optional]`

### 23.1 Approach `[REC RID-11]`
Review-1's own gap analysis describes CICFlowMeter-style extraction as offline/batch. FlowSentry therefore targets **near-live** classification:
```text
Interface → Tshark/Scapy ring-buffer capture (time- or size-rotated chunks)
          → completed chunk → FlowExtractor → Normalizer → Predictor
          → append to artifacts/live/predictions.jsonl → (optional) dashboard
          → delete chunk (default)
```

### 23.2 Capture tooling (`VERIFY` all flags/APIs on the target OS before use)
- Tshark: interface selection (`-i`), write file (`-w`), ring-buffer (`-b duration:…`, `-b files:…`), capture filter (`-f`), snapshot length (`-s`). Confirm with `tshark -h` on the installed version.
- Scapy: sniffing and PCAP writing utilities exist; confirm names/behaviour for the installed version.
- Prerequisites: packet-capture driver (e.g., Npcap on Windows) and capture privileges (U-13). Missing privileges → `CaptureError` with clear guidance.

### 23.3 Behaviour & limits
- A chunk still being written must not be processed; process completed chunks only (`VERIFY` how the chosen tool signals completion).
- Flows spanning chunk boundaries are split → partial-flow features (RT-007). Chunk duration trades latency against fragmentation (config).
- Latency measured per chunk: (chunk close time → prediction written), plus per-flow inference time, logged. **The word "real-time" is prohibited in docs/UI until latency data exists (RT-004).**
- Privacy defaults `[RID-18]`: capture only on an interface the team is authorised to monitor; optional BPF filter; optional snaplen to avoid storing payload; delete chunks after processing; no payload persisted. If snaplen truncation is used, `VERIFY` the extractor still computes lengths correctly (captured vs original length).
- Graceful stop (signal/KeyboardInterrupt) flushes the last chunk and exits cleanly.

## 24. Dashboard Architecture `[BRF][REC RID-09]`
- Technology: **Streamlit** recommended (Python-only, minimal code, easy to demo) — alternative Flask/Dash; decision U-12. Dependency added only at CN-018.
- Read-only over `artifacts/`; no database; binds `localhost` by default.
- Views: (1) Dataset & class distribution; (2) Model comparison (table + bar chart); (3) Confusion matrix; (4) PCAP classification (upload or select file → per-flow table, class distribution, five-tuple + key features); (5) Live/near-live monitor (auto-refresh reading `predictions.jsonl`, timeline, class counts, measured latency) — only if §23 delivered.
- Option to mask IPs in display (privacy); metrics shown only from artifacts (DB-008).
- A "How it works" page showing Packets → Five-Tuple → Flow → Features → ML → Class, for viva clarity.

## 25. Configuration `[REC RID-13]`
`config/default.yaml` (illustrative keys; values decided at implementation):
```yaml
seed: <int>
paths: { data_raw, data_processed, artifacts, tmp }
split: { test_fraction: <U-09>, stratify: true, group_column: <null|name, U-17> }
cv: { folds: <U-09>, shuffle: true }
preprocessing: { drop_duplicates: true, missing_strategy: <decide at CN-003>, port_features: excluded }
feature_selection: { variance_threshold, correlation_threshold, top_k }
svm: { subsample_fraction: <decide> }
cicflowmeter: { command_template: "", expected_version: "", timeout_seconds: <int> }   # empty until CN-013
capture: { interface: "", chunk_seconds: <int>, bpf_filter: "", snaplen: <null|int>, keep_chunks: false }
dashboard: { host: "127.0.0.1", port: <int>, mask_ips: true }
logging: { level: INFO, file: artifacts/logs/flowsentry.log }
```
`.env.example` holds machine-specific values only (e.g., `FLOWSENTRY_DATA_DIR`, `CICFLOWMETER_PATH`, `CAPTURE_INTERFACE`); no secrets are required by this project, and `.env` is git-ignored.

## 26. Error Handling `[REC]`
Typed exceptions in `common/errors.py`: `ConfigError`, `DatasetError`, `LabelMappingError`, `SchemaMismatchError`, `ExtractorUnavailableError`, `ExtractionError`, `ModelNotFoundError`, `RegistryIntegrityError`, `CaptureError`, `LeakageGuardError`.
Principles: **fail closed** (schema mismatch, unapproved mapping, missing model ⇒ stop); never silently drop data (always count and report); CLI exits non-zero with a one-line cause and a pointer to the log; unavailable optional tools produce a clear "not available" state, never a fake result.

## 27. Logging `[REC]`
Python `logging`, console + rotating file in `artifacts/logs/`. Structured key=value messages. Log: stage start/end, row counts before/after each cleaning step, seeds, config hash, library versions, subprocess command (arguments, not captured data), durations, test-set access audit lines. Do **not** log packet contents; log five-tuples only at DEBUG.

## 28. Testing `[REC RID-17]`
`pytest`. Markers: `requires_dataset`, `requires_cicflowmeter`, `requires_capture` — tests with unmet prerequisites are **skipped and reported as skipped**, never counted as passed.

| Layer | Examples (minimum) |
|---|---|
| Unit | label-mapping refuses unapproved status / unlisted label; cleaning counts; scaler fit on train only (fit data identity check); schema validator; normalizer alias mapping; metrics vs hand-computed tiny example; registry round-trip + checksum; config loading |
| Leakage | `models/` does not import test loaders; train/test row-ID sets disjoint; no duplicate rows across splits; group disjointness if groups exist |
| Adapter | CICFlowMeter adapter with a mocked subprocess (command construction, error mapping); real run only under `requires_cicflowmeter` |
| Integration | dataset→train→evaluate on **tiny synthetic fixtures** (clearly labelled synthetic; used for plumbing, not for results); PCAP generated with Scapy in test → extractor (if available) → predict |
| E2E | real PCAP → class predictions; live capture smoke test under `requires_capture` |
Synthetic data must never be used to report model performance.

## 29. Reproducibility `[REC]`
Seeds from config for split, CV, models; dataset SHA-256 manifest; label-mapping hash; split row-ID manifest; pinned `requirements.txt`; `env.json` with versions and git commit; config snapshot per run; deterministic run IDs; a documented "reproduce results" command sequence in `README.md` (filled after implementation). Note: some algorithms/parallelism may produce small run-to-run differences — record and state if observed.

## 30. Security and Privacy Considerations
- **No payload use** (FR-002); features are flow statistics. Header-derived metadata (IPs/ports) is excluded from model input.
- Captured traffic and PCAPs are **potentially sensitive** (may contain credentials/PII in payloads and identifying addresses). Capture only on networks/devices the team owns or is authorised to monitor; minimise retention (chunk deletion, snaplen, BPF filters); never commit PCAPs/captures; `.gitignore` enforces it.
- Dashboard binds to localhost, offers IP masking, and has no authentication (documented limitation; academic scope).
- Uploaded PCAPs: size limit, temp directory, never executed, filename sanitised, never interpolated into a shell command.
- `joblib`/pickle loading only from the trusted local registry.
- Respect dataset licences/terms; cite datasets properly.

## 31. Known Limitations
See PRD §21. Additionally (technical): unverified CICFlowMeter details (U-05); feature-schema parity risk between dataset CSVs and live extractor (U-04); label-mapping uncertainty (U-03); possible session-level leakage (U-17); SVM subsampling effects; boundary-split flows in near-live mode; forced classification of out-of-scope traffic; no performance numbers exist yet.

---

# Appendix A — Recommended Implementation Decisions (not in Review-1)

| ID | Decision | Rationale | Reversible by |
|---|---|---|---|
| RID-01 | Repository layout per §3 (added `common/ config/ artifacts/ docs/`) | separates code/config/outputs | team |
| RID-02 | Python 3.10+ (`VERIFY` against team machines and library support at CN-001) | library compatibility | team |
| RID-03 | One scikit-learn `Pipeline` (imputer → min-max scaler → selector → model), persisted with `joblib` | train/inference parity | team |
| RID-04 | Stratified train/test split frozen by row-ID manifest; deduplicate before split | prevents leakage via duplicates | team |
| RID-05 | Stratified 5-fold CV for tuning (configurable) | standard practice | team |
| RID-06 | SVM: tune on stratified training subsample and/or `LinearSVC` variant, disclosed | kernel SVM scalability | team |
| RID-07 | Port features excluded from model input by default; optional reported ablation | avoids recreating port-based classification | team |
| RID-08 | Feature selection: variance → correlation → importance top-k, fit in-fold | Review-1 gives no method | team |
| RID-09 | Streamlit dashboard | minimal, Python-only | team |
| RID-10 | Extractor adapter + contingency native Scapy extractor (team approval needed) | de-risks U-05 | team |
| RID-11 | Live mode = near-live chunked processing | extractor is batch-oriented | team |
| RID-12 | `argparse` CLIs run as `python -m …` | simple, explainable | team |
| RID-13 | YAML config + `.env` | externalised settings | team |
| RID-14 | CSV/JSON/JSONL file artifacts; no DB; Parquet only if justified | simplicity | team |
| RID-15 | Additional metrics: macro/weighted F1, confusion matrix, timings, size | comparison depth | team |
| RID-16 | File-based model registry with checksum | no DB needed | team |
| RID-17 | pytest with prerequisite markers | explicit skipped-vs-passed | team |
| RID-18 | Capture privacy defaults (delete chunks, optional BPF/snaplen) | sensitive data | team |
| RID-19 | Optional "Uncertain/Other" via confidence threshold for out-of-distribution flows | TC-005 | team (optional) |
| RID-20 | Best model = highest CV macro-F1, tie → simpler/faster; decided before test eval | avoids test-set selection | team |
| RID-21 | Group-aware split/CV if capture/session identifiers exist | leakage risk | team |

# Appendix B — Unresolved / To Be Finalized

| ID | Item | Blocks | Resolve at |
|---|---|---|---|
| U-01 | Target class set: four classes vs the figure's "Web / VoIP / Media"; is "Media" = "Streaming"? | CN-004 | before CN-004 |
| U-02 | Role of each dataset (primary? both? is CIC-IDS2017 usable for application classes?) | CN-002/004 | CN-003 |
| U-03 | Original labels and the approved Dataset → Target mapping | CN-004 (training) | after CN-003 |
| U-04 | Train from dataset CSVs vs regenerate flows from dataset PCAPs; feature-schema parity | CN-005/013 | CN-003/013 |
| U-05 | CICFlowMeter implementation, version, runtime, command, output header, timeouts | CN-013 onward | CN-013 |
| U-06 | Is live classification feasible; definition of acceptable latency | CN-016/017 | CN-016 |
| U-07 | Review-1 problem statement/objectives text truncated in supplied PDF | PRD wording | team check |
| U-08 | Review-1's 95–98% accuracy claim — unverified; not an acceptance threshold | final report | CN-010/022 |
| U-09 | Test fraction, number of CV folds | CN-004 | CN-004 |
| U-10 | Feature selection method confirmation (RID-08) | CN-005 | CN-005 |
| U-11 | Handling of non-TCP/UDP flows and out-of-scope traffic | CN-015 | CN-014 |
| U-12 | Dashboard technology confirmation (RID-09) | CN-018 | CN-018 |
| U-13 | Team OS/hardware, capture privileges, drivers for live capture | CN-001/016 | CN-001 |
| U-14 | Dataset availability, licence, size, storage location, sample inclusion | CN-002 | CN-002 |
| U-15 | No minimum-performance acceptance threshold defined | final eval | team |
| U-16 | VPN vs non-VPN / encrypted-tunnel variants: same or separate target classes | CN-004 | after CN-003 |
| U-17 | Session/capture-level leakage: are group identifiers available? | CN-004 | CN-003 |

# Appendix C — Traceability (requirement group → TRD section → tasks)

| PRD group | TRD sections | Tasks |
|---|---|---|
| FR-001…013 | 1, 2, 4, 8, 21, 23, 24 | CN-001, 014–018 |
| ML-001…012 | 10–18 | CN-004, 006–009 |
| DS-001…008 | 4–6 | CN-002–004 |
| FE-001…010 | 9, 10, 22 | CN-005, 013 |
| TC-001…005 | 6, 21 | CN-004, 015 |
| PC-001…006 | 21, 22 | CN-013–015 |
| RT-001…007 | 23 | CN-016, 017 |
| DB-001…008 | 24 | CN-018 |
| EV-001…009 | 19 | CN-010, 011, 020 |
| NFR-001…009 | 25–30 | all; CN-019–022 |
