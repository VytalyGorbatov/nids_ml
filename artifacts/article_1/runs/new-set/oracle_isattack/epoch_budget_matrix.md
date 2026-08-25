# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 7 (validation AP=0.9997).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0327 | 0.9501 | 407 | 2.7090% |
| 5% | 0.0003 | 0.9912 | 1224 | 8.1470% |
| 10% | 0.0000 | 0.9988 | 2250 | 14.9760% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.8127 / 332 | 0.9143 / 628 | 0.9583 / 1291 | 0.9204 |
| 1 | 0.9049 / 471 | 0.9231 / 694 | 0.9413 / 1052 | 0.9261 |
| 2 | 0.9049 / 387 | 0.9378 / 861 | 0.9695 / 1680 | 0.9342 |
| 3 | 0.9102 / 397 | 0.9589 / 1054 | 0.9877 / 2110 | 0.9451 |
| 4 | 0.9166 / 408 | 0.9712 / 1035 | 0.9918 / 2101 | 0.9456 |
| 5 | 0.9237 / 410 | 0.9789 / 1138 | 0.9941 / 2213 | 0.9568 |
| 6 | 0.9342 / 402 | 0.9877 / 1215 | 0.9959 / 2225 | 0.9625 |
| 7 | 0.9501 / 407 | 0.9912 / 1224 | 0.9988 / 2250 | 0.9526 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 7 | 0.9501 | 2.7090% |
| 5% | 7 | 0.9912 | 8.1470% |
| 10% | 7 | 0.9988 | 14.9760% |
