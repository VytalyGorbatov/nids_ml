# Snort False-Negative Recovery — Root-Cause Analysis & Implementation Plan

**Model:** ByteTCN2Way, `head_last_block` production checkpoint (Stage-2 epoch 3)
**Objective:** Recover Snort false negatives (`is_attack=1 AND alerted=0`) at benign FPR ≤ 5%
**Current result:** R@5% = 0.324 (692 / 2135 Snort FN recovered)
**Date:** 2026-06-27

---

## 1. Executive Summary

The model's missed Snort false negatives are **not random** and **not a byte-level feature limitation**. They are governed almost entirely by **SIP message type**:

| SIP message type | Snort FN | Recovered | Recovery rate |
|---|---:|---:|---:|
| `OPTIONS` (request) | 480 | 381 | **79.4 %** |
| `INVITE` (request) | 875 | 302 | **34.5 %** |
| `REGISTER` (request) | 511 | 0 | **0.0 %** |
| SIP responses (`100`, `503`, …) | 269 | ~9 | **~3 %** |

**Root cause:** the weak-supervision teacher (Snort, `alerted=1`) fires on **only two** message types — `INVITE` (280) and `OPTIONS` (202). The nnPU model therefore learns attack signatures for those two types only. `REGISTER` attacks and SIP-response attacks — **780 samples, 36.5 % of all Snort FN** — are never positively labelled, so the model scores them like benign traffic of the same type.

**This is recoverable.** The attack signal is present and byte-distinguishable *within* the uncovered types (fuzzed/gibberish header field values), but the supervision to learn it is missing. The fix is a **label-free, message-type-stratified pseudo-positive mining** step that extends teacher coverage — no architecture change required.

**Projected outcome:** R@5% ≈ **0.45–0.51** (central estimate **+16 pp**), recovering an additional ~350–400 Snort FN at the same FPR budget.

---

## 2. Background

The neural layer is an *additive* risk score on top of Snort. It is trained with PU (positive–unlabeled) learning:

- `alerted=1` → reliable positive (Snort teacher signal)
- `alerted=0` → **unlabeled** (NOT benign)
- `is_attack` → ground truth, used for evaluation only

The primary metric is **Snort-FN recovery at a controlled benign FPR budget** (R@1/5/10 %), computed as a validation-selected threshold applied to test in raw-sigmoid space (calibrator-invariant).

The `head_last_block` Stage-2 recipe (validated in the trainability campaign) is the current best: R@5% = 0.324, test PR-AUC = 0.718.

---

## 3. The Investigation (how we found it)

The root cause was reached in three escalating steps. Each step corrected the previous interpretation — the audit trail matters for the dissertation.

### Step 1 — Score-band split (aggregate)
Splitting the 2135 Snort FN at the FPR≤5% threshold (0.553):

| Band | Count | % of FN |
|---|---:|---:|
| Recovered (score ≥ 0.553) | 692 | 32.4 % |
| Near (0.40–0.553) | 425 | 19.9 % |
| Mid (0.30–0.40) | 313 | 14.7 % |
| Hard (< 0.30) | 705 | 33.0 % |

A third of all FN score **below the benign mean** (0.266). A subset of body-carrying missed attacks scored **0.187** — *lower* than benign. This first suggested a "body-suppression" hypothesis.

### Step 2 — Byte-level decode (corrects Step 1)
Decoding the actual SIP bytes of the lowest-scoring body-carrying attacks revealed they were **`SIP/2.0 100 Trying` responses** carrying SDP fragments — not a body problem at all. The "body-suppression" signal was a **symptom of message type**, not a cause.

### Step 3 — Message-type cross-tabulation (root cause)
Parsing the SIP request-line / status-line of every sample produced the definitive table in §1 and the teacher distribution in §4. Recovery tracks message type with near-perfect determinism: types in the teacher set are recovered; types absent from it are not.

> **Lesson:** aggregate score statistics (Step 1) can manufacture a plausible but wrong mechanism. Byte-level evidence (Steps 2–3) was required to find the true cause.

---

## 4. Root Cause — Teacher Message-Type Coverage Gap

