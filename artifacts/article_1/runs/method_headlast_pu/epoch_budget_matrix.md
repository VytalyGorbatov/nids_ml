# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 4 (validation AP=0.8792).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.5613 | 28 | 0.1724% |
| 5% | 0.8827 | 628 | 3.8672% |
| 10% | 0.9753 | 1842 | 11.3431% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6906 / 200 | 0.9178 / 858 | 0.9970 / 1734 | 0.9029 |
| 1 | 0.6196 / 81 | 0.9058 / 695 | 0.9978 / 1895 | 0.9289 |
| 2 | 0.5135 / 40 | 0.8789 / 670 | 0.9933 / 1924 | 0.9197 |
| 3 | 0.5478 / 21 | 0.8939 / 656 | 0.9858 / 1864 | 0.9364 |
| 4 | 0.5613 / 28 | 0.8827 / 628 | 0.9753 / 1842 | 0.9322 |
| 5 | 0.5022 / 32 | 0.8595 / 616 | 0.9619 / 1822 | 0.9163 |
| 6 | 0.5082 / 39 | 0.8311 / 571 | 0.9469 / 1821 | 0.9085 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 0 | 0.6906 | 1.2316% |
| 5% | 0 | 0.9178 | 5.2836% |
| 10% | 1 | 0.9978 | 11.6694% |
