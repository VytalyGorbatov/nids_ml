# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.7868).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.3241 | 0.6633 | 472 | 3.3872% |
| 5% | 0.2220 | 0.7877 | 1106 | 7.9368% |
| 10% | 0.1733 | 0.8331 | 1853 | 13.2975% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6633 / 472 | 0.7877 / 1106 | 0.8331 / 1853 | 0.6446 |
| 1 | 0.3997 / 431 | 0.5139 / 890 | 0.5827 / 1482 | 0.4782 |
| 2 | 0.4305 / 456 | 0.5637 / 923 | 0.6398 / 1506 | 0.5395 |
| 3 | 0.3529 / 390 | 0.6559 / 902 | 0.7496 / 1423 | 0.5813 |
| 4 | 0.3265 / 366 | 0.5695 / 932 | 0.6823 / 1577 | 0.4612 |
| 5 | 0.3397 / 381 | 0.6266 / 821 | 0.7277 / 1546 | 0.5641 |
| 6 | 0.3250 / 367 | 0.5417 / 1000 | 0.6574 / 1735 | 0.4669 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 0 | 0.6633 | 3.3872% |
| 5% | 0 | 0.7877 | 7.9368% |
| 10% | 0 | 0.8331 | 13.2975% |
