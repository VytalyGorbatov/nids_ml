"""Join two-way prediction rows to source records and provenance manifests."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SEP_BYTE = 0x1E

_CALL_ID_RE = re.compile(r"(?im)^Call-ID\s*:\s*([^\r\n]+)")
_VIA_BRANCH_RE = re.compile(
    r"(?im)^(?:Via|v)\s*:\s*[^\r\n]*;\s*branch=([^;\s\r\n]+)"
)
_REQUEST_METHOD_RE = re.compile(r"(?im)^\s*([A-Z]+)\s+\S+\s+SIP/2\.0")
_RESPONSE_CLASS_RE = re.compile(r"(?im)^\s*SIP/2\.0\s+(\d)\d\d\b")
_TELEMETRY_FIELDS = (
    "flowstart_time", "seconds", "proto", "pkt_gen", "pkt_len", "eth_len",
    "ip_len", "ttl", "udp_len", "dir", "client_bytes", "client_pkts",
    "server_bytes", "server_pkts",
)
_PROVENANCE_FIELDS = (
    "sample_id", "run_id", "generator_id", "source", "source_role", "pcap_id",
    "scenario", "scenario_id", "template_id", "split_group_id", "method",
    "method_family", "mutation_id", "mutation_chain", "defect_id", "rfc4475_case",
    "signal_field",
)
_FINGERPRINT_POLICY = "sha256(decoded buffers bytes; list[int] bytes, normalized float lists rounded(x*255), latin-1 strings encoded with errors=ignore)"


class JoinValidationError(ValueError):
    """Raised when source alignment or provenance identity is invalid."""


def decode_buffers_field(value: Any) -> list[int]:
    """Decode buffers with the same serialization policy as model input."""
    if isinstance(value, list):
        if not value:
            return []
        if isinstance(value[0], int):
            return [int(item) & 0xFF for item in value]
        if isinstance(value[0], float):
            return [int(round(float(item) * 255.0)) & 0xFF for item in value]
    if isinstance(value, str):
        return list(value.encode("latin1", errors="ignore"))
    raise TypeError(f"Unsupported buffers field type: {type(value)}")


def buffer_sha256(buffer_value: Any) -> str:
    import hashlib
    return hashlib.sha256(bytes(decode_buffers_field(buffer_value))).hexdigest()


@dataclass(frozen=True)
class SourceRecord:
    source_class: str
    source_index: int
    global_source_index: int
    record: dict[str, Any]


def _load_json_array(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise JoinValidationError(f"{path}: expected a JSON array of objects")
    return value


def _load_dataset(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    dataset = value.get("dataset") if isinstance(value, dict) else None
    if not isinstance(dataset, list) or not all(isinstance(row, dict) for row in dataset):
        raise JoinValidationError(f"{path}: expected an object with a dataset array")
    return dataset


def _load_manifest(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = [json.loads(line) for line in text.splitlines() if line.strip()]
    if isinstance(value, dict):
        value = value.get("dataset", [value])
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise JoinValidationError(f"{path}: expected JSON, JSON array, or JSONL objects")
    return value


def _buffer_text(record: dict[str, Any]) -> str:
    try:
        return bytes(decode_buffers_field(record["buffers"])).decode("latin1")
    except (KeyError, TypeError):
        return ""


def _extract(text: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.search(text.replace("\\r\\n", "\r\n").replace("\\n", "\n"))
    return match.group(1).strip() if match else None


def _source_identity(record: dict[str, Any]) -> tuple[str | None, str | None, str, int, int | None]:
    text = _buffer_text(record)
    call_id = record.get("call_id") or _extract(text, _CALL_ID_RE)
    via_branch = _extract(text, _VIA_BRANCH_RE)
    request = _extract(text, _REQUEST_METHOD_RE)
    response = _extract(text, _RESPONSE_CLASS_RE)
    method = request or (f"RESPONSE_{response}XX" if response else "UNKNOWN")
    raw_bytes = bytes(decode_buffers_field(record["buffers"]))
    separator_position = raw_bytes.find(bytes([SEP_BYTE]))
    return (
        str(call_id).strip() if call_id else None,
        via_branch,
        method,
        len(raw_bytes),
        separator_position if separator_position >= 0 else None,
    )


def _build_sources(benign_path: Path, attack_path: Path) -> tuple[list[SourceRecord], int]:
    benign = _load_dataset(benign_path)
    attack = _load_dataset(attack_path)
    sources = [SourceRecord("benign", index, index, record) for index, record in enumerate(benign)]
    offset = len(benign)
    sources.extend(
        SourceRecord("attack", index, offset + index, record)
        for index, record in enumerate(attack)
    )
    return sources, offset


def _manifest_index(rows: Iterable[dict[str, Any]], field: str) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        value = row.get(field)
        if value is not None and str(value).strip():
            index[str(value).strip()].append(row)
    return index


def _provenance_match(
    source: SourceRecord,
    indexes: dict[str, dict[str, list[dict[str, Any]]]],
) -> tuple[dict[str, Any] | None, str, str]:
    call_id, via_branch, _, _, _ = _source_identity(source.record)
    call_matches = indexes["call_id"].get(call_id, []) if call_id else []
    if len(call_matches) == 1:
        return call_matches[0], "call_id", "matched"
    if len(call_matches) > 1:
        return None, "call_id", "ambiguous"
    if call_id:
        return None, "none", "unmatched"
    via_matches = indexes["via_branch"].get(via_branch, []) if via_branch else []
    if len(via_matches) == 1:
        return via_matches[0], "via_branch", "matched"
    if len(via_matches) > 1:
        return None, "via_branch", "ambiguous"
    return None, "none", "unmatched"


def _validate_alignment(predictions: list[dict[str, Any]], sources: list[SourceRecord]) -> tuple[list[tuple[dict[str, Any], SourceRecord]], list[str]]:
    failures: list[str] = []
    direct_fields = {"source_index", "source_class", "buffer_sha256"}
    direct_rows = [direct_fields <= row.keys() for row in predictions]
    if any(direct_rows) and not all(direct_rows):
        return [], ["prediction export mixes direct identity rows with legacy rows"]
    direct = all(direct_rows)
    if direct:
        source_map = {(source.source_class, source.source_index): source for source in sources}
        pairs = []
        used_indexes: set[int] = set()
        for row_index, prediction in enumerate(predictions):
            key = (str(prediction["source_class"]), int(prediction["source_index"]))
            source = source_map.get(key)
            if source is None:
                failures.append(f"prediction {row_index}: invalid direct source index {key}")
                continue
            if source.global_source_index in used_indexes:
                failures.append(f"prediction {row_index}: duplicate direct source index {key}")
            used_indexes.add(source.global_source_index)
            if prediction["buffer_sha256"] != buffer_sha256(source.record["buffers"]):
                failures.append(f"prediction {row_index}: buffer_sha256 mismatch")
            pairs.append((prediction, source))
        if len(used_indexes) != len(sources):
            failures.append("direct export does not cover every source record exactly once")
        return pairs, failures

    if len(predictions) != len(sources):
        failures.append(f"prediction count {len(predictions)} != source count {len(sources)}")
    return list(zip(predictions, sources)), failures


def join_predictions(
    predictions: list[dict[str, Any]], benign_records: list[dict[str, Any]],
    attack_records: list[dict[str, Any]], benign_provenance: list[dict[str, Any]],
    attack_provenance: list[dict[str, Any]], allow_unmatched: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, int], list[str]]:
    sources = [SourceRecord("benign", index, index, record) for index, record in enumerate(benign_records)]
    offset = len(sources)
    sources.extend(SourceRecord("attack", index, offset + index, record) for index, record in enumerate(attack_records))
    pairs, failures = _validate_alignment(predictions, sources)
    audit = defaultdict(int)
    joined: list[dict[str, Any]] = []
    indexes_by_class = {
        "benign": {field: _manifest_index(benign_provenance, field) for field in ("call_id", "via_branch")},
        "attack": {field: _manifest_index(attack_provenance, field) for field in ("call_id", "via_branch")},
    }
    for prediction, source in pairs:
        call_id, via_branch, method, buffer_length, separator_position = _source_identity(source.record)
        expected_class = 0 if source.source_class == "benign" else 1
        if int(prediction.get("is_attack", -1)) != expected_class:
            audit["label_mismatch_count"] += 1
            failures.append(f"source {source.global_source_index}: is_attack mismatch")
        if int(prediction.get("alerted", -1)) != int(source.record.get("alerted", 0)):
            audit["alerted_mismatch_count"] += 1
            failures.append(f"source {source.global_source_index}: alerted mismatch")
        if prediction.get("call_id") != call_id:
            audit["call_id_mismatch_count"] += 1
            failures.append(f"source {source.global_source_index}: call_id mismatch")
        if call_id is None:
            audit["missing_call_id_count"] += 1
        provenance, join_key, join_status = _provenance_match(source, indexes_by_class[source.source_class])
        if join_status == "matched":
            audit[f"matched_by_{join_key}"] += 1
        elif join_status == "ambiguous":
            audit["ambiguous_count"] += 1
            failures.append(f"source {source.global_source_index}: ambiguous {join_key} provenance")
        else:
            audit["unmatched_count"] += 1
            audit["missing_provenance_count"] += 1
            if not allow_unmatched:
                failures.append(f"source {source.global_source_index}: missing provenance")
        row = dict(prediction)
        row.update({
            "source_class": source.source_class, "source_index": source.source_index,
            "global_source_index": source.global_source_index,
            "buffer_sha256": buffer_sha256(source.record["buffers"]), "call_id": call_id,
            "via_branch": via_branch, "sip_method": method, "buffer_length": buffer_length,
            "separator_position": separator_position, "has_separator": separator_position is not None,
            "provenance_join_key": join_key, "provenance_join_status": join_status,
            "provenance": {field: provenance.get(field) if provenance else None for field in _PROVENANCE_FIELDS},
        })
        for field in _TELEMETRY_FIELDS:
            if field in source.record:
                row[field] = source.record[field]
        joined.append(row)
    return joined, dict(audit), failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--benign-split", required=True, type=Path)
    parser.add_argument("--attack-split", required=True, type=Path)
    parser.add_argument("--benign-provenance", required=True, type=Path)
    parser.add_argument("--attack-provenance", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--audit-output", required=True, type=Path)
    parser.add_argument("--split-name", required=True, choices=("val", "test"))
    parser.add_argument("--include-buffers", action="store_true")
    parser.add_argument("--allow-unmatched", action="store_true")
    args = parser.parse_args(argv)
    predictions = _load_json_array(args.predictions)
    sources, benign_count = _build_sources(args.benign_split, args.attack_split)
    joined, counters, failures = join_predictions(
        predictions, [source.record for source in sources[:benign_count]],
        [source.record for source in sources[benign_count:]],
        _load_manifest(args.benign_provenance), _load_manifest(args.attack_provenance),
        args.allow_unmatched,
    )
    if args.include_buffers:
        source_by_global_index = {source.global_source_index: source for source in sources}
        for row in joined:
            row["buffers"] = source_by_global_index[row["global_source_index"]].record["buffers"]
    audit = {
        "prediction_path": str(args.predictions),
        "dataset_paths": {"benign": str(args.benign_split), "attack": str(args.attack_split)},
        "provenance_paths": {"benign": str(args.benign_provenance), "attack": str(args.attack_provenance)},
        "split_name": args.split_name, "prediction_count": len(predictions),
        "benign_record_count": benign_count, "attack_record_count": len(sources) - benign_count,
        "joined_count": len(joined), "buffer_fingerprint_policy": _FINGERPRINT_POLICY,
        "source_order_policy": "dataset array order; benign records first, attack records second; no sorting, shuffling, deduplication, or filtering",
        "failed_validation_checks": failures,
        **{key: counters.get(key, 0) for key in (
            "matched_by_call_id", "matched_by_via_branch", "unmatched_count", "ambiguous_count",
            "missing_call_id_count", "missing_provenance_count", "label_mismatch_count",
            "alerted_mismatch_count", "call_id_mismatch_count",
        )},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for row in joined:
            stream.write(json.dumps(row, ensure_ascii=True) + "\n")
    with args.audit_output.open("w", encoding="utf-8") as stream:
        json.dump(audit, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
    if failures:
        raise JoinValidationError("; ".join(failures[:10]))
    return 0


if __name__ == "__main__":
    main()