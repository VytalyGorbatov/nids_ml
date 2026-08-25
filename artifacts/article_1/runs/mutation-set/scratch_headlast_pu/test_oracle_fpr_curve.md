# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.4891 | 139 / 13935 | 0.9975% | 268 / 683 | 39.24% |
| < 5% | 0.3621 | 696 / 13935 | 4.9946% | 553 / 683 | 80.97% |
| < 10% | 0.2952 | 1393 / 13935 | 9.9964% | 635 / 683 | 92.97% |
