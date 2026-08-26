# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.4168 | 149 / 15024 | 0.9917% | 1118 / 1703 | 65.65% |
| < 5% | 0.2798 | 751 / 15024 | 4.9987% | 1540 / 1703 | 90.43% |
| < 10% | 0.187 | 1500 / 15024 | 9.9840% | 1670 / 1703 | 98.06% |
