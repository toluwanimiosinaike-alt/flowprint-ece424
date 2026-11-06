# Local Andrubis input data

Put your authorized Andrubis PCAP archives and VirusTotal archive in this
folder. The preprocessing script looks here by default, so you do not need to
copy the archives into the repository root or pass their paths individually.

Expected files:

- One or more PCAP archives named `pcaps*.tar.gz` (for example
  `pcaps_a.tar.gz`, `pcaps_f.tar.gz`, `pcaps_4.tar.gz`, and `pcaps_5.tar.gz`).
- `virustotal.tar.gz`.

The PCAP archives are streamed and only the configured bounded sample is
extracted to temporary storage. For the 32-capture sample (up to eight APK
groups per archive and one capture per APK), run from the NDSS repository root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-member-b.txt
```

Install Wireshark/TShark separately and make `tshark` available on `PATH`.
If it is installed elsewhere, pass its executable path using `--tshark`.

The preprocessor discovers all `pcaps*.tar.gz` files in this folder and
`virustotal.tar.gz` automatically. Follow the complete fresh-run procedure
below to write a new, submission-specific input pickle and evaluate it.

## Fresh Member B submission run

The following process starts from the PCAP archives in this folder, creates a
new 32-capture FlowPrint input, and evaluates that new input. The output names
are specific to this submission run:

- `experiments\recognition\results\member_b_submission_data_flows.p` — freshly preprocessed `(flows, labels)` input.
- `experiments\recognition\results\member_b_submission_data_flows_virustotal.csv` — recovered VirusTotal annotations, not used in recognition metrics.
- `experiments\recognition\results\member_b_submission_preprocess.log` — preprocessing output and archive warnings.
- `experiments\recognition\results\member_b_submission_metrics.csv`
- `experiments\recognition\results\member_b_submission_metrics.log`
- `experiments\recognition\results\member_b_submission_run_log.md`

From the repository root in PowerShell, preprocess the archives first. The
script discovers the four `pcaps*.tar.gz` files and the VirusTotal archive in
this folder automatically. It selects up to eight APK groups from each PCAP
archive and one capture per APK:

```powershell
python experiments\recognition\preprocess_andrubis_sample.py `
  --max-apps-per-archive 8 `
  --max-captures-per-app 1 `
  --output experiments\recognition\results\member_b_submission_data_flows.p
```

Then evaluate the newly created pickle. Set the hash seed before Python starts
to reproduce the canonical metrics:

```powershell
$env:PYTHONHASHSEED = "0"
python experiments\recognition\observation_window.py `
  --load experiments\recognition\results\member_b_submission_data_flows.p `
  --output experiments\recognition\results\member_b_submission_metrics.csv
Remove-Item Env:\PYTHONHASHSEED
```

The fresh preprocessing run recorded 12,550 packets, 885 TCP/UDP flows,
32 APK-hash labels, and zero PCAP capture errors. The evaluator excludes
labels with fewer than three flows, leaving metrics across 30 labels and 881
flows. At 10 seconds, validation accuracy was unchanged (78.66%) and test
accuracy was 2.5 percentage points lower (75.00% versus 77.50% at 30 seconds).
See the run log for detailed metrics, sampling limitations, and the
VirusTotal archive warning.

The self-test is a lightweight fallback check if the real-data pickle is
missing or invalid; it does not produce recognition-performance results:

```powershell
python experiments\recognition\observation_window.py --self-test
```

It should report `PASS` for split coverage/disjointness/order and the 30s/10s
window settings.

The preprocessing script overwrites its output pickle and matching
VirusTotal-annotation CSV when those output paths already exist. The supplied
archives are large, but the script streams them and extracts only the bounded
sample to temporary storage.

To use a different input folder, including
`C:\Users\alext\FlowPrint-NDSS\FlowPrint-NDSS\experiments\recognition\result\user_data`,
pass its path to `--user-data-dir`:

```powershell
python experiments\recognition\preprocess_andrubis_sample.py `
  --user-data-dir "C:\Users\alext\FlowPrint-NDSS\FlowPrint-NDSS\experiments\recognition\result\user_data" `
  --max-apps-per-archive 8 `
  --max-captures-per-app 1
```

To use specific archives instead of automatic discovery, pass `--pcaps-a`,
`--pcaps-f`, and/or `--pcaps-extra`; `--virustotal` can override the default
VirusTotal path. The default input folder is resolved relative to the script,
not tied to a particular Windows account or checkout location.

Keep the large or access-restricted archives out of version control. The
repository ignores files in this folder except this README.
