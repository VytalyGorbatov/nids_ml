# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.0553 | 139 / 13935 | 0.9975% | 378 / 683 | 55.34% |
| < 5% | 0.0296 | 694 / 13935 | 4.9803% | 516 / 683 | 75.55% |
| < 10% | 0.019 | 1393 / 13935 | 9.9964% | 569 / 683 | 83.31% |
