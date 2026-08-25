# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.4378 | 150 / 15024 | 0.9984% | 1121 / 1703 | 65.83% |
| < 5% | 0.2771 | 751 / 15024 | 4.9987% | 1420 / 1703 | 83.38% |
| < 10% | 0.1936 | 1501 / 15024 | 9.9907% | 1573 / 1703 | 92.37% |
