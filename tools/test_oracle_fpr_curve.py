"""Compute test-oracle Snort-FN recovery below exact empirical FPR caps.

This tool deliberately selects thresholds from frozen test benign scores. Its
results are diagnostic only: they describe the score-ranking frontier and are
not valid operational operating points.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable


DEFAULT_BUDGETS = (0.01, 0.05, 0.10)


def load_prediction_rows(path: Path) -> list[dict[str, Any]]:
    """Load a JSON array or JSONL prediction export."""
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    if content.startswith("["):
        rows = json.loads(content)
        if not isinstance(rows, list):
            raise ValueError(f"Expected a JSON array in {path}")
        return rows
    return [json.loads(line) for line in content.splitlines() if line.strip()]


def score_value(row: dict[str, Any], score_key: str) -> float:
    """Return a finite ranking score from a prediction row."""
    try:
        score = float(row[score_key])
    except KeyError as error:
        raise ValueError(f"Prediction row does not contain score key {score_key!r}") from error
    if not math.isfinite(score):
        raise ValueError(f"Prediction row has a non-finite {score_key!r} value")
    return score


def strictly_below_budget_count(benign_total: int, budget: float) -> int:
    """Return the largest integer FP count whose rate is strictly below budget."""
    if benign_total <= 0:
        raise ValueError("Need at least one benign non-alerted test row")
    if not 0.0 < budget < 1.0:
        raise ValueError("FPR budget must be strictly between zero and one")
    return math.ceil(budget * benign_total) - 1


def strict_fpr_oracle_threshold(
    rows: Iterable[dict[str, Any]], budget: float, score_key: str = "raw_logit",
) -> tuple[float, int, int]:
    """Choose a tie-safe test threshold with benign FPR strictly below budget."""
    benign_scores = sorted(
        (
            score_value(row, score_key)
            for row in rows
            if row["is_attack"] == 0 and row["alerted"] == 0
        ),
        reverse=True,
    )
    allowed_fp = strictly_below_budget_count(len(benign_scores), budget)
    if allowed_fp < 0:
        return math.nextafter(benign_scores[0], math.inf), 0, len(benign_scores)

    threshold = math.inf
    for score in benign_scores:
        false_positives = sum(candidate >= score for candidate in benign_scores)
        if false_positives <= allowed_fp:
            threshold = score
        else:
            break
    if math.isinf(threshold):
        # The benign score frontier is too high to satisfy the strict cap with
        # any finite threshold from those scores.  The next representable float
        # above the strongest benign score yields zero benign false positives while
        # remaining JSON-safe and tie-safe.
        return math.nextafter(benign_scores[0], math.inf), 0, len(benign_scores)
    false_positives = sum(score >= threshold for score in benign_scores)
    return threshold, false_positives, len(benign_scores)


def evaluate_oracle_threshold(
    rows: Iterable[dict[str, Any]], threshold: float, score_key: str,
) -> dict[str, int | float]:
    """Measure benign FPR and Snort-FN recovery at a frozen threshold."""
    rows = list(rows)
    benign = [row for row in rows if row["is_attack"] == 0 and row["alerted"] == 0]
    snort_fn = [row for row in rows if row["is_attack"] == 1 and row["alerted"] == 0]
    benign_fp = sum(score_value(row, score_key) >= threshold for row in benign)
    recovered = sum(score_value(row, score_key) >= threshold for row in snort_fn)
    return {
        "benign_total": len(benign),
        "benign_fp": benign_fp,
        "benign_fpr": benign_fp / len(benign),
        "snort_fn_total": len(snort_fn),
        "snort_fn_recovered": recovered,
        "snort_fn_recovery": recovered / len(snort_fn) if snort_fn else 0.0,
    }


def build_report(
    rows: list[dict[str, Any]], budgets: tuple[float, ...], score_key: str,
) -> dict[str, Any]:
    """Build diagnostic-only test-oracle operating points for each FPR cap."""
    operating_points = []
    for budget in budgets:
        threshold, benign_fp, benign_total = strict_fpr_oracle_threshold(
            rows, budget, score_key,
        )
        metrics = evaluate_oracle_threshold(rows, threshold, score_key)
        operating_points.append({
            "budget_strictly_below": budget,
            "threshold": threshold,
            "maximum_allowed_benign_fp": strictly_below_budget_count(benign_total, budget),
            **metrics,
        })
    return {
        "diagnostic_only": True,
        "warning": "Thresholds were selected from test benign labels; do not report as operational results.",
        "score_key": score_key,
        "operating_points": operating_points,
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render a concise human-readable diagnostic table."""
    lines = [
        "# Test-Oracle Strict-FPR Diagnostic",
        "",
        "Thresholds are selected from frozen test benign labels. This is diagnostic only, not an operational result.",
        "",
        "| strict FPR cap | threshold | benign FP / total | realized FPR | Snort FN recovered / total | recovery |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for point in report["operating_points"]:
        lines.append(
            f"| < {point['budget_strictly_below']:.0%} | {point['threshold']:.8g} | "
            f"{point['benign_fp']} / {point['benign_total']} | {point['benign_fpr']:.4%} | "
            f"{point['snort_fn_recovered']} / {point['snort_fn_total']} | "
            f"{point['snort_fn_recovery']:.2%} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path, help="Test prediction JSON or JSONL export.")
    parser.add_argument("--out", required=True, type=Path, help="Output JSON report path.")
    parser.add_argument("--score-key", default="raw_logit", help="Full-precision ranking score key (default: raw_logit).")
    parser.add_argument("--budgets", default="0.01,0.05,0.10", help="Comma-separated strict FPR caps.")
    args = parser.parse_args()

    budgets = tuple(float(value) for value in args.budgets.split(","))
    rows = load_prediction_rows(args.predictions)
    report = build_report(rows, budgets, args.score_key)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    args.out.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")


if __name__ == "__main__":
    main()