### 4.1 The teacher only covers two message types

Snort alerts (`alerted=1`, the entire PU positive set, n=482 in test):

| Type | Count | Share of teacher |
|---|---:|---:|
| `INVITE` | 280 | 58.1 % |
| `OPTIONS` | 202 | 41.9 % |
| `REGISTER` | 0 | 0 % |
| responses | 0 | 0 % |

The model can only learn attack signatures for message types that appear in the positive set. With **zero** positive `REGISTER` or response examples, the nnPU objective has no gradient that says "this fuzzed REGISTER is an attack." It defaults to scoring them like the benign `REGISTER`/responses that dominate the unlabeled set.

### 4.2 Coverage determines recovery

| Coverage class | Types | FN total | Recovered | Rate |
|---|---|---:|---:|---:|
| **Covered** by teacher | INVITE + OPTIONS | 1355 | 683 | **50.4 %** |
| **Uncovered** by teacher | REGISTER + responses | 780 | ~9 | **1.2 %** |

The 49-point recovery gap between covered and uncovered types **is** the failure mode. The uncovered 780 FN are 36.5 % of all Snort FN and account for essentially the entire shortfall below a ~50 % ceiling.

### 4.3 Message-type context (full distributions)

All attack messages (n=2617): INVITE 44.1 %, OPTIONS 26.1 %, REGISTER 19.5 %, responses 10.3 %.

Benign messages (n=4416): responses 38.4 %, BYE 18.5 %, INVITE 16.6 %, ACK 13.0 %, REGISTER 3.8 %, OPTIONS 2.9 %, SUBSCRIBE 2.8 %, CANCEL 2.4 %, REFER 1.5 %.

Because benign traffic contains `REGISTER` (170) and responses (1695), the model must perform **within-type discrimination** (attack-REGISTER vs benign-REGISTER), not merely "REGISTER ⇒ attack."

---

## 5. Evidence — The Signal Exists and Is Distinguishable

The uncovered attacks are recoverable because they carry a clear, byte-level attack signature that benign messages of the same type never have.

**Attack `REGISTER` (missed, score < 0.2):**
```
REGISTER sip:172.18.0.2 SIP/2.0
Via: SIP/2.0/UDP 172.18.0.4:9081;branch=z9hG4bK-729959-1-1
From: "1039" <sip:1039@172.18.0.2>;tag=729959SIPpTag
To:   "1039" <sip:1039@172.18.0.2>            ← self-registration
CSeq: 1 REGISTER                               ← CSeq=1 (no session)
Content-Length: 0                              ← no Contact header
Authorization: lkyomwxpzyyolto lky            ← GIBBERISH (fuzzed)
Accept: text/brulgeb                           ← GIBBERISH (fuzzed)
```

**Benign `REGISTER` (for comparison):**
```
REGISTER sip:2016 SIP/2.0
Via: SIP/2.0/UDP 172.18.0.4:9075;branch=z9hG4bK-336455-1-0
From: "PiperJames" <sip:2016@172.18.0.4:9075>;tag=336455SIPpTag
To:   "KaraMorgan" <sip:1063@172.18.0.2:5060>
CSeq: 7 REGISTER                               ← established session
Contact: <sip:2016@172.18.0.4:9075>            ← Contact present
```

The discriminator is **high-entropy / non-dictionary fuzzed values in header fields** (Authorization, Accept, User-Agent, …), plus low-weight structural flags (bare-IP registrar, missing Contact, CSeq=1).

> **Note on the `,,,`/`;;` "malformed-Via" artifact:** it appears in only **8.7 %** of attack INVITE and **0 %** of all other types. It is *not* the general signature — it is one fuzzing variant of one message type. The general signature is fuzzed field **values**, present across all attack types.

---

## 6. Recoverability & Ceiling

- **Genuinely recoverable (covered types, more headroom):** INVITE at 34.5 % is well below OPTIONS at 79.4 %, suggesting the INVITE FN still has recoverable mass with better training, but it is already in-distribution.
- **Recoverable via coverage extension (uncovered types):** REGISTER (511) + responses (269). If brought to the covered-type average (~50 %), this adds **~390 recovered FN**.
- **Irreducible floor:** a small set of header-only messages whose bytes are genuinely indistinguishable from benign of the same type (no fuzzed fields visible within 1024 bytes). Estimated < 5 % of FN.

