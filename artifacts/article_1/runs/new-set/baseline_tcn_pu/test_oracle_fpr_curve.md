# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.2159 | 150 / 15024 | 0.9984% | 1335 / 1703 | 78.39% |
| < 5% | 0.1413 | 750 / 15024 | 4.9920% | 1693 / 1703 | 99.41% |
| < 10% | 0.129 | 1494 / 15024 | 9.9441% | 1696 / 1703 | 99.59% |
