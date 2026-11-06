# Member B four-archive 32-capture run

## Source comparison and scope of changes

Compared against `FlowPrint-NDSS-original\FlowPrint-NDSS`:

- The original `experiments\recognition\recognition.py` and the working copy
  have identical SHA-256 contents. The underlying `Recogniser.evaluate`
  implementation was not edited.
- Added `experiments\recognition\observation_window.py` to make fixed
  chronological per-label splits, call `Recogniser.evaluate` on held-out
  validation/test flows for both windows, and save the four metric rows. It
  avoids the unchanged `Recogniser.run` early return that evaluates the same
  data as both train and test.
- Added `experiments\recognition\preprocess_andrubis_sample.py` to produce
  FlowPrint flows from bounded Andrubis archive samples, with TShark parsing,
  a Scapy fallback, hash labels, VT joins, and explicit parse/count logging.
  For this run it was extended to accept `--pcaps-extra` and to cap captures
  per selected APK group.
- Removed the unused `tcluster.distances` import from
  `experiments\recognition\jaccard.py`. No executable Jaccard matching logic
  changed.
- Added the protocol and these outputs as experiment documentation/evidence.
  The FlowPrint clustering, fingerprinting, and recognition implementation
  were otherwise left untouched.

## Input data and sampling

The run used `pcaps_a.tar.gz`, `pcaps_f.tar.gz`, `pcaps_4.tar.gz`, and
`pcaps_5.tar.gz`, plus `virustotal.tar.gz`, from the supplied data folder.
Selection was deterministic archive order: one capture from each of the first
eight APK-hash groups in each PCAP archive (eight captures per archive, 32
total). This is a bounded sample, not the full contents of the archives.

## Preprocessing command

From the NDSS repository root:

```powershell
python experiments\recognition\preprocess_andrubis_sample.py `
  --pcaps-a C:\path\to\pcaps_a.tar.gz `
  --pcaps-f C:\path\to\pcaps_f.tar.gz `
  --pcaps-extra C:\path\to\pcaps_4.tar.gz C:\path\to\pcaps_5.tar.gz `
  --virustotal C:\path\to\virustotal.tar.gz `
  --output experiments\recognition\results\member_b_32_captures_flows.p `
  --max-apps-per-archive 8 `
  --max-captures-per-app 1
```

Observed result:

```text
TShark captures=32, packets=12550, TCP/UDP flows=885, capture_errors=0
Preprocessed 885 flows from 32 APK hashes
pcaps_a: apps_seen=8, pcaps_extracted=8, pcap_errors=0
pcaps_f: apps_seen=8, pcaps_extracted=8, pcap_errors=0
pcaps_4.tar: apps_seen=8, pcaps_extracted=8, pcap_errors=0
pcaps_5.tar: apps_seen=8, pcaps_extracted=8, pcap_errors=0
```

Two labels had fewer than three flows (four flows total), so the evaluation's
`--min-flows 3` filter retained 30 labels and 881 flows.

VirusTotal returned eight matching reports for the selected 32 hashes, then
reported `ReadError: unexpected end of data`. The recovered annotations were
saved to `member_b_32_captures_flows_virustotal.csv`; they were not used for
recognition labels or metrics.

## FlowPrint comparison

```powershell
python experiments\recognition\observation_window.py `
  --load experiments\recognition\results\member_b_32_captures_flows.p `
  --output experiments\recognition\results\member_b_32_captures_observation_window.csv
```

Parameters held constant: `batch=300`, `correlation=0.1`, and `similarity=0.9`.
The same chronological per-label 60/20/20 split was used for both windows.

```text
validation window=30.0s accuracy=0.7866 f1=0.7561 support=164
validation window=10.0s accuracy=0.7805 f1=0.7237 support=164
test window=30.0s accuracy=0.7750 f1=0.7678 support=200
test window=10.0s accuracy=0.7500 f1=0.6984 support=200
```

The 10s window measured lower accuracy in both splits. This remains a pilot
result: the archive-order sample uses one capture per APK, and the flow-level
split can put flows from one capture into separate partitions.

## Sanity check and artifacts

`python experiments\recognition\observation_window.py --self-test` passed:
14 synthetic flows were placed into disjoint chronological splits, and the
30s/10s ordering was verified. This is a harness check, not an accuracy test.

Artifacts:

- `member_b_32_captures_flows.p`: preprocessed flows and APK-hash labels.
- `member_b_32_captures_observation_window.csv`: four metrics rows.
- `member_b_32_captures_preprocess.log`: preprocessing and VirusTotal output.
- `member_b_32_captures_metrics.log`: comparison output.
- `member_b_32_captures_flows_virustotal.csv`: eight recovered reports.
