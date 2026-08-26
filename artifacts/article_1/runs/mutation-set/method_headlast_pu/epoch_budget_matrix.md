# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 2 (validation AP=0.8655).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4286 | 0.7086 | 662 | 4.7506% |
| 5% | 0.3034 | 0.8697 | 1225 | 8.7908% |
| 10% | 0.2193 | 0.9561 | 1813 | 13.0104% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6618 / 408 | 0.8770 / 1200 | 0.9517 / 1894 | 0.7950 |
| 1 | 0.6662 / 554 | 0.8799 / 1188 | 0.9590 / 1822 | 0.6056 |
| 2 | 0.7086 / 662 | 0.8697 / 1225 | 0.9561 / 1813 | 0.6161 |
| 3 | 0.6633 / 581 | 0.8638 / 1362 | 0.9502 / 2000 | 0.6256 |
| 4 | 0.5534 / 482 | 0.8199 / 1225 | 0.9092 / 1929 | 0.6034 |
| 5 | 0.6501 / 462 | 0.8023 / 1198 | 0.8931 / 2129 | 0.7772 |
| 6 | 0.6428 / 480 | 0.8038 / 1090 | 0.8843 / 1985 | 0.6783 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 2 | 0.7086 | 4.7506% |
| 5% | 1 | 0.8799 | 8.5253% |
| 10% | 1 | 0.9590 | 13.0750% |
