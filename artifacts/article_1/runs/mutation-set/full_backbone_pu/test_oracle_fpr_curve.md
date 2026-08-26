# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.3327 | 139 / 13935 | 0.9975% | 491 / 683 | 71.89% |
| < 5% | 0.2384 | 695 / 13935 | 4.9874% | 574 / 683 | 84.04% |
| < 10% | 0.2039 | 1391 / 13935 | 9.9821% | 612 / 683 | 89.60% |
