# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 1 (validation AP=0.9696).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4157 | 0.8420 | 232 | 1.5442% |
| 5% | 0.1799 | 0.9824 | 1269 | 8.4465% |
| 10% | 0.1195 | 0.9900 | 1853 | 12.3336% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6494 / 48 | 0.9513 / 1809 | 0.9836 / 2885 | 0.9214 |
| 1 | 0.8420 / 232 | 0.9824 / 1269 | 0.9900 / 1853 | 0.9646 |
| 2 | 0.8602 / 270 | 0.9771 / 1177 | 0.9836 / 1875 | 0.9633 |
| 3 | 0.8831 / 387 | 0.9753 / 1135 | 0.9894 / 1777 | 0.9566 |
| 4 | 0.8139 / 320 | 0.9524 / 1162 | 0.9789 / 1905 | 0.9432 |
| 5 | 0.8585 / 394 | 0.9583 / 1192 | 0.9865 / 1863 | 0.9467 |
| 6 | 0.7598 / 316 | 0.9243 / 1065 | 0.9742 / 1975 | 0.9249 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 3 | 0.8831 | 2.5759% |
| 5% | 1 | 0.9824 | 8.4465% |
| 10% | 1 | 0.9900 | 12.3336% |
