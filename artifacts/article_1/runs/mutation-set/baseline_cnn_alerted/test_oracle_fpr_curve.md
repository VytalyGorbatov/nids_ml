# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.2467 | 139 / 13935 | 0.9975% | 87 / 683 | 12.74% |
| < 5% | 0.1259 | 696 / 13935 | 4.9946% | 224 / 683 | 32.80% |
| < 10% | 0.0842 | 1392 / 13935 | 9.9892% | 344 / 683 | 50.37% |
