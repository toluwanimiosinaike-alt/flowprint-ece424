# Member B 62-app observation-window experiment

## Summary

Member B ran the paired FlowPrint activity-window comparison on
`results/flows_ndss.p`, the 62-app NDSS-format pickle. The 30-second and
10-second conditions used identical training and evaluation splits and held
`batch=300`, `correlation=0.1`, and `similarity=0.9` constant.

| Split | Window | Accuracy | Weighted precision | Weighted recall | Weighted F1 | Evaluation flows |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 30 s | 0.5271 | 0.3953 | 0.5271 | 0.4358 | 258 |
| Validation | 10 s | 0.4147 | 0.3215 | 0.4147 | 0.3437 | 258 |
| Test | 30 s | 0.4789 | 0.3769 | 0.4789 | 0.3922 | 332 |
| Test | 10 s | 0.4096 | 0.3322 | 0.4096 | 0.3380 | 332 |

Reducing the activity window changed test accuracy from 47.89% to 40.96%, a
decrease of 6.93 percentage points. Weighted F1 decreased from 0.3922 to
0.3380. Validation showed the same direction: accuracy decreased by 11.24
percentage points and weighted F1 decreased by 0.0921.

## Dataset and protocol

- Input: `results/flows_ndss.p`
- Input SHA-256:
  `672eb25175eb92cce4550fa321edc664667f652e861dfb5bd62b4bd607086357`
- Total input: 1,405 flows across 62 labels
- Per-label chronological 60%/20%/20% split
- Training flows: 813
- Validation flows: 258
- Test flows: 332
- One label had fewer than three flows and was excluded under `--min-flows 3`
- Python: 3.13.14
- Seed: `PYTHONHASHSEED=0`

The chronological split is at flow level, so flows from a single capture or
session can occur in more than one split. Results are therefore estimates for
this prepared dataset and are not capture-independent generalization evidence.

## Input compatibility

`results/flows.p` contains 1,407 package-style FlowPrint flows across the same
62 labels, but it uses the package's `flowprint.flows` object format. The
NDSS branch's recognizer could not execute those objects directly: the
package-format object API differs from the NDSS `Flow` API. The
`flows_ndss.p` file was produced in the NDSS format and is the valid input for
this run.

## Reproducibility

```powershell
$env:PYTHONHASHSEED = "0"
python experiments\recognition\observation_window.py `
  --load results\flows_ndss.p `
  --output experiments\recognition\results\member_b_62app_flows_ndss_metrics.csv `
  --min-flows 3
Remove-Item Env:\PYTHONHASHSEED
```

The seeded run was repeated with the same CSV values. The metrics CSV SHA-256
is `e8ad8a560148c4bab07802a1b8e9d2a6f36838eb319719f7c8eae348d58dd7fe`.

## Evidence files

- `member_b_62app_flows_ndss_metrics.csv`: exact four-row metrics
- `member_b_62app_flows_ndss_metrics.log`: run trace
- `member_b_62app_flows_ndss_report.md`: protocol and interpretation
