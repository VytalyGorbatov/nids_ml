"""
Metrics for NIDS classifier evaluation.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import torch
from sklearn.metrics import average_precision_score

from ..local_types import Metrics


class MetricUtils:
    @staticmethod
    def compute_binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Metrics:
        """Computes Accuracy, Precision, Recall, and F1 from hard predictions."""
        assert y_true.shape == y_pred.shape

        tp = float(np.sum((y_true == 1) & (y_pred == 1)))
        tn = float(np.sum((y_true == 0) & (y_pred == 0)))
        fp = float(np.sum((y_true == 0) & (y_pred == 1)))
        fn = float(np.sum((y_true == 1) & (y_pred == 0)))

        eps = 1e-12
        return {
            "accuracy": (tp + tn) / max(tp + tn + fp + fn, eps),
            "precision": tp / max(tp + fp, eps),
            "recall": tp / max(tp + fn, eps),
            "f1": 2.0 * tp / max(2.0 * tp + fp + fn, eps),
        }


@torch.no_grad()
def average_precision(
    scores: torch.Tensor,
    y_true: torch.Tensor,
) -> float:
    """Return the canonical tie-safe Average Precision score.

    The metric is computed from the full score ranking with all samples that
    share a score treated as one threshold group.  This is the definition used
    for checkpoint selection and all reported AP values.
    """
    scores = scores.detach().cpu().reshape(-1)
    y_true = y_true.detach().cpu().reshape(-1)
    if scores.numel() != y_true.numel():
        raise ValueError("scores and y_true must have the same number of elements")
    if scores.numel() == 0 or not bool((y_true == 1).any()):
        return 0.0

    return float(average_precision_score(
        y_true.numpy(), scores.numpy(), pos_label=1,
    ))


@torch.no_grad()
def pr_curve_best_f1(
    scores: torch.Tensor,
    y_true: torch.Tensor,
) -> Dict[str, float]:
    """Return tie-safe Average Precision and the threshold maximising F1."""
    scores = scores.detach().cpu().reshape(-1)
    y_true = y_true.detach().cpu().reshape(-1)

    if scores.numel() == 0:
        return {
            "best_threshold": 0.5,
            "best_f1": 0.0,
            "average_precision": 0.0,
            "pr_auc": 0.0,
            "precision_at_best": 0.0,
            "recall_at_best": 0.0,
        }
    if scores.numel() != y_true.numel():
        raise ValueError("scores and y_true must have the same number of elements")

    idx = torch.argsort(scores, descending=True)
    s = scores[idx]
    y = y_true[idx]

    tp = torch.cumsum(y, dim=0)
    fp = torch.cumsum(1 - y, dim=0)
    # A threshold applies to every sample at the same score.  Evaluating only
    # after each tied score group makes the selected F1/threshold executable.
    group_ends = torch.cat((
        torch.nonzero(s[:-1] != s[1:], as_tuple=False).flatten(),
        torch.tensor([s.numel() - 1]),
    ))
    tp = tp[group_ends]
    fp = fp[group_ends]
    thresholds = s[group_ends]
    fn = tp[-1] - tp

    precision = tp / (tp + fp).clamp_min(1.0)
    recall = tp / (tp + fn).clamp_min(1.0)
    f1 = 2 * precision * recall / (precision + recall).clamp_min(1e-12)

    best_i = int(torch.argmax(f1).item())
    ap = average_precision(scores, y_true)

    return {
        "best_threshold": float(thresholds[best_i].item()),
        "best_f1": float(f1[best_i].item()),
        "average_precision": ap,
        # Backward-compatible artifact key.  New reports must call this AP.
        "pr_auc": ap,
        "precision_at_best": float(precision[best_i].item()),
        "recall_at_best": float(recall[best_i].item()),
    }


@torch.no_grad()
def snort_fn_metrics(
    scores: torch.Tensor,
    is_attack: torch.Tensor,
    alerted: torch.Tensor,
    threshold: float,
) -> Dict[str, float]:
    """Compute metrics on the Snort-FN subset (alerted=0, is_attack=1).

    This measures the model's ability to detect attacks that Snort missed.
    """
    scores = scores.detach().cpu()
    is_attack = is_attack.detach().cpu()
    alerted = alerted.detach().cpu()

    # Snort FN subset: attacks that Snort did NOT alert on
    fn_mask = (alerted == 0) & (is_attack == 1)
    fn_count = int(fn_mask.sum().item())

    if fn_count == 0:
        return {
            "snort_fn_count": 0,
            "snort_fn_recall": 0.0,
            "snort_fn_recovered": 0,
        }

    fn_scores = scores[fn_mask]
    recovered = (fn_scores >= threshold).sum().item()
    recall = recovered / fn_count

    # Also compute precision: of all model positives in the alerted=0 subset,
    # how many are true attacks?
    unalerted_mask = (alerted == 0)
    unalerted_preds = (scores[unalerted_mask] >= threshold)
    unalerted_attacks = is_attack[unalerted_mask]
    tp = (unalerted_preds & (unalerted_attacks == 1)).sum().item()
    fp = (unalerted_preds & (unalerted_attacks == 0)).sum().item()
    precision = tp / max(tp + fp, 1e-12)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)

    return {
        "snort_fn_count": fn_count,
        "snort_fn_recovered": int(recovered),
        "snort_fn_recall": recall,
        "snort_fn_precision": precision,
        "snort_fn_f1": f1,
    }


__all__ = [
    "MetricUtils", "average_precision", "pr_curve_best_f1", "snort_fn_metrics",
]
