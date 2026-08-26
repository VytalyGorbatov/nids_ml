# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 5 (validation AP=0.8909).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0030 | 0.7704 | 449 | 2.9886% |
| 5% | 0.0006 | 0.9219 | 1256 | 8.3600% |
| 10% | 0.0002 | 0.9536 | 1859 | 12.3735% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6119 / 95 | 0.7381 / 500 | 0.8732 / 1681 | 0.8647 |
| 1 | 0.6224 / 159 | 0.7874 / 508 | 0.8937 / 1109 | 0.8941 |
| 2 | 0.6207 / 134 | 0.8238 / 583 | 0.9360 / 1622 | 0.9068 |
| 3 | 0.6494 / 252 | 0.8297 / 654 | 0.9436 / 1624 | 0.8953 |
| 4 | 0.7005 / 317 | 0.8732 / 917 | 0.9436 / 1672 | 0.9039 |
| 5 | 0.7704 / 449 | 0.9219 / 1256 | 0.9536 / 1859 | 0.9086 |
| 6 | 0.7821 / 537 | 0.9213 / 1239 | 0.9448 / 1816 | 0.8968 |
| 7 | 0.1715 / 6 | 0.4463 / 713 | 0.5866 / 2270 | 0.5626 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.7821 | 3.5743% |
| 5% | 5 | 0.9219 | 8.3600% |
| 10% | 5 | 0.9536 | 12.3735% |
