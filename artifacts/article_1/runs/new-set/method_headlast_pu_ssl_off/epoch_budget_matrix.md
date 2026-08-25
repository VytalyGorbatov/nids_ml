# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 2 (validation AP=0.8996).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4192 | 0.6665 | 65 | 0.4326% |
| 5% | 0.2114 | 0.8949 | 968 | 6.4430% |
| 10% | 0.0992 | 0.9812 | 2024 | 13.4718% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6277 / 55 | 0.7792 / 343 | 0.9154 / 1165 | 0.9148 |
| 1 | 0.6312 / 107 | 0.7833 / 402 | 0.9489 / 1535 | 0.9161 |
| 2 | 0.6665 / 65 | 0.8949 / 968 | 0.9812 / 2024 | 0.9263 |
| 3 | 0.5520 / 24 | 0.8338 / 622 | 0.9853 / 1915 | 0.9229 |
| 4 | 0.5661 / 29 | 0.8755 / 885 | 0.9877 / 2269 | 0.9260 |
| 5 | 0.6301 / 96 | 0.8485 / 845 | 0.9812 / 2296 | 0.9167 |
| 6 | 0.6723 / 217 | 0.8573 / 807 | 0.9771 / 2000 | 0.9124 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.6723 | 1.4444% |
| 5% | 2 | 0.8949 | 6.4430% |
| 10% | 4 | 0.9877 | 15.1025% |
