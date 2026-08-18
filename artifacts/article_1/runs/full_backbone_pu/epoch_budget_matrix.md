# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.8921).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.7078 | 170 | 1.0469% |
| 5% | 0.8700 | 737 | 4.5385% |
| 10% | 0.9679 | 2000 | 12.3160% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.7078 / 170 | 0.8700 / 737 | 0.9679 / 2000 | 0.9048 |
| 1 | 0.4723 / 281 | 0.7145 / 1373 | 0.8161 / 2556 | 0.7652 |
| 2 | 0.3176 / 315 | 0.6480 / 1393 | 0.7638 / 2391 | 0.6841 |
| 3 | 0.2975 / 273 | 0.6286 / 1386 | 0.7631 / 2410 | 0.6803 |
| 4 | 0.3027 / 192 | 0.5815 / 1120 | 0.7040 / 1941 | 0.6967 |
| 5 | 0.2818 / 218 | 0.6031 / 1250 | 0.7317 / 2102 | 0.6856 |
| 6 | 0.2997 / 172 | 0.5673 / 1028 | 0.7018 / 1916 | 0.7000 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 0 | 0.7078 | 1.0469% |
| 5% | 0 | 0.8700 | 4.5385% |
| 10% | 0 | 0.9679 | 12.3160% |
