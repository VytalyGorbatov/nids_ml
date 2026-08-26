# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 5 (validation AP=0.8742).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.3949 | 0.7046 | 321 | 2.1366% |
| 5% | 0.2357 | 0.8779 | 819 | 5.4513% |
| 10% | 0.1039 | 0.9706 | 1709 | 11.3751% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6242 / 175 | 0.7786 / 480 | 0.9154 / 1199 | 0.8964 |
| 1 | 0.5872 / 208 | 0.7669 / 512 | 0.9419 / 1442 | 0.8780 |
| 2 | 0.6594 / 303 | 0.7951 / 537 | 0.9495 / 1452 | 0.8835 |
| 3 | 0.6682 / 249 | 0.8315 / 726 | 0.9648 / 1609 | 0.9029 |
| 4 | 0.6224 / 205 | 0.8009 / 609 | 0.9624 / 1669 | 0.8947 |
| 5 | 0.7046 / 321 | 0.8779 / 819 | 0.9706 / 1709 | 0.9014 |
| 6 | 0.6759 / 251 | 0.8837 / 964 | 0.9513 / 1502 | 0.8979 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 5 | 0.7046 | 2.1366% |
| 5% | 6 | 0.8837 | 6.4164% |
| 10% | 5 | 0.9706 | 11.3751% |
