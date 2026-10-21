# FlowSentry — Dataset Instructions
# data/README.md
# ─────────────────────────────────────────────────────────────────────────────
# This file is committed to git. Dataset files are NOT — they are in
# data/raw/ which is git-ignored. See .gitignore.
# ─────────────────────────────────────────────────────────────────────────────

# FlowSentry Dataset Guide

FlowSentry uses two benchmark datasets named in the Review-1 document.
They are **not included** in this repository (datasets are large and have
their own licences). You must download them manually from their official
sources and place them under `data/raw/`.

---

## Dataset 1 — ISCX-VPN2016

| Field | Value |
|---|---|
| Official name | ISCX VPN-nonVPN Traffic Dataset |
| Maintained by | Canadian Institute for Cybersecurity (CIC), University of New Brunswick |
| Source URL | https://www.unb.ca/cic/datasets/vpn.html |
| Citation | Draper-Gil G. et al. (2016). "Characterization of Encrypted and VPN Traffic Using Time-Related Features." ICISSP. |
| Licence | Academic use only; check current terms at the source URL. |
| Expected path | `data/raw/ISCX-VPN2016/` |
| Acquisition date | *(fill in when you download)* |
| Dataset version / date | *(fill in from the dataset page)* |
| SHA-256 checksums | *(generated automatically by CN-002: `python -m preprocessing.ingest`)* |

---

## Dataset 2 — CIC-IDS2017

| Field | Value |
|---|---|
| Official name | CIC-IDS2017 Intrusion Detection Evaluation Dataset |
| Maintained by | Canadian Institute for Cybersecurity (CIC), University of New Brunswick |
| Source URL | https://www.unb.ca/cic/datasets/ids-2017.html |
| Citation | Sharafaldin I. et al. (2018). "Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization." ICISSP. |
| Licence | Academic use only; check current terms at the source URL. |
| Expected path | `data/raw/CIC-IDS2017/` |
| Acquisition date | *(fill in when you download)* |
| Dataset version / date | *(fill in from the dataset page)* |
| SHA-256 checksums | *(generated automatically by CN-002: `python -m preprocessing.ingest`)* |

> ⚠️ **Open question (U-02):** CIC-IDS2017 is primarily an intrusion-detection
> dataset. Whether it contains usable **application-category** labels
> (Web Browsing, VoIP, Streaming, File Transfer) must be verified during
> the CN-003 inspection step. Do **not** assume it is usable for FlowSentry's
> four target classes until the inspection report confirms it.
>
> ⚠️ **Open question (U-16):** ISCX-VPN2016 contains both VPN and non-VPN
> traffic variants. Whether these map to the same target class or are handled
> separately must be decided by the team at CN-004.

---

## Step-by-step: obtaining the data

1. Visit the source URL for each dataset; read and accept the licence terms.
2. Download the dataset files (CSV flows and/or PCAP files, depending on U-04).
3. Place files under `data/raw/<DatasetName>/`, e.g.:
   ```
   data/raw/ISCX-VPN2016/TimeBasedFeatures-Dataset-15s-VPN.csv
   data/raw/CIC-IDS2017/MachineLearningCSV/Monday-WorkingHours.pcap_ISCX.csv
   ```
4. Fill in the acquisition date and version in this file.
5. Run ingestion to generate checksums and a manifest:
   ```
   python -m preprocessing.ingest --raw-dir data/raw --out data/processed/manifest.json
   ```
   (CN-002 — available after Phase 2 is started)
6. Do **NOT** commit any dataset files (enforced by `.gitignore`).

---

## data/ directory structure

```text
data/
├── raw/           ← immutable; git-ignored; dataset files go here
├── processed/     ← generated; git-ignored; train/test splits, manifests
├── sample/        ← tiny samples (if licence permits) or clearly-synthetic fixtures
└── README.md      ← this file (committed to git)
```

`data/raw/` and `data/processed/` are git-ignored.
`data/sample/` may contain committed files **only if** the dataset licence explicitly
permits redistribution of samples, or if the files are clearly synthetic/self-generated.
