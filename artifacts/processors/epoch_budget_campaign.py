#!/usr/bin/env python3
"""Per-epoch x FPR-budget metric matrix for Stage-2 trainability runs.

Given a run directory containing ``config_used.json`` and one or more
``model_ep{e}.pt`` checkpoints (saved by ``TwoWayTrainer.train_pu`` when
``save_epoch_checkpoints=true``), this script regenerates raw val/test risk
logits for every requested epoch and computes the calibrator-invariant
Snort-FN recovery (R) at fixed benign-FPR budgets, plus PR-AUC and
calibration diagnostics.

No training happens here -- purely inference + threshold selection.

Usage
-----
    python -m nids_ml.artifacts.processors.epoch_budget_campaign \
        --run-dir artifacts/experiments/my_run \
        --epochs 0,2,4,6 \
        --budgets 0.01,0.05,0.10 \
        --out artifacts/experiments/my_run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import torch

# Make the nids_ml package importable when launched as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from nids_ml.data import TwoWayDatasetBuilder
from nids_ml.data.common import to_device
from nids_ml.models import build_model
from nids_ml.training.calibration import IsotonicCalibrator

# Reuse the score-space metric helpers; never duplicate them.
try:
    from nids_ml.artifacts.processors.iteration_campaign import (
        _best_fpr_threshold,
        _binary_metrics,
        _pr_auc,
        _snort_metrics,
    )
except ModuleNotFoundError:  # pragma: no cover - namespace-package fallback
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from iteration_campaign import (  # type: ignore
        _best_fpr_threshold,
        _binary_metrics,
        _pr_auc,
        _snort_metrics,
    )


# ─── small utilities ─────────────────────────────────


def _resolve_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _load_config(run_dir: Path) -> Dict[str, Any]:
    cfg_path = run_dir / "config_used.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"config_used.json not found in {run_dir}")
    with cfg_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _discover_epochs(run_dir: Path) -> List[int]:
    epochs: List[int] = []
    for p in run_dir.glob("model_ep*.pt"):
        try:
            epochs.append(int(p.stem.replace("model_ep", "")))
        except ValueError:
            continue
    return sorted(epochs)


def _brier(probs: torch.Tensor, labels: torch.Tensor) -> float:
    return float(((probs - labels.float()) ** 2).mean().item())


def _logloss(probs: torch.Tensor, labels: torch.Tensor) -> float:
    p = probs.clamp(1e-7, 1.0 - 1e-7)
    y = labels.float()
    return float(-(y * p.log() + (1.0 - y) * (1.0 - p).log()).mean().item())


@torch.no_grad()
def _collect(
    model: Any, loader: Any, device: torch.device,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Forward a loader; return (raw_logits, is_attack, alerted) on CPU."""
    model.backbone.eval()
    model.heads.eval()
    logits: List[torch.Tensor] = []
    labels: List[torch.Tensor] = []
    alerted: List[torch.Tensor] = []
    for batch in loader:
        batch = to_device(batch, device)
        z = model.backbone(batch)
        out = model.heads(z)
        logits.append(out["risk_logit"].cpu())
        labels.append(batch["is_attack"].cpu())
        if "alerted" in batch:
            alerted.append(batch["alerted"].cpu())
    log_t = torch.cat(logits)
    lab_t = torch.cat(labels)
    ale_t = torch.cat(alerted) if alerted else torch.zeros_like(lab_t)
    return log_t, lab_t, ale_t


# ─── per-epoch evaluation ────────────────────────────


