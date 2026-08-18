# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.9064).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.7317 | 152 | 0.9360% |
| 5% | 0.8999 | 801 | 4.9326% |
| 10% | 0.9865 | 1777 | 10.9428% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.7317 / 152 | 0.8999 / 801 | 0.9865 / 1777 | 0.9262 |
| 1 | 0.6697 / 153 | 0.8812 / 844 | 0.9634 / 2091 | 0.8973 |
| 2 | 0.6248 / 121 | 0.8371 / 794 | 0.9170 / 1925 | 0.8836 |
| 3 | 0.5710 / 141 | 0.8460 / 879 | 0.9268 / 2269 | 0.8665 |
| 4 | 0.5785 / 141 | 0.8543 / 907 | 0.9253 / 2241 | 0.8677 |
| 5 | 0.5486 / 132 | 0.7885 / 784 | 0.8685 / 1819 | 0.8401 |
| 6 | 0.5807 / 127 | 0.8027 / 814 | 0.8759 / 1753 | 0.8549 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 0 | 0.7317 | 0.9360% |
| 5% | 0 | 0.8999 | 4.9326% |
| 10% | 0 | 0.9865 | 10.9428% |
