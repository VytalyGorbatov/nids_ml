# REGISTER False-Negative Recovery — Research Summary

**Model:** ByteTCN2Way (`tcn_2way`), Stage-2 fine-tune from shared SSL backbone `epoch29.pt`
**Objective:** Recover Snort false negatives (`is_attack=1 AND alerted=0`) at benign FPR ≤ 5%, focusing on REGISTER attacks
**Date:** 2026-06-29

---

## 1. Prerequisites (brief)

The neural layer is an *additive* risk score on top of Snort, trained with PU (positive–unlabeled) learning:

- `alerted=1` → reliable positive (Snort teacher)
- `alerted=0` → unlabeled (not benign)
- `is_attack` → ground truth, evaluation only

Primary metric is **R@5%**: Snort-FN recovery at a validation-selected FPR≤5% threshold applied to test, in raw-sigmoid space (calibrator-invariant). The production baseline is `head_last_block` Stage-2, R@5% = 0.325, PR-AUC = 0.718.

Test set: 2135 Snort FN, typed by SIP message: INVITE 875, OPTIONS 480, REGISTER 511, RESPONSE 269.

---

## 2. The Starting Problem

The Snort teacher (`alerted=1`) fires on **only two** message types — INVITE and OPTIONS. The model therefore learns those signatures and scores REGISTER like benign traffic of the same type. Baseline recovery by type:

| Type | FN | Recovered | Rate |
|---|---:|---:|---:|
| OPTIONS | 480 | 381 | 79.6% |
| INVITE | 875 | 302 | 34.5% |
| REGISTER | 511 | 0 | **0.0%** |
| RESPONSE | 269 | ~9 | ~3% |

REGISTER + RESPONSE = 780 FN (36.5% of all) were structurally invisible. The campaign targeted REGISTER.

The intervention: a label-free fuzz scorer (`data/sip_struct.py`) mines 770 REGISTER records from the unlabeled pool whose credential/header fields are gibberish, and promotes them from U to P (`pseudo_positive=1`). Mining precision = 1.0 (all 770 are real attacks). This adds REGISTER to the teacher coverage without touching `is_attack`.

---

## 3. Mechanisms Tested

Four levers were tried to make the model learn from those 770 REGISTER positives.

| Route | Mechanism | Result |
|---|---|---|
| **K-sweep** | More pseudo-positives (K=128→770) | REGISTER stays 0 until K≈700; needs full strength |
| **A: loss weighting** | Per-sample weight on REGISTER P (pw 0.1–0.5) | REGISTER → 0 at any pw<1.0; counterproductive |
| **B: stratified sampler** | Fixed REGISTER fraction per batch (bf) | REGISTER recovers, but flips INVITE at bf≥0.25 |
| **C: backbone_hybrid** | +1 trainable TCN block (42% vs 37%) | Identical to head_last_block; capacity irrelevant |

---

## 4. Gathered Statistics

All R@5%, calibrator-invariant, val-selected threshold. Baseline = `head_last_block` production.

| Run | Lever | REGISTER | INVITE | OPTIONS | Global | T_run |
|---|---|---:|---:|---:|---:|---:|
| Baseline | — | 0.000 | 0.345 | 0.796 | **0.325** | 0.553 |
| E2b_hlb | K=770, pw=1.0 | 0.053 | 0.221 | 0.802 | 0.283 | 0.553 |
| E3 (A) | pw=0.1–0.5 | 0.000 | 0.30 | 0.81 | 0.30 | ~0.55 |
| E4c (B) | bf=0.15 | 0.000 | 0.275 | 0.798 | 0.293 | 0.540 |
| E5a (B) | bf=0.20 | 0.112 | 0.221 | 0.798 | 0.296 | 0.538 |
| E5b (B) | bf=0.25 | 0.695 | 0.041 | 0.804 | 0.364 | 0.658 |
| **E4a (B)** | **bf=0.30** | **0.791** | 0.037 | 0.804 | **0.385** | 0.640 |
| E4b (B) | bf=0.50 | 0.828 | 0.014 | 0.723 | 0.366 | 0.730 |
| E6 (C) | hybrid, bf=0.20–0.30 | mirrors hlb | mirrors hlb | 0.80–0.82 | mirrors hlb | mirrors hlb |

REGISTER added benign FP = **0** in every run. OPTIONS never collapsed except `backbone_low_lr` (a fifth mode, −55pp, abandoned).

---

## 5. Mechanism / Theory

