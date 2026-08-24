"""Report benign-FPR transfer and Snort-FN recovery from joined predictions.

Thresholds are selected only from validation benign non-alerted rows and then
applied unchanged to validation and test.  This keeps scenario/template
diagnosis separate from operational threshold selection.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from nids_ml.tools.join_predictions_with_provenance import (
    _source_identity,
    _load_dataset,
    _load_manifest,
)

DEFAULT_BUDGETS = (0.01, 0.05, 0.10)
BENIGN_GROUP_COLUMNS = (
    "model", "split", "budget", "threshold", "scenario", "template_id",
    "sip_method", "benign_rows", "high_risk_rows", "group_fpr",
    "fp_share", "seen_exact_group_in_train", "seen_scenario_in_train",
    "seen_template_method_in_train",
)
FN_GROUP_COLUMNS = (
    "model", "split", "budget", "threshold", "mutation_id", "scenario",
    "template_id", "sip_method", "snort_fn_rows", "recovered_rows",
    "recovery_rate",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load a JSONL joined-prediction export."""
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def validation_fpr_threshold(rows: Iterable[dict[str, Any]], budget: float) -> float:
    """Return the lowest validation score satisfying the benign-FPR budget."""
    scores = sorted(
        {
            float(row["raw_score"])
            for row in rows
            if row["is_attack"] == 0 and row["alerted"] == 0
        },
        reverse=True,
    )
    if not scores:
        raise ValueError("Validation rows contain no benign non-alerted scores")

    best_threshold = 1.0
    benign_rows = [
        row for row in rows if row["is_attack"] == 0 and row["alerted"] == 0
    ]
    for threshold in scores:
        false_positives = sum(
            float(row["raw_score"]) >= threshold for row in benign_rows
        )
        if false_positives / len(benign_rows) <= budget + 1e-12:
            best_threshold = threshold
    return best_threshold


def group_key(row: dict[str, Any]) -> tuple[str, str, str]:
    """Return the benign scenario/template/method grouping key."""
    provenance = row.get("provenance") or {}
    scenario = provenance.get("scenario") or "<missing>"
    template_id = provenance.get("template_id") or "<missing>"
    return str(scenario), str(template_id), str(row.get("sip_method") or "UNKNOWN")


def fn_group_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    """Return the hidden-attack grouping key."""
    provenance = row.get("provenance") or {}
    mutation_id = provenance.get("mutation_id") or "<missing>"
    scenario, template_id, method = group_key(row)
    return str(mutation_id), scenario, template_id, method


def benign_group_rows(
    model: str,
    split: str,
    rows: Iterable[dict[str, Any]],
    budget: float,
    threshold: float,
    train_groups: set[tuple[str, str, str]],
) -> list[dict[str, Any]]:
    """Summarize benign high-risk rates per provenance group."""
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["is_attack"] == 0 and row["alerted"] == 0:
            groups[group_key(row)].append(row)

    high_risk_total = sum(
        float(row["raw_score"]) >= threshold
        for group_rows in groups.values()
        for row in group_rows
    )
    train_scenarios = {scenario for scenario, _, _ in train_groups}
    train_template_methods = {
        (template_id, method) for _, template_id, method in train_groups
    }
    report_rows: list[dict[str, Any]] = []
    for key, group_rows in groups.items():
        high_risk_rows = sum(float(row["raw_score"]) >= threshold for row in group_rows)
        scenario, template_id, method = key
        report_rows.append({
            "model": model,
            "split": split,
            "budget": budget,
            "threshold": threshold,
            "scenario": scenario,
            "template_id": template_id,
            "sip_method": method,
            "benign_rows": len(group_rows),
            "high_risk_rows": high_risk_rows,
            "group_fpr": high_risk_rows / len(group_rows),
            "fp_share": high_risk_rows / high_risk_total if high_risk_total else 0.0,
            "seen_exact_group_in_train": key in train_groups,
            "seen_scenario_in_train": scenario in train_scenarios,
            "seen_template_method_in_train": (template_id, method) in train_template_methods,
        })
    return report_rows