| Scenario | R@5% | Δ |
|---|---:|---:|
| Current production | 0.324 | — |
| REGISTER coverage restored | ~0.42–0.44 | +10–12 pp |
| REGISTER + responses restored | **~0.45–0.51** | **+13–18 pp** |
| Byte-only single-packet hard ceiling | ~0.52 | — |

---

## 7. Implementation Plan

A **pure data-side fix** that reuses the proven `pseudo_positive_manifest` path (the same mechanism that recovered the `stream_ip` blind spot from 0 % → 73 %). No model architecture change. Fully reversible (two config keys).

### Phase 0 — Index-alignment refactor (prerequisite)
**Why:** pseudo-positive manifests index into the unlabeled training list `[r for r in train if alerted==0]`, built inside `build_loaders`. A miner must produce the *same* indices, or promotion is silently misaligned.

- **Add** `TwoWayDatasetBuilder.split_train_pu()` (public) as the single source of truth for the P/U split; `build_loaders()` calls it. Behaviour-preserving refactor.
- **Smoke assert:** miner and loader produce identical U-index ordering.
- **File:** [nids_ml/data/twoway.py](nids_ml/data/twoway.py)

### Phase 1 — Label-free fuzzed-field detector
**New module:** `nids_ml/data/sip_struct.py` (pure Python, no torch, **no `is_attack` access**).

- `header_text_from_record(rec)` → `decode_buffers_field` + `split_header_body(1024, 30, 512)`.
- `parse_sip_header(text)` → `ParsedSip(method, request_uri, fields, first_line)`.
- `gibberish(s) → [0,1]`: fixed-weight combination of Shannon entropy, English char-bigram negative-log-likelihood, vowel-ratio deviation, max consonant run, and `1 − dictionary_hit`. **Static linguistic assets only** — never fit to the dataset or to `is_attack`.
- `field_fuzz` — **typed**:
  - Credential fields (Authorization, Proxy-Authorization): score **grammar violation** (missing `Digest`/`Basic` scheme or `key=value` structure) — NOT raw entropy, because benign nonces are legitimately high-entropy hex.
  - NLP fields (Accept, User-Agent, Subject): `gibberish()` on the subtype/product token.
  - Structural flags (low weight): bare-IP request-URI, missing Contact, CSeq=1. `self_registration` ≈ **zero weight** (benign REGISTER is also self-registration).
- `fuzz_score = 0.80·field_fuzz + 0.20·flags`.
- **Unit test** on the literal evidence strings in §5.

### Phase 2 — Stratified pseudo-positive miner
**New script:** `nids_ml/artifacts/processors/mine_fuzzed_pseudo_positives.py`.

- Stratify the unlabeled training set by parsed message type; mine **only** REGISTER + responses (INVITE/OPTIONS already covered).
- Per-type threshold `τ_m` = **q99.5 of the fuzz-score on the benign corpus** for that type (a within-type, label-free floor).
- Selection: `keep = min(K_m, |{score ≥ τ_m}|)`. Start conservative, then ablate:
  - `K_REGISTER ∈ {64, 128, 256}` (start 128)
  - `K_RESP ∈ {96, 150}` (start 96)
- **Manifest:** reuse the `stream_ip` JSON schema (only `u_indices` required). Add an `audit` block (`precision_is_attack`, `first_benign_rank`) where `is_attack` is used **for measurement only, never for selection**.
- **Acceptance gate on the manifest:** promoted-set precision ≥ **0.95** against `is_attack` (audit-only). If below, raise `τ_m` / lower `K_m`.
- **Wire-up:** `training.pseudo_positive_manifest` + `pseudo_positive_max_promoted` (existing keys). One manifest only — union `u_indices` if combining with the stream_ip manifest.

### Phase 3 — Per-message-type evaluation
**Edit:** [nids_ml/artifacts/processors/epoch_budget_campaign.py](nids_ml/artifacts/processors/epoch_budget_campaign.py).

