"""Conservative multi-cohort benign-scenario threshold calibration.

A single validation cohort can understate the benign false-positive rate a
threshold will see on unseen scenarios. This tool partitions validation
benign scenarios into disjoint folds, selects a threshold per fold, and
takes the maximum across folds so the result must satisfy the FPR budget on
every fold, not only the full validation pool. It then compares that
conservative threshold against the current single-cohort baseline on the
frozen test set. No retraining is involved.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from nids_ml.tools.frozen_threshold_transfer import (
    _write_csv,
    group_key,
    load_jsonl,
    validation_fpr_threshold,
)

DEFAULT_SEED = 137744799
SUMMARY_COLUMNS = (
    "model", "budget", "folds", "policy", "threshold", "val_benign_fpr",
    "test_benign_fpr", "test_snort_fn_recovery",
)


def assign_scenario_folds(
    rows: Iterable[dict[str, Any]], folds: int, seed: int,
) -> dict[str, int]:
    """Assign each benign scenario to one fold, balanced by benign row count."""
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        if row["is_attack"] == 0 and row["alerted"] == 0:
            counts[group_key(row)[0]] += 1
    if len(counts) < folds:
        raise ValueError(
            f"Need at least {folds} distinct benign scenarios for {folds} "
            f"folds, found {len(counts)}"
        )

    randomizer = random.Random(seed)
    scenarios = list(counts)
    randomizer.shuffle(scenarios)  # tie-break order only; sort below is stable
    scenarios.sort(key=lambda scenario: -counts[scenario])

    fold_totals = [0] * folds
    assignment: dict[str, int] = {}
    for scenario in scenarios:
        fold = min(range(folds), key=lambda index: fold_totals[index])
        assignment[scenario] = fold
        fold_totals[fold] += counts[scenario]
    return assignment


def fold_threshold(
    rows: list[dict[str, Any]], fold_assignment: dict[str, int], fold: int, budget: float,
) -> float:
    """Return the budget threshold using only one fold's benign scenarios."""
    fold_rows = [
        row for row in rows if fold_assignment.get(group_key(row)[0]) == fold
    ]
    return validation_fpr_threshold(fold_rows, budget)


def conservative_threshold(
    rows: list[dict[str, Any]], fold_assignment: dict[str, int], folds: int, budget: float,
) -> tuple[float, dict[int, float]]:
    """Return the max-over-folds threshold and each fold's own threshold."""
    per_fold = {
        fold: fold_threshold(rows, fold_assignment, fold, budget)
        for fold in range(folds)
    }
    return max(per_fold.values()), per_fold


def evaluate_threshold(rows: Iterable[dict[str, Any]], threshold: float) -> dict[str, Any]:
    """Return overall benign FPR and hidden-attack recovery at one threshold."""
    benign = [row for row in rows if row["is_attack"] == 0 and row["alerted"] == 0]
    hidden_attacks = [row for row in rows if row["is_attack"] == 1 and row["alerted"] == 0]
    benign_fp = sum(float(row["raw_score"]) >= threshold for row in benign)
    recovered = sum(float(row["raw_score"]) >= threshold for row in hidden_attacks)
    return {
        "benign_total": len(benign),
        "benign_fp": benign_fp,
        "benign_fpr": benign_fp / len(benign) if benign else 0.0,
        "snort_fn_total": len(hidden_attacks),
        "snort_fn_recovered": recovered,
        "snort_fn_recovery": recovered / len(hidden_attacks) if hidden_attacks else 0.0,
    }


def analyze_run(
    run_dir: Path, budgets: tuple[float, ...], folds: int, seed: int,
) -> dict[str, Any]:
    """Compare baseline single-cohort thresholds against conservative folds."""
    val_rows = load_jsonl(run_dir / "val_predictions_joined.jsonl")
    test_rows = load_jsonl(run_dir / "test_predictions_joined.jsonl")
    fold_assignment = assign_scenario_folds(val_rows, folds, seed)
    model = run_dir.name

    budget_reports: list[dict[str, Any]] = []
    for budget in budgets:
        baseline_threshold = validation_fpr_threshold(val_rows, budget)
        conservative_t, per_fold = conservative_threshold(
            val_rows, fold_assignment, folds, budget,
        )
        budget_reports.append({
            "model": model,
            "budget": budget,
            "folds": folds,
            "per_fold_thresholds": per_fold,
            "baseline_threshold": baseline_threshold,
            "baseline_val": evaluate_threshold(val_rows, baseline_threshold),
            "baseline_test": evaluate_threshold(test_rows, baseline_threshold),
            "conservative_threshold": conservative_t,
            "conservative_val": evaluate_threshold(val_rows, conservative_t),
            "conservative_test": evaluate_threshold(test_rows, conservative_t),
        })
    return {
        "model": model,
        "fold_assignment": fold_assignment,
        "budget_reports": budget_reports,
    }


