# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.4825 | 150 / 15024 | 0.9984% | 989 / 1703 | 58.07% |
| < 5% | 0.3252 | 751 / 15024 | 4.9987% | 1472 / 1703 | 86.44% |
| < 10% | 0.2449 | 1502 / 15024 | 9.9973% | 1571 / 1703 | 92.25% |
