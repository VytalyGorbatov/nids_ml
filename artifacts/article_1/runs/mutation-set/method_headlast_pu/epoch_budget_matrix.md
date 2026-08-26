# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 2 (validation AP=0.8795).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4271 | 0.7540 | 429 | 3.0786% |
| 5% | 0.2863 | 0.9312 | 1359 | 9.7524% |
| 10% | 0.1896 | 0.9693 | 2221 | 15.9383% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6574 / 158 | 0.9034 / 1041 | 0.9649 / 1807 | 0.8686 |
| 1 | 0.7160 / 335 | 0.8843 / 1149 | 0.9678 / 2132 | 0.8423 |
| 2 | 0.7540 / 429 | 0.9312 / 1359 | 0.9693 / 2221 | 0.8255 |
| 3 | 0.7262 / 430 | 0.8799 / 1182 | 0.9678 / 1995 | 0.7967 |
| 4 | 0.4085 / 223 | 0.8228 / 1109 | 0.9649 / 1993 | 0.6448 |
| 5 | 0.6413 / 383 | 0.8975 / 1205 | 0.9649 / 1971 | 0.7496 |
| 6 | 0.4612 / 249 | 0.8302 / 1216 | 0.9268 / 2153 | 0.6631 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 2 | 0.7540 | 3.0786% |
| 5% | 2 | 0.9312 | 9.7524% |
| 10% | 2 | 0.9693 | 15.9383% |
