"""
Loss functions for NIDS models.

Consolidates:
  - ``PULoss``: class-form non-negative PU loss with stable gradient handling.
  - ``nnpu_loss``: function-form nnPU using a logistic surrogate over
    pre-split P / U logit batches (used by the 2-way TCN).
  - ``contrastive_nt_xent``: SimCLR-style NT-Xent loss for SSL pretraining.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

import torch
import torch.nn.functional as F
from torch import nn

logger = logging.getLogger(__name__)


# ─── Class-prior helpers ──────────────────────────────


def unlabeled_prior_from_pool(pi_pool: float, n_p: int, n_u: int) -> float:
    """Convert a pool-wide positive prior into the prior *inside* the U set.

    The nnPU estimator assumes the unlabeled sample is drawn from the marginal
    distribution, so its prior must be ``P(y=1 | unlabeled)``.  When U is built
    as the complement of a labelled positive set (``U = pool \\ P``) the labelled
    positives are absent from U, so the pool prior over-states it.  Uses only
    observable counts and the assumed pool prior — never ground-truth labels.
    """
    if not 0.0 < pi_pool < 1.0:
        raise ValueError(f"pi_pool must be in (0, 1), got {pi_pool}")
    if n_u <= 0:
        raise ValueError(f"n_u must be positive, got {n_u}")

    hidden_positives = pi_pool * (n_p + n_u) - n_p
    pi_u = hidden_positives / n_u
    if not 0.0 < pi_u < 1.0:
        raise ValueError(
            f"Derived unlabeled prior {pi_u:.4f} is outside (0, 1): the pool "
            f"prior {pi_pool} implies {hidden_positives:.0f} hidden positives "
            f"among {n_u} unlabeled samples (|P|={n_p}). Either the prior is "
            "mis-specified or it already refers to the unlabeled set "
            "(set pi_p_scope='unlabeled')."
        )
    return pi_u


# ─── nnPU (class form, mixed P/U batches) ─────────────


def _defit_surrogate(
    pos_risk: torch.Tensor,
    neg_risk: torch.Tensor,
    beta: float,
    gamma: float,
) -> torch.Tensor:
    """Return the nnPU objective with Kiryo et al.'s de-fitting correction.

    While ``neg_risk >= -beta`` the estimator is the plain PU risk.  Once the
    empirical negative risk drops below ``-beta`` the model is over-fitting the
    unlabeled set, and the correct response is a gradient *ascent* step on the
    negative term (backward through ``-gamma * neg_risk``).  Clamping instead
    would zero the gradient and silently stop the unlabeled set from
    contributing at all.  The returned tensor carries the reported objective as
    its value and the de-fitting direction as its gradient.
    """
    if float(neg_risk.detach()) >= -beta:
        return pos_risk + neg_risk

    ascent = -gamma * neg_risk
    reported = pos_risk.detach() - beta
    return ascent + (reported - ascent).detach()


class PULoss(nn.Module):
    """Non-negative Positive-Unlabeled (nnPU) loss for mixed P/U batches."""

    def __init__(
        self,
        prior: float,
        nnpu: bool = True,
        beta: float = 0.0,
        gamma: float = 1.0,
    ) -> None:
        super().__init__()
        if not 0.0 < prior < 1.0:
            raise ValueError(f"prior must be in (0, 1), got {prior}")
        self.prior = prior
        self.nnpu = nnpu
        self.beta = beta
        self.gamma = gamma
        self._warned_negative = False

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        pos_mask = targets.bool()
        unl_mask = ~pos_mask
        n_pos = pos_mask.float().sum().clamp_min(1.0)
        n_unl = unl_mask.float().sum().clamp_min(1.0)

        loss_pos_as_pos = F.softplus(-logits)
        loss_as_neg = F.softplus(logits)

        positive_risk = self.prior * loss_pos_as_pos[pos_mask].sum() / n_pos
        unlabeled_neg_risk = loss_as_neg[unl_mask].sum() / n_unl
        positive_neg_risk = self.prior * loss_as_neg[pos_mask].sum() / n_pos
        negative_risk = unlabeled_neg_risk - positive_neg_risk

        if not self.nnpu:
            return positive_risk + negative_risk

        if float(negative_risk.detach()) < -self.beta and not self._warned_negative:
            logger.debug(
                "nnPU: de-fitting engaged (negative risk %.4f). Normal early on.",
                float(negative_risk.detach()),
            )
            self._warned_negative = True
        return _defit_surrogate(positive_risk, negative_risk, self.beta, self.gamma)


# ─── nnPU (function form, separate P / U logits) ──────


def logistic_loss(logit: torch.Tensor, y_pm1: torch.Tensor) -> torch.Tensor:
    """Logistic surrogate with labels in {+1, -1}: softplus(-y·f)."""
    return F.softplus(-y_pm1 * logit)


def nnpu_loss(
    logit_p: torch.Tensor,
    logit_u: torch.Tensor,
    pi_p: float,
    p_weights: Optional[torch.Tensor] = None,
    beta: float = 0.0,
    gamma: float = 1.0,
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """nnPU risk estimator over pre-split P and U logit batches.

    Args:
        logit_p: Risk logits for the positive (P) batch, shape ``[n_p]``.
        logit_u: Risk logits for the unlabeled (U) batch, shape ``[n_u]``.
        pi_p: Prior probability of a positive event *within the unlabeled set*.
        p_weights: Optional per-sample weights for P samples, shape ``[n_p]``.
            When provided, the positive risk terms are computed as a weighted
            mean (``sum(w·l) / sum(w)``), which downweights pseudo-positive
            samples relative to native positives.  When ``None``, falls back
            to the standard unweighted mean.
        beta: Non-negativity slack; de-fitting starts once the negative risk
            falls below ``-beta``.
        gamma: Scale of the de-fitting (gradient-ascent) step.
    """
    if not 0.0 < pi_p < 1.0:
        raise ValueError(f"pi_p must be in (0, 1), got {pi_p}")

    lp_pos = logistic_loss(logit_p, torch.ones_like(logit_p))
    lp_neg = logistic_loss(logit_p, -torch.ones_like(logit_p))

    if p_weights is not None:
        w = p_weights.to(logit_p.device)
        w_sum = w.sum().clamp_min(1e-8)
        rp_pos = (lp_pos * w).sum() / w_sum
        rp_neg = (lp_neg * w).sum() / w_sum
    else:
        rp_pos = lp_pos.mean()
        rp_neg = lp_neg.mean()

    ru_neg = logistic_loss(logit_u, -torch.ones_like(logit_u)).mean()

    pos_risk = pi_p * rp_pos
    neg_risk = ru_neg - pi_p * rp_neg
    defitting = float(neg_risk.detach()) < -beta
    total = _defit_surrogate(pos_risk, neg_risk, beta, gamma)

    stats = {
        "pos_risk": float(pos_risk.detach()),
        "neg_risk_raw": float(neg_risk.detach()),
        "nnpu_risk": float(total.detach()),
        "defitting": float(defitting),
    }
    return total, stats


# ─── Contrastive (SimCLR / NT-Xent) ───────────────────


def contrastive_nt_xent(
    z1: torch.Tensor,
    z2: torch.Tensor,
    temperature: float = 0.2,
) -> torch.Tensor:
    """NT-Xent (SimCLR) contrastive loss over a batch of two augmented views."""
    B = z1.size(0)
    z = torch.cat([z1, z2], dim=0)
    sim = (z @ z.t()) / temperature
    sim = sim - torch.eye(2 * B, device=z.device) * 1e9

    targets = (torch.arange(2 * B, device=z.device) + B) % (2 * B)
    return F.cross_entropy(sim, targets)
