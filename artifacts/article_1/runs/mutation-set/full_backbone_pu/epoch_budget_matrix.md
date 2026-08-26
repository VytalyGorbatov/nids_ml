# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.8414).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.3342 | 0.6706 | 369 | 2.6480% |
| 5% | 0.2143 | 0.8375 | 1163 | 8.3459% |
| 10% | 0.1584 | 0.9136 | 2619 | 18.7944% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6706 / 369 | 0.8375 / 1163 | 0.9136 / 2619 | 0.8184 |
| 1 | 0.6413 / 390 | 0.7687 / 1445 | 0.8375 / 2804 | 0.7658 |
| 2 | 0.6296 / 323 | 0.7160 / 1215 | 0.7892 / 2478 | 0.7578 |
| 3 | 0.6325 / 435 | 0.7218 / 1575 | 0.7818 / 2607 | 0.7458 |
| 4 | 0.4480 / 273 | 0.5974 / 1258 | 0.6750 / 2063 | 0.6266 |
| 5 | 0.3719 / 188 | 0.6105 / 1291 | 0.7072 / 2536 | 0.6269 |
| 6 | 0.3792 / 328 | 0.5286 / 1313 | 0.6091 / 2270 | 0.5522 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 0 | 0.6706 | 2.6480% |
| 5% | 0 | 0.8375 | 8.3459% |
| 10% | 0 | 0.9136 | 18.7944% |
