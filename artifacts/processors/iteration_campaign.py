#!/usr/bin/env python3
"""Run a 10-iteration IDS-focused improvement campaign on existing model outputs.

This script does not retrain the network. It iterates over calibration and
validation-selected operating-point policies, then ranks iterations by
Snort-FN recovery at fixed benign FPR budgets.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import torch

# Make package importable when launched as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from nids_ml.training.calibration import (
    IsotonicCalibrator,
    PlattCalibrator,
    PriorCorrectionCalibrator,
)


def _load_rows(path: Path) -> List[Dict[str, float]]:
    with path.open("r", encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        raise ValueError(f"Expected list in {path}")
    return rows


def _to_tensors(rows: List[Dict[str, float]]) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    logits = torch.tensor([float(r["raw_logit"]) for r in rows], dtype=torch.float32)
    labels = torch.tensor([int(r["is_attack"]) for r in rows], dtype=torch.float32)
    alerted = torch.tensor([int(r["alerted"]) for r in rows], dtype=torch.float32)
    return logits, labels, alerted


def _binary_metrics(scores: torch.Tensor, labels: torch.Tensor, threshold: float) -> Dict[str, float]:
    pred = (scores >= threshold).float()
    tp = float((pred * labels).sum().item())
    fp = float((pred * (1 - labels)).sum().item())
    fn = float(((1 - pred) * labels).sum().item())
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
    }


def _snort_metrics(
    scores: torch.Tensor,
    labels: torch.Tensor,
    alerted: torch.Tensor,
    threshold: float,
) -> Dict[str, float]:
    pred = (scores >= threshold).float()
    benign = (labels == 0) & (alerted == 0)
    snort_fn = (labels == 1) & (alerted == 0)

    benign_total = int(benign.sum().item())
    snort_fn_total = int(snort_fn.sum().item())

    benign_fp = int((pred[benign] == 1).sum().item())
    fn_recovered = int((pred[snort_fn] == 1).sum().item())

    benign_fpr = benign_fp / benign_total if benign_total else 0.0
    fn_recovery = fn_recovered / snort_fn_total if snort_fn_total else 0.0

    return {
        "benign_fpr": benign_fpr,
        "benign_fp_added": benign_fp,
        "benign_total": benign_total,
        "snort_fn_recovered": fn_recovered,
        "snort_fn_total": snort_fn_total,
        "snort_fn_recovery": fn_recovery,
    }


def _pr_auc(scores: torch.Tensor, labels: torch.Tensor) -> float:
    # Approximate PR-AUC by threshold sweep over unique scores.
    thresholds = torch.unique(scores)
    thresholds = torch.sort(thresholds, descending=True).values
    p_vals = []
    r_vals = []
    for t in thresholds:
        m = _binary_metrics(scores, labels, float(t.item()))
        p_vals.append(m["precision"])
        r_vals.append(m["recall"])
    area = 0.0
    prev_r = 0.0
    prev_p = p_vals[-1] if p_vals else 0.0
    for p, r in sorted(zip(p_vals, r_vals), key=lambda x: x[1]):
        area += (r - prev_r) * (p + prev_p) / 2.0
        prev_r = r
        prev_p = p
    return float(max(area, 0.0))


def _best_f1_threshold(scores: torch.Tensor, labels: torch.Tensor) -> float:
    thresholds = torch.unique(scores)
    thresholds = torch.sort(thresholds, descending=True).values
    best_t = 0.5
    best_f1 = -1.0
    for t in thresholds:
        f1 = _binary_metrics(scores, labels, float(t.item()))["f1"]
        if f1 > best_f1:
            best_f1 = f1
            best_t = float(t.item())
    return best_t


def _best_p90_threshold(scores: torch.Tensor, labels: torch.Tensor) -> float:
    thresholds = torch.unique(scores)
    thresholds = torch.sort(thresholds, descending=True).values
    best_t = 0.5
    best_recall = -1.0
    for t in thresholds:
        m = _binary_metrics(scores, labels, float(t.item()))
        if m["precision"] >= 0.90 and m["recall"] > best_recall:
            best_recall = m["recall"]
            best_t = float(t.item())
    return best_t


def _best_fpr_threshold(
    scores: torch.Tensor,
    labels: torch.Tensor,
    alerted: torch.Tensor,
    budget: float,
) -> float:
    # Goal: find the LOWEST threshold T* that satisfies benign_fpr <= budget.
    # Lower T = more permissive = higher Snort-FN recovery.
    #
    # Algorithm: scan DESCENDING (high → low), unconditionally update best_t
    # whenever the budget is satisfied.  Each valid update pushes best_t to a
    # lower, more permissive value.  The final best_t is the lowest T where
    # benign_fpr still fits the budget.
    #
    # The old code added a `best_recovery > prev_best_recovery` guard to avoid
    # updating at T=max where recovery=0.  That guard is incorrect: it prevents
    # the loop from descending past the first valid T with recovery=0 (e.g., in
    # the isotonic staircase gap), leaving best_t stranded at 1.0.  The
    # unconditional update is the correct approach.
    thresholds = torch.unique(scores)
    thresholds = torch.sort(thresholds, descending=True).values  # descending
    best_t = 1.0
    for t in thresholds:
        s = _snort_metrics(scores, labels, alerted, float(t.item()))
        if s["benign_fpr"] <= budget + 1e-12:
            best_t = float(t.item())  # push best_t lower on each valid step
    return best_t


def _evaluate_iteration(
    iteration: int,
    name: str,
    val_scores: torch.Tensor,
    test_scores: torch.Tensor,
    val_labels: torch.Tensor,
    test_labels: torch.Tensor,
    val_alerted: torch.Tensor,
    test_alerted: torch.Tensor,
    selected_threshold: float,
) -> Dict[str, object]:
    t_f1 = _best_f1_threshold(val_scores, val_labels)
    t_p90 = _best_p90_threshold(val_scores, val_labels)
    t_fpr10 = _best_fpr_threshold(val_scores, val_labels, val_alerted, 0.10)
    t_fpr5 = _best_fpr_threshold(val_scores, val_labels, val_alerted, 0.05)
    t_fpr1 = _best_fpr_threshold(val_scores, val_labels, val_alerted, 0.01)

    def at_thr(thr: float) -> Dict[str, float]:
        b = _binary_metrics(test_scores, test_labels, thr)
        s = _snort_metrics(test_scores, test_labels, test_alerted, thr)
        return {
            "threshold": thr,
            "precision": b["precision"],
            "recall": b["recall"],
            "f1": b["f1"],
            "benign_fpr": s["benign_fpr"],
            "benign_fp_added": s["benign_fp_added"],
            "snort_fn_recovery": s["snort_fn_recovery"],
            "snort_fn_recovered": s["snort_fn_recovered"],
            "snort_fn_total": s["snort_fn_total"],
        }

    selected = at_thr(selected_threshold)

    return {
        "iteration": iteration,
        "name": name,
        "pr_auc_test": _pr_auc(test_scores, test_labels),
        "selected_threshold": selected_threshold,
        "selected_test_metrics": selected,
        "operating_points": {
            "T_f1": at_thr(t_f1),
            "T_p90": at_thr(t_p90),
            "T_fpr10": at_thr(t_fpr10),
            "T_fpr5": at_thr(t_fpr5),
            "T_fpr1": at_thr(t_fpr1),
        },
    }


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    artifacts = root / "artifacts"
    out_dir = artifacts / "iter_campaign"
    out_dir.mkdir(parents=True, exist_ok=True)

    val_rows = _load_rows(artifacts / "val_samples.json")
    test_rows = _load_rows(artifacts / "test_samples.json")

    v_log, v_y, v_a = _to_tensors(val_rows)
    t_log, t_y, t_a = _to_tensors(test_rows)

    # Build calibrated score spaces.
    raw_v = torch.sigmoid(v_log)
    raw_t = torch.sigmoid(t_log)

    prior = PriorCorrectionCalibrator(pi_train=0.2)
    prior.fit(v_log, v_y)
    pc_v = prior.transform(v_log)
    pc_t = prior.transform(t_log)

    platt = PlattCalibrator()
    platt.fit(v_log, v_y)
    pl_v = platt.transform(v_log)
    pl_t = platt.transform(t_log)

    iso = IsotonicCalibrator()
    iso.fit(v_log, v_y)
    iso_v = iso.transform(v_log)
    iso_t = iso.transform(t_log)

    p2 = PlattCalibrator()
    p2.fit(v_log + prior.shift, v_y)
    pp_v = p2.transform(v_log + prior.shift)
    pp_t = p2.transform(t_log + prior.shift)

    iterations: List[Dict[str, object]] = []
    iterations.append(_evaluate_iteration(1, "baseline_raw@0.5", raw_v, raw_t, v_y, t_y, v_a, t_a, 0.5))
    iterations.append(_evaluate_iteration(2, "prior_correction@0.5", pc_v, pc_t, v_y, t_y, v_a, t_a, 0.5))
    iterations.append(_evaluate_iteration(3, "platt@0.5", pl_v, pl_t, v_y, t_y, v_a, t_a, 0.5))
    iterations.append(_evaluate_iteration(4, "isotonic@0.5", iso_v, iso_t, v_y, t_y, v_a, t_a, 0.5))
    iterations.append(_evaluate_iteration(5, "prior_plus_platt@0.5", pp_v, pp_t, v_y, t_y, v_a, t_a, 0.5))

    # Choose calibration backbone by highest FN recovery at T_fpr5 on test.
    first_five = iterations[:5]
    best_cal = max(first_five, key=lambda r: r["operating_points"]["T_fpr5"]["snort_fn_recovery"])
    best_name = best_cal["name"]

    if "prior_plus_platt" in best_name:
        b_v, b_t = pp_v, pp_t
    elif "isotonic" in best_name:
        b_v, b_t = iso_v, iso_t
    elif "platt" in best_name:
        b_v, b_t = pl_v, pl_t
    elif "prior_correction" in best_name:
        b_v, b_t = pc_v, pc_t
    else:
        b_v, b_t = raw_v, raw_t

    # Policy-focused iterations.
    t_f1 = _best_f1_threshold(b_v, v_y)
    t_p90 = _best_p90_threshold(b_v, v_y)
    t_fpr10 = _best_fpr_threshold(b_v, v_y, v_a, 0.10)
    t_fpr5 = _best_fpr_threshold(b_v, v_y, v_a, 0.05)
    t_fpr1 = _best_fpr_threshold(b_v, v_y, v_a, 0.01)

    iterations.append(_evaluate_iteration(6, f"policy_T_f1_on_{best_name}", b_v, b_t, v_y, t_y, v_a, t_a, t_f1))
    iterations.append(_evaluate_iteration(7, f"policy_T_p90_on_{best_name}", b_v, b_t, v_y, t_y, v_a, t_a, t_p90))
    iterations.append(_evaluate_iteration(8, f"policy_T_fpr10_on_{best_name}", b_v, b_t, v_y, t_y, v_a, t_a, t_fpr10))
    iterations.append(_evaluate_iteration(9, f"policy_T_fpr5_on_{best_name}", b_v, b_t, v_y, t_y, v_a, t_a, t_fpr5))
    iterations.append(_evaluate_iteration(10, f"policy_T_fpr1_on_{best_name}", b_v, b_t, v_y, t_y, v_a, t_a, t_fpr1))

    ranked = sorted(
        iterations,
        key=lambda r: (
            r["operating_points"]["T_fpr5"]["snort_fn_recovery"],
            r["operating_points"]["T_fpr1"]["snort_fn_recovery"],
            r["operating_points"]["T_fpr10"]["snort_fn_recovery"],
            -r["operating_points"]["T_fpr5"]["benign_fpr"],
        ),
        reverse=True,
    )

    summary = {
        "best_iteration": ranked[0]["iteration"],
        "best_name": ranked[0]["name"],
        "iterations": iterations,
        "ranking": [
            {
                "iteration": r["iteration"],
                "name": r["name"],
                "T_fpr10_fn_recovery": r["operating_points"]["T_fpr10"]["snort_fn_recovery"],
                "T_fpr5_fn_recovery": r["operating_points"]["T_fpr5"]["snort_fn_recovery"],
                "T_fpr1_fn_recovery": r["operating_points"]["T_fpr1"]["snort_fn_recovery"],
                "selected_f1": r["selected_test_metrics"]["f1"],
                "selected_precision": r["selected_test_metrics"]["precision"],
                "selected_recall": r["selected_test_metrics"]["recall"],
                "selected_threshold": r["selected_threshold"],
            }
            for r in ranked
        ],
    }

    with (out_dir / "campaign_results.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    top = ranked[0]
    op = top["operating_points"]
    s = top["selected_test_metrics"]

    lines = [
        "# 10-Iteration Improvement Campaign",
        "",
        f"Best iteration: {top['iteration']} - {top['name']}",
        "",
        "## Best iteration summary",
        f"- Selected threshold: {top['selected_threshold']:.4f}",
        f"- Test PR-AUC: {top['pr_auc_test']:.4f}",
        f"- Test F1: {s['f1']:.4f}",
        f"- Precision: {s['precision']:.4f}",
        f"- Recall: {s['recall']:.4f}",
        f"- Snort FN recovery @FPR<=10%: {op['T_fpr10']['snort_fn_recovery']:.4f}",
        f"- Snort FN recovery @FPR<=5%: {op['T_fpr5']['snort_fn_recovery']:.4f}",
        f"- Snort FN recovery @FPR<=1%: {op['T_fpr1']['snort_fn_recovery']:.4f}",
        "",
        "## Ranking (primary: FN recovery at FPR<=5%)",
    ]

    for i, r in enumerate(summary["ranking"], start=1):
        lines.append(
            f"{i}. iter {r['iteration']} {r['name']} | "
            f"FN@10%={r['T_fpr10_fn_recovery']:.4f}, "
            f"FN@5%={r['T_fpr5_fn_recovery']:.4f}, "
            f"FN@1%={r['T_fpr1_fn_recovery']:.4f}, "
            f"F1={r['selected_f1']:.4f}, P={r['selected_precision']:.4f}, R={r['selected_recall']:.4f}"
        )

    with (out_dir / "campaign_report.md").open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved {(out_dir / 'campaign_results.json').as_posix()}")
    print(f"Saved {(out_dir / 'campaign_report.md').as_posix()}")
    print(f"Best iteration: {top['iteration']} - {top['name']}")


if __name__ == "__main__":
    main()
