# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 6 (validation AP=0.9048).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4894 | 0.7064 | 246 | 1.6374% |
| 5% | 0.3519 | 0.8773 | 1083 | 7.2085% |
| 10% | 0.2507 | 0.9448 | 1801 | 11.9875% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6078 / 81 | 0.7563 / 541 | 0.9272 / 1518 | 0.8967 |
| 1 | 0.6224 / 186 | 0.8456 / 908 | 0.9636 / 1880 | 0.8958 |
| 2 | 0.6324 / 213 | 0.8526 / 930 | 0.9624 / 1959 | 0.8942 |
| 3 | 0.7029 / 361 | 0.8914 / 1286 | 0.9765 / 1901 | 0.8957 |
| 4 | 0.6260 / 245 | 0.8432 / 1010 | 0.9648 / 1882 | 0.8803 |
| 5 | 0.6365 / 228 | 0.8233 / 787 | 0.9448 / 1673 | 0.8903 |
| 6 | 0.7064 / 246 | 0.8773 / 1083 | 0.9448 / 1801 | 0.9060 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.7064 | 1.6374% |
| 5% | 3 | 0.8914 | 8.5596% |
| 10% | 3 | 0.9765 | 12.6531% |
