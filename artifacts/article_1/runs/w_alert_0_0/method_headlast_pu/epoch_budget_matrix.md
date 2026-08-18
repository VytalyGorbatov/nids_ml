# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.8595).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.6921 | 226 | 1.3917% |
| 5% | 0.9185 | 859 | 5.2897% |
| 10% | 0.9970 | 1714 | 10.5548% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6921 / 226 | 0.9185 / 859 | 0.9970 / 1714 | 0.8980 |
| 1 | 0.6413 / 101 | 0.9051 / 735 | 0.9955 / 1845 | 0.9248 |
| 2 | 0.5463 / 71 | 0.8610 / 672 | 0.9910 / 1866 | 0.9106 |
| 3 | 0.5374 / 69 | 0.8543 / 663 | 0.9888 / 1869 | 0.9091 |
| 4 | 0.5725 / 43 | 0.9088 / 688 | 0.9963 / 1916 | 0.9327 |
| 5 | 0.5546 / 38 | 0.8909 / 633 | 0.9955 / 1893 | 0.9307 |
| 6 | 0.5157 / 35 | 0.8685 / 615 | 0.9918 / 1874 | 0.9222 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 0 | 0.6921 | 1.3917% |
| 5% | 0 | 0.9185 | 5.2897% |
| 10% | 0 | 0.9970 | 10.5548% |
