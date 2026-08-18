# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 1 (validation AP=0.9275).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.5456 | 194 | 1.1947% |
| 5% | 0.8767 | 950 | 5.8501% |
| 10% | 0.9559 | 1901 | 11.7064% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.4148 / 294 | 0.8924 / 1101 | 0.9843 / 1727 | 0.8331 |
| 1 | 0.5456 / 194 | 0.8767 / 950 | 0.9559 / 1901 | 0.8416 |
| 2 | 0.4746 / 177 | 0.7631 / 773 | 0.9036 / 1487 | 0.8274 |
| 3 | 0.4469 / 182 | 0.7339 / 842 | 0.9043 / 1640 | 0.8128 |
| 4 | 0.4544 / 167 | 0.7683 / 815 | 0.9006 / 1539 | 0.8314 |
| 5 | 0.4581 / 169 | 0.7646 / 725 | 0.8782 / 1392 | 0.8354 |
| 6 | 0.4581 / 173 | 0.7339 / 784 | 0.8827 / 1544 | 0.8178 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 1 | 0.5456 | 1.1947% |
| 5% | 0 | 0.8924 | 6.7800% |
| 10% | 0 | 0.9843 | 10.6349% |
