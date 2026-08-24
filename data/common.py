"""
Shared data primitives for the NIDS ML framework.

Contains buffer decoding, sequence processing, dataset classes,
collation, augmentations, and device helpers used by both the
standard and 2-way data pipelines.
"""
from __future__ import annotations

import logging
import random
import re
from hashlib import sha256
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import torch
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)

PAD_IDX = 256
SEP_BYTE = 0x1E  # record separator (decimal 30)
_CALL_ID_RE = re.compile(r"(?im)^Call-ID\s*:\s*([^\r\n]+)")


# ─── Buffer decoding ──────────────────────────────────


def decode_buffers_field(x: Any) -> List[int]:
    """Robustly decode the ``buffers`` field into a list of ints in [0, 255].

    Supported formats:
      - ``list[int]`` (raw byte values)
      - ``list[float]`` in [0, 1] (legacy normalised) → ``round(x*255)``
      - ``str`` (latin-1 transport) → byte values via ``encode('latin1')``
    """
    if isinstance(x, list):
        if len(x) == 0:
            return []
        if isinstance(x[0], int):
            return [int(v) & 0xFF for v in x]
        if isinstance(x[0], float):
            return [int(round(float(v) * 255.0)) & 0xFF for v in x]
        raise TypeError(f"Unsupported list element type: {type(x[0])}")

    if isinstance(x, str):
        return list(x.encode("latin1", errors="ignore"))

    raise TypeError(f"Unsupported buffers field type: {type(x)}")


def buffer_sha256(buffer_value: Any) -> str:
    """Hash the decoded model-input bytes using a stable SHA-256 policy."""
    return sha256(bytes(decode_buffers_field(buffer_value))).hexdigest()


def extract_record_call_id(record: Dict[str, Any], buffer_field: str) -> Optional[str]:
    """Return an explicit or SIP-header Call-ID for prediction provenance."""
    explicit_call_id = record.get("call_id")
    if explicit_call_id is not None and str(explicit_call_id).strip():
        return str(explicit_call_id).strip()

    buffer_value = record.get(buffer_field)
    if buffer_value is None:
        return None
    try:
        text = bytes(decode_buffers_field(buffer_value)).decode(
            "latin1", errors="ignore",
        )
    except TypeError:
        return None
    text = text.replace("\\r\\n", "\r\n").replace("\\n", "\n")
    match = _CALL_ID_RE.search(text)
    return match.group(1).strip() if match else None


# ─── Sequence helpers ─────────────────────────────────


def pad_or_truncate(ids: List[int], fixed_len: int, pad_idx: int = PAD_IDX) -> List[int]:
    if len(ids) >= fixed_len:
        return ids[:fixed_len]
    return ids + [pad_idx] * (fixed_len - len(ids))


def split_header_body(
    ids: List[int],
    fixed_len: int,
    sep_byte: int = SEP_BYTE,
    fallback_header_len: Optional[int] = None,
) -> Tuple[List[int], List[int]]:
    """Split a byte stream into header and body at the first ``sep_byte``."""
    if fallback_header_len is None:
        fallback_header_len = fixed_len // 2

    header_len = fallback_header_len
    body_len = fixed_len - header_len

    ids_fixed = pad_or_truncate(ids, fixed_len)
    try:
        sep_pos = ids_fixed.index(sep_byte)
        header_raw = ids_fixed[:sep_pos]
        body_raw = ids_fixed[sep_pos + 1:]
    except ValueError:
        header_raw = ids_fixed[:header_len]
        body_raw = ids_fixed[header_len:]

    return (
        pad_or_truncate(header_raw, header_len),
        pad_or_truncate(body_raw, body_len),
    )


# ─── Config ───────────────────────────────────────────


@dataclass
class DataConfig2Way:
    fixed_len: int = 1024
    fallback_header_len: int = 512
    buffer_field: str = "buffers"
    sep_byte: int = SEP_BYTE


# ─── Dataset ──────────────────────────────────────────


