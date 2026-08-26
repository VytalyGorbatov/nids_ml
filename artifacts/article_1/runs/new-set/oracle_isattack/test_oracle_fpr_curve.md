# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.9892 | 150 / 15024 | 0.9984% | 1463 / 1703 | 85.91% |
| < 5% | 0.0008 | 735 / 15024 | 4.8922% | 1678 / 1703 | 98.53% |
| < 10% | 0.0002 | 1310 / 15024 | 8.7194% | 1696 / 1703 | 99.59% |
