# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 3 (validation AP=0.8944).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4509 | 0.8191 | 706 | 4.6991% |
| 5% | 0.3612 | 0.8978 | 1356 | 9.0256% |
| 10% | 0.3139 | 0.9278 | 1957 | 13.0258% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6383 / 95 | 0.8215 / 678 | 0.9336 / 1634 | 0.9117 |
| 1 | 0.6853 / 414 | 0.8315 / 1121 | 0.8937 / 1826 | 0.8763 |
| 2 | 0.6735 / 340 | 0.8021 / 1146 | 0.8761 / 1986 | 0.8775 |
| 3 | 0.8191 / 706 | 0.8978 / 1356 | 0.9278 / 1957 | 0.8795 |
| 4 | 0.6823 / 616 | 0.7898 / 1308 | 0.8479 / 2039 | 0.8127 |
| 5 | 0.5314 / 444 | 0.7052 / 1226 | 0.7915 / 2010 | 0.8003 |
| 6 | 0.5267 / 458 | 0.6888 / 1136 | 0.7769 / 1937 | 0.7917 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 3 | 0.8191 | 4.6991% |
| 5% | 3 | 0.8978 | 9.0256% |
| 10% | 0 | 0.9336 | 10.8759% |
