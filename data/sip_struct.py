"""SIP structure parsing and fuzz-score heuristics for pseudo-positive mining.

Pure Python — no torch dependency. Used by mine_fuzzed_pseudo_positives.py
to detect fuzzed/gibberish header field values in unlabeled training records
without accessing ``is_attack`` labels during selection.

Design principles
-----------------
- Field-typed scoring: credential fields (Authorization) are scored by grammar
  violation, not entropy, because benign nonces are legitimately high-entropy.
- NLP fields (Accept, User-Agent, Subject) are scored by the ``gibberish()``
  heuristic (3-component: Shannon entropy of alpha chars, max consonant run,
  bigram pair frequency).
- Structural flags (bare-IP URI, missing Contact, CSeq=1) contribute a small
  fixed-weight bonus.
- Response messages score Via grammar, From/To URI structure, User-Agent,
  and WWW-Authenticate rather than request-specific fields.
- ``is_attack`` is NEVER accessed here. All thresholds are static.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .common import decode_buffers_field, split_header_body

# ─── constants ────────────────────────────────────────────────────────────────

_SEP_BYTE = 0x1E
_FIXED_LEN = 1024
_FALLBACK_HEADER_LEN = 512

# Top English letter-pair frequencies (case-folded). Used for the bigram
# unknownness score.  A pair NOT in this set is "unusual", raising the
# gibberish score. Built from standard bigram frequency tables.
_COMMON_BIGRAMS: frozenset[str] = frozenset({
    "th", "he", "in", "er", "an", "re", "on", "at", "en",
    "nt", "ha", "es", "st", "ou", "ed", "to", "it", "is",
    "hi", "or", "et", "of", "ti", "ar", "te", "se", "nd",
    "le", "sa", "al", "ro", "li", "ng", "ve", "ra", "as",
    "me", "de", "ri", "pr", "tr", "ch", "sh", "ss", "ll",
    "wh", "we", "wo", "si", "so", "fo", "be", "co", "ma",
    "no", "ca", "la", "pe", "ly", "ta", "io", "us", "ow",
    "pa", "na", "ac", "wa", "lo", "ic", "ea", "ne", "ge",
    "gh", "ur", "em", "el", "mo", "il", "di", "ni", "ce",
    "pl", "sp", "ci", "fr", "cl", "gr", "sc", "bl", "fl",
})

_VOWELS: frozenset[str] = frozenset("aeiou")

# ─── ParsedSip ────────────────────────────────────────────────────────────────


@dataclass
class ParsedSip:
    """Lightweight representation of a parsed SIP message header."""

    is_response: bool
    """True for status lines (``SIP/2.0 CODE Reason``), False for requests."""

    method: str
    """Request method (e.g. ``REGISTER``) or empty string for responses."""

    status_code: int
    """HTTP-style status code (e.g. ``100``) or 0 for requests."""

    request_uri: str
    """Request-URI token (e.g. ``sip:172.18.0.2``) or empty for responses."""

    first_line: str
    """Raw first line of the SIP message."""

    fields: Dict[str, str] = field(default_factory=dict)
    """Lower-cased header field names → last observed value (stripped)."""


# ─── public API ───────────────────────────────────────────────────────────────


def header_text_from_record(
    rec: Dict[str, Any],
    fixed_len: int = _FIXED_LEN,
    sep_byte: int = _SEP_BYTE,
    fallback_header_len: int = _FALLBACK_HEADER_LEN,
) -> str:
    """Extract the SIP header bytes from a raw dataset record as a latin-1 string.

    Uses the same ``decode_buffers_field`` + ``split_header_body`` pipeline as
    the training data loader so the text is byte-for-byte consistent.

    Args:
        rec: A record dict with a ``"buffers"`` key (raw or normalised bytes).
        fixed_len: Total number of bytes to consider (default 1024).
        sep_byte: Separator byte value (default 0x1E).
        fallback_header_len: Header window when no sep_byte is found.

    Returns:
        The header portion decoded as latin-1 (lossless for raw bytes).
    """
    ids = decode_buffers_field(rec.get("buffers", rec.get("buffers_field", [])))
    header_ids, _ = split_header_body(ids, fixed_len, sep_byte, fallback_header_len)
    return bytes(v & 0xFF for v in header_ids).decode("latin-1", errors="replace")


def parse_sip_header(text: str) -> ParsedSip:
    """Parse SIP header text into a :class:`ParsedSip` dataclass.

    Handles:
    - Request lines: ``METHOD sip:... SIP/2.0``
    - Status lines: ``SIP/2.0 CODE Reason text``
    - Multi-value / folded header fields (continuation lines starting with
      whitespace are joined to the preceding field).

    Returns a :class:`ParsedSip` with lower-cased field names.  Duplicate
    fields keep the last observed value.
    """
    lines = text.splitlines()
    if not lines:
        return ParsedSip(
            is_response=False, method="", status_code=0,
            request_uri="", first_line="", fields={},
        )

    first_line = lines[0].strip()
    is_response = first_line.upper().startswith("SIP/")

    method = ""
    status_code = 0
    request_uri = ""

    if is_response:
        # SIP/2.0 CODE Reason
        parts = first_line.split(None, 2)
        if len(parts) >= 2:
            try:
                status_code = int(parts[1])
            except ValueError:
                status_code = 0
    else:
        # METHOD sip:uri SIP/2.0
        parts = first_line.split(None, 2)
        if parts:
            method = parts[0].upper()
        if len(parts) >= 2:
            request_uri = parts[1]

    # Parse header fields (RFC 3261 folding: line starting with SP/HT continues
    # the previous field).
    fields: Dict[str, str] = {}
    current_name: Optional[str] = None
    current_val: List[str] = []

    def _flush() -> None:
        if current_name is not None:
            fields[current_name] = " ".join(current_val).strip()

    for line in lines[1:]:
        if not line:
            continue
        if line[0] in (" ", "\t") and current_name is not None:
            # Continuation line
            current_val.append(line.strip())
            continue
        _flush()
        colon = line.find(":")
        if colon == -1:
            current_name = None
            current_val = []
            continue
        current_name = line[:colon].strip().lower()
        current_val = [line[colon + 1:].strip()]

    _flush()

    return ParsedSip(
        is_response=is_response,
        method=method,
        status_code=status_code,
        request_uri=request_uri,
        first_line=first_line,
        fields=fields,
    )


def sip_message_type(parsed: ParsedSip) -> str:
    """Return a canonical message-type string.

    Returns:
        The request method (e.g. ``"REGISTER"``, ``"INVITE"``, ``"OPTIONS"``)
        for requests, or ``"RESPONSE"`` for SIP status-line messages.
    """
    if parsed.is_response:
        return "RESPONSE"
    return parsed.method if parsed.method else "UNKNOWN"


# ─── fuzz scoring primitives ──────────────────────────────────────────────────


def gibberish(s: str) -> float:
    """Return a [0, 1] gibberish score; higher = more random / fuzzed.

    Three-component heuristic:
    1. Shannon entropy of alpha-only characters (normalized by log2(26)).
    2. Maximum consecutive consonant run (normalized, capped at 6).
    3. Fraction of consecutive alpha-pair bigrams NOT in a common English set.

    Designed for NLP fields (User-Agent, Accept subtypes, Subject).  Do NOT
    apply to credential fields — benign nonces are legitimately high-entropy.
    """
    s = s.strip().lower()
    alpha = [c for c in s if c.isalpha()]
    if len(alpha) < 4:
        return 0.5  # too short to judge reliably

    # Component 1: Shannon entropy over alpha chars
    counts = Counter(alpha)
    total = len(alpha)
    H = -sum((n / total) * math.log2(n / total) for n in counts.values())
    H_norm = min(1.0, H / math.log2(26))

    # Component 2: max consecutive consonant run
    max_run = 0
    run = 0
    for c in alpha:
        if c not in _VOWELS:
            run += 1
            if run > max_run:
                max_run = run
        else:
            run = 0
    run_norm = min(1.0, max_run / 6.0)

    # Component 3: bigram unknownness
    pairs = [alpha[i] + alpha[i + 1] for i in range(len(alpha) - 1)]
    if pairs:
        unknown_frac = sum(1 for p in pairs if p not in _COMMON_BIGRAMS) / len(pairs)
    else:
        unknown_frac = 0.0

    return 0.45 * H_norm + 0.30 * run_norm + 0.25 * unknown_frac


def credential_grammar_violation(value: str) -> float:
    """Return a [0, 1] grammar-violation score for an Authorization-like field.

    0.0 = well-formed Digest or Basic credential.
    1.0 = unrecognised scheme or structurally malformed.

    This function checks grammar (scheme + key=value structure), NOT entropy,
    to avoid penalising legitimate high-entropy hex nonces.
    """
    value = value.strip()
    if not value:
        return 0.0

    if not re.match(r"^(Digest|Basic)\s", value, re.IGNORECASE):
        # Unknown scheme — hard grammar violation
        return 1.0

    upper = value.upper()
    if upper.startswith("BASIC"):
        # Basic auth: must be a single base64 token after the scheme keyword
        rest = value.split(None, 1)
        token = rest[1] if len(rest) > 1 else ""
        return 0.0 if re.match(r"^[A-Za-z0-9+/=]+$", token) else 0.8

    # Digest auth: must contain realm= and nonce=
    has_realm = bool(re.search(r"\brealm\s*=", value, re.IGNORECASE))
    has_nonce = bool(re.search(r"\bnonce\s*=", value, re.IGNORECASE))
    if not has_realm and not has_nonce:
        return 0.95
    if not has_realm or not has_nonce:
        return 0.60
    return 0.0


def _via_grammar_violation(value: str) -> float:
    """Check whether a Via field conforms to ``SIP/2.0/<transport>``."""
    if re.match(r"^SIP/2\.0/(UDP|TCP|TLS|SCTP|WS)\s", value, re.IGNORECASE):
        return 0.0
    return 0.9


def _uri_has_sip(value: str) -> bool:
    """True if the field value contains a sip: or tel: URI."""
    lv = value.lower()
    return "sip:" in lv or "tel:" in lv


def _bare_ip_uri(uri: str) -> bool:
    """True if the request-URI host is a raw IPv4/IPv6 address (no domain name)."""
    # Strip scheme
    m = re.search(r"sip[s]?:([^;>?\s]+)", uri, re.IGNORECASE)
    if not m:
        return False
    host_part = m.group(1)
    # Remove user@ prefix if present
    if "@" in host_part:
        host_part = host_part.split("@", 1)[1]
    # Remove port
    host_part = host_part.split(":")[0].rstrip("]")
    if host_part.startswith("["):
        host_part = host_part[1:]
    # IPv4 pattern
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host_part):
        return True
    # IPv6 pattern (simplified)
    if re.match(r"^[0-9a-fA-F:]+$", host_part) and ":" in host_part:
        return True
    return False


# ─── composite fuzz_score ─────────────────────────────────────────────────────


def fuzz_score(parsed: ParsedSip) -> float:
    """Return a [0, 1] composite fuzz score for a parsed SIP message.

    Dispatches to request or response scoring based on ``parsed.is_response``.
    Higher score = more likely to be a fuzzed/attack message.

    Weighting:
      - 80 % field-level fuzz (typed by field category)
      - 20 % structural flags (request only; responses return 0.0 for flags)
    """
    if parsed.is_response:
        return _fuzz_score_response(parsed)
    return _fuzz_score_request(parsed)


def _fuzz_score_request(parsed: ParsedSip) -> float:
    """Field-typed fuzz score for SIP request messages."""
    fields = parsed.fields
    field_scores: List[Tuple[str, float]] = []

    # Credential fields — grammar violation only, never entropy
    for fname in ("authorization", "proxy-authorization"):
        val = fields.get(fname, "")
        if val:
            field_scores.append((fname, credential_grammar_violation(val)))

    # NLP fields — gibberish on subtype / product token
    accept_val = fields.get("accept", "")
    if accept_val:
        # Score the first media-type subtype token
        token = re.split(r"[,;\s/]", accept_val.strip())[0]
        if token:
            field_scores.append(("accept", gibberish(token)))

    ua_val = fields.get("user-agent", "")
    if ua_val:
        # Score the product name (before the first '/')
        token = ua_val.split("/")[0].strip()
        if token:
            field_scores.append(("user-agent", gibberish(token)))

    subject_val = fields.get("subject", "")
    if subject_val:
        field_scores.append(("subject", gibberish(subject_val)))

    field_fuzz = (
        sum(s for _, s in field_scores) / len(field_scores)
        if field_scores
        else 0.0
    )

    # Structural flags (all weak, averaged into a 0–1 flag score)
    flag_bits: List[float] = []

    # Bare-IP request URI
    flag_bits.append(1.0 if _bare_ip_uri(parsed.request_uri) else 0.0)

    # Missing Contact header (unusual for REGISTER/INVITE but not universal)
    flag_bits.append(0.0 if fields.get("contact", "") else 1.0)

    # CSeq=1 with no existing session (low-confidence signal; weight is low)
    cseq_val = fields.get("cseq", "")
    if cseq_val:
        m = re.match(r"^\s*(\d+)", cseq_val)
        flag_bits.append(1.0 if (m and int(m.group(1)) == 1) else 0.0)
    else:
        flag_bits.append(0.0)

    flags = sum(flag_bits) / len(flag_bits) if flag_bits else 0.0

    return 0.80 * field_fuzz + 0.20 * flags


def _fuzz_score_response(parsed: ParsedSip) -> float:
    """Field-typed fuzz score for SIP response messages.

    Scores Via grammar, From/To URI structure, User-Agent, and
    WWW-Authenticate.  Does NOT score Accept or Authorization (those appear
    in requests, not responses).
    """
    fields = parsed.fields
    component_scores: List[float] = []

    # Via grammar
    via_val = fields.get("via", "")
    if via_val:
        component_scores.append(_via_grammar_violation(via_val))

    # From and To must contain a sip: or tel: URI
    for fname in ("from", "to"):
        val = fields.get(fname, "")
        if val:
            component_scores.append(0.0 if _uri_has_sip(val) else gibberish(val))

    # User-Agent — product name
    ua_val = fields.get("user-agent", "")
    if ua_val:
        token = ua_val.split("/")[0].strip()
        if token:
            component_scores.append(gibberish(token))

    # WWW-Authenticate / Proxy-Authenticate — grammar violation
    for fname in ("www-authenticate", "proxy-authenticate"):
        val = fields.get(fname, "")
        if val:
            component_scores.append(credential_grammar_violation(val))

    return (
        sum(component_scores) / len(component_scores)
        if component_scores
        else 0.0
    )


# ─── convenience: score a raw record ─────────────────────────────────────────


def score_record(
    rec: Dict[str, Any],
    fixed_len: int = _FIXED_LEN,
    sep_byte: int = _SEP_BYTE,
    fallback_header_len: int = _FALLBACK_HEADER_LEN,
) -> Tuple[str, float]:
    """Parse a raw record and return ``(message_type, fuzz_score)``.

    Convenience wrapper for the mining script.  Calls
    ``header_text_from_record`` → ``parse_sip_header`` → ``sip_message_type``
    and ``fuzz_score`` in one call.

    Returns:
        A 2-tuple ``(msg_type, score)`` where ``msg_type`` is e.g.
        ``"REGISTER"`` or ``"RESPONSE"`` and ``score`` is in [0, 1].
    """
    text = header_text_from_record(rec, fixed_len, sep_byte, fallback_header_len)
    parsed = parse_sip_header(text)
    return sip_message_type(parsed), fuzz_score(parsed)
