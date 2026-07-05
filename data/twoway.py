"""TwoWayDatasetBuilder — builds P/U/val/test loaders for 2-way training."""
from __future__ import annotations

import functools
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from torch.utils.data import DataLoader, WeightedRandomSampler

from .common import (
    SEP_BYTE,
    DataConfig2Way,
    TwoWayRecordDataset,
    twoway_collate_fn,
)

logger = logging.getLogger(__name__)


# ─── Stratified batch sampler ────────────────────────


class PseudoPositiveBatchSampler:
    """Stratified batch sampler that guarantees a fixed fraction of pseudo-
    positive P samples in every training batch.

    In the nnPU / weak-supervision setting, pseudo-positives (promoted via the
    fuzz miner) are a small minority of the P set.  With a plain random shuffle
    each batch receives roughly ``len(pp) / len(p)`` PP samples, which can be
    below the detection floor when K=770 and batch_size=256.  This sampler
    oversamples pseudo-positives to a configurable fraction while still
    covering native P samples approximately once per epoch.

    Args:
        p_records: Full list of P records (native + promoted), in the same
            order as passed to ``TwoWayRecordDataset``.
        batch_size: Number of samples per batch.
        pp_fraction: Fraction of each batch that should be pseudo-positives.
            Must satisfy ``0 < pp_fraction < 1``.
    """

    def __init__(
        self,
        p_records: List[Dict[str, Any]],
        batch_size: int,
        pp_fraction: float,
    ) -> None:
        self.pp_indices = [
            i for i, r in enumerate(p_records) if r.get("pseudo_positive", 0)
        ]
        self.native_indices = [
            i for i, r in enumerate(p_records) if not r.get("pseudo_positive", 0)
        ]
        if not self.pp_indices:
            raise ValueError(
                "PseudoPositiveBatchSampler: no pseudo_positive records found "
                "in p_records. Enable a pseudo-positive manifest first."
            )
        if not self.native_indices:
            raise ValueError(
                "PseudoPositiveBatchSampler: no native (non-pseudo-positive) "
                "records found in p_records."
            )

        self.batch_size = batch_size
        self.pp_per_batch = max(1, round(batch_size * pp_fraction))
        self.native_per_batch = batch_size - self.pp_per_batch
        # Drop the last partial batch so every batch is exactly batch_size.
        self.n_batches = len(p_records) // batch_size

        logger.info(
            "PseudoPositiveBatchSampler: %d native, %d PP, "
            "native_per_batch=%d, pp_per_batch=%d, n_batches=%d "
            "(oversample factor %.2fx)",
            len(self.native_indices),
            len(self.pp_indices),
            self.native_per_batch,
            self.pp_per_batch,
            self.n_batches,
            (self.pp_per_batch * self.n_batches) / max(len(self.pp_indices), 1),
        )

    def __iter__(self):
        # Seed a per-epoch generator from the global seed so each epoch gets a
        # different permutation while remaining fully reproducible.
        g = torch.Generator()
        g.manual_seed(torch.initial_seed())

        # ── Native indices: one random permutation, tiled cyclically ──────
        # This ensures each native P sample appears roughly once per epoch
        # regardless of the oversampling ratio on the PP side.
        native_needed = self.n_batches * self.native_per_batch
        base_perm = torch.randperm(len(self.native_indices), generator=g).tolist()
        tiled: List[int] = []
        while len(tiled) < native_needed:
            tiled.extend(base_perm)
        tiled = tiled[:native_needed]
        native_pool = torch.tensor(
            [self.native_indices[i] for i in tiled], dtype=torch.long
        )

        # ── PP indices: sample with replacement ────────────────────────────
        # Replacement is correct here: we have K=770 pseudo-positives but need
        # pp_per_batch * n_batches > K draws per epoch.  randperm would exhaust
        # the PP set and give zero PP in the remaining batches; randint ensures
        # every PP sample can appear multiple times so the gradient contribution
        # per epoch scales with pp_fraction rather than being capped by K.
        pp_needed = self.n_batches * self.pp_per_batch
        pp_rand = torch.randint(
            len(self.pp_indices), (pp_needed,), generator=g, dtype=torch.long
        )
        pp_pool = torch.tensor(
            [self.pp_indices[int(i)] for i in pp_rand], dtype=torch.long
        )

        for b in range(self.n_batches):
            n_slice = native_pool[b * self.native_per_batch:(b + 1) * self.native_per_batch]
            p_slice = pp_pool[b * self.pp_per_batch:(b + 1) * self.pp_per_batch]
            batch_idx = torch.cat([n_slice, p_slice])
            # Intra-batch shuffle so the model cannot infer position from order.
            perm = torch.randperm(len(batch_idx), generator=g)
            yield batch_idx[perm].tolist()

    def __len__(self) -> int:
        return self.n_batches


