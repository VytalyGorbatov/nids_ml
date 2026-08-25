# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.5401 | 139 / 13935 | 0.9975% | 152 / 683 | 22.25% |
| < 5% | 0.2724 | 696 / 13935 | 4.9946% | 501 / 683 | 73.35% |
| < 10% | 0.2004 | 1392 / 13935 | 9.9892% | 553 / 683 | 80.97% |
