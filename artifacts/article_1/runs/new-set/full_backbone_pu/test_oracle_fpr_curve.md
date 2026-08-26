# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.6464 | 150 / 15024 | 0.9984% | 854 / 1703 | 50.15% |
| < 5% | 0.4418 | 751 / 15024 | 4.9987% | 1414 / 1703 | 83.03% |
| < 10% | 0.3488 | 1502 / 15024 | 9.9973% | 1544 / 1703 | 90.66% |
