# Member B frozen evidence snapshot

Frozen 2026-11-24 for the ECE 424 FlowPrint presentation.

## What this snapshot supports

This evidence supports the bounded pilot comparing FlowPrint's activity
window at 30 seconds and 10 seconds on the available Member A pickle
`experiments/data/processed.p`:

- 1,490 flows from two labels (`spotify`: 429, `youtube`: 1,061).
- Per-label chronological split: 60% train, 20% validation, 20% test.
- Fixed parameters: batch 300 s, correlation 0.1, similarity 0.9.
- Seed: `PYTHONHASHSEED=0`.

The test accuracy was 99.00% at 30 s and 90.67% at 10 s. Validation moved in
the opposite direction. Read the report's limitations before using this as a
claim: this is a two-label pilot with a flow-level split, not capture-
independent evidence.

## Files

- `Member_B_Observation_Window_Pilot.pptx` — five presentation slides,
  including the paper citation, evidence contents, and staff-access handoff.
- `member_b_observation_window_processed_p.csv` — exact metric rows.
- `member_b_observation_window_processed_p.png` — chart used on slide 3.
- `member_b_observation_window_processed_p_report.md` — protocol,
  interpretation, and limitations.
- `member_b_observation_window_processed_p_run.log` — concise test trace and
  reproducibility outcome.
- `member_b_used_captures_rerun_status.md` — status of the separate
  62-app Andrubis manifest run.
- `source/` — the Member B harness, recognition/evaluation implementation,
  and FlowPrint source files for code review.
- `SHA256SUMS.txt` — file integrity checksums.

The prepared pickle and raw captures are intentionally excluded. The pickle
contains packet-level metadata. Its SHA-256, recorded in the report, lets the
team identify the exact local input without redistributing it.

## Validation and integrity

The harness self-test passed. A second seeded run generated a byte-for-byte
identical metrics CSV. Verify extracted files against `SHA256SUMS.txt` before
use. The ZIP file has a separate `.sha256` sidecar.

This bundle can be uploaded to the course-approved submission location. Give
course staff permission to view/download it and check access from a signed-
out or separate account. A local file path or chat artifact alone is not a
permanent course-wide link.

The 62-row `used_captures.tsv` refers to Andrubis captures that are not
available in the attached folder. Therefore, this snapshot does not claim to
contain a 62-app Andrubis Member B result.
