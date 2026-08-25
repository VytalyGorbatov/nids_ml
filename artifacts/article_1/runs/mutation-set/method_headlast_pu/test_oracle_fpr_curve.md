# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.7425 | 139 / 13935 | 0.9975% | 95 / 683 | 13.91% |
| < 5% | 0.4438 | 696 / 13935 | 4.9946% | 528 / 683 | 77.31% |
| < 10% | 0.3095 | 1393 / 13935 | 9.9964% | 621 / 683 | 90.92% |
