import argparse
import csv
import math
import os
import sys
from collections import defaultdict


BASELINE_WINDOW = 30.0
REDUCED_WINDOW = 10.0


def temporal_split_indices(labels, timestamps, train_fraction=0.6,
                           validation_fraction=0.2):
    """Split each label's flows chronologically into train, validation, test."""
    if len(labels) != len(timestamps):
        raise ValueError("Labels and timestamps must have the same length.")
    if train_fraction <= 0 or validation_fraction <= 0 or \
            train_fraction + validation_fraction >= 1:
        raise ValueError("Fractions must be positive and leave a test split.")

    grouped = defaultdict(list)
    for index, (label, timestamp) in enumerate(zip(labels, timestamps)):
        timestamp = float(timestamp)
        if not math.isfinite(timestamp):
            raise ValueError("Flow timestamps must be finite.")
        grouped[label].append((timestamp, index))

    train, validation, test = [], [], []
    for label, flows in grouped.items():
        if len(flows) < 3:
            raise ValueError(
                "Label {!r} has {} flows; at least 3 are required for "
                "train/validation/test.".format(label, len(flows)))

        flows.sort(key=lambda flow: (flow[0], flow[1]))
        train_end = max(1, int(len(flows) * train_fraction))
        validation_count = max(1, int(len(flows) * validation_fraction))
        validation_end = train_end + validation_count
        if validation_end >= len(flows):
            validation_end = len(flows) - 1
            train_end = validation_end - 1

        train.extend(index for _, index in flows[:train_end])
        validation.extend(index for _, index in flows[train_end:validation_end])
        test.extend(index for _, index in flows[validation_end:])

    return train, validation, test


def run_self_test():
    labels = ["app-a"] * 6 + ["app-b"] * 5 + ["app-c"] * 3
    timestamps = list(range(6)) + list(range(10, 15)) + list(range(20, 23))
    train, validation, test = temporal_split_indices(labels, timestamps)

    splits = (set(train), set(validation), set(test))
    assert not (splits[0] & splits[1] or splits[0] & splits[2] or
                splits[1] & splits[2])
    assert set.union(*splits) == set(range(len(labels)))
    for label in set(labels):
        ordered = [
            [timestamps[index] for index in split if labels[index] == label]
            for split in (train, validation, test)
        ]
        assert ordered[0] and ordered[1] and ordered[2]
        assert max(ordered[0]) <= min(ordered[1])
        assert max(ordered[1]) <= min(ordered[2])

    assert BASELINE_WINDOW == 30.0
    assert REDUCED_WINDOW == 10.0
    assert REDUCED_WINDOW < BASELINE_WINDOW
    print("SANITY CHECK: observation-window protocol")
    print("PASS: 14 synthetic flows across 3 labels are fully assigned to "
          "disjoint, chronological train/validation/test splits.")
    print("PASS: fixed baseline window is 30s and reduced window is 10s.")


def run_experiment(args):
    import numpy as np

    experiment_dir = os.path.abspath(os.path.dirname(__file__))
    root = os.path.abspath(os.path.join(experiment_dir, "..", ".."))
    sys.path.insert(0, experiment_dir)
    sys.path.insert(0, os.path.join(root, "flowprint"))
    from loader import Loader

    X, y = Loader().load_files(args.load, args.min_flows)
    y = np.asarray(y)
    timestamps = [flow.time_start() for flow in X]
    train_idx, validation_idx, test_idx = temporal_split_indices(
        y, timestamps, args.train_fraction, args.validation_fraction)

    from recognition import Recogniser

    splits = {
        "validation": (X[train_idx], y[train_idx],
                       X[validation_idx], y[validation_idx]),
        "test": (X[train_idx], y[train_idx], X[test_idx], y[test_idx]),
    }
    recogniser = Recogniser()
    rows = []
    for split_name, (X_train, y_train, X_eval, y_eval) in splits.items():
        for window in (args.baseline_window, args.reduced_window):
            metrics, _ = recogniser.evaluate(
                X_train, y_train, X_eval, y_eval,
                batch=args.batch,
                window=window,
                correlation=args.correlation,
                similarity=args.similarity,
                verbose=False)
            row = {
                "split": split_name,
                "window_seconds": window,
                "batch_seconds": args.batch,
                "correlation": args.correlation,
                "similarity": args.similarity,
                "train_flows": len(X_train),
                "evaluation_flows": len(X_eval),
                "accuracy": metrics["accuracy"],
                "precision_weighted": metrics["precision"],
                "recall_weighted": metrics["recall"],
                "f1_weighted": metrics["f1-score"],
            }
            rows.append(row)
            print("{} window={}s accuracy={:.4f} f1={:.4f} support={}".format(
                split_name, window, row["accuracy"], row["f1_weighted"],
                row["evaluation_flows"]))

    output_parent = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(output_parent, exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print("Results written to {}".format(os.path.abspath(args.output)))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compare FlowPrint's original and reduced activity windows.")
    parser.add_argument("--load", nargs="+",
                        help="Preprocessed FlowPrint pickle file(s), each "
                             "containing (flows, labels).")
    parser.add_argument("--output", default="results/member_b_window.csv",
                        help="CSV results path.")
    parser.add_argument("--min-flows", type=int, default=3,
                        help="Minimum flows per label (default: 3).")
    parser.add_argument("--batch", type=float, default=300,
                        help="FlowPrint batch size in seconds (default: 300).")
    parser.add_argument("--baseline-window", type=float,
                        default=BASELINE_WINDOW,
                        help="Baseline activity window in seconds (default: 30).")
    parser.add_argument("--reduced-window", type=float,
                        default=REDUCED_WINDOW,
                        help="Reduced activity window in seconds (default: 10).")
    parser.add_argument("--correlation", type=float, default=0.1,
                        help="Cross-correlation threshold (default: 0.1).")
    parser.add_argument("--similarity", type=float, default=0.9,
                        help="Fingerprint similarity threshold (default: 0.9).")
    parser.add_argument("--train-fraction", type=float, default=0.6,
                        help="Per-label chronological training fraction.")
    parser.add_argument("--validation-fraction", type=float, default=0.2,
                        help="Per-label chronological validation fraction.")
    parser.add_argument("--self-test", action="store_true",
                        help="Run dependency-free split/window sanity checks.")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        return 0
    if not args.load:
        parser.error("--load is required unless --self-test is selected.")
    if args.baseline_window <= 0 or args.reduced_window <= 0:
        parser.error("Window sizes must be positive.")
    if args.reduced_window >= args.baseline_window:
        parser.error("--reduced-window must be smaller than --baseline-window.")
    if args.min_flows < 3:
        parser.error("--min-flows must be at least 3 for three-way evaluation.")
    run_experiment(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
