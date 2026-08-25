# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 6 (validation AP=0.9073).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4513 | 0.6518 | 246 | 1.6374% |
| 5% | 0.2833 | 0.8967 | 1095 | 7.2883% |
| 10% | 0.2175 | 0.9383 | 1843 | 12.2670% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6395 / 27 | 0.7416 / 957 | 0.8227 / 2333 | 0.8507 |
| 1 | 0.6101 / 16 | 0.8456 / 929 | 0.9331 / 1933 | 0.9100 |
| 2 | 0.5796 / 20 | 0.8831 / 1023 | 0.9430 / 1829 | 0.9175 |
| 3 | 0.5966 / 71 | 0.9025 / 1143 | 0.9495 / 1794 | 0.9147 |
| 4 | 0.5573 / 98 | 0.9072 / 1115 | 0.9489 / 1832 | 0.9130 |
| 5 | 0.6142 / 171 | 0.9002 / 1111 | 0.9448 / 1802 | 0.9086 |
| 6 | 0.6518 / 246 | 0.8967 / 1095 | 0.9383 / 1843 | 0.9055 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.6518 | 1.6374% |
| 5% | 4 | 0.9072 | 7.4215% |
| 10% | 3 | 0.9495 | 11.9409% |
