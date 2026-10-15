# TASKS — FlowSentry
**Implementation task authority.** One task at a time, in order, per `BUILD_PLAN.md`. Obey `AGENTS.md` (anti-hallucination, ML/network rules, mandatory Task Report saved to `docs/task_reports/CN-xxx.md`).

Status legend for each task: `NOT STARTED` → `IN PROGRESS` → `DONE` / `DONE WITH UNVERIFIED ITEMS` / `BLOCKED`. All tasks are currently **NOT STARTED**.

Global "Do Not" (applies to every task): do not start another task; do not touch files outside the listed ones; do not add unjustified dependencies; do not invent labels/columns/APIs/commands/results; do not commit data, PCAPs, models, `.env`, `artifacts/`; do not use payload content; do not report skipped tests as passed.

| Task | Phase | Name | Depends on |
|---|---|---|---|
| CN-001 | 1 | Repository Foundation | — |
| CN-002 | 2 | Dataset Ingestion | CN-001 |
| CN-003 | 2 | Dataset Inspection | CN-002 |
| CN-004 | 2 | Preprocessing | CN-003 + **G-LABEL** |
| CN-005 | 2 | Feature Validation | CN-004 |
| CN-006 | 3 | Decision Tree | CN-005 |
| CN-007 | 3 | Random Forest | CN-006 |
| CN-008 | 3 | SVM | CN-006 |
| CN-009 | 3 | XGBoost | CN-006 |
| CN-010 | 4 | Evaluation | CN-006…009 |
| CN-011 | 4 | Model Comparison | CN-010 |
| CN-012 | 5 | Model Registry | CN-011 |
| CN-013 | 6 | CICFlowMeter Integration | CN-001 (+ **G-CFM**) |
| CN-014 | 6 | PCAP Flow Extraction | CN-005, CN-013 |
| CN-015 | 6 | PCAP Inference | CN-012, CN-014 |
| CN-016 | 7 | Live Capture | CN-015 |
| CN-017 | 7 | Real-Time Inference | CN-016 |
| CN-018 | 8 | Dashboard | CN-011, CN-012, CN-015 (CN-017 optional) |
| CN-019 | 9 | Integration Testing | CN-015 (+CN-017, CN-018 if delivered) |
| CN-020 | 9 | End-to-End Testing | CN-019 |
| CN-021 | 10 | Demo Packaging | CN-020 |
| CN-022 | 10 | Final Documentation | CN-021 |

---

## CN-001 — Repository Foundation
- **Task ID:** CN-001 · **Task Name:** Repository Foundation
- **Goal:** Create the repository skeleton (TRD §3), config/logging/error infrastructure, dependency file, environment verification script, and a passing test harness.
- **Why It Is Needed:** Every later task builds on a stable, importable, tested base. Covers FR-011, FR-012, NFR-003, NFR-004, NFR-006, NFR-009; surfaces U-13 early.
- **Dependencies:** Phase 0 complete (documents present; decision log started).
- **Files/Directories:** `requirements.txt`, `.env.example`, `.gitignore`, `config/default.yaml`, `common/{config,logging_setup,errors,paths}.py`, package `__init__.py` files in all code packages, `scripts/verify_environment.py`, `tests/conftest.py`, `tests/unit/test_common.py`, `data/README.md`, empty `data/{raw,processed,sample}/`, `docs/{verification,task_reports,decisions}/`.
- **Implementation Requirements:**
  1. Create the structure in TRD §3 (placeholders only for later packages).
  2. `requirements.txt` with only: pandas, scikit-learn, xgboost, scapy, PyYAML, joblib, matplotlib, pytest (Review-1 stack + minimal [REC] helpers). **Install in a virtual environment and pin the versions actually installed.** Justify each non-Review-1 package in the report. No dashboard library yet.
  3. `common/config.py`: load YAML + `.env` overrides; validate required keys; `ConfigError` on problems.
  4. `common/errors.py`: all exception classes in TRD §26.
  5. `common/logging_setup.py`: console + rotating file in `artifacts/logs/`.
  6. `.gitignore`: `data/raw`, `data/processed`, `artifacts/`, `*.pcap`, `*.pcapng`, `.env`, `__pycache__`, virtualenvs, `*.joblib`.
  7. `scripts/verify_environment.py`: print Python version, OS, installed library versions, and **report availability** of `tshark`, `java`, and (best-effort) capture privileges; never fail merely because optional tools are absent.
  8. `pytest` markers registered: `requires_dataset`, `requires_cicflowmeter`, `requires_capture`.