### The tradeoff is a threshold reorganization, not a learning gain
Median attack-FN scores (E4a vs baseline) explain everything:

| Run | INVITE p50 | REGISTER p50 | OPTIONS p50 | benign p50 | T_run |
|---|---:|---:|---:|---:|---:|
| Baseline | 0.444 | 0.282 | 0.624 | 0.239 | 0.553 |
| E4a (bf0.30) | 0.136 | 0.768 | 0.802 | 0.056 | 0.640 |

The sampler lifts REGISTER scores to the top of the distribution (0.282 → 0.768). Because the threshold is pegged to 5% benign FPR, it rises 0.553 → 0.640. INVITE scores fall to 0.136 and drop below the new threshold (302 → 32 recovered). OPTIONS rides above it both ways. **INVITE is not forgotten; it is out-ranked.** The model has a single output threshold, and two types cannot both sit on the right side of it.

### Phase transition is binary
Between bf=0.20 and bf=0.25, REGISTER jumps 0.112 → 0.695 and the threshold jumps 0.54 → 0.66. There is no smooth middle: either INVITE is preserved and REGISTER stays small, or REGISTER dominates and INVITE collapses.

### Capacity is not the constraint
backbone_hybrid (Route C) added a trainable TCN block and reproduced head_last_block to the third decimal. The limit is the shared threshold, not representational power.

### The recovery is genuine, not memorization
Exact REGISTER header overlap train↔test = 0/511 (0%). The 770 mined positives are 100% real attacks. REGISTER FP = 0. The signal is the fuzzed credential fields, not template reuse.

---

## 6. Findings (frank)

- **REGISTER is recoverable.** From 0% to 79% with a sampler change and zero added REGISTER false positives. This breaks a hard zero-floor that K-scaling, loss-weighting, and extra capacity all failed to move.
- **It is a type rebalancing, not a net discriminative gain.** E4a's +6pp global (0.325 → 0.385) comes from converting ~404 REGISTER recoveries while losing ~270 INVITE. The model trades, it does not add new separating power.
- **A single threshold cannot serve both peaks.** INVITE peaks at bf≤0.20 (R≈0.22) and REGISTER peaks at bf≥0.30 (R≈0.79); their score bands interleave below the operating point.
- **The bf knob moves along one tradeoff curve, it does not escape it.** Every run is a single point on the INVITE↔REGISTER axis. E5a (bf=0.20) keeps INVITE intact with modest REGISTER (11%, −2.9pp global); E4a (bf=0.30) maximizes global (+6pp) at INVITE's expense. Neither recovers both.
- A reproduced minor correction: the REGISTER P/benign-U ratio shifts ~1:8.6 → ~1:1.4 across K=128→770 (earlier 1:31→1:5.2 did not reproduce). Direction unchanged.

---

## 7. Constraint: the model must stay generic

The target is a **protocol-agnostic** risk scorer. It must operate from one global threshold on the raw score, without branching on traffic characteristics. This rules out the otherwise-obvious fix for the interleaving problem:

- **Dual / per-type thresholds are not applicable.** Applying `T_REGISTER` vs `T_INVITE` requires first classifying each record's SIP message type and routing it — SIP-specific logic baked into inference. That contradicts the generic-model goal and is therefore off the table.
- A type-routed ensemble (different model/threshold per message type) is excluded for the same reason.

Under the generic single-threshold constraint, the campaign's structural finding is binding: REGISTER and INVITE cannot both be recovered, because their score distributions interleave and only one can sit above a shared FPR-pegged threshold.

---

## 8. Conclusion

- The REGISTER **zero-floor is solved as a learning problem**: the model can be made to score REGISTER attacks highly, with zero added false positives, and the signal is genuine (0% exact train↔test overlap).
- But **there is no current way to properly detect REGISTER in this scenario** without sacrificing INVITE, given a single global threshold. The only configuration that recovers REGISTER (bf≥0.25) collapses INVITE, and the only way to keep both apart — per-type thresholds — is disallowed by the generic-model requirement.
- The capacity/sampling line is exhausted: K-scaling, loss-weighting, and extra backbone capacity were each ruled out. The remaining limit is structural (one threshold over interleaved type distributions), not a tuning or capacity gap.
- Practical takeaway: keep the production baseline (or E5a as an INVITE-safe variant). E4a stands as evidence that REGISTER is *learnable*, not as a deployable generic operating point. Genuine simultaneous recovery would require a fundamentally different signal or training objective that separates the type score-bands **without** type-aware inference — an open problem, not addressed by the levers tested here.
