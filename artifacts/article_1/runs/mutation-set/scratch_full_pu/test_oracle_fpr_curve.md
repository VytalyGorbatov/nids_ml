# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.605 | 139 / 13935 | 0.9975% | 156 / 683 | 22.84% |
| < 5% | 0.3794 | 696 / 13935 | 4.9946% | 369 / 683 | 54.03% |
| < 10% | 0.2912 | 1393 / 13935 | 9.9964% | 561 / 683 | 82.14% |
