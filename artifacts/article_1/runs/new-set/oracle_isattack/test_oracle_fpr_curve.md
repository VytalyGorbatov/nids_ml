# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.9951 | 150 / 15024 | 0.9984% | 1416 / 1703 | 83.15% |
| < 5% | 0.003 | 744 / 15024 | 4.9521% | 1651 / 1703 | 96.95% |
| < 10% | 0.0002 | 1278 / 15024 | 8.5064% | 1693 / 1703 | 99.41% |
