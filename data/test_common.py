"""Regression tests for record provenance retained by two-way batches."""

import torch

from nids_ml.data.common import (
    DataConfig2Way,
    TwoWayRecordDataset,
    extract_record_call_id,
    to_device,
    twoway_collate_fn,
)


def test_extract_record_call_id_prefers_explicit_metadata() -> None:
    record = {
        "call_id": "metadata-id",
        "buffers": "INVITE sip:user@example.test SIP/2.0\r\nCall-ID: wire-id\r\n",
    }

    assert extract_record_call_id(record, "buffers") == "metadata-id"


def test_collated_call_ids_survive_device_transfer() -> None:
    cfg = DataConfig2Way(fixed_len=16, fallback_header_len=8)
    dataset = TwoWayRecordDataset([
        {"buffers": "INVITE sip:a SIP/2.0\r\nCall-ID: first\r\n", "alerted": 0, "is_attack": 0},
        {"buffers": "INVITE sip:b SIP/2.0\r\nCall-ID: second\r\n", "alerted": 0, "is_attack": 1},
    ], cfg)

    batch = twoway_collate_fn([dataset[0], dataset[1]], cfg)
    transferred = to_device(batch, torch.device("cpu"))

    assert transferred["call_id"] == ["first", "second"]
    assert isinstance(transferred["header_ids"], torch.Tensor)