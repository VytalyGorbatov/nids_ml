# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.8695 | 139 / 13935 | 0.9975% | 631 / 683 | 92.39% |
| < 5% | 0.0083 | 696 / 13935 | 4.9946% | 683 / 683 | 100.00% |
| < 10% | 0.0007 | 1378 / 13935 | 9.8888% | 683 / 683 | 100.00% |
