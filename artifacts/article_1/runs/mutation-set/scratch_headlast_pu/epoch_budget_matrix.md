# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 1 (validation AP=0.8941).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.3166 | 0.7365 | 824 | 5.9132% |
| 5% | 0.1827 | 0.8682 | 1745 | 12.5224% |
| 10% | 0.1326 | 0.9385 | 2816 | 20.2081% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6955 / 839 | 0.8389 / 1858 | 0.8814 / 2988 | 0.6361 |
| 1 | 0.7365 / 824 | 0.8682 / 1745 | 0.9385 / 2816 | 0.5710 |
| 2 | 0.6911 / 715 | 0.8990 / 1763 | 0.9458 / 2512 | 0.6441 |
| 3 | 0.6237 / 547 | 0.9122 / 1673 | 0.9575 / 2408 | 0.6415 |
| 4 | 0.5417 / 455 | 0.9092 / 1579 | 0.9575 / 2357 | 0.6467 |
| 5 | 0.4700 / 437 | 0.8814 / 1415 | 0.9444 / 2335 | 0.6395 |
| 6 | 0.4597 / 448 | 0.8755 / 1406 | 0.9488 / 2342 | 0.6166 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 1 | 0.7365 | 5.9132% |
| 5% | 3 | 0.9122 | 12.0057% |
| 10% | 4 | 0.9575 | 16.9142% |
