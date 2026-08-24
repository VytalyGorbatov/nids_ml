import json
from pathlib import Path

from nids_ml.tools.skeleton_saliency import (
    build_ids,
    decode_ids_window,
    select_group_records,
    top_k_positions,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")


def test_select_group_records_filters_benign_non_alerted_and_template(tmp_path: Path) -> None:
    dataset_path = tmp_path / "benign.json"
    dataset_path.write_text(json.dumps({"dataset": [
        {"buffers": "OPTIONS sip:x SIP/2.0\r\nCall-ID: a\r\n\r\n", "is_attack": 0, "alerted": 0},
        {"buffers": "OPTIONS sip:x SIP/2.0\r\nCall-ID: b\r\n\r\n", "is_attack": 0, "alerted": 0},
        {"buffers": "OPTIONS sip:x SIP/2.0\r\nCall-ID: c\r\n\r\n", "is_attack": 0, "alerted": 1},  # alerted, excluded
    ]}), encoding="utf-8")
    provenance_path = tmp_path / "manifest.jsonl"
    _write_jsonl(provenance_path, [
        {"call_id": "a", "template_id": "BYE-S5"},
        {"call_id": "b", "template_id": "BYE-S1"},
        {"call_id": "c", "template_id": "BYE-S5"},
    ])

    records = select_group_records(dataset_path, provenance_path, "BYE-S5", max_examples=10)

    assert len(records) == 1
    assert "Call-ID: a" in records[0]["buffers"]


def test_select_group_records_respects_max_examples(tmp_path: Path) -> None:
    dataset_path = tmp_path / "benign.json"
    dataset_path.write_text(json.dumps({"dataset": [
        {"buffers": f"OPTIONS sip:x SIP/2.0\r\nCall-ID: {i}\r\n\r\n", "is_attack": 0, "alerted": 0}
        for i in range(5)
    ]}), encoding="utf-8")
    provenance_path = tmp_path / "manifest.jsonl"
    _write_jsonl(provenance_path, [{"call_id": str(i), "template_id": "BYE-S5"} for i in range(5)])

    records = select_group_records(dataset_path, provenance_path, "BYE-S5", max_examples=2)

    assert len(records) == 2


def test_decode_ids_window_marks_non_printable_bytes() -> None:
    ids = [ord("A"), ord("B"), 0, ord("C"), 256]

    window = decode_ids_window(ids, center=2, window=2)

    assert window == "AB.C."


def test_top_k_positions_returns_highest_first() -> None:
    import numpy as np

    saliency = np.array([0.1, 0.9, 0.4, 0.9, 0.0])

    top = top_k_positions(saliency, k=2)

    assert set(top) == {1, 3}


def test_build_ids_matches_split_header_body(monkeypatch) -> None:
    from nids_ml.data.common import DataConfig2Way, split_header_body, decode_buffers_field

    cfg = DataConfig2Way(fixed_len=32, fallback_header_len=16, sep_byte=30)
    record = {"buffers": "GET\x1ebody"}

    header_ids, body_ids = build_ids(record, cfg)
    expected_header, expected_body = split_header_body(
        decode_buffers_field(record["buffers"]), cfg.fixed_len, cfg.sep_byte, cfg.fallback_header_len,
    )

    assert header_ids == expected_header
    assert body_ids == expected_body


def test_occlusion_saliency_runs_end_to_end_on_a_tiny_model() -> None:
    """Wiring smoke test: a full occlusion pass on a tiny model, not real weights."""
    import numpy as np
    from nids_ml.data.common import DataConfig2Way
    from nids_ml.models import build_model
    from nids_ml.tools.skeleton_saliency import aggregate_saliency

    tiny_config = {
        "model": {
            "type": "tcn_2way", "embed_dim": 4, "channels": 4, "kernel": 3,
            "dilations": [1], "prefix_lengths": [4], "proj_dim": 8, "fusion_dim": 8,
        },
    }
    model = build_model(tiny_config)
    model.backbone.eval()
    model.heads.eval()
    cfg = DataConfig2Way(fixed_len=16, fallback_header_len=8, sep_byte=30)
    records = [
        {"buffers": "OPTIONS sip:x SIP/2.0\r\n\x1ebody one"},
        {"buffers": "OPTIONS sip:y SIP/2.0\r\n\x1ebody two"},
    ]

    saliency = aggregate_saliency(records, model, cfg, device="cpu")

    assert saliency.shape == (cfg.fixed_len,)
    assert np.isfinite(saliency).all()
