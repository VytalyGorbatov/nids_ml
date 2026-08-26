# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.6406 | 139 / 13935 | 0.9975% | 217 / 683 | 31.77% |
| < 5% | 0.4322 | 696 / 13935 | 4.9946% | 576 / 683 | 84.33% |
| < 10% | 0.3449 | 1393 / 13935 | 9.9964% | 647 / 683 | 94.73% |
