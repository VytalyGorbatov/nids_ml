#!/usr/bin/env python3
"""Audit PU vs teacher-copy recovery with mutation-level defect-presence splits.

This script uses validation-selected thresholds (benign, non-alerted) and applies
those thresholds unchanged to val/test rows. It then reports Snort-FN recovery
per mutation and SIP method for both models, split by mutation-specific defect
presence in raw message bytes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from nids_ml.tools.frozen_threshold_transfer import validation_fpr_threshold
from nids_ml.tools.join_predictions_with_provenance import decode_buffers_field


SEP_BYTE = 0x1E
UINT32_MAX = 2**32 - 1


@dataclass(frozen=True)
class MutationRule:
    mutation_id: str
    detector: Callable[[str], bool]
    description: str


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def load_dataset(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    dataset = value.get("dataset") if isinstance(value, dict) else None
    if not isinstance(dataset, list):
        raise ValueError(f"{path} does not contain a dataset array")
    return dataset


def decode_record_text(record: dict[str, Any]) -> str:
    return bytes(decode_buffers_field(record["buffers"])).decode("latin1", errors="ignore")


def split_message(text: str) -> tuple[str, str]:
    if chr(SEP_BYTE) in text:
        head, body = text.split(chr(SEP_BYTE), 1)
        return head, body
    marker = "\r\n\r\n"
    if marker in text:
        head, body = text.split(marker, 1)
        return head, body
    marker = "\n\n"
    if marker in text:
        head, body = text.split(marker, 1)
        return head, body
    return text, ""


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n")


def parse_start_line(text: str) -> str:
    head, _ = split_message(text)
    norm = normalize_newlines(head)
    lines = norm.split("\n")
    return lines[0].strip() if lines else ""


def header_values(text: str, key: str) -> list[str]:
    wanted = key.lower()
    head, _ = split_message(text)
    vals: list[str] = []
    for line in normalize_newlines(head).split("\n")[1:]:
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        if name.strip().lower() == wanted:
            vals.append(value.strip())
    return vals


def has_lowercase_duplicate_header(text: str) -> bool:
    head, _ = split_message(text)
    counts: dict[str, int] = defaultdict(int)
    for line in normalize_newlines(head).split("\n")[1:]:
        if ":" not in line:
            continue
        name, _ = line.split(":", 1)
        counts[name.strip().lower()] += 1
    return any(
        counts.get(name, 0) > 1
        for name in ("call-id", "cseq", "to", "from", "max-forwards")
    )


def cseq_method_mismatch(text: str) -> bool:
    start = parse_start_line(text)
    start_match = re.match(r"^([A-Z]+)\s+\S+\s+SIP/2\.0$", start)
    if not start_match:
        return False
    req_method = start_match.group(1)
    cseq_vals = header_values(text, "CSeq")
    if not cseq_vals:
        return False
    cseq_match = re.match(r"^\s*\d+\s+([A-Z]+)\s*$", cseq_vals[0])
    if not cseq_match:
        return False
    return cseq_match.group(1) != req_method


def unbalanced_display_quote(text: str) -> bool:
    for key in ("To", "From"):
        for value in header_values(text, key):
            if value.count('"') % 2 == 1:
                return True
    return False


def exthdsep_pattern(text: str) -> bool:
    for key in ("Via", "Contact"):
        for value in header_values(text, key):
            if any(token in value for token in (",,", ";;", ",;", ";,")):
                return True
    return False


def invdisp_pattern(text: str) -> bool:
    for key in ("To", "From"):
        for value in header_values(text, key):
            left = value.split("<", 1)[0]
            if "," in left and '"' not in left:
                return True
    return False


def content_length_value(text: str) -> int | None:
    vals = header_values(text, "Content-Length")
    if not vals:
        return None
    token = vals[0].strip()
    if not re.match(r"^-?\d+$", token):
        return None
    try:
        return int(token)
    except ValueError:
        return None


def body_length(text: str) -> int:
    _, body = split_message(text)
    return len(body.encode("latin1", errors="ignore"))


def is_status_line_with_code(text: str, min_code: int = 0) -> bool:
    start = parse_start_line(text)
    m = re.match(r"^SIP/2\.0\s+(\d{3,})\b", start)
    if not m:
        return False
    try:
        code = int(m.group(1))
    except ValueError:
        return False
    return code >= min_code


def has_sdp_body(text: str) -> bool:
    _, body = split_message(text)
    norm = normalize_newlines(body)
    return any(marker in norm for marker in ("\nv=0", "\no=", "\nm="))


def reqsclarg_pattern(text: str) -> bool:
    max_forwards = header_values(text, "Max-Forwards")
    expires = header_values(text, "Expires")
    cseq_vals = header_values(text, "CSeq")
    contact_vals = header_values(text, "Contact")

    if max_forwards:
        m = re.match(r"^\s*(\d+)\s*$", max_forwards[0])
        if m and int(m.group(1)) >= 200:
            return True
    if expires:
        m = re.match(r"^\s*(\d+)\s*$", expires[0])
        if m and int(m.group(1)) > UINT32_MAX:
            return True
    if cseq_vals:
        m = re.match(r"^\s*(\d{12,})\s+[A-Z]+\s*$", cseq_vals[0])
        if m:
            return True
    for value in contact_vals:
        m = re.search(r";expires=(\d{12,})\b", value)
        if m:
            return True
    return False


def respsclarg_pattern(text: str) -> bool:
    retry_after = header_values(text, "Retry-After")
    warning = header_values(text, "Warning")
    cseq_vals = header_values(text, "CSeq")

    if parse_start_line(text).strip() == "SIP/2.0 503 Service Unavailable":
        return True
    if retry_after and re.match(r"^\d{12,}$", retry_after[0].strip()):
        return True
    if warning and re.match(r"^\s*\d{4,}\s+", warning[0]):
        return True
    if cseq_vals and re.match(r"^\s*\d{12,}\s+[A-Z]+\s*$", cseq_vals[0]):
        return True
    return False


def longreq_pattern(text: str) -> bool:
    call_ids = header_values(text, "Call-ID")
    if call_ids and len(call_ids[0]) >= 80:
        return True

    head, _ = split_message(text)
    for line in normalize_newlines(head).split("\n"):
        if re.match(r"^[A-Za-z]-Lo{10,}ng-Field\s*:", line):
            return True

    via_count = sum(1 for line in normalize_newlines(head).split("\n") if line.lower().startswith("via:"))
    return via_count >= 3


def build_rules() -> dict[str, MutationRule]:
    return {
        "badbranch": MutationRule(
            "badbranch",
            lambda t: re.search(r"(?im)^Via:.*;\s*branch=z9hG4bK(?:[;\s,]|$)", t) is not None,
            "Via branch parameter equals bare z9hG4bK token",
        ),
        "balquote": MutationRule(
            "balquote",
            unbalanced_display_quote,
            "Odd quote count in To/From display-name header",
        ),
        "bigcode": MutationRule(
            "bigcode",
            lambda t: is_status_line_with_code(t, min_code=700),
            "Response status code >= 700",
        ),
        "clerr": MutationRule(
            "clerr",
            lambda t: (content_length_value(t) or -1) > body_length(t),
            "Content-Length exceeds actual body length",
        ),
        "cseqmatch": MutationRule(
            "cseqmatch",
            cseq_method_mismatch,
            "CSeq method differs from request-line method",
        ),
        "dblreq": MutationRule(
            "dblreq",
            lambda t: re.search(r"(?m)^INVITE\s+\S+\s+SIP/2\.0$", normalize_newlines(split_message(t)[1])) is not None,
            "Body carries appended SIP INVITE start-line",
        ),
        "escnull": MutationRule(
            "escnull",
            lambda t: "%00" in t,
            "Escaped null token %00 present in URI fields",
        ),
        "escuri": MutationRule(
            "escuri",
            lambda t: "%3Csip:" in t and "%3E" in t,
            "Escaped header URI fragment %3Csip:...%3E in Request-URI",
        ),
        "exthdsep": MutationRule(
            "exthdsep",
            exthdsep_pattern,
            "Extraneous header separators (,, ;; ,; ;,)",
        ),
        "invdisp": MutationRule(
            "invdisp",
            invdisp_pattern,
            "Unquoted display names with comma-separated tokens",
        ),
        "invsdp": MutationRule(
            "invsdp",
            has_sdp_body,
            "SDP body markers present (v=0/o=/m=)",
        ),
        "longreq": MutationRule(
            "longreq",
            longreq_pattern,
            "Overlong header pattern (long Call-ID/custom header/multi-Via)",
        ),
        "ltgtrequri": MutationRule(
            "ltgtrequri",
            lambda t: re.match(r"^[A-Z]+\s+<sip:[^>]+>\s+SIP/2\.0$", parse_start_line(t)) is not None,
            "Request-URI enclosed in angle brackets in start-line",
        ),
        "multireq": MutationRule(
            "multireq",
            has_lowercase_duplicate_header,
            "Lowercase duplicate single-value headers present",
        ),
        "negcl": MutationRule(
            "negcl",
            lambda t: (content_length_value(t) or 0) < 0,
            "Negative Content-Length value",
        ),
        "noreason": MutationRule(
            "noreason",
            lambda t: re.match(r"^SIP/2\.0\s+\d{3}\s*$", parse_start_line(t)) is not None,
            "Status line has empty reason phrase",
        ),
        "reginvct": MutationRule(
            "reginvct",
            lambda t: "%3Csip:" in t and "%3E" in t,
            "Contact URI contains escaped embedded SIP URI",
        ),
        "reqsclarg": MutationRule(
            "reqsclarg",
            reqsclarg_pattern,
            "Overlarge scalar request fields (Max-Forwards/CSeq/Expires)",
        ),
        "respsclarg": MutationRule(
            "respsclarg",
            respsclarg_pattern,
            "Overlarge scalar response fields (Retry-After/Warning/CSeq)",
        ),
        "spacaddr": MutationRule(
            "spacaddr",
            lambda t: any("< " in v or " >" in v for v in header_values(t, "To")),
            "To header addr-spec contains injected spaces near angle brackets",
        ),
        "unkauth": MutationRule(
            "unkauth",
            lambda t: any(
                not re.match(r"^(Digest|Basic|Bearer)\b", v, flags=re.IGNORECASE)
                for v in header_values(t, "Authorization")
            ),
            "Authorization scheme is non-standard token",
        ),
    }


def mutation_id_of(row: dict[str, Any]) -> str:
    provenance = row.get("provenance") or {}
    value = provenance.get("mutation_id")
    return str(value) if value else "<none>"


def run_context(run_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    with (run_dir / "config_used.json").open(encoding="utf-8") as stream:
        config = json.load(stream)

    nids_root = Path(__file__).resolve().parents[1]
    attack_val = load_dataset((nids_root / config["attack_paths"]["val"]).resolve())
    attack_test = load_dataset((nids_root / config["attack_paths"]["test"]).resolve())
    benign_val = load_dataset((nids_root / config["benign_paths"]["val"]).resolve())
    benign_test = load_dataset((nids_root / config["benign_paths"]["test"]).resolve())
    return attack_val, attack_test, benign_val, benign_test


def source_record(
    row: dict[str, Any],
    attack_rows: list[dict[str, Any]],
    benign_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    source_class = row.get("source_class")
    index = int(row.get("source_index", -1))
    if source_class == "attack":
        return attack_rows[index]
    if source_class == "benign":
        return benign_rows[index]
    raise ValueError(f"Unexpected source_class {source_class!r}")


def annotate_rows(
    rows: list[dict[str, Any]],
    attack_rows: list[dict[str, Any]],
    benign_rows: list[dict[str, Any]],
    rules: dict[str, MutationRule],
) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for row in rows:
        mid = mutation_id_of(row)
        rule = rules.get(mid)
        if row.get("is_attack") != 1 or row.get("alerted") != 0 or rule is None:
            continue

        record = source_record(row, attack_rows, benign_rows)
        text = decode_record_text(record)
        present = bool(rule.detector(text))

        out = {
            "split": row.get("split"),
            "source_class": row.get("source_class"),
            "source_index": row.get("source_index"),
            "global_source_index": row.get("global_source_index"),
            "sip_method": row.get("sip_method"),
            "mutation_id": mid,
            "raw_score": float(row.get("raw_score", 0.0)),
            "is_attack": int(row.get("is_attack", 0)),
            "alerted": int(row.get("alerted", 0)),
            "defect_present": present,
            "defect_rule": rule.description,
        }
        annotated.append(out)
    return annotated


def aggregate(
    split_name: str,
    model_name: str,
    threshold: float,
    annotated: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in annotated:
        grouped[(row["mutation_id"], row["sip_method"])].append(row)

    out: list[dict[str, Any]] = []
    for (mutation_id, sip_method), rows in sorted(grouped.items()):
        total = len(rows)
        rec = sum(1 for row in rows if row["raw_score"] >= threshold)
        det_rows = [row for row in rows if row["defect_present"]]
        undet_rows = [row for row in rows if not row["defect_present"]]
        det_rec = sum(1 for row in det_rows if row["raw_score"] >= threshold)
        undet_rec = sum(1 for row in undet_rows if row["raw_score"] >= threshold)
        rule = rows[0]["defect_rule"] if rows else ""
        out.append({
            "split_set": split_name,
            "model": model_name,
            "threshold": threshold,
            "mutation_id": mutation_id,
            "sip_method": sip_method,
            "snort_fn_rows": total,
            "recovered_rows": rec,
            "recovery_rate": rec / total if total else 0.0,
            "detectable_rows": len(det_rows),
            "detectable_recovered_rows": det_rec,
            "detectable_recovery_rate": det_rec / len(det_rows) if det_rows else 0.0,
            "undetectable_rows": len(undet_rows),
            "undetectable_recovered_rows": undet_rec,
            "undetectable_recovery_rate": undet_rec / len(undet_rows) if undet_rows else 0.0,
            "defect_rule": rule,
        })
    return out


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize_divergence(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_key[(row["split_set"], row["mutation_id"], row["sip_method"])][row["model"]] = row

    out: list[dict[str, Any]] = []
    for (split_name, mutation_id, sip_method), models in sorted(by_key.items()):
        pu = models.get("method_headlast_pu")
        tc = models.get("teacher_copy_alerted")
        if not pu or not tc:
            continue
        out.append({
            "split_set": split_name,
            "mutation_id": mutation_id,
            "sip_method": sip_method,
            "pu_recovery": pu["recovery_rate"],
            "teacher_recovery": tc["recovery_rate"],
            "gap_pu_minus_teacher": pu["recovery_rate"] - tc["recovery_rate"],
            "pu_detectable_recovery": pu["detectable_recovery_rate"],
            "teacher_detectable_recovery": tc["detectable_recovery_rate"],
            "gap_detectable": pu["detectable_recovery_rate"] - tc["detectable_recovery_rate"],
            "pu_undetectable_rows": pu["undetectable_rows"],
            "teacher_undetectable_rows": tc["undetectable_rows"],
        })
    return out


def render_markdown(
    threshold_rows: list[dict[str, Any]],
    divergence_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# Defect-Presence Audit (Validation-Selected Threshold Transfer)",
        "",
        "Threshold policy: threshold selected only from validation benign non-alerted rows, then frozen for evaluation.",
        "",
        "## Thresholds",
        "",
        "| split_set | model | beta | threshold | val_benign_rows |",
        "|---|---|---:|---:|---:|",
    ]
    for row in threshold_rows:
        lines.append(
            f"| {row['split_set']} | {row['model']} | {row['beta']:.2f} | {row['threshold']:.6f} | {row['val_benign_rows']} |"
        )

    lines.extend([
        "",
        "## Largest PU-vs-Teacher Recovery Gaps",
        "",
        "| split_set | mutation_id | sip_method | PU | Teacher | gap | PU detectable | Teacher detectable | detectable gap |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ])

    top = sorted(divergence_rows, key=lambda row: abs(row["gap_pu_minus_teacher"]), reverse=True)[:20]
    for row in top:
        lines.append(
            "| {split_set} | {mutation_id} | {sip_method} | {pu_recovery:.2%} | {teacher_recovery:.2%} | {gap_pu_minus_teacher:+.2%} | {pu_detectable_recovery:.2%} | {teacher_detectable_recovery:.2%} | {gap_detectable:+.2%} |".format(
                **row
            )
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path("nids_ml/artifacts/article_1/runs"),
        help="Root directory containing split/model run folders.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("nids_ml/artifacts/article_1/analysis/defect_presence_audit"),
        help="Output directory for generated tables and annotated JSONL files.",
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=0.05,
        help="Validation benign FPR budget for threshold transfer.",
    )
    args = parser.parse_args()

    if not (0.0 < args.beta < 1.0):
        raise ValueError("--beta must be strictly between 0 and 1")

    rules = build_rules()
    run_specs = [
        ("mutation-set", "method_headlast_pu"),
        ("mutation-set", "teacher_copy_alerted"),
        ("new-set", "method_headlast_pu"),
        ("new-set", "teacher_copy_alerted"),
    ]

    args.out_dir.mkdir(parents=True, exist_ok=True)

    threshold_rows: list[dict[str, Any]] = []
    aggregate_rows: list[dict[str, Any]] = []

    for split_name, model_name in run_specs:
        run_dir = (args.runs_root / split_name / model_name).resolve()
        val_joined = load_jsonl(run_dir / "val_predictions_joined.jsonl")
        test_joined = load_jsonl(run_dir / "test_predictions_joined.jsonl")

        threshold = validation_fpr_threshold(val_joined, args.beta)

        attack_val, attack_test, benign_val, benign_test = run_context(run_dir)
        val_annotated = annotate_rows(val_joined, attack_val, benign_val, rules)
        test_annotated = annotate_rows(test_joined, attack_test, benign_test, rules)

        for row in val_annotated:
            row["split_set"] = split_name
            row["model"] = model_name
            row["eval_split"] = "val"
            row["threshold"] = threshold
            row["high_risk"] = row["raw_score"] >= threshold
        for row in test_annotated:
            row["split_set"] = split_name
            row["model"] = model_name
            row["eval_split"] = "test"
            row["threshold"] = threshold
            row["high_risk"] = row["raw_score"] >= threshold

        write_jsonl(args.out_dir / f"{split_name}_{model_name}_val_fn_defect_presence.jsonl", val_annotated)
        write_jsonl(args.out_dir / f"{split_name}_{model_name}_test_fn_defect_presence.jsonl", test_annotated)

        aggregate_rows.extend(aggregate(split_name, model_name, threshold, test_annotated))
        threshold_rows.append({
            "split_set": split_name,
            "model": model_name,
            "beta": args.beta,
            "threshold": threshold,
            "val_benign_rows": sum(1 for row in val_joined if row.get("is_attack") == 0 and row.get("alerted") == 0),
        })

    divergence_rows = summarize_divergence(aggregate_rows)

    write_csv(args.out_dir / "thresholds.csv", threshold_rows)
    write_csv(args.out_dir / "recovery_by_mutation_method.csv", aggregate_rows)
    write_csv(args.out_dir / "pu_teacher_gap_by_mutation_method.csv", divergence_rows)
    (args.out_dir / "SUMMARY.md").write_text(
        render_markdown(threshold_rows, divergence_rows),
        encoding="utf-8",
    )

    print(f"Wrote audit outputs to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
