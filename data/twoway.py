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
        manifest_path = training_cfg.get("pseudo_positive_manifest")
        if not manifest_path:
            return p_records, u_records

        path = Path(manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Pseudo-positive manifest not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)

        raw_indices = manifest.get("u_indices", manifest)
        if not isinstance(raw_indices, list):
            raise TypeError("Pseudo-positive manifest must be a list or an object with 'u_indices'")

        max_promoted = int(training_cfg.get("pseudo_positive_max_promoted", len(raw_indices)))
        selected: List[int] = []
        seen: set[int] = set()
        for item in raw_indices:
            idx = int(item)
            if idx < 0 or idx >= len(u_records) or idx in seen:
                continue
            selected.append(idx)
            seen.add(idx)
            if len(selected) >= max_promoted:
                break

        if not selected:
            logger.warning("Pseudo-positive manifest provided no valid U indices; skipping promotion.")
            return p_records, u_records

        promoted: List[Dict[str, Any]] = []
        selected_set = set(selected)
        remaining_u: List[Dict[str, Any]] = []
        for idx, record in enumerate(u_records):
            if idx in selected_set:
                promoted_record = dict(record)
                promoted_record["alerted"] = 1
                promoted_record["pseudo_positive"] = 1
                promoted_record["pseudo_positive_source"] = str(manifest.get("source", "manifest"))
                promoted_record["pseudo_positive_u_index"] = idx
                promoted.append(promoted_record)
            else:
                remaining_u.append(record)

        logger.info(
            "Promoted %d pseudo-positives from U to P using %s",
            len(promoted),
            path,
        )
        return p_records + promoted, remaining_u

    # ── main entry ──────────────────────────────────

    def build_loaders(self) -> Dict[str, DataLoader]:
        training_cfg = self.config.get("training", {})
        batch_size = int(training_cfg.get("batch_size", 256))
        num_workers = int(training_cfg.get("num_workers", 0))

        train_records = self._load_split_records("train")
        val_records = self._load_split_records("val")
        test_records = self._load_split_records("test")

        # Split train into P (alerted=1) and U (alerted=0)
        p_records = [r for r in train_records if int(r.get("alerted", 0)) == 1]
        u_records = [r for r in train_records if int(r.get("alerted", 0)) == 0]
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

        loaders = {
            "train_p": DataLoader(
                ds_p, batch_size=batch_size, shuffle=True,
                num_workers=num_workers, collate_fn=collate,
            ),
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
