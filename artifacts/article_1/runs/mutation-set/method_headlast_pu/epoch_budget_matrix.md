# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.8407).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.5302 | 0.6164 | 453 | 3.2508% |
| 5% | 0.3412 | 0.8829 | 1213 | 8.7047% |
| 10% | 0.2036 | 0.9590 | 1865 | 13.3836% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6164 / 453 | 0.8829 / 1213 | 0.9590 / 1865 | 0.5944 |
| 1 | 0.6179 / 497 | 0.8858 / 1183 | 0.9502 / 1810 | 0.5271 |
| 2 | 0.6823 / 495 | 0.8902 / 1147 | 0.9488 / 1722 | 0.5496 |
| 3 | 0.5124 / 492 | 0.8682 / 1105 | 0.9473 / 1624 | 0.5017 |
| 4 | 0.4597 / 439 | 0.8682 / 1088 | 0.9283 / 1715 | 0.5029 |
| 5 | 0.5461 / 450 | 0.8199 / 1042 | 0.8975 / 1626 | 0.5251 |
| 6 | 0.5681 / 433 | 0.7936 / 1082 | 0.8594 / 1704 | 0.5004 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 2 | 0.6823 | 3.5522% |
| 5% | 2 | 0.8902 | 8.2311% |
| 10% | 0 | 0.9590 | 13.3836% |
