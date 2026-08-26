# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.5248 | 150 / 15024 | 0.9984% | 1111 / 1703 | 65.24% |
| < 5% | 0.3942 | 751 / 15024 | 4.9987% | 1407 / 1703 | 82.62% |
| < 10% | 0.29 | 1502 / 15024 | 9.9973% | 1577 / 1703 | 92.60% |
