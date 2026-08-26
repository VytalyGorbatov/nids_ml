# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.5287 | 139 / 13935 | 0.9975% | 158 / 683 | 23.13% |
| < 5% | 0.4019 | 696 / 13935 | 4.9946% | 214 / 683 | 31.33% |
| < 10% | 0.225 | 1393 / 13935 | 9.9964% | 394 / 683 | 57.69% |
