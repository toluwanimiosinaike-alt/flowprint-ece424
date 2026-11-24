r"""
Turn Andrubis captures into a labelled FlowPrint flows file.

Andrubis stores one folder per analysed app, each with the same file name
(allowed_traffic.dump). FlowPrint needs a label per capture, so we label each
file by its parent folder, and map that to an app name via appdict.p if present.

Usage (from the repo root):
    python prep_andrubis.py experiments\data\Andrubis results\flows.p [--max-apps 50]

(run_experiments.py calls this for you if results\flows.p doesn't exist yet)
"""
import argparse
import os
import pickle
import random
import sys

from flowprint.preprocessor import Preprocessor

CAPTURE_EXT = ('.dump', '.pcap', '.pcapng', '.cap')


def load_appdict(root):
    """Optional mapping folder/hash -> app name (format as used in the NDSS code)."""
    path = os.path.join(root, 'appdict.p')
    if not os.path.exists(path):
        return {}
    with open(path, 'rb') as f:
        d = pickle.load(f)
    out = {}
    for k, v in d.items():
        # NDSS code reads the name as v[0]; accept plain strings too
        if isinstance(v, (list, tuple)) and v:
            v = v[0]
            if isinstance(v, (list, tuple)) and v:
                v = v[0]
        out[str(k)] = str(v)
    print(f"[*] appdict.p loaded: {len(out)} entries")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', help='folder holding the Andrubis app folders')
    ap.add_argument('out', help='output flows file, e.g. results/flows.p')
    ap.add_argument('--max-apps', type=int, default=50,
                    help='use at most this many app folders (default 50, keeps it laptop-sized)')
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    appdict = load_appdict(args.root)

    # Collect captures, grouped by TOP-LEVEL folder under root
    # (Andrubis nests them: root/<app hash>/<run hash>/allowed_traffic.dump)
    by_folder = {}
    root = os.path.abspath(args.root)
    for dirpath, _, files in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        if rel == '.':
            continue  # skip files sitting directly in root (e.g. processed.p)
        folder = rel.split(os.sep)[0]
        for name in files:
            if name.lower().endswith(CAPTURE_EXT):
                by_folder.setdefault(folder, []).append(os.path.join(dirpath, name))
    if not by_folder:
        sys.exit("No capture files found under " + args.root)

    folders = sorted(by_folder)
    random.Random(args.seed).shuffle(folders)
    folders = sorted(folders[:args.max_apps])

    files, labels = [], []
    for folder in folders:
        label = appdict.get(folder, folder)
        for f in sorted(by_folder[folder]):
            files.append(f)
            labels.append(label)

    print(f"[*] {len(by_folder)} app folders found, using {len(folders)} "
          f"({len(files)} capture files, {len(set(labels))} distinct labels)")

    # Record exactly which captures were used - this goes in the evidence snapshot
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(os.path.join(os.path.dirname(args.out) or '.', 'used_captures.tsv'), 'w') as f:
        f.write("label\tfile\n")
        for lab, fn in zip(labels, files):
            f.write(f"{lab}\t{fn}\n")

    pre = Preprocessor(verbose=True)
    X, y = pre.process(files, labels)
    pre.save(args.out, X, y)
    print(f"[*] saved {len(X)} flows to {args.out}")
    if len(X) == 0:
        print("[!] 0 flows - check that tshark is installed and the dumps contain TCP/UDP traffic")


if __name__ == '__main__':
    main()
