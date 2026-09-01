import json
import math

from nids_ml.tools.test_oracle_fpr_curve import build_report, strict_fpr_oracle_threshold


def test_zero_fp_budget_uses_threshold_above_top_benign_score() -> None:
    rows = [
        {"is_attack": 0, "alerted": 0, "raw_logit": 0.9},
        {"is_attack": 0, "alerted": 0, "raw_logit": 0.8},
        {"is_attack": 1, "alerted": 0, "raw_logit": 0.7},
    ]

    threshold, benign_fp, benign_total = strict_fpr_oracle_threshold(rows, 0.01)

    assert benign_total == 2
    assert benign_fp == 0
    assert threshold > 0.9
    assert math.isfinite(threshold)
    assert json.dumps(build_report(rows, (0.01,), "raw_logit"), allow_nan=False)
