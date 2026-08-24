from nids_ml.tools.conservative_scenario_calibration import (
    assign_scenario_folds,
    conservative_threshold,
    evaluate_threshold,
)


def _row(
    score: float, is_attack: int = 0, alerted: int = 0, scenario: str = "a.xml",
) -> dict:
    return {
        "raw_score": score,
        "is_attack": is_attack,
        "alerted": alerted,
        "sip_method": "INVITE",
        "provenance": {"scenario": scenario, "template_id": "t", "mutation_id": "m"},
    }


def test_assign_scenario_folds_balances_by_benign_row_count() -> None:
    rows = (
        [_row(0.1, scenario="big.xml") for _ in range(10)]
        + [_row(0.1, scenario="small_a.xml") for _ in range(2)]
        + [_row(0.1, scenario="small_b.xml") for _ in range(2)]
    )

    assignment = assign_scenario_folds(rows, folds=2, seed=1)

    # The greedy balancer isolates the 10-row scenario and packs both 2-row
    # scenarios into the other fold (10 vs 4), which is more balanced than
    # any assignment that splits the two small scenarios apart (12 vs 2).
    assert assignment["big.xml"] != assignment["small_a.xml"]
    assert assignment["small_a.xml"] == assignment["small_b.xml"]


def test_assign_scenario_folds_requires_enough_scenarios() -> None:
    rows = [_row(0.1, scenario="only.xml")]
    try:
        assign_scenario_folds(rows, folds=2, seed=1)
    except ValueError as error:
        assert "Need at least 2" in str(error)
    else:
        raise AssertionError("expected ValueError for too few scenarios")


def test_conservative_threshold_is_the_max_over_folds() -> None:
    # 20-row folds so a 5% budget allows exactly one high-scoring benign row.
    strict_rows = [_row(0.1, scenario="strict.xml")] * 19 + [_row(0.9, scenario="strict.xml")]
    lenient_rows = [_row(0.95, scenario="lenient.xml")] * 20  # indistinguishable scores
    fold_assignment = {"strict.xml": 0, "lenient.xml": 1}

    threshold, per_fold = conservative_threshold(
        strict_rows + lenient_rows, fold_assignment, folds=2, budget=0.05,
    )

    assert per_fold[0] == 0.9  # strict fold can isolate its one risky row
    assert per_fold[1] == 1.0  # lenient fold has no score that clears the budget
    assert threshold == 1.0  # conservative = max over folds, driven by the weak fold


def test_evaluate_threshold_reports_fpr_and_recovery() -> None:
    rows = [
        _row(0.9, is_attack=0, alerted=0),
        _row(0.1, is_attack=0, alerted=0),
        _row(0.9, is_attack=1, alerted=0),
        _row(0.1, is_attack=1, alerted=0),
        _row(0.9, is_attack=1, alerted=1),
    ]

    metrics = evaluate_threshold(rows, threshold=0.5)

    assert metrics["benign_total"] == 2
    assert metrics["benign_fp"] == 1
    assert metrics["benign_fpr"] == 0.5
    assert metrics["snort_fn_total"] == 2
    assert metrics["snort_fn_recovered"] == 1
    assert metrics["snort_fn_recovery"] == 0.5
