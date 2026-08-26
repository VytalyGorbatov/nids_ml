# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 0 (validation AP=0.8429).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.3408 | 0.7130 | 123 | 0.8827% |
| 5% | 0.2349 | 0.8448 | 739 | 5.3032% |
| 10% | 0.1874 | 0.9195 | 1993 | 14.3021% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.7130 / 123 | 0.8448 / 739 | 0.9195 / 1993 | 0.8921 |
| 1 | 0.3455 / 95 | 0.7057 / 1328 | 0.7745 / 2096 | 0.6824 |
| 2 | 0.4129 / 111 | 0.7540 / 906 | 0.8638 / 2072 | 0.7416 |
| 3 | 0.0791 / 108 | 0.6720 / 797 | 0.8009 / 1770 | 0.5295 |
| 4 | 0.4041 / 118 | 0.7174 / 1027 | 0.8053 / 2304 | 0.7102 |
| 5 | 0.2621 / 108 | 0.5798 / 642 | 0.6413 / 1119 | 0.6068 |
| 6 | 0.0761 / 103 | 0.4202 / 632 | 0.5271 / 1094 | 0.4472 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 0 | 0.7130 | 0.8827% |
| 5% | 0 | 0.8448 | 5.3032% |
| 10% | 0 | 0.9195 | 14.3021% |
