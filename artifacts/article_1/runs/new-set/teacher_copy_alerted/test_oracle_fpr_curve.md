# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.0172 | 149 / 15024 | 0.9917% | 1022 / 1703 | 60.01% |
| < 5% | 0.0048 | 751 / 15024 | 4.9987% | 1404 / 1703 | 82.44% |
| < 10% | 0.0019 | 1487 / 15024 | 9.8975% | 1554 / 1703 | 91.25% |
