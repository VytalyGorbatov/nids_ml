"""Run the test-oracle FPR diagnostic for every model_best.pt run directory."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_ORACLE_SCRIPT = SCRIPT_DIR / "test_oracle_fpr_curve.py"
DEFAULT_ROOT = REPO_ROOT / "artifacts" / "article_1" / "runs"


def iter_run_dirs(root: Path) -> list[Path]:
    """Return all run directories containing a model_best.pt checkpoint."""
    if not root.exists():
        raise FileNotFoundError(f"Runs root does not exist: {root}")
    return sorted(
        {path.parent for path in root.glob("**/model_best.pt") if path.is_file()},
        key=lambda path: str(path),
    )


def build_command(
    oracle_script: Path,
    prediction_path: Path,
    out_path: Path,
    budgets: tuple[float, ...],
    score_key: str,
) -> list[str]:
    return [
        sys.executable,
        str(oracle_script),
        "--predictions",
        str(prediction_path),
        "--out",
        str(out_path),
        "--score-key",
        score_key,
        "--budgets",
        ",".join(str(value) for value in budgets),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run test_oracle_fpr_curve.py for every run directory under "
            "artifacts/article_1/runs that contains model_best.pt."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Root directory to scan for run folders (default: %(default)s).",
    )
    parser.add_argument(
        "--oracle-script",
        type=Path,
        default=DEFAULT_ORACLE_SCRIPT,
        help="Path to test_oracle_fpr_curve.py (default: %(default)s).",
    )
    parser.add_argument(
        "--score-key",
        default="raw_logit",
        help="Score column used for ranking thresholds (default: raw_logit).",
    )
    parser.add_argument(
        "--budgets",
        default="0.01,0.05,0.10",
        help="Comma-separated strict FPR budgets to evaluate.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the commands instead of executing them.",
    )
    args = parser.parse_args()

    root = args.root if args.root.is_absolute() else (REPO_ROOT / args.root).resolve()
    oracle_script = args.oracle_script
    if not oracle_script.is_absolute():
        oracle_script = (REPO_ROOT / oracle_script).resolve()

    budgets = tuple(float(part.strip()) for part in args.budgets.split(",") if part.strip())
    if not budgets:
        raise ValueError("At least one FPR budget is required.")

    run_dirs = iter_run_dirs(root)
    if not run_dirs:
        raise FileNotFoundError(f"No model_best.pt checkpoints found under {root}")

    print(f"Found {len(run_dirs)} run directories under {root}")
    successes: list[Path] = []
    failures: list[tuple[Path, str]] = []

    for run_dir in run_dirs:
        prediction_path = run_dir / "test_samples.json"
        if not prediction_path.exists():
            failures.append((run_dir, f"missing test_samples.json: {prediction_path}"))
            continue

        out_path = run_dir / "test_oracle_fpr_curve.json"
        command = build_command(oracle_script, prediction_path, out_path, budgets, args.score_key)
        print(f"\n[{run_dir.name}] {command}")
        if args.dry_run:
            continue

        try:
            subprocess.run(command, cwd=str(REPO_ROOT), check=True)
        except subprocess.CalledProcessError as exc:
            failures.append((run_dir, f"exit code {exc.returncode}"))
            continue

        successes.append(run_dir)

    print("\nSummary:")
    print(f"  successful: {len(successes)}")
    print(f"  failed: {len(failures)}")
    for run_dir, reason in failures:
        print(f"  - {run_dir}: {reason}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
