# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test PR-AUC |
|---|---|---|---|---|
| 0 | 0.1663 / 58 | 0.2862 / 228 | 0.3696 / 445 | 0.6522 |
| 1 | 0.0581 / 41 | 0.2061 / 218 | 0.3644 / 444 | 0.6585 |
| 2 | 0.0412 / 38 | 0.1878 / 212 | 0.2904 / 454 | 0.6490 |
| 3 | 0.0370 / 35 | 0.1859 / 235 | 0.2398 / 468 | 0.6479 |
