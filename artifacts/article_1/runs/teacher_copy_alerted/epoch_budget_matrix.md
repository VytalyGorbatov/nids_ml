# Epoch x Budget Matrix

Each cell = R (Snort-FN recovery) / benign FP added, at a val-selected FPR budget applied to test.

| epoch | FPR<=1% | FPR<=5% | FPR<=10% | test PR-AUC |
|---|---|---|---|---|
| 0 | 0.0501 / 38 | 0.1883 / 223 | 0.2370 / 484 | 0.6930 |
| 1 | 0.0061 / 40 | 0.1649 / 251 | 0.2581 / 475 | 0.6881 |
| 2 | 0.0037 / 38 | 0.1326 / 235 | 0.2112 / 451 | 0.6680 |
| 3 | 0.0117 / 48 | 0.1185 / 228 | 0.1813 / 464 | 0.6611 |
| 4 | 0.0098 / 52 | 0.1054 / 241 | 0.1653 / 464 | 0.6584 |
