# Jordan Furtado — Training-Set-Size Contribution

## Responsibility

I am responsible for evaluating how the amount of training data affects
FlowPrint's mobile-application recognition performance and analyzing the
resulting metrics.

## Research question

How does FlowPrint's recognition performance change when the observer has
less labeled training traffic available?

## Method

The experiment compares four training-data amounts: 100%, 75%, 50%, and 25%
of the training split. The data is divided once into 60% training, 20%
validation, and 20% held-out test data. The same validation and test examples
are reused for each training fraction so that the amount of training data is
the main variable.

Applications with fewer than five flows are excluded before splitting. The
reduced training subsets retain at least one flow per application. FlowPrint's
batch, window, correlation, and similarity settings remain fixed at the
baseline values so the experiment focuses on training-set size.

## Metrics

I report accuracy, weighted precision, weighted recall, and weighted F1-score
for validation and held-out test data. The held-out test results are used for
the final comparison.

## Analysis

The results will be compared across the four training fractions to determine
whether recognition performance decreases as the amount of training data is
reduced. Any unexpected trend, such as stable performance or improvement with
less data, will be discussed rather than treated as proof that training data
does not matter.

## Limitations

The conclusions are limited to the selected Andrubis subset and the
applications that remain after minimum-flow filtering. The split is
flow-level, so it does not guarantee that captures are independent across
training, validation, and test sets. A single seeded run also does not measure
variation across different random splits.

Final numerical results will be added after the experiment is successfully
run on the larger Andrubis dataset.
