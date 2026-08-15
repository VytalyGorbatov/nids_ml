# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 2 (validation AP=0.8210).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.2521 | 89 | 0.5736% |
| 5% | 0.7064 | 929 | 5.9870% |
| 10% | 0.8446 | 1345 | 8.6679% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.0244 / 0 | 0.2699 / 417 | 0.5820 / 1179 | 0.5609 |
| 1 | 0.1573 / 42 | 0.3305 / 550 | 0.7505 / 1304 | 0.6346 |
| 2 | 0.2521 / 89 | 0.7064 / 929 | 0.8446 / 1345 | 0.7529 |
| 3 | 0.2311 / 25 | 0.6840 / 999 | 0.8255 / 1604 | 0.7639 |
| 4 | 0.1600 / 0 | 0.6847 / 988 | 0.8282 / 1832 | 0.7811 |
| 5 | 0.1455 / 0 | 0.6537 / 1059 | 0.8124 / 2338 | 0.7514 |
| 6 | 0.3311 / 62 | 0.5899 / 1027 | 0.7367 / 2602 | 0.7252 |
| 7 | 0.0000 / 0 | 0.4536 / 1001 | 0.5267 / 1472 | 0.4897 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.3311 | 0.3996% |
| 5% | 2 | 0.7064 | 5.9870% |
| 10% | 2 | 0.8446 | 8.6679% |
