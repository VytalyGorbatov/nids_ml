# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 1 (validation AP=0.8115).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.3533 | 0.6618 | 859 | 6.1643% |
| 5% | 0.2525 | 0.8492 | 1735 | 12.4507% |
| 10% | 0.1993 | 0.9385 | 2564 | 18.3997% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6559 / 1173 | 0.8302 / 2420 | 0.8726 / 3258 | 0.4937 |
| 1 | 0.6618 / 859 | 0.8492 / 1735 | 0.9385 / 2564 | 0.6236 |
| 2 | 0.4773 / 418 | 0.8126 / 1193 | 0.9136 / 2379 | 0.6653 |
| 3 | 0.4817 / 370 | 0.8360 / 1050 | 0.9678 / 2254 | 0.6828 |
| 4 | 0.5168 / 340 | 0.8375 / 1041 | 0.9488 / 1880 | 0.7151 |
| 5 | 0.4671 / 293 | 0.7613 / 1078 | 0.8843 / 1803 | 0.7408 |
| 6 | 0.6018 / 316 | 0.8697 / 1052 | 0.9429 / 1860 | 0.7958 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 1 | 0.6618 | 6.1643% |
| 5% | 6 | 0.8697 | 7.5493% |
| 10% | 3 | 0.9678 | 16.1751% |
