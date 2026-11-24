# N05 – Stress-Testing FlowPrint (ECE 424, Fall 2026)

**Team:** Tolu Osinaike, Alex Tornopsky, Jordan Furtado
**Paper:** van Ede et al., *FlowPrint: Semi-Supervised Mobile-App Fingerprinting on Encrypted Network Traffic*, NDSS 2020
**Code base:** authors' repository, `NDSS` branch (https://github.com/Thijsvanede/FlowPrint/tree/NDSS), plus the authors' released `flowprint` pip package

This file documents the baseline reproduction and dataset preparation (owner: Tolu Osinaike) and how the stress-test runs (observation window: Alex; training-set size: Jordan) were produced.

---

## 1. Environment

| Item | Version |
|---|---|
| OS | Windows 11 (64-bit), CPU only (Intel i7-1255U, 16 GB RAM) |
| Python | 3.15.1 |
| tshark (Wireshark) | 4.6.9 |
| Python packages | `flowprint` (pip), `argformat`, `scikit-learn`, `numpy`, `pyshark`, `networkx`, `cryptography` |

```powershell
pip install flowprint argformat
# tshark: install Wireshark, then add it to PATH for the session
$env:Path += ";C:\Program Files\Wireshark"
tshark --version
```

## 2. Dataset

- **Source:** Andrubis subset linked in the authors' `datasets/README.md`:
  https://drive.google.com/drive/folders/1IXa3IJS9zJS4vggpyU7yda8f7jZjz4gB
- **Used:** 62 apps, 124 captures (2 sandbox runs per app). Captures are not committed (size); the exact files used are listed in `results/used_captures.tsv`.
- **Layout on disk:** `experiments/data/Andrubis/<app hash>/<run hash>/allowed_traffic.dump`
- **Labels:** each capture is labelled by its top-level `<app hash>` folder (all files share the name `allowed_traffic.dump`, so the folder is the only app identifier). The download did not include the authors' `appdict.p` / `vt.p`, so labels are hashes, not app names, and no benign/malicious split is possible.

## 3. What was run

### 3a. Baseline with the NDSS experiment code (Tolu)

```powershell
# Build flows with the NDSS preprocessor (same 62 apps, same labels)
python prep_andrubis_ndss.py experiments\data\Andrubis results\flows_ndss.p --max-apps 62

cd experiments\recognition
$env:PYTHONHASHSEED = "0"   # makes FlowPrint's clustering deterministic (see Section 6)
# As released (see Section 4)
python recognition.py       -l ..\..\results\flows_ndss.p -b 300 -w 30 -c 0.1 -s 0.9 -k 1 2>&1 | Tee-Object -FilePath ..\..\results\logs\ndss_baseline.log
# With the train/test split restored
python recognition_split.py -l ..\..\results\flows_ndss.p -b 300 -w 30 -c 0.1 -s 0.9 -k 1 2>&1 | Tee-Object -FilePath ..\..\results\logs\ndss_baseline_split.log
cd ..\..
```

Parameters are the paper's defaults: batch 300 s, window 30 s, correlation 0.1, similarity 0.9.

### 3b. Stress tests with the FlowPrint package (Alex, Jordan)

```powershell
python run_experiments.py experiments\data\Andrubis 62   # prep + 6 runs, random_state 42
python compute_metrics.py                                # scores the logs -> results\metrics.csv
```

| Run | Batch (observation) | Window | Test fraction |
|---|---|---|---|
| baseline | 300 s | 30 s | 0.50 |
| obs_120s / obs_60s / obs_30s | 120 / 60 / 30 s | 30 s | 0.50 |
| train_25pct / train_10pct | 300 s | 30 s | 0.75 / 0.90 |

The package's `--recognition` mode prints one prediction per test fingerprint and no scores; `compute_metrics.py` parses those lines and computes accuracy and weighted precision/recall/F1 **per fingerprint**.

## 4. Modification to the authors' code

`experiments/recognition/recognition.py` (NDSS branch) contains, at the start of `Recogniser.run`:

