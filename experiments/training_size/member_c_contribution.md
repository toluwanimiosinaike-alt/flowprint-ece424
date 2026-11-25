# Jordan Furtado — Training-Set-Size Contribution

## Responsibility

I evaluated how the amount of labeled training traffic affects FlowPrint's
mobile-application recognition performance and analyzed the resulting metrics.

## Research question

How does FlowPrint's recognition performance change when an observer has less
labeled training traffic available?

## Dataset

The experiment used the team's preprocessed Andrubis dataset.

- 1,386 flows were retained after filtering.
- 56 applications were represented.
- Applications with fewer than five flows were excluded before splitting.

## Method

The dataset was divided once using a stratified split:

- 60% training: 831 flows
- 20% validation: 277 flows
- 20% held-out test: 278 flows

The experiment compared four training-set sizes: 100%, 75%, 50%, and 25%.
The corresponding training subsets contained 831, 623, 416, and 208 flows.
All 56 applications remained represented in each subset.

The subsets were nested: each smaller training set was selected from the
larger training-set ordering. The same validation and held-out test examples
were used for every training fraction.

FlowPrint's settings were held constant:

- Batch: 300
- Window: 30
- Correlation threshold: 0.1
- Similarity threshold: 0.9

The random seed was 0. No parameter tuning was performed for this experiment.

## Metrics and results

I report accuracy, weighted precision, weighted recall, and weighted F1-score.
The held-out test results are used for the final performance comparison.

| Training data | Training flows | Test accuracy | Test weighted precision | Test weighted recall | Test weighted F1 |
|---|---:|---:|---:|---:|---:|
| 100% | 831 | 63.67% | 61.30% | 63.67% | 61.29% |
| 75% | 623 | 51.80% | 51.15% | 51.80% | 49.81% |
| 50% | 416 | 51.08% | 48.47% | 51.08% | 48.06% |
| 25% | 208 | 29.50% | 24.02% | 29.50% | 23.07% |

Validation results were also recorded in `training_size_results.csv`. They
were used as development checks; the held-out test results above are the
basis for the final comparison.

## Analysis

The highest held-out test accuracy and weighted F1-score occurred with the
full training set: 63.67% accuracy and 61.29% weighted F1.

Performance was lower with the 75% and 50% training subsets. Those two results
were relatively close to each other (51.80% and 51.08% test accuracy), so the
results do not show a perfectly even decline at every step.

The largest drop occurred at 25% training data, where test accuracy fell to
29.50% and weighted F1 fell to 23.07%. In this experiment, substantially
reducing the available training data—especially to one quarter—was associated
with worse app-recognition performance.

## Limitations

- The results apply to this selected 56-application Andrubis subset, not to
  every mobile application or every FlowPrint deployment.
- The split is flow-level, not capture-independent. Flows from the same
  capture may appear in different splits, so the test set is not a fully
  independent capture-level evaluation.
- The experiment uses one fixed split and one random seed. Repeated runs with
  multiple seeds would help measure variability.
- The 75% and 50% test results are close; small differences between them should
  not be overinterpreted.

## Evidence files

- `train_size.py`: implementation of the training-set-size experiment
- `training_size_results.csv`: validation and held-out test metrics
- This document: individual contribution, method, results, and limitations

A separate execution log was not generated for this run. The CSV and source
code are included as the experiment's result and implementation artifacts.