def fn_recovery_rows(
    model: str,
    split: str,
    rows: Iterable[dict[str, Any]],
    budget: float,
    threshold: float,
) -> list[dict[str, Any]]:
    """Summarize Snort-FN recovery per held-out mutation/provenance group."""
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["is_attack"] == 1 and row["alerted"] == 0:
            groups[fn_group_key(row)].append(row)

    report_rows: list[dict[str, Any]] = []
    for key, group_rows in groups.items():
        recovered_rows = sum(float(row["raw_score"]) >= threshold for row in group_rows)
        mutation_id, scenario, template_id, method = key
        report_rows.append({
            "model": model,
            "split": split,
            "budget": budget,
            "threshold": threshold,
            "mutation_id": mutation_id,
            "scenario": scenario,
            "template_id": template_id,
            "sip_method": method,
            "snort_fn_rows": len(group_rows),
            "recovered_rows": recovered_rows,
            "recovery_rate": recovered_rows / len(group_rows),
        })
    return report_rows


def _load_train_groups(run_dir: Path) -> set[tuple[str, str, str]]:
    """Load benign provenance groups available to the model during training."""
    train_path = run_dir / "train_predictions_joined.jsonl"
    if train_path.exists():
        return {
            group_key(row)
            for row in load_jsonl(train_path)
            if row["is_attack"] == 0 and row["alerted"] == 0
        }

    with (run_dir / "config_used.json").open(encoding="utf-8") as stream:
        config = json.load(stream)
    with (run_dir / "val_predictions_join_audit.json").open(encoding="utf-8") as stream:
        audit = json.load(stream)
    nids_ml_root = Path(__file__).resolve().parents[1]
    workspace_root = nids_ml_root.parent
    train_path = (nids_ml_root / config["benign_paths"]["train"]).resolve()
    manifest_path = (workspace_root / audit["provenance_paths"]["benign"]).resolve()
    provenance_by_call_id = {
        str(row["call_id"]): row
        for row in _load_manifest(manifest_path)
        if row.get("call_id")
    }
    groups: set[tuple[str, str, str]] = set()
    for record in _load_dataset(train_path):
        if record.get("alerted", 0):
            continue
        call_id, _, method, _, _ = _source_identity(record)
        provenance = provenance_by_call_id.get(call_id) if call_id else None
        if provenance is None:
            continue
        groups.add((
            str(provenance.get("scenario") or "<missing>"),
            str(provenance.get("template_id") or "<missing>"),
            method,
        ))
    return groups


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _format_group(row: dict[str, Any]) -> str:
    return f"{row['template_id']} / {row['sip_method']} / {Path(row['scenario']).name}"


def _render_summary(
    summaries: list[dict[str, Any]], benign_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# Frozen-Threshold Provenance Transfer",
        "",
        "Thresholds were selected from validation benign non-alerted rows using "
        "rounded joined `raw_score` values and applied unchanged to both splits.",
        "Exact campaign values can differ slightly because native exports retain "
        "more score precision.",
        "",
        "## Overall Transfer",
        "",
        "| model | nominal budget | threshold | validation FPR | test FPR | ",
        "|---|---:|---:|---:|---:|",
    ]
    for summary in summaries:
        lines.append(
            f"| {summary['model']} | {summary['budget']:.0%} | "
            f"{summary['threshold']:.4f} | {summary['val_fpr']:.2%} | "
            f"{summary['test_fpr']:.2%} |"
        )

    lines.extend(["", "## Test Benign FP Concentration", ""])
    for summary in summaries:
        candidates = [
            row for row in benign_rows
            if row["model"] == summary["model"] and row["split"] == "test"
            and row["budget"] == summary["budget"] and row["high_risk_rows"]
        ]
        candidates.sort(key=lambda row: row["high_risk_rows"], reverse=True)
        lines.extend([
            f"### {summary['model']} at {summary['budget']:.0%}",
            "",
            "| group | added benign FP | group FPR | FP share | scenario seen | template/method seen |",
            "|---|---:|---:|---:|---|---|",
        ])
        for row in candidates[:10]:
            scenario_seen = "yes" if row["seen_scenario_in_train"] else "no"
            template_seen = "yes" if row["seen_template_method_in_train"] else "no"
            lines.append(
                f"| {_format_group(row)} | {row['high_risk_rows']} | "
                f"{row['group_fpr']:.2%} | {row['fp_share']:.2%} | "
                f"{scenario_seen} | {template_seen} |"
            )
        lines.append("")
    return "\n".join(lines)


