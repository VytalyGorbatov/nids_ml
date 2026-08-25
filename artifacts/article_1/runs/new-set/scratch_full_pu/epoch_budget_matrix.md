# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 1 (validation AP=0.9507).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.3998 | 0.8033 | 390 | 2.5958% |
| 5% | 0.2707 | 0.9360 | 887 | 5.9039% |
| 10% | 0.1549 | 0.9753 | 1811 | 12.0540% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6430 / 72 | 0.9378 / 1556 | 0.9736 / 2393 | 0.9161 |
| 1 | 0.8033 / 390 | 0.9360 / 887 | 0.9753 / 1811 | 0.9426 |
| 2 | 0.7722 / 262 | 0.9366 / 896 | 0.9794 / 1755 | 0.9383 |
| 3 | 0.8291 / 452 | 0.9219 / 867 | 0.9677 / 1802 | 0.9366 |
| 4 | 0.8591 / 398 | 0.9378 / 809 | 0.9654 / 1529 | 0.9398 |
| 5 | 0.7311 / 338 | 0.8967 / 1008 | 0.9472 / 1571 | 0.9131 |
| 6 | 0.7957 / 396 | 0.9172 / 853 | 0.9618 / 1608 | 0.9008 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 4 | 0.8591 | 2.6491% |
| 5% | 4 | 0.9378 | 5.3847% |
| 10% | 2 | 0.9794 | 11.6813% |
