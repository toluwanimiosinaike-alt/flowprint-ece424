r"""
Score FlowPrint recognition runs from the logs written by run_experiments.py.

FlowPrint's command-line --recognition mode does not print accuracy. It prints,
for every TRUE app label, each test fingerprint and the app it was PREDICTED as:

     <true app label>
        Fingerprint(0x...) [size=   4] --> <predicted app label>

This script parses those lines and computes accuracy and weighted
precision / recall / F1 (same metric style as the paper's Table IV),
one row per run.

Usage (from the FlowPrint folder):
    python compute_metrics.py            # reads results\logs\*.log
Writes results\metrics.csv and prints a table.
"""
import csv
import glob
import os
import re
import sys

from sklearn.metrics import accuracy_score, precision_recall_fscore_support

LOG_DIR = os.path.join('results', 'logs')
OUT_CSV = os.path.join('results', 'metrics.csv')

FP_LINE = re.compile(r'^\s+Fingerprint\(.*?\)\s*\[size=\s*(\d+)\]\s*-->\s*(\S+)\s*$')
HEADER = re.compile(r'^\s?(\S+)\s*$')        # " <label>" printed by FlowPrint
PARAMS = re.compile(r'^# \S+ (.*)$')          # "# name batch=.. window=.."


def parse(path):
    y_true, y_pred, params = [], [], ''
    current = None
    in_recognition = False
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('$ ') and '--recognition' in line:
                in_recognition = True
                continue
            if line.startswith('$ '):
                in_recognition = False
                continue
            if not in_recognition:
                continue
            m = FP_LINE.match(line)
            if m:
                if current is not None:
                    y_true.append(current)
                    y_pred.append(m.group(2))
                continue
            m = HEADER.match(line)
            if m and not line.startswith('[exit') and 'Traceback' not in line:
                current = m.group(1)
    return y_true, y_pred


def main():
    logs = sorted(p for p in glob.glob(os.path.join(LOG_DIR, '*.log'))
                  if not os.path.basename(p).startswith('00_'))
    if not logs:
        sys.exit(f'No logs found in {LOG_DIR}')

    # Keep the order the experiments were run in
    order = ['baseline', 'obs_120s', 'obs_60s', 'obs_30s', 'train_25pct', 'train_10pct']
    logs.sort(key=lambda p: order.index(os.path.basename(p)[:-4])
              if os.path.basename(p)[:-4] in order else 99)

    rows = []
    for path in logs:
        name = os.path.basename(path)[:-4]
        y_true, y_pred = parse(path)
        if not y_true:
            rows.append({'run': name, 'test_fingerprints': 0, 'apps_in_test': 0,
                         'accuracy': '', 'precision': '', 'recall': '', 'f1': '',
                         'note': 'no recognition output - check log'})
            continue
        p, r, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average='weighted', zero_division=0)
        rows.append({
            'run': name,
            'test_fingerprints': len(y_true),
            'apps_in_test': len(set(y_true)),
            'accuracy': round(accuracy_score(y_true, y_pred), 4),
            'precision': round(p, 4),
            'recall': round(r, 4),
            'f1': round(f1, 4),
            'note': '',
        })

    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"{'run':<13}{'test fps':>9}{'apps':>6}{'acc':>8}{'prec':>8}{'rec':>8}{'f1':>8}")
    for r in rows:
        if r['note']:
            print(f"{r['run']:<13}  {r['note']}")
        else:
            print(f"{r['run']:<13}{r['test_fingerprints']:>9}{r['apps_in_test']:>6}"
                  f"{r['accuracy']:>8}{r['precision']:>8}{r['recall']:>8}{r['f1']:>8}")
    print(f'\nSaved to {OUT_CSV}')


if __name__ == '__main__':
    main()
