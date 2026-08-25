# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.9977 | 149 / 15024 | 0.9917% | 1449 / 1703 | 85.09% |
| < 5% | 0.0017 | 750 / 15024 | 4.9920% | 1668 / 1703 | 97.94% |
| < 10% | 0.0002 | 1480 / 15024 | 9.8509% | 1691 / 1703 | 99.30% |
