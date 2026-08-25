# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.959 | 139 / 13935 | 0.9975% | 616 / 683 | 90.19% |
| < 5% | 0.0068 | 695 / 13935 | 4.9874% | 682 / 683 | 99.85% |
| < 10% | 0.001 | 1360 / 13935 | 9.7596% | 683 / 683 | 100.00% |
