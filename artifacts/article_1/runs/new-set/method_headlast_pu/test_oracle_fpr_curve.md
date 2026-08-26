# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.4947 | 150 / 15024 | 0.9984% | 979 / 1703 | 57.49% |
| < 5% | 0.2514 | 751 / 15024 | 4.9987% | 1465 / 1703 | 86.02% |
| < 10% | 0.1237 | 1500 / 15024 | 9.9840% | 1635 / 1703 | 96.01% |
