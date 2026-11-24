# Member B: observation-window evaluation

## Research question and safe scope

We ask whether FlowPrint's known-application recognition accuracy changes when
the passive observer has a shorter activity-correlation window. The evaluation
uses only FlowPrint's packet/flow metadata features from previously recorded,
authorized traces; it does not inspect payloads, decrypt TLS, access devices,
inject traffic, or identify people. All processing is offline, and any dataset
must be used under its access terms. The scope is limited to one prepared
traffic subset and two preselected window values on CPU.

## Midpoint contribution

Member B's bounded contribution is a paired FlowPrint app-recognition comparison
using the NDSS implementation's activity-correlation window:

| Condition | `window` | Other FlowPrint settings |
|---|---:|---|
| Baseline | 30 seconds | `batch=300`, `correlation=0.1`, `similarity=0.9` |
| Reduced observation | 10 seconds | Same as baseline |

Here, "observation window" means FlowPrint's `window` argument: the time span
used to correlate destination-cluster activity. This experiment does not truncate
packets or change the capture duration. Both values are fixed before evaluation;
the test split is not used to select a value.

### What changed relative to `FlowPrint-NDSS-original`

The original checkout is at `C:\Users\alext\Downloads\FlowPrint-NDSS-original\FlowPrint-NDSS`;
the working checkout is `C:\Users\alext\Downloads\FlowPrint-NDSS\FlowPrint-NDSS`.
A recursive file comparison found no original-only files. Within the shared
source tree, `experiments/recognition/recognition.py` is byte-for-byte identical
in both checkouts. Therefore, the original FlowPrint recognition algorithm and
its `Recogniser.evaluate` implementation were not changed for this contribution.

The Member B-specific changes are:

1. **Added `experiments/recognition/observation_window.py`.** The original has
   no paired observation-window experiment or this chronological three-way
   evaluation harness. The new script makes per-label chronological
   train/validation/test splits, checks coverage and ordering, evaluates the
   existing `Recogniser.evaluate` at 30s and 10s on the same splits, and writes
   accuracy plus weighted precision/recall/F1 to CSV. It calls `evaluate`
   directly rather than `Recogniser.run`: the unchanged original `run` has an
   early return that evaluates `X, y` against the same `X, y`, which is not an
   appropriate held-out comparison.
2. **Added `experiments/recognition/preprocess_andrubis_sample.py`.** The
   original has no helper for streaming the supplied Andrubis archive members
   into a bounded FlowPrint `(flows, labels)` pickle. This helper extracts
   selected gzip-wrapped PCAPs to temporary storage, uses TShark to parse
   packet metadata/certificate fields (with a documented Scapy fallback),
   assigns APK-hash labels, and records archive/parse counts and VirusTotal
   join errors. During the multi-archive run it was extended with
   `--pcaps-extra` and `--max-captures-per-app` so it could sample all four
   archive families without extracting the entire dataset.
3. **Changed one import line in `experiments/recognition/jaccard.py`.** The
   original imports `precompute` and `jaccard` from `tcluster.distances`; the
   working copy removes that import. Those names are unused by the executable
   `closest` path (their remaining mentions are commented-out test code), and
   the dependency was unavailable in the environment. The `closest` and
   `closest_single` implementations themselves are unchanged. This is a
   dependency/import fix, not a change to the matching algorithm.
4. **Added this protocol and run artifacts.** These record the bounded design,
   commands, observed counts, metrics, and limitations; they do not alter
   FlowPrint behavior. The result files are listed in the run log.

The change is therefore an experiment harness and bounded data-preparation
workflow around the original recognizer, plus a small import cleanup needed to
run it in this environment. It should not be described as a modified FlowPrint
recognition algorithm.

The script loads preprocessed `(flows, labels)` pickle data, then splits each
application's flows chronologically into 60% train, 20% validation, and 20%
test. At least three flows per label are required. The same training set is
used for both window settings; each evaluation set is fingerprinted separately.
The primary outcome is known-app accuracy. Weighted precision, recall, and F1
are recorded as secondary diagnostics. The CSV contains a row for each of the
four split/window combinations.