def _summary_rows(run_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report in run_report["budget_reports"]:
        for policy, threshold_key, val_key, test_key in (
            ("baseline", "baseline_threshold", "baseline_val", "baseline_test"),
            ("conservative", "conservative_threshold", "conservative_val", "conservative_test"),
        ):
            rows.append({
                "model": report["model"],
                "budget": report["budget"],
                "folds": report["folds"],
                "policy": policy,
                "threshold": report[threshold_key],
                "val_benign_fpr": report[val_key]["benign_fpr"],
                "test_benign_fpr": report[test_key]["benign_fpr"],
                "test_snort_fn_recovery": report[test_key]["snort_fn_recovery"],
            })
    return rows


def _render_summary(run_reports: list[dict[str, Any]]) -> str:
    lines = [
        "# Conservative Multi-Cohort Calibration",
        "",
        "Validation benign scenarios were partitioned into disjoint folds by "
        "scenario name. The conservative threshold is the maximum of the "
        "per-fold budget thresholds, so it must hold on every fold, not only "
        "on the full validation pool.",
        "",
    ]
    for run_report in run_reports:
        lines.extend([f"## {run_report['model']}", ""])
        for report in run_report["budget_reports"]:
            lines.extend([
                f"### Nominal budget {report['budget']:.0%} "
                f"({report['folds']} folds)",
                "",
                "| policy | threshold | validation FPR | test FPR | test FN recovery |",
                "|---|---:|---:|---:|---:|",
            ])
            for policy, threshold_key, val_key, test_key in (
                ("baseline (single cohort)", "baseline_threshold", "baseline_val", "baseline_test"),
                ("conservative (max over folds)", "conservative_threshold", "conservative_val", "conservative_test"),
            ):
                val_metrics = report[val_key]
                test_metrics = report[test_key]
                lines.append(
                    f"| {policy} | {report[threshold_key]:.4f} | "
                    f"{val_metrics['benign_fpr']:.2%} | "
                    f"{test_metrics['benign_fpr']:.2%} | "
                    f"{test_metrics['snort_fn_recovery']:.2%} |"
                )
            lines.extend(["", "Per-fold thresholds:", "", "| fold | threshold |", "|---:|---:|"])
            for fold, threshold in sorted(report["per_fold_thresholds"].items()):
                lines.append(f"| {fold} | {threshold:.4f} |")
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir", action="append", required=True, type=Path,
        help="Run directory containing val/test_predictions_joined.jsonl; repeatable.",
    )
    parser.add_argument(
        "--out", required=True, type=Path,
        help="Directory for JSON, CSV, and Markdown reports.",
    )
    parser.add_argument(
        "--budgets", default="0.01,0.05,0.10",
        help="Comma-separated validation benign-FPR budgets.",
    )
    parser.add_argument(
        "--folds", type=int, default=3,
        help="Number of scenario-disjoint calibration folds (default: 3).",
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help="Seed for scenario fold tie-breaking (default matches project convention).",
    )
    args = parser.parse_args()
    budgets = tuple(float(value) for value in args.budgets.split(","))
    if not budgets or any(not 0.0 < budget < 1.0 for budget in budgets):
        raise ValueError("--budgets must contain values strictly between 0 and 1")
    if args.folds < 2:
        raise ValueError("--folds must be at least 2")

    run_reports = [
        analyze_run(run_dir.resolve(), budgets, args.folds, args.seed)
        for run_dir in args.run_dir
    ]

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "conservative_fold_assignment.json").open("w", encoding="utf-8") as stream:
        json.dump(
            {report["model"]: report["fold_assignment"] for report in run_reports},
            stream, indent=2,
        )
        stream.write("\n")
    with (args.out / "conservative_threshold_summary.json").open("w", encoding="utf-8") as stream:
        json.dump(run_reports, stream, indent=2)
        stream.write("\n")
    summary_rows = [row for report in run_reports for row in _summary_rows(report)]
    _write_csv(args.out / "conservative_threshold_summary.csv", SUMMARY_COLUMNS, summary_rows)
    (args.out / "conservative_calibration_summary.md").write_text(
        _render_summary(run_reports), encoding="utf-8",
    )


if __name__ == "__main__":
    main()
