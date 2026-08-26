# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 4 (validation AP=0.9029).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0039 | 0.7275 | 677 | 4.5061% |
| 5% | 0.0009 | 0.8784 | 1504 | 10.0106% |
| 10% | 0.0003 | 0.9366 | 2147 | 14.2905% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.5849 / 10 | 0.7223 / 441 | 0.8861 / 1645 | 0.8784 |
| 1 | 0.5479 / 89 | 0.7493 / 590 | 0.9583 / 1994 | 0.8852 |
| 2 | 0.6600 / 314 | 0.8420 / 1113 | 0.9548 / 1993 | 0.8860 |
| 3 | 0.7017 / 671 | 0.8802 / 1471 | 0.9612 / 2052 | 0.8449 |
| 4 | 0.7275 / 677 | 0.8784 / 1504 | 0.9366 / 2147 | 0.8631 |
| 5 | 0.6406 / 661 | 0.8315 / 1462 | 0.9055 / 2190 | 0.8259 |
| 6 | 0.5073 / 483 | 0.7305 / 1267 | 0.8567 / 2093 | 0.7946 |
| 7 | 0.1715 / 6 | 0.4463 / 713 | 0.5866 / 2270 | 0.5626 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 4 | 0.7275 | 4.5061% |
| 5% | 3 | 0.8802 | 9.7910% |
| 10% | 3 | 0.9612 | 13.6581% |
