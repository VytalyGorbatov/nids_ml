# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 3 (validation AP=0.8994).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0133 | 0.6512 | 264 | 1.7572% |
| 5% | 0.0043 | 0.8356 | 810 | 5.3914% |
| 10% | 0.0015 | 0.9301 | 1663 | 11.0690% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.5361 / 0 | 0.8191 / 635 | 0.9266 / 2146 | 0.8991 |
| 1 | 0.6195 / 35 | 0.7446 / 321 | 0.9260 / 1305 | 0.9158 |
| 2 | 0.5244 / 22 | 0.6941 / 313 | 0.9231 / 1423 | 0.9072 |
| 3 | 0.6512 / 264 | 0.8356 / 810 | 0.9301 / 1663 | 0.9012 |
| 4 | 0.6676 / 233 | 0.8679 / 1196 | 0.9295 / 2029 | 0.8984 |
| 5 | 0.7363 / 728 | 0.8784 / 1617 | 0.9196 / 2389 | 0.8581 |
| 6 | 0.6905 / 806 | 0.8291 / 1679 | 0.8831 / 2455 | 0.8136 |
| 7 | 0.1715 / 6 | 0.4463 / 713 | 0.5866 / 2270 | 0.5626 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 5 | 0.7363 | 4.8456% |
| 5% | 5 | 0.8784 | 10.7628% |
| 10% | 3 | 0.9301 | 11.0690% |
