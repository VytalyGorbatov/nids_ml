# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 2 (validation AP=0.9107).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.5091 | 0.6254 | 97 | 0.6456% |
| 5% | 0.2558 | 0.9178 | 1176 | 7.8275% |
| 10% | 0.1771 | 0.9695 | 1845 | 12.2804% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6577 / 348 | 0.7833 / 1832 | 0.8784 / 2791 | 0.8420 |
| 1 | 0.6518 / 208 | 0.8602 / 1352 | 0.9419 / 2234 | 0.8857 |
| 2 | 0.6254 / 97 | 0.9178 / 1176 | 0.9695 / 1845 | 0.9147 |
| 3 | 0.5942 / 76 | 0.9378 / 1188 | 0.9789 / 1839 | 0.9231 |
| 4 | 0.5261 / 62 | 0.9336 / 1157 | 0.9824 / 1766 | 0.9151 |
| 5 | 0.5443 / 63 | 0.9266 / 1124 | 0.9806 / 1752 | 0.9203 |
| 6 | 0.5414 / 75 | 0.9172 / 1099 | 0.9759 / 1720 | 0.9148 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 0 | 0.6577 | 2.3163% |
| 5% | 3 | 0.9378 | 7.9073% |
| 10% | 4 | 0.9824 | 11.7545% |
