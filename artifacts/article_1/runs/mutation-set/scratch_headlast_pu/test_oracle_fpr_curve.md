# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.7304 | 138 / 13935 | 0.9903% | 102 / 683 | 14.93% |
| < 5% | 0.5853 | 696 / 13935 | 4.9946% | 288 / 683 | 42.17% |
| < 10% | 0.3971 | 1393 / 13935 | 9.9964% | 490 / 683 | 71.74% |