## Running it

From the NDSS repository root, create a Python 3.13 environment using
`requirements-member-b.txt`, then run the dependency-free sanity check:

```powershell
python experiments\recognition\observation_window.py --self-test
```

To make a bounded local Andrubis sample, place all `pcaps*.tar.gz` archives
and `virustotal.tar.gz` in `experiments/recognition/user_data`. The command
samples eight APK-hash groups per archive and one capture per group,
extracting only those captures to a temporary directory, invoking TShark,
and saving the FlowPrint `(flows, labels)` pickle. APK MD5 hashes are used as
labels because application-name metadata is not part of this bounded run.

```powershell
python experiments\recognition\preprocess_andrubis_sample.py `
  --max-apps-per-archive 8 `
  --max-captures-per-app 1 `
  --output experiments\recognition\results\member_b_submission_data_flows.p
```

Install TShark separately; put it on `PATH` or pass its executable using
`--tshark`. The
default data and output folders are derived from the script location. An
alternate input directory can be provided with `--user-data-dir`; explicit
archive paths remain supported.

The script uses the NDSS FlowPrint flow representation and TShark to extract
packet metadata and TLS certificate serials. If TShark is unavailable it uses
a Scapy parser as a documented fallback, with certificate serials set to
`None`; such a run is an exploratory variant, not a full-feature baseline.
The cap above selects one capture for each of the first eight APK-hash groups
in each archive, for up to 32 captures total while covering all four archives.
Matching VirusTotal reports are exported to a separate CSV when present.

This fresh preprocessing run writes the input pickle and a separate
VirusTotal-annotation CSV. Run the window comparison on that pickle:

```powershell
$env:PYTHONHASHSEED = "0"
python experiments\recognition\observation_window.py `
  --load experiments\recognition\results\member_b_submission_data_flows.p `
  --output experiments\recognition\results\member_b_submission_metrics.csv
