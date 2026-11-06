# Training-Set-Size Experiment

## Research Question
How does the amount of training data affect FlowPrint's application recognition performance?

## Experimental Design
The experiment evaluates four training-set sizes:
- 100% of the training data
- 75% of the training data
- 50% of the training data
- 25% of the training data

A single 67% training / 33% testing split is created using random seed 0. The test set remains fixed across all four configurations. Only the training data size changes.

## FlowPrint Parameters
- Batch: 300 seconds
- Window: 30 seconds
- Correlation threshold: 0.1
- Similarity threshold: 0.9

## Evaluation Metrics
- Accuracy
- Weighted precision
- Weighted recall
- Weighted F1-score

## Preliminary Dataset
The current sanity-check dataset contains 1,490 flows:
- Spotify: 429 flows
- YouTube: 1,061 flows

## Preliminary Results
All four training fractions currently produce 100% accuracy, precision, recall, and F1-score.

These results demonstrate that the experiment pipeline runs successfully. They should not be interpreted as evidence of generalizable performance because the dataset is small and contains traffic from only two applications.

## Files
- `train_size.py`: experiment implementation
- `training_size_results.csv`: numerical results
- `training_size_run.log`: execution log

## Next Steps
Repeat the experiment using a larger research dataset and analyze how recognition performance changes as training data decreases.
