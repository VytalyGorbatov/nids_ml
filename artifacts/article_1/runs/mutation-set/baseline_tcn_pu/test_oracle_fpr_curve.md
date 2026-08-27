# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.6427 | 139 / 13935 | 0.9975% | 196 / 683 | 28.70% |
| < 5% | 0.4864 | 695 / 13935 | 4.9874% | 451 / 683 | 66.03% |
| < 10% | 0.3815 | 1392 / 13935 | 9.9892% | 568 / 683 | 83.16% |