- **Do Not:** write dataset/ML/flow code; assume tshark/Java exist; hard-code paths; add Docker/CI.
- **Verification:** `python -m venv` + install from `requirements.txt`; `pytest -q`; `python scripts/verify_environment.py`; confirm `.gitignore` ignores a dummy `.pcap` and `.env`; confirm `python -c "import common.config"` from repo root.
- **Expected Output:** Repo skeleton; passing tests; environment report text saved into the task report (shows actual tool availability → feeds U-13).
- **Definition of Done:** All verification commands run with real outputs recorded; requirements pinned; Task Report saved.

## CN-002 — Dataset Ingestion
- **Task ID:** CN-002 · **Task Name:** Dataset Ingestion
- **Goal:** Register the datasets the humans placed in `data/raw/` and produce a checksummed manifest.
- **Why It Is Needed:** Provenance and reproducibility (DS-003, DS-005, NFR-003); establishes what data actually exists (U-14).
- **Dependencies:** CN-001; humans have downloaded dataset(s) per `data/README.md` and recorded source/licence.
- **Files/Directories:** `preprocessing/ingest.py`, `data/README.md`, `data/processed/manifest.json` (generated), `tests/unit/test_ingest.py`, `tests/fixtures/` (tiny synthetic files, labelled synthetic).
- **Implementation Requirements:**
  1. CLI `python -m preprocessing.ingest --raw-dir data/raw --out data/processed/manifest.json`.
  2. For every file: relative path, size, SHA-256, detected format (by extension + light sniff), and for CSV: row count and header (streamed, not fully loaded unless small).
  3. Never modify `data/raw/`. Flag unreadable/unknown files rather than skipping silently.
  4. `data/README.md`: instructions for humans to record dataset name, URL/citation, version/date, licence, acquisition date (fields left blank for humans — do not fill from memory).
- **Do Not:** download datasets automatically; guess licences; parse labels yet; commit data.
- **Verification:** Unit tests on synthetic fixtures (checksum correctness vs `sha256sum`/`hashlib` independent calc, unknown-format flag); run on the real `data/raw/`; confirm raw files unchanged (checksums before/after).
- **Expected Output:** `manifest.json` listing real files; report states honestly which dataset(s) are present or missing.
- **Definition of Done:** Manifest generated from real data (or task reported BLOCKED because no dataset is present — human action needed).

