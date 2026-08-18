# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 6 (validation AP=0.9948).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.9178 | 0 | 0.0000% |
| 5% | 0.9985 | 401 | 2.4694% |
| 10% | 1.0000 | 1699 | 10.4625% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.7466 / 5 | 0.9559 / 612 | 0.9985 / 1756 | 0.9550 |
| 1 | 0.7242 / 0 | 0.9641 / 458 | 1.0000 / 1725 | 0.9790 |
| 2 | 0.7481 / 0 | 0.9821 / 440 | 1.0000 / 1653 | 0.9896 |
| 3 | 0.8214 / 0 | 0.9880 / 373 | 1.0000 / 1567 | 0.9948 |
| 4 | 0.8229 / 0 | 0.9978 / 570 | 1.0000 / 1557 | 0.9971 |
| 5 | 0.8722 / 0 | 0.9978 / 484 | 1.0000 / 1668 | 0.9986 |
| 6 | 0.9178 / 0 | 0.9985 / 401 | 1.0000 / 1699 | 0.9989 |
| 7 | 0.9126 / 0 | 0.9993 / 635 | 1.0000 / 1568 | 0.9990 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.9178 | 0.0000% |
| 5% | 7 | 0.9993 | 3.9103% |
| 10% | 4 | 1.0000 | 9.5880% |
