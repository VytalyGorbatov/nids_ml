# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.8338).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0453 | 0.6252 | 290 | 2.0811% |
| 5% | 0.0202 | 0.8199 | 1270 | 9.1137% |
| 10% | 0.0101 | 0.9209 | 2381 | 17.0865% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6252 / 290 | 0.8199 / 1270 | 0.9209 / 2381 | 0.7795 |
| 1 | 0.6223 / 521 | 0.8331 / 1214 | 0.9385 / 2549 | 0.6716 |
| 2 | 0.3909 / 467 | 0.6676 / 1694 | 0.8799 / 2355 | 0.5767 |
| 3 | 0.2050 / 251 | 0.5242 / 1640 | 0.7613 / 2763 | 0.4743 |
| 4 | 0.2328 / 666 | 0.4641 / 1974 | 0.6676 / 3095 | 0.4252 |
| 5 | 0.2372 / 873 | 0.4597 / 2054 | 0.6589 / 3227 | 0.3904 |
| 6 | 0.2430 / 924 | 0.4407 / 2199 | 0.6223 / 3318 | 0.3131 |
| 7 | 0.2240 / 431 | 0.6296 / 1038 | 0.7599 / 2747 | 0.4053 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 0 | 0.6252 | 2.0811% |
| 5% | 1 | 0.8331 | 8.7119% |
| 10% | 1 | 0.9385 | 18.2921% |
