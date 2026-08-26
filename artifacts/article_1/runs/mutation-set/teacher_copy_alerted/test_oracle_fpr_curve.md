# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.0577 | 139 / 13935 | 0.9975% | 365 / 683 | 53.44% |
| < 5% | 0.0313 | 696 / 13935 | 4.9946% | 500 / 683 | 73.21% |
| < 10% | 0.0184 | 1390 / 13935 | 9.9749% | 573 / 683 | 83.89% |
