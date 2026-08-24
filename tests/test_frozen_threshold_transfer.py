from nids_ml.tools.frozen_threshold_transfer import (
    benign_group_rows,
    fn_recovery_rows,
    validation_fpr_threshold,
)


def _row(
    score: float,
    is_attack: int = 0,
    alerted: int = 0,
    scenario: str = "scenario.xml",
    template_id: str = "template",
    mutation_id: str = "mutation",
) -> dict:
    return {
        "raw_score": score,
        "is_attack": is_attack,
        "alerted": alerted,
        "sip_method": "INVITE",
        "provenance": {
            "scenario": scenario,
            "template_id": template_id,
            "mutation_id": mutation_id,
        },
    }


def test_validation_threshold_is_lowest_score_within_budget() -> None:
    rows = [_row(0.9), _row(0.8), _row(0.7), _row(0.1, is_attack=1)]

    assert validation_fpr_threshold(rows, 1 / 3) == 0.9
    assert validation_fpr_threshold(rows, 2 / 3) == 0.8


def test_benign_group_rows_expose_fp_share_and_train_visibility() -> None:
    rows = [_row(0.9, scenario="a.xml"), _row(0.8, scenario="a.xml"), _row(0.1, scenario="b.xml")]
    reports = benign_group_rows(
        "pu", "test", rows, 0.05, 0.8,
        {("a.xml", "template", "INVITE")},
    )
    by_scenario = {row["scenario"]: row for row in reports}

    assert by_scenario["a.xml"]["high_risk_rows"] == 2
    assert by_scenario["a.xml"]["fp_share"] == 1.0
    assert by_scenario["a.xml"]["seen_exact_group_in_train"] is True
    assert by_scenario["a.xml"]["seen_scenario_in_train"] is True
    assert by_scenario["a.xml"]["seen_template_method_in_train"] is True
    assert by_scenario["b.xml"]["group_fpr"] == 0.0


def test_fn_recovery_groups_only_snort_false_negatives() -> None:
    rows = [
        _row(0.9, is_attack=1, alerted=0),
        _row(0.1, is_attack=1, alerted=0),
        _row(0.9, is_attack=1, alerted=1),
    ]

    reports = fn_recovery_rows("pu", "test", rows, 0.05, 0.5)

    assert len(reports) == 1
    assert reports[0]["snort_fn_rows"] == 2
    assert reports[0]["recovered_rows"] == 1
    assert reports[0]["recovery_rate"] == 0.5