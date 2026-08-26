# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 2 (validation AP=0.8916).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4673 | 0.7701 | 515 | 3.6957% |
| 5% | 0.3487 | 0.9444 | 1365 | 9.7955% |
| 10% | 0.2307 | 0.9707 | 2291 | 16.4406% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.7306 / 242 | 0.9239 / 1265 | 0.9663 / 1940 | 0.8846 |
| 1 | 0.7408 / 426 | 0.9122 / 1250 | 0.9707 / 2152 | 0.7935 |
| 2 | 0.7701 / 515 | 0.9444 / 1365 | 0.9707 / 2291 | 0.7092 |
| 3 | 0.7189 / 467 | 0.8785 / 1173 | 0.9634 / 2081 | 0.7280 |
| 4 | 0.5505 / 351 | 0.8507 / 1132 | 0.9693 / 1977 | 0.6899 |
| 5 | 0.6881 / 479 | 0.9253 / 1209 | 0.9707 / 1817 | 0.7278 |
| 6 | 0.5417 / 403 | 0.8507 / 1188 | 0.9517 / 1971 | 0.6395 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 2 | 0.7701 | 3.6957% |
| 5% | 2 | 0.9444 | 9.7955% |
| 10% | 5 | 0.9707 | 13.0391% |
