"""
N05 FlowPrint stress test - Windows/Mac/Linux runner.

Runs: baseline, shorter observation windows, smaller training sets.
Writes everything to results/ : one log per run + summary.txt.

Usage (from the FlowPrint folder):
    python run_experiments.py experiments\\data\\Andrubis

Needs: pip install flowprint, and tshark (comes with Wireshark) on PATH.
"""
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone

PY = sys.executable            # same python you launched this with
OUT = 'results'
LOGS = os.path.join(OUT, 'logs')
FPS = os.path.join(OUT, 'fingerprints')
FLOWS = os.path.join(OUT, 'flows.p')
SUMMARY = os.path.join(OUT, 'summary.txt')

# (name, batch seconds, window seconds, test fraction)
RUNS = [
    ('baseline',     300, 30, 0.5),   # Exp 1 (Tolu): paper defaults
    ('obs_120s',     120, 30, 0.5),   # Exp 2 (Alex): shorter observation
    ('obs_60s',       60, 30, 0.5),
    ('obs_30s',       30, 30, 0.5),
    ('train_25pct',  300, 30, 0.75),  # Exp 3 (Jordan): smaller training set
    ('train_10pct',  300, 30, 0.9),
]



def sh(cmd, log):
    """Run a command, append its output to log, return exit code."""
    with open(log, 'a', encoding='utf-8') as f:
        f.write('$ ' + ' '.join(cmd) + '\n')
        f.flush()
        p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
        f.write(f'[exit code {p.returncode}]\n\n')
    return p.returncode


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python run_experiments.py <andrubis folder>')
    data_dir = sys.argv[1]
    max_apps = sys.argv[2] if len(sys.argv) > 2 else '50'

    os.makedirs(LOGS, exist_ok=True)
    os.makedirs(FPS, exist_ok=True)

    if shutil.which('tshark') is None:
        print('[!] tshark not found on PATH - install Wireshark and add '
              'C:\\Program Files\\Wireshark to PATH (needed for the .dump files)')

    with open(SUMMARY, 'w', encoding='utf-8') as s:
        s.write(f'N05 FlowPrint runs - {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}\n')
        s.write(f'python {platform.python_version()} on {platform.system()}\n')
        s.write(f'data: {data_dir}\n\n')

    # Step 0: dumps -> labelled flows (once)
    if not os.path.exists(FLOWS):
        print('[*] Extracting flows from captures (slow part)...')
        here = os.path.dirname(os.path.abspath(__file__))
        code = sh([PY, os.path.join(here, 'prep_andrubis.py'), data_dir, FLOWS,
                   '--max-apps', max_apps], os.path.join(LOGS, '00_prep.log'))
        if code != 0 or not os.path.exists(FLOWS):
            sys.exit(f'[!] Preprocessing failed - see {LOGS}\\00_prep.log')
    else:
        print(f'[*] Reusing existing {FLOWS}')

    for name, b, w, split in RUNS:
        print(f'[*] {name}: batch={b}s window={w}s test_fraction={split}')
        log = os.path.join(LOGS, f'{name}.log')
        open(log, 'w').close()
        fp = os.path.join(FPS, f'{name}.json')
        c1 = sh([PY, '-m', 'flowprint', '--read', FLOWS, '--fingerprint', fp,
                 '-b', str(b), '-w', str(w), '-l', str(split), '-a', '42'], log)
        c2 = sh([PY, '-m', 'flowprint',
                 '--train', fp.replace('.json', '.train.json'),
                 '--test',  fp.replace('.json', '.test.json'),
                 '--recognition'], log)

        with open(SUMMARY, 'a', encoding='utf-8') as s:
            s.write(f'{name}: batch={b} window={w} test_fraction={split} '
                    f'-> {"FAILED" if (c1 or c2) else "ok"} ({log})\n')
        if c1 or c2:
            print(f'    [!] a step failed - see {log}')

    # FlowPrint's CLI prints predictions, not scores - compute them here
    here = os.path.dirname(os.path.abspath(__file__))
    print('[*] Scoring runs...')
    subprocess.run([PY, os.path.join(here, 'compute_metrics.py')])
    print(f'[*] Done. Scores in {OUT}\\metrics.csv, run list in {SUMMARY}')


if __name__ == '__main__':
    main()