def _overall_fpr(rows: Iterable[dict[str, Any]], threshold: float) -> tuple[int, int, float]:
    benign = [row for row in rows if row["is_attack"] == 0 and row["alerted"] == 0]
    high_risk = sum(float(row["raw_score"]) >= threshold for row in benign)
    return high_risk, len(benign), high_risk / len(benign) if benign else 0.0


def analyze_run(run_dir: Path, budgets: tuple[float, ...]) -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]],
]:
    """Analyze one run directory containing joined validation and test exports."""
    val_rows = load_jsonl(run_dir / "val_predictions_joined.jsonl")
    test_rows = load_jsonl(run_dir / "test_predictions_joined.jsonl")
    train_groups = _load_train_groups(run_dir)
    model = run_dir.name
    summaries: list[dict[str, Any]] = []
    benign_reports: list[dict[str, Any]] = []
    fn_reports: list[dict[str, Any]] = []
    for budget in budgets:
        threshold = validation_fpr_threshold(val_rows, budget)
        val_high, val_total, val_fpr = _overall_fpr(val_rows, threshold)
        test_high, test_total, test_fpr = _overall_fpr(test_rows, threshold)
        summaries.append({
            "model": model,
            "budget": budget,
            "threshold": threshold,
            "val_benign_fp": val_high,
            "val_benign_total": val_total,
            "val_fpr": val_fpr,
            "test_benign_fp": test_high,
            "test_benign_total": test_total,
            "test_fpr": test_fpr,
        })
        for split, rows in (("val", val_rows), ("test", test_rows)):
            benign_reports.extend(
                benign_group_rows(model, split, rows, budget, threshold, train_groups)
            )
            fn_reports.extend(fn_recovery_rows(model, split, rows, budget, threshold))
    return summaries, benign_reports, fn_reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir", action="append", required=True, type=Path,
        help="Run directory containing val/test_predictions_joined.jsonl; repeatable.",
    )
    parser.add_argument(
        "--out", required=True, type=Path,
        help="Directory for CSV, JSON, and Markdown reports.",
    )
    parser.add_argument(
        "--budgets", default="0.01,0.05,0.10",
        help="Comma-separated validation benign-FPR budgets.",
    )
    args = parser.parse_args()
    budgets = tuple(float(value) for value in args.budgets.split(","))
    if not budgets or any(not 0.0 < budget < 1.0 for budget in budgets):
        raise ValueError("--budgets must contain values strictly between 0 and 1")

    summaries: list[dict[str, Any]] = []
    benign_reports: list[dict[str, Any]] = []
    fn_reports: list[dict[str, Any]] = []
    for run_dir in args.run_dir:
        run_summaries, run_benign, run_fn = analyze_run(run_dir.resolve(), budgets)
        summaries.extend(run_summaries)
        benign_reports.extend(run_benign)
        fn_reports.extend(run_fn)

    args.out.mkdir(parents=True, exist_ok=True)
    _write_csv(args.out / "benign_fpr_by_scenario_template.csv", BENIGN_GROUP_COLUMNS, benign_reports)
    _write_csv(args.out / "snort_fn_recovery_by_mutation.csv", FN_GROUP_COLUMNS, fn_reports)
    with (args.out / "frozen_threshold_transfer_summary.json").open("w", encoding="utf-8") as stream:
        json.dump(summaries, stream, indent=2)
        stream.write("\n")
    (args.out / "benign_fpr_transfer_summary.md").write_text(
        _render_summary(summaries, benign_reports), encoding="utf-8",
    )


if __name__ == "__main__":
    main()