# 10-Iteration Improvement Campaign

Best iteration: 1 - baseline_raw@0.5

## Best iteration summary
- Selected threshold: 0.5000
- Test PR-AUC: 0.8338
- Test F1: 0.7087
- Precision: 0.8328
- Recall: 0.6167
- Snort FN recovery @FPR<=10%: 0.5902
- Snort FN recovery @FPR<=5%: 0.4895
- Snort FN recovery @FPR<=1%: 0.3269

## Ranking (primary: FN recovery at FPR<=5%)
1. iter 1 baseline_raw@0.5 | FN@10%=0.5902, FN@5%=0.4895, FN@1%=0.3269, F1=0.7087, P=0.8328, R=0.6167
2. iter 2 prior_correction@0.5 | FN@10%=0.5902, FN@5%=0.4895, FN@1%=0.3269, F1=0.6950, P=0.6224, R=0.7868
3. iter 3 platt@0.5 | FN@10%=0.5902, FN@5%=0.4895, FN@1%=0.3269, F1=0.7060, P=0.8366, R=0.6106
4. iter 4 isotonic@0.5 | FN@10%=0.5902, FN@5%=0.4895, FN@1%=0.3269, F1=0.7102, P=0.8287, R=0.6213
5. iter 5 prior_plus_platt@0.5 | FN@10%=0.5902, FN@5%=0.4895, FN@1%=0.3269, F1=0.7060, P=0.8366, R=0.6106
6. iter 6 policy_T_f1_on_baseline_raw@0.5 | FN@10%=0.5902, FN@5%=0.4895, FN@1%=0.3269, F1=0.7222, P=0.7752, R=0.6760
7. iter 7 policy_T_p90_on_baseline_raw@0.5 | FN@10%=0.5902, FN@5%=0.4895, FN@1%=0.3269, F1=0.6536, P=0.8873, R=0.5174
8. iter 8 policy_T_fpr10_on_baseline_raw@0.5 | FN@10%=0.5902, FN@5%=0.4895, FN@1%=0.3269, F1=0.7210, P=0.7865, R=0.6656
9. iter 9 policy_T_fpr5_on_baseline_raw@0.5 | FN@10%=0.5902, FN@5%=0.4895, FN@1%=0.3269, F1=0.6939, P=0.8559, R=0.5835
10. iter 10 policy_T_fpr1_on_baseline_raw@0.5 | FN@10%=0.5902, FN@5%=0.4895, FN@1%=0.3269, F1=0.6149, P=0.9664, R=0.4509