## CN-003 — Dataset Inspection
- **Task ID:** CN-003 · **Task Name:** Dataset Inspection
- **Goal:** Produce a factual inspection report from the real dataset files so the team can finalize the Dataset → Target Label Mapping.
- **Why It Is Needed:** Resolves U-02, U-04, U-16, U-17 inputs; provides real column names/labels (DS-004, FE-006); prevents invented labels.
- **Dependencies:** CN-002.
- **Files/Directories:** `preprocessing/inspect.py`, `artifacts/reports/dataset_inspection.{md,json}` (generated), `docs/decisions/label_mapping_worksheet.md` (generated, labels list for humans), `tests/unit/test_inspect.py`.
- **Implementation Requirements:**
  1. Per dataset/file: column names (verbatim), count, dtypes, rows; label column candidates and **every distinct label with counts**; NaN/±inf counts per column; exact-duplicate counts; constant columns; presence of identifier-like columns (IP/port/timestamp/flow-ID); presence of capture/session/file identifiers usable for grouping (U-17).
  2. Report whether the files appear to contain flow-feature CSVs, raw PCAPs, or both (U-04), and the number of columns (compare to Review-1's "80+").
  3. Generate `label_mapping_worksheet.md`: a table of *original labels with counts and an empty "target class / DROP" column* for the humans. **Do not propose or fill in mappings.**
  4. Flag (do not decide) the risk that a dataset may lack application-category labels (U-02).
- **Do Not:** map labels; drop rows; modify raw data; infer meaning of labels beyond what files/documentation show; guess.
- **Verification:** Tests on synthetic CSVs with known NaN/inf/dup counts; run on real data; a human spot-checks three numbers (a label count, a NaN count, a column count) against an independent tool (e.g., `pandas` in a shell or spreadsheet).
- **Expected Output:** Inspection report + empty-mapping worksheet; summary of open questions for the team.
- **Definition of Done:** Report generated from real files; spot-check recorded; **STOP — human completes the mapping worksheet and `config/label_mapping.yaml`; CN-004 is gated (G-LABEL).**

## CN-004 — Preprocessing
- **Task ID:** CN-004 · **Task Name:** Preprocessing (mapping, cleaning, split)
- **Goal:** Apply the approved label mapping, clean data, create a frozen stratified (group-aware if possible) train/test split, and build the learned-preprocessing pipeline (imputer + min-max scaler).
- **Why It Is Needed:** Review-1 Module 1 (missing values, min-max scaling, identifier removal); ML-002…ML-004, ML-007, ML-008, ML-010, DS-002, DS-007, TC-001, AC-001, AC-003.
- **Dependencies:** CN-003; **G-LABEL** — `config/label_mapping.yaml` is `status: approved`; U-09 (split ratio, folds) answered in `docs/decisions/`.
- **Files/Directories:** `preprocessing/{label_mapping,cleaning,split,pipeline}.py`, `config/default.yaml` (split/cv/preprocessing keys), `data/processed/{train,test}` + `split_manifest.json` (generated), `tests/unit/test_{label_mapping,cleaning,split,pipeline}.py`, `tests/unit/test_no_leakage.py`.
- **Implementation Requirements:**
  1. `label_mapping.py`: raises `LabelMappingError` unless `status: approved`; every original label mapped or `DROP`; unlisted label ⇒ error; outputs per-class counts and dropped-label counts; records mapping SHA-256.
  2. `cleaning.py` (deterministic only): drop metadata/identifier columns from model input (keep as metadata), ±inf→NaN, exact-duplicate removal before split, port-feature policy per RID-07; log counts at each step.
  3. `split.py`: stratified split (group-aware if CN-003 found usable group identifiers and the team decided so — U-17); seed from config; write train/test + row-ID manifest + hash; assert disjointness.
  4. `pipeline.py`: `build_preprocessor()` returning imputer + `MinMaxScaler` scikit-learn steps (selector added in CN-005); documented parameters; fit only on train.
  5. Test-set loader is **not** created here (it belongs to `evaluation/`, CN-010).
- **Do Not:** invent mappings; proceed if status ≠ approved; fit anything on test; resample the test set; touch raw data; silently drop rows.
- **Verification:** Tests: unapproved mapping refused; unlisted label error; counts reconcile (rows in = rows out + dropped, with reasons); train/test disjoint; no duplicate rows across splits; scaler's fitted min/max equal train-only min/max; run on real data; two runs with same seed give identical splits.
- **Expected Output:** Frozen train/test + manifests; class-count table post-mapping; pipeline builder; leakage tests passing.
- **Definition of Done:** All tests run and pass; row-count reconciliation in report; any class below the team's minimum-sample threshold raised as a decision item.

## CN-005 — Feature Validation
- **Task ID:** CN-005 · **Task Name:** Feature Validation & Selection Stage
- **Goal:** Validate the feature set against Review-1's four feature families, produce the canonical `config/feature_schema.yaml`, and implement in-fold feature selection.
- **Why It Is Needed:** FE-001…FE-010, ML-005, ML-009; fixes the feature contract that both training and PCAP inference must obey (U-04, U-10).
- **Dependencies:** CN-004.
- **Files/Directories:** `preprocessing/validate_features.py`, `preprocessing/pipeline.py` (selector added), `config/feature_schema.yaml`, `artifacts/reports/feature_validation.{md,json}` (generated), `tests/unit/test_{validate_features,selector}.py`.
- **Implementation Requirements:**
  1. Classify each real column into `features | metadata | label | excluded(reason)`; record group membership (time / volume / TCP-flag / directional-ratio) **based on real column names and documented meaning**; list any Review-1 family with no available column.
  2. Report constant/near-constant features, highly correlated pairs (training data only), suspicious scales/units, and port/identifier handling per RID-07.
  3. Implement the staged selector (variance → correlation → importance top-k, RID-08) as pipeline steps fit only inside training folds; parameters from config.
  4. Write `feature_schema.yaml` including alias map placeholders (to be completed against the extractor in CN-014).
- **Do Not:** include IPs/MACs/timestamps/flow IDs as features; choose features by looking at test data; hard-code column lists from memory.
- **Verification:** Tests: selector fit sees only training fold (data-identity test); schema validator catches missing/extra columns; run on real train data; report reviewed by a human for the group classification.
- **Expected Output:** Schema file, validation report, working selector.
- **Definition of Done:** Tests pass; schema approved by a human (decision logged) — it is now the contract for training and inference.

## CN-006 — Decision Tree
- **Task ID:** CN-006 · **Task Name:** Decision Tree (+ shared training infrastructure)
- **Goal:** Build the model-spec/tuning/training framework and train + tune the Decision Tree.
- **Why It Is Needed:** FR-005, ML-001, ML-006, ML-009, ML-011; establishes the pattern the other three models reuse.
- **Dependencies:** CN-005.
- **Files/Directories:** `models/{base,tuning,train,decision_tree}.py`, `config/models.yaml` (decision_tree section), `artifacts/runs/<run_id>/` (generated), `tests/unit/test_{train,tuning}.py`.
- **Implementation Requirements:**
  1. `ModelSpec` interface (TRD §12); `train.py` CLI `python -m models.train --model decision_tree`.
  2. Full pipeline (imputer → scaler → selector → model) cross-validated with stratified (or group) K-fold inside train; scoring macro-F1 (RID-20); all trials saved.
  3. Run directory contents per TRD §12 (config snapshot, mapping hash, cv_results, best params, pipeline.joblib, selected features, env info, seed).
  4. Verify the estimator's parameter names against the installed scikit-learn before writing the search space.
  5. Export tree depth/leaf count (and a human-readable rule export if feasible).
- **Do Not:** import or load the test set; use test data for early stopping/selection; hard-code seeds.
- **Verification:** Test that `models/` has no import path to the test loader; test same-seed reproducibility; real run on real training data; confirm test set files were not opened (audit/log).
- **Expected Output:** One run directory; CV score table; saved pipeline.
- **Definition of Done:** CLI works end-to-end; tests pass; report includes real CV results (no test metrics).

## CN-007 — Random Forest
- **Task ID:** CN-007 · **Task Name:** Random Forest
- **Goal:** Train + tune Random Forest with the shared infrastructure.
- **Why It Is Needed:** FR-005, ML-001; feature importances support selection discussion.
- **Dependencies:** CN-006.
- **Files/Directories:** `models/random_forest.py`, `config/models.yaml` (random_forest section), tests.
- **Implementation Requirements:** Same pipeline/CV/tuning pattern; verify parameter names against installed version; bound search budget via config; save feature importances (training-derived) to the run directory.
- **Do Not:** change shared preprocessing for this model; touch the test set; run unbounded searches.
- **Verification:** Same checks as CN-006; log wall-clock time; seed reproducibility (or document non-determinism).
- **Expected Output:** Run directory + CV results + importances.
- **Definition of Done:** CLI works; tests pass; report with real timings and CV scores.

## CN-008 — SVM
- **Task ID:** CN-008 · **Task Name:** SVM
- **Goal:** Train + tune SVM under the disclosed scalability policy.
- **Why It Is Needed:** FR-005, ML-001, ML-012.
- **Dependencies:** CN-006.
- **Files/Directories:** `models/svm.py`, `config/models.yaml` (svm section incl. `subsample_fraction`), tests.
- **Implementation Requirements:** Measure feasibility first (time a small subsample); apply RID-06 (stratified training subsample for tuning and/or `LinearSVC` variant); record exactly what subsample/variant was used and why; confirm scaling is in the pipeline; probability estimates off unless justified.
- **Do Not:** subsample the test set; hide the subsampling; run indefinitely without a time budget.
- **Verification:** Tests for stratified-subsample class proportions; real run; report states n_train used for SVM vs other models.
- **Expected Output:** Run directory with a `scalability_note.md`.
- **Definition of Done:** SVM trained and tuned with documented policy; tests pass.

## CN-009 — XGBoost
- **Task ID:** CN-009 · **Task Name:** XGBoost
- **Goal:** Train + tune XGBoost with the shared infrastructure.
- **Why It Is Needed:** FR-005, ML-001; Review-1 gap analysis highlights ensemble boosting.
- **Dependencies:** CN-006.
- **Files/Directories:** `models/xgboost_model.py`, `config/models.yaml` (xgboost section), tests.
- **Implementation Requirements:** **Check the installed XGBoost version's scikit-learn-wrapper parameters and multi-class objective before coding** (record version and what you checked); integer-encoded labels; sample weights from training class frequencies if imbalance is material; any early-stopping validation split carved from training data only.
- **Do Not:** copy parameter names from memory; use test data for early stopping.
- **Verification:** Tests for label encoding round-trip; real run; seed reproducibility check.
- **Expected Output:** Run directory with CV results.
- **Definition of Done:** CLI works; tests pass; version/API verification recorded.

## CN-010 — Evaluation
- **Task ID:** CN-010 · **Task Name:** Evaluation
- **Goal:** Evaluate all four trained models on the frozen test set exactly once, producing the required metrics.
- **Why It Is Needed:** FR-006, EV-001…EV-006, EV-009, AC-004, AC-005.
- **Dependencies:** CN-006, CN-007, CN-008, CN-009; RID-20 best-model criterion confirmed in decision log **before** running.
- **Files/Directories:** `evaluation/{metrics,evaluate}.py`, `artifacts/reports/<run_id>/` (generated), `tests/unit/test_metrics.py`, `tests/unit/test_test_set_guard.py`.
- **Implementation Requirements:**
  1. `load_test_set(purpose="final_evaluation")` with audit-log line; only `evaluation/` may call it.
  2. Metrics: Accuracy; Precision/Recall/F1 per class; macro and weighted; confusion matrix; per-flow inference time; model size; train time (from run info).
  3. Write JSON/CSV/PNG artifacts; no hand-typed numbers.
  4. Log if a model is evaluated more than once.
- **Do Not:** tune, refit, or select anything using test results; evaluate before the criterion is recorded.
- **Verification:** Unit test: metrics on a tiny hand-computed confusion example match; guard test: non-evaluation callers are refused/not importable; run on real test set; audit log shows one read per model.
- **Expected Output:** Per-model metrics + confusion matrices from the real test set.
- **Definition of Done:** Artifacts exist; tests pass; report quotes numbers only by referencing artifact files.

## CN-011 — Model Comparison
- **Task ID:** CN-011 · **Task Name:** Model Comparison
- **Goal:** Generate the four-model comparison and the best-model decision record.
- **Why It Is Needed:** FR-007, EV-004, EV-007, EV-009, AC-006.
- **Dependencies:** CN-010.
- **Files/Directories:** `evaluation/{compare,report}.py`, `artifacts/reports/comparison.{csv,md,png}`, `docs/decisions/best_model.md`, tests.
- **Implementation Requirements:** Build table/plots from JSON artifacts only; apply the pre-declared criterion (CV macro-F1, RID-20) to name the best model; include per-class results, timing, size, SVM-subsample disclosure, limitations (PRD §21), and an explicit note that Review-1's 95–98% claim is neither a target nor assumed.
- **Do Not:** edit numbers by hand; pick the winner from test results unless the decision log says so (then disclose); omit weak classes.
- **Verification:** Test that the table regenerates identically from artifacts; human cross-checks three numbers against raw JSON.
- **Expected Output:** Comparison table/plot + decision record.
- **Definition of Done:** Comparison reproducible by one command; decision record saved.

## CN-012 — Model Registry
- **Task ID:** CN-012 · **Task Name:** Model Registry
- **Goal:** Persist chosen model(s) with complete metadata in a file-based registry with integrity checks.
- **Why It Is Needed:** FR-007, ML-009, AC-007.
- **Dependencies:** CN-011.
- **Files/Directories:** `models/registry.py`, `artifacts/registry/` (generated), `tests/unit/test_registry.py`.
- **Implementation Requirements:** Layout and metadata per TRD §20; CLI to register a run, list entries, set/show active; SHA-256 verification on load; library-version mismatch warning; schema/label-mapping copies stored; refuse load on checksum mismatch (`RegistryIntegrityError`).
- **Do Not:** load registry files from uploads/untrusted paths; store raw data or PCAPs; build a database.
- **Verification:** Round-trip test (identical predictions on a fixed sample); tamper test (modify bytes → rejected); metadata completeness test; run on the real best run.
- **Expected Output:** Registry with the active best model.
- **Definition of Done:** Tests pass; `python -m models.registry list` output captured in report.

## CN-013 — CICFlowMeter Integration
- **Task ID:** CN-013 · **Task Name:** CICFlowMeter Integration (adapter + verification)
- **Goal:** Establish, by real execution, how CICFlowMeter is installed and run on the team's machine, and implement the adapter around the verified interface.
- **Why It Is Needed:** Review-1 Module 2; PC-002, FE-010, AC-008; resolves U-05; de-risks the PCAP pipeline.
- **Dependencies:** CN-001; **human assists with installation/choice of implementation (U-05)**; **G-CFM**.
- **Files/Directories:** `flow/{extractor_base,cicflowmeter_adapter}.py`, `scripts/verify_cicflowmeter.py`, `docs/verification/cicflowmeter.md`, `config/default.yaml` (`cicflowmeter.*` keys), `tests/unit/test_adapter_mock.py`, `tests/integration/test_adapter_real.py` (marker `requires_cicflowmeter`).
- **Implementation Requirements:**
  1. Do **not** assume any command, API, or output format. Discover from the installed tool's own help/docs/source and record findings per TRD §22.2 (implementation & source, version, runtime, OS, exact working command, output naming, verbatim CSV header + column count, sample row, timeouts, units, `.pcap`/`.pcapng` support, empty/corrupt PCAP behaviour).
  2. Implement `FlowExtractor` protocol and `CICFlowMeterAdapter` using `subprocess` with an argument list (no `shell=True`), timeout, captured stderr, mapped errors.
  3. Fill `cicflowmeter.command_template` **only** with the verified command.
  4. If CICFlowMeter cannot be made to run: **STOP, report BLOCKED** with evidence; do not build the fallback — that requires the human decision (G-FALLBACK, RID-10).
- **Do Not:** guess flags; claim a Python API; implement fallback unprompted; store PCAPs in git.
- **Verification:** Run the adapter on one real PCAP (small); inspect output CSV; mocked-subprocess unit tests (command construction, timeout, non-zero exit); real test marked and reported as run/skipped honestly.
- **Expected Output:** `cicflowmeter.md` verification record; working adapter producing a flow CSV from a real PCAP.
- **Definition of Done:** Verified record + adapter tests; or BLOCKED report with evidence.

## CN-014 — PCAP Flow Extraction
- **Task ID:** CN-014 · **Task Name:** PCAP Flow Extraction (normalizer + parity)
- **Goal:** Convert extractor output into the canonical feature table and prove train/inference schema parity.
- **Why It Is Needed:** FE-005…FE-008, PC-002, PC-004, PC-005, U-04, U-11.
- **Dependencies:** CN-005, CN-013.
- **Files/Directories:** `flow/normalizer.py`, `config/feature_schema.yaml` (alias map completed), `docs/verification/feature_parity.md`, `tests/unit/test_normalizer.py`, `tests/integration/test_pcap_to_features.py`.
- **Implementation Requirements:**
  1. Normalizer per TRD §9.3 (alias mapping, verified unit conversions, documented derived features, required-feature assertion, metadata separated).
  2. Parity analysis: compare extractor-produced columns/units/semantics with the training schema; if dataset PCAPs are available, compare distributions for matching traffic. Features that disagree in semantics are excluded or converted — and if that changes the training schema, **STOP and report** (human decision; may require retraining).
  3. Handle: zero flows, non-TCP/UDP flows (report count, exclude per U-11 default), malformed rows.
- **Do Not:** silently fill missing features with zeros; relax the schema check to make tests pass.
- **Verification:** Unit tests (missing/extra/alias/unit cases); integration run on the real PCAP from CN-013; explicit failing-case demo (wrong schema ⇒ `SchemaMismatchError`).
- **Expected Output:** Canonical feature table for a real PCAP; parity document.
- **Definition of Done:** Parity documented with real evidence; tests pass.

## CN-015 — PCAP Inference
- **Task ID:** CN-015 · **Task Name:** PCAP Inference
- **Goal:** Classify the flows of a PCAP with a registry model end-to-end.
- **Why It Is Needed:** FR-008, TC-002…TC-005, PC-001…PC-006, AC-009.
- **Dependencies:** CN-012, CN-014; **G-SCHEMA** (`config/feature_schema.yaml` approved and train/inference parity decided, U-04).
- **Files/Directories:** `inference/{predictor,pcap_classifier}.py`, `artifacts/predictions/` (generated), `tests/unit/test_predictor.py`, `tests/integration/test_pcap_inference.py`.
- **Implementation Requirements:** CLI per TRD §21; load model by id/active with integrity check; schema-parity gate; output per-flow predictions (five-tuple metadata + class + confidence if available) and `summary.json` (flows per class, excluded counts, model id, extractor version, runtime); temp files cleaned unless configured; optional low-confidence handling only if RID-19 was adopted.
- **Do Not:** use payload; copy PCAP into the repo; claim accuracy for unlabeled PCAPs (no ground truth — say so).
- **Verification:** Run on the real PCAP; invalid/empty/corrupt-PCAP error tests; schema-mismatch refusal test; check output class names ⊆ registry class list.
- **Expected Output:** Predictions + summary for a real PCAP.
- **Definition of Done:** Real run recorded; error-path tests pass; limitations (TC-005) noted in output summary.

## CN-016 — Live Capture
- **Task ID:** CN-016 · **Task Name:** Live Capture
- **Goal:** Capture from a real interface into rotating PCAP chunks with privacy-safe defaults.
- **Why It Is Needed:** FR-013, RT-002, RT-005, RT-006, U-06, U-13.
- **Dependencies:** CN-015; human confirms authorised interface/network and privileges.
- **Files/Directories:** `capture/{tshark_capture,scapy_capture,chunk_manager}.py`, `config/default.yaml` (`capture.*`), `docs/verification/capture.md`, `tests/unit/test_chunk_manager.py`, `tests/integration/test_capture.py` (`requires_capture`).
- **Implementation Requirements:** Verify `tshark` flags and/or Scapy functions against the installed versions before use (record in `capture.md`); interface listing; chunk rotation by duration/count; identify *completed* chunks only; optional BPF filter and snaplen (verify extractor still handles truncated captures); `CaptureError` with guidance on permission/driver issues; clean stop.
- **Do Not:** capture on networks without authorisation; persist payload beyond chunks; commit captures; assume Windows/Linux specifics.
- **Verification:** Generate known benign traffic on the authorised interface; confirm chunks are produced, completed-chunk logic works, chunks readable by `tshark`/Scapy; permission-denied path tested or reported UNVERIFIED.
- **Expected Output:** Chunked PCAPs from a real interface; `capture.md`.
- **Definition of Done:** Verified on real hardware (or BLOCKED with evidence).

## CN-017 — Real-Time Inference
- **Task ID:** CN-017 · **Task Name:** Real-Time (near-live) Inference
- **Goal:** Process completed chunks through extractor → normalizer → model, emitting live predictions and measured latency.
- **Why It Is Needed:** FR-009, RT-001, RT-003, RT-004, RT-007, AC-010.
- **Dependencies:** CN-016.
- **Files/Directories:** `inference/live_classifier.py`, `artifacts/live/predictions.jsonl` (generated), `artifacts/live/latency.csv`, `docs/verification/live_latency.md`, `tests/unit/test_live_loop.py`, `tests/integration/test_live.py` (`requires_capture` + `requires_cicflowmeter`).
- **Implementation Requirements:** Loop per TRD §23.1; append-only JSONL results; per-chunk latency (chunk close → prediction written) and per-flow inference time recorded; chunk deleted after processing by default; graceful shutdown; errors in one chunk don't kill the loop (logged, counted); document boundary-splitting effect (RT-007).
- **Do Not:** call it "real-time" in code/docs/UI until `live_latency.md` contains measured data; process partial chunks; keep chunks by default.
- **Verification:** Run live for a few minutes with known generated traffic (e.g., browsing, a file download, streaming) and inspect predictions qualitatively (label results as qualitative, EV-008); record latency stats; kill-signal test.
- **Expected Output:** Live predictions file, latency measurements, honest limitations.
- **Definition of Done:** Verified end-to-end with measured latency; or documented as not delivered (AC-010 = N/A).

## CN-018 — Dashboard
- **Task ID:** CN-018 · **Task Name:** Dashboard
- **Goal:** Provide a read-only dashboard over artifacts that keeps the networking chain visible.
- **Why It Is Needed:** FR-010, DB-001…DB-008, AC-011, OBJ-6/7.
- **Dependencies:** CN-011, CN-012, CN-015 (CN-017 if delivered); U-12 confirmed.
- **Files/Directories:** `dashboard/{app,loaders}.py`, `dashboard/views/*`, `requirements.txt` (add the dashboard library — justify), `tests/unit/test_loaders.py`.
- **Implementation Requirements:** Views per TRD §24 (distribution, comparison, confusion matrix, PCAP results, optional live view, "How it works" page); loaders read artifacts only and handle missing/empty artifacts gracefully; IP masking option; bind to `127.0.0.1` by default; no hard-coded metrics.
- **Do Not:** add a database/server framework beyond the chosen library; require internet; display metrics not in artifacts; expose to all interfaces by default.
- **Verification:** Unit tests for loaders (including empty cases); launch locally, load each view, compare displayed metrics with artifact JSON (three spot checks); screenshots optional for the demo.
- **Expected Output:** Running dashboard.
- **Definition of Done:** All delivered views functional with real artifacts; dependency justified; tests pass.

## CN-019 — Integration Testing
- **Task ID:** CN-019 · **Task Name:** Integration Testing
- **Goal:** Test module boundaries and cross-component contracts.
- **Why It Is Needed:** NFR-006, AC-012.
- **Dependencies:** CN-015 (+ CN-017, CN-018 if delivered).
- **Files/Directories:** `tests/integration/*`, `tests/fixtures/*`, `docs/task_reports/integration_test_report.md`.
- **Implementation Requirements:** Cover: dataset→preprocess→train→evaluate→register on tiny **synthetic** fixtures (plumbing only); registry→predictor; extractor adapter (mock + real if available); normalizer→predictor schema gate; live-loop with fake chunk source; leakage tests (train/test disjointness; `models/` ↛ test loader). All prerequisite-dependent tests carry markers.
- **Do Not:** report model performance from synthetic data; hide skipped tests; weaken assertions to pass.
- **Verification:** `pytest -q -rs` full run; list of passed/failed/skipped with reasons in the report; failures triaged.
- **Expected Output:** Integration test suite + honest report.
- **Definition of Done:** Suite runs; failures fixed or documented as known issues; skipped tests reported as skipped.

## CN-020 — End-to-End Testing
- **Task ID:** CN-020 · **Task Name:** End-to-End Testing
- **Goal:** Execute the full user scenarios from a clean checkout following README commands.
- **Why It Is Needed:** AC-009, AC-010, AC-012, EV-008.
- **Dependencies:** CN-019.
- **Files/Directories:** `tests/e2e/*`, `docs/task_reports/e2e_report.md`, `docs/verification/sanity_captures.md`.
- **Implementation Requirements:** Scenario A: real PCAP → predictions. Scenario B (if delivered): live → predictions.jsonl → dashboard. Scenario C: failure paths (no model, schema mismatch, unavailable extractor, no privileges). EV-008 sanity check: capture known applications (team-labelled, small, authorised) and compare predictions *qualitatively*, stating that this is not a benchmark.
- **Do Not:** present the sanity check as accuracy; edit docs to match results; skip failure-path tests.
- **Verification:** Exact commands recorded; clean virtual environment used; outputs inspected by a human.
- **Expected Output:** E2E report and sanity-check record.
- **Definition of Done:** All delivered scenarios executed with recorded results; discrepancies logged.

## CN-021 — Demo Packaging
- **Task ID:** CN-021 · **Task Name:** Demo Packaging
- **Goal:** Make a rehearsed, reliable viva demo.
- **Why It Is Needed:** OBJ-7, AC-013.
- **Dependencies:** CN-020.
- **Files/Directories:** `docs/DEMO.md`, `scripts/demo_*.{py,sh,ps1}` (only if needed), `data/sample/` (permitted sample PCAP/CSV, licence-checked or self-generated), `docs/demo_fallbacks.md`.
- **Implementation Requirements:** Step-by-step runbook (commands actually tested); packets→five-tuple→flow→features→model→class talking points mapped to dashboard/CLI outputs; fallback plan if live capture fails (use recorded PCAP); pre-flight checklist (privileges, tool paths, model in registry).
- **Do Not:** include untested steps; use copyrighted/sensitive captures; promise features not delivered.
- **Verification:** A teammate follows `DEMO.md` on a clean machine/environment; timing recorded.
- **Expected Output:** Demo package.
- **Definition of Done:** Dry-run completed; issues fixed or documented.

## CN-022 — Final Documentation
- **Task ID:** CN-022 · **Task Name:** Final Documentation
- **Goal:** Bring all docs in line with what was actually built and measured.
- **Why It Is Needed:** NFR-008, AC-013, EV-007.
- **Dependencies:** CN-021.
- **Files/Directories:** `README.md`, `docs/FINAL_REPORT_INPUTS.md`, `docs/decisions/decisions.md`; modifications to PRD/TRD/BUILD_PLAN/TASKS statuses *only as this task authorises* (status tables, resolved U-items, "not delivered" notes).
- **Implementation Requirements:** README with real install/run/reproduce commands; resolved/unresolved decision table; delivered vs not-delivered features; results summary referencing artifact paths (numbers copied from artifacts, each with its path); limitations; dataset citations/licences; viva Q&A preparation notes (why flow features, why five-tuple, why these four models, leakage safeguards).
- **Do Not:** claim anything not verified; leave "planned" wording for delivered features or vice versa; include numbers without artifact references.
- **Verification:** Script/checklist that every number in README/report has an artifact path; commands in README re-run successfully from a clean environment.
- **Expected Output:** Final docs.
- **Definition of Done:** Docs match reality; all U-items resolved or explicitly carried as known limitations.
