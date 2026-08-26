# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 6 (validation AP=0.9243).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4423 | 0.7493 | 334 | 2.2231% |
| 5% | 0.3191 | 0.8990 | 1211 | 8.0604% |
| 10% | 0.2174 | 0.9589 | 1824 | 12.1406% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.5972 / 81 | 0.7481 / 507 | 0.9301 / 1533 | 0.8931 |
| 1 | 0.6806 / 215 | 0.8567 / 932 | 0.9595 / 1752 | 0.9046 |
| 2 | 0.7193 / 385 | 0.8896 / 1203 | 0.9753 / 1978 | 0.8944 |
| 3 | 0.7258 / 425 | 0.9014 / 1289 | 0.9789 / 1882 | 0.8879 |
| 4 | 0.7293 / 367 | 0.8925 / 1250 | 0.9712 / 1906 | 0.8990 |
| 5 | 0.6594 / 284 | 0.8233 / 910 | 0.9501 / 1745 | 0.8828 |
| 6 | 0.7493 / 334 | 0.8990 / 1211 | 0.9589 / 1824 | 0.9156 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.7493 | 2.2231% |
| 5% | 3 | 0.9014 | 8.5796% |
| 10% | 3 | 0.9789 | 12.5266% |
