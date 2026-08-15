#!/usr/bin/env python3
"""Per-epoch x FPR-budget metric matrix for Stage-2 trainability runs.

Given a run directory containing ``config_used.json`` and one or more
``model_ep{e}.pt`` checkpoints (saved by ``TwoWayTrainer.train_pu`` when
``save_epoch_checkpoints=true``), this script regenerates raw val/test risk
logits for every requested epoch and computes the calibrator-invariant
Snort-FN recovery (R) at fixed benign-FPR budgets, plus AP and calibration
diagnostics.

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
from nids_ml.training.metrics import average_precision

# Reuse the score-space metric helpers; never duplicate them.
try:
    from nids_ml.artifacts.processors.iteration_campaign import (
        _best_fpr_threshold,
        _binary_metrics,
        _snort_metrics,
    )
except ModuleNotFoundError:  # pragma: no cover - namespace-package fallback
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from iteration_campaign import (  # type: ignore
        _best_fpr_threshold,
        _binary_metrics,
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

    test_average_precision = average_precision(raw_test, test_labels)
    val_average_precision = average_precision(raw_val, val_labels)

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
            "test_average_precision": test_average_precision,
            "val_average_precision": val_average_precision,
            "test_pr_auc": test_average_precision,
            "val_pr_auc": val_average_precision,
            "brier": brier,
            "logloss": logloss,
        })

    summary = {
        "epoch": epoch,
        "test_average_precision": test_average_precision,
        "val_average_precision": val_average_precision,
        "test_pr_auc": test_average_precision,
        "val_pr_auc": val_average_precision,
        "brier": brier,
        "logloss": logloss,
        "f1_calibrated_0.5": f1_cal,
    }
    return rows, summary


def _select_validation_epoch(summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Select one checkpoint using validation AP only; lower epoch breaks ties."""
    if not summaries:
        raise ValueError("At least one epoch summary is required for selection")
    return max(
        summaries,
        key=lambda summary: (
            summary["val_average_precision"], -int(summary["epoch"]),
        ),
    )


def _test_oracle_diagnostics(
    rows: List[Dict[str, Any]], budgets: List[float],
) -> List[Dict[str, Any]]:
    """Return test-best epoch rows as explicitly non-operational diagnostics."""
    diagnostics: List[Dict[str, Any]] = []
    for budget in budgets:
        candidates = [row for row in rows if row["budget"] == budget]
        best = max(
            candidates,
            key=lambda row: (row["R"], -row["benign_fpr"], -row["epoch"]),
        )
        diagnostics.append({
            "budget": budget,
            "diagnostic_only": True,
            "warning": "Test-selected epoch; not a reportable operating point.",
            "test_best_epoch": best["epoch"],
            "test_metrics": best,
        })
    return diagnostics


# ─── markdown rendering ─────────────────────────────


def _render_markdown(
    rows: List[Dict[str, Any]],
    summaries: List[Dict[str, Any]],
    budgets: List[float],
    epochs: List[int],
    selected: Dict[str, Any],
    selected_rows: List[Dict[str, Any]],
    oracle_diagnostics: List[Dict[str, Any]],
) -> str:
    cell = {(r["epoch"], r["budget"]): r for r in rows}
    ap_by_epoch = {s["epoch"]: s["test_average_precision"] for s in summaries}

    lines = [
        "# Epoch x Budget Matrix",
        "",
        "Each cell = R (Snort-FN recovery) / benign FP added, at a "
        "val-selected FPR budget applied to test.",
        "",
        "## Reportable Validation Selection",
        "",
        f"Checkpoint policy: maximum validation AP. Selected epoch: "
        f"{selected['epoch']} (validation AP={selected['val_average_precision']:.4f}).",
        "The following test values use that single validation-selected checkpoint.",
        "",
        "| nominal FPR budget | Snort-FN recovery | added benign FP | observed test FPR |",
        "|---|---:|---:|---:|",
    ]
    for row in selected_rows:
        lines.append(
            f"| {row['budget']:.0%} | {row['R']:.4f} | "
            f"{row['benign_fp_added']} | {row['benign_fpr']:.4%} |"
        )
    lines.extend([
        "",
        "## All Epochs (Diagnostic)",
        "",
        "Do not choose an epoch from this table using test results.",
        "",
        "| epoch | " + " | ".join(f"FPR<={b:.0%}" for b in budgets)
        + " | test AP |",
        "|" + "---|" * (len(budgets) + 2),
    ])
    for e in epochs:
        cells: List[str] = []
        for b in budgets:
            r = cell.get((e, b))
            cells.append("-" if r is None else f"{r['R']:.4f} / {r['benign_fp_added']}")
        ap = ap_by_epoch.get(e)
        ap_str = "-" if ap is None else f"{ap:.4f}"
        lines.append(f"| {e} | " + " | ".join(cells) + f" | {ap_str} |")

    lines.extend([
        "",
        "## Test-Oracle Diagnostics (Not Reportable)",
        "",
        "These entries retrospectively choose an epoch on test data and are "
        "diagnostics only, never article results or operational settings.",
        "",
        "| nominal FPR budget | test-selected epoch | recovery | observed test FPR |",
        "|---|---:|---:|---:|",
    ])
    for diagnostic in oracle_diagnostics:
        row = diagnostic["test_metrics"]
        lines.append(
            f"| {diagnostic['budget']:.0%} | {diagnostic['test_best_epoch']} | "
            f"{row['R']:.4f} | {row['benign_fpr']:.4%} |"
        )

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
        print(
            f"[epoch {e}] test_average_precision="
            f"{summary['test_average_precision']:.4f} | {r_str}"
        )

    if not all_rows:
        raise RuntimeError("No epoch checkpoints were evaluated.")

    selected_summary = _select_validation_epoch(summaries)
    selected_epoch = selected_summary["epoch"]
    selected_rows = [
        row for row in all_rows if row["epoch"] == selected_epoch
    ]
    oracle_diagnostics = _test_oracle_diagnostics(all_rows, budgets)

    matrix_path = out_dir / "epoch_budget_matrix.json"
    with matrix_path.open("w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=2)

    md_path = out_dir / "epoch_budget_matrix.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(_render_markdown(
            all_rows, summaries, budgets, used_epochs, selected_summary,
            selected_rows, oracle_diagnostics,
        ))

    selection_path = out_dir / "validation_selected_results.json"
    with selection_path.open("w", encoding="utf-8") as f:
        json.dump({
            "selection_policy": "maximum validation Average Precision; lower epoch breaks ties",
            "selected_epoch": selected_epoch,
            "selected_validation_metrics": selected_summary,
            "test_metrics_at_validation_selected_epoch": selected_rows,
            "oracle_diagnostics": oracle_diagnostics,
        }, f, indent=2)

    print(f"Saved {matrix_path.as_posix()}")
    print(f"Saved {md_path.as_posix()}")
    print(f"Saved {selection_path.as_posix()}")


if __name__ == "__main__":
    main()
