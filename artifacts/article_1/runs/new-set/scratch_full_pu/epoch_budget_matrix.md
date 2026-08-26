# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.9545).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.1907 | 0.6806 | 93 | 0.6190% |
| 5% | 0.0758 | 0.9630 | 1599 | 10.6430% |
| 10% | 0.0535 | 0.9812 | 2443 | 16.2606% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6806 / 93 | 0.9630 / 1599 | 0.9812 / 2443 | 0.9373 |
| 1 | 0.7287 / 112 | 0.9671 / 1438 | 0.9836 / 2066 | 0.9526 |
| 2 | 0.8004 / 271 | 0.9383 / 1244 | 0.9677 / 1931 | 0.9407 |
| 3 | 0.7769 / 348 | 0.9207 / 1092 | 0.9654 / 1948 | 0.9317 |
| 4 | 0.7722 / 391 | 0.9137 / 1217 | 0.9454 / 1893 | 0.9204 |
| 5 | 0.6406 / 294 | 0.8150 / 1117 | 0.9366 / 2035 | 0.8878 |
| 6 | 0.6447 / 146 | 0.8426 / 1001 | 0.8943 / 1800 | 0.8930 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 2 | 0.8004 | 1.8038% |
| 5% | 1 | 0.9671 | 9.5714% |
| 10% | 1 | 0.9836 | 13.7513% |
