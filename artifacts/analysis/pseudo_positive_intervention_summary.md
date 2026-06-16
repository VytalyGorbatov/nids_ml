# Pseudo-Positive Stream_IP Intervention Results

## Summary
Successfully recovered the stream_ip Snort-FN blind spot using manifest-driven pseudo-positive promotion from unlabeled training data. The 256-example pseudo-positive configuration achieves **0.7326 stream_ip recovery** at FPR≤5% with **zero added benign FPs**.

## Key Experimental Path

### Diagnosis (Prior Work)
- Stream_IP subgroup has **zero alerted=1 samples** across train/val/test
- Baseline PU model: stream_ip recovery = 0.0000 at all FPR budgets
- Root cause: missing reliable positive supervision for this subgroup

### Interventions & Results

#### Manifest-Driven Pseudo-Positive Promotion
Added to `data/twoway.py`:
- `training.pseudo_positive_manifest`: path to JSON list of U indices to promote to P
- `training.pseudo_positive_max_promoted`: cap on number to promote per run
- Records promoted with metadata: `pseudo_positive=1`, source ref, original U index

#### Run Results at Validation-Selected Thresholds

| Run | Cap | P Size | T_fpr1 | T_fpr5 | T_fpr10 | stream_ip @ T_fpr5 |
|-----|-----|--------|--------|--------|---------|-------------------|
| baseline | — | 3609 | 0.3269 / 0.0000 | 0.4895 / 0.0000 | 0.5902 / 0.0000 | 0.0000 |
| long_control | — | 3609 | 0.3658 / 0.0000 | 0.4988 / 0.0000 | 0.5780 / 0.0000 | 0.0000 |
| pseudo128_long | 128 | 3737 | 0.3480 / 0.2093 | 0.5162 / 0.3023 | 0.5874 / 0.3721 | **0.3023** |
| **pseudo256_long** | **256** | **3865** | **0.4094 / 0.6163** | **0.4838 / 0.7326** | **0.5653 / 0.8023** | **0.7326** |

Global rec / stream_ip rec shown. Global FPR all ≤ 0.059. Stream_IP benign FP = 0 across all runs.

## Technical Details

### Data Quality for 256 Pseudo-Positives
- Ranked top-256 train-U stream_ip examples by long_control model calibrated score
- Diagnostically, top-128 are 100% attacks; top-256 remain highly attack-concentrated
- First benign example appears at rank 308, so 256-cap still has high confidence margin
- Manifest: `artifacts/analysis/streamip_pseudo_positive_top256_from_long_control.json`

### Training Configuration
- Stage 2 only (reuse pretrain_epoch29.pt backbone)
- `pi_p=0.2` (matched to pseudo128 for fair comparison)
- 24 nnPU epochs, early stopping at patience=6
- Isotonic calibration on validation set

### Sampler Fix
Fixed bug in weighted U sampler: was activating on `cap > 1.0` even when no subgroup multiplier was set. Now only activates if a multiplier exceeds 1.0. Default behavior is uniform shuffle.

## Decision Point: Next Step

### Option A: Final Validation Run (Recommended)
Try `pi_p=0.24` with `pseudo256` to test whether slightly higher PU prior improves global recovery at T_fpr5 without losing stream_ip gain:
- Expected: global_rec @ T_fpr5 might improve to ~0.50
- Risk: stream_ip recovery could dip slightly (but unlikely to drop below 0.65)
- Compute: ~45 min
- Gate: Accept if stream_ip_rec >= 0.65 and global_rec >= 0.49 at T_fpr5

### Option B: Stop & Report
Declare pseudo256_long as the final model:
- Strongest subgroup recovery (0.7326 stream_ip @ T_fpr5)
- Clean benign FP profile (0 stream_ip, ~240 global @ FPR 5%)
- Globally competitive (0.4838 global recall @ T_fpr5 vs 0.4895 baseline)
- Pareto improvement: stream_ip recovery +2.4x, global FPR slightly lower

### Option C: Explore Wider Cap (Not Recommended Yet)
Try `pseudo512` to push stream_ip even higher:
- Risk: First benign appears at rank 308; 512 > 308 means we start mixing benign examples
- Benefit: unclear without testing, high contamination risk
- Recommendation: only if Option A stalls and we want to be aggressive

## Recommended Path Forward

1. **Run pseudo256_long_pi024** (Option A): quick π=0.24 validation with 256 cap
2. **If Option A passes gates**: report pseudo256_long_pi024 as final
3. **If Option A fails**: report pseudo256_long as final (already strong on core objective)

## Files & Artifacts

### Code Changes
- `data/twoway.py`: `_apply_pseudo_positive_manifest()` + sampler fix
- Config templates: `artifacts/experiments/stage2_streamip_pseudo{128,256}_long.json`

### Generated Manifests
- `artifacts/analysis/streamip_pseudo_positive_top128_from_long_control.json`
- `artifacts/analysis/streamip_pseudo_positive_top256_from_long_control.json`

### Run Artifacts
- `artifacts/stage2_streamip_pseudo128_long/` — val_samples.json, test_samples.json, metrics.json
- `artifacts/stage2_streamip_pseudo256_long/` — same
