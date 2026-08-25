# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 2 (validation AP=0.8338).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4474 | 0.6925 | 509 | 3.6527% |
| 5% | 0.2988 | 0.8902 | 1209 | 8.6760% |
| 10% | 0.2252 | 0.9488 | 1819 | 13.0535% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.5871 / 461 | 0.8785 / 1288 | 0.9649 / 1937 | 0.5668 |
| 1 | 0.4129 / 455 | 0.8741 / 1270 | 0.9678 / 1909 | 0.4889 |
| 2 | 0.6925 / 509 | 0.8902 / 1209 | 0.9488 / 1819 | 0.5474 |
| 3 | 0.5520 / 488 | 0.8799 / 1109 | 0.9546 / 1617 | 0.5229 |
| 4 | 0.4876 / 442 | 0.8902 / 1105 | 0.9502 / 1615 | 0.5136 |
| 5 | 0.5578 / 447 | 0.8682 / 1076 | 0.9400 / 1677 | 0.5582 |
| 6 | 0.5944 / 436 | 0.8346 / 1071 | 0.9034 / 1709 | 0.5507 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 2 | 0.6925 | 3.6527% |
| 5% | 4 | 0.8902 | 7.9297% |
| 10% | 1 | 0.9678 | 13.6993% |
