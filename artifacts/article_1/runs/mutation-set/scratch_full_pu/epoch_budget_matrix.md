# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 2 (validation AP=0.6704).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.3067 | 0.4495 | 916 | 6.5734% |
| 5% | 0.2306 | 0.5622 | 1326 | 9.5156% |
| 10% | 0.1904 | 0.7116 | 2350 | 16.8640% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.2196 / 605 | 0.5242 / 1649 | 0.7291 / 3032 | 0.3366 |
| 1 | 0.3163 / 655 | 0.5520 / 1611 | 0.7204 / 2572 | 0.3694 |
| 2 | 0.4495 / 916 | 0.5622 / 1326 | 0.7116 / 2350 | 0.4926 |
| 3 | 0.3060 / 342 | 0.4949 / 1247 | 0.7379 / 2064 | 0.5616 |
| 4 | 0.3572 / 314 | 0.5710 / 1177 | 0.7101 / 2216 | 0.6050 |
| 5 | 0.2958 / 154 | 0.7101 / 1045 | 0.9209 / 2384 | 0.6051 |
| 6 | 0.2679 / 260 | 0.5871 / 1222 | 0.7233 / 1792 | 0.5273 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 2 | 0.4495 | 6.5734% |
| 5% | 5 | 0.7101 | 7.4991% |
| 10% | 5 | 0.9209 | 17.1080% |
