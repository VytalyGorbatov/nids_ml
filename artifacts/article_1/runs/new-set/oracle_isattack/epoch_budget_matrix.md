# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 7 (validation AP=0.9990).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0192 | 0.9477 | 403 | 2.6824% |
| 5% | 0.0003 | 0.9941 | 1048 | 6.9755% |
| 10% | 0.0001 | 0.9994 | 1935 | 12.8794% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.8450 / 420 | 0.9307 / 731 | 0.9871 / 1509 | 0.9254 |
| 1 | 0.9295 / 433 | 0.9818 / 912 | 0.9982 / 1645 | 0.9463 |
| 2 | 0.9401 / 415 | 0.9918 / 1019 | 0.9994 / 1811 | 0.9578 |
| 3 | 0.9319 / 417 | 0.9865 / 981 | 0.9971 / 1824 | 0.9609 |
| 4 | 0.9401 / 411 | 0.9947 / 1065 | 0.9994 / 1966 | 0.9677 |
| 5 | 0.9565 / 414 | 0.9982 / 1198 | 1.0000 / 2097 | 0.9680 |
| 6 | 0.9618 / 405 | 0.9977 / 1183 | 1.0000 / 2098 | 0.9713 |
| 7 | 0.9477 / 403 | 0.9941 / 1048 | 0.9994 / 1935 | 0.9724 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.9618 | 2.6957% |
| 5% | 5 | 0.9982 | 7.9739% |
| 10% | 5 | 1.0000 | 13.9577% |
