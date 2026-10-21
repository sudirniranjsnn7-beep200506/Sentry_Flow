# FlowSentry
**Machine Learning Based Network Traffic Classification Using Flow Features**
*Computer Networks project — Review-1 specification*

> **Project status: Phase 0 — Specification complete. Nothing is implemented yet.**
> No dataset has been processed, no model has been trained, and **no performance results exist**. Sections marked *(planned)* describe intended behaviour, not working features.

**Team (per Review-1):** Sudir Niranj R (24BDS0267) · Vishal B S (24BCE2475)

## What is FlowSentry?
Traffic classification by port numbers is unreliable (dynamic/random ports, P2P tunnelling) and Deep Packet Inspection is costly, privacy-invasive and ineffective on encrypted traffic (Review-1). FlowSentry classifies traffic by **how a flow behaves** — timing, packet sizes, directions, TCP flags — and **never reads payloads**.

```text
Network Packets
      ↓
Five-Tuple (Src IP, Dst IP, Src Port, Dst Port, Protocol)
      ↓
Bidirectional Flow
      ↓
Flow-Level Statistical Features (time · volume · TCP flags · directional ratios)
      ↓
Machine Learning (Decision Tree · Random Forest · SVM · XGBoost)
      ↓
Traffic Classification (Web Browsing · VoIP · Streaming · File Transfer)
```
Target classes follow Review-1; the final class set is subject to decision U-01 (Review-1's figure abbreviates to "Web / VoIP / Media").

## Pipeline *(planned)*
```text
Traffic / PCAP / Live Interface → Flow Generation → Five-Tuple Grouping → Feature Extraction
→ Preprocessing → Feature Selection → Model Training → Evaluation → Best Model
→ PCAP / Live Inference → Classification → Dashboard
```

## Capabilities and delivery status
| Capability | Status |
|---|---|
| Dataset ingestion, inspection, preprocessing | Not started (CN-002…005) |
| Four-model training & tuning | Not started (CN-006…009) |
| Evaluation & comparison (Accuracy, Precision, Recall, F1) | Not started (CN-010, 011) |
| Model registry | Not started (CN-012) |
| CICFlowMeter integration (via adapter) | Not started — implementation/version unverified (CN-013) |
| PCAP classification | Not started (CN-014, 015) |
| Live / near-live classification | Not started — **optional**, delivered only if verified (CN-016, 017) |
| Dashboard | Not started — optional (CN-018) |
| Test & demo packaging | Not started (CN-019…022) |

## Technology (Review-1 stack)
Python · Pandas · scikit-learn · XGBoost · Scapy · Tshark/Wireshark · CICFlowMeter · benchmark datasets ISCX-VPN2016 and CIC-IDS2017.
Additional helper libraries (joblib, PyYAML, matplotlib, pytest, a dashboard library) are *recommended decisions*, justified in the task reports.

## Documentation map
| File | Purpose |
|---|---|
| `PRD.md` | Product requirements (what) — requirement IDs FR/ML/DS/FE/TC/PC/RT/DB/EV/NFR/AC |
| `TRD.md` | Technical design (how) — includes the Dataset → Target Label Mapping, decision register (RID-xx) and unresolved items (U-xx) |
| `AGENTS.md` | Rules for AI coding agents (anti-hallucination, ML/network rules, verification reports) |
| `BUILD_PLAN.md` | Phases 0–10, dependencies, gates, risks |
| `TASKS.md` | Tasks CN-001…CN-022 |

## Repository structure
```text
flowsentry/
├── PRD.md TRD.md AGENTS.md README.md BUILD_PLAN.md TASKS.md
├── requirements.txt  .env.example
├── config/      common/      data/       capture/   flow/
├── preprocessing/  models/   evaluation/ inference/ dashboard/
├── scripts/     tests/       artifacts/ (generated, git-ignored)   docs/
```
(Details in `TRD.md` §3.)

## Prerequisites *(to be verified in CN-001 / CN-013 — nothing below has been tested)*
- Python (version recorded at CN-001)
- The benchmark datasets, downloaded by the team from their official sources, respecting licences (`data/README.md`)
- CICFlowMeter — implementation, version and runtime **not yet decided/verified** (U-05)
- For capture: Tshark and/or Scapy, plus a capture driver and privileges (e.g., Npcap on Windows) — only for the optional live mode

## Quick start *(planned — commands will be filled in with the exact, tested commands at CN-022)*
```text
1. Create virtual environment and install requirements
2. Place datasets under data/raw/ (see data/README.md)
3. Ingest → inspect → (team approves label mapping) → preprocess
4. Train four models → evaluate → compare → register best model
5. Classify a PCAP
6. (optional) live classification  7. (optional) dashboard
```

## Important caveats
- **No numbers yet.** Review-1's abstract quotes accuracy "upwards of 95–98%". FlowSentry treats that as an unverified claim; this project's own results, once produced, will appear here with references to their artifact files.
- **Label mapping is unresolved.** Dataset labels have not yet been mapped to FlowSentry's target classes ("To be finalized before model training"). See `TRD.md` §6.
- Flow statistics cannot see payload; some applications may be statistically similar, and benchmark datasets may not generalise to other networks.
- Captured traffic can be sensitive. Capture only where you are authorised; PCAPs and datasets are never committed to git.

## Working with an AI coding agent
Give the agent `AGENTS.md` first, then one task at a time from `TASKS.md`. Every task ends with a verification report (what changed, files, tests executed, exact commands, results, limitations).

## References (as cited in Review-1; not independently verified here)
Nguyen & Armitage (2008), *IEEE Communications Surveys*; Lashkari et al. (2016), ICISSP; Enisoglu & Rakocevic (2023), IEEE IWCMC. Dataset citations to be added from official dataset pages at CN-002.
