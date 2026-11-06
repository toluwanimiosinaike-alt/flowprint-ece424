# FlowPrint Baseline: ECE 424 Midpoint

**Team:** Tolu Osinaike, Alex Tornopsky, Jordan Furtado. **This part:** Tolu Osinaike (baseline reproduction and dataset preparation)

This repository runs the original FlowPrint code from the authors' NDSS branch
(van Ede et al., NDSS 2020, upstream commit `8e088db`), with small fixes so that it runs on current software.

## 1. Setup

```
pip install pyshark scikit-learn numpy networkx cryptography matplotlib pandas
```
Wireshark/tshark is needed only to preprocess new pcap files (install from wireshark.org with **TShark** checked).

## 2. Run (from the repository root)

```
# App recognition (the baseline run)
python experiments/recognition/recognition.py -l experiments/data/processed.p -k 1

# Unseen-app detection (not yet verified)
python experiments/anomaly/anomaly.py -l experiments/data/processed.p -k 1

# Preprocess new pcaps (optional). Put each app's files in experiments/data/<app>/; the folder name is the label.
python flowprint\main.py -f (Get-ChildItem experiments\data\*\*.pcap).FullName -s experiments\data\processed.p
```
All runs use the paper's default parameters: batch 300 s, window 30 s, correlation 0.1, similarity 0.9.

## 3. Code changes

| File | Problem | Fix |
|---|---|---|
| `flowprint/reader.py` | pyshark fails on newer Python ("no current event loop") | Create the event loop explicitly |
| `flowprint/reader.py` | Packet layers read by position caused crashes on ICMP packets; the `SSL` layer name is outdated | Look up IP/TCP/UDP layers by name, skip ICMP, check for `TLS` |
| `experiments/recognition/jaccard.py` | Imports `tcluster`, an unpublished library | Removed the unused import |
| `flowprint/preprocessor.py` | Read errors were hidden | Print the full traceback |
| `experiments/recognition/recognition.py` | An early `return` marked `# TODO remove` evaluated on the training data | Commented it out so the train/test split runs; use `-k 1`, because `-k` ≥ 2 crashes on current scikit-learn |

## 4. Protocol

- **Dataset:** two traces we captured on a team member's own laptop on 2026-11-05 (Spotify web player, YouTube),
  with 1,490 flows in total (429 / 1,061). Raw pcaps are not shared for privacy reasons; `processed.p` contains
  only flow metadata. The paper comparison will use a research dataset subset (ReCon, Cross Platform or Andrubis).
- **Environment:** Windows `<…>`, Python 3.15.`<…>`, tshark 4.6.9, CPU only. Package versions are in `logs/environment.txt`.
- **Seed:** the train/test split uses `random_state = 0`. Fingerprinting has no random components, so runs are
  deterministic.
- **Splits:** a random 67% train / 33% test split at the flow level. There is no validation split yet; parameter
  tuning will use a validation set taken from the training portion only, and the test set stays untouched.

## 5. Baseline run and sanity check

**Baseline run** (`logs/recognition_split.log`):
```
<paste the output of the -k 1 run here>
```

**Sanity check: does the evaluation hold out test data?** Our first run, with the unmodified code
(`logs/recognition_baseline.log`), scored 1.0 on everything. But it reported `Flows: 2980`, exactly 2 × 1,490, and
the test support covered all 1,490 flows. So the training and test sets were identical. The code confirmed it: the
`# TODO remove` early return passes the full dataset as both. After the fix, the test set is a held-out 33%.

Even with a correct split, a high score here is expected. There are only two apps, recorded in separate sessions,
from desktop browsers. This dataset shows that the pipeline works, not how accurate FlowPrint is.

## 6. Fallback trace

If our later snapshot is missing or invalid, use the baseline run above:
`experiments/data/processed.p` (SHA-256 `<…>`) and `logs/recognition_split.log` (SHA-256 `<…>`), Git tag
`midpoint-fallback`. These files will not be changed after the midpoint.

## 7. Evidence

- **Commits:** one per fix in section 3, plus the dataset, logs and this README.
- **Logs:** `recognition_baseline.log` (original code, train = test), `recognition_split.log` (fixed baseline),
  `environment.txt`.
