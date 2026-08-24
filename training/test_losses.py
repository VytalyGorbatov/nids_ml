"""Regression checks for the nnPU estimator and its class-prior handling."""

import pytest
import torch

from nids_ml.training.losses import PULoss, nnpu_loss, unlabeled_prior_from_pool


def _overfit_logits() -> tuple[torch.Tensor, torch.Tensor]:
    """P scored high and U scored low drives the negative risk below zero."""
    return (
        torch.full((64,), 6.0, requires_grad=True),
        torch.full((256,), -6.0, requires_grad=True),
    )


def test_defitting_sends_gradient_to_unlabeled_batch() -> None:
    logit_p, logit_u = _overfit_logits()

    loss, stats = nnpu_loss(logit_p, logit_u, pi_p=0.10)
    loss.backward()

    assert stats["neg_risk_raw"] < 0
    assert stats["defitting"] == 1.0
    # A clamp would zero this out and stop the unlabeled set from training.
    assert logit_u.grad.abs().sum() > 0


def test_defitting_pushes_unlabeled_scores_up() -> None:
    logit_p, logit_u = _overfit_logits()

    nnpu_loss(logit_p, logit_u, pi_p=0.10)[0].backward()

    # Descending the surrogate must raise U logits back toward the P side.
    assert logit_u.grad.sum() < 0


def test_plain_pu_risk_used_while_negative_risk_is_healthy() -> None:
    logit_p = torch.zeros(64, requires_grad=True)
    logit_u = torch.zeros(256, requires_grad=True)

    loss, stats = nnpu_loss(logit_p, logit_u, pi_p=0.10)
    loss.backward()

    assert stats["defitting"] == 0.0
    assert stats["neg_risk_raw"] > 0
    assert loss.item() == pytest.approx(
        stats["pos_risk"] + stats["neg_risk_raw"], rel=1e-6
    )
    assert logit_u.grad.sum() > 0


def test_beta_slack_delays_defitting() -> None:
    logit_p, logit_u = _overfit_logits()

    _, strict = nnpu_loss(logit_p, logit_u, pi_p=0.10, beta=0.0)
    _, slack = nnpu_loss(logit_p, logit_u, pi_p=0.10, beta=10.0)

    assert strict["defitting"] == 1.0
    assert slack["defitting"] == 0.0


def test_pu_loss_class_form_defits_in_the_same_direction() -> None:
    logits = torch.cat([
        torch.full((64,), 6.0), torch.full((256,), -6.0),
    ]).requires_grad_(True)
    targets = torch.cat([torch.ones(64), torch.zeros(256)])

    PULoss(prior=0.10)(logits, targets).backward()

    assert logits.grad[64:].sum() < 0


def test_unlabeled_prior_excludes_the_labelled_positives() -> None:
    # 1000 samples at a 20% pool prior with 100 labelled positives leaves
    # 100 hidden positives among the 900 unlabeled ones.
    assert unlabeled_prior_from_pool(0.20, n_p=100, n_u=900) == pytest.approx(
        100 / 900
    )


def test_unlabeled_prior_is_below_the_pool_prior() -> None:
    assert unlabeled_prior_from_pool(0.12, n_p=1967, n_u=70147) < 0.12


def test_unlabeled_prior_rejects_impossible_priors() -> None:
    with pytest.raises(ValueError, match="outside"):
        unlabeled_prior_from_pool(0.05, n_p=100, n_u=900)
