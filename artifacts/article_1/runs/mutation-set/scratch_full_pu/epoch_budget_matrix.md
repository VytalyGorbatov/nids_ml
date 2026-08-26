# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 2 (validation AP=0.8879).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4369 | 0.7775 | 644 | 4.6215% |
| 5% | 0.2565 | 0.9034 | 1753 | 12.5798% |
| 10% | 0.2032 | 0.9649 | 2668 | 19.1460% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.7657 / 1620 | 0.8697 / 2873 | 0.9634 / 3741 | 0.4632 |
| 1 | 0.7042 / 1465 | 0.8682 / 2554 | 0.9751 / 3021 | 0.6144 |
| 2 | 0.7775 / 644 | 0.9034 / 1753 | 0.9649 / 2668 | 0.7749 |
| 3 | 0.5827 / 616 | 0.8067 / 1385 | 0.9385 / 2663 | 0.6944 |
| 4 | 0.5095 / 331 | 0.8463 / 1200 | 0.9546 / 2203 | 0.7108 |
| 5 | 0.4026 / 208 | 0.7365 / 1267 | 0.8917 / 2253 | 0.6875 |
| 6 | 0.5373 / 330 | 0.8668 / 1172 | 0.9780 / 2089 | 0.7502 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 2 | 0.7775 | 4.6215% |
| 5% | 2 | 0.9034 | 12.5798% |
| 10% | 6 | 0.9780 | 14.9910% |
