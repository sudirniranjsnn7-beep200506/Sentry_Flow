# BUILD_PLAN — FlowSentry
**Phase and dependency authority.** Task details live in `TASKS.md`; requirements in `PRD.md`; design in `TRD.md`; agent rules in `AGENTS.md`.

Progression (strict, never parallel across phases):
```text
Dataset → ML → PCAP → Live Traffic → Dashboard
```
Do not build everything at once. A phase starts only when the previous phase's **Verification gate** is passed and recorded in `docs/task_reports/`.

## Phase overview

| Phase | Name | Tasks | Needs human decision before/within |
|---|---|---|---|
| 0 | Specification | (documents) | U-01, U-02, U-07, U-13, U-14 acknowledged |
| 1 | Repository Foundation | CN-001 | U-13 (OS/privileges) |
| 2 | Dataset Pipeline | CN-002, CN-003, CN-004, CN-005 | **G-LABEL** (U-01/02/03/16/17), U-04, U-09, U-10 |
| 3 | ML Training | CN-006, CN-007, CN-008, CN-009 | RID-06 SVM policy |
| 4 | Model Evaluation | CN-010, CN-011 | RID-20 criterion confirmed before CN-010 |
| 5 | Model Registry | CN-012 | — |
| 6 | PCAP Classification | CN-013, CN-014, CN-015 | **G-CFM** (U-05), RID-10 fallback decision, U-11 |
| 7 | Live Classification | CN-016, CN-017 | U-06, U-13, **G-LIVE** |
| 8 | Dashboard | CN-018 | U-12 |
| 9 | Testing | CN-019, CN-020 | — |
| 10 | Final Demo & Documentation | CN-021, CN-022 | — |

## Dependency graph
```text
CN-001 → CN-002 → CN-003 → [G-LABEL human approval] → CN-004 → CN-005
CN-005 → CN-006 ─┐
CN-005 → CN-007 ─┤
CN-005 → CN-008 ─┼→ CN-010 → CN-011 → CN-012
CN-005 → CN-009 ─┘
CN-001 → CN-013 → CN-014 ─┐                   (CN-013 can start after CN-001; schema parity check needs CN-005)
CN-012 + CN-014 → CN-015 → CN-016 → CN-017
CN-011 + CN-015 (+ CN-017 if delivered) → CN-018
CN-015 [+CN-017, CN-018] → CN-019 → CN-020 → CN-021 → CN-022
```
Note: CN-013 (verifying CICFlowMeter) may be done early, in parallel with Phase 2 *by a human*, because it has long lead time and de-risks everything (U-05). Agents still execute one task at a time.

## Cut-lines if time runs short (decided by the team, not the agent)
1. **Must deliver (core):** Phases 1–5 and CN-013…CN-015 (dataset → four-model comparison → registry → PCAP classification), plus CN-019/020 (scoped to delivered parts) and CN-022.
2. **Should deliver:** CN-018 dashboard (static views from artifacts are enough).
3. **Optional:** CN-016/017 live classification. If not delivered, `README.md` and final docs state "not delivered", and PRD AC-010 is marked N/A.

---

## Phase 0 — Specification
- **Goal:** Establish authoritative requirements, design, rules, plan, tasks; surface unresolved decisions.
- **Dependencies:** CN Review-1 document.
- **Tasks:** none (document generation + human review).
- **Expected outputs:** `PRD.md`, `TRD.md`, `AGENTS.md`, `README.md`, `BUILD_PLAN.md`, `TASKS.md`; consistency check report.
- **Verification gate:** Team reads all six, resolves or consciously defers each `U-xx` (at minimum: U-01 class set, U-07 objectives text, U-13 OS/privileges, U-14 dataset access) and records answers in `docs/decisions/decisions.md`.
- **Failure conditions:** Documents contradict each other or Review-1; an assumption is presented as a requirement; the team cannot access any dataset (re-plan U-02/U-14 before Phase 2).
- **Definition of Done:** Documents committed; decision log started; the first agent prompt issued.

