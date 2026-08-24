"""Focused tests for prediction/source/provenance joins."""

from nids_ml.tools.join_predictions_with_provenance import join_predictions


def _record(call_id: str | None, branch: str, is_attack: int, alerted: int = 0) -> dict:
    call_id_line = f"Call-ID: {call_id}\r\n" if call_id else ""
    return {
        "buffers": (
            f"INVITE sip:target@example.test SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP host.example.test;branch={branch}\r\n"
            f"{call_id_line}\r\nbody"
        ),
        "is_attack": is_attack,
        "alerted": alerted,
        "proto": 17,
    }


def _prediction(call_id: str | None, is_attack: int, alerted: int = 0) -> dict:
    return {
        "split": "test", "call_id": call_id, "raw_logit": -1.2,
        "raw_score": 0.23, "calibrated_score": 0.11,
        "is_attack": is_attack, "alerted": alerted,
    }


def _provenance(call_id: str | None, branch: str, **extra: object) -> dict:
    return {"call_id": call_id, "via_branch": branch, "scenario": "scenario.xml", **extra}


def test_successful_legacy_index_reconstruction_join() -> None:
    benign = _record("benign-id", "benign-branch", 0)
    attack = _record("attack-id", "attack-branch", 1, alerted=1)
    joined, audit, failures = join_predictions(
        [_prediction("benign-id", 0), _prediction("attack-id", 1, alerted=1)],
        [benign], [attack],
        [_provenance("benign-id", "benign-branch", source_role="benign")],
        [_provenance("attack-id", "attack-branch", mutation_id="defect")],
    )

    assert not failures
    assert audit["matched_by_call_id"] == 2
    assert joined[0]["source_index"] == 0
    assert joined[1]["global_source_index"] == 1
    assert joined[1]["provenance"]["mutation_id"] == "defect"
    assert joined[0]["proto"] == 17


def test_duplicate_call_ids_are_ambiguous() -> None:
    joined, audit, failures = join_predictions(
        [_prediction("shared", 0)], [_record("shared", "branch", 0)], [],
        [_provenance("shared", "branch"), _provenance("shared", "other")], [],
    )

    assert joined[0]["provenance_join_status"] == "ambiguous"
    assert audit["ambiguous_count"] == 1
    assert any("ambiguous call_id" in failure for failure in failures)


def test_ambiguous_via_branch_is_rejected_when_call_id_is_missing() -> None:
    joined, audit, failures = join_predictions(
        [_prediction(None, 0)], [_record(None, "shared-branch", 0)], [],
        [_provenance(None, "shared-branch"), _provenance(None, "shared-branch")], [],
    )

    assert joined[0]["provenance_join_key"] == "via_branch"
    assert audit["missing_call_id_count"] == 1
    assert any("ambiguous via_branch" in failure for failure in failures)


def test_missing_provenance_requires_explicit_opt_in() -> None:
    prediction = _prediction("unknown", 0)
    source = _record("unknown", "branch", 0)

    joined, audit, failures = join_predictions([prediction], [source], [], [], [])
    assert joined[0]["provenance_join_status"] == "unmatched"
    assert audit["missing_provenance_count"] == 1
    assert failures

    _, _, allowed_failures = join_predictions(
        [prediction], [source], [], [], [], allow_unmatched=True,
    )
    assert not allowed_failures


def test_present_call_id_does_not_fall_back_to_via_branch() -> None:
    joined, _, failures = join_predictions(
        [_prediction("unmatched-call-id", 0)],
        [_record("unmatched-call-id", "branch", 0)], [],
        [_provenance(None, "branch")], [],
    )

    assert joined[0]["provenance_join_status"] == "unmatched"
    assert failures


def test_incorrect_class_order_is_an_alignment_failure() -> None:
    _, audit, failures = join_predictions(
        [_prediction("attack-id", 1), _prediction("benign-id", 0)],
        [_record("benign-id", "benign", 0)], [_record("attack-id", "attack", 1)],
        [_provenance("benign-id", "benign")], [_provenance("attack-id", "attack")],
    )

    assert audit["label_mismatch_count"] == 2
    assert sum("is_attack mismatch" in failure for failure in failures) == 2


def test_label_mismatch_is_an_alignment_failure() -> None:
    _, audit, failures = join_predictions(
        [_prediction("benign-id", 1)], [_record("benign-id", "branch", 0)], [],
        [_provenance("benign-id", "branch")], [],
    )

    assert audit["label_mismatch_count"] == 1
    assert any("is_attack mismatch" in failure for failure in failures)


def test_direct_identity_fingerprint_disagreement_is_hard_failure() -> None:
    source = _record("benign-id", "branch", 0)
    prediction = _prediction("benign-id", 0)
    prediction.update({
        "source_class": "benign", "source_index": 0,
        "buffer_sha256": "not-the-source-fingerprint",
    })

    _, _, failures = join_predictions(
        [prediction], [source], [], [_provenance("benign-id", "branch")], [],
    )

    assert any("buffer_sha256 mismatch" in failure for failure in failures)