# N05 – Stress-Testing FlowPrint (ECE 424, Fall 2026)

**Team:** Tolu Osinaike, Alex Tornopsky, Jordan Furtado
**Paper:** T. van Ede et al., "FlowPrint: Semi-Supervised Mobile-App Fingerprinting on Encrypted Network Traffic," NDSS 2020. doi: 10.14722/ndss.2020.24412. PDF: https://www.ndss-symposium.org/wp-content/uploads/2020/02/24412-paper.pdf
**Code base:** authors' repository, `NDSS` branch (https://github.com/Thijsvanede/FlowPrint/tree/NDSS)

This file documents the **baseline reproduction and dataset preparation** (owner: Tolu Osinaike). The observation-window and training-set-size experiments are documented by their owners in `experiments/recognition/` (Alex) and `experiments/training_size/` (Jordan).

---

## 1. Environment

| Item | Version |
|---|---|
| OS | Windows 11 (64-bit), CPU only (Intel i7-1255U, 16 GB RAM) |
| Python | 3.15.1 |
| tshark (Wireshark) | 4.6.9 |
| Python packages | `scikit-learn`, `numpy`, `pyshark`, `networkx`, `cryptography` (installed via `pip install flowprint`) |

```powershell
pip install flowprint
# tshark: install Wireshark, then add it to PATH for the session
$env:Path += ";C:\Program Files\Wireshark"
tshark --version
```

## 2. Dataset

- **Source:** Andrubis subset linked in the authors' `datasets/README.md`:
  https://drive.google.com/drive/folders/1IXa3IJS9zJS4vggpyU7yda8f7jZjz4gB
- **Used:** 62 apps, 124 captures (2 sandbox runs per app), 1,405 flows. Captures are not committed (size); the exact files used and their labels are listed in `results/used_captures.tsv`.
- **Layout on disk:** `experiments/data/Andrubis/<app hash>/<run hash>/allowed_traffic.dump`
- **Labels:** each capture is labelled by its top-level `<app hash>` folder (all files share the name `allowed_traffic.dump`, so the folder is the only app identifier). The download did not include the authors' `appdict.p` / `vt.p`, so labels are hashes, not app names, and no benign/malicious split is possible.

## 3. What was run

```powershell
# Build flows with the NDSS preprocessor (62 apps, labelled by app folder)
python prep_andrubis_ndss.py experiments\data\Andrubis results\flows_ndss.p --max-apps 62

cd experiments\recognition
$env:PYTHONHASHSEED = "0"   # makes FlowPrint's clustering deterministic (see Section 6)
# As released (see Section 4)
python recognition.py       -l ..\..\results\flows_ndss.p -b 300 -w 30 -c 0.1 -s 0.9 -k 1 2>&1 | Tee-Object -FilePath ..\..\results\logs\ndss_baseline.log
# With the train/test split restored
python recognition_split.py -l ..\..\results\flows_ndss.p -b 300 -w 30 -c 0.1 -s 0.9 -k 1 2>&1 | Tee-Object -FilePath ..\..\results\logs\ndss_baseline_split.log
cd ..\..
```

Parameters are the paper's defaults: batch 300 s, window 30 s, correlation 0.1, similarity 0.9. Expected output of the second run: `Number of flows: 1405`, `Flows: 1405`, `Accuracy : 0.7328`.

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

Per-flow scoring, 62 apps, 1,405 flows.

| Run | Accuracy | Precision | Recall | F1 | Log |
|---|---|---|---|---|---|
| Paper [1, Table IV], Andrubis, apps ≥1 flow | 0.5871 | 0.5842 | 0.5871 | 0.5856 | (paper) |
| NDSS code, train/test split restored (`PYTHONHASHSEED=0`) | **0.7328** | 0.7291 | 0.7328 | 0.7189 | `results/logs/ndss_baseline_split.log` (repeat: `ndss_baseline_split_check.log`) |
| NDSS code as released (tests on training data) | 0.9744 | 0.9755 | 0.9744 | 0.9745 | `results/logs/ndss_baseline.log` |

0.7328 falls inside the paper's own Andrubis range across its minimum-flow filters (0.503 to 0.811, [1, Table IV]). It is higher than the ≥1-flow row mainly because we choose among 62 apps rather than thousands, and the authors' script trains on 67% of flows rather than 50%.

## 6. Limitations

- 62 apps vs. thousands in the paper; a single seeded run, so differences of 1–2 points are within noise.
- FlowPrint's clustering depends on the iteration order of Python sets, which changes with Python's per-process hash seed. Without a fixed seed the baseline varied between runs (we observed accuracy 0.718 to 0.733). The reported baseline uses `PYTHONHASHSEED=0`; two runs gave identical results. The as-released 0.9744 run was not seeded.
- The authors' script uses a 67/33 random flow split; the paper describes a 50:50 split of each app's traffic.
- Unseen-app detection (proposal extension) was not run.

## 7. Files

| File | Purpose |
|---|---|
| `prep_andrubis_ndss.py` | Andrubis captures → labelled flows, using the NDSS preprocessor |
| `experiments/recognition/recognition_split.py` | NDSS recognition script with the train/test split restored |
| `results/logs/ndss_baseline.log`, `ndss_baseline_split.log`, `ndss_baseline_split_check.log` | Raw output of the baseline runs |
| `results/used_captures.tsv` | Exact captures and labels used (written by `prep_andrubis.py`, which selects the same 62 apps and labels) |

`prep_andrubis.py`, `run_experiments.py`, `compute_metrics.py` and `results/metrics.csv` are exploratory runs with the pip package; they are not part of the results reported here.

## References

[1] T. van Ede, R. Bortolameotti, A. Continella, J. Ren, D. J. Dubois, M. Lindorfer, D. Choffnes, M. van Steen, and A. Peter, "FlowPrint: Semi-Supervised Mobile-App Fingerprinting on Encrypted Network Traffic," in *Proc. Network and Distributed System Security Symposium (NDSS)*, 2020. doi: 10.14722/ndss.2020.24412.

[2] M. Lindorfer, M. Neugschwandtner, L. Weichselbaum, Y. Fratantonio, V. van der Veen, and C. Platzer, "ANDRUBIS – 1,000,000 Apps Later: A View on Current Android Malware Behaviors," in *Proc. BADGERS*, 2014.
