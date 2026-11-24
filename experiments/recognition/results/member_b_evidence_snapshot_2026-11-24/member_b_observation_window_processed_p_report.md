# Member B observation-window experiment

## Result summary

We compared FlowPrint's activity-correlation window at 30 seconds (baseline)
and 10 seconds (reduced), using the Member A prepared input
`experiments/data/processed.p`.

| Split | Window | Accuracy | Weighted precision | Weighted recall | Weighted F1 | Eval flows |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 30 s | 0.2862 | 0.0819 | 0.2862 | 0.1274 | 297 |
| Validation | 10 s | 0.3636 | 0.8026 | 0.3636 | 0.2752 | 297 |
| Test | 30 s | 0.9900 | 0.9903 | 0.9900 | 0.9900 | 300 |
| Test | 10 s | 0.9067 | 0.9294 | 0.9067 | 0.9099 | 300 |

On this pilot's test split, reducing the activity window from 30 s to 10 s
reduced accuracy by 8.33 percentage points and weighted F1 by 0.0802.
Validation moved in the opposite direction: accuracy rose by 7.74 points at
10 s. This split disagreement does not support a reliable, general
degradation claim.

## Protocol and evidence

- Input pickle SHA-256:
  `c48d1cf672e221369578525a2cc3bc6ae84d10e813e34b13bc3f4243bc2e8b4f`
- Loaded input: 1,490 NDSS FlowPrint flows, 2 labels (`spotify`: 429,
  `youtube`: 1,061).
- Per-label chronological split: 60% train, 20% validation, 20% test.
- Shared training population: 893 flows; validation: 297; test: 300.
- Fixed parameters: `batch=300`, `correlation=0.1`, `similarity=0.9`.
- Only the FlowPrint activity `window` changed (30 s versus 10 s).
- Runtime: Python 3.13.14, NumPy 2.5.4, scikit-learn 1.9.1, NetworkX 3.7,
  cryptography 50.0.2.
- `PYTHONHASHSEED=0` was set before each run. A second evaluation produced a
  byte-for-byte identical metrics CSV (SHA-256
  `d3f9ad5e08449f3acec0229c99ba40df94d36328cbd212ab824896c3ffb06693`).
- The synthetic split self-test passed.

The exact run output is in `member_b_observation_window_processed_p_run.log`;
the full-precision values are in `member_b_observation_window_processed_p.csv`.
`member_b_observation_window_processed_p.png` is a slide-ready plot.

## Scope and limitations — read before presenting

This run uses the available two-app laptop trace pickle documented in the
project README. It is **not** the 62-app Andrubis dataset listed in
`used_captures.tsv`; those manifest paths refer to a Lenovo-specific directory
and the capture files are not included here. Do not describe this result as an
Andrubis rerun or as Member A's 62-app baseline.

There are only two labels, and the chronological split is at flow level.
Flows from the same capture/session can therefore occur in training,
validation, and test. The very high test score at 30 s, low validation scores,
and opposite validation trend make these results a pipeline demonstration,
not a capture-independent performance estimate or a reproduction of the
paper. Use them in a presentation only with these caveats clearly visible.

The local `results/metrics.csv` is also not a substitute for this experiment:
`run_experiments.py` varies batch duration for its `obs_*` runs while holding
the activity window at 30 s.

## Reproduction

From the project root in PowerShell:

```powershell
$env:PYTHONHASHSEED = "0"
python experiments\recognition\observation_window.py `
  --load experiments\data\processed.p `
  --output results\member_b_observation_window_processed_p.csv
Remove-Item Env:\PYTHONHASHSEED
```

The current Member B harness self-test can be run with:

```powershell
python experiments\recognition\observation_window.py --self-test
```
