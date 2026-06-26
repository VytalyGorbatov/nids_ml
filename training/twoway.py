"""
2-Stage trainer for the 2-Way ByteTCN.

Stage 1: Contrastive SSL pretraining with auxiliary IDS-structured tasks.
Stage 2: nnPU multitask training with optional SSL regulariser.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from ..data.common import augment_ids, to_device
from .base import BaseTrainer, EarlyStopper
from .losses import contrastive_nt_xent, nnpu_loss
from .metrics import pr_curve_best_f1, snort_fn_metrics
from ..models.tcn_2way import ByteTCN2WayClassifier, ByteTCNBackbone, Heads

logger = logging.getLogger(__name__)


# ─── Evaluation helpers ──────────────────────────────


@torch.no_grad()
def eval_on_loader(
    backbone: ByteTCNBackbone,
    heads: Heads,
    loader: DataLoader,
    device: torch.device,
) -> Dict[str, float]:
    backbone.eval()
    heads.eval()
    all_scores: list[torch.Tensor] = []
    all_y: list[torch.Tensor] = []
    all_alerted: list[torch.Tensor] = []

    for batch in loader:
        batch = to_device(batch, device)
        z = backbone(batch)
        out = heads(z)
        all_scores.append(torch.sigmoid(out["risk_logit"]))
        all_y.append(batch["is_attack"])
        if "alerted" in batch:
            all_alerted.append(batch["alerted"])

    if not all_scores:
        return {
            "best_threshold": 0.5, "best_f1": 0.0, "pr_auc": 0.0,
            "precision_at_best": 0.0, "recall_at_best": 0.0,
            "snort_fn_recall": 0.0,
        }

    scores = torch.cat(all_scores)
    y = torch.cat(all_y)
    result = pr_curve_best_f1(scores, y)

    # Snort FN recovery at the best threshold
    if all_alerted:
        alerted = torch.cat(all_alerted)
        fn_stats = snort_fn_metrics(scores, y, alerted, result["best_threshold"])
        result.update(fn_stats)

    return result

@torch.no_grad()
def eval_on_loader_at_threshold(
    backbone: ByteTCNBackbone,
    heads: Heads,
    loader: DataLoader,
    device: torch.device,
    threshold: float,
) -> Dict[str, float]:
    """Evaluate using a fixed decision threshold (e.g. from validation)."""
    backbone.eval()
    heads.eval()
    all_scores: list[torch.Tensor] = []
    all_y: list[torch.Tensor] = []

    for batch in loader:
        batch = to_device(batch, device)
        z = backbone(batch)
        out = heads(z)
        all_scores.append(torch.sigmoid(out["risk_logit"]))
        all_y.append(batch["is_attack"])

    if not all_scores:
        return {
            "threshold": threshold, "f1": 0.0, "pr_auc": 0.0,
            "precision": 0.0, "recall": 0.0,
        }

    scores = torch.cat(all_scores)
    y_true = torch.cat(all_y)
    preds = (scores >= threshold).float()
    tp = (preds * y_true).sum()
    fp = (preds * (1 - y_true)).sum()
    fn = ((1 - preds) * y_true).sum()
    precision = tp / (tp + fp).clamp_min(1.0)
    recall = tp / (tp + fn).clamp_min(1.0)
    f1 = 2 * precision * recall / (precision + recall).clamp_min(1e-12)

    # Also report the sweep-based pr_auc for reference
    sweep = pr_curve_best_f1(scores, y_true)

    return {
        "threshold": threshold,
        "f1": float(f1.item()),
        "precision": float(precision.item()),
        "recall": float(recall.item()),
        "pr_auc": sweep["pr_auc"],
        "best_f1_sweep": sweep["best_f1"],
        "best_threshold_sweep": sweep["best_threshold"],
    }

# ─── Trainer ─────────────────────────────────────────


class TwoWayTrainer(BaseTrainer):
    """Manages the 2-stage pretrain → nnPU training loop."""

    def __init__(
        self,
        model: ByteTCN2WayClassifier,
        device: torch.device,
        training_cfg: Dict[str, Any],
    ) -> None:
        super().__init__(device, training_cfg)

        self.model = model.to(device)
        self.backbone = model.backbone
        self.heads = model.heads

        self.lr = float(training_cfg.get("lr", training_cfg.get("learning_rate", 3e-4)))
        self.weight_decay = float(training_cfg.get("weight_decay", 1e-4))
        self.max_epochs_pretrain = int(training_cfg.get("max_epochs_pretrain", 5))
        self.max_epochs_pu = int(training_cfg.get("max_epochs_pu", 10))

        self.w_ssl = float(training_cfg.get("w_ssl", 1.0))
        self.w_alert = float(training_cfg.get("w_alert", 0.2))
        self.w_pu = float(training_cfg.get("w_pu", 1.0))
        self.pi_p = float(training_cfg.get("pi_p", training_cfg.get("pu_prior", 0.10)))
        self.temp = float(training_cfg.get("temp", 0.2))

        self.all_params = list(self.model.parameters())
        self.sched_cfg = {"factor": 0.5, "patience": 3, "min_lr": 1e-6}
        self.best_metric = str(training_cfg.get("best_metric", "pr_auc"))

        # ── Stage-2 trainability controls ───────────────
        # ``freeze_backbone`` (legacy) is kept as a backward-compatible alias:
        # when True and no explicit ``stage2_trainable`` is given it maps to the
        # "head" mode (heads-only updates).  An explicit ``stage2_trainable``
        # always wins.
        self.freeze_backbone = bool(training_cfg.get("freeze_backbone", False))
        explicit_mode = training_cfg.get("stage2_trainable", None)
        if explicit_mode is not None:
            self.stage2_trainable = str(explicit_mode)
        elif self.freeze_backbone:
            self.stage2_trainable = "head"
        else:
            self.stage2_trainable = "full"

        valid_modes = {"head", "head_last_block", "backbone_low_lr", "full"}
        if self.stage2_trainable not in valid_modes:
            raise ValueError(
                "stage2_trainable must be one of "
                f"{sorted(valid_modes)}; got {self.stage2_trainable!r}"
            )

        # Used only by the "backbone_low_lr" mode.
        self.backbone_lr_scale = float(training_cfg.get("backbone_lr_scale", 0.1))
        # Campaign flags (default off → original behaviour preserved).
        self.save_epoch_checkpoints = bool(
            training_cfg.get("save_epoch_checkpoints", False)
        )
        self.disable_early_stop = bool(training_cfg.get("disable_early_stop", False))
        self.disable_plateau_sched = bool(
            training_cfg.get("disable_plateau_sched", False)
        )

        # Populated by ``_setup_stage2_trainability`` at the start of train_pu.
        self._trainable_params: list = self.all_params
        self._frozen_modules: list = []

    # ── helpers ─────────────────────────────────────

    def _make_augmented_view(
        self, batch: Dict[str, torch.Tensor],
    ) -> Dict[str, torch.Tensor]:
        """Return a copy of *batch* with augmented header/body ids."""
        h, hm = augment_ids(batch["header_ids"], batch["header_mask"])
        b, bm = augment_ids(batch["body_ids"], batch["body_mask"])
        view = dict(batch)
        view["header_ids"], view["header_mask"] = h, hm
        view["body_ids"], view["body_mask"] = b, bm
        return view

    def load_pretrained(self, path: Path) -> None:
        """Load backbone + heads weights from a pretrain checkpoint."""
        ckpt = torch.load(path, map_location=self.device, weights_only=True)
        self.backbone.load_state_dict(ckpt["backbone"])
        self.heads.load_state_dict(ckpt["heads"])
        logger.info("Loaded pretrained checkpoint from %s", path)

    def _reset_optimizer(self, param_groups=None, use_adamw: bool = True) -> None:
        """Create a fresh optimizer + scheduler.

        If ``param_groups`` (a list of param-group dicts) is supplied, it is
        passed straight to the optimizer so per-group ``lr`` keys are honoured;
        the constructor-level ``self.lr`` is then only the default for groups
        that omit ``lr``.  When ``param_groups`` is None all model parameters
        are optimized at ``self.lr`` (legacy behaviour, used by ``pretrain``).
        """
        params = param_groups if param_groups is not None else self.all_params
        self.optim = self._init_optimizer(
            params, self.lr, self.weight_decay, use_adamw=use_adamw,
        )
        self.sched = self._init_scheduler(
            self.optim, self.sched_cfg, mode="max",
        )

    def _do_optim_step(self, loss: torch.Tensor) -> None:
        self._optim_step(loss, self.optim, self.all_params)

    # ── Stage 2 trainability / plasticity ───────────

    def _setup_stage2_trainability(self) -> list:
        """Configure ``requires_grad`` per Stage-2 mode and return param-groups.

        Modes
        -----
        full
            Every parameter trainable; one group at ``self.lr``.
        head
            Whole backbone frozen, heads trainable; one group at ``self.lr``.
        head_last_block
            Freeze everything except the dilation-8 (last) ResTCN block of each
            encoder, the fusion MLP, and all heads; one group at ``self.lr``.
        backbone_low_lr
            All parameters trainable; two groups — backbone at
            ``self.lr * self.backbone_lr_scale`` and heads at ``self.lr``.

        Side effects
        ------------
        Sets ``self._trainable_params`` (flat list of params with
        ``requires_grad=True``, used for gradient clipping) and
        ``self._frozen_modules`` (fully-frozen ``nn.Module`` list, forced to
        ``eval()`` each epoch by ``_set_frozen_eval``).
        """
        mode = self.stage2_trainable

        # Start from a clean slate: everything trainable, then freeze per mode.
        for p in self.model.parameters():
            p.requires_grad_(True)

        frozen_modules: list = []

        if mode == "full":
            param_groups = [
                {"params": [p for p in self.model.parameters() if p.requires_grad]},
            ]

        elif mode == "head":
            for p in self.backbone.parameters():
                p.requires_grad_(False)
            frozen_modules = [self.backbone]
            param_groups = [{"params": list(self.heads.parameters())}]

        elif mode == "head_last_block":
            for p in self.backbone.parameters():
                p.requires_grad_(False)
            unfrozen = [
                self.backbone.enc_h.blocks[3],
                self.backbone.enc_b.blocks[3],
                self.backbone.fusion,
                self.heads,
            ]
            for m in unfrozen:
                for p in m.parameters():
                    p.requires_grad_(True)
            # Still frozen in each encoder: emb, stem, blocks 0-2, proj.
            frozen_modules = [
                self.backbone.enc_h.emb,
                self.backbone.enc_h.stem,
                self.backbone.enc_h.blocks[0],
                self.backbone.enc_h.blocks[1],
                self.backbone.enc_h.blocks[2],
                self.backbone.enc_h.proj,
                self.backbone.enc_b.emb,
                self.backbone.enc_b.stem,
                self.backbone.enc_b.blocks[0],
                self.backbone.enc_b.blocks[1],
                self.backbone.enc_b.blocks[2],
                self.backbone.enc_b.proj,
            ]
            param_groups = [
                {"params": [p for p in self.model.parameters() if p.requires_grad]},
            ]

        elif mode == "backbone_low_lr":
            backbone_lr = self.lr * self.backbone_lr_scale
            param_groups = [
                {"params": list(self.backbone.parameters()), "lr": backbone_lr},
                {"params": list(self.heads.parameters()), "lr": self.lr},
            ]
            frozen_modules = []

        else:  # pragma: no cover — validated in __init__
            raise ValueError(f"Unknown stage2_trainable mode: {mode!r}")

        self._frozen_modules = frozen_modules
        self._trainable_params = [
            p for p in self.model.parameters() if p.requires_grad
        ]

        n_trainable = sum(p.numel() for p in self._trainable_params)
        n_frozen = sum(
            p.numel() for p in self.model.parameters() if not p.requires_grad
        )
        group_lrs = [float(g.get("lr", self.lr)) for g in param_groups]
        logger.info(
            "Stage-2 trainability: mode=%s | %d group(s) lrs=%s | "
            "trainable=%s params | frozen=%s params",
            mode, len(param_groups), [f"{x:.2e}" for x in group_lrs],
            f"{n_trainable:,}", f"{n_frozen:,}",
        )
        return param_groups

    def _set_frozen_eval(self) -> None:
        """Force fully-frozen submodules into ``eval()`` mode.

        ``train_pu`` calls ``self.backbone.train()`` each epoch, which would
        re-enable dropout inside frozen submodules and make their features
        stochastic.  Putting them back into ``eval()`` keeps frozen features
        deterministic and consistent with inference.  For the "full" and
        "backbone_low_lr" modes ``_frozen_modules`` is empty, so this is a
        no-op.
        """
        for m in getattr(self, "_frozen_modules", []):
            m.eval()

    # ── Stage 1: contrastive pretraining ────────────

    def pretrain(
        self,
        loader_u: DataLoader,
        loader_val: DataLoader,
        out_dir: Path,
        stop_flag: Optional[Callable[[], bool]] = None,
    ) -> Dict[str, float]:
        logger.info(
            "== Stage 1: contrastive pretraining (%d epochs) ==",
            self.max_epochs_pretrain,
        )
        self._reset_optimizer()
        best_val: Dict[str, float] = {}

        for epoch in range(self.max_epochs_pretrain):
            if stop_flag and stop_flag():
                logger.info("Stop signal; exiting pretrain.")
                break

            self.backbone.train()
            self.heads.train()
            total_loss = 0.0
            n = 0

            for batch in loader_u:
                if stop_flag and stop_flag():
                    break
                batch = to_device(batch, self.device)

                view1 = self._make_augmented_view(batch)
                view2 = self._make_augmented_view(batch)

                z1 = self.backbone(view1)
                z2 = self.backbone(view2)
                out1 = self.heads(z1)
                out2 = self.heads(z2)

                loss_ssl = contrastive_nt_xent(
                    out1["proj"], out2["proj"], temperature=self.temp,
                )
                loss_alert = F.binary_cross_entropy_with_logits(
                    out1["alerted_logit"], batch["alerted"],
                )
                loss = self.w_ssl * loss_ssl + self.w_alert * loss_alert

                self._do_optim_step(loss)
                total_loss += float(loss.detach())
                n += 1

            val_stats = eval_on_loader(
                self.backbone, self.heads, loader_val, self.device,
            )
            # No scheduler step during pretraining — pr_auc is not the
            # pretraining objective; decaying LR based on it is harmful.
            best_val = val_stats
            lr = self.optim.param_groups[0]["lr"]
            logger.info(
                "[pretrain epoch %d] loss=%.4f val_pr_auc=%.4f bestF1=%.4f lr=%.2e",
                epoch, total_loss / max(1, n),
                val_stats["pr_auc"], val_stats["best_f1"], lr,
            )

            torch.save(
                {"backbone": self.backbone.state_dict(),
                 "heads": self.heads.state_dict()},
                out_dir / f"pretrain_epoch{epoch}.pt",
            )

        return best_val

    # ── Stage 2: nnPU multitask training ────────────

    def train_pu(
        self,
        loader_p: DataLoader,
        loader_u: DataLoader,
        loader_val: DataLoader,
        out_dir: Path,
        stop_flag: Optional[Callable[[], bool]] = None,
    ) -> Tuple[Dict[str, float], Path]:
        logger.info(
            "== Stage 2: nnPU training (%d epochs, π=%.3f) ==",
            self.max_epochs_pu, self.pi_p,
        )
        param_groups = self._setup_stage2_trainability()
        self._reset_optimizer(param_groups=param_groups)
        stopper = EarlyStopper(patience=self.patience, mode="max")
        best_path = out_dir / "model_best.pt"
        best_pr_auc = -1.0
        best_val: Dict[str, float] = {}

        for epoch in range(self.max_epochs_pu):
            if stop_flag and stop_flag():
                logger.info("Stop signal; exiting nnPU training.")
                break

            self.backbone.train()
            self.heads.train()
            # Keep fully-frozen submodules deterministic (no dropout) so their
            # features match eval time; no-op for "full"/"backbone_low_lr".
            self._set_frozen_eval()
            total = 0.0
            n = 0

            iter_u = iter(loader_u)
            for batch_p in loader_p:
                if stop_flag and stop_flag():
                    break
                try:
                    batch_u = next(iter_u)
                except StopIteration:
                    iter_u = iter(loader_u)
                    batch_u = next(iter_u)

                batch_p = to_device(batch_p, self.device)
                batch_u = to_device(batch_u, self.device)

                # --- Pass 1: PU + alert (backward frees this graph) ---
                z_p = self.backbone(batch_p)
                z_u = self.backbone(batch_u)
                out_p = self.heads(z_p)
                out_u = self.heads(z_u)

                loss_pu, _ = nnpu_loss(
                    out_p["risk_logit"], out_u["risk_logit"], pi_p=self.pi_p,
                )
                loss_alert = (
                    F.binary_cross_entropy_with_logits(
                        out_p["alerted_logit"], batch_p["alerted"],
                    )
                    + F.binary_cross_entropy_with_logits(
                        out_u["alerted_logit"], batch_u["alerted"],
                    )
                ) / 2.0

                loss_main = self.w_pu * loss_pu + self.w_alert * loss_alert
                loss_main.backward()

                # --- Pass 2: SSL regulariser (separate graph, less peak memory) ---
                view1 = self._make_augmented_view(batch_u)
                view2 = self._make_augmented_view(batch_u)
                z1 = self.backbone(view1)
                z2 = self.backbone(view2)
                ssl = contrastive_nt_xent(
                    self.heads(z1)["proj"], self.heads(z2)["proj"],
                    temperature=self.temp,
                )
                loss_ssl = 0.1 * self.w_ssl * ssl
                loss_ssl.backward()

                # --- Single optimizer step (gradients from both passes accumulate) ---
                if self.clip_grad:
                    torch.nn.utils.clip_grad_norm_(
                        self._trainable_params, self.clip_grad,
                    )
                self.optim.step()
                self.optim.zero_grad()

                total += float(loss_main.detach()) + float(loss_ssl.detach())
                n += 1

            val_stats = eval_on_loader(
                self.backbone, self.heads, loader_val, self.device,
            )
            metric_val = val_stats.get(self.best_metric, val_stats["pr_auc"])

            # Per-epoch checkpoint for offline epoch-budget studies.
            if self.save_epoch_checkpoints:
                torch.save(
                    {"backbone": self.backbone.state_dict(),
                     "heads": self.heads.state_dict(),
                     "epoch": epoch,
                     "val_stats": val_stats},
                    out_dir / f"model_ep{epoch}.pt",
                )

            # Plateau scheduler is optional: when disabled the LR stays constant.
            if not self.disable_plateau_sched:
                self._step_scheduler(self.sched, metric_val)
            lr = self.optim.param_groups[0]["lr"]
            fn_recall = val_stats.get("snort_fn_recall", 0.0)
            logger.info(
                "[nnPU epoch %d] loss=%.4f %s=%.4f bestF1=%.4f "
                "fn_recall=%.4f thr=%.3f lr=%.2e",
                epoch, total / max(1, n), self.best_metric, metric_val,
                val_stats["best_f1"], fn_recall,
                val_stats["best_threshold"], lr,
            )

            if metric_val > best_pr_auc:
                best_pr_auc = metric_val
                best_val = val_stats
                torch.save(
                    {"backbone": self.backbone.state_dict(),
                     "heads": self.heads.state_dict(),
                     "best_val": val_stats},
                    best_path,
                )

            # Early stopping is optional: when disabled all epochs run.
            if not self.disable_early_stop and stopper.step(metric_val):
                logger.info("Early stopping triggered.")
                break

        logger.info("Best checkpoint: %s=%.4f", self.best_metric, best_pr_auc)
        torch.save(
            {"backbone": self.backbone.state_dict(),
             "heads": self.heads.state_dict()},
            out_dir / "model_last.pt",
        )
        return best_val, best_path

    # ── Abstract interface implementation ───────────

    def train(
        self,
        loaders: Dict[str, DataLoader],
        out_dir: Path,
        stop_flag: Optional[Callable[[], bool]] = None,
    ) -> Tuple[Dict[str, float], Path]:
        """Full 2-stage training: pretrain then nnPU."""
        self.pretrain(loaders["train_u"], loaders["val"], out_dir, stop_flag=stop_flag)
        return self.train_pu(
            loaders["train_p"], loaders["train_u"], loaders["val"],
            out_dir, stop_flag=stop_flag,
        )

    def evaluate(self, loader: DataLoader) -> Dict[str, float]:
        return eval_on_loader(self.backbone, self.heads, loader, self.device)
