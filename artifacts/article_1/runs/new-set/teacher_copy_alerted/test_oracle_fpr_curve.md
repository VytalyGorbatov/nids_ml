# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.007 | 148 / 15024 | 0.9851% | 1074 / 1703 | 63.07% |
| < 5% | 0.0017 | 747 / 15024 | 4.9720% | 1442 / 1703 | 84.67% |
| < 10% | 0.0005 | 1396 / 15024 | 9.2918% | 1586 / 1703 | 93.13% |
