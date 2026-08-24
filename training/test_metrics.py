"""Focused regression checks for canonical ranking and threshold metrics."""

import pytest
import torch
from sklearn.metrics import average_precision_score

from nids_ml.training.metrics import average_precision, pr_curve_best_f1


def test_average_precision_matches_sklearn_with_tied_scores() -> None:
    scores = torch.tensor([0.8, 0.8, 0.5, 0.5, 0.1])
    labels = torch.tensor([1, 0, 1, 0, 0])

    expected = average_precision_score(labels.numpy(), scores.numpy())

    assert average_precision(scores, labels) == expected
    assert pr_curve_best_f1(scores, labels)["pr_auc"] == expected


def test_best_f1_threshold_never_splits_a_tied_score_group() -> None:
    scores = torch.tensor([0.9, 0.9, 0.5, 0.5])
    labels = torch.tensor([1, 0, 1, 1])

    result = pr_curve_best_f1(scores, labels)
    predictions = scores >= result["best_threshold"]
    tp = int((predictions & (labels == 1)).sum())
    fp = int((predictions & (labels == 0)).sum())
    fn = int(((~predictions) & (labels == 1)).sum())
    expected_f1 = 2 * tp / (2 * tp + fp + fn)

    assert result["best_threshold"] == 0.5
    assert result["best_f1"] == pytest.approx(expected_f1)