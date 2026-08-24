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

from ..data.common import augment_ids, concat_batches, to_device
from .base import BaseTrainer, EarlyStopper
from .losses import contrastive_nt_xent, nnpu_loss, unlabeled_prior_from_pool
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
        steps_per_epoch = training_cfg.get("stage2_steps_per_epoch")
        self.stage2_steps_per_epoch = (
            int(steps_per_epoch) if steps_per_epoch is not None else None
        )
        if self.stage2_steps_per_epoch is not None and self.stage2_steps_per_epoch < 1:
            raise ValueError("stage2_steps_per_epoch must be positive when set")

        self.w_ssl = float(training_cfg.get("w_ssl", 1.0))
        self.w_alert = float(training_cfg.get("w_alert", 0.2))
        self.w_pu = float(training_cfg.get("w_pu", 1.0))
        self.pi_p = float(training_cfg.get("pi_p", training_cfg.get("pu_prior", 0.10)))
        self.temp = float(training_cfg.get("temp", 0.2))

        # ── nnPU prior scope + de-fitting controls ──────
        # nnPU needs the positive prior *within* the unlabeled sample. Configs
        # normally state the pool-wide prior, so "pool" (the default) converts
        # it using the observed |P| / |U| sizes; "unlabeled" passes it through.
        self.pi_p_scope = str(training_cfg.get("pi_p_scope", "pool"))
        if self.pi_p_scope not in {"pool", "unlabeled"}:
            raise ValueError(
                "pi_p_scope must be 'pool' or 'unlabeled'; "
                f"got {self.pi_p_scope!r}"
            )
        self.pi_p_effective = self.pi_p
        self.nnpu_beta = float(training_cfg.get("nnpu_beta", 0.0))
        self.nnpu_gamma = float(training_cfg.get("nnpu_gamma", 1.0))

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

        valid_modes = {
            "head", "head_last_block", "backbone_hybrid",
            "backbone_low_lr", "full",
        }
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

        # ── Stage-2 objective (PU vs supervised baselines) ──────────────
        # "pu" (default) preserves the nnPU + SSL + alert-aux multitask loop.
        # "supervised" runs plain BCE on the risk head against a chosen target
        # so teacher-copy (alerted) and oracle (is_attack) baselines can be
        # trained on the SAME architecture and trainability modes as the PU
        # method.  Absent key ⇒ "pu" ⇒ byte-for-byte the original behaviour.
        self.stage2_objective = str(training_cfg.get("stage2_objective", "pu"))
        valid_objectives = {"pu", "supervised"}
        if self.stage2_objective not in valid_objectives:
            raise ValueError(
                "stage2_objective must be one of "
                f"{sorted(valid_objectives)}; got {self.stage2_objective!r}"
            )

        # ``supervised_target`` is required iff the objective is supervised.
        self.supervised_target: Optional[str] = None
        _raw_target = training_cfg.get("supervised_target", None)
        if self.stage2_objective == "supervised":
            if _raw_target is None:
                raise ValueError(
                    "supervised_target is required when "
                    "stage2_objective='supervised' (choose 'alerted' or "
                    "'is_attack')"
                )
            self.supervised_target = str(_raw_target)
            if self.supervised_target not in {"alerted", "is_attack"}:
                raise ValueError(
                    "supervised_target must be 'alerted' or 'is_attack'; "
                    f"got {self.supervised_target!r}"
                )

        # Supervised batch composition. "natural" draws from the raw training
        # distribution; "match_pu" reuses the nnPU P/U batch pairing so both
        # objectives see the same number of positives per step.
        self.supervised_batch_balance = str(
            training_cfg.get("supervised_batch_balance", "natural")
        )
        if self.supervised_batch_balance not in {"natural", "match_pu"}:
            raise ValueError(
                "supervised_batch_balance must be 'natural' or 'match_pu'; "
                f"got {self.supervised_batch_balance!r}"
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

    @staticmethod
    def _next_batch(loader: DataLoader, iterator: Any) -> Tuple[Any, Any]:
        """Return the next batch, restarting the loader after exhaustion."""
        try:
            return next(iterator), iterator
        except StopIteration:
            iterator = iter(loader)
            try:
                return next(iterator), iterator
            except StopIteration as exc:
                raise ValueError("Stage-2 training loader must not be empty") from exc

    @staticmethod
    def _loader_records(loader: DataLoader) -> Optional[list]:
        dataset = getattr(loader, "dataset", None)
        return getattr(dataset, "records", None)

    @classmethod
    def _count_alerted(cls, loader: DataLoader) -> Optional[int]:
        records = cls._loader_records(loader)
        if records is None:
            return None
        return sum(1 for r in records if int(r.get("alerted", 0)) == 1)

    def _resolve_pu_prior(self, n_p: int, n_u: int) -> float:
        """Return the prior to feed nnPU, converting pool scope when needed."""
        if self.pi_p_scope == "unlabeled":
            logger.info(
                "PU prior: using configured unlabeled-scope pi=%.4f "
                "(|P|=%d, |U|=%d)", self.pi_p, n_p, n_u,
            )
            return self.pi_p

        pi_u = unlabeled_prior_from_pool(self.pi_p, n_p, n_u)
        logger.info(
            "PU prior: pool pi=%.4f -> unlabeled pi=%.4f (|P|=%d, |U|=%d); "
            "nnPU requires the prior inside U",
            self.pi_p, pi_u, n_p, n_u,
        )
        return pi_u

    @staticmethod
    def _log_positive_exposure(
        objective: str, positives_per_epoch: float, n_p: int,
    ) -> None:
        passes = positives_per_epoch / max(n_p, 1)
        logger.info(
            "Positive exposure [%s]: ~%.0f positive samples/epoch = %.2f "
            "pass(es) over |P|=%d",
            objective, positives_per_epoch, passes, n_p,
        )

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
        backbone_hybrid
            Freeze emb/stem/blocks[0:2]/proj of each encoder (SSL-pretrained
            dilation-1/2 features preserved) and unfreeze blocks[2]+blocks[3]
            (dilation-4 and dilation-8) of each encoder, the fusion MLP, and
            all heads; one group at ``self.lr``.  Gives ~2 extra TCN blocks of
            capacity beyond head_last_block to separate REGISTER/INVITE score
            regions while keeping early SSL features intact.
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

        elif mode == "backbone_hybrid":
            for p in self.backbone.parameters():
                p.requires_grad_(False)
            unfrozen = [
                self.backbone.enc_h.blocks[2], self.backbone.enc_h.blocks[3],
                self.backbone.enc_b.blocks[2], self.backbone.enc_b.blocks[3],
                self.backbone.fusion, self.heads,
            ]
            for m in unfrozen:
                for p in m.parameters():
                    p.requires_grad_(True)
            # Frozen: emb, stem, blocks[0:2], proj in each encoder (SSL kept).
            frozen_modules = [
                self.backbone.enc_h.emb, self.backbone.enc_h.stem,
                self.backbone.enc_h.blocks[0], self.backbone.enc_h.blocks[1],
                self.backbone.enc_h.proj,
                self.backbone.enc_b.emb, self.backbone.enc_b.stem,
                self.backbone.enc_b.blocks[0], self.backbone.enc_b.blocks[1],
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
        loader_train: DataLoader,
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

        # The auxiliary head is only informative if the teacher flag varies.
        w_alert = self.w_alert
        n_alerted = self._count_alerted(loader_train)
        if w_alert > 0.0 and n_alerted == 0:
            logger.warning(
                "Stage-1 auxiliary alert target is constant zero (the loader "
                "holds no alerted=1 records); disabling it. Pretrain over the "
                "full train split to keep this term meaningful."
            )
            w_alert = 0.0

        for epoch in range(self.max_epochs_pretrain):
            if stop_flag and stop_flag():
                logger.info("Stop signal; exiting pretrain.")
                break

            self.backbone.train()
            self.heads.train()
            total_loss = 0.0
            n = 0

            for batch in loader_train:
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
                loss = self.w_ssl * loss_ssl
                if w_alert > 0.0:
                    loss = loss + w_alert * F.binary_cross_entropy_with_logits(
                        out1["alerted_logit"], batch["alerted"],
                    )

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
        n_p = len(loader_p.dataset)
        n_u = len(loader_u.dataset)
        self.pi_p_effective = self._resolve_pu_prior(n_p, n_u)
        param_groups = self._setup_stage2_trainability()
        self._reset_optimizer(param_groups=param_groups)
        stopper = EarlyStopper(patience=self.patience, mode="max")
        best_path = out_dir / "model_best.pt"
        best_pr_auc = -1.0
        best_val: Dict[str, float] = {}
        steps_per_epoch = self.stage2_steps_per_epoch or len(loader_p)
        self._log_positive_exposure(
            "nnPU", steps_per_epoch * loader_p.batch_size, n_p,
        )

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
            n_defit = 0

            iter_p = iter(loader_p)
            iter_u = iter(loader_u)
            steps_this_epoch = self.stage2_steps_per_epoch or len(loader_p)
            for _ in range(steps_this_epoch):
                if stop_flag and stop_flag():
                    break
                batch_p, iter_p = self._next_batch(loader_p, iter_p)
                batch_u, iter_u = self._next_batch(loader_u, iter_u)

                batch_p = to_device(batch_p, self.device)
                batch_u = to_device(batch_u, self.device)

                # --- Pass 1: PU + alert (backward frees this graph) ---
                z_p = self.backbone(batch_p)
                z_u = self.backbone(batch_u)
                out_p = self.heads(z_p)
                out_u = self.heads(z_u)

                loss_pu, pu_stats = nnpu_loss(
                    out_p["risk_logit"], out_u["risk_logit"],
                    pi_p=self.pi_p_effective,
                    p_weights=batch_p.get("loss_weight"),
                    beta=self.nnpu_beta,
                    gamma=self.nnpu_gamma,
                )
                n_defit += int(pu_stats["defitting"])
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
                "[nnPU epoch %d] steps=%d loss=%.4f %s=%.4f bestF1=%.4f "
                "fn_recall=%.4f thr=%.3f lr=%.2e defit=%.0f%%",
                epoch, n, total / max(1, n), self.best_metric, metric_val,
                val_stats["best_f1"], fn_recall,
                val_stats["best_threshold"], lr, 100.0 * n_defit / max(1, n),
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

    # ── Stage 2 (baseline): supervised BCE on the risk head ─────────

    def train_supervised(
        self,
        loader_train: DataLoader,
        loader_val: DataLoader,
        out_dir: Path,
        stop_flag: Optional[Callable[[], bool]] = None,
        loader_p: Optional[DataLoader] = None,
        loader_u: Optional[DataLoader] = None,
    ) -> Tuple[Dict[str, float], Path]:
        """Fully-supervised BCE baseline on the risk head.

        Trains ``heads.risk`` with plain ``BCEWithLogitsLoss`` against
        ``batch[self.supervised_target]`` (``alerted`` → teacher-copy of Snort,
        ``is_attack`` → oracle upper bound).  There is NO nnPU term, NO SSL
        regulariser, NO alert-aux term.

        Batch composition follows ``supervised_batch_balance``: ``"natural"``
        draws from the raw training distribution via ``loader_train``, while
        ``"match_pu"`` pairs a P batch with a U batch exactly as ``train_pu``
        does, so both objectives see the same positives per step.

        Everything else mirrors :meth:`train_pu` so the two objectives are
        directly comparable: the same ``_setup_stage2_trainability`` /
        ``_reset_optimizer`` path, the same ``best_metric`` checkpointing to
        ``model_best.pt``, the same per-epoch ``model_ep{e}.pt`` gating, the
        same ``disable_early_stop`` / ``disable_plateau_sched`` handling, and
        ``model_last.pt`` at the end.  Evaluation reuses
        :func:`eval_on_loader` unchanged.

        Returns ``(best_val, best_path)`` — identical contract to ``train_pu``.
        """
        assert self.supervised_target in {"alerted", "is_attack"}, (
            "train_supervised requires supervised_target in {'alerted', "
            f"'is_attack'}}; got {self.supervised_target!r}"
        )
        paired = self.supervised_batch_balance == "match_pu"
        if paired and (loader_p is None or loader_u is None):
            raise ValueError(
                "supervised_batch_balance='match_pu' requires both loader_p "
                "and loader_u"
            )
        logger.info(
            "== Stage 2: supervised BCE training (%d epochs, target=%s, "
            "batching=%s) ==",
            self.max_epochs_pu, self.supervised_target,
            self.supervised_batch_balance,
        )
        param_groups = self._setup_stage2_trainability()
        self._reset_optimizer(param_groups=param_groups)
        stopper = EarlyStopper(patience=self.patience, mode="max")
        best_path = out_dir / "model_best.pt"
        best_pr_auc = -1.0
        best_val: Dict[str, float] = {}

        primary_loader = loader_p if paired else loader_train
        steps_per_epoch = self.stage2_steps_per_epoch or len(primary_loader)
        n_alerted = self._count_alerted(loader_train) or 0
        if paired:
            positives_per_epoch = float(steps_per_epoch * loader_p.batch_size)
        else:
            n_total = max(len(loader_train.dataset), 1)
            positives_per_epoch = (
                steps_per_epoch * loader_train.batch_size * n_alerted / n_total
            )
        self._log_positive_exposure(
            f"supervised/{self.supervised_target}", positives_per_epoch,
            max(n_alerted, 1),
        )

        for epoch in range(self.max_epochs_pu):
            if stop_flag and stop_flag():
                logger.info("Stop signal; exiting supervised training.")
                break

            self.backbone.train()
            self.heads.train()
            # Keep fully-frozen submodules deterministic (no dropout); no-op for
            # "full"/"backbone_low_lr".
            self._set_frozen_eval()
            total = 0.0
            n = 0

            iter_train = iter(primary_loader)
            iter_u = iter(loader_u) if paired else None
            steps_this_epoch = steps_per_epoch
            for _ in range(steps_this_epoch):
                if stop_flag and stop_flag():
                    break
                batch, iter_train = self._next_batch(primary_loader, iter_train)
                if paired:
                    batch_u, iter_u = self._next_batch(loader_u, iter_u)
                    batch = concat_batches(batch, batch_u)
                batch = to_device(batch, self.device)

                z = self.backbone(batch)
                out = self.heads(z)
                loss = F.binary_cross_entropy_with_logits(
                    out["risk_logit"], batch[self.supervised_target],
                )

                self.optim.zero_grad(set_to_none=True)
                if torch.isfinite(loss):
                    loss.backward()
                    if self.clip_grad:
                        torch.nn.utils.clip_grad_norm_(
                            self._trainable_params, self.clip_grad,
                        )
                    self.optim.step()
                else:
                    logger.warning(
                        "Non-finite supervised loss; skipping optimizer step."
                    )

                total += float(loss.detach())
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
                "[supervised epoch %d] steps=%d loss=%.4f %s=%.4f bestF1=%.4f "
                "fn_recall=%.4f thr=%.3f lr=%.2e",
                epoch, n, total / max(1, n), self.best_metric, metric_val,
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
