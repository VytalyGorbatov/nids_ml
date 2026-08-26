# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 7 (validation AP=0.9980).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0072 | 0.9971 | 841 | 6.0352% |
| 5% | 0.0001 | 1.0000 | 1772 | 12.7162% |
| 10% | 0.0000 | 1.0000 | 2619 | 18.7944% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.8477 / 791 | 0.9810 / 1146 | 0.9985 / 2950 | 0.8866 |
| 1 | 0.8624 / 758 | 0.9839 / 1130 | 1.0000 / 2257 | 0.8910 |
| 2 | 0.9136 / 779 | 0.9985 / 1230 | 1.0000 / 2513 | 0.9084 |
| 3 | 0.9546 / 764 | 0.9985 / 1319 | 1.0000 / 2498 | 0.9166 |
| 4 | 0.9766 / 767 | 1.0000 / 1643 | 1.0000 / 2844 | 0.9325 |
| 5 | 0.9898 / 775 | 1.0000 / 1698 | 1.0000 / 2751 | 0.9425 |
| 6 | 0.9898 / 812 | 1.0000 / 1771 | 1.0000 / 2720 | 0.9522 |
| 7 | 0.9971 / 841 | 1.0000 / 1772 | 1.0000 / 2619 | 0.9586 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 7 | 0.9971 | 6.0352% |
| 5% | 4 | 1.0000 | 11.7905% |
| 10% | 1 | 1.0000 | 16.1966% |
