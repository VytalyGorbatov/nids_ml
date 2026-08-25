# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

## Reportable Validation Selection

Checkpoint policy: maximum validation AP. Selected epoch: 5 (validation AP=0.9109).
The following test values use that single validation-selected checkpoint.

| nominal FPR budget | threshold | Snort-FN recovery | added benign FP | observed test FPR |
|---|---:|---:|---:|---:|
| 1% | 0.4464 | 0.6653 | 128 | 0.8520% |
| 5% | 0.2988 | 0.8573 | 783 | 5.2117% |
| 10% | 0.1726 | 0.9701 | 2152 | 14.3237% |

## All Epochs (Diagnostic)

Do not choose an epoch from this table using test results.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test AP |
|---|---|---|---|---|
| 0 | 0.6230 / 47 | 0.7868 / 345 | 0.9207 / 1380 | 0.9138 |
| 1 | 0.6277 / 93 | 0.7857 / 405 | 0.9425 / 1471 | 0.9141 |
| 2 | 0.6477 / 44 | 0.8884 / 834 | 0.9765 / 1999 | 0.9291 |
| 3 | 0.5531 / 19 | 0.8344 / 511 | 0.9736 / 2036 | 0.9248 |
| 4 | 0.5948 / 37 | 0.8784 / 820 | 0.9783 / 2187 | 0.9249 |
| 5 | 0.6653 / 128 | 0.8573 / 783 | 0.9701 / 2152 | 0.9169 |
| 6 | 0.6747 / 144 | 0.8397 / 757 | 0.9560 / 1876 | 0.9150 |

## Test-Oracle Diagnostics (Not Reportable)

These entries retrospectively choose an epoch on test data and are diagnostics only, never article results or operational settings.

| nominal FPR budget | test-selected epoch | recovery | observed test FPR |
|---|---:|---:|---:|
| 1% | 6 | 0.6747 | 0.9585% |
| 5% | 2 | 0.8884 | 5.5511% |
| 10% | 4 | 0.9783 | 14.5567% |
