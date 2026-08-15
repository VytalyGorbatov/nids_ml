# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 6 (validation AP=0.6263).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.1856 | 0 | 0.0000% |
| 5% | 0.3647 | 108 | 0.6960% |
| 10% | 0.6294 | 1010 | 6.5090% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.0388 / 0 | 0.0415 / 8 | 0.0441 / 469 | 0.1641 |
| 1 | 0.0316 / 0 | 0.0402 / 39 | 0.0448 / 951 | 0.1651 |
| 2 | 0.0421 / 73 | 0.1764 / 461 | 0.3463 / 1150 | 0.3419 |
| 3 | 0.0118 / 8 | 0.1876 / 220 | 0.3614 / 1017 | 0.4106 |
| 4 | 0.2172 / 0 | 0.3232 / 175 | 0.4483 / 726 | 0.5845 |
| 5 | 0.2153 / 0 | 0.4009 / 32 | 0.4490 / 215 | 0.6706 |
| 6 | 0.1856 / 0 | 0.3647 / 108 | 0.6294 / 1010 | 0.7176 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 4 | 0.2172 | 0.0000% |
| 5% | 5 | 0.4009 | 0.2062% |
| 10% | 6 | 0.6294 | 6.5090% |