class TwoWayDatasetBuilder:
    """Builds P, U, val, and test loaders from existing JSON data files."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        data_dict = config.get("data", {})
        self.cfg = DataConfig2Way(
            fixed_len=int(data_dict.get("fixed_len", 1024)),
            fallback_header_len=int(data_dict.get("fallback_header_len", 512)),
            buffer_field=data_dict.get("buffer_field", "buffers"),
            sep_byte=int(data_dict.get("sep_byte", SEP_BYTE)),
        )

    # ── path helpers ────────────────────────────────

    @staticmethod
    def _ensure_path_list(val: Any) -> List[Path]:
        if val is None:
            return []
        if isinstance(val, str):
            return [Path(val)]
        if isinstance(val, list):
            return [Path(p) for p in val]
        raise TypeError(f"Invalid path type: {type(val)}")

    def _load_records_from_file(self, path: Path) -> List[Dict[str, Any]]:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        dataset = obj.get("dataset", [])
        if not isinstance(dataset, list):
            logger.error("File %s invalid: 'dataset' is not a list", path)
            return []
        return [rec for rec in dataset if isinstance(rec, dict) and self.cfg.buffer_field in rec]

    def _load_split_records(self, split: str) -> List[Dict[str, Any]]:
        benign = self._ensure_path_list(self.config.get("benign_paths", {}).get(split))
        attack = self._ensure_path_list(self.config.get("attack_paths", {}).get(split))
        records: List[Dict[str, Any]] = []
        for p in benign + attack:
            records.extend(self._load_records_from_file(p))
        return records

    @staticmethod
    def _is_sip_header_body(record: Dict[str, Any]) -> bool:
        names = str(record.get("buffer_names", ""))
        return "sip_header" in names and "sip_body" in names

    def _build_u_weighted_sampler(
        self,
        u_records: List[Dict[str, Any]],
        training_cfg: Dict[str, Any],
    ) -> Optional[WeightedRandomSampler]:
        stream_ip_multiplier = float(training_cfg.get("u_stream_ip_weight", 1.0))
        header_body_multiplier = float(training_cfg.get("u_header_body_weight", 1.0))
        max_multiplier = float(training_cfg.get("u_weight_cap", 3.0))

        if (
            stream_ip_multiplier <= 1.0
            and header_body_multiplier <= 1.0
        ):
            return None

        weights: List[float] = []
        for rec in u_records:
            w = 1.0
            if int(rec.get("pkt_gen", 0)) == 1:
                w *= max(1.0, stream_ip_multiplier)
            if self._is_sip_header_body(rec):
                w *= max(1.0, header_body_multiplier)
            if max_multiplier > 0:
                w = min(w, max_multiplier)
            weights.append(w)

        weight_tensor = torch.tensor(weights, dtype=torch.double)
        logger.info(
            "Using weighted U sampler: stream_ip_weight=%.2f header_body_weight=%.2f cap=%.2f",
            stream_ip_multiplier,
            header_body_multiplier,
            max_multiplier,
        )
        return WeightedRandomSampler(
            weights=weight_tensor,
            num_samples=len(u_records),
            replacement=True,
        )

    def _apply_pseudo_positive_manifest(
        self,
        p_records: List[Dict[str, Any]],
        u_records: List[Dict[str, Any]],
        training_cfg: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Apply one or more pseudo-positive manifests to the P/U split.

        ``training.pseudo_positive_manifest`` may be a single path string or a
        list of path strings.  When a list is provided all manifests are applied
        in order; their ``u_indices`` are unioned (duplicates silently ignored).
        Each manifest may contain an ``audit.u_count`` field; if present, it is
        checked against the current U-set size to detect config mismatches.
        """
        manifest_val = training_cfg.get("pseudo_positive_manifest")
        if not manifest_val:
            return p_records, u_records

        # Normalise to a list of path strings.
        if isinstance(manifest_val, str):
            manifest_paths: List[str] = [manifest_val]
        elif isinstance(manifest_val, list):
            manifest_paths = [str(m) for m in manifest_val]
        else:
            raise TypeError(
                f"pseudo_positive_manifest must be a str or list[str], "
                f"got {type(manifest_val)}"
            )

        max_promoted = int(
            training_cfg.get("pseudo_positive_max_promoted", len(u_records))
        )
        pseudo_positive_loss_weight = float(
            training_cfg.get("pseudo_positive_loss_weight", 1.0)
        )

        # Collect all promoted U-indices from all manifests (union, ordered by
        # manifest order then by within-manifest order).
        seen_indices: set[int] = set()
        all_selected: List[tuple[int, str]] = []  # (u_idx, source_name)

        for manifest_path_str in manifest_paths:
            path = Path(manifest_path_str)
            if not path.exists():
                raise FileNotFoundError(
                    f"Pseudo-positive manifest not found: {path}"
                )

            with path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)

            # Alignment guard: verify U-set size matches the manifest audit.
            expected_u = manifest.get("audit", {}).get("u_count")
            if expected_u is not None and int(expected_u) != len(u_records):
                raise ValueError(
                    f"Manifest u_count={expected_u} does not match current "
                    f"U-set size={len(u_records)} for {path}. "
                    "Ensure the miner and training configs point to the same "
                    "training split files."
                )

            raw_indices = manifest.get("u_indices", manifest)
            if not isinstance(raw_indices, list):
                raise TypeError(
                    f"Pseudo-positive manifest {path} must be a list or an "
                    "object with 'u_indices'"
                )

            source_name = str(manifest.get("source", str(path)))
            for item in raw_indices:
                idx = int(item)
                if idx < 0 or idx >= len(u_records) or idx in seen_indices:
                    continue
                all_selected.append((idx, source_name))
                seen_indices.add(idx)
                if len(all_selected) >= max_promoted:
                    break
            if len(all_selected) >= max_promoted:
                break

            logger.info(
                "Loaded manifest %s: %d valid indices (running total %d)",
                path, len([x for x in all_selected if x[1] == source_name]),
                len(all_selected),
            )

        if not all_selected:
            logger.warning(
                "Pseudo-positive manifest(s) provided no valid U indices; "
                "skipping promotion."
            )
            return p_records, u_records

        promoted_index_map: Dict[int, str] = {
            idx: src for idx, src in all_selected
        }
        promoted: List[Dict[str, Any]] = []
        remaining_u: List[Dict[str, Any]] = []
        for idx, record in enumerate(u_records):
            if idx in promoted_index_map:
                promoted_record = dict(record)
                promoted_record["alerted"] = 1
                promoted_record["pseudo_positive"] = 1
                promoted_record["pseudo_positive_source"] = promoted_index_map[idx]
                promoted_record["pseudo_positive_u_index"] = idx
                promoted_record["loss_weight"] = pseudo_positive_loss_weight
                promoted.append(promoted_record)
            else:
                remaining_u.append(record)

        logger.info(
            "Promoted %d pseudo-positives from U to P (%d manifest(s))",
            len(promoted),
            len(manifest_paths),
        )
        return p_records + promoted, remaining_u

    # ── P/U split (single source of truth) ──────────

    def split_train_pu(
        self,
        train_records: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split the training set into P (``alerted=1``) and U (``alerted=0``).

        This is the **single source of truth** for the positive/unlabeled split.
        Both ``build_loaders`` and any pseudo-positive miner must obtain the
        unlabeled list through this method so that manifest ``u_indices`` align
        exactly with the U-loader ordering. Pseudo-positive promotion is *not*
        applied here — the returned ``u_records`` is the raw, canonical U list
        that manifests index into.

        Args:
            train_records: Optional pre-loaded training records. When ``None``,
                records are loaded from the ``train`` split paths.

        Returns:
            ``(p_records, u_records)`` in canonical (file-load) order.
        """
        if train_records is None:
            train_records = self._load_split_records("train")
        p_records = [r for r in train_records if int(r.get("alerted", 0)) == 1]
        u_records = [r for r in train_records if int(r.get("alerted", 0)) == 0]
        return p_records, u_records

    # ── main entry ──────────────────────────────────

    def build_loaders(self) -> Dict[str, DataLoader]:
        training_cfg = self.config.get("training", {})
        batch_size = int(training_cfg.get("batch_size", 256))
        num_workers = int(training_cfg.get("num_workers", 0))

        train_records = self._load_split_records("train")
        val_records = self._load_split_records("val")
        test_records = self._load_split_records("test")

        # Split train into P (alerted=1) and U (alerted=0) via the single
        # source of truth so miner indices stay aligned with the U loader.
        p_records, u_records = self.split_train_pu(train_records)
        p_records, u_records = self._apply_pseudo_positive_manifest(
            p_records,
            u_records,
            training_cfg,
        )

        logger.info(
            "Train P (alerted=1): %d, Train U (alerted=0): %d",
            len(p_records), len(u_records),
        )
        logger.info("Val: %d, Test: %d", len(val_records), len(test_records))

        ds_p = TwoWayRecordDataset(p_records, self.cfg)
        ds_u = TwoWayRecordDataset(u_records, self.cfg)
        ds_val = TwoWayRecordDataset(val_records, self.cfg)
        ds_test = TwoWayRecordDataset(test_records, self.cfg)

        collate = functools.partial(twoway_collate_fn, cfg=self.cfg)
        u_sampler = self._build_u_weighted_sampler(u_records, training_cfg)

        pp_fraction = float(training_cfg.get("pseudo_positive_batch_fraction", 0.0))
        if pp_fraction > 0.0:
            p_batch_sampler = PseudoPositiveBatchSampler(
                p_records, batch_size, pp_fraction
            )
            # When batch_sampler is set, batch_size / shuffle / sampler /
            # drop_last must NOT be passed — PyTorch raises ValueError otherwise.
            train_p_loader: DataLoader = DataLoader(
                ds_p,
                batch_sampler=p_batch_sampler,
                num_workers=num_workers,
                collate_fn=collate,
            )
        else:
            train_p_loader = DataLoader(
                ds_p, batch_size=batch_size, shuffle=True,
                num_workers=num_workers, collate_fn=collate,
            )

        loaders = {
            "train_p": train_p_loader,
            "train_u": DataLoader(
                ds_u,
                batch_size=batch_size,
                shuffle=u_sampler is None,
                sampler=u_sampler,
                num_workers=num_workers,
                collate_fn=collate,
            ),
            "val": DataLoader(
                ds_val, batch_size=batch_size, shuffle=False,
                num_workers=num_workers, collate_fn=collate,
            ),
            "test": DataLoader(
                ds_test, batch_size=batch_size, shuffle=False,
                num_workers=num_workers, collate_fn=collate,
            ),
        }
        return loaders

    # ── supervised (single labelled train loader) ───

    def build_supervised_loader(self) -> DataLoader:
        """Build a shuffled loader over the FULL training set (P ∪ U, unsplit).

        Supervised baselines (teacher-copy on ``alerted`` / oracle on
        ``is_attack``) need one labelled loader over every training sample
        rather than the P/U pair used by nnPU.  The union of P and U is exactly
        the raw ``train`` split, so we load it directly and skip the
        pseudo-positive manifest entirely: promotion flips ``alerted`` for mined
        U samples, which would corrupt the teacher-copy target.  ``is_attack``
        and ``alerted`` therefore carry their original ground-truth values.

        The batch schema is identical to ``build_loaders`` (same dataset class
        and collate fn), so the trainer and per-sample prognosis code are
        reused unchanged.  The P/U path in ``build_loaders`` is not touched.
        """
        training_cfg = self.config.get("training", {})
        batch_size = int(training_cfg.get("batch_size", 256))
        num_workers = int(training_cfg.get("num_workers", 0))

        train_records = self._load_split_records("train")
        n_pos = sum(1 for r in train_records if int(r.get("alerted", 0)) == 1)
        n_att = sum(1 for r in train_records if int(r.get("is_attack", 0)) == 1)
        logger.info(
            "Supervised train (all): %d records (alerted=1: %d, is_attack=1: %d)",
            len(train_records), n_pos, n_att,
        )

        ds_all = TwoWayRecordDataset(train_records, self.cfg)
        collate = functools.partial(twoway_collate_fn, cfg=self.cfg)
        return DataLoader(
            ds_all,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            collate_fn=collate,
        )
