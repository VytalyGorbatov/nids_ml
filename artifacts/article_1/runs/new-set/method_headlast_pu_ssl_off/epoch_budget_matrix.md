# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 3 (validation AP=0.8782).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4508 | 0.7123 | 317 | 2.1100% |
| 5% | 0.2928 | 0.8409 | 641 | 4.2665% |
| 10% | 0.1290 | 0.9565 | 1511 | 10.0572% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6400 / 175 | 0.7839 / 493 | 0.8990 / 1081 | 0.8983 |
| 1 | 0.5338 / 223 | 0.7452 / 533 | 0.9166 / 1199 | 0.8522 |
| 2 | 0.6635 / 285 | 0.8015 / 561 | 0.9436 / 1515 | 0.8963 |
| 3 | 0.7123 / 317 | 0.8409 / 641 | 0.9565 / 1511 | 0.9084 |
| 4 | 0.6882 / 287 | 0.8203 / 645 | 0.9659 / 1577 | 0.9039 |
| 5 | 0.7287 / 386 | 0.8667 / 865 | 0.9624 / 1519 | 0.8971 |
| 6 | 0.7410 / 401 | 0.8937 / 992 | 0.9624 / 1512 | 0.9028 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.7410 | 2.6691% |
| 5% | 6 | 0.8937 | 6.6028% |
| 10% | 4 | 0.9659 | 10.4965% |
