# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 6 (validation AP=0.6727).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.0908 | 0 | 0.0000% |
| 5% | 0.3713 | 275 | 1.7722% |
| 10% | 0.6471 | 1093 | 7.0439% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.0000 / 84 | 0.0652 / 481 | 0.1810 / 1402 | 0.1730 |
| 1 | 0.0000 / 17 | 0.2047 / 416 | 0.3377 / 1032 | 0.3045 |
| 2 | 0.0000 / 1 | 0.2772 / 293 | 0.4042 / 883 | 0.4222 |
| 3 | 0.0007 / 0 | 0.2745 / 238 | 0.4312 / 808 | 0.5416 |
| 4 | 0.0059 / 0 | 0.3239 / 235 | 0.4694 / 775 | 0.6346 |
| 5 | 0.0263 / 0 | 0.3581 / 286 | 0.6142 / 1016 | 0.6885 |
| 6 | 0.0908 / 0 | 0.3713 / 275 | 0.6471 / 1093 | 0.7103 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.0908 | 0.0000% |
| 5% | 6 | 0.3713 | 1.7722% |
| 10% | 6 | 0.6471 | 7.0439% |
