# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 7 (validation AP=0.9983).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0139 | 0.9985 | 590 | 4.2339% |
| 5% | 0.0006 | 1.0000 | 1588 | 11.3958% |
| 10% | 0.0001 | 1.0000 | 2711 | 19.4546% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.8477 / 739 | 0.9824 / 1210 | 0.9956 / 1902 | 0.8898 |
| 1 | 0.9546 / 757 | 0.9912 / 1283 | 1.0000 / 2015 | 0.9073 |
| 2 | 0.9795 / 696 | 1.0000 / 1327 | 1.0000 / 2085 | 0.9361 |
| 3 | 0.9985 / 685 | 1.0000 / 1419 | 1.0000 / 2165 | 0.9552 |
| 4 | 0.9985 / 620 | 1.0000 / 1433 | 1.0000 / 2297 | 0.9714 |
| 5 | 0.9985 / 614 | 1.0000 / 1470 | 1.0000 / 2480 | 0.9716 |
| 6 | 1.0000 / 589 | 1.0000 / 1627 | 1.0000 / 2720 | 0.9810 |
| 7 | 0.9985 / 590 | 1.0000 / 1588 | 1.0000 / 2711 | 0.9777 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 1.0000 | 4.2268% |
| 5% | 2 | 1.0000 | 9.5228% |
| 10% | 1 | 1.0000 | 14.4600% |
