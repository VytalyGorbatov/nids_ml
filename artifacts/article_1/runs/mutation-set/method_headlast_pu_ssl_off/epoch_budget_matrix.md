# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 2 (validation AP=0.8752).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4121 | 0.7394 | 664 | 4.7650% |
| 5% | 0.2990 | 0.8682 | 1191 | 8.5468% |
| 10% | 0.2124 | 0.9590 | 1758 | 12.6157% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6589 / 351 | 0.8755 / 1130 | 0.9546 / 2078 | 0.8260 |
| 1 | 0.6398 / 547 | 0.8580 / 1207 | 0.9517 / 1856 | 0.5684 |
| 2 | 0.7394 / 664 | 0.8682 / 1191 | 0.9590 / 1758 | 0.6521 |
| 3 | 0.6750 / 627 | 0.8755 / 1293 | 0.9634 / 1940 | 0.5640 |
| 4 | 0.4934 / 514 | 0.8551 / 1197 | 0.9341 / 1858 | 0.5821 |
| 5 | 0.5549 / 435 | 0.8199 / 1245 | 0.9122 / 2146 | 0.7234 |
| 6 | 0.5666 / 464 | 0.8009 / 1161 | 0.8887 / 1956 | 0.6722 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 2 | 0.7394 | 4.7650% |
| 5% | 0 | 0.8755 | 8.1091% |
| 10% | 3 | 0.9634 | 13.9218% |
