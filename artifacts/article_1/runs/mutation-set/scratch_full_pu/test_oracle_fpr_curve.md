# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.5862 | 139 / 13935 | 0.9975% | 279 / 683 | 40.85% |
| < 5% | 0.4255 | 696 / 13935 | 4.9946% | 546 / 683 | 79.94% |
| < 10% | 0.2867 | 1393 / 13935 | 9.9964% | 587 / 683 | 85.94% |
