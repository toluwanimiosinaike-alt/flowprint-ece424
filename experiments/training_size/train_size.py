import argparse
import csv
import os
import sys
import numpy as np

from sklearn.model_selection import train_test_split

# Set up imports from this repository
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(ROOT, "flowprint"))
sys.path.insert(0, os.path.join(ROOT, "experiments", "recognition"))

from recognition import Recogniser
from loader import Loader


def main():
    parser = argparse.ArgumentParser(
        description="FlowPrint training-set-size experiment"
    )

    parser.add_argument("--data", default="experiments/data/processed.p")
    parser.add_argument(
        "--output",
        default="experiments/training_size/training_size_results.csv"
    )
    parser.add_argument("--seed", type=int, default=0)

    args = parser.parse_args()

    # Load data using the same Loader as Tolu's baseline
    loader = Loader()
    X, y = loader.load_files([args.data])

    X = np.asarray(X, dtype=object)
    y = np.asarray(y)

    print("Total flows:", len(X))
    print("Applications:", len(np.unique(y)))

    # Create one fixed train/test split
    indices = np.arange(len(X))

    train_idx, test_idx = train_test_split(
        indices,
        test_size=0.33,
        random_state=args.seed,
        stratify=y
    )

    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    print("Training flows:", len(X_train))
    print("Testing flows:", len(X_test))

    fractions = [1.0, 0.75, 0.50, 0.25]
    recogniser = Recogniser()
    results = []

    for fraction in fractions:
        print("\nRunning training fraction:", fraction)

        if fraction == 1.0:
            selected_idx = np.arange(len(X_train))
        else:
            selected_idx, _ = train_test_split(
                np.arange(len(X_train)),
                train_size=fraction,
                random_state=args.seed,
                stratify=y_train
            )

        X_subset = X_train[selected_idx]
        y_subset = y_train[selected_idx]

        print("Training flows used:", len(X_subset))

        metrics, _ = recogniser.evaluate(
            X_subset,
            y_subset,
            X_test,
            y_test,
            batch=300,
            window=30,
            correlation=0.1,
            similarity=0.9,
            verbose=True
        )

        row = {
            "training_fraction": fraction,
            "training_flows": len(X_subset),
            "testing_flows": len(X_test),
            "accuracy": metrics["accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1_score": metrics["f1-score"]
        }

        results.append(row)
        print("Results:", row)

    with open(args.output, "w", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("\nExperiment complete!")
    print("Results saved to:", args.output)


if __name__ == "__main__":
    main()
