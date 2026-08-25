# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.3682 | 150 / 15024 | 0.9984% | 1221 / 1703 | 71.70% |
| < 5% | 0.2445 | 751 / 15024 | 4.9987% | 1455 / 1703 | 85.44% |
| < 10% | 0.1434 | 1502 / 15024 | 9.9973% | 1628 / 1703 | 95.60% |
