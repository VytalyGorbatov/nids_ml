# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.7735 | 139 / 13935 | 0.9975% | 36 / 683 | 5.27% |
| < 5% | 0.4027 | 696 / 13935 | 4.9946% | 523 / 683 | 76.57% |
| < 10% | 0.2706 | 1393 / 13935 | 9.9964% | 625 / 683 | 91.51% |
