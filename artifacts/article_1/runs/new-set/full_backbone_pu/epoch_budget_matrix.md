# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.8699).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4900 | 0.5966 | 100 | 0.6656% |
| 5% | 0.2529 | 0.8632 | 919 | 6.1169% |
| 10% | 0.1411 | 0.9724 | 2371 | 15.7814% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.5966 / 100 | 0.8632 / 919 | 0.9724 / 2371 | 0.9058 |
| 1 | 0.7187 / 792 | 0.8450 / 1462 | 0.9102 / 2267 | 0.8391 |
| 2 | 0.8103 / 971 | 0.8796 / 1527 | 0.9190 / 2091 | 0.8200 |
| 3 | 0.7029 / 891 | 0.8004 / 1328 | 0.8497 / 1942 | 0.7963 |
| 4 | 0.5238 / 802 | 0.6383 / 1502 | 0.7146 / 2441 | 0.6603 |
| 5 | 0.7134 / 903 | 0.8103 / 1418 | 0.8538 / 1871 | 0.8137 |
| 6 | 0.6671 / 619 | 0.8086 / 1448 | 0.8614 / 2073 | 0.8281 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 2 | 0.8103 | 6.4630% |
| 5% | 2 | 0.8796 | 10.1637% |
| 10% | 0 | 0.9724 | 15.7814% |
