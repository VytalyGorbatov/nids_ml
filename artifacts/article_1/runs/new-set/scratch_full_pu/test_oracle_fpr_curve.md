# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.4507 | 150 / 15024 | 0.9984% | 1364 / 1703 | 80.09% |
| < 5% | 0.2619 | 751 / 15024 | 4.9987% | 1617 / 1703 | 94.95% |
| < 10% | 0.1471 | 1502 / 15024 | 9.9973% | 1684 / 1703 | 98.88% |
