# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.4741 | 150 / 15024 | 0.9984% | 1195 / 1703 | 70.17% |
| < 5% | 0.2947 | 751 / 15024 | 4.9987% | 1568 / 1703 | 92.07% |
| < 10% | 0.1856 | 1502 / 15024 | 9.9973% | 1658 / 1703 | 97.36% |
