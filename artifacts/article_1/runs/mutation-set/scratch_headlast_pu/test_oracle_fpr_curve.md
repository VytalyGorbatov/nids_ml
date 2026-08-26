# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.6465 | 138 / 13935 | 0.9903% | 81 / 683 | 11.86% |
| < 5% | 0.3669 | 696 / 13935 | 4.9946% | 447 / 683 | 65.45% |
| < 10% | 0.2137 | 1393 / 13935 | 9.9964% | 571 / 683 | 83.60% |
