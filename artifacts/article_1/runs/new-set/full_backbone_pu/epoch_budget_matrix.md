# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 2 (validation AP=0.8768).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4065 | 0.8068 | 593 | 3.9470% |
| 5% | 0.2475 | 0.9278 | 1117 | 7.4348% |
| 10% | 0.1678 | 0.9683 | 1854 | 12.3403% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.7093 / 218 | 0.8855 / 893 | 0.9759 / 1790 | 0.9203 |
| 1 | 0.7939 / 535 | 0.8826 / 838 | 0.9507 / 1728 | 0.9059 |
| 2 | 0.8068 / 593 | 0.9278 / 1117 | 0.9683 / 1854 | 0.9113 |
| 3 | 0.8092 / 612 | 0.8861 / 974 | 0.9419 / 1874 | 0.8881 |
| 4 | 0.7340 / 593 | 0.8550 / 1078 | 0.9266 / 1981 | 0.8585 |
| 5 | 0.7622 / 865 | 0.8344 / 1991 | 0.8796 / 3013 | 0.8286 |
| 6 | 0.8027 / 828 | 0.8644 / 1851 | 0.9014 / 2750 | 0.8550 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 3 | 0.8092 | 4.0735% |
| 5% | 2 | 0.9278 | 7.4348% |
| 10% | 0 | 0.9759 | 11.9143% |
