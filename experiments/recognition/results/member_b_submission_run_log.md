# seeded submission run

## Input and protocol

The submission input was freshly generated from the local offline archives
and saved as `member_b_submission_data_flows.p`; it was not loaded from the
earlier `member_b_user_data_flows.p`. The preprocessing command and complete
output are recorded in `member_b_submission_preprocess.log`. It sampled 32
captures across `pcaps_a`, `pcaps_f`, `pcaps_4`, and `pcaps_5`, producing
12,550 packets, 885 TCP/UDP flows, 32 APK-hash labels, and zero PCAP capture
errors. The evaluator excluded two labels containing four flows in total for
having fewer than three flows; the reported metrics use 881 flows across 30
labels.

Flows were sorted chronologically within each label and partitioned 60/20/20
into train, validation, and test. Both window conditions used the same splits
and training data. `batch=300`, `correlation=0.1`, and `similarity=0.9` were
held fixed; only the correlation window changed, from 30 seconds to 10 seconds.
This changes FlowPrint's activity-correlation parameter; it does not truncate
the packet capture.

## Exact evaluation command

Run from the repository root in PowerShell. The hash seed must be set before
Python starts; this seeded invocation is the canonical one for the submission.

```powershell
python experiments\recognition\preprocess_andrubis_sample.py `
  --max-apps-per-archive 8 `
  --max-captures-per-app 1 `
  --output experiments\recognition\results\member_b_submission_data_flows.p

$env:PYTHONHASHSEED = "0"
python experiments\recognition\observation_window.py `
  --load experiments\recognition\results\member_b_submission_data_flows.p `
  --output experiments\recognition\results\member_b_submission_metrics.csv
Remove-Item Env:\PYTHONHASHSEED
```

The synthetic harness sanity check was also rerun:

```powershell
python experiments\recognition\observation_window.py --self-test
```

Result: **PASS**. All 14 synthetic flows across three labels were assigned to
disjoint chronological train/validation/test splits, and the 30-second
baseline and 10-second reduced settings were verified.

## Results

| Split | Window | Accuracy | Weighted precision | Weighted recall | Weighted F1 | Evaluation flows |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 30s | 0.7866 | 0.7330 | 0.7866 | 0.7561 | 164 |
| Validation | 10s | 0.7866 | 0.7330 | 0.7866 | 0.7561 | 164 |
| Test | 30s | 0.7750 | 0.7844 | 0.7750 | 0.7678 | 200 |
| Test | 10s | 0.7500 | 0.7423 | 0.7500 | 0.7315 | 200 |

Validation accuracy was unchanged. Test accuracy was 2.5 percentage points
lower at 10 seconds, and test weighted F1 was 0.0363 lower. This is a bounded
pilot, not a full reproduction: archive-order sampling selected one capture
for each of the first eight APK-hash groups per archive, and a flow-level split
can place flows from the same capture in separate partitions.

## Output files and limitations

- `member_b_submission_metrics.csv` is the canonical four-row metrics file.
- `member_b_submission_metrics.log` is the console output from that same run.
- `member_b_submission_data_flows.p` is the fresh input pickle used for these metrics.
- `member_b_submission_preprocess.log` documents preprocessing and the
  VirusTotal archive read error.
- `member_b_submission_data_flows_virustotal.csv` contains the recovered
  annotations; they were not used for recognition labels or metrics.
- VirusTotal annotations were not used for labels or recognition metrics.
  The archive yielded eight reports before ending with
  `ReadError: unexpected end of data`.
- Earlier unseeded evaluation runs produced different metrics. Do not mix
  their CSVs or logs with the canonical seeded outputs above.
- If the real-data pickle is missing or invalid, use the synthetic self-test
  as the documented fallback for checking the harness only; it is not a
  fallback performance result.
