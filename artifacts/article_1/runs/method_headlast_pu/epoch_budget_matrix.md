# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 6 (validation AP=0.4168).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.0138 | 0 | 0.0000% |
| 5% | 0.2541 | 246 | 1.5854% |
| 10% | 0.3720 | 614 | 3.9570% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.0007 / 102 | 0.0237 / 545 | 0.1244 / 1300 | 0.1320 |
| 1 | 0.0000 / 44 | 0.0434 / 407 | 0.1435 / 1049 | 0.1524 |
| 2 | 0.0000 / 8 | 0.0553 / 274 | 0.1468 / 891 | 0.1752 |
| 3 | 0.0013 / 0 | 0.0764 / 206 | 0.1501 / 737 | 0.2228 |
| 4 | 0.0053 / 0 | 0.1113 / 171 | 0.1988 / 607 | 0.2968 |
| 5 | 0.0086 / 0 | 0.1850 / 196 | 0.2897 / 504 | 0.3976 |
| 6 | 0.0138 / 0 | 0.2541 / 246 | 0.3720 / 614 | 0.4822 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.0138 | 0.0000% |
| 5% | 6 | 0.2541 | 1.5854% |
| 10% | 6 | 0.3720 | 3.9570% |
