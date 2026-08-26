# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.5644 | 149 / 15024 | 0.9917% | 1066 / 1703 | 62.60% |
| < 5% | 0.327 | 751 / 15024 | 4.9987% | 1480 / 1703 | 86.91% |
| < 10% | 0.1979 | 1502 / 15024 | 9.9973% | 1628 / 1703 | 95.60% |
