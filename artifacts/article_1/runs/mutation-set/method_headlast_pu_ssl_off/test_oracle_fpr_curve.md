# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.6372 | 139 / 13935 | 0.9975% | 128 / 683 | 18.74% |
| < 5% | 0.4049 | 696 / 13935 | 4.9946% | 506 / 683 | 74.08% |
| < 10% | 0.2688 | 1393 / 13935 | 9.9964% | 613 / 683 | 89.75% |
