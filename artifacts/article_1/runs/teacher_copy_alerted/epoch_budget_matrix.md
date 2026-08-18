# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 1 (validation AP=0.8721).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|
| 1% | 0.7339 | 127 | 0.7821% |
| 5% | 0.9372 | 790 | 4.8648% |
| 10% | 0.9985 | 1711 | 10.5364% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.7212 / 188 | 0.9230 / 1034 | 0.9836 / 1666 | 0.8928 |
| 1 | 0.7339 / 127 | 0.9372 / 790 | 0.9985 / 1711 | 0.9261 |
| 2 | 0.5478 / 109 | 0.8490 / 705 | 0.9985 / 1896 | 0.8926 |
| 3 | 0.3244 / 8 | 0.8722 / 632 | 0.9970 / 2018 | 0.9106 |
| 4 | 0.3027 / 12 | 0.8199 / 552 | 0.9514 / 1873 | 0.8995 |
| 5 | 0.2601 / 25 | 0.7085 / 673 | 0.8692 / 1935 | 0.8207 |
| 6 | 0.5321 / 162 | 0.7205 / 939 | 0.8102 / 2103 | 0.8150 |
| 7 | 0.1241 / 0 | 0.7294 / 765 | 0.7937 / 1411 | 0.7346 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 1 | 0.7339 | 0.7821% |
| 5% | 1 | 0.9372 | 4.8648% |
| 10% | 1 | 0.9985 | 10.5364% |
