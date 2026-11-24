r"""
Same as prep_andrubis.py, but builds the flows file with the NDSS branch's
own preprocessor (FlowPrint\flowprint\), so experiments\recognition\recognition.py
can load it. (A flows file made with the pip package can't be opened by the
NDSS code, and vice versa.)

Usage (from the FlowPrint folder):
    python prep_andrubis_ndss.py experiments\data\Andrubis results\flows_ndss.p --max-apps 62
Then:
    cd experiments\recognition
    python recognition.py -l ..\..\results\flows_ndss.p -b 300 -w 30 -c 0.1 -s 0.9 -k 1

Note: keep 'andrubis' OUT of the output path, otherwise recognition.py looks
for vt.p / appdict.p, which this download doesn't include.
"""
import argparse
import os
import pickle
import random
import sys

# Use the NDSS code in FlowPrint\flowprint\ (same way recognition.py does)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'flowprint'))
from preprocessor import Preprocessor  # noqa: E402  (NDSS version)

CAPTURE_EXT = ('.dump', '.pcap', '.pcapng', '.cap')


def load_appdict(root):
    path = os.path.join(root, 'appdict.p')
    if not os.path.exists(path):
        return {}
    with open(path, 'rb') as f:
        d = pickle.load(f)
    out = {}
    for k, v in d.items():
        if isinstance(v, (list, tuple)) and v:
            v = v[0]
            if isinstance(v, (list, tuple)) and v:
                v = v[0]
        out[str(k)] = str(v)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('out')
    ap.add_argument('--max-apps', type=int, default=50)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    if 'andrubis' in args.out.lower():
        sys.exit("Pick an output path without 'andrubis' in it, e.g. results\\flows_ndss.p")

    appdict = load_appdict(args.root)

    # Group captures by TOP-LEVEL folder (root/<app hash>/<run hash>/allowed_traffic.dump)
    by_folder = {}
    root = os.path.abspath(args.root)
    for dirpath, _, files in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        if rel == '.':
            continue
        folder = rel.split(os.sep)[0]
        for name in files:
            if name.lower().endswith(CAPTURE_EXT):
                by_folder.setdefault(folder, []).append(os.path.join(dirpath, name))
    if not by_folder:
        sys.exit("No capture files found under " + args.root)

    # Same app selection as prep_andrubis.py (same seed -> same apps)
    folders = sorted(by_folder)
    random.Random(args.seed).shuffle(folders)
    folders = sorted(folders[:args.max_apps])

    files, labels = [], []
    for folder in folders:
        for f in sorted(by_folder[folder]):
            files.append(f)
            labels.append(appdict.get(folder, folder))

    print(f"[*] {len(by_folder)} app folders found, using {len(folders)} "
          f"({len(files)} capture files, {len(set(labels))} distinct labels)")

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    pre = Preprocessor(verbose=True)
    X, y = pre.process(files, labels)
    pre.save(args.out, X, y)
    print(f"[*] saved {len(X)} flows to {args.out} (NDSS format)")


if __name__ == '__main__':
    main()
