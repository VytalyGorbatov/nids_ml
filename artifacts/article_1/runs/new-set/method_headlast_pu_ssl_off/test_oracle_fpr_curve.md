# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.5457 | 150 / 15024 | 0.9984% | 1038 / 1703 | 60.95% |
| < 5% | 0.2685 | 751 / 15024 | 4.9987% | 1471 / 1703 | 86.38% |
| < 10% | 0.1319 | 1500 / 15024 | 9.9840% | 1624 / 1703 | 95.36% |
