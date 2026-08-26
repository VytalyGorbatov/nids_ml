# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 6 (validation AP=0.9218).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4177 | 0.6530 | 144 | 0.9585% |
| 5% | 0.2233 | 0.9607 | 1131 | 7.5280% |
| 10% | 0.1606 | 0.9918 | 1909 | 12.7063% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6465 / 396 | 0.7622 / 1227 | 0.8614 / 2120 | 0.8400 |
| 1 | 0.6248 / 7 | 0.8309 / 964 | 0.9683 / 1893 | 0.9136 |
| 2 | 0.6124 / 28 | 0.9002 / 1098 | 0.9871 / 2012 | 0.9308 |
| 3 | 0.5931 / 37 | 0.9530 / 1156 | 0.9947 / 1994 | 0.9384 |
| 4 | 0.6048 / 63 | 0.9601 / 1155 | 0.9959 / 1989 | 0.9390 |
| 5 | 0.6224 / 99 | 0.9624 / 1144 | 0.9953 / 1912 | 0.9362 |
| 6 | 0.6530 / 144 | 0.9607 / 1131 | 0.9918 / 1909 | 0.9354 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.6530 | 0.9585% |
| 5% | 5 | 0.9624 | 7.6145% |
| 10% | 4 | 0.9959 | 13.2388% |
