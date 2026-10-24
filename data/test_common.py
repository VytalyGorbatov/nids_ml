import json
from pathlib import Path

import torch

from nids_ml.data.common import (
    DataConfig2Way,
    TwoWayRecordDataset,
    extract_record_call_id,
    split_header_body,
    to_device,
    twoway_collate_fn,
)
from nids_ml.data.twoway import TwoWayDatasetBuilder
from nids_ml.data.standard import DatasetBuilder


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


def test_split_header_body_sep_byte() -> None:
    # 30 is SEP_BYTE (0x1E)
    ids = [ord("A"), ord("B"), 30, ord("C"), ord("D")]
    h, b = split_header_body(ids, fixed_len=10, sep_byte=30, fallback_header_len=5)
    assert h == [ord("A"), ord("B"), 256, 256, 256]
    assert b == [ord("C"), ord("D"), 256, 256, 256]


def test_split_header_body_http_with_0x1e() -> None:
    raw_str = "GET /test HTTP/1.1\r\nHost: example.com\x1e{'payload': 'data'}\x1e"
    raw_bytes = list(raw_str.encode("latin1"))
    h, b = split_header_body(
        raw_bytes,
        fixed_len=80,
        sep_byte=30,
        header_len=40,
        body_len=40,
    )
    expected_header = list("GET /test HTTP/1.1\r\nHost: example.com".encode("latin1"))
    expected_body = list("{'payload': 'data'}".encode("latin1"))

    assert h[:len(expected_header)] == expected_header
    assert set(h[len(expected_header):]) == {256}
    assert b[:len(expected_body)] == expected_body
    assert set(b[len(expected_body):]) == {256}


def test_split_header_body_fallback() -> None:
    raw_str = "A" * 60
    raw_bytes = list(raw_str.encode("latin1"))
    h, b = split_header_body(
        raw_bytes,
        fixed_len=80,
        sep_byte=30,
        fallback_header_len=40,
        header_len=40,
        body_len=40,
    )
    assert h == [ord("A")] * 40
    assert b == [ord("A")] * 20 + [256] * 20

    # Short ids <= fallback_header_len without 0x1e
    short_ids = [ord("X")] * 10
    h_short, b_short = split_header_body(
        short_ids,
        fixed_len=80,
        sep_byte=30,
        fallback_header_len=40,
        header_len=40,
        body_len=40,
    )
    assert h_short == [ord("X")] * 10 + [256] * 30
    assert b_short == [256] * 40


def test_dataconfig2way_http() -> None:
    cfg = DataConfig2Way(
        fixed_len=1664,
        header_len=1280,
        body_len=384,
        sep_byte=30,
    )
    assert cfg.header_len == 1280
    assert cfg.body_len == 384
    assert cfg.sep_byte == 30

    # Defaults
    cfg_default = DataConfig2Way(fixed_len=1024, fallback_header_len=512)
    assert cfg_default.header_len == 512
    assert cfg_default.body_len == 512
    assert cfg_default.sep_byte == 30


def test_extract_record_call_id_generalized() -> None:
    rec_http = {"request_id": "req-12345", "buffers": "GET / HTTP/1.1\r\n\r\n"}
    assert extract_record_call_id(rec_http, "buffers") == "req-12345"

    rec_seq = {"seq_id": "seq-999", "buffers": "GET / HTTP/1.1\r\n\r\n"}
    assert extract_record_call_id(rec_seq, "buffers") == "seq-999"

    rec_sip = {"call_id": "call-abc", "buffers": "INVITE ..."}
    assert extract_record_call_id(rec_sip, "buffers") == "call-abc"


