# AGENTS.md — FlowSentry Agent Operating Contract
**Read this file completely at the start of every session, before touching any file.**
(For Claude Code, create a `CLAUDE.md` containing one line: `Read and obey AGENTS.md.` If your tool does not auto-load `AGENTS.md`, the first prompt in your task instructs it to be read explicitly.)

FlowSentry is a **Computer Networks academic project**: ML-based network traffic classification from **flow-level statistical features, never payload inspection**. It must stay explainable in a university viva. You are a careful engineer, not a researcher: you build what the documents specify, verify it, and report honestly.

---

## 1. Source of Truth

```text
CN Review-1 document → origin of requirements (PRIMARY; summarised in PRD.md)
PRD.md        → Product authority      (WHAT must exist)
TRD.md        → Technical authority    (HOW it is designed)
AGENTS.md     → Agent execution rules  (HOW YOU MUST BEHAVE)
TASKS.md      → Implementation task authority (WHAT TO DO NEXT)
BUILD_PLAN.md → Phase/dependency authority    (IN WHAT ORDER)
```

1. Work **only** on the task you are given (`CN-xxx`). Do not start the next task.
2. If two documents conflict, or a document conflicts with reality (a tool behaves differently than documented), **STOP and report the conflict**. Do not pick silently. Authority: PRD on *what*, TRD on *how*, TASKS on *scope of this task*.
3. Requirement provenance tags: `[SRC]` Review-1, `[BRF]` brief, `[REC]` recommended decision (`RID-xx`), `[UNRES]` unresolved (`U-xx`). **Never promote a `[REC]` or `[UNRES]` item to an established fact.**
4. Do not edit `PRD.md`, `TRD.md`, `BUILD_PLAN.md`, or `AGENTS.md` unless the task explicitly says so. If you believe a document is wrong, report it in the task report instead.

## 2. Unresolved-Decision Gates (hard stops)

If a task depends on an item in `TRD.md` Appendix B (`U-xx`) that is not yet recorded as resolved in `docs/decisions/`, **stop and ask the human**. Specifically:

| Gate | Condition |
|---|---|
| G-LABEL | No training, and no code that assumes target labels, until `config/label_mapping.yaml` has `status: approved` by the team (U-01/U-02/U-03/U-16). |
| G-SCHEMA | No inference code until `config/feature_schema.yaml` exists and train/inference parity is decided (U-04). |
| G-CFM | No CICFlowMeter command is written into config or code until verified and recorded in `docs/verification/cicflowmeter.md` (U-05). |
| G-FALLBACK | The native Scapy extractor fallback (RID-10) is built only after the human records that decision. |
| G-LIVE | No "real-time" claim until latency is measured (RT-004). |

## 3. Anti-Hallucination Rules

You must **never**:
- fabricate APIs, function signatures, CLI flags, or file formats — check the installed version (`--help`, `help()`, docs, source) and cite what you actually observed;
- fabricate commands — every command you report must be one you actually ran;
- fabricate dataset labels, column names, label mappings, row counts, class counts, or dataset statistics — read them from the real files;
- fabricate results, accuracy, F1, latency, throughput, or timing numbers;
- claim tests passed when they were not run, or count **skipped tests as passed**;
- claim real-time/live functionality before an end-to-end test on a real interface with measured latency;
- invent CICFlowMeter behaviour or assume it has a Python API (TRD §22);
- add dependencies unnecessarily. Each new dependency needs a one-line justification in the task report; stdlib/the stack in Review-1 first;
- write "should work" as if it were "works". If something could not be verified in your environment (no dataset, no CICFlowMeter, no capture privileges), say so explicitly and mark it **UNVERIFIED**.

When you do not know: say "I don't know / not verified", propose how to verify, and stop at the gate.

## 4. ML Rules

1. **Prevent data leakage.** Fit every transformer (imputer, scaler, selector, encoder) and every hyperparameter search **only on training data**; cross-validation only inside the training set.
2. **Never train on test data**, and never look at test results to make modelling choices. The test set is loaded only by `evaluation/` via `load_test_set(purpose="final_evaluation")`; `models/` must not import it.
3. **Identical preprocessing between training and inference**: one persisted pipeline object; schema-parity check fails loudly (`SchemaMismatchError`).
4. **Document every feature transformation** (what, why, parameters, fit-on-what) in code docstrings, run artifacts, and registry metadata.
5. **Reproducibility:** seeds from config; record config snapshot, dataset hashes, label-mapping hash, library versions, git commit.
6. Dedupe **before** splitting; handle imbalance on training data only; never alter the test distribution.
7. No performance number appears in any document, README, dashboard, or comment unless produced by a recorded run and traceable to an artifact file.
8. Synthetic/test fixtures are for plumbing only — **never report model performance from synthetic data**.
9. The four models are exactly: Decision Tree, Random Forest, SVM, XGBoost. Do not add or swap models without a PRD change.

