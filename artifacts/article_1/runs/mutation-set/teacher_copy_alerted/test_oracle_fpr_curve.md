# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.2007 | 139 / 13935 | 0.9975% | 20 / 683 | 2.93% |
| < 5% | 0.0177 | 696 / 13935 | 4.9946% | 465 / 683 | 68.08% |
| < 10% | 0.0064 | 1391 / 13935 | 9.9821% | 629 / 683 | 92.09% |
