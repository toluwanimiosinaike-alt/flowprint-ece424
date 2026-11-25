
import argparse
import csv
import os
import sys

import numpy as np
from sklearn.model_selection import train_test_split

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(ROOT, "flowprint"))
sys.path.insert(0, os.path.join(ROOT, "experiments", "recognition"))

from loader import Loader
from recognition import Recogniser


FRACTIONS = [1.00, 0.75, 0.50, 0.25]

FLOWPRINT_PARAMETERS = {
    "batch": 300,
    "window": 30,
    "correlation": 0.1,
    "similarity": 0.9,
}


def split_train_validation_test(X, y, seed):
    all_indices = np.arange(len(y))

    train_val_indices, test_indices = train_test_split(
        all_indices,
        test_size=0.20,
        random_state=seed,
        stratify=y,
    )

    train_indices, validation_indices = train_test_split(
        train_val_indices,
        test_size=0.25,
        random_state=seed,
        stratify=y[train_val_indices],
    )

    return (
        X[train_indices], y[train_indices],
        X[validation_indices], y[validation_indices],
        X[test_indices], y[test_indices],
    )


def choose_training_indices(y_train, fraction, seed):
    labels = np.unique(y_train)
    total = len(y_train)

    requested = int(round(total * fraction))
    target = min(total, max(requested, len(labels)))

    rng = np.random.default_rng(seed)
    shuffled_indices = rng.permutation(total)

    reserved = []
    remaining = []

    seen_labels = set()

    for index in shuffled_indices:
        label = y_train[index]

        if label not in seen_labels:
            reserved.append(index)
            seen_labels.add(label)
        else:
            remaining.append(index)

    nested_order = np.array(reserved + remaining, dtype=int)

    return nested_order[:target]


def evaluate_split(X_train, y_train, X_eval, y_eval, verbose):
    recogniser = Recogniser()

    metrics, _ = recogniser.evaluate(
        X_train,
        y_train,
        X_eval,
        y_eval,
        **FLOWPRINT_PARAMETERS,
        verbose=verbose,
    )

    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate FlowPrint with different training-set sizes."
    )

    parser.add_argument(
        "--data",
        default="results/flows_ndss.p",
        help=(
            "Path to the preprocessed Andrubis dataset. "
            "Default: results/flows_ndss.p"
        ),
    )

    parser.add_argument(
        "--output",
        default="experiments/training_size/training_size_results.csv",
    )

    parser.add_argument("--seed", type=int, default=0)

    parser.add_argument(
        "--min-flows",
        type=int,
        default=5,
        help="Discard applications with fewer than this many flows.",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress FlowPrint's per-run classification report.",
    )

    args = parser.parse_args()

    if not os.path.isfile(args.data):
        raise FileNotFoundError(
            f"Dataset not found: {args.data}\n"
            "Obtain Tolu's preprocessed Andrubis dataset and pass its path "
            "with --data. The repository's experiments/data/processed.p "
            "file is only the earlier two-application pilot dataset."
        )

    if args.min_flows < 2:
        parser.error("--min-flows must be at least 2 for stratified splitting.")

    print("Loading dataset:", args.data)
    print("Minimum flows per application:", args.min_flows)

    loader = Loader()
    X, y = loader.load_files([args.data], min_flows=args.min_flows)

    X = np.asarray(X, dtype=object)
    y = np.asarray(y)

    labels, counts = np.unique(y, return_counts=True)

    print("Flows after filtering:", len(X))
    print("Applications after filtering:", len(labels))
    print("Smallest application flow count:", int(counts.min()))

    if len(labels) < 2:
        raise ValueError("At least two applications are required.")

    (
        X_train, y_train,
        X_validation, y_validation,
        X_test, y_test,
    ) = split_train_validation_test(X, y, args.seed)

    print("\nFixed data split:")
    print("Training flows:", len(X_train))
    print("Validation flows:", len(X_validation))
    print("Held-out test flows:", len(X_test))
    print("FlowPrint parameters:", FLOWPRINT_PARAMETERS)

    rows = []

    for fraction in FRACTIONS:
        selected = choose_training_indices(
            y_train,
            fraction,
            seed=args.seed,
        )

        X_subset = X_train[selected]
        y_subset = y_train[selected]

        print("\n" + "=" * 60)
        print(f"Training fraction requested: {fraction:.0%}")
        print("Training flows actually used:", len(X_subset))
        print("Applications represented:", len(np.unique(y_subset)))

        print("\nValidation results:")

        validation_metrics = evaluate_split(
            X_subset,
            y_subset,
            X_validation,
            y_validation,
            verbose=not args.quiet,
        )

        rows.append({
            "split": "validation",
            "training_fraction": fraction,
            "training_flows": len(X_subset),
            "evaluation_flows": len(X_validation),
            "accuracy": validation_metrics["accuracy"],
            "precision": validation_metrics["precision"],
            "recall": validation_metrics["recall"],
            "f1_score": validation_metrics["f1-score"],
        })

        print("\nHeld-out test results:")

        test_metrics = evaluate_split(
            X_subset,
            y_subset,
            X_test,
            y_test,
            verbose=not args.quiet,
        )

        rows.append({
            "split": "test",
            "training_fraction": fraction,
            "training_flows": len(X_subset),
            "evaluation_flows": len(X_test),
            "accuracy": test_metrics["accuracy"],
            "precision": test_metrics["precision"],
            "recall": test_metrics["recall"],
            "f1_score": test_metrics["f1-score"],
        })

    output_directory = os.path.dirname(args.output)

    if output_directory:
        os.makedirs(output_directory, exist_ok=True)

    fieldnames = [
        "split",
        "training_fraction",
        "training_flows",
        "evaluation_flows",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
    ]

    with open(args.output, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("\nExperiment finished.")
    print("Results saved to:", args.output)
    print(
        "Reminder: use the held-out test rows for final performance claims; "
        "validation rows are for development checks."
    )


if __name__ == "__main__":
    main()
