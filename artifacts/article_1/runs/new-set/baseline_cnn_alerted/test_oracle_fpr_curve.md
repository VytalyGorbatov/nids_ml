# Test-Oracle Strict-FPR Diagnostic

Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.

| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |
|---:|---:|---:|---:|---:|---:|
| < 1% | 0.0425 | 149 / 15024 | 0.9917% | 466 / 1703 | 27.36% |
| < 5% | 0.0138 | 747 / 15024 | 4.9720% | 744 / 1703 | 43.69% |
| < 10% | 0.0072 | 1491 / 15024 | 9.9241% | 933 / 1703 | 54.79% |
