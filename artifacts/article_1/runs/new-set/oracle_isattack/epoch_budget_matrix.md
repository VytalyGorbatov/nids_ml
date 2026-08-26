# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 7 (validation AP=0.9993).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0438 | 0.9413 | 438 | 2.9153% |
| 5% | 0.0004 | 0.9894 | 1053 | 7.0088% |
| 10% | 0.0000 | 0.9959 | 1746 | 11.6214% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.8291 / 441 | 0.9137 / 687 | 0.9724 / 1319 | 0.9264 |
| 1 | 0.9107 / 571 | 0.9278 / 688 | 0.9683 / 1189 | 0.9299 |
| 2 | 0.9143 / 530 | 0.9395 / 719 | 0.9794 / 1209 | 0.9409 |
| 3 | 0.9178 / 436 | 0.9642 / 836 | 0.9912 / 1370 | 0.9475 |
| 4 | 0.9196 / 446 | 0.9730 / 894 | 0.9965 / 1501 | 0.9545 |
| 5 | 0.9319 / 472 | 0.9830 / 954 | 0.9971 / 1572 | 0.9596 |
| 6 | 0.9401 / 457 | 0.9871 / 970 | 0.9971 / 1630 | 0.9620 |
| 7 | 0.9413 / 438 | 0.9894 / 1053 | 0.9959 / 1746 | 0.9655 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 7 | 0.9413 | 2.9153% |
| 5% | 7 | 0.9894 | 7.0088% |
| 10% | 5 | 0.9971 | 10.4633% |
