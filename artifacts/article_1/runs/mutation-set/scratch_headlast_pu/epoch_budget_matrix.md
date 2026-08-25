# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 6 (validation AP=0.8255).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4201 | 0.6486 | 366 | 2.6265% |
| 5% | 0.3134 | 0.8990 | 1158 | 8.3100% |
| 10% | 0.2376 | 0.9751 | 2197 | 15.7661% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.3968 / 514 | 0.7789 / 1505 | 0.9546 / 2477 | 0.6307 |
| 1 | 0.4539 / 362 | 0.8389 / 1387 | 0.9795 / 2655 | 0.6928 |
| 2 | 0.4553 / 363 | 0.9048 / 1237 | 0.9839 / 2591 | 0.7106 |
| 3 | 0.5578 / 407 | 0.9165 / 1242 | 0.9839 / 2540 | 0.7263 |
| 4 | 0.6091 / 395 | 0.9283 / 1206 | 0.9810 / 2552 | 0.7491 |
| 5 | 0.5622 / 355 | 0.9004 / 1147 | 0.9766 / 2320 | 0.7697 |
| 6 | 0.6486 / 366 | 0.8990 / 1158 | 0.9751 / 2197 | 0.7791 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.6486 | 2.6265% |
| 5% | 4 | 0.9283 | 8.6545% |
| 10% | 3 | 0.9839 | 18.2275% |
