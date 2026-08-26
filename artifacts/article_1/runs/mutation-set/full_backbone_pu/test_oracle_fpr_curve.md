# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.4419 | 138 / 13935 | 0.9903% | 361 / 683 | 52.86% |
| < 5% | 0.2581 | 696 / 13935 | 4.9946% | 525 / 683 | 76.87% |
| < 10% | 0.2002 | 1393 / 13935 | 9.9964% | 588 / 683 | 86.09% |
