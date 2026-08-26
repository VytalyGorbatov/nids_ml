# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.4883 | 150 / 15024 | 0.9984% | 1098 / 1703 | 64.47% |
| < 5% | 0.3392 | 751 / 15024 | 4.9987% | 1397 / 1703 | 82.03% |
| < 10% | 0.21 | 1502 / 15024 | 9.9973% | 1626 / 1703 | 95.48% |
