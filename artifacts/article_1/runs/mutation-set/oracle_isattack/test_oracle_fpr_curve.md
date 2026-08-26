# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.9578 | 139 / 13935 | 0.9975% | 530 / 683 | 77.60% |
| < 5% | 0.0243 | 696 / 13935 | 4.9946% | 678 / 683 | 99.27% |
| < 10% | 0.0005 | 1345 / 13935 | 9.6520% | 682 / 683 | 99.85% |
