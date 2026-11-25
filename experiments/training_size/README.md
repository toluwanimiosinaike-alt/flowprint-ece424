# Training-Set-Size Experiment

## Research question

How does the amount of labeled training traffic available to an observer affect
FlowPrint's ability to recognize mobile applications from encrypted traffic
metadata?

## Experiment

The experiment compares four amounts of training data:

- 100% of the available training split
- 75% of the available training split
- 50% of the available training split
- 25% of the available training split

The dataset is split once into 60% training, 20% validation, and 20% held-out
testing data. The same validation and test examples are used for every training
fraction. Only the amount of training data changes.

The split uses stratification so each application is represented across the
three splits. Applications with fewer than five flows are excluded by default
before splitting. Within each reduced training subset, the script keeps at
least one flow per application. If 25% would be too small to represent every
application, the script uses the smallest size that still represents all
applications and reports the actual number of training flows.

## FlowPrint parameters

The parameters are held constant to isolate the effect of training-set size:

- Batch: 300 seconds
- Window: 30 seconds
- Correlation threshold: 0.1
- Similarity threshold: 0.9

No parameter tuning is performed in this experiment. Validation results are
reported as development checks; the held-out test set is reserved for final
performance reporting.

## Evaluation metrics

- Accuracy
- Weighted precision
- Weighted recall
- Weighted F1-score

## Dataset

The intended dataset is Tolu's preprocessed Andrubis dataset. The script's
default path is `results/flows_ndss.p`. That file was not present in the
repository ZIP reviewed for this update, so it must be obtained from Tolu or
generated using the team's preprocessing procedure before the larger-dataset
experiment can run.

The repository also contains `experiments/data/processed.p`, the earlier
1,490-flow, two-application Spotify/YouTube pilot. It can be used to check that
the script starts and runs, but it is not a substitute for the larger Andrubis
dataset and should not be used to claim the larger-dataset experiment is done.

## Running the experiment

Run these commands from the repository's top-level folder.

PowerShell:

```powershell
python experiments/training_size/train_size.py --data results/flows_ndss.p 2>&1 | Tee-Object -FilePath experiments/training_size/training_size_run.log
```

If Tolu provides the file under a different path, replace `results/flows_ndss.p`
with the actual path.

To run the old two-application pilot only:

```powershell
python experiments/training_size/train_size.py --data experiments/data/processed.p 2>&1 | Tee-Object -FilePath experiments/training_size/training_size_pilot.log
```

The pilot output must be labeled as preliminary and limited to two applications.

## Output

The script writes:

- `training_size_results.csv`: validation and held-out test metrics for all
  four training fractions
- `training_size_run.log`: console output when run with the PowerShell command
  above

The CSV contains one validation row and one test row for each training
fraction. Use the test rows for final performance comparisons.

## Limitations

- The result applies to the selected Andrubis subset, not all mobile apps.
- Removing applications with fewer than five flows limits the set of
  applications evaluated.
- The split is flow-level, not capture/device-independent. Flows from the same
  capture may appear in more than one split, so the results should not be
  described as a fully independent real-world test.
- A single random seed is used for this run. Repeated seeds would provide a
  stronger estimate of variability.
- The 25% subset may be increased slightly when necessary to keep at least one
  training flow for every application. The actual training-flow count is
  recorded in the CSV.

## Files

- `train_size.py`: training-size experiment implementation
- `training_size_results.csv`: generated numerical results
- `training_size_run.log`: generated execution log