def test_twoway_builder_split_paths(tmp_path: Path) -> None:
    train_file = tmp_path / "train.json"
    val_file = tmp_path / "val.json"
    test_file = tmp_path / "test.json"

    train_data = {
        "dataset": [
            {
                "request_id": "r1",
                "buffers": "GET / HTTP/1.1\r\nHost: a\r\n\r\nbody1",
                "buffer_names": "http_header\x1ehttp_client_body\x1e",
                "is_attack": 1,
                "alerted": 1,
            },
            {
                "request_id": "r2",
                "buffers": "GET / HTTP/1.1\r\nHost: b\r\n\r\nbody2",
                "buffer_names": "http_header\x1ehttp_client_body\x1e",
                "is_attack": 0,
                "alerted": 0,
            },
        ]
    }
    for f in (train_file, val_file, test_file):
        with f.open("w", encoding="utf-8") as fp:
            json.dump(train_data, fp)

    config = {
        "split_paths": {
            "train": str(train_file),
            "val": str(val_file),
            "test": str(test_file),
        },
        "data": {
            "fixed_len": 64,
            "header_len": 32,
            "body_len": 32,
            "sep_seq": "\r\n\r\n",
        },
        "training": {
            "batch_size": 2,
        },
    }
    builder = TwoWayDatasetBuilder(config)
    loaders = builder.build_loaders()
    assert "train_p" in loaders
    assert "train_u" in loaders
    assert "val" in loaders
    assert "test" in loaders

    p_batch = next(iter(loaders["train_p"]))
    assert p_batch["source_class"] == ["attack"]
    assert p_batch["call_id"] == ["r1"]

    u_batch = next(iter(loaders["train_u"]))
    assert u_batch["source_class"] == ["benign"]
    assert u_batch["call_id"] == ["r2"]


def test_twoway_builder_benign_attack_paths_backward_compat(tmp_path: Path) -> None:
    benign_train = tmp_path / "benign_train.json"
    attack_train = tmp_path / "attack_train.json"
    val_file = tmp_path / "val.json"
    test_file = tmp_path / "test.json"

    with benign_train.open("w", encoding="utf-8") as fp:
        json.dump({"dataset": [{"call_id": "c_b", "buffers": "INVITE ...\x1e...", "alerted": 0, "is_attack": 0}]}, fp)
    with attack_train.open("w", encoding="utf-8") as fp:
        json.dump({"dataset": [{"call_id": "c_a", "buffers": "INVITE ...\x1e...", "alerted": 1, "is_attack": 1}]}, fp)
    with val_file.open("w", encoding="utf-8") as fp:
        json.dump({"dataset": [{"call_id": "c_v", "buffers": "INVITE ...\x1e...", "alerted": 0, "is_attack": 0}]}, fp)
    with test_file.open("w", encoding="utf-8") as fp:
        json.dump({"dataset": [{"call_id": "c_t", "buffers": "INVITE ...\x1e...", "alerted": 0, "is_attack": 0}]}, fp)

    config = {
        "benign_paths": {"train": str(benign_train), "val": str(val_file), "test": str(test_file)},
        "attack_paths": {"train": str(attack_train), "val": str(val_file), "test": str(test_file)},
        "data": {"fixed_len": 64, "sep_byte": 30},
        "training": {"batch_size": 2},
    }
    builder = TwoWayDatasetBuilder(config)
    loaders = builder.build_loaders()
    p_batch = next(iter(loaders["train_p"]))
    assert p_batch["call_id"] == ["c_a"]
    assert p_batch["source_class"] == ["attack"]

    u_batch = next(iter(loaders["train_u"]))
    assert u_batch["call_id"] == ["c_b"]
    assert u_batch["source_class"] == ["benign"]


def test_standard_builder_split_paths(tmp_path: Path) -> None:
    train_file = tmp_path / "train.json"
    val_file = tmp_path / "val.json"
    test_file = tmp_path / "test.json"

    data = {
        "dataset": [
            {"request_id": "r1", "buffers": "GET ...\x1eBODY\x1e", "alerted": 1, "is_attack": 1},
            {"request_id": "r2", "buffers": "GET ...\x1eBODY\x1e", "alerted": 0, "is_attack": 0},
        ]
    }
    for f in (train_file, val_file, test_file):
        with f.open("w", encoding="utf-8") as fp:
            json.dump(data, fp)

    config = {
        "split_paths": {
            "train": str(train_file),
            "val": str(val_file),
            "test": str(test_file),
        },
        "data": {
            "fixed_len": 64,
            "header_len": 32,
            "body_len": 32,
            "sep_byte": 30,
        },
        "training": {"batch_size": 2},
        "sampling": {"enabled": False},
    }
    builder = DatasetBuilder(config)
    loaders = builder.build_loaders()
    batch = next(iter(loaders["train"]))
    assert len(batch["call_id"]) == 2