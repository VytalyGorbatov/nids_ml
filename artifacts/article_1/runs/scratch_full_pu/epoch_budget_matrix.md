# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 1 (validation AP=0.7819).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.2369 | 133 | 0.8190% |
| 5% | 0.7070 | 921 | 5.6715% |
| 10% | 0.9096 | 1569 | 9.6619% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.2145 / 48 | 0.8199 / 912 | 0.9836 / 2171 | 0.7963 |
| 1 | 0.2369 / 133 | 0.7070 / 921 | 0.9096 / 1569 | 0.7849 |
| 2 | 0.3460 / 234 | 0.4701 / 425 | 0.5912 / 535 | 0.7885 |
| 3 | 0.0979 / 77 | 0.5665 / 823 | 0.7758 / 1236 | 0.7191 |
| 4 | 0.1353 / 119 | 0.5643 / 759 | 0.7646 / 1207 | 0.7248 |
| 5 | 0.1749 / 110 | 0.5643 / 727 | 0.7287 / 1044 | 0.7432 |
| 6 | 0.1375 / 78 | 0.5583 / 745 | 0.7601 / 1145 | 0.7413 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 2 | 0.3460 | 1.4410% |
| 5% | 0 | 0.8199 | 5.6161% |
| 10% | 0 | 0.9836 | 13.3690% |
