# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 6 (validation AP=0.9986).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0083 | 1.0000 | 692 | 4.9659% |
| 5% | 0.0004 | 1.0000 | 1703 | 12.2210% |
| 10% | 0.0001 | 1.0000 | 2857 | 20.5023% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.8990 / 773 | 0.9824 / 1150 | 1.0000 / 2461 | 0.9085 |
| 1 | 0.9693 / 748 | 1.0000 / 1147 | 1.0000 / 1830 | 0.9369 |
| 2 | 0.9956 / 684 | 1.0000 / 1221 | 1.0000 / 2101 | 0.9643 |
| 3 | 1.0000 / 678 | 1.0000 / 1259 | 1.0000 / 2285 | 0.9707 |
| 4 | 1.0000 / 686 | 1.0000 / 1415 | 1.0000 / 2431 | 0.9806 |
| 5 | 1.0000 / 709 | 1.0000 / 1547 | 1.0000 / 2674 | 0.9826 |
| 6 | 1.0000 / 692 | 1.0000 / 1703 | 1.0000 / 2857 | 0.9850 |
| 7 | 1.0000 / 645 | 1.0000 / 1572 | 1.0000 / 2783 | 0.9901 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 7 | 1.0000 | 4.6286% |
| 5% | 1 | 1.0000 | 8.2311% |
| 10% | 1 | 1.0000 | 13.1324% |