## Phase 1 — Repository Foundation
- **Goal:** A clean, runnable skeleton: structure, config loading, logging, errors, tests harness, environment verification.
- **Dependencies:** Phase 0.
- **Tasks:** CN-001.
- **Expected outputs:** Directory tree (TRD §3), `requirements.txt` (versions verified), `.env.example`, `.gitignore` (data/PCAP/artifacts), `common/` modules, `scripts/verify_environment.py`, passing smoke tests, `data/README.md`.
- **Verification gate:** `pytest` runs and passes; environment script reports Python, library versions, and *whether* `tshark`, `java`, and capture privileges are available (reports, doesn't assume).
- **Failure conditions:** Dependencies not installable; hard-coded paths; data/PCAP not git-ignored.
- **Definition of Done:** CN-001 report with real commands/results; repo importable from root.

## Phase 2 — Dataset Pipeline
- **Goal:** From raw datasets to a validated, leakage-safe, mapped, split dataset and a canonical feature schema.
- **Dependencies:** Phase 1; datasets obtained by the humans (U-14); **G-LABEL** satisfied before CN-004.
- **Tasks:** CN-002 (ingestion), CN-003 (inspection), CN-004 (preprocessing: mapping, cleaning, split), CN-005 (feature validation / schema).
- **Expected outputs:** manifest with checksums; inspection report from real files; approved `config/label_mapping.yaml`; frozen train/test split with row-ID manifest; `config/feature_schema.yaml`; leakage tests.
- **Verification gate:** Inspection report matches the files (spot-checked by a human); mapping `status: approved`; train/test disjoint; preprocessing fit on train only (tested); schema lists feature groups from all four Review-1 families (or documents which are unavailable).
- **Failure conditions:** Any invented label/column; unmapped labels silently dropped; test data used for fitting; no valid mapping to the target classes exists (→ escalate: change dataset role/class set — human decision).
- **Definition of Done:** CN-002…005 reports; AC-001, AC-002, AC-003 satisfied.

## Phase 3 — ML Training
- **Goal:** Train and tune the four models on the same training set with the same pipeline.
- **Dependencies:** Phase 2.
- **Tasks:** CN-006 (Decision Tree), CN-007 (Random Forest), CN-008 (SVM), CN-009 (XGBoost).
- **Expected outputs:** one run directory per model (`artifacts/runs/<run_id>/`) containing pipeline, CV results, best params, selected features, config snapshot, env info.
- **Verification gate:** Each model trains from the CLI; CV happens only within train; seeds recorded; second run with same seed gives same selected features/params (or differences are explained); `models/` does not import the test loader (test passes).
- **Failure conditions:** Test data touched; model-specific preprocessing divergence; SVM run unbounded in time without the disclosed subsampling policy; XGBoost parameters used that don't exist in the installed version.
- **Definition of Done:** Four run directories + CN-006…009 reports.

## Phase 4 — Model Evaluation
- **Goal:** Evaluate all four on the frozen test set exactly once, compare, choose best by the pre-declared criterion.
- **Dependencies:** Phase 3.
- **Tasks:** CN-010 (evaluation), CN-011 (comparison).
- **Expected outputs:** per-model metrics (Accuracy, Precision, Recall, F1 per class + macro/weighted), confusion matrices, timing/size, generated comparison table/plot, best-model decision record.
- **Verification gate:** Metrics reproduced by an independent recomputation on a tiny hand-checkable example (unit test) and re-runnable from artifacts; test-access audit log shows only evaluation reads; all numbers in the comparison trace to JSON artifacts.
- **Failure conditions:** Best model chosen using test results contrary to RID-20 without disclosure; hand-typed numbers; classes missing from reports.
- **Definition of Done:** AC-004, AC-005, AC-006 satisfied.

## Phase 5 — Model Registry
- **Goal:** Persist the best (and optionally all) models with everything needed for exact inference.
- **Dependencies:** Phase 4.
- **Tasks:** CN-012.
- **Expected outputs:** `artifacts/registry/` with index, entries, checksums, schema/label-mapping copies, metadata.
- **Verification gate:** Round-trip test (save → load → identical predictions on a fixed sample); tampered artifact detected via checksum; schema-mismatch input is refused.
- **Failure conditions:** Pipeline saved without scaler/selector/label encoder; metadata missing hashes.
- **Definition of Done:** AC-007 satisfied.

## Phase 6 — PCAP Classification
- **Goal:** Offline PCAP → flows (CICFlowMeter via adapter) → features → prediction.
- **Dependencies:** Phase 5 (model) and CN-013 (verified extractor); **G-CFM**.
- **Tasks:** CN-013 (CICFlowMeter integration), CN-014 (PCAP flow extraction), CN-015 (PCAP inference).
- **Expected outputs:** `docs/verification/cicflowmeter.md` from real runs; adapter + normalizer; per-flow predictions and summary for at least one real PCAP; documented handling of non-TCP/UDP.
- **Verification gate:** Adapter works on a real PCAP on the team's machine (or fallback decision formally recorded); extractor output header matches the canonical schema through the alias map; schema-parity check demonstrated (pass and fail cases); predictions produced for real PCAP.
- **Failure conditions:** Assumed CICFlowMeter command/API; unit mismatch between training and extractor features; silent zero-flow output.
- **Definition of Done:** AC-008, AC-009 satisfied.

## Phase 7 — Live Classification (optional)
- **Goal:** Near-live capture → classification with measured latency.
- **Dependencies:** Phase 6; capture privileges/driver available (U-13); U-06 answered.
- **Tasks:** CN-016 (live capture), CN-017 (real-time inference).
- **Expected outputs:** capture module with chunk rotation; live classifier writing `predictions.jsonl`; recorded latency measurements; documented limits.
- **Verification gate:** Capture verified on a real interface with generated known traffic; chunk → prediction path works; latency numbers recorded from real runs; clean stop; chunks deleted by default.
- **Failure conditions:** Processing incomplete chunks; payload persisted; "real-time" claimed without data; privileges errors uncaught.
- **Definition of Done:** AC-010 satisfied, **or** formally recorded as not delivered.

## Phase 8 — Dashboard
- **Goal:** Read-only visualisation of artifacts, keeping networking concepts visible.
- **Dependencies:** Phases 4–6 (and 7 if delivered); U-12 resolved.
- **Tasks:** CN-018.
- **Expected outputs:** dashboard with dataset distribution, comparison, confusion matrix, PCAP results (and live view if available), "how it works" page.
- **Verification gate:** Launches locally; every displayed metric matches its artifact file; empty-artifact states handled; IP masking works.
- **Failure conditions:** Hard-coded metrics; DB introduced; binds to all interfaces by default.
- **Definition of Done:** AC-011 satisfied.

## Phase 9 — Testing
- **Goal:** Whole-system confidence with honest reporting of what ran.
- **Dependencies:** Phases 1–8 as delivered.
- **Tasks:** CN-019 (integration testing), CN-020 (end-to-end testing).
- **Expected outputs:** integration tests, e2e tests, test report (passed/failed/skipped + reasons), known-issue list, controlled sanity-check captures (EV-008) with qualitative results.
- **Verification gate:** Full `pytest` run recorded; e2e scenario (dataset→model→PCAP→predictions[→dashboard]) executed from a clean checkout following README commands.
- **Failure conditions:** Skipped tests reported as passed; tests depend on non-committed local data without markers.
- **Definition of Done:** AC-012 satisfied.

## Phase 10 — Final Demo & Documentation
- **Goal:** Viva-ready demo and accurate final docs.
- **Dependencies:** Phase 9.
- **Tasks:** CN-021 (demo packaging), CN-022 (final documentation).
- **Expected outputs:** demo script/runbook (what to show, fallback if live fails), sample demo PCAP handling, final README with real reproduce-steps, final report text with real results, updated limitations and decision log.
- **Verification gate:** A teammate not involved in a task follows the runbook on a clean machine; every number in docs traces to an artifact; claims match delivered features.
- **Failure conditions:** Docs describing undelivered features; numbers without artifacts.
- **Definition of Done:** AC-013 satisfied.

---

## Risk register (top risks)

| ID | Risk | Phase hit | Mitigation |
|---|---|---|---|
| RK-1 | No usable mapping from dataset labels to four classes (U-02/03) | 2 | Early CN-003 inspection; human decision; adjust dataset role/class set |
| RK-2 | CICFlowMeter can't be installed/run or output differs from dataset features (U-04/05) | 6 | Do CN-013 early; parity check; fallback RID-10 by team decision |
| RK-3 | SVM too slow on full data | 3 | RID-06 subsample/LinearSVC, disclosed |
| RK-4 | Session-level leakage inflates scores (U-17) | 2/4 | Group-aware split if identifiers exist; report caveat |
| RK-5 | Live capture needs privileges/drivers not available on demo machine (U-13) | 7 | Verify early (CN-001 env script); keep PCAP demo as primary |
| RK-6 | Results lower than Review-1's claimed range (U-08) | 4/10 | Report honestly with analysis; no tuning on test |
| RK-7 | Scope creep | all | AGENTS.md scope rules; cut-lines above |
