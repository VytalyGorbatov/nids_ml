# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.019 | 150 / 15024 | 0.9984% | 824 / 1703 | 48.39% |
| < 5% | 0.0034 | 746 / 15024 | 4.9654% | 1278 / 1703 | 75.04% |
| < 10% | 0.001 | 1463 / 15024 | 9.7378% | 1489 / 1703 | 87.43% |