def _evaluate_epoch(
    epoch: int,
    model: Any,
    loaders: Dict[str, Any],
    device: torch.device,
    budgets: List[float],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    val_logits, val_labels, val_alerted = _collect(model, loaders["val"], device)
    test_logits, test_labels, test_alerted = _collect(model, loaders["test"], device)

    # Calibrator-invariant score space: raw sigmoid for BOTH splits so the
    # val-selected threshold transfers directly to test.
    raw_val = torch.sigmoid(val_logits)
    raw_test = torch.sigmoid(test_logits)

    test_pr_auc = _pr_auc(raw_test, test_labels)
    val_pr_auc = _pr_auc(raw_val, val_labels)

    # Calibration diagnostics (context only; never used for R selection).
    iso = IsotonicCalibrator()
    iso.fit(val_logits, val_labels)
    cal_test = iso.transform(test_logits)
    brier = _brier(cal_test, test_labels)
    logloss = _logloss(cal_test, test_labels)
    f1_cal = _binary_metrics(cal_test, test_labels, 0.5)["f1"]

    rows: List[Dict[str, Any]] = []
    for b in budgets:
        # Val-quantile threshold at the FPR budget, applied to test.
        t = _best_fpr_threshold(raw_val, val_labels, val_alerted, b)
        s = _snort_metrics(raw_test, test_labels, test_alerted, t)
        bm = _binary_metrics(raw_test, test_labels, t)
        rows.append({
            "epoch": epoch,
            "budget": b,
            "R": s["snort_fn_recovery"],
            "snort_fn_recovered": s["snort_fn_recovered"],
            "snort_fn_total": s["snort_fn_total"],
            "benign_fp_added": s["benign_fp_added"],
            "benign_fpr": s["benign_fpr"],
            "precision": bm["precision"],
            "recall": bm["recall"],
            "f1": bm["f1"],
            "test_pr_auc": test_pr_auc,
            "val_pr_auc": val_pr_auc,
            "brier": brier,
            "logloss": logloss,
        })

    summary = {
        "epoch": epoch,
        "test_pr_auc": test_pr_auc,
        "val_pr_auc": val_pr_auc,
        "brier": brier,
        "logloss": logloss,
        "f1_calibrated_0.5": f1_cal,
    }
    return rows, summary


# ─── markdown rendering ──────────────────────────────


def _render_markdown(
    rows: List[Dict[str, Any]],
    summaries: List[Dict[str, Any]],
    budgets: List[float],
    epochs: List[int],
) -> str:
    cell = {(r["epoch"], r["budget"]): r for r in rows}
    pr_by_epoch = {s["epoch"]: s["test_pr_auc"] for s in summaries}

    lines = [
        "# Epoch x Budget Matrix",
        "",
        "Each cell = R (Snort-FN recovery) / benign FP added, at a "
        "val-selected FPR budget applied to test.",
        "",
        "| epoch | " + " | ".join(f"FPR<={b:.0%}" for b in budgets)
        + " | test PR-AUC |",
        "|" + "---|" * (len(budgets) + 2),
    ]
    for e in epochs:
        cells: List[str] = []
        for b in budgets:
            r = cell.get((e, b))
            cells.append("-" if r is None else f"{r['R']:.4f} / {r['benign_fp_added']}")
        pr = pr_by_epoch.get(e)
        pr_str = "-" if pr is None else f"{pr:.4f}"
        lines.append(f"| {e} | " + " | ".join(cells) + f" | {pr_str} |")

    return "\n".join(lines) + "\n"


# ─── driver ──────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Per-epoch x FPR-budget Snort-FN recovery matrix.",
    )
    parser.add_argument(
        "--run-dir", required=True,
        help="Run directory with config_used.json + model_ep*.pt checkpoints.",
    )
    parser.add_argument(
        "--epochs", default=None,
        help="Comma-separated epoch indices (default: all model_ep*.pt found).",
    )
    parser.add_argument(
        "--budgets", default="0.01,0.05,0.10",
        help="Comma-separated benign-FPR budgets (default 0.01,0.05,0.10).",
    )
    parser.add_argument(
        "--out", default=None,
        help="Output directory for the matrix files (default: run-dir).",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    out_dir = Path(args.out).resolve() if args.out else run_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    config = _load_config(run_dir)
    # Inference-only driver: force single-process loading to avoid the known
    # macOS DataLoader worker stall (see repo memory).
    config.setdefault("training", {})["num_workers"] = 0

    budgets = [float(x) for x in args.budgets.split(",") if x.strip()]
    if args.epochs:
        epochs = [int(x) for x in args.epochs.split(",") if x.strip()]
    else:
        epochs = _discover_epochs(run_dir)
    if not epochs:
        raise FileNotFoundError(f"No model_ep*.pt checkpoints found in {run_dir}")

    device = _resolve_device()
    print(f"Device: {device} | epochs: {epochs} | budgets: {budgets}")

    # The config's data paths (e.g. ../sip-dataset/...) are relative to the
    # nids_ml package dir -- the cwd training is launched from. This driver may
    # run as a module from the workspace root, so chdir to the package root so
    # those relative paths resolve identically to training. run_dir/out_dir were
    # already resolved to absolute paths above, so outputs are unaffected.
    os.chdir(Path(__file__).resolve().parents[2])

    # Build loaders ONCE and reuse across epochs.
    builder = TwoWayDatasetBuilder(config)
    loaders = builder.build_loaders()

    model = build_model(config)
    model.to(device)

    all_rows: List[Dict[str, Any]] = []
    summaries: List[Dict[str, Any]] = []
    used_epochs: List[int] = []

    for e in epochs:
        ckpt_path = run_dir / f"model_ep{e}.pt"
        if not ckpt_path.exists():
            print(f"[skip] {ckpt_path.name} not found")
            continue
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=True)
        model.backbone.load_state_dict(ckpt["backbone"])
        model.heads.load_state_dict(ckpt["heads"])

        rows, summary = _evaluate_epoch(e, model, loaders, device, budgets)
        all_rows.extend(rows)
        summaries.append(summary)
        used_epochs.append(e)
        r_str = ", ".join(
            f"R@{r['budget']:.0%}={r['R']:.4f}(fp+{r['benign_fp_added']})"
            for r in rows
        )
        print(f"[epoch {e}] test_pr_auc={summary['test_pr_auc']:.4f} | {r_str}")

    if not all_rows:
        raise RuntimeError("No epoch checkpoints were evaluated.")

    matrix_path = out_dir / "epoch_budget_matrix.json"
    with matrix_path.open("w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=2)

    md_path = out_dir / "epoch_budget_matrix.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(_render_markdown(all_rows, summaries, budgets, used_epochs))

    print(f"Saved {matrix_path.as_posix()}")
    print(f"Saved {md_path.as_posix()}")


if __name__ == "__main__":
    main()