```python
# TODO remove
return self.evaluate(X, y, X, y, ...)
```

This returns before the train/test split, so the released script **trains and tests on the same flows** (its log shows `Flows: 2810` = 2 × 1405). We left `recognition.py` unchanged and created `recognition_split.py`, identical except that these three lines are commented out, which restores the authors' own split code below it (k-fold over labels, then `train_test_split(test_size=0.33, random_state=i)`). Its log shows `Flows: 1405`.

**Other changes to the authors' files (separate commit):**

- `flowprint/cluster.py`, `flows.py`, `main.py`, `preprocessor.py`, `reader.py`, `split.py`: study notes added as comments and docstrings while walking through the code. No code behaviour changed.
- `flowprint/split.py`, `Splitter.split_labels()`: `np.unique(labels)` changed to `np.unique(y)`. The original refers to an undefined name and would raise `NameError`. This method is not called by any run reported here (recognition uses `k_fold_label()`).

## 5. Results

### Baseline (per-flow scoring, 62 apps, 1405 flows)

| Run | Accuracy | Precision | Recall | F1 | Log |
|---|---|---|---|---|---|
| Paper, Table IV, Andrubis, apps ≥1 flow | 0.5871 | 0.5842 | 0.5871 | 0.5856 | (paper) |
| NDSS code, train/test split restored (`PYTHONHASHSEED=0`) | **0.7328** | 0.7291 | 0.7328 | 0.7189 | `results/logs/ndss_baseline_split.log` (repeat: `ndss_baseline_split_check.log`) |
| NDSS code as released (tests on training data) | 0.9744 | 0.9755 | 0.9744 | 0.9745 | `results/logs/ndss_baseline.log` |

### Stress tests (per-fingerprint scoring, FlowPrint package)

| Run | Test fingerprints | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|---|
| baseline (300 s, 50% train) | 92 | 0.5761 | 0.6620 | 0.5761 | 0.5900 |
| obs_120s | 102 | 0.5686 | 0.6664 | 0.5686 | 0.5833 |
| obs_60s | 109 | 0.5229 | 0.6618 | 0.5229 | 0.5466 |
| obs_30s | 118 | 0.4746 | 0.5806 | 0.4746 | 0.4839 |
| train_25pct | 112 | 0.3750 | 0.4091 | 0.3750 | 0.3641 |
| train_10pct | 108 | 0.2037 | 0.2640 | 0.2037 | 0.2049 |

Source: `results/metrics.csv`, computed from `results/logs/*.log`.

## 6. Limitations

- 62 apps vs. thousands in the paper; a single run (random_state 42) per setting, so differences of 1–2 points are within noise.
- FlowPrint's clustering depends on the iteration order of Python sets, which changes with Python's per-process hash seed. Without a fixed seed, the NDSS baseline varied between runs (we observed accuracy 0.718 to 0.733). The reported baseline uses `PYTHONHASHSEED=0`; two runs gave identical results. The stress-test runs and the as-released 0.9744 run were not seeded.
- NDSS baseline uses a 67/33 random flow split; the paper splits each app's traffic 50:50. Stress tests use a random 50/50 (or 25/75, 10/90) split, not a separate validation/test split.
- Stress-test scores are per fingerprint, the NDSS baseline and the paper are per flow — compare trends, not absolute values, across the two.
- Unseen-app detection (proposal extension) was not run.

## 7. Files

| File | Purpose |
|---|---|
| `prep_andrubis.py` | Andrubis captures → labelled flows (pip package format) |
| `prep_andrubis_ndss.py` | Same, using the NDSS preprocessor (for `recognition.py`) |
| `run_experiments.py` | Runs the 6 stress-test configurations |
| `compute_metrics.py` | Scores the stress-test logs → `results/metrics.csv` |
| `experiments/recognition/recognition_split.py` | NDSS recognition script with the train/test split restored |
| `results/logs/` | Raw output of every run |
| `results/used_captures.tsv` | Exact captures and labels used |
