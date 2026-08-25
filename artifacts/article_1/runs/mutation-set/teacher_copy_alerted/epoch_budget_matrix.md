# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 1 (validation AP=0.7699).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.0292 | 0.5403 | 448 | 3.2149% |
| 5% | 0.0097 | 0.8389 | 1092 | 7.8364% |
| 10% | 0.0033 | 0.9561 | 1671 | 11.9914% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.4641 / 411 | 0.7687 / 1068 | 0.9327 / 1876 | 0.5960 |
| 1 | 0.5403 / 448 | 0.8389 / 1092 | 0.9561 / 1671 | 0.5215 |
| 2 | 0.3646 / 469 | 0.6999 / 1007 | 0.9004 / 1571 | 0.5108 |
| 3 | 0.2006 / 445 | 0.6032 / 1034 | 0.8360 / 1569 | 0.4205 |
| 4 | 0.1786 / 333 | 0.6384 / 1027 | 0.7862 / 1985 | 0.4308 |
| 5 | 0.0864 / 294 | 0.5095 / 1074 | 0.7130 / 2279 | 0.3366 |
| 6 | 0.1332 / 253 | 0.4334 / 1483 | 0.6398 / 2586 | 0.3135 |
| 7 | 0.2240 / 431 | 0.6296 / 1038 | 0.7599 / 2747 | 0.4053 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 1 | 0.5403 | 3.2149% |
| 5% | 1 | 0.8389 | 7.8364% |
| 10% | 1 | 0.9561 | 11.9914% |
