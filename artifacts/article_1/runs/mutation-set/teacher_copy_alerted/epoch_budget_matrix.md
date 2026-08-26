# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.7776).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0574 | 0.5373 | 123 | 0.8827% |
| 5% | 0.0250 | 0.7818 | 934 | 6.7025% |
| 10% | 0.0111 | 0.9078 | 2627 | 18.8518% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.5373 / 123 | 0.7818 / 934 | 0.9078 / 2627 | 0.7763 |
| 1 | 0.5944 / 467 | 0.7775 / 1179 | 0.9209 / 2970 | 0.6374 |
| 2 | 0.3294 / 288 | 0.6061 / 1504 | 0.8551 / 2228 | 0.5821 |
| 3 | 0.2958 / 361 | 0.5652 / 1551 | 0.7775 / 2277 | 0.5025 |
| 4 | 0.3250 / 651 | 0.5300 / 1601 | 0.6925 / 2463 | 0.4174 |
| 5 | 0.2840 / 784 | 0.4905 / 1597 | 0.6691 / 2515 | 0.3260 |
| 6 | 0.2387 / 915 | 0.4597 / 1598 | 0.6559 / 2579 | 0.3001 |
| 7 | 0.2240 / 431 | 0.6296 / 1038 | 0.7599 / 2747 | 0.4053 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 1 | 0.5944 | 3.3513% |
| 5% | 0 | 0.7818 | 6.7025% |
| 10% | 1 | 0.9209 | 21.3132% |