- Keep the **global** val-selected FPR threshold (honest, deployable). Measure per-type R at that **same global threshold** — never per-type thresholds.
- `_collect` returns parsed message types (from `batch["header_ids"]`, already present — no schema change).
- `_evaluate_epoch` adds a `per_method` block via the existing `_snort_metrics` on type-masked test tensors.
- Emit `per_method` JSON + a second markdown table (type × R@1/5/10 + benign FP per type).

### Phase 4 — Controlled retraining sequence
All runs use the `head_last_block_production` config (constant LR, ep≤7, patience 2, per-epoch checkpoints). **pi_p stays 0.25** (ranking-invariant here; relabelling does not move the population prior). Manifest is the **only** variable.

| Run | Manifest | Isolates |
|---|---|---|
| **E0** baseline | none | reproduces 0.324 |
| **E1** REGISTER-only | REGISTER top-K | REGISTER coverage effect |
| **E2** REGISTER + responses | both strata | full coverage effect |
| **E3** K-sweep | {64,128,256}×{96,150} | promotion-budget sensitivity |

Evaluate per-epoch at {0,2,3,4,6}; select the operating epoch by **validation** R@5%.

### Phase 5 — Validation & acceptance
- **Per-type benign FP caps** at the global threshold: REGISTER ≤ 5, responses ≤ 34 (≈ proportional to their benign mass within the 5 % budget).
- **Global regression rule:** reject any manifest that drops global R@5% below 0.324 by more than 1 pp.
- **Mandatory leakage check** (data-analyst): REGISTER template overlap across train/val/test. `sip-dataset` has known high cross-split template overlap — dedup by header-template hash and audit before trusting the REGISTER recovery number.

---

## 8. Risks & Mitigations

| Risk | Mechanism | Mitigation |
|---|---|---|
| **P-set poisoning** | A benign REGISTER promoted as positive teaches the model wrong | q99.5 within-type τ floor + ≥0.95 audit-precision gate on the manifest |
| **FPR-budget blowout** | Promoted positives push benign of that type above threshold | Per-type benign-FP caps in Phase 3; ablate K downward if exceeded |
| **Heuristic overfit** | Model memorises the detector instead of generalising | Detector is **never** a model input feature; verify recovery on detector-blind held-out attacks |
| **Template leakage** | Cross-split duplicate REGISTER templates inflate recovery | Dedup by template hash + cross-split overlap audit (gates acceptance) |
| **Index drift** | Miner indices ≠ loader indices | `split_train_pu()` single source of truth + smoke assertion (Phase 0) |

---

## 9. Expected Outcome

- **E1 (REGISTER-only):** +10–12 pp global R@5%.
- **E2 (full mining):** central **R@5% ≈ 0.49 (+16 pp)**, plausible range **0.45–0.51**.
- Per-type targets: REGISTER 0 % → ~40–55 %; responses ~1 % → ~30–45 %.
- The dissertation claim is gated on the **template-leakage audit**, not on the recovery number alone.

---

## 10. Appendix — Reproduction

**Validated statistics source:** `head_last_block_production/{val,test}_samples.json` + raw dataset `sip-dataset/{attack,benign}/test.json` (field `pkt_gen_mapping = {raw:0, stream_ip:1}`; samples ordered benign-first [0:4416], attack-after [4416:]).

**Message type parsed from** `decode_buffers_field(rec['buffers'])` → `split_header_body(ids, 1024, 30, 512)` → first line (`SIP/2.0 …` ⇒ response; else first token ⇒ request method).

**Per-epoch recovery driver:**
```bash
cd /Users/vhorbato/Desktop/NeuralNetworks
python -m nids_ml.artifacts.processors.epoch_budget_campaign \
  --run-dir nids_ml/artifacts/runs/phase3_trainability/<RUN> \
  --budgets 0.01,0.05,0.10
```

**Key validated numbers:** 2135 Snort FN; teacher = 280 INVITE + 202 OPTIONS (zero REGISTER/response); covered-type recovery 50.4 % vs uncovered 1.2 %; current global R@5% = 0.324 (692 recovered).