class TwoWayRecordDataset(Dataset):
    """Dataset backed by pre-loaded record dicts."""

    def __init__(
        self,
        records: List[Dict[str, Any]],
        cfg: DataConfig2Way,
    ) -> None:
        super().__init__()
        self.records = records
        self.cfg = cfg

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        r = self.records[idx]
        ids = decode_buffers_field(r[self.cfg.buffer_field])
        header_ids, body_ids = split_header_body(
            ids, self.cfg.fixed_len, self.cfg.sep_byte, self.cfg.fallback_header_len,
        )
        return {
            "header_ids": header_ids,
            "body_ids": body_ids,
            "call_id": extract_record_call_id(r, self.cfg.buffer_field),
            "source_index": int(r.get("source_index", idx)),
            "source_class": r.get("source_class"),
            "buffer_sha256": buffer_sha256(r[self.cfg.buffer_field]),
            "alerted": int(r.get("alerted", 0)),
            "is_attack": int(r.get("is_attack", 0)),
            "loss_weight": float(r.get("loss_weight", 1.0)),
            "pseudo_positive": int(r.get("pseudo_positive", 0)),
        }


# ─── Collation ────────────────────────────────────────


def twoway_collate_fn(
    batch: List[Dict[str, Any]], cfg: DataConfig2Way,
) -> Dict[str, Any]:
    header = torch.tensor([b["header_ids"] for b in batch], dtype=torch.long)
    body = torch.tensor([b["body_ids"] for b in batch], dtype=torch.long)
    return {
        "header_ids": header,
        "body_ids": body,
        "header_mask": header.ne(PAD_IDX),
        "body_mask": body.ne(PAD_IDX),
        "call_id": [b.get("call_id") for b in batch],
        "source_index": torch.tensor([b["source_index"] for b in batch], dtype=torch.long),
        "source_class": [b.get("source_class") for b in batch],
        "buffer_sha256": [b.get("buffer_sha256") for b in batch],
        "alerted": torch.tensor([b["alerted"] for b in batch], dtype=torch.float32),
        "is_attack": torch.tensor([b["is_attack"] for b in batch], dtype=torch.float32),
        "loss_weight": torch.tensor([b.get("loss_weight", 1.0) for b in batch], dtype=torch.float32),
        "pseudo_positive": torch.tensor([b.get("pseudo_positive", 0) for b in batch], dtype=torch.long),
    }


def concat_batches(
    first: Dict[str, Any], second: Dict[str, Any],
) -> Dict[str, Any]:
    """Concatenate two collated batches that share the same schema.

    Lets a supervised objective consume the same P/U batch pairing that the
    nnPU loop uses, so positive-exposure per step is identical across
    objectives.
    """
    merged: Dict[str, Any] = {}
    for key, value in first.items():
        other = second[key]
        if isinstance(value, torch.Tensor):
            merged[key] = torch.cat([value, other], dim=0)
        elif isinstance(value, list):
            merged[key] = value + other
        else:
            merged[key] = value
    return merged


# ─── Byte augmentations for SSL ──────────────────────


def augment_ids(
    ids: torch.Tensor, mask: torch.Tensor,
    p_drop: float = 0.05, p_span: float = 0.10,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Lightweight byte augmentations: random token dropout + span masking."""
    B, L = ids.shape
    out = ids.clone()
    out_mask = mask.clone()

    # token dropout
    drop = (torch.rand(B, L, device=ids.device) < p_drop) & out_mask
    out[drop] = PAD_IDX
    out_mask = out.ne(PAD_IDX)

    # span masking
    if p_span > 0:
        for b in range(B):
            if torch.rand(1).item() < p_span:
                valid_positions = torch.where(out_mask[b])[0]
                if valid_positions.numel() < 8:
                    continue
                start = valid_positions[0].item()
                end = valid_positions[-1].item()
                span_len = int(min(32, max(8, (end - start) * 0.1)))
                s = random.randint(start, max(start, end - span_len))
                out[b, s:s + span_len] = PAD_IDX
        out_mask = out.ne(PAD_IDX)

    return out, out_mask


# ─── Batch device helper ─────────────────────────────


def to_device(
    batch: Dict[str, Any], device: torch.device,
) -> Dict[str, Any]:
    """Move tensor values to a device while retaining provenance metadata."""
    return {
        key: value.to(device) if isinstance(value, torch.Tensor) else value
        for key, value in batch.items()
    }
