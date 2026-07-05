#!/usr/bin/env python3
"""Lightweight smoke test for Stage-2 trainability modes (no training loop).

Builds a tiny ``tcn_2way`` model, wraps it in ``TwoWayTrainer`` for each of the
four ``stage2_trainable`` modes, and verifies:

  * the EXACT set of trainable parameter names matches the intended boundary,
  * the optimizer param-group count and per-group learning rates are correct,
  * ``_set_frozen_eval`` leaves frozen submodules in eval() while trainable
    submodules stay in train().

Run it as a module or a script:

    python -m nids_ml.artifacts.processors._smoke_stage2_modes
    python nids_ml/artifacts/processors/_smoke_stage2_modes.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Set

import torch
import torch.nn.functional as F

# Make the nids_ml package importable when launched as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from nids_ml.models import build_model
from nids_ml.models.tcn_2way import PAD_IDX
from nids_ml.training.twoway import TwoWayTrainer

_LR = 1e-3
_SCALE = 0.25  # deliberately != default 0.1 so the LR assertion is meaningful


# ─── builders ────────────────────────────────────────


def _small_config() -> Dict[str, Any]:
    return {
        "model": {
            "type": "tcn_2way",
            "embed_dim": 8,
            "channels": 16,
            "kernel": 3,
            "dilations": [1, 2, 4, 8],  # 4 blocks → blocks[3] is the last
            "dropout": 0.1,
            "prefix_lengths": [16, 32],
            "proj_dim": 16,
            "fusion_dim": 32,
        },
    }


def _make_trainer(mode: str) -> TwoWayTrainer:
    model = build_model(_small_config())
    cfg: Dict[str, Any] = {
        "lr": _LR,
        "weight_decay": 1e-4,
        "stage2_trainable": mode,
        "backbone_lr_scale": _SCALE,
    }
    return TwoWayTrainer(model, torch.device("cpu"), cfg)


def _make_supervised_trainer(mode: str, target: str) -> TwoWayTrainer:
    model = build_model(_small_config())
    cfg: Dict[str, Any] = {
        "lr": _LR,
        "weight_decay": 1e-4,
        "stage2_trainable": mode,
        "backbone_lr_scale": _SCALE,
        "stage2_objective": "supervised",
        "supervised_target": target,
    }
    return TwoWayTrainer(model, torch.device("cpu"), cfg)


def _synthetic_batch(batch_size: int = 4, fixed_len: int = 32) -> Dict[str, torch.Tensor]:
    """Tiny two-way batch matching the collate schema (bytes 0..255, no PAD)."""
    header = torch.randint(0, 256, (batch_size, fixed_len), dtype=torch.long)
    body = torch.randint(0, 256, (batch_size, fixed_len), dtype=torch.long)
    return {
        "header_ids": header,
        "body_ids": body,
        "header_mask": header.ne(PAD_IDX),
        "body_mask": body.ne(PAD_IDX),
        "alerted": torch.tensor([0.0, 1.0, 0.0, 1.0]),
        "is_attack": torch.tensor([1.0, 1.0, 0.0, 0.0]),
        "loss_weight": torch.ones(batch_size),
        "pseudo_positive": torch.zeros(batch_size, dtype=torch.long),
    }


# ─── name helpers ────────────────────────────────────


def _all_names(trainer: TwoWayTrainer) -> Set[str]:
    return {n for n, _ in trainer.model.named_parameters()}


def _trainable_names(trainer: TwoWayTrainer) -> Set[str]:
    return {n for n, p in trainer.model.named_parameters() if p.requires_grad}


def _frozen_names(trainer: TwoWayTrainer) -> Set[str]:
    return {n for n, p in trainer.model.named_parameters() if not p.requires_grad}


def _ok(label: str) -> None:
    print(f"  [ok] {label}")


# ─── per-mode boundary assertions ────────────────────


def _check_full() -> None:
    trainer = _make_trainer("full")
    groups = trainer._setup_stage2_trainability()
    names = _all_names(trainer)

    assert _trainable_names(trainer) == names, "full: all params must be trainable"
    assert _frozen_names(trainer) == set(), "full: no params may be frozen"
    assert len(groups) == 1, f"full: expected 1 group, got {len(groups)}"
    assert groups[0].get("lr", trainer.lr) == trainer.lr, "full: group lr must be lr"
    assert trainer._frozen_modules == [], "full: no frozen modules"

    trainer.backbone.train()
    trainer.heads.train()
    trainer._set_frozen_eval()
    assert trainer.backbone.training is True, "full: backbone should stay in train()"
    assert trainer.heads.training is True, "full: heads should stay in train()"
    _ok("full")


def _check_head() -> None:
    trainer = _make_trainer("head")
    groups = trainer._setup_stage2_trainability()
    names = _all_names(trainer)

    expected_trainable = {n for n in names if n.startswith("heads.")}
    expected_frozen = {n for n in names if n.startswith("backbone.")}
    assert _trainable_names(trainer) == expected_trainable, (
        "head: only heads.* may be trainable"
    )
    assert _frozen_names(trainer) == expected_frozen, (
        "head: the whole backbone must be frozen"
    )
    assert len(groups) == 1, f"head: expected 1 group, got {len(groups)}"
    assert groups[0].get("lr", trainer.lr) == trainer.lr, "head: group lr must be lr"

    trainer.backbone.train()
    trainer.heads.train()
    trainer._set_frozen_eval()
    assert trainer.backbone.training is False, "head: frozen backbone must be eval()"
    assert trainer.heads.training is True, "head: heads must stay in train()"
    _ok("head")


def _check_head_last_block() -> None:
    trainer = _make_trainer("head_last_block")
    groups = trainer._setup_stage2_trainability()
    names = _all_names(trainer)

    def is_trainable(n: str) -> bool:
        return (
            n.startswith("backbone.enc_h.blocks.3.")
            or n.startswith("backbone.enc_b.blocks.3.")
            or n.startswith("backbone.fusion.")
            or n.startswith("heads.")
        )

    expected_trainable = {n for n in names if is_trainable(n)}
    trainable = _trainable_names(trainer)
    frozen = _frozen_names(trainer)

    assert trainable == expected_trainable, (
        "head_last_block: trainable set must be exactly "
        "{enc_h.blocks.3, enc_b.blocks.3, fusion, heads}\n"
        f"  unexpected trainable: {sorted(trainable - expected_trainable)}\n"
        f"  missing trainable:    {sorted(expected_trainable - trainable)}"
    )
    assert frozen == (names - expected_trainable), "head_last_block: frozen mismatch"

    # The deeper encoder layers must be frozen.
    required_frozen = [
        "backbone.enc_h.emb", "backbone.enc_h.stem",
        "backbone.enc_h.blocks.0.", "backbone.enc_h.blocks.1.",
        "backbone.enc_h.blocks.2.", "backbone.enc_h.proj.",
        "backbone.enc_b.emb", "backbone.enc_b.stem",
        "backbone.enc_b.blocks.0.", "backbone.enc_b.blocks.1.",
        "backbone.enc_b.blocks.2.", "backbone.enc_b.proj.",
    ]
    for pref in required_frozen:
        hits = {n for n in frozen if n.startswith(pref)}
        assert hits, f"head_last_block: expected frozen params under {pref!r}"
        assert not (hits & trainable), f"head_last_block: {pref!r} leaked into trainable"

    assert len(groups) == 1, f"head_last_block: expected 1 group, got {len(groups)}"
    assert groups[0].get("lr", trainer.lr) == trainer.lr, (
        "head_last_block: group lr must be lr"
    )

    trainer.backbone.train()
    trainer.heads.train()
    trainer._set_frozen_eval()
    assert trainer.backbone.enc_h.blocks[3].training is True, "hlb: enc_h.blocks[3] train"
    assert trainer.backbone.enc_b.blocks[3].training is True, "hlb: enc_b.blocks[3] train"
    assert trainer.backbone.fusion.training is True, "hlb: fusion train"
    assert trainer.heads.training is True, "hlb: heads train"
    assert trainer.backbone.enc_h.blocks[0].training is False, "hlb: enc_h.blocks[0] eval"
    assert trainer.backbone.enc_h.proj.training is False, "hlb: enc_h.proj eval"
    assert trainer.backbone.enc_b.blocks[2].training is False, "hlb: enc_b.blocks[2] eval"
    _ok("head_last_block")


def _check_backbone_low_lr() -> None:
    trainer = _make_trainer("backbone_low_lr")
    groups = trainer._setup_stage2_trainability()
    names = _all_names(trainer)

    assert _trainable_names(trainer) == names, "backbone_low_lr: all params trainable"
    assert _frozen_names(trainer) == set(), "backbone_low_lr: nothing frozen"
    assert len(groups) == 2, f"backbone_low_lr: expected 2 groups, got {len(groups)}"
    assert trainer._frozen_modules == [], "backbone_low_lr: no frozen modules"

    backbone_ids = {id(p) for p in trainer.backbone.parameters()}
    heads_ids = {id(p) for p in trainer.heads.parameters()}
    expected_backbone_lr = trainer.lr * trainer.backbone_lr_scale

    saw_backbone = saw_heads = False
    for g in groups:
        pids = {id(p) for p in g["params"]}
        if pids <= backbone_ids:
            saw_backbone = True
            assert abs(g["lr"] - expected_backbone_lr) < 1e-12, (
                f"backbone_low_lr: backbone group lr={g['lr']} != "
                f"lr*scale={expected_backbone_lr}"
            )
        elif pids <= heads_ids:
            saw_heads = True
            assert abs(g.get("lr", trainer.lr) - trainer.lr) < 1e-12, (
                "backbone_low_lr: heads group lr must be lr"
            )
        else:
            raise AssertionError("backbone_low_lr: group mixes backbone and heads params")
    assert saw_backbone and saw_heads, "backbone_low_lr: need one backbone + one heads group"

    trainer.backbone.train()
    trainer.heads.train()
    trainer._set_frozen_eval()
    assert trainer.backbone.training is True, "backbone_low_lr: backbone stays train()"
    assert trainer.heads.training is True, "backbone_low_lr: heads stays train()"
    _ok("backbone_low_lr")


def _check_invalid_mode() -> None:
    raised = False
    try:
        _make_trainer("not_a_mode")
    except ValueError:
        raised = True
    assert raised, "invalid stage2_trainable should raise ValueError"
    _ok("invalid-mode rejected")


def _check_freeze_backbone_alias() -> None:
    # Legacy alias: freeze_backbone=True with no explicit mode → "head".
    model = build_model(_small_config())
    trainer = TwoWayTrainer(
        model, torch.device("cpu"),
        {"lr": _LR, "freeze_backbone": True},
    )
    assert trainer.stage2_trainable == "head", (
        "freeze_backbone=True must alias to 'head' mode"
    )
    _ok("freeze_backbone→head alias")


# ─── supervised objective checks ─────────────────────


def _check_supervised_default_is_pu() -> None:
    # Backward compat: absent stage2_objective ⇒ "pu", no supervised_target.
    model = build_model(_small_config())
    trainer = TwoWayTrainer(model, torch.device("cpu"), {"lr": _LR})
    assert trainer.stage2_objective == "pu", (
        "absent stage2_objective must default to 'pu'"
    )
    assert trainer.supervised_target is None, (
        "pu objective must leave supervised_target unset"
    )
    _ok("stage2_objective default → pu")


def _check_supervised_step(target: str) -> None:
    """One forward+backward of the supervised path; assert grad isolation.

    Uses ``head_last_block`` so there is a real frozen/trainable split, making
    the "only ``_trainable_params`` receive grads" assertion meaningful.
    """
    trainer = _make_supervised_trainer("head_last_block", target)
    assert trainer.stage2_objective == "supervised"
    assert trainer.supervised_target == target

    param_groups = trainer._setup_stage2_trainability()
    trainer._reset_optimizer(param_groups=param_groups)

    trainer.backbone.train()
    trainer.heads.train()
    trainer._set_frozen_eval()

    batch = _synthetic_batch()
    z = trainer.backbone(batch)
    out = trainer.heads(z)
    loss = F.binary_cross_entropy_with_logits(out["risk_logit"], batch[target])
    assert torch.isfinite(loss), f"supervised BCE loss must be finite (target={target})"

    trainer.optim.zero_grad(set_to_none=True)
    loss.backward()

    trainable_ids = {id(p) for p in trainer._trainable_params}
    got_grad = 0
    for name, p in trainer.model.named_parameters():
        if not p.requires_grad:
            assert p.grad is None, (
                f"frozen param {name} received a grad (target={target})"
            )
        if p.grad is not None:
            assert id(p) in trainable_ids, (
                f"{name} received a grad but is not in _trainable_params "
                f"(target={target})"
            )
            got_grad += 1
    assert got_grad > 0, f"no trainable param received a grad (target={target})"

    # The optimizer step must run cleanly over the trainable params only.
    torch.nn.utils.clip_grad_norm_(trainer._trainable_params, trainer.clip_grad)
    trainer.optim.step()
    _ok(f"supervised step target={target}")


def _check_supervised_invalid_target() -> None:
    # Missing target and out-of-vocab targets must both raise ValueError.
    for bad in (None, "risk", "foo", "proj"):
        cfg: Dict[str, Any] = {"lr": _LR, "stage2_objective": "supervised"}
        if bad is not None:
            cfg["supervised_target"] = bad
        raised = False
        try:
            TwoWayTrainer(build_model(_small_config()), torch.device("cpu"), cfg)
        except ValueError:
            raised = True
        assert raised, f"supervised_target={bad!r} should raise ValueError"
    _ok("supervised invalid/missing target rejected")


def _check_invalid_objective() -> None:
    raised = False
    try:
        TwoWayTrainer(
            build_model(_small_config()), torch.device("cpu"),
            {"lr": _LR, "stage2_objective": "not_an_objective"},
        )
    except ValueError:
        raised = True
    assert raised, "invalid stage2_objective should raise ValueError"
    _ok("invalid stage2_objective rejected")


def main() -> None:
    print("Stage-2 trainability smoke test")
    _check_full()
    _check_head()
    _check_head_last_block()
    _check_backbone_low_lr()
    _check_invalid_mode()
    _check_freeze_backbone_alias()
    print("SMOKE OK")

    print("Stage-2 supervised-objective smoke test")
    _check_supervised_default_is_pu()
    _check_supervised_step("alerted")
    _check_supervised_step("is_attack")
    _check_supervised_invalid_target()
    _check_invalid_objective()
    print("SUPERVISED SMOKE OK")


if __name__ == "__main__":
    main()
