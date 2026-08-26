# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.4965 | 150 / 15024 | 0.9984% | 1145 / 1703 | 67.23% |
| < 5% | 0.3787 | 751 / 15024 | 4.9987% | 1428 / 1703 | 83.85% |
| < 10% | 0.2724 | 1502 / 15024 | 9.9973% | 1587 / 1703 | 93.19% |
