# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.4398 | 150 / 15024 | 0.9984% | 1149 / 1703 | 67.47% |
| < 5% | 0.3039 | 751 / 15024 | 4.9987% | 1454 / 1703 | 85.38% |
| < 10% | 0.2204 | 1500 / 15024 | 9.9840% | 1602 / 1703 | 94.07% |
