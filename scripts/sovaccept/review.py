"""Bind a presentation to its complete packet and one local subject's bytes."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path


class AcceptanceError(ValueError):
    """An acceptance operation was refused without recording an action."""


def digest(value: bytes) -> str:
    """Address exact bytes with the repository's SHA-256 vocabulary."""
    return "sha256:" + sha256(value).hexdigest()


def canonical(value: dict) -> bytes:
    """Packet identity ignores JSON whitespace but preserves every field's meaning."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def capture(root: Path, packet: dict) -> dict:
    """Read a concrete subject and return the review identity, without writing state.

    Historical descriptive or multi-document subjects remain readable. A fresh
    decision needs a single file (which may itself be a version manifest).
    """
    artifact = packet["subject"]["artifact"]
    relative = Path(artifact)
    target = (root / relative).resolve()
    if relative.is_absolute() or not target.is_relative_to(root.resolve()) or not target.is_file():
        raise AcceptanceError(
            "REVIEW_SUBJECT_UNAVAILABLE: present one existing file inside the repository")
    try:
        subject_digest = digest(target.read_bytes())
    except OSError as error:
        raise AcceptanceError("REVIEW_SUBJECT_UNAVAILABLE: cannot read the subject") from error
    identity = {
        "review_schema": "soveraeign-acceptance-review/v1",
        "packet_id": packet["packet_id"],
        "packet_digest": digest(canonical(packet)),
        "subject": {"artifact": artifact, "digest": subject_digest},
    }
    return {**identity, "review_digest": digest(canonical(identity))}
