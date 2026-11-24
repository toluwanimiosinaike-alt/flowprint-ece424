# Member B dataset and rerun status

## Andrubis manifest run: blocked by missing trace inputs

`results/used_captures.tsv` contains 62 rows and 62 unique app labels. Its
capture paths are absolute paths rooted at
`C:\Users\Lenovo\PycharmProjects\FlowPrint\experiments\data\Andrubis`.
None of the referenced paths exists in the attached project environment, and
there are no `.dump`, `.pcap`, `.pcapng`, or `.cap` files in this project.
The exact manifest SHA-256 is
`33e304affcb8fe752070fc11143460adf84bb07e25fe84a39c6dea4892d52c53`.

The existing `member_b_*_flows.p` pickles are from an earlier 32-capture
sample and are not the 62-app manifest input.

## Available Member A pickle: pilot completed

The project also includes `experiments/data/processed.p`, which the project
README identifies as a separate two-app laptop trace dataset. It loaded as
1,490 NDSS FlowPrint flows: `spotify` (429) and `youtube` (1,061).

Member B's 30-second versus 10-second activity-window comparison was run on
this input. The synthetic split self-test passed, and a seeded repeat
reproduced the metrics CSV byte-for-byte. The pilot metrics and presentation
caveats are documented in
`member_b_observation_window_processed_p_report.md`.

This pilot is **not** a result on the 62-app Andrubis manifest and must not be
presented as such. Its flow-level chronological split can put flows from the
same capture/session in train, validation, and test.

The existing root `results/metrics.csv` is also not a substitute for the
Andrubis manifest comparison. The `obs_120s`, `obs_60s`, and `obs_30s` runs in
`run_experiments.py` vary batch duration while holding the activity window at
30 seconds; they do not measure the 30s-versus-10s activity window.

To run the requested Andrubis experiment, provide the authorized capture
files referenced by `used_captures.tsv`, or a FlowPrint NDSS-format
`(flows, labels)` pickle prepared from exactly those rows.
