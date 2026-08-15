# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 7 (validation AP=0.9445).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.9144 | 1 | 0.0064% |
| 5% | 0.9645 | 488 | 3.1449% |
| 10% | 0.9908 | 1432 | 9.2286% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.5695 / 33 | 0.7156 / 526 | 0.8315 / 1511 | 0.8120 |
| 1 | 0.6590 / 0 | 0.7722 / 425 | 0.9394 / 1678 | 0.8866 |
| 2 | 0.6919 / 1 | 0.7808 / 462 | 0.9164 / 1482 | 0.8952 |
| 3 | 0.7340 / 0 | 0.8051 / 254 | 0.9724 / 1691 | 0.9282 |
| 4 | 0.7584 / 1 | 0.8302 / 360 | 0.9605 / 1450 | 0.9354 |
| 5 | 0.8025 / 1 | 0.8841 / 397 | 0.9770 / 1425 | 0.9575 |
| 6 | 0.8637 / 5 | 0.9342 / 572 | 0.9849 / 1439 | 0.9720 |
| 7 | 0.9144 / 1 | 0.9645 / 488 | 0.9908 / 1432 | 0.9848 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 7 | 0.9144 | 0.0064% |
| 5% | 7 | 0.9645 | 3.1449% |
| 10% | 7 | 0.9908 | 9.2286% |
