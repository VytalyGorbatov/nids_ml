# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.5316 | 139 / 13935 | 0.9975% | 403 / 683 | 59.00% |
| < 5% | 0.376 | 696 / 13935 | 4.9946% | 569 / 683 | 83.31% |
| < 10% | 0.283 | 1393 / 13935 | 9.9964% | 639 / 683 | 93.56% |
