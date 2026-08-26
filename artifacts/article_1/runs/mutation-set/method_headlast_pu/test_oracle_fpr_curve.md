# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.6654 | 139 / 13935 | 0.9975% | 98 / 683 | 14.35% |
| < 5% | 0.4191 | 695 / 13935 | 4.9874% | 494 / 683 | 72.33% |
| < 10% | 0.2739 | 1393 / 13935 | 9.9964% | 621 / 683 | 90.92% |