## 5. Network Rules

1. Use **flow-level statistical features** (time, volume, TCP-flag, directional-ratio families). **Do not use payload content** for classification, ever.
2. Keep the chain visible in code and docs: packets → five-tuple → bidirectional flow → flow features → ML → class. Use networking terms in names (`flow`, `five_tuple`, `fwd/bwd`, `iat`).
3. IP/MAC identifiers and (by default) port numbers are **not** model inputs (ML-004, RID-07); they may be retained as metadata for display.
4. Avoid unnecessary storage of captured traffic: delete capture chunks after processing by default; never commit PCAPs/captures/datasets; prefer BPF filters/snaplen where verified.
5. Treat captured traffic as **potentially sensitive**. Capture only on networks you are authorised to monitor. Do not capture, store, or print payload; do not log five-tuples above DEBUG.
6. Call external tools (CICFlowMeter, tshark) with `subprocess` **argument lists**, never `shell=True`, never interpolating user-supplied filenames into a shell string.
7. Every capture/extractor command must be **VERIFIED** on the actual installation before being relied on; record it.

## 6. Scope & Simplicity Rules (anti-overengineering)

No Kubernetes, Docker orchestration, microservices, cloud services, message queues, databases, authentication systems, async frameworks, or plugin systems. File-based artifacts, argparse CLIs, plain Python. No refactors outside the task's files. If a task seems to require more, report it instead of building it. Code must be readable by a second-year student: short functions, docstrings, type hints, no cleverness.

## 7. Working Method (every task)

1. Read `AGENTS.md`, then the task in `TASKS.md`, its phase in `BUILD_PLAN.md`, and the cited `PRD`/`TRD` sections.
2. Check dependencies are Done and gates are open. If not → stop and report.
3. State a short plan (files to touch, tests to write). Keep to the task's **Files/Directories**.
4. Implement the minimum that meets the **Implementation Requirements**; honour **Do Not**.
5. Write tests first or alongside. Run them. Run the verification commands in the task.
6. Produce the **Task Report** (§8) and save it to `docs/task_reports/CN-xxx.md`.
7. Stop. Do not start the next task.

## 8. Verification Rules — Task Report (mandatory)

A task is **not complete merely because code was written.** Every task ends with this report, in this order:

```text
Task ID / Name:
What changed:                  (plain-language summary)
Files modified:                (created / modified / deleted, with paths)
Tests executed:                (names; which were skipped and why — skipped ≠ passed)
Exact commands used:           (copy-paste of the commands actually run, in order)
Test results:                  (real output summary: passed / failed / skipped counts)
Verification-gate checks:      (each item from the task's Verification, with ✅ / ❌ / ⚠ UNVERIFIED)
Decisions touched:             (RID-xx / U-xx / gates; anything needing human input)
Dependencies added:            (name, version, justification) or "none"
Known limitations:
Deviations from TASKS/TRD:     (or "none")
Definition of Done:            (met / not met, with reason)
```
If any check failed or could not run, the task status is **NOT DONE** or **DONE WITH UNVERIFIED ITEMS** — say which. Never mark ✅ without evidence from a command you ran.

## 9. Code Conventions

- Python (version per `requirements.txt`/CN-001 verification); type hints; docstrings stating *networking meaning* where relevant.
- Configuration via `config/*.yaml` + `.env`; no hard-coded paths, seeds, or thresholds.
- Errors: use the typed exceptions in `common/errors.py`; fail closed; never swallow exceptions; never silently drop rows (count and report).
- Logging via the `logging` module; no `print` in library code.
- Tests: `pytest`; markers `requires_dataset`, `requires_cicflowmeter`, `requires_capture`.
- Git: one logical commit per task if git is available; message `CN-xxx: <summary>`. Never commit data, PCAPs, models, `.env`, or `artifacts/`.

## 10. Definition of "Stop and Ask"
Stop and ask the human when: a gate is closed; documents conflict; a tool/dataset differs from the docs; a decision belongs to the team (label mapping, class set, fallback extractor, dashboard tech); a task would exceed its scope; you cannot verify something that the task requires.

## 11. Final Self-Check Before Reporting
- [ ] I only touched files listed for this task.
- [ ] Every command in my report was actually run; every number comes from real output.
- [ ] No invented labels, columns, APIs, flags, or results.
- [ ] No leakage; no payload use; no captured data committed.
- [ ] Skipped/unverified items are labelled as such.
- [ ] I did not start the next task.
