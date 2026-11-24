# Alex Tornopsky Midpoint Contribution

## 1. Bounded-contribution plan: changes beyond the baseline

### Research contribution

The bounded question is whether FlowPrint's known-application recognition
changes when its activity-correlation window is reduced from the baseline
30 seconds to 10 seconds. Other parameters are held constant:
`batch=300`, `correlation=0.1`, and `similarity=0.9`. This tests the effect of
FlowPrint's temporal correlation parameter; it does not truncate captures or
simulate a shorter packet capture.

### Comparison with the original checkout

The working checkout was compared with
`C:\Users\alext\Downloads\FlowPrint-NDSS-original\FlowPrint-NDSS`.
The shared `experiments/recognition/recognition.py` file is byte-for-byte
identical in both trees. Thus Member B did not change FlowPrint's core
recognition, clustering, or fingerprinting algorithms.

The following changes implement the experiment around the existing baseline:

1. **New `experiments/recognition/observation_window.py`.** The original
   checkout does not contain this paired window harness. It creates
   chronological 60/20/20 train/validation/test splits within each label,
   verifies split coverage/disjointness/order in a self-test, calls the
   existing `Recogniser.evaluate` with the same train and evaluation data for
   both window values, and writes accuracy and weighted precision/recall/F1
   to CSV. It calls `evaluate` directly because the unchanged
   `Recogniser.run` has an early return that evaluates the same samples as
   both train and test, which would not provide held-out metrics.
2. **New `experiments/recognition/preprocess_andrubis_sample.py`.** This
   script converts selected gzip-wrapped PCAP archive members into FlowPrint
   `Flow` objects and APK-hash labels. It parses metadata with TShark, includes
   a documented Scapy fallback, extracts only bounded selections to temporary
   storage, counts parse failures, and attempts a VirusTotal hash join. The
   multi-archive workflow added `--pcaps-extra` and `--max-captures-per-app`
   to cover `pcaps_a`, `pcaps_f`, `pcaps_4`, and `pcaps_5` while limiting the
   sample.
3. **One import cleanup in `experiments/recognition/jaccard.py`.** The original
   has an import of `precompute` and `jaccard` from `tcluster.distances`; the
   working copy removes it. These imported names are unused by the active
   `closest` matching path, and the dependency was unavailable in the run
   environment. The executable matching functions were not changed.
4. **Protocol, run logs, and outputs.** These additions document the
   experiment and preserve the inputs/results. They do not change baseline
   algorithm behavior.

This contribution should therefore be described as a bounded experiment and
data-preparation harness around the original FlowPrint baseline, not a new or
modified FlowPrint recognition algorithm.

## 2. Updated experimental protocol and logs

### Data and sampling

The run used the supplied `pcaps_a.tar.gz`, `pcaps_f.tar.gz`,
`pcaps_4.tar.gz`, and `pcaps_5.tar.gz` archives. To respect local storage
limits, selection was deterministic archive order: one capture from each of
the first eight APK-hash groups in each archive, for 32 captures total. This
is a bounded sample, not the full archive contents.

TShark preprocessing produced **12,550 packets and 885 TCP/UDP flows across
32 APK-hash labels**, with zero PCAP capture errors. Two labels had fewer than
three flows (four flows total) and were excluded by the evaluator. Metrics
therefore cover **30 labels and 881 flows**.

### Protocol

1. Preprocess the four archive samples into FlowPrint `(flows, labels)` data.
   The label is the APK hash from the archive path.
2. Sort each label's flows chronologically and split 60%/20%/20% into train,
   validation, and test.
3. Use the same training flows and held-out split for each window setting.
4. Run the existing FlowPrint evaluator at 30s and 10s, keeping all other
   settings constant. Set `PYTHONHASHSEED=0` before launching Python so this
   run uses the same deterministic iteration order as the repeat check.
5. Record accuracy as the primary metric and weighted precision, recall, and
   F1 as supporting metrics.

### Canonical seeded results

The canonical submission output is
`results/member_b_submission_metrics.csv`; its matching console output is in
`results/member_b_submission_metrics.log`. The earlier
`member_b_32_captures_*` metrics are retained as run history and should not be
combined with this seeded result.

| Split | Window | Accuracy | Weighted precision | Weighted recall | Weighted F1 | Evaluation flows |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 30s | 0.7866 | 0.7330 | 0.7866 | 0.7561 | 164 |
| Validation | 10s | 0.7866 | 0.7330 | 0.7866 | 0.7561 | 164 |
| Test | 30s | 0.7750 | 0.7844 | 0.7750 | 0.7678 | 200 |
| Test | 10s | 0.7500 | 0.7423 | 0.7500 | 0.7315 | 200 |

In this seeded run, reducing the window did not change validation accuracy;
test accuracy decreased by 2.5 percentage points. The test weighted F1 also
decreased, from 0.7678 to 0.7315. These are preliminary estimates: selection
was archive-ordered, one capture was used per selected APK, and the splits
were flow-level, so flows from one capture may appear in multiple splits. The
result is not a capture-independent generalization estimate or a reproduction
of the paper's full dataset. Earlier unseeded runs varied, so use the
`PYTHONHASHSEED=0` command below and do not mix their CSVs with this result.

The VirusTotal archive yielded eight reports for the 32 selected APK hashes,
then ended with `ReadError: unexpected end of data`. The recovered annotations
were not used as recognition labels or in the metrics.

### Checkable trace and fallback

Command:

```powershell
python experiments\recognition\observation_window.py --self-test
```

Result: **PASS.** The deterministic synthetic trace assigned all 14 flows
across three labels to disjoint chronological train/validation/test splits
and verified the 30s baseline is greater than the 10s reduced window. If the
real-data snapshot is missing or invalid, use this self-test trace as the
fallback for checking the harness. It is not a fallback performance result
and does not establish FlowPrint accuracy.

### Reproduction and evidence files

Put authorized `pcaps*.tar.gz` files and `virustotal.tar.gz` in
`experiments/recognition/user_data`. The preprocessor discovers all matching
archives there automatically and writes its pickle to the results directory.
For Python 3.13, install `requirements-member-b.txt`; install TShark separately
and make it available on `PATH` (or provide `--tshark`). From the NDSS
repository root:

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

Artifacts:

- `experiments/recognition/observation_window.py` — evaluation harness.
- `experiments/recognition/preprocess_andrubis_sample.py` — bounded archive preprocessor.
- `experiments/recognition/user_data/README.md` — input folder instructions.
- `requirements-member-b.txt` — tested Python 3.13 dependency pins.
- `experiments/recognition/results/member_b_submission_metrics.csv` — canonical four-row metrics output.
- `experiments/recognition/results/member_b_submission_metrics.log` — captured evaluator output matching that CSV.
- `experiments/recognition/results/member_b_submission_data_flows.p` — freshly preprocessed input for this submission run.
- `experiments/recognition/results/member_b_submission_preprocess.log` — preprocessing counts, selected archives, and VirusTotal warning.
- `experiments/recognition/results/member_b_submission_data_flows_virustotal.csv` — recovered annotations; not used in metrics.
- `experiments/recognition/results/member_b_submission_run_log.md` — seeded run command, result, and limitations.
- `experiments/recognition/results/member_b_32_captures_run_log.md` — earlier unseeded run history; not the canonical result.
- `experiments/recognition/results/member_b_user_data_flows.p` — prior prepared input, not used for this fresh submission run.
