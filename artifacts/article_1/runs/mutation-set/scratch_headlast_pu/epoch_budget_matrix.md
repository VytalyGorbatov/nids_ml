# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.8065).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4971 | 0.5549 | 951 | 6.8245% |
| 5% | 0.3071 | 0.9209 | 2119 | 15.2063% |
| 10% | 0.2230 | 0.9605 | 3153 | 22.6265% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.5549 / 951 | 0.9209 / 2119 | 0.9605 / 3153 | 0.5041 |
| 1 | 0.5198 / 521 | 0.9517 / 1922 | 0.9649 / 3684 | 0.6130 |
| 2 | 0.5271 / 400 | 0.9605 / 1949 | 0.9780 / 3389 | 0.6739 |
| 3 | 0.3133 / 336 | 0.9678 / 1691 | 0.9824 / 3081 | 0.6183 |
| 4 | 0.3163 / 353 | 0.9722 / 1635 | 0.9810 / 3063 | 0.6180 |
| 5 | 0.3397 / 412 | 0.9531 / 1448 | 0.9795 / 2907 | 0.5898 |
| 6 | 0.4173 / 469 | 0.8448 / 1348 | 0.9722 / 2538 | 0.5768 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 0 | 0.5549 | 6.8245% |
| 5% | 4 | 0.9722 | 11.7330% |
| 10% | 3 | 0.9824 | 22.1098% |