Remove-Item Env:\PYTHONHASHSEED
```

The prepared pickle must contain an `(X, y)` tuple; `X` contains FlowPrint
`Flow` objects and `y` contains one application label per flow. Multiple pickle
paths can be supplied after `--load`. Output parent directories are created
automatically. The dataset should be prepared and labeled according to its
access terms; this experiment uses only offline traces.

The defaults reproduce the paper implementation's recognition settings
(`batch=300`, `window=30`, `correlation=0.1`, `similarity=0.9`) except for the
deliberately reduced `window=10` condition. Other values can be supplied
explicitly, but changes must be recorded with the results.

## Checkable sanity trace

Command:

```text
python experiments\recognition\observation_window.py --self-test
```

Result:

```text
SANITY CHECK: observation-window protocol
PASS: 14 synthetic flows across 3 labels are fully assigned to disjoint, chronological train/validation/test splits.
PASS: fixed baseline window is 30s and reduced window is 10s.
```

This checks split coverage, disjointness, chronological ordering, and the
baseline/reduced-window ordering. It does not claim a FlowPrint accuracy result.

## Midpoint evidence and run log

| Member | Evidence visible in the checked workspace | Midpoint status |
|---|---|---|
| A | The downloaded material includes Andrubis metadata files. No Member A baseline report was visible in the NDSS checkout at the time of this run. | Dataset/baseline completion is not independently evidenced here. |
| B | `preprocess_andrubis_sample.py`, `observation_window.py`, four-archive 32-capture sample, metrics CSV, saved logs, and passing synthetic sanity check. | Four-archive 32-capture pilot completed; limitations are recorded below. |
| C | No training-size result or attributable artifact was present in the checked workspace. | Work so far needs to be supplied by Member C for team evidence. |

### Current four-archive 32-capture run

The canonical seeded evaluation freshly preprocesses a bounded sample from
`pcaps_a.tar.gz`, `pcaps_f.tar.gz`, `pcaps_4.tar.gz`, and
`pcaps_5.tar.gz`, plus the supplied VirusTotal archive. To stay within local
storage limits, it selected one capture from each of the first eight APK-hash
groups encountered in each archive, in archive order: 32 captures total.
Preprocessing produced 12,550 packets and 885 flows across 32 APK-hash labels.
Two labels had fewer than three flows (four flows total) and were excluded by
`--min-flows 3`; metrics therefore cover 30 labels and 881 flows. There were
zero PCAP capture errors.

| Evaluation split | Window | Accuracy | Weighted precision | Weighted recall | Weighted F1 | Flows |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 30s | 0.7866 | 0.7330 | 0.7866 | 0.7561 | 164 |
| Validation | 10s | 0.7866 | 0.7330 | 0.7866 | 0.7561 | 164 |
| Test | 30s | 0.7750 | 0.7844 | 0.7750 | 0.7678 | 200 |
| Test | 10s | 0.7500 | 0.7423 | 0.7500 | 0.7315 | 200 |

For this seeded run, validation accuracy was unchanged and test accuracy
decreased by 2.5 percentage points at 10s; test weighted F1 decreased from
0.7678 to 0.7315. The sample is archive-ordered, with only one capture per
selected APK. The chronological split is by flow, so flows from a single
capture can appear across splits. Do not treat this as a capture-independent
generalization estimate or a reproduction of the paper's full dataset.
Earlier unseeded runs varied, so set `PYTHONHASHSEED=0` before starting Python
and use only the matching canonical CSV and log:
`results/member_b_submission_metrics.csv` and
`results/member_b_submission_metrics.log`. See
`results/member_b_submission_run_log.md` for the command and limitations.
The current submission input is freshly generated at
`results/member_b_submission_data_flows.p`; preprocessing output is recorded
in `results/member_b_submission_preprocess.log`.

The VirusTotal archive yielded eight reports for the 32 selected APK hashes,
with one archive read error (`ReadError: unexpected end of data`). The available
annotations were exported to `results/member_b_32_captures_flows_virustotal.csv`;
they were not used as recognition labels or in the metrics.

### Earlier four-archive 16-capture pilot (superseded)

The previous all-archive run selected one capture from the first four APK-hash
groups per archive. It yielded 16 captures, 7,001 packets, and 504 flows from
16 labels; one two-flow label was excluded. Its test accuracy was 0.7909 at
30s and 0.7455 at 10s. It is retained as historical evidence, superseded by
the 32-capture result above.

### Earlier two-archive pilot (superseded)

The earlier run used only `pcaps_a.tar.gz` and `pcaps_f.tar.gz`, selecting the
first four APK-hash groups per archive. It yielded nine captures, 3,627 packets,
and 309 flows over eight labels. One two-flow label was excluded, leaving seven
labels for metrics. Accuracy was unchanged between 30s and 10s in that sample.
It is retained as historical evidence, but the four-archive run above is the
current Member B result.

| Evaluation split | Window | Accuracy | Weighted precision | Weighted recall | Weighted F1 | Flows |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 30s | 0.8448 | 0.7632 | 0.8448 | 0.7913 | 58 |
| Validation | 10s | 0.8448 | 0.7632 | 0.8448 | 0.7913 | 58 |
| Test | 30s | 0.8955 | 0.8317 | 0.8955 | 0.8559 | 67 |
| Test | 10s | 0.8955 | 0.8317 | 0.8955 | 0.8559 | 67 |

No accuracy change was observed between these windows on this small pilot.
Three of the 309 flows contained a TLS certificate serial in preprocessing.
The VirusTotal join recovered zero of the eight selected reports: scanning
stopped with `ReadError: unexpected end of data`, and a full archive check
reported `EOFError: Compressed file ended before the end-of-stream marker was
reached`. Thus VT information was not used for labels or metrics.

The `results` directory contains earlier pilot outputs and the current
`member_b_32_captures_*` pickle, metrics CSV, preprocessing log, metrics log,
VirusTotal annotations, and run log. The separate deterministic synthetic
sanity check remains the fallback trace if a later real-data snapshot is
missing or invalid.
