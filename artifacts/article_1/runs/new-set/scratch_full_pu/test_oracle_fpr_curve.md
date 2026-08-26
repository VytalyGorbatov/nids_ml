# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.1779 | 150 / 15024 | 0.9984% | 1169 / 1703 | 68.64% |
| < 5% | 0.1025 | 750 / 15024 | 4.9920% | 1530 / 1703 | 89.84% |
| < 10% | 0.0793 | 1501 / 15024 | 9.9907% | 1637 / 1703 | 96.12% |
