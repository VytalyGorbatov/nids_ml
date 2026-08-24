"""Byte-level occlusion saliency for a confounded skeleton vs a control skeleton.

Loads an already-trained checkpoint (no retraining) and, for two benign
template groups -- one confounded (attack-only in train) and one control
(both benign+attack in train) -- measures which input byte positions the
risk head relies on most, via leave-one-out occlusion: mask one position at
a time to PAD and record the resulting drop in risk logit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from nids_ml.tools.join_predictions_with_provenance import (
    _load_dataset,
    _load_manifest,
    _source_identity,
)

PAD_IDX = 256


def select_group_records(
    dataset_path: Path, provenance_manifest_path: Path, template_id: str, max_examples: int,
) -> list[dict[str, Any]]:
    """Return up to ``max_examples`` benign, non-alerted records for one template group."""
    provenance_by_call_id = {
        str(row["call_id"]): row for row in _load_manifest(provenance_manifest_path) if row.get("call_id")
    }
    selected: list[dict[str, Any]] = []
    for record in _load_dataset(dataset_path):
        if record.get("is_attack", 0) or record.get("alerted", 0):
            continue
        call_id, _, _, _, _ = _source_identity(record)
        provenance = provenance_by_call_id.get(call_id) if call_id else None
        if provenance and str(provenance.get("template_id")) == template_id:
            selected.append(record)
            if len(selected) >= max_examples:
                break
    return selected


def decode_ids_window(ids: list[int], center: int, window: int = 12) -> str:
    """Render a short human-readable window of byte ids around one position."""
    start = max(0, center - window)
    end = min(len(ids), center + window + 1)
    chars = [chr(b) if 32 <= b < 127 else "." for b in ids[start:end]]
    return "".join(chars)


def build_ids(record: dict[str, Any], cfg: Any, buffer_field: str = "buffers") -> tuple[list[int], list[int]]:
    """Tokenize one record into (header_ids, body_ids) exactly like TwoWayRecordDataset."""
    from nids_ml.data.common import decode_buffers_field, split_header_body

    ids = decode_buffers_field(record[buffer_field])
    return split_header_body(ids, cfg.fixed_len, cfg.sep_byte, cfg.fallback_header_len)


def occlude_saliency(model: Any, cfg: Any, record: dict[str, Any], device: Any) -> "Any":
    """Return a per-position risk-logit drop array for one record (length = fixed_len)."""
    import torch

    header_ids, body_ids = build_ids(record, cfg)
    header_len, body_len = len(header_ids), len(body_ids)
    total = header_len + body_len

    header_batch = torch.tensor([header_ids] * (total + 1), dtype=torch.long)
    body_batch = torch.tensor([body_ids] * (total + 1), dtype=torch.long)
    for position in range(total):
        row = position + 1
        if position < header_len:
            header_batch[row, position] = PAD_IDX
        else:
            body_batch[row, position - header_len] = PAD_IDX

    batch = {
        "header_ids": header_batch.to(device), "body_ids": body_batch.to(device),
        "header_mask": header_batch.ne(PAD_IDX).to(device), "body_mask": body_batch.ne(PAD_IDX).to(device),
    }
    with torch.no_grad():
        z = model.backbone(batch)
        risk_logit = model.heads(z)["risk_logit"]
    baseline = risk_logit[0]
    return (baseline - risk_logit[1:]).cpu().numpy()


def aggregate_saliency(records: Iterable[dict[str, Any]], model: Any, cfg: Any, device: Any) -> "Any":
    """Mean per-position saliency across a group of records."""
    import numpy as np

    per_record = [occlude_saliency(model, cfg, record, device) for record in records]
    return np.mean(np.stack(per_record), axis=0)


def top_k_positions(saliency: "Any", k: int) -> list[int]:
    import numpy as np

    return list(np.argsort(saliency)[::-1][:k])


def render_report(
    target_template: str, control_template: str,
    target_saliency: "Any", control_saliency: "Any",
    target_records: list[dict[str, Any]], control_records: list[dict[str, Any]],
    cfg: Any, top_k: int,
) -> str:
    lines = [
        "# Skeleton Byte-Occlusion Saliency",
        "",
        f"Confounded (attack-only-in-train) template: `{target_template}`  ",
        f"Control (benign+attack-in-train) template: `{control_template}`",
        "",
        "Each row is a byte POSITION (0-indexed into the concatenated "
        "header+body sequence). Delta = drop in risk logit when that byte "
        "is masked; higher means the model relies on it more to raise risk.",
        "",
        f"## Top {top_k} positions for `{target_template}`",
        "",
        "| position | mean delta | example context (first record) |",
        "|---:|---:|---|",
    ]
    header_len, _ = build_ids(target_records[0], cfg)
    header_len = len(header_len)
    example_ids = build_ids(target_records[0], cfg)
    combined_example = example_ids[0] + example_ids[1]
    for position in top_k_positions(target_saliency, top_k):
        context = decode_ids_window(combined_example, position)
        lines.append(f"| {position} | {target_saliency[position]:.4f} | `{context}` |")

    lines.extend(["", f"## Top {top_k} positions for `{control_template}`", "", "| position | mean delta | example context (first record) |", "|---:|---:|---|"])
    control_example_ids = build_ids(control_records[0], cfg)
    control_combined = control_example_ids[0] + control_example_ids[1]
    for position in top_k_positions(control_saliency, top_k):
        context = decode_ids_window(control_combined, position)
        lines.append(f"| {position} | {control_saliency[position]:.4f} | `{context}` |")

    return "\n".join(lines) + "\n"


def main() -> None:
    import torch
    from nids_ml.models import build_model
    from nids_ml.data.common import DataConfig2Way

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--checkpoint", default="model_best.pt")
    parser.add_argument(
        "--target-dataset", required=True, type=Path,
        help="Benign split JSON containing the confounded template, e.g. benign/val.json",
    )
    parser.add_argument(
        "--control-dataset", required=True, type=Path,
        help="Benign split JSON containing the control template, e.g. benign/train.json",
    )
    parser.add_argument("--benign-provenance", required=True, type=Path)
    parser.add_argument("--target-template-id", required=True, help="Confounded template, e.g. BYE-S5")
    parser.add_argument("--control-template-id", required=True, help="Non-confounded template, e.g. BYE-S1")
    parser.add_argument("--max-examples", type=int, default=40)
    parser.add_argument("--top-k", type=int, default=15)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    config = json.load((args.run_dir / "config_used.json").open(encoding="utf-8"))
    data_cfg = config.get("data", {})
    cfg = DataConfig2Way(
        fixed_len=int(data_cfg.get("fixed_len", 1024)),
        fallback_header_len=int(data_cfg.get("fallback_header_len", 512)),
        buffer_field=data_cfg.get("buffer_field", "buffers"),
        sep_byte=int(data_cfg.get("sep_byte", 30)),
    )
    device = torch.device("cpu")
    model = build_model(config)
    model.to(device)
    checkpoint = torch.load(args.run_dir / args.checkpoint, map_location=device, weights_only=True)
    model.backbone.load_state_dict(checkpoint["backbone"])
    model.heads.load_state_dict(checkpoint["heads"])
    model.backbone.eval()
    model.heads.eval()

    target_records = select_group_records(
        args.target_dataset, args.benign_provenance, args.target_template_id, args.max_examples,
    )
    control_records = select_group_records(
        args.control_dataset, args.benign_provenance, args.control_template_id, args.max_examples,
    )
    if not target_records:
        raise SystemExit(f"No records found for target template {args.target_template_id!r}")
    if not control_records:
        raise SystemExit(f"No records found for control template {args.control_template_id!r}")

    target_saliency = aggregate_saliency(target_records, model, cfg, device)
    control_saliency = aggregate_saliency(control_records, model, cfg, device)

    args.out.mkdir(parents=True, exist_ok=True)
    import numpy as np
    np.savez(
        args.out / "saliency_arrays.npz",
        target_saliency=target_saliency, control_saliency=control_saliency,
    )
    report = render_report(
        args.target_template_id, args.control_template_id,
        target_saliency, control_saliency, target_records, control_records,
        cfg, args.top_k,
    )
    (args.out / "skeleton_saliency_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